/**
 * SupplyChain.AI - Analytics & Visualizations Chart Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const data = window.ANALYTICS_DATA;
  if (!data) {
    console.error("ANALYTICS_DATA not found.");
    return;
  }

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

  // --------------------------------------------------
  // 1. WEATHER IMPACT CHART (Bar Chart)
  // --------------------------------------------------
  const weatherCtx = document.getElementById('weatherChart');
  if (weatherCtx && data.weather_chart) {
    const palette = [
      'rgba(239, 68, 68, 0.85)',   // Hurricane - Red
      'rgba(249, 115, 22, 0.85)',  // Storm - Orange
      'rgba(234, 179, 8, 0.85)',   // Fog - Amber
      'rgba(14, 165, 233, 0.85)',  // Rain - Sky Blue
      'rgba(16, 185, 129, 0.85)'   // Clear - Emerald
    ];

    const borders = [
      '#ef4444',
      '#f97316',
      '#eab308',
      '#0ea5e9',
      '#10b981'
    ];

    new Chart(weatherCtx, {
      type: 'bar',
      data: {
        labels: data.weather_chart.labels,
        datasets: [{
          label: 'Disruption Probability (%)',
          data: data.weather_chart.rates,
          backgroundColor: palette,
          borderColor: borders,
          borderWidth: 1.5,
          borderRadius: 6,
          barThickness: 32
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Disruption Rate: ${ctx.raw}% (${data.weather_chart.counts[ctx.dataIndex].toLocaleString()} records)`
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
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // --------------------------------------------------
  // 2. PRODUCT CATEGORY BREAKDOWN (Grouped Bar Chart)
  // --------------------------------------------------
  const categoryCtx = document.getElementById('categoryChart');
  if (categoryCtx && data.category_chart) {
    new Chart(categoryCtx, {
      type: 'bar',
      data: {
        labels: data.category_chart.labels,
        datasets: [
          {
            label: 'Disrupted Shipments',
            data: data.category_chart.disrupted,
            backgroundColor: 'rgba(239, 68, 68, 0.75)',
            borderColor: '#ef4444',
            borderWidth: 1.5,
            borderRadius: 6
          },
          {
            label: 'On-Time Shipments',
            data: data.category_chart.ontime,
            backgroundColor: 'rgba(16, 185, 129, 0.75)',
            borderColor: '#10b981',
            borderWidth: 1.5,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // --------------------------------------------------
  // 3. MONTHLY TIMELINE TREND (Smooth Line Chart)
  // --------------------------------------------------
  const timelineCtx = document.getElementById('timelineChart');
  if (timelineCtx && data.timeline_chart) {
    new Chart(timelineCtx, {
      type: 'line',
      data: {
        labels: data.timeline_chart.labels,
        datasets: [{
          label: 'Disruption Rate (%)',
          data: data.timeline_chart.rates,
          borderColor: '#38bdf8',
          borderWidth: 2.5,
          backgroundColor: 'rgba(56, 189, 248, 0.1)',
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#38bdf8',
          pointBorderColor: '#0f172a',
          pointBorderWidth: 2,
          pointRadius: 3.5,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Disruption Rate: ${ctx.raw}% (${data.timeline_chart.counts[ctx.dataIndex]} shipments)`
            }
          }
        },
        scales: {
          y: {
            min: 45,
            max: 75,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { callback: (val) => `${val}%` }
          },
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.03)' },
            ticks: { maxTicksLimit: 12 }
          }
        }
      }
    });
  }

  // --------------------------------------------------
  // 4. TRANSPORT MODE COMPARISON (Bar Chart)
  // --------------------------------------------------
  const modeCtx = document.getElementById('modeChart');
  if (modeCtx && data.mode_chart) {
    new Chart(modeCtx, {
      type: 'bar',
      data: {
        labels: data.mode_chart.labels,
        datasets: [{
          label: 'Disruption Rate (%)',
          data: data.mode_chart.rates,
          backgroundColor: [
            'rgba(56, 189, 248, 0.75)',
            'rgba(129, 140, 248, 0.75)',
            'rgba(52, 211, 153, 0.75)',
            'rgba(244, 114, 182, 0.75)'
          ],
          borderColor: [
            '#38bdf8',
            '#818cf8',
            '#34d399',
            '#f472b6'
          ],
          borderWidth: 1.5,
          borderRadius: 6,
          barThickness: 36
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${ctx.raw}% (${data.mode_chart.counts[ctx.dataIndex].toLocaleString()} total shipments)`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 80,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { callback: (val) => `${val}%` }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // --------------------------------------------------
  // 5. ML FEATURE IMPORTANCE (Horizontal Bar Chart)
  // --------------------------------------------------
  const featureCtx = document.getElementById('featureChart');
  if (featureCtx && data.feature_chart) {
    new Chart(featureCtx, {
      type: 'bar',
      data: {
        labels: data.feature_chart.labels,
        datasets: [{
          label: 'Predictive Weight (%)',
          data: data.feature_chart.values,
          backgroundColor: 'rgba(99, 102, 241, 0.75)',
          borderColor: '#818cf8',
          borderWidth: 1.5,
          borderRadius: 6,
          barThickness: 18
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Model Feature Weight: ${ctx.raw}%`
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { callback: (val) => `${val}%` }
          },
          y: {
            grid: { display: false }
          }
        }
      }
    });
  }
});
