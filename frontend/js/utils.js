// utils.js — helpers, clock, sparkline rendering

/* ── Live clock ───────────────────────────────── */
function startClock(el) {
  function tick() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    el.textContent = `${h}:${m}:${s}`;
  }
  tick();
  setInterval(tick, 1000);
}

/* ── Number formatting ────────────────────────── */
function fmtNumber(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}

function fmtChange(val) {
  const sign = val >= 0 ? '▲' : '▼';
  const cls  = val >= 0 ? 'change-up' : 'change-down';
  return `<span class="${cls}"><span class="change-arrow">${sign}</span> ${Math.abs(val).toFixed(1)}%</span>`;
}

function getTrendClass(score) {
  if (score >= 65) return 'rising';
  if (score >= 40) return 'flat';
  return 'falling';
}

function getTrendIcon(score) {
  if (score >= 65) return '🔥';
  if (score >= 40) return '➡️';
  return '❄️';
}

function getSentimentColor(pct) {
  if (pct >= 60) return '#22c55e';
  if (pct >= 45) return '#f59e0b';
  return '#ef4444';
}

/* ── Canvas sparkline ─────────────────────────── */
function drawSparkline(canvas, data, color) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.offsetWidth || 120;
  const h = canvas.offsetHeight || 40;
  canvas.width  = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width  = w + 'px';
  canvas.style.height = h + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pad = 4;

  const xs = data.map((_, i) => pad + (i / (data.length - 1)) * (w - pad * 2));
  const ys = data.map(v => h - pad - ((v - min) / range) * (h - pad * 2));

  // Fill gradient
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, color + '40');
  grad.addColorStop(1, color + '00');

  ctx.beginPath();
  ctx.moveTo(xs[0], ys[0]);
  for (let i = 1; i < xs.length; i++) {
    const cpx = (xs[i - 1] + xs[i]) / 2;
    ctx.bezierCurveTo(cpx, ys[i - 1], cpx, ys[i], xs[i], ys[i]);
  }
  ctx.lineTo(xs[xs.length - 1], h);
  ctx.lineTo(xs[0], h);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line
  ctx.beginPath();
  ctx.moveTo(xs[0], ys[0]);
  for (let i = 1; i < xs.length; i++) {
    const cpx = (xs[i - 1] + xs[i]) / 2;
    ctx.bezierCurveTo(cpx, ys[i - 1], cpx, ys[i], xs[i], ys[i]);
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.8;
  ctx.stroke();
}

/* ── Gauge SVG ────────────────────────────────── */
function drawGauge(svgEl, value, label) {
  const W = 120, H = 70;
  const cx = W / 2, cy = H - 8;
  const r = 44;
  const startA = Math.PI;
  const endA = 0;

  // value 0-100 → angle
  const angle = startA + (value / 100) * Math.PI;
  const needleX = cx + r * 0.85 * Math.cos(Math.PI + angle - Math.PI);
  const needleY = cy + r * 0.85 * Math.sin(Math.PI + angle - Math.PI);

  // Arc path helper
  function arc(cx, cy, r, startAngle, endAngle) {
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
  }

  // Color stops for the arc
  const segments = [
    { color: '#ef4444', start: Math.PI,       end: Math.PI + Math.PI * 0.25 },
    { color: '#f59e0b', start: Math.PI + Math.PI * 0.25, end: Math.PI + Math.PI * 0.5 },
    { color: '#facc15', start: Math.PI + Math.PI * 0.5,  end: Math.PI + Math.PI * 0.75 },
    { color: '#22c55e', start: Math.PI + Math.PI * 0.75, end: Math.PI * 2 },
  ];

  let paths = '';
  segments.forEach(seg => {
    paths += `<path d="${arc(cx, cy, r, seg.start, seg.end)}" stroke="${seg.color}" stroke-width="8" fill="none" stroke-linecap="butt"/>`;
  });

  // Needle
  const nAngle = Math.PI + (value / 100) * Math.PI;
  const nx = cx + r * 0.75 * Math.cos(nAngle);
  const ny = cy + r * 0.75 * Math.sin(nAngle);

  svgEl.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svgEl.setAttribute('width', W);
  svgEl.setAttribute('height', H);
  svgEl.innerHTML = `
    ${paths}
    <circle cx="${cx}" cy="${cy}" r="4" fill="#1a1d27"/>
    <line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" stroke="#e8eaf0" stroke-width="2" stroke-linecap="round"/>
    <text x="${cx}" y="${cy - 12}" class="gauge-value" style="font-size:18px;font-weight:700;font-family:monospace;text-anchor:middle;fill:#e8eaf0">${value}</text>
    <text x="${cx}" y="${cy - 2}" class="gauge-label-text" style="font-size:9px;text-anchor:middle;fill:#8b90a0;letter-spacing:0.06em;text-transform:uppercase">${label}</text>
  `;
}

/* ── Metric sparkline on canvas ───────────────── */
function drawMetricSparkline(canvas, data, color) {
  drawSparkline(canvas, data, color);
}
