import os
from datetime import date
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import pandas as pd
import joblib
from geopy.distance import geodesic
from .auth_db import (
    consume_reset_token,
    create_reset_token,
    ensure_admin_user,
    update_password,
    verify_user,
)
from .live_data import get_live_context

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-development-secret-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
ensure_admin_user(ADMIN_USERNAME, ADMIN_PASSWORD)

# --------------------------------------------------
# PATHS & CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "best_model.pkl"
TRAIN_PATH = ROOT / "data" / "processed" / "train.csv"
CONNECTIVITY_PATH = ROOT / "data" / "raw" / "route_connectivity_195_completed.csv"

PORT_LOCATIONS = {
    "Antwerp": {"country": "Belgium", "coordinates": (51.2194, 4.4025)},
    "Busan": {"country": "South Korea", "coordinates": (35.1796, 129.0756)},
    "Dubai": {"country": "United Arab Emirates", "coordinates": (25.2048, 55.2708)},
    "Hamburg": {"country": "Germany", "coordinates": (53.5511, 9.9937)},
    "Los Angeles": {"country": "United States", "coordinates": (33.7701, -118.1937)},
    "Marseille": {"country": "France", "coordinates": (43.2965, 5.3698)},
    "Rotterdam": {"country": "Netherlands", "coordinates": (51.9244, 4.4777)},
    "Shanghai": {"country": "China", "coordinates": (31.2304, 121.4737)},
    "Singapore": {"country": "Singapore", "coordinates": (1.3521, 103.8198)},
    "Sri Lanka": {"country": "Sri Lanka", "coordinates": (6.9271, 79.8612)},
    "India": {"country": "India", "coordinates": (19.0760, 72.8777)},
}

# --------------------------------------------------
# DATA & MODEL LOADING
# --------------------------------------------------

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

model = joblib.load(MODEL_PATH)

if not TRAIN_PATH.exists():
    raise FileNotFoundError(f"Training data not found at {TRAIN_PATH}")

train_df = pd.read_csv(TRAIN_PATH)
feature_names = [col for col in train_df.columns if col != "disruption"]

connectivity_df = None
if CONNECTIVITY_PATH.exists():
    connectivity_df = pd.read_csv(CONNECTIVITY_PATH)

# Build feature metadata (types, defaults, min/max, options)
FEATURE_METADATA = {}
for col in feature_names:
    if col == "date":
        continue
    series = train_df[col]
    if pd.api.types.is_numeric_dtype(series):
        num_s = pd.to_numeric(series, errors="coerce")
        FEATURE_METADATA[col] = {
            "type": "numeric",
            "min": float(num_s.min()) if not pd.isna(num_s.min()) else 0.0,
            "max": float(num_s.max()) if not pd.isna(num_s.max()) else 100.0,
            "median": float(num_s.median()) if not pd.isna(num_s.median()) else 0.0,
            "step": 0.01 if (num_s.max() - num_s.min()) < 100 else 1.0,
        }
    else:
        options = sorted(series.dropna().astype(str).unique().tolist())
        if col in {"origin_port", "destination_port"}:
            options = sorted(set(options) | set(PORT_LOCATIONS.keys()))
        FEATURE_METADATA[col] = {
            "type": "categorical",
            "options": options,
            "default": options[0] if options else "",
        }


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

@app.before_request
def require_login():
    if request.endpoint in {"login", "forgot_password", "reset_password", "health", "static"}:
        return None
    if session.get("authenticated"):
        return None
    if request.path.startswith("/api/"):
        return jsonify({"error": "Authentication required."}), 401
    return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if verify_user(username, password):
            session.clear()
            session["authenticated"] = True
            session["username"] = username
            next_url = request.form.get("next", "/")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = "/"
            return redirect(next_url)
        error = "Invalid username or password."

    return render_template("login.html", error=error, next_url=request.args.get("next", "/"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    error = None
    success = None
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        username = session.get("username", "")

        if not verify_user(username, current_password):
            error = "Your current password is incorrect."
        elif len(new_password) < 8:
            error = "The new password must contain at least 8 characters."
        elif new_password != confirm_password:
            error = "The new passwords do not match."
        else:
            update_password(username, new_password)
            success = "Your password has been changed successfully."

    return render_template("change_password.html", error=error, success=success)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    reset_url = None
    message = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        token = create_reset_token(username)
        message = "If that account exists, a password-reset link has been created."
        if token:
            reset_url = url_for("reset_password", token=token, _external=True)
    return render_template("forgot_password.html", message=message, reset_url=reset_url)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    error = None
    success = None
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if len(new_password) < 8:
            error = "The new password must contain at least 8 characters."
        elif new_password != confirm_password:
            error = "The new passwords do not match."
        elif consume_reset_token(token, new_password):
            success = "Password reset successfully. You can now sign in."
        else:
            error = "This reset link is invalid or expired."
    return render_template("reset_password.html", token=token, error=error, success=success)

def get_route_connectivity(origin_port, destination_port):
    """
    Evaluates physical cross-border connectivity.
    Returns:
        is_same (bool)
        mode_status (dict of mode: bool)
        allowed_modes (list of str)
        unavailable_modes (list of str)
    """
    all_modes = ["Air", "Rail", "Road", "Sea"]
    default_status = {"Sea": True, "Air": True, "Road": True, "Rail": True}

    if not origin_port or not destination_port:
        return False, default_status, all_modes, []

    if origin_port.strip().lower() == destination_port.strip().lower():
        return True, {m: False for m in all_modes}, [], all_modes

    orig_country = PORT_LOCATIONS.get(origin_port, {}).get("country", origin_port).strip()
    dest_country = PORT_LOCATIONS.get(destination_port, {}).get("country", destination_port).strip()

    # Domestic shipment within the same country
    if orig_country.lower() == dest_country.lower():
        return False, default_status, all_modes, []

    if connectivity_df is not None:
        match = connectivity_df[
            (connectivity_df["origin"].str.strip().str.lower() == orig_country.lower()) &
            (connectivity_df["destination"].str.strip().str.lower() == dest_country.lower())
        ]
        if not match.empty:
            row = match.iloc[0]
            status = {
                "Sea": bool(row.get("sea", 0) == 1),
                "Air": bool(row.get("air", 0) == 1),
                "Road": bool(row.get("road", 0) == 1),
                "Rail": bool(row.get("railway", 0) == 1),
            }
            allowed = [m for m in all_modes if status.get(m, False)]
            if not allowed:
                allowed = ["Air"]
            unavailable = [m for m in all_modes if not status.get(m, False)]
            return False, status, allowed, unavailable

    return False, default_status, all_modes, []


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/")
def index():
    latest_training_date = "2025-12-31"
    if "date" in train_df.columns:
        dt = pd.to_datetime(train_df["date"], errors="coerce").max()
        if not pd.isna(dt):
            latest_training_date = dt.date().isoformat()

    all_ports = sorted(
        set(train_df["origin_port"].dropna().astype(str).unique())
        | set(train_df["destination_port"].dropna().astype(str).unique())
        | set(PORT_LOCATIONS.keys())
    )

    default_origin = "Sri Lanka" if "Sri Lanka" in all_ports else all_ports[0]
    default_dest = "India" if "India" in all_ports else (all_ports[1] if len(all_ports) > 1 else all_ports[0])

    return render_template(
        "index.html",
        active_page="predictor",
        ports=all_ports,
        default_origin=default_origin,
        default_destination=default_dest,
        today_date=date.today().isoformat(),
        latest_training_date=latest_training_date,
        feature_metadata=FEATURE_METADATA,
        port_locations={k: {"country": v["country"], "coordinates": list(v["coordinates"])} for k, v in PORT_LOCATIONS.items()}
    )


# --------------------------------------------------
# DYNAMIC SIMULATION & VISUALIZATION ENGINE
# --------------------------------------------------

def generate_dynamic_visualizations(input_row, base_prob, allowed_modes):
    """
    Generates dynamic what-if simulation data and multi-factor radar metrics
    tailored specifically to the given input row and corridor.
    """
    all_modes = ["Air", "Rail", "Road", "Sea"]
    mode_sim_labels = []
    mode_sim_probs = []
    mode_sim_feasible = []
    mode_sim_is_current = []

    current_mode = str(input_row.get("transport_mode", "Sea"))
    for m in all_modes:
        row_copy = input_row.copy()
        row_copy["transport_mode"] = m
        try:
            m_df = pd.DataFrame([row_copy])[feature_names]
            m_prob = float(model.predict_proba(m_df)[0][1])
        except Exception:
            m_prob = base_prob

        is_feas = bool(m in allowed_modes)
        mode_sim_labels.append(m)
        mode_sim_probs.append(round(m_prob * 100, 1))
        mode_sim_feasible.append(is_feas)
        mode_sim_is_current.append(bool(m == current_mode))

    # 2. What-if Weather Stress-Test
    all_weathers = ["Clear", "Rain", "Fog", "Storm", "Hurricane"]
    weather_sim_labels = []
    weather_sim_probs = []
    weather_sim_is_current = []

    current_weather = str(input_row.get("weather_condition", "Clear"))
    for w in all_weathers:
        row_copy = input_row.copy()
        row_copy["weather_condition"] = w
        try:
            w_df = pd.DataFrame([row_copy])[feature_names]
            w_prob = float(model.predict_proba(w_df)[0][1])
        except Exception:
            w_prob = base_prob

        weather_sim_labels.append(w)
        weather_sim_probs.append(round(w_prob * 100, 1))
        weather_sim_is_current.append(bool(w == current_weather))

    # 3. 6-Axis Multi-Factor Risk Radar Profile (Normalized 0 - 100%)
    w_scores = {"Clear": 12, "Rain": 38, "Fog": 55, "Storm": 88, "Hurricane": 100}
    w_radar = w_scores.get(current_weather, 25)

    geo_val = float(input_row.get("geopolitical_risk_score", 1.0))
    geo_radar = min(100, max(0, round((geo_val / 5.0) * 100, 1)))

    rel_val = float(input_row.get("carrier_reliability_score", 0.9))
    carrier_deficit = min(100, max(0, round((1.0 - rel_val) * 100, 1)))

    lt_val = float(input_row.get("lead_time_days", 5))
    lt_radar = min(100, max(10, round(100 - (lt_val / 30.0 * 80), 1)))

    dist_val = float(input_row.get("distance_km", 1500))
    dist_radar = min(100, max(10, round((dist_val / 12000.0) * 100, 1)))

    cat = str(input_row.get("product_category", "Electronics"))
    cat_sens = {
        "Pharmaceuticals": 90,
        "Perishables": 85,
        "Electronics": 70,
        "Automotive": 60,
        "Textiles": 45,
        "Consumer Goods": 40
    }
    cargo_radar = cat_sens.get(cat, 50)

    radar_profile = {
        "labels": ["Weather Threat", "Geopolitical Tension", "Carrier Deficit", "Lead Time Pressure", "Distance Arc", "Cargo Sensitivity"],
        "shipment_scores": [w_radar, geo_radar, carrier_deficit, lt_radar, dist_radar, cargo_radar],
        "safe_baseline": [20, 20, 15, 25, 25, 30]
    }

    # 4. Transit Timeline & Buffer Waterfall
    lead_days = int(float(input_row.get("lead_time_days", 5)))
    if base_prob >= 0.50:
        delay_min = max(2, int(lead_days * 0.4))
        delay_max = delay_min + 3
    else:
        delay_min = 0
        delay_max = 1

    delay_waterfall = {
        "scheduled_days": lead_days,
        "delay_min": delay_min,
        "delay_max": delay_max,
        "total_transit_min": lead_days + delay_min,
        "total_transit_max": lead_days + delay_max
    }

    # 5. Speedometer Gauge Data
    gauge_data = {
        "disruption_prob": round(base_prob * 100, 1),
        "ontime_prob": round((1.0 - base_prob) * 100, 1),
        "risk_level": "Critical" if base_prob >= 0.7 else ("High" if base_prob >= 0.5 else ("Moderate" if base_prob >= 0.35 else "Low"))
    }

    return {
        "mode_simulation": {
            "labels": mode_sim_labels,
            "probabilities": mode_sim_probs,
            "feasible": mode_sim_feasible,
            "is_current": mode_sim_is_current
        },
        "weather_simulation": {
            "labels": weather_sim_labels,
            "probabilities": weather_sim_probs,
            "is_current": weather_sim_is_current
        },
        "radar_profile": radar_profile,
        "delay_waterfall": delay_waterfall,
        "gauge": gauge_data
    }


def run_full_prediction(payload):
    if not payload:
        return {"error": "Invalid JSON payload."}, 400

    origin = payload.get("origin_port", "").strip()
    destination = payload.get("destination_port", "").strip()
    mode = payload.get("transport_mode", "").strip()

    if not origin or not destination:
        return {"error": "Origin and destination ports are required."}, 400

    if origin.lower() == destination.lower():
        return {"error": "Origin and destination cannot be identical locations."}, 400

    is_same, mode_status, allowed_modes, unavailable = get_route_connectivity(origin, destination)

    if not mode and allowed_modes:
        mode = allowed_modes[0]

    if mode not in allowed_modes:
        return {
            "error": f"Physical Route Infeasible: Transport mode '{mode}' cannot connect {origin} and {destination} directly. Allowed modes: {', '.join(allowed_modes)}."
        }, 400

    # Build input row matching exact feature names
    input_row = {}
    for col in feature_names:
        if col in payload:
            val = payload[col]
            if col in FEATURE_METADATA and FEATURE_METADATA[col]["type"] == "numeric":
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = FEATURE_METADATA[col]["median"]
            input_row[col] = val
        else:
            if col in FEATURE_METADATA:
                input_row[col] = FEATURE_METADATA[col].get("median", FEATURE_METADATA[col].get("default", ""))
            elif col == "date":
                input_row[col] = date.today().isoformat()
            else:
                input_row[col] = ""

    live_context = None
    if payload.get("use_live_data", True):
        live_context = get_live_context(origin, destination, PORT_LOCATIONS)
        live_weather = live_context.get("weather", {}).get("category")
        weather_options = FEATURE_METADATA.get("weather_condition", {}).get("options", [])
        if live_weather in weather_options:
            input_row["weather_condition"] = live_weather

        live_geo = live_context.get("geopolitics", {})
        if live_geo.get("available") and "news_attention_score" in live_geo:
            input_row["geopolitical_risk_score"] = float(live_geo["news_attention_score"])

    input_df = pd.DataFrame([input_row])[feature_names]

    try:
        prediction = int(model.predict(input_df)[0])
        probability = float(model.predict_proba(input_df)[0][1])
        no_disruption_prob = 1.0 - probability

        # Detailed Risk Classification
        if probability >= 0.70:
            risk_level = "Critical"
            risk_badge = "CRITICAL DISRUPTION RISK"
        elif probability >= 0.50:
            risk_level = "High"
            risk_badge = "ELEVATED RISK"
        elif probability >= 0.35:
            risk_level = "Moderate"
            risk_badge = "MODERATE RISK"
        else:
            risk_level = "Low"
            risk_badge = "OPTIMAL TRANSIT (LOW RISK)"

        from datetime import datetime, timedelta
        ship_date_str = str(input_row.get("date", date.today().isoformat()))
        try:
            ship_date = datetime.fromisoformat(ship_date_str)
        except Exception:
            ship_date = datetime.now()

        lead_days = int(float(input_row.get("lead_time_days", 5)))
        weather = str(input_row.get("weather_condition", "Clear"))
        geo_score = float(input_row.get("geopolitical_risk_score", 1.0))
        carrier_score = float(input_row.get("carrier_reliability_score", 0.9))

        if prediction == 1:
            delay_min = max(2, int(lead_days * 0.4))
            delay_max = delay_min + 3
            delay_variance = f"+{delay_min} to +{delay_max} Days Buffer"
            arrival_start = (ship_date + timedelta(days=lead_days + delay_min)).strftime("%b %d, %Y")
            arrival_end = (ship_date + timedelta(days=lead_days + delay_max)).strftime("%b %d, %Y")
            delivery_window = f"{arrival_start} - {arrival_end}"

            recommendations = [
                f"Incorporate a +{delay_min}-{delay_max} business days safety stock buffer for downstream manufacturing.",
                "Activate secondary carrier backup or split consignment across sailings to mitigate bottleneck risk.",
                "Initiate active GPS/IoT container tracking telemetry for real-time monitoring across transit waypoints.",
                "Pre-clear customs documentation in advance to prevent port-side processing delays."
            ]
        else:
            delay_variance = "On-Schedule (+/- 0-1 Day)"
            arrival_start = (ship_date + timedelta(days=lead_days)).strftime("%b %d, %Y")
            arrival_end = (ship_date + timedelta(days=lead_days + 1)).strftime("%b %d, %Y")
            delivery_window = f"{arrival_start} - {arrival_end}"

            recommendations = [
                "Proceed with primary carrier booking under standard SLA terms.",
                "Corridor parameters and carrier reliability scores support smooth transit execution.",
                "Maintain standard shipping visibility and automated milestone notifications."
            ]

        weather_impact = "Severe Threat" if weather in ["Hurricane", "Storm"] else ("Elevated" if weather in ["Fog", "Rain"] else "Favorable")
        geo_impact = "High Instability" if geo_score >= 3.5 else ("Moderate Caution" if geo_score >= 2.0 else "Stable Region")
        carrier_status = "Optimal (High Reliability)" if carrier_score >= 0.85 else ("Suboptimal (Monitoring Needed)" if carrier_score >= 0.70 else "At-Risk Carrier")

        factors = {
            "weather": {
                "label": "Weather Vulnerability",
                "value": weather,
                "status": weather_impact,
                "is_risk": weather in ["Hurricane", "Storm", "Fog"]
            },
            "geopolitics": {
                "label": "Geopolitical Index",
                "value": f"{geo_score:.1f} / 5.0",
                "status": geo_impact,
                "is_risk": geo_score >= 2.5
            },
            "carrier": {
                "label": "Carrier Reliability",
                "value": f"{carrier_score * 100:.0f}%",
                "status": carrier_status,
                "is_risk": carrier_score < 0.80
            },
            "lead_time": {
                "label": "Scheduled Lead Time",
                "value": f"{lead_days} Days",
                "status": "Tight Tolerance" if lead_days <= 3 else "Standard Window",
                "is_risk": lead_days <= 3
            }
        }

        confidence = max(probability, no_disruption_prob)

        # Generate Dynamic Visualizations & Simulations
        visualizations = generate_dynamic_visualizations(input_row, probability, allowed_modes)

        return {
            "success": True,
            "prediction": prediction,
            "prediction_label": "Disruption Likely" if prediction == 1 else "No Disruption (On-Schedule)",
            "disruption_probability": round(probability, 4),
            "no_disruption_probability": round(no_disruption_prob, 4),
            "disruption_percent": f"{probability:.2%}",
            "no_disruption_percent": f"{no_disruption_prob:.2%}",
            "confidence_percent": f"{confidence:.1%}",
            "risk_level": risk_level,
            "risk_badge": risk_badge,
            "delay_variance": delay_variance,
            "delivery_window": delivery_window,
            "factors": factors,
            "recommendations": recommendations,
            "telemetry": {
                "route": f"{origin} ➔ {destination}",
                "mode": mode,
                "distance_km": f"{float(input_row.get('distance_km', 0)):,.0f} km",
                "product_category": input_row.get("product_category"),
                "weight_mt": f"{float(input_row.get('weight_mt', 0)):,.1f} MT",
                "scheduled_date": ship_date.strftime("%b %d, %Y")
            },
            "visualizations": visualizations,
            "inputs": {
                "origin_port": origin,
                "destination_port": destination,
                "transport_mode": mode,
                "weather_condition": weather,
                "product_category": input_row.get("product_category"),
                "distance_km": float(input_row.get("distance_km", 0)),
                "weight_mt": float(input_row.get("weight_mt", 0)),
                "lead_time_days": lead_days,
                "carrier_reliability_score": carrier_score,
                "geopolitical_risk_score": geo_score,
                "date": ship_date_str
            },
            "live_context": live_context
        }, 200

    except Exception as e:
        return {"error": f"Model inference error: {str(e)}"}, 500


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/analytics", methods=["GET"])
def analytics_view():
    all_ports = sorted(
        set(train_df["origin_port"].dropna().astype(str).unique())
        | set(train_df["destination_port"].dropna().astype(str).unique())
        | set(PORT_LOCATIONS.keys())
    )

    default_origin = "Sri Lanka" if "Sri Lanka" in all_ports else all_ports[0]
    default_dest = "India" if "India" in all_ports else (all_ports[1] if len(all_ports) > 1 else all_ports[0])

    default_payload = {
        "origin_port": default_origin,
        "destination_port": default_dest,
        "transport_mode": "Sea",
        "weather_condition": "Clear",
        "product_category": "Electronics",
        "distance_km": 1542,
        "weight_mt": 500,
        "lead_time_days": 5,
        "carrier_reliability_score": 0.90,
        "geopolitical_risk_score": 2.0,
        "date": date.today().isoformat()
    }
    default_prediction, _ = run_full_prediction(default_payload)

    return render_template(
        "analytics.html",
        active_page="analytics",
        ports=all_ports,
        default_origin=default_origin,
        default_destination=default_dest,
        today_date=date.today().isoformat(),
        feature_metadata=FEATURE_METADATA,
        port_locations={k: {"country": v["country"], "coordinates": list(v["coordinates"])} for k, v in PORT_LOCATIONS.items()},
        initial_prediction=default_prediction
    )


@app.route("/api/route-info", methods=["GET"])
def route_info():
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()

    if not origin or not destination:
        return jsonify({"error": "Missing origin or destination"}), 400

    is_same, mode_status, allowed_modes, unavailable_modes = get_route_connectivity(origin, destination)

    distance_km = None
    orig_coords = None
    dest_coords = None

    if origin in PORT_LOCATIONS and destination in PORT_LOCATIONS and not is_same:
        orig_coords = list(PORT_LOCATIONS[origin]["coordinates"])
        dest_coords = list(PORT_LOCATIONS[destination]["coordinates"])
        distance_km = round(geodesic(orig_coords, dest_coords).km, 1)

    return jsonify({
        "is_same": is_same,
        "origin": {
            "name": origin,
            "country": PORT_LOCATIONS.get(origin, {}).get("country", origin),
            "coordinates": orig_coords
        },
        "destination": {
            "name": destination,
            "country": PORT_LOCATIONS.get(destination, {}).get("country", destination),
            "coordinates": dest_coords
        },
        "distance_km": distance_km,
        "mode_status": mode_status,
        "allowed_modes": allowed_modes,
        "unavailable_modes": unavailable_modes
    })


@app.route("/api/live-context", methods=["GET"])
def live_context():
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()

    if not origin or not destination:
        return jsonify({"error": "Missing origin or destination"}), 400

    return jsonify(get_live_context(origin, destination, PORT_LOCATIONS))


@app.route("/api/predict", methods=["POST"])
def predict():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Invalid JSON body"}), 400
    res, status_code = run_full_prediction(payload)
    return jsonify(res), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

