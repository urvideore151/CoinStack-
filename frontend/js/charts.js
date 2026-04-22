// charts.js — Chart.js builders

/* ── Sentiment breakdown bar chart ─────────────── */
function buildSentimentChart(canvasId, positive, neutral, negative) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{
        data: [positive, neutral, negative],
        backgroundColor: ['#22c55e', '#8b90a0', '#ef4444'],
        borderRadius: 4,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false }, tooltip: { enabled: true } },
      scales: {
        x: {
          max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#8b90a0', font: { size: 11 }, callback: v => v + '%' },
          border: { color: 'rgba(255,255,255,0.05)' },
        },
        y: {
          grid: { display: false },
          ticks: { color: '#8b90a0', font: { size: 11 } },
          border: { display: false },
        },
      },
    },
  });
}

/* ── Hype score over time line chart ───────────── */
function buildHypeTimeChart(canvasId, coinData, color) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  // Generate 24 hourly labels
  const labels = [];
  for (let i = 23; i >= 0; i--) {
    const h = new Date(Date.now() - i * 3600000);
    labels.push(h.getHours() + ':00');
  }

  // Simulate time series from sparkline
  const sparkline = coinData.sparkline || [];
  // Extend to 24 points
  const data = [];
  for (let i = 0; i < 24; i++) {
    const idx = Math.floor((i / 23) * (sparkline.length - 1));
    const base = sparkline[idx] || 50;
    data.push(+(base + (Math.random() - 0.5) * 3).toFixed(1));
  }

  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data,
        borderColor: color,
        backgroundColor: color + '20',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8b90a0', font: { size: 10 }, maxTicksLimit: 8, autoSkip: true },
          border: { color: 'rgba(255,255,255,0.05)' },
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8b90a0', font: { size: 10 } },
          border: { color: 'rgba(255,255,255,0.05)' },
        },
      },
    },
  });
}

/* ── Overview multi-coin line chart ────────────── */
function buildOverviewChart(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000);
    labels.push(['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()]);
  }

  const datasets = DEMO_DATA.map(coin => ({
    label: coin.coin,
    data: coin.sparkline.slice(-7).map(v => +v.toFixed(1)),
    borderColor: COINS[coin.coin]?.color || '#fff',
    backgroundColor: 'transparent',
    tension: 0.4,
    pointRadius: 0,
    borderWidth: 2,
  }));

  new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8b90a0', font: { size: 11 } },
          border: { color: 'rgba(255,255,255,0.05)' },
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8b90a0', font: { size: 11 } },
          border: { color: 'rgba(255,255,255,0.05)' },
        },
      },
    },
  });
}
