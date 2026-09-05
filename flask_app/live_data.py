"""Optional live signals for route-risk assessment.

Free sources are used where practical. Keyed providers are opt-in through
environment variables so local development still works without credentials.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


_CACHE = {}
_CACHE_TTL_SECONDS = int(os.getenv("LIVE_DATA_CACHE_TTL_SECONDS", "300"))
_TIMEOUT_SECONDS = float(os.getenv("LIVE_DATA_TIMEOUT_SECONDS", "4"))


def _request_json(base_url, params=None, headers=None):
    query = urlencode(params or {})
    url = f"{base_url}?{query}" if query else base_url
    request = Request(
        url,
        headers={"User-Agent": "SupplyChainRiskDashboard/1.0", **(headers or {})},
    )
    with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _unavailable(source, reason):
    return {
        "source": source,
        "available": False,
        "observed_at": None,
        "error": reason,
    }


def _available(source, values):
    return {
        "source": source,
        "available": True,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        **values,
    }


def _safe_call(source, function):
    try:
        return function()
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return _unavailable(source, str(exc))
    except Exception as exc:  # Keep live integrations from breaking prediction.
        return _unavailable(source, f"Unexpected provider error: {exc}")


def _weather_category(weather_code):
    if weather_code in {45, 48}:
        return "Fog"
    if weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return "Rain"
    if weather_code in {71, 73, 75, 77, 85, 86, 95, 96, 99}:
        return "Storm"
    return "Clear"


def get_weather(port_name, coordinates):
    """Read current weather for a port from Open-Meteo."""
    latitude, longitude = coordinates

    def fetch():
        response = _request_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "UTC",
            },
        )
        current = response["current"]
        code = int(current["weather_code"])
        return _available(
            "Open-Meteo",
            {
                "port": port_name,
                "category": _weather_category(code),
                "weather_code": code,
                "temperature_c": current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
            },
        )

    return _safe_call("Open-Meteo", fetch)


def get_geopolitical_signal(origin, destination):
    """Estimate current route attention from recent GDELT news volume.

    This is a news-volume proxy, not a formal geopolitical risk score.
    """
    query = f'"{origin}" "{destination}"'

    def fetch():
        response = _request_json(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            {
                "query": query,
                "mode": "timelinevolraw",
                "format": "json",
                "timespan": "7d",
            },
        )
        timeline = response.get("timeline", [])
        article_count = sum(int(point.get("value", 0)) for point in timeline)
        risk_score = min(10.0, round(article_count / 25.0, 2))
        return _available(
            "GDELT",
            {
                "route": f"{origin} -> {destination}",
                "article_count_7d": article_count,
                "news_attention_score": risk_score,
                "interpretation": "Higher news volume requires review; it is not proof of disruption.",
            },
        )

    return _safe_call("GDELT", fetch)


def get_traffic(port_name, coordinates):
    """Read TomTom traffic flow when a TOMTOM_API_KEY is configured."""
    api_key = os.getenv("TOMTOM_API_KEY")
    if not api_key:
        return _unavailable("TomTom", "TOMTOM_API_KEY is not configured")

    latitude, longitude = coordinates

    def fetch():
        response = _request_json(
            "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json",
            {
                "point": f"{latitude},{longitude}",
                "unit": "KMPH",
                "key": api_key,
            },
        )
        flow = response["flowSegmentData"]
        current_speed = float(flow["currentSpeed"])
        free_flow_speed = float(flow["freeFlowSpeed"])
        congestion_ratio = round(max(0.0, 1 - current_speed / free_flow_speed), 3) if free_flow_speed else None
        return _available(
            "TomTom",
            {
                "port": port_name,
                "current_speed_kmh": current_speed,
                "free_flow_speed_kmh": free_flow_speed,
                "congestion_ratio": congestion_ratio,
            },
        )

    return _safe_call("TomTom", fetch)


def get_port_congestion(port_name):
    """Read a provider-specific port signal from PORT_CONGESTION_API_URL.

    The endpoint must accept ``?port=<name>`` and return JSON. Common keys such
    as congestion_score, vessel_wait_hours, and status are passed through.
    """
    endpoint = os.getenv("PORT_CONGESTION_API_URL")
    if not endpoint:
        return _unavailable("Port provider", "PORT_CONGESTION_API_URL is not configured")

    def fetch():
        response = _request_json(endpoint, {"port": port_name})
        return _available("Configured port provider", {"port": port_name, **response})

    return _safe_call("Configured port provider", fetch)


def get_live_context(origin, destination, port_locations):
    """Collect live signals for both ends of a route with short-lived caching."""
    cache_key = f"{origin}|{destination}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached["cached_at"] < _CACHE_TTL_SECONDS:
        return cached["value"]

    ports = {origin: port_locations.get(origin), destination: port_locations.get(destination)}
    jobs = {}
    for port_name, details in ports.items():
        if details:
            jobs[f"weather_{port_name}"] = lambda p=port_name, d=details: get_weather(p, d["coordinates"])
            jobs[f"traffic_{port_name}"] = lambda p=port_name, d=details: get_traffic(p, d["coordinates"])
        jobs[f"congestion_{port_name}"] = lambda p=port_name: get_port_congestion(p)
    jobs["geopolitics"] = lambda: get_geopolitical_signal(origin, destination)

    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as executor:
        results = dict(zip(jobs, executor.map(lambda job: _safe_call("live provider", job), jobs.values())))

    weather_values = [value for key, value in results.items() if key.startswith("weather_") and value.get("available")]
    categories = [value.get("category") for value in weather_values]
    weather_priority = {"Clear": 0, "Rain": 1, "Fog": 2, "Storm": 3, "Hurricane": 4}
    weather_category = max(categories, key=lambda category: weather_priority.get(category, 0)) if categories else None

    value = {
        "enabled": True,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "route": {"origin": origin, "destination": destination},
        "weather": {
            "category": weather_category,
            "ports": {key.removeprefix("weather_"): item for key, item in results.items() if key.startswith("weather_")},
        },
        "traffic": {key.removeprefix("traffic_"): item for key, item in results.items() if key.startswith("traffic_")},
        "port_congestion": {key.removeprefix("congestion_"): item for key, item in results.items() if key.startswith("congestion_")},
        "geopolitics": results["geopolitics"],
    }
    _CACHE[cache_key] = {"cached_at": time.time(), "value": value}
    return value
