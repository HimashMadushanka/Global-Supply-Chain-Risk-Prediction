/**
 * SupplyChain.AI - Executive Dashboard Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // Navigation elements
  const navOriginText = document.getElementById('navOriginText');
  const navDestText = document.getElementById('navDestText');
  const navModeText = document.getElementById('navModeText');

  // Form & Route Selection Elements
  const originSelect = document.getElementById('origin_port');
  const destSelect = document.getElementById('destination_port');
  const modeSelect = document.getElementById('transport_mode');
  const allowedCountBadge = document.getElementById('allowedCountBadge');

  const sameLocationAlert = document.getElementById('sameLocationAlert');
  const blockedModesAlert = document.getElementById('blockedModesAlert');

  // Feasibility Badges
  const badgeSea = document.getElementById('badgeSea');
  const badgeAir = document.getElementById('badgeAir');
  const badgeRoad = document.getElementById('badgeRoad');
  const badgeRail = document.getElementById('badgeRail');

  const statusSea = document.getElementById('statusSea');
  const statusAir = document.getElementById('statusAir');
  const statusRoad = document.getElementById('statusRoad');
  const statusRail = document.getElementById('statusRail');

  // Parameters & Sync
  const distanceInput = document.getElementById('distance_km');
  const btnSyncMapDist = document.getElementById('btnSyncMapDist');
  const predictBtn = document.getElementById('predictBtn');
  const btnSpinner = document.getElementById('btnSpinner');
  const btnLabel = document.getElementById('btnLabel');
  const predictionForm = document.getElementById('predictionForm');

  // Map & Legend Elements
  const distMetricVal = document.getElementById('distMetricVal');
  const mapLegendOrigin = document.getElementById('mapLegendOrigin');
  const mapLegendDest = document.getElementById('mapLegendDest');
  const mapLegendArc = document.getElementById('mapLegendArc');

  // Report Workspace Elements
  const reportMetaTag = document.getElementById('reportMetaTag');
  const reportIdleState = document.getElementById('reportIdleState');
  const reportEvaluatedState = document.getElementById('reportEvaluatedState');

  const outcomeHeroBanner = document.getElementById('outcomeHeroBanner');
  const statusRiskPill = document.getElementById('statusRiskPill');
  const confidenceBadge = document.getElementById('confidenceBadge');
  const probLargeNumber = document.getElementById('probLargeNumber');
  const meterFill = document.getElementById('meterFill');
  const statDisruptProb = document.getElementById('statDisruptProb');
  const statOnTimeProb = document.getElementById('statOnTimeProb');
  const outcomeHeadline = document.getElementById('outcomeHeadline');
  const outcomeSubtext = document.getElementById('outcomeSubtext');

  const valDelayVariance = document.getElementById('valDelayVariance');
  const valDeliveryWindow = document.getElementById('valDeliveryWindow');

  // Factors
  const cardWeather = document.getElementById('cardWeather');
  const valWeather = document.getElementById('valWeather');
  const statusWeather = document.getElementById('statusWeather');

  const cardGeopolitics = document.getElementById('cardGeopolitics');
  const valGeopolitics = document.getElementById('valGeopolitics');
  const statusGeopolitics = document.getElementById('statusGeopolitics');

  const cardCarrier = document.getElementById('cardCarrier');
  const valCarrier = document.getElementById('valCarrier');
  const statusCarrier = document.getElementById('statusCarrier');

  const cardLeadTime = document.getElementById('cardLeadTime');
  const valLeadTime = document.getElementById('valLeadTime');
  const statusLeadTime = document.getElementById('statusLeadTime');

  const recommendationsList = document.getElementById('recommendationsList');

  // Leaflet Map Variables
  let map = null;
  let originMarker = null;
  let destMarker = null;
  let routePolyline = null;
  let currentDistanceKm = null;

  // Initialize Map with Clear Color CartoDB Voyager Tiles
  function initMap() {
    map = L.map('routeMap', {
      center: [15, 78],
      zoom: 3,
      minZoom: 2,
      maxZoom: 18,
      worldCopyJump: true,
      zoomControl: true
    });

    // Clear colorful Voyager tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(map);

    setTimeout(() => {
      map.invalidateSize();
    }, 200);
  }

  initMap();

  // Custom Colorful Map Marker Icons
  function makeMarker(color, label) {
    return L.divIcon({
      className: 'pro-map-pin',
      html: `<div style="
        background-color: ${color};
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 13px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.5);
        border: 2.5px solid #ffffff;
      ">${label}</div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
      popupAnchor: [0, -16]
    });
  }

  const originPin = makeMarker('#10b981', 'A');
  const destPin = makeMarker('#ef4444', 'B');

  // Fetch Route Connectivity & Feasibility Info
  async function fetchRouteInfo() {
    const origin = originSelect.value;
    const destination = destSelect.value;

    if (!origin || !destination) return;

    // Update Top Corridor Text
    if (navOriginText) navOriginText.textContent = origin;
    if (navDestText) navDestText.textContent = destination;
    if (mapLegendOrigin) mapLegendOrigin.textContent = origin;
    if (mapLegendDest) mapLegendDest.textContent = destination;

    // Check same location
    if (origin.toLowerCase() === destination.toLowerCase()) {
      sameLocationAlert.style.display = 'flex';
      predictBtn.disabled = true;
      modeSelect.innerHTML = '<option value="">(Infeasible: Same Location)</option>';
      modeSelect.disabled = true;
      blockedModesAlert.style.display = 'none';
      if (allowedCountBadge) allowedCountBadge.textContent = '(0 allowed)';
      if (distMetricVal) distMetricVal.textContent = '0 km';
      resetFeasibility();
      return;
    }

    sameLocationAlert.style.display = 'none';
    predictBtn.disabled = false;
    modeSelect.disabled = false;

    try {
      const res = await fetch(`/api/route-info?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`);
      const data = await res.json();

      if (!res.ok) {
        console.error(data.error);
        return;
      }

      currentDistanceKm = data.distance_km;

      // Distance Metric
      if (data.distance_km !== null) {
        if (distMetricVal) distMetricVal.textContent = `${data.distance_km.toLocaleString()} km`;
        if (distanceInput && (!distanceInput.dataset.userChanged || distanceInput.dataset.userChanged === 'false')) {
          distanceInput.value = data.distance_km;
        }
      } else {
        if (distMetricVal) distMetricVal.textContent = 'N/A';
      }

      // Update Feasibility Badges
      updateBadge(badgeSea, statusSea, 'Sea Freight', data.mode_status.Sea);
      updateBadge(badgeAir, statusAir, 'Air Cargo', data.mode_status.Air);
      updateBadge(badgeRoad, statusRoad, 'Road Transit', data.mode_status.Road, 'No Road Link');
      updateBadge(badgeRail, statusRail, 'Rail Freight', data.mode_status.Rail, 'No Rail Link');

      // Populate Transport Modes
      const prevSelected = modeSelect.value;
      modeSelect.innerHTML = '';

      data.allowed_modes.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = `${getIcon(m)} ${m}`;
        if (m === prevSelected) opt.selected = true;
        modeSelect.appendChild(opt);
      });

      if (!data.allowed_modes.includes(prevSelected) && data.allowed_modes.length > 0) {
        modeSelect.value = data.allowed_modes[0];
      }

      if (allowedCountBadge) {
        allowedCountBadge.textContent = `(${data.allowed_modes.length} allowed)`;
      }

      updateSelectedModeHighlight();

      // Show Blocked Warning (e.g. Sri Lanka to India)
      if (data.unavailable_modes && data.unavailable_modes.length > 0) {
        blockedModesAlert.style.display = 'flex';
        blockedModesAlert.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
          <span><strong>${data.unavailable_modes.join(', ')}</strong> cannot connect ${origin} and ${destination} directly (no overland physical road/rail connection).</span>
        `;
      } else {
        blockedModesAlert.style.display = 'none';
      }

      // Draw Map Route
      drawMapRoute(data.origin, data.destination, data.distance_km);

    } catch (err) {
      console.error("Error loading route connectivity:", err);
    }
  }

  function getIcon(mode) {
    switch (mode) {
      case 'Sea': return '🚢';
      case 'Air': return '✈️';
      case 'Road': return '🚚';
      case 'Rail': return '🚆';
      default: return '📦';
    }
  }

  function updateBadge(badgeElem, statusElem, name, isAvailable, blockedText = 'No Link') {
    if (!badgeElem || !statusElem) return;
    if (isAvailable) {
      badgeElem.className = 'f-badge f-available';
      statusElem.textContent = 'Available';
    } else {
      badgeElem.className = 'f-badge f-blocked';
      statusElem.textContent = blockedText;
    }
  }

  function resetFeasibility() {
    [badgeSea, badgeAir, badgeRoad, badgeRail].forEach(b => {
      if (b) b.className = 'f-badge f-blocked';
    });
    [statusSea, statusAir, statusRoad, statusRail].forEach(s => {
      if (s) s.textContent = 'Unavailable';
    });
  }

  function updateSelectedModeHighlight() {
    const selected = modeSelect.value;
    if (navModeText) {
      navModeText.textContent = selected ? `(${selected} Freight)` : '';
    }
    if (mapLegendArc) {
      mapLegendArc.textContent = selected ? `${selected} Arc` : 'Connecting Arc';
    }

    [
      { badge: badgeSea, mode: 'Sea' },
      { badge: badgeAir, mode: 'Air' },
      { badge: badgeRoad, mode: 'Road' },
      { badge: badgeRail, mode: 'Rail' }
    ].forEach(({ badge, mode }) => {
      if (badge) {
        if (mode === selected) {
          badge.classList.add('is-selected');
        } else {
          badge.classList.remove('is-selected');
        }
      }
    });
  }

  function drawMapRoute(orig, dest, distance) {
    if (!map) return;

    if (originMarker) map.removeLayer(originMarker);
    if (destMarker) map.removeLayer(destMarker);
    if (routePolyline) map.removeLayer(routePolyline);

    if (!orig.coordinates || !dest.coordinates) return;

    const origLatLng = [orig.coordinates[0], orig.coordinates[1]];
    const destLatLng = [dest.coordinates[0], dest.coordinates[1]];

    // Add Green Origin Pin
    originMarker = L.marker(origLatLng, { icon: originPin })
      .bindTooltip(`<strong>Origin Port:</strong> ${orig.name}, ${orig.country}`, { permanent: false, direction: 'top' })
      .addTo(map);

    // Add Red Destination Pin
    destMarker = L.marker(destLatLng, { icon: destPin })
      .bindTooltip(`<strong>Destination Port:</strong> ${dest.name}, ${dest.country}`, { permanent: false, direction: 'top' })
      .addTo(map);

    // Draw Bright Route Polyline
    routePolyline = L.polyline([origLatLng, destLatLng], {
      color: '#2563eb',
      weight: 5,
      opacity: 0.9,
      dashArray: modeSelect.value === 'Air' ? '8, 8' : null
    }).addTo(map);

    if (distance) {
      routePolyline.bindTooltip(`${modeSelect.value || 'Route'}: ${distance.toLocaleString()} km`, {
        sticky: true
      });
    }

    const bounds = L.latLngBounds([origLatLng, destLatLng]);
    map.fitBounds(bounds, { padding: [45, 45], maxZoom: 6 });
  }

  // Distance sync button
  if (btnSyncMapDist) {
    btnSyncMapDist.addEventListener('click', () => {
      if (currentDistanceKm && distanceInput) {
        distanceInput.value = currentDistanceKm;
        distanceInput.dataset.userChanged = 'false';
      }
    });
  }

  if (distanceInput) {
    distanceInput.addEventListener('input', () => {
      distanceInput.dataset.userChanged = 'true';
    });
  }

  // Event Listeners
  originSelect.addEventListener('change', fetchRouteInfo);
  destSelect.addEventListener('change', fetchRouteInfo);

  modeSelect.addEventListener('change', () => {
    updateSelectedModeHighlight();
    if (routePolyline) {
      routePolyline.setStyle({
        dashArray: modeSelect.value === 'Air' ? '8, 8' : null
      });
    }
  });

  // Handle Form Submission
  predictionForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (originSelect.value.toLowerCase() === destSelect.value.toLowerCase()) {
      alert("Origin and destination ports cannot be the same.");
      return;
    }

    const formData = new FormData(predictionForm);
    const payload = {};
    formData.forEach((val, key) => {
      payload[key] = val;
    });

    // Loading State
    btnSpinner.style.display = 'inline-block';
    btnLabel.textContent = 'Analyzing Risk Telemetry...';
    predictBtn.disabled = true;

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.error || "Prediction request failed.");
        return;
      }

      // Render Comprehensive AI Report
      renderAIReport(data);

    } catch (err) {
      console.error(err);
      alert("Network error submitting prediction.");
    } finally {
      btnSpinner.style.display = 'none';
      btnLabel.textContent = 'Run Disruption Assessment';
      predictBtn.disabled = false;
    }
  });

  function renderAIReport(data) {
    // Hide idle placeholder, reveal evaluated report
    if (reportIdleState) reportIdleState.style.display = 'none';
    if (reportEvaluatedState) reportEvaluatedState.style.display = 'flex';

    if (reportMetaTag) {
      reportMetaTag.innerHTML = `<span>Completed &bull; ${data.risk_level} Risk</span>`;
    }

    const isDisruption = data.prediction === 1;

    // Outcome Hero Banner
    outcomeHeroBanner.className = isDisruption
      ? 'outcome-hero-banner is-disruption'
      : 'outcome-hero-banner is-no-disruption';

    statusRiskPill.textContent = data.risk_badge || (isDisruption ? 'ELEVATED RISK' : 'OPTIMAL TRANSIT');
    confidenceBadge.textContent = `Confidence: ${data.confidence_percent || '--%'}`;
    probLargeNumber.textContent = isDisruption ? data.disruption_percent : data.no_disruption_percent;
    meterFill.style.width = `${data.disruption_probability * 100}%`;

    statDisruptProb.textContent = data.disruption_percent;
    statOnTimeProb.textContent = data.no_disruption_percent;

    if (isDisruption) {
      outcomeHeadline.textContent = `Elevated Disruption Risk (${data.disruption_percent})`;
      outcomeSubtext.textContent = `Model indicates significant probability of logistical latency or bottleneck along the ${data.telemetry ? data.telemetry.route : 'transit corridor'}.`;
    } else {
      outcomeHeadline.textContent = `Optimal Transit Conditions (${data.no_disruption_percent} On-Time)`;
      outcomeSubtext.textContent = `Shipment is projected to arrive on-schedule within contracted service level agreement.`;
    }

    // Delay & Delivery Schedule
    valDelayVariance.textContent = data.delay_variance || '+0 Days';
    valDeliveryWindow.textContent = data.delivery_window || '--';

    // Factors Breakdown
    if (data.factors) {
      // Weather
      if (data.factors.weather) {
        valWeather.textContent = data.factors.weather.value;
        statusWeather.textContent = data.factors.weather.status;
        cardWeather.className = data.factors.weather.is_risk ? 'factor-card is-alert' : 'factor-card';
      }

      // Geopolitics
      if (data.factors.geopolitics) {
        valGeopolitics.textContent = data.factors.geopolitics.value;
        statusGeopolitics.textContent = data.factors.geopolitics.status;
        cardGeopolitics.className = data.factors.geopolitics.is_risk ? 'factor-card is-alert' : 'factor-card';
      }

      // Carrier
      if (data.factors.carrier) {
        valCarrier.textContent = data.factors.carrier.value;
        statusCarrier.textContent = data.factors.carrier.status.split(' ')[0];
        cardCarrier.className = data.factors.carrier.is_risk ? 'factor-card is-alert' : 'factor-card';
      }

      // Lead Time
      if (data.factors.lead_time) {
        valLeadTime.textContent = data.factors.lead_time.value;
        statusLeadTime.textContent = data.factors.lead_time.status;
        cardLeadTime.className = data.factors.lead_time.is_risk ? 'factor-card is-alert' : 'factor-card';
      }
    }

    // Recommendations
    if (recommendationsList && data.recommendations) {
      recommendationsList.innerHTML = '';
      data.recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recommendationsList.appendChild(li);
      });
    }

    // Trigger map resize in case layout expanded
    if (map) {
      setTimeout(() => map.invalidateSize(), 150);
    }
  }

  // Initial load
  fetchRouteInfo();
});
