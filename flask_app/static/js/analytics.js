/**
 * SupplyChain.AI - Dynamic Prediction Analytics & Simulation Controller
 * Powers 5 dynamic, reactive Chart.js visualizations that auto-update
 * whenever shipment data is entered and predict is clicked.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Chart Global Dark Theme Configuration
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.95)';
  Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
  Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
  Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.12)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;

  // DOM Elements - Navigation & Corridor
  const navOriginText = document.getElementById('navOriginText');
  const navDestText = document.getElementById('navDestText');
  const navModeText = document.getElementById('navModeText');
  const syncStatusBadge = document.getElementById('syncStatusBadge');

  // DOM Elements - Form & Inputs
  const simForm = document.getElementById('simForm');
  const originSelect = document.getElementById('origin_port');
  const destSelect = document.getElementById('destination_port');
  const modeSelect = document.getElementById('transport_mode');
  const allowedCountBadge = document.getElementById('allowedCountBadge');
  const weatherSelect = document.getElementById('weather_condition');
  const productSelect = document.getElementById('product_category');
  const leadTimeInput = document.getElementById('lead_time_days');
  const carrierInput = document.getElementById('carrier_reliability_score');
  const geoInput = document.getElementById('geopolitical_risk_score');
  const weightInput = document.getElementById('weight_mt');
  const distanceInput = document.getElementById('distance_km');
  const dateInput = document.getElementById('date');

  const sameLocationAlert = document.getElementById('sameLocationAlert');
  const blockedModesAlert = document.getElementById('blockedModesAlert');
  const simPredictBtn = document.getElementById('simPredictBtn');
  const simSpinner = document.getElementById('simSpinner');
  const simBtnLabel = document.getElementById('simBtnLabel');

  // DOM Elements - KPI Strip
  const kpiDisruptProb = document.getElementById('kpiDisruptProb');
  const kpiProbTag = document.getElementById('kpiProbTag');
  const kpiOnTimeProb = document.getElementById('kpiOnTimeProb');
  const kpiRiskLevel = document.getElementById('kpiRiskLevel');
  const kpiConfidenceBadge = document.getElementById('kpiConfidenceBadge');
  const kpiRiskBadgeText = document.getElementById('kpiRiskBadgeText');
  const kpiDeliveryWindow = document.getElementById('kpiDeliveryWindow');
  const kpiDelayVariance = document.getElementById('kpiDelayVariance');
  const kpiPrimaryBottleneck = document.getElementById('kpiPrimaryBottleneck');
  const kpiBottleneckStatus = document.getElementById('kpiBottleneckStatus');
  const kpiCarrierRating = document.getElementById('kpiCarrierRating');

  // DOM Elements - Chart Center Labels & Notes
  const gaugeRiskBadge = document.getElementById('gaugeRiskBadge');
  const gaugeCenterNumber = document.getElementById('gaugeCenterNumber');
  const gaugeCenterCaption = document.getElementById('gaugeCenterCaption');
  const simRecommendationsList = document.getElementById('simRecommendationsList');

  // Telemetry Chips
  const chipRoute = document.getElementById('chipRoute');
  const chipMode = document.getElementById('chipMode');
  const chipDistance = document.getElementById('chipDistance');
  const chipWeight = document.getElementById('chipWeight');
  const chipDate = document.getElementById('chipDate');

  // Chart Instances
  let gaugeChart = null;
  let radarChart = null;
  let modeSimChart = null;
  let weatherSimChart = null;
  let delayChart = null;

  // --------------------------------------------------
  // 1. INITIALIZE CHART INSTANCES
  // --------------------------------------------------

  // 1.1 Speedometer Gauge (Half-Doughnut)
  function initGaugeChart() {
    const ctx = document.getElementById('gaugeChart');
    if (!ctx) return;

    gaugeChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Disruption Probability', 'On-Time Probability'],
        datasets: [{
          data: [50, 50],
          backgroundColor: ['#f97316', 'rgba(255, 255, 255, 0.08)'],
          borderColor: ['#f97316', 'rgba(255, 255, 255, 0.12)'],
          borderWidth: 1,
          circumference: 180,
          rotation: 270,
          cutout: '76%'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (item) => `${item.label}: ${item.raw}%`
            }
          }
        }
      }
    });
  }

  // 1.2 Multi-Factor 6-Axis Risk Radar
  function initRadarChart() {
    const ctx = document.getElementById('radarChart');
    if (!ctx) return;

    radarChart = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Weather Threat', 'Geopolitical Tension', 'Carrier Deficit', 'Lead Time Pressure', 'Distance Arc', 'Cargo Sensitivity'],
        datasets: [
          {
            label: 'Current Shipment Risk',
            data: [50, 50, 50, 50, 50, 50],
            backgroundColor: 'rgba(56, 189, 248, 0.25)',
            borderColor: '#38bdf8',
            pointBackgroundColor: '#38bdf8',
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: '#38bdf8',
            borderWidth: 2,
            pointRadius: 4
          },
          {
            label: 'Safe Industry Baseline',
            data: [20, 20, 15, 25, 25, 30],
            backgroundColor: 'rgba(16, 185, 129, 0.08)',
            borderColor: '#10b981',
            borderDash: [4, 4],
            pointBackgroundColor: '#10b981',
            pointBorderColor: '#ffffff',
            borderWidth: 1.5,
            pointRadius: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12, padding: 16 }
          }
        },
        scales: {
          r: {
            angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
            grid: { color: 'rgba(255, 255, 255, 0.08)' },
            pointLabels: {
              color: '#cbd5e1',
              font: { size: 11, weight: 600 }
            },
            ticks: {
              backdropColor: 'transparent',
              color: '#64748b',
              stepSize: 20
            },
            suggestedMin: 0,
            suggestedMax: 100
          }
        }
      }
    });
  }

  // 1.3 Modal What-If Simulation Bar Chart
  function initModeSimChart() {
    const ctx = document.getElementById('modeSimChart');
    if (!ctx) return;

    modeSimChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Air', 'Rail', 'Road', 'Sea'],
        datasets: [{
          label: 'Predicted Disruption Risk (%)',
          data: [0, 0, 0, 0],
          backgroundColor: ['#38bdf8', '#818cf8', '#34d399', '#f59e0b'],
          borderColor: ['#38bdf8', '#818cf8', '#34d399', '#f59e0b'],
          borderWidth: 1.5,
          borderRadius: 6,
          barThickness: 34
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Disruption Probability: ${ctx.raw}%`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 105,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { callback: (val) => `${val}%` }
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 1.4 Weather Condition Stress-Test Bar Chart
  function initWeatherSimChart() {
    const ctx = document.getElementById('weatherSimChart');
    if (!ctx) return;

    weatherSimChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Clear', 'Rain', 'Fog', 'Storm', 'Hurricane'],
        datasets: [{
          label: 'Risk Under Weather Shift (%)',
          data: [0, 0, 0, 0, 0],
          backgroundColor: [
            'rgba(16, 185, 129, 0.85)',
            'rgba(14, 165, 233, 0.85)',
            'rgba(234, 179, 8, 0.85)',
            'rgba(249, 115, 22, 0.85)',
            'rgba(239, 68, 68, 0.9)'
          ],
          borderColor: ['#10b981', '#0ea5e9', '#eab308', '#f97316', '#ef4444'],
          borderWidth: 1.5,
          borderRadius: 6,
          barThickness: 30
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Disruption Probability: ${ctx.raw}%`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 105,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { callback: (val) => `${val}%` }
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 1.5 Transit Delay Waterfall Stacked Chart
  function initDelayChart() {
    const ctx = document.getElementById('delayChart');
    if (!ctx) return;

    delayChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Standard Schedule', 'Worst-Case Scenario'],
        datasets: [
          {
            label: 'Contracted Lead Time',
            data: [5, 5],
            backgroundColor: 'rgba(37, 99, 235, 0.85)',
            borderColor: '#2563eb',
            borderWidth: 1.5,
            borderRadius: 6
          },
          {
            label: 'Predicted Delay Buffer',
            data: [0, 4],
            backgroundColor: 'rgba(245, 158, 11, 0.85)',
            borderColor: '#f59e0b',
            borderWidth: 1.5,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.raw} Days`
            }
          }
        },
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: {
            stacked: true,
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { callback: (val) => `${val}d` }
          }
        }
      }
    });
  }

  // Initialize all charts
  initGaugeChart();
  initRadarChart();
  initModeSimChart();
  initWeatherSimChart();
  initDelayChart();

  // --------------------------------------------------
  // 2. DYNAMIC VISUALIZATION UPDATE ENGINE
  // --------------------------------------------------
  function updateAllVisualizations(data) {
    if (!data) return;

    const prob = (data.disruption_probability !== undefined)
      ? data.disruption_probability
      : (parseFloat(data.disruption_percent) / 100 || 0.5);

    const onTimeProb = (data.no_disruption_probability !== undefined)
      ? data.no_disruption_probability
      : (1.0 - prob);

    const probPercent = Math.round(prob * 1000) / 10;
    const onTimePercent = Math.round(onTimeProb * 1000) / 10;
    const isDisruption = data.prediction === 1;

    // 1. Update Top Navbar Corridor
    if (navOriginText && data.inputs && data.inputs.origin_port) navOriginText.textContent = data.inputs.origin_port;
    if (navDestText && data.inputs && data.inputs.destination_port) navDestText.textContent = data.inputs.destination_port;
    if (navModeText && data.inputs && data.inputs.transport_mode) navModeText.textContent = `(${data.inputs.transport_mode} Freight)`;

    // 2. Update KPI Cards
    if (kpiDisruptProb) {
      kpiDisruptProb.textContent = `${probPercent}%`;
      kpiDisruptProb.className = prob >= 0.70 ? 'kpi-number text-danger' : (prob >= 0.50 ? 'kpi-number text-orange' : (prob >= 0.35 ? 'kpi-number text-cyan' : 'kpi-number text-green'));
    }

    if (kpiProbTag) {
      kpiProbTag.textContent = prob >= 0.70 ? 'Critical Threat' : (prob >= 0.50 ? 'Elevated Vulnerability' : (prob >= 0.35 ? 'Moderate Caution' : 'Optimal Path'));
      kpiProbTag.className = prob >= 0.50 ? 'trend-alert' : 'trend-positive';
    }

    if (kpiOnTimeProb) kpiOnTimeProb.textContent = `${onTimePercent}% On-Time Probability`;

    if (kpiRiskLevel) {
      kpiRiskLevel.textContent = `${data.risk_level || (prob >= 0.5 ? 'High' : 'Low')} Risk`;
      kpiRiskLevel.className = prob >= 0.70 ? 'kpi-number text-danger' : (prob >= 0.50 ? 'kpi-number text-orange' : 'kpi-number text-green');
    }

    if (kpiConfidenceBadge) kpiConfidenceBadge.textContent = `Confidence: ${data.confidence_percent || '94.2%'}`;
    if (kpiRiskBadgeText) kpiRiskBadgeText.textContent = data.risk_badge || (isDisruption ? 'ELEVATED RISK' : 'OPTIMAL TRANSIT');

    if (kpiDeliveryWindow) kpiDeliveryWindow.textContent = data.delivery_window || '--';
    if (kpiDelayVariance) kpiDelayVariance.textContent = data.delay_variance || '+0 Days';

    // Primary Bottleneck Driver
    if (kpiPrimaryBottleneck && data.factors) {
      if (data.factors.weather && data.factors.weather.is_risk) {
        kpiPrimaryBottleneck.textContent = `${data.factors.weather.value} Weather`;
        kpiPrimaryBottleneck.className = 'kpi-number text-danger';
        if (kpiBottleneckStatus) {
          kpiBottleneckStatus.textContent = data.factors.weather.status;
          kpiBottleneckStatus.className = 'trend-alert';
        }
      } else if (data.factors.geopolitics && data.factors.geopolitics.is_risk) {
        kpiPrimaryBottleneck.textContent = `Geopolitics: ${data.factors.geopolitics.value}`;
        kpiPrimaryBottleneck.className = 'kpi-number text-orange';
        if (kpiBottleneckStatus) {
          kpiBottleneckStatus.textContent = data.factors.geopolitics.status;
          kpiBottleneckStatus.className = 'trend-alert';
        }
      } else {
        kpiPrimaryBottleneck.textContent = 'Transit Balanced';
        kpiPrimaryBottleneck.className = 'kpi-number text-green';
        if (kpiBottleneckStatus) {
          kpiBottleneckStatus.textContent = 'Stable Parameters';
          kpiBottleneckStatus.className = 'trend-positive';
        }
      }
      if (kpiCarrierRating && data.factors.carrier) {
        kpiCarrierRating.textContent = `Carrier: ${data.factors.carrier.value} (${data.factors.carrier.status})`;
      }
    }

    // 3. Update Gauge Chart
    if (gaugeChart) {
      const gaugeColor = prob >= 0.70 ? '#ef4444' : (prob >= 0.50 ? '#f97316' : (prob >= 0.35 ? '#eab308' : '#10b981'));
      gaugeChart.data.datasets[0].data = [probPercent, onTimePercent];
      gaugeChart.data.datasets[0].backgroundColor = [gaugeColor, 'rgba(255, 255, 255, 0.08)'];
      gaugeChart.data.datasets[0].borderColor = [gaugeColor, 'rgba(255, 255, 255, 0.12)'];
      gaugeChart.update('active');

      if (gaugeCenterNumber) {
        gaugeCenterNumber.textContent = `${probPercent}%`;
        gaugeCenterNumber.style.color = gaugeColor;
      }
      if (gaugeCenterCaption) {
        gaugeCenterCaption.textContent = isDisruption ? 'Disruption Risk' : 'On-Schedule';
      }
      if (gaugeRiskBadge) {
        gaugeRiskBadge.textContent = data.risk_level ? `${data.risk_level} Risk` : 'Live Inference';
      }
    }

    // 4. Update Visualizations Data
    if (data.visualizations) {
      const viz = data.visualizations;

      // Radar Chart
      if (radarChart && viz.radar_profile) {
        radarChart.data.labels = viz.radar_profile.labels;
        radarChart.data.datasets[0].data = viz.radar_profile.shipment_scores;
        radarChart.data.datasets[1].data = viz.radar_profile.safe_baseline;
        radarChart.update('active');
      }

      // Mode Simulation Chart
      if (modeSimChart && viz.mode_simulation) {
        modeSimChart.data.labels = viz.mode_simulation.labels.map((m, i) => {
          const isFeas = viz.mode_simulation.feasible[i];
          const isCurr = viz.mode_simulation.is_current[i];
          return isFeas ? (isCurr ? `⭐ ${m} (Active)` : m) : `⚠️ ${m} (Blocked)`;
        });

        modeSimChart.data.datasets[0].data = viz.mode_simulation.probabilities;
        modeSimChart.data.datasets[0].backgroundColor = viz.mode_simulation.probabilities.map((p, i) => {
          const isFeas = viz.mode_simulation.feasible[i];
          const isCurr = viz.mode_simulation.is_current[i];
          if (!isFeas) return 'rgba(239, 68, 68, 0.25)';
          if (isCurr) return '#38bdf8';
          return 'rgba(56, 189, 248, 0.6)';
        });
        modeSimChart.data.datasets[0].borderColor = viz.mode_simulation.probabilities.map((p, i) => {
          const isFeas = viz.mode_simulation.feasible[i];
          const isCurr = viz.mode_simulation.is_current[i];
          if (!isFeas) return '#ef4444';
          if (isCurr) return '#ffffff';
          return '#38bdf8';
        });
        modeSimChart.update('active');
      }

      // Weather Stress-Test Chart
      if (weatherSimChart && viz.weather_simulation) {
        weatherSimChart.data.labels = viz.weather_simulation.labels.map((w, i) => {
          return viz.weather_simulation.is_current[i] ? `⭐ ${w} (Current)` : w;
        });
        weatherSimChart.data.datasets[0].data = viz.weather_simulation.probabilities;
        weatherSimChart.update('active');
      }

      // Delay Waterfall Chart
      if (delayChart && viz.delay_waterfall) {
        const sched = viz.delay_waterfall.scheduled_days;
        const delay = viz.delay_waterfall.delay_max;
        delayChart.data.datasets[0].data = [sched, sched];
        delayChart.data.datasets[1].data = [0, delay];
        delayChart.update('active');
      }
    }

    // 5. Update Recommendations List
    if (simRecommendationsList && data.recommendations) {
      simRecommendationsList.innerHTML = '';
      data.recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        simRecommendationsList.appendChild(li);
      });
    }

    // 6. Update Telemetry Chips
    if (data.telemetry) {
      if (chipRoute) chipRoute.textContent = data.telemetry.route;
      if (chipMode) chipMode.textContent = data.telemetry.mode ? `${data.telemetry.mode} Freight` : '--';
      if (chipDistance) chipDistance.textContent = data.telemetry.distance_km || '--';
      if (chipWeight) chipWeight.textContent = data.telemetry.weight_mt || '--';
      if (chipDate) chipDate.textContent = data.telemetry.scheduled_date || '--';
    }

    if (syncStatusBadge) {
      syncStatusBadge.textContent = '⚡ Synchronized';
      syncStatusBadge.style.color = '#38bdf8';
    }
  }

  // --------------------------------------------------
  // 3. ROUTE CONNECTIVITY & ALLOWED MODES CHECK
  // --------------------------------------------------
  async function checkCorridorModes() {
    const origin = originSelect.value;
    const dest = destSelect.value;

    if (!origin || !dest) return;

    if (origin.toLowerCase() === dest.toLowerCase()) {
      if (sameLocationAlert) sameLocationAlert.style.display = 'flex';
      if (simPredictBtn) simPredictBtn.disabled = true;
      if (modeSelect) modeSelect.disabled = true;
      if (blockedModesAlert) blockedModesAlert.style.display = 'none';
      if (allowedCountBadge) allowedCountBadge.textContent = '(0 allowed)';
      return;
    }

    if (sameLocationAlert) sameLocationAlert.style.display = 'none';
    if (simPredictBtn) simPredictBtn.disabled = false;
    if (modeSelect) modeSelect.disabled = false;

    try {
      const res = await fetch(`/api/route-info?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(dest)}`);
      const data = await res.json();

      if (!res.ok) return;

      // Auto-update distance if available
      if (data.distance_km && distanceInput) {
        distanceInput.value = data.distance_km;
      }

      // Populate Transport Modes
      const prevMode = modeSelect.value;
      modeSelect.innerHTML = '';

      data.allowed_modes.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = `${getModeIcon(m)} ${m}`;
        if (m === prevMode) opt.selected = true;
        modeSelect.appendChild(opt);
      });

      if (!data.allowed_modes.includes(prevMode) && data.allowed_modes.length > 0) {
        modeSelect.value = data.allowed_modes[0];
      }

      if (allowedCountBadge) {
        allowedCountBadge.textContent = `(${data.allowed_modes.length} allowed)`;
      }

      // Infeasible modes warning (e.g. Sri Lanka to India)
      if (data.unavailable_modes && data.unavailable_modes.length > 0 && blockedModesAlert) {
        blockedModesAlert.style.display = 'flex';
        blockedModesAlert.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
          <span><strong>${data.unavailable_modes.join(', ')}</strong> unavailable: no physical overland road/rail transit between ${origin} and ${dest}.</span>
        `;
      } else if (blockedModesAlert) {
        blockedModesAlert.style.display = 'none';
      }

    } catch (err) {
      console.error("Error loading corridor connectivity:", err);
    }
  }

  function getModeIcon(mode) {
    switch (mode) {
      case 'Sea': return '🚢';
      case 'Air': return '✈️';
      case 'Road': return '🚚';
      case 'Rail': return '🚆';
      default: return '📦';
    }
  }

  // --------------------------------------------------
  // 4. FORM SUBMISSION & PREDICTION TRIGGER
  // --------------------------------------------------
  simForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (originSelect.value.toLowerCase() === destSelect.value.toLowerCase()) {
      alert("Origin and destination ports cannot be identical.");
      return;
    }

    const formData = new FormData(simForm);
    const payload = {};
    formData.forEach((val, key) => {
      payload[key] = val;
    });

    // Loading State
    if (simSpinner) simSpinner.style.display = 'inline-block';
    if (simBtnLabel) simBtnLabel.textContent = 'Simulating & Updating Visualizations...';
    if (simPredictBtn) simPredictBtn.disabled = true;

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.error || "Simulation evaluation failed.");
        return;
      }

      // Persist latest prediction state so Page 1 and Page 2 stay synchronized
      try {
        localStorage.setItem('sc_current_prediction', JSON.stringify(data));
      } catch (e) {
        console.warn("localStorage quota exceeded or disabled", e);
      }

      // Auto-update all dynamic charts and UI elements
      updateAllVisualizations(data);

    } catch (err) {
      console.error(err);
      alert("Network error executing prediction simulation.");
    } finally {
      if (simSpinner) simSpinner.style.display = 'none';
      if (simBtnLabel) simBtnLabel.textContent = 'Run Disruption Assessment & Auto-Update Visualizations';
      if (simPredictBtn) simPredictBtn.disabled = false;
    }
  });

  // Listen for corridor node changes
  originSelect.addEventListener('change', checkCorridorModes);
  destSelect.addEventListener('change', checkCorridorModes);

  // --------------------------------------------------
  // 5. INITIAL STATE HYDRATION (localStorage or default)
  // --------------------------------------------------
  function hydrateInitialData() {
    let saved = null;
    try {
      const raw = localStorage.getItem('sc_current_prediction');
      if (raw) saved = JSON.parse(raw);
    } catch (e) {
      console.warn("Could not read from localStorage", e);
    }

    if (saved && saved.inputs) {
      // Hydrate inputs from previous prediction on Page 1 or Page 2
      if (originSelect) originSelect.value = saved.inputs.origin_port || originSelect.value;
      if (destSelect) destSelect.value = saved.inputs.destination_port || destSelect.value;
      if (weatherSelect && saved.inputs.weather_condition) weatherSelect.value = saved.inputs.weather_condition;
      if (productSelect && saved.inputs.product_category) productSelect.value = saved.inputs.product_category;
      if (leadTimeInput && saved.inputs.lead_time_days) leadTimeInput.value = saved.inputs.lead_time_days;
      if (carrierInput && saved.inputs.carrier_reliability_score) carrierInput.value = saved.inputs.carrier_reliability_score;
      if (geoInput && saved.inputs.geopolitical_risk_score !== undefined) geoInput.value = saved.inputs.geopolitical_risk_score;
      if (weightInput && saved.inputs.weight_mt) weightInput.value = saved.inputs.weight_mt;
      if (distanceInput && saved.inputs.distance_km) distanceInput.value = saved.inputs.distance_km;
      if (dateInput && saved.inputs.date) dateInput.value = saved.inputs.date;

      checkCorridorModes().then(() => {
        if (modeSelect && saved.inputs.transport_mode) {
          modeSelect.value = saved.inputs.transport_mode;
        }
        updateAllVisualizations(saved);
      });
    } else if (window.INITIAL_PREDICTION) {
      // Fallback to server-rendered initial prediction
      checkCorridorModes().then(() => {
        updateAllVisualizations(window.INITIAL_PREDICTION);
      });
    }
  }

  hydrateInitialData();
});
