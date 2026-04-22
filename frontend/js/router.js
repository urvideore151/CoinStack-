// router.js — SPA router with all pages inlined (no fetch needed)

let currentRoute = 'top';
let mainContent  = null;

/* ── Page templates ───────────────────────────────────────────────── */

function pageTrending() {
  return `
    <div class="coin-table-wrap">
      <table class="coin-table">
        <thead>
          <tr>
            <th><div class="th-inner">#</div></th>
            <th><div class="th-inner">Name ⇅</div></th>
            <th><div class="th-inner">Hype Score ⇅</div></th>
            <th><div class="th-inner">1h % ⇅</div></th>
            <th><div class="th-inner">24h % ⇅</div></th>
            <th><div class="th-inner">7d % ⇅</div></th>
            <th><div class="th-inner"><span class="th-info">i</span> Mentions(24h) ⇅</div></th>
            <th><div class="th-inner"><span class="th-info">i</span> Sentiment ⇅</div></th>
            <th><div class="th-inner"><span class="th-info">i</span> Engagement ⇅</div></th>
            <th><div class="th-inner">Last 24h</div></th>
          </tr>
        </thead>
        <tbody id="coin-tbody"></tbody>
      </table>
    </div>
  `;
}

function formatPrice(p) {
  if (!p || p === 0) return '—';
  if (p >= 1)        return '$' + p.toLocaleString(undefined, { maximumFractionDigits: 4 });
  if (p >= 0.01)     return '$' + p.toFixed(4);
  if (p >= 0.0001)   return '$' + p.toFixed(6);
  return '$' + p.toExponential(3);
}

function btcSignalColor(sig) {
  if (!sig || sig === 'N/A') return 'var(--text-muted)';
  if (sig.includes('BUY'))   return '#22c55e';
  if (sig.includes('WATCH')) return '#f59e0b';
  if (sig.includes('AVOID')) return '#ef4444';
  return 'var(--text-secondary)';
}

function pageCoinDetail() {
  return `
    <div style="padding:24px 20px;max-width:960px;">
      <div style="margin-bottom:16px;">
        <button onclick="navigate('trending')" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-md);font-size:12px;color:var(--text-secondary);cursor:pointer;">
          ← Back to Trending
        </button>
      </div>
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px;">
        <div id="detail-avatar" style="width:52px;height:52px;border-radius:50%;background:rgba(74,222,128,0.15);display:flex;align-items:center;justify-content:center;font-size:26px">🪙</div>
        <div>
          <div style="font-size:22px;font-weight:700;" id="detail-name">Loading...</div>
          <div style="font-size:13px;color:var(--text-muted);" id="detail-symbol">—</div>
        </div>
        <div id="detail-score-badge" class="score-badge flat" style="margin-left:12px;font-size:16px">— —</div>
      </div>

      <!-- 6 stat cards -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px;">
        <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Price (USD)</div>
          <div style="font-size:18px;font-weight:700;font-family:var(--font-mono)" id="detail-price">—</div>
          <div style="font-size:10px;color:var(--text-muted);margin-top:4px">via CoinGecko</div>
        </div>
        <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Mentions 24h</div>
          <div style="font-size:22px;font-weight:700;font-family:var(--font-mono)" id="detail-mentions">—</div>
        </div>
        <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Sentiment</div>
          <div style="font-size:22px;font-weight:700;color:var(--color-up)" id="detail-sentiment">—</div>
        </div>
        <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Engagement</div>
          <div style="font-size:22px;font-weight:700;font-family:var(--font-mono)" id="detail-engagement">—</div>
        </div>
        <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">7d Change</div>
          <div style="font-size:22px;font-weight:700;" id="detail-7d">—</div>
        </div>
        <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">BTC Corr.</div>
          <div style="font-size:18px;font-weight:700;" id="detail-btc-signal">—</div>
          <div style="font-size:10px;color:var(--text-muted);margin-top:4px" id="detail-btc-conf"></div>
        </div>
      </div>

      <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:16px;margin-bottom:20px;">
        <div style="font-size:12px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:12px">Hype Score — Last 24 Hours</div>
        <div style="position:relative;height:180px;"><canvas id="hype-time-chart"></canvas></div>
      </div>
      <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:16px;">
        <div style="font-size:12px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:12px">Sentiment Breakdown</div>
        <div style="position:relative;height:120px;"><canvas id="sentiment-chart"></canvas></div>
      </div>
    </div>
  `;
}

function pageAlerts() {
  const ALERTS_DATA = [
    { coin:'PEPE', icon:'🔥', text:'PEPE mentions up 340% in last hour',      severity:'high'   },
    { coin:'DOGE', icon:'🚀', text:'DOGE pump detected — 7.4% in 24h',        severity:'medium' },
    { coin:'WIF',  icon:'📡', text:'WIF hits 3-day high on Reddit',            severity:'medium' },
    { coin:'BONK', icon:'⚡', text:'BONK whale wallet spotted accumulating',   severity:'high'   },
    { coin:'SHIB', icon:'📊', text:'SHIB sentiment dropped below 50%',         severity:'low'    },
    { coin:'PEPE', icon:'💎', text:'PEPE community engagement 9.4x average',  severity:'medium' },
    { coin:'DOGE', icon:'🔔', text:'DOGE weekly change crosses +21%',          severity:'low'    },
  ];
  const times = ['2m ago','5m ago','12m ago','18m ago','25m ago','31m ago','44m ago'];
  const sColors = { high:'#ef4444', medium:'#f59e0b', low:'#22c55e' };
  const sBg     = { high:'rgba(239,68,68,0.1)', medium:'rgba(245,158,11,0.1)', low:'rgba(34,197,94,0.1)' };

  const rows = ALERTS_DATA.map((a, i) => {
    const meta = (typeof COINS !== 'undefined' && COINS[a.coin]) || { bgColor:'rgba(255,255,255,0.1)' };
    return `
      <div style="display:flex;align-items:center;gap:14px;padding:14px 16px;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);border-left:3px solid ${sColors[a.severity]};">
        <div style="width:36px;height:36px;border-radius:50%;background:${meta.bgColor};display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">${a.icon}</div>
        <div style="flex:1">
          <div style="font-size:13px;font-weight:500;margin-bottom:2px">${a.text}</div>
          <div style="font-size:11px;color:var(--text-muted)">${a.coin} · ${times[i]}</div>
        </div>
        <div style="padding:3px 8px;border-radius:var(--radius-sm);background:${sBg[a.severity]};color:${sColors[a.severity]};font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">${a.severity}</div>
      </div>
    `;
  }).join('');

  return `<div style="padding:24px 20px;max-width:860px;"><div style="font-size:16px;font-weight:600;margin-bottom:16px;">Hype Alerts</div><div style="display:flex;flex-direction:column;gap:10px;">${rows}</div></div>`;
}

function pageRedditFeed() {
  return `
    <div style="padding:24px 20px;max-width:860px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <div style="font-size:16px;font-weight:600;">Live Reddit Feed</div>
        <div style="font-size:11px;padding:3px 8px;background:rgba(255,69,0,0.12);color:#ff4500;border-radius:var(--radius-sm);font-weight:600;border:1px solid rgba(255,69,0,0.2)">● LIVE</div>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap;">
        <button onclick="window._filterFeed('ALL')" class="feed-pill active" data-coin="ALL">All Coins</button>
        <button onclick="window._filterFeed('PEPE')" class="feed-pill" data-coin="PEPE">🐸 PEPE</button>
        <button onclick="window._filterFeed('DOGE')" class="feed-pill" data-coin="DOGE">🐕 DOGE</button>
        <button onclick="window._filterFeed('WIF')"  class="feed-pill" data-coin="WIF">🎩 WIF</button>
        <button onclick="window._filterFeed('SHIB')" class="feed-pill" data-coin="SHIB">🐕‍🦺 SHIB</button>
        <button onclick="window._filterFeed('BONK')" class="feed-pill" data-coin="BONK">🔥 BONK</button>
      </div>
      <div id="feed-list" style="display:flex;flex-direction:column;gap:10px;"></div>
    </div>
    <style>
      .feed-pill{padding:5px 12px;border-radius:var(--radius-md);border:1px solid var(--border-light);background:var(--bg-tertiary);color:var(--text-secondary);font-size:12px;font-weight:500;cursor:pointer;transition:all 0.15s;}
      .feed-pill.active,.feed-pill:hover{background:rgba(77,124,255,0.1);border-color:rgba(77,124,255,0.3);color:#4d7cff;}
      .sent-tag{padding:2px 7px;border-radius:var(--radius-sm);font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.04em;}
      .sent-tag.positive{background:rgba(34,197,94,0.12);color:#22c55e;}
      .sent-tag.neutral{background:rgba(139,144,160,0.12);color:#8b90a0;}
      .sent-tag.negative{background:rgba(239,68,68,0.12);color:#ef4444;}
    </style>
  `;
}

function pageSentiment() {
  return `<div style="padding:24px 20px;max-width:900px;"><div style="font-size:16px;font-weight:600;margin-bottom:20px;">Sentiment Analysis</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin-bottom:24px;" id="sentiment-cards"></div><div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:16px;"><div style="font-size:12px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:14px">Overall Sentiment Distribution</div><div style="position:relative;height:200px"><canvas id="overall-sent-chart"></canvas></div></div></div>`;
}

/* ── Router core ──────────────────────────────────────────────────── */

function initRouter() {
  mainContent = document.getElementById('main-content');

  document.querySelectorAll('[data-route]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.route));
  });
  // Do NOT auto-navigate — index.html renders the default table view
}

function navigate(route) {
  currentRoute = route;

  document.querySelectorAll('[data-route]').forEach(el => {
    el.classList.toggle('active', el.dataset.route === route);
  });

  switch (route) {
    case 'top':
    case 'trending':
    case 'watchlist':
    case 'active':
    case 'new':
      showTrendingPage();
      break;
    case 'coin-detail':
      showCoinDetailPage();
      break;
    case 'alerts':
      showAlertsPage();
      break;
    case 'reddit-feed':
      showRedditFeedPage();
      break;
    case 'sentiment':
      showSentimentPage();
      break;
    default:
      showTrendingPage();
  }
}

/* ── Page renderers ───────────────────────────────────────────────── */

async function showTrendingPage() {
  if (!mainContent) return;
  mainContent.innerHTML = pageTrending();
  const coins = await fetchScoredCoins();
  renderCoinTable(coins);
}

async function showCoinDetailPage() {
  if (!mainContent) return;
  mainContent.innerHTML = pageCoinDetail();

  const symbol = window.selectedCoin || 'PEPE';
  const coin   = await fetchCoinDetail(symbol);
  if (!coin) return;

  const meta = (typeof COINS !== 'undefined' && COINS[coin.coin]) || {
    name: coin.coin, emoji: '🪙', color: '#4d7cff', bgColor: 'rgba(77,124,255,0.15)',
  };

  // Header
  document.getElementById('detail-name').textContent       = meta.name || coin.coin;
  document.getElementById('detail-symbol').textContent     = coin.coin;
  document.getElementById('detail-avatar').innerHTML       = `<span style="font-size:26px">${meta.emoji}</span>`;
  document.getElementById('detail-avatar').style.background = meta.bgColor;

  // Hype badge
  const badge = document.getElementById('detail-score-badge');
  const tc    = getTrendClass(coin.hype_score);
  badge.className   = `score-badge ${tc}`;
  badge.textContent = getTrendIcon(coin.hype_score) + ' ' + coin.hype_score.toFixed(1);

  // Price — use smart formatter
  document.getElementById('detail-price').textContent = formatPrice(coin.price_usd);

  // Mentions
  document.getElementById('detail-mentions').textContent = fmtNumber(coin.mention_count);

  // Sentiment
  const sentEl = document.getElementById('detail-sentiment');
  sentEl.textContent = (coin.sentiment_pct || 0) + '% Positive';
  sentEl.style.color = coin.sentiment_pct >= 60 ? 'var(--color-up)'
                     : coin.sentiment_pct >= 45 ? 'var(--color-flat)'
                     : 'var(--color-down)';

  // Engagement
  document.getElementById('detail-engagement').textContent = coin.engagement || '—';

  // 7d change
  const c7El = document.getElementById('detail-7d');
  const c7   = coin.change_7d || 0;
  c7El.textContent = (c7 >= 0 ? '+' : '') + c7.toFixed(1) + '%';
  c7El.style.color = c7 >= 0 ? 'var(--color-up)' : 'var(--color-down)';

  // BTC signal
  const sig     = coin.btc_signal || 'N/A';
  const conf    = coin.btc_confidence || 0;
  const sigEl   = document.getElementById('detail-btc-signal');
  const confEl  = document.getElementById('detail-btc-conf');
  if (sigEl) { sigEl.textContent = sig; sigEl.style.color = btcSignalColor(sig); }
  if (confEl && conf > 0) confEl.textContent = 'Confidence: ' + conf.toFixed(0) + '%';
  else if (confEl) confEl.textContent = 'inverse = meme spike';

  // Charts
  buildHypeTimeChart('hype-time-chart', coin, meta.color);
  const pos = coin.sentiment_pct || 50;
  const neg = Math.round((100 - pos) * 0.4);
  const neu = 100 - pos - neg;
  buildSentimentChart('sentiment-chart', pos, neu, neg);
}

function showAlertsPage() {
  if (!mainContent) return;
  mainContent.innerHTML = pageAlerts();
}

function showRedditFeedPage() {
  if (!mainContent) return;
  mainContent.innerHTML = pageRedditFeed();

  const FEED_POSTS = [
    { coin:'PEPE', title:'PEPE is mooning right now!! 🐸🚀',               sub:'r/CryptoCurrency',    upvotes:2840, sentiment:'positive', time:'2m ago'  },
    { coin:'DOGE', title:'Just bought more DOGE, WAGMI 🚀',                sub:'r/dogecoin',           upvotes:1240, sentiment:'positive', time:'5m ago'  },
    { coin:'WIF',  title:'WIF technical analysis — cup and handle?',       sub:'r/CryptoMoonShots',   upvotes:890,  sentiment:'neutral',  time:'12m ago' },
    { coin:'PEPE', title:'PEPE 24h chart looking very bullish',            sub:'r/SatoshiStreetBets', upvotes:760,  sentiment:'positive', time:'15m ago' },
    { coin:'SHIB', title:'Is SHIB a good long-term hold in 2025?',         sub:'r/shib',              upvotes:540,  sentiment:'neutral',  time:'18m ago' },
    { coin:'BONK', title:'BONK dumping — should I sell?',                  sub:'r/CryptoMoonShots',   upvotes:210,  sentiment:'negative', time:'24m ago' },
    { coin:'DOGE', title:'Elon tweeted a DOGE meme again 💀',              sub:'r/dogecoin',          upvotes:3200, sentiment:'positive', time:'28m ago' },
    { coin:'WIF',  title:'WIF Reddit mentions tripled in 24h',             sub:'r/CryptoCurrency',    upvotes:480,  sentiment:'positive', time:'35m ago' },
    { coin:'BONK', title:'Bought BONK at the top like an idiot',           sub:'r/SatoshiStreetBets', upvotes:1100, sentiment:'negative', time:'40m ago' },
  ];

  let currentFilter = 'ALL';

  function renderFeed() {
    const posts = currentFilter === 'ALL' ? FEED_POSTS : FEED_POSTS.filter(p => p.coin === currentFilter);
    const list  = document.getElementById('feed-list');
    if (!list) return;
    list.innerHTML = posts.map(p => {
      const meta = (typeof COINS !== 'undefined' && COINS[p.coin]) || { emoji:'🪙', bgColor:'rgba(255,255,255,0.1)' };
      return `
        <div style="display:flex;align-items:flex-start;gap:12px;padding:14px 16px;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);cursor:pointer;" onmouseover="this.style.background='var(--bg-hover)'" onmouseout="this.style.background='var(--bg-tertiary)'">
          <div style="width:32px;height:32px;border-radius:50%;background:${meta.bgColor};display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">${meta.emoji}</div>
          <div style="flex:1">
            <div style="font-size:13px;font-weight:500;margin-bottom:4px;line-height:1.4">${p.title}</div>
            <div style="display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text-muted)">
              <span style="color:#ff4500">●</span><span>${p.sub}</span><span>·</span>
              <span>▲ ${p.upvotes.toLocaleString()}</span><span>·</span><span>${p.time}</span>
            </div>
          </div>
          <div class="sent-tag ${p.sentiment}">${p.sentiment}</div>
        </div>`;
    }).join('');
  }

  window._filterFeed = (coin) => {
    currentFilter = coin;
    document.querySelectorAll('.feed-pill').forEach(p => p.classList.toggle('active', p.dataset.coin === coin));
    renderFeed();
  };

  renderFeed();
}

function showSentimentPage() {
  if (!mainContent) return;
  mainContent.innerHTML = pageSentiment();

  const data = (typeof DEMO_DATA !== 'undefined') ? DEMO_DATA : [];
  const cards = document.getElementById('sentiment-cards');
  if (cards) {
    cards.innerHTML = data.map(coin => {
      const meta = (typeof COINS !== 'undefined' && COINS[coin.coin]) || { emoji:'🪙', color:'#fff', name: coin.coin };
      const pos = coin.sentiment_pct;
      const neg = Math.round((100 - pos) * 0.4);
      const neu = 100 - pos - neg;
      return `
        <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
            <span style="font-size:20px">${meta.emoji}</span>
            <span style="font-weight:600">${meta.name}</span>
            <span style="font-size:11px;color:var(--text-muted)">${coin.coin}</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;text-align:center">
            <div><div style="font-size:18px;font-weight:700;color:#22c55e">${pos}%</div><div style="font-size:10px;color:var(--text-muted)">Positive</div></div>
            <div><div style="font-size:18px;font-weight:700;color:#8b90a0">${neu}%</div><div style="font-size:10px;color:var(--text-muted)">Neutral</div></div>
            <div><div style="font-size:18px;font-weight:700;color:#ef4444">${neg}%</div><div style="font-size:10px;color:var(--text-muted)">Negative</div></div>
          </div>
          <div style="margin-top:10px;height:4px;border-radius:99px;overflow:hidden;display:flex">
            <div style="width:${pos}%;background:#22c55e"></div>
            <div style="width:${neu}%;background:#8b90a0"></div>
            <div style="width:${neg}%;background:#ef4444"></div>
          </div>
        </div>`;
    }).join('');
  }

  setTimeout(() => {
    const ctx = document.getElementById('overall-sent-chart');
    if (!ctx || typeof Chart === 'undefined') return;
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(c => c.coin),
        datasets: [
          { label:'Positive', data: data.map(c => c.sentiment_pct), backgroundColor:'#22c55e', borderRadius:4 },
          { label:'Neutral',  data: data.map(c => { const p=c.sentiment_pct,n=Math.round((100-p)*0.4); return 100-p-n; }), backgroundColor:'#8b90a0', borderRadius:4 },
          { label:'Negative', data: data.map(c => Math.round((100-c.sentiment_pct)*0.4)), backgroundColor:'#ef4444', borderRadius:4 },
        ],
      },
      options: {
        responsive:true, maintainAspectRatio:false,
        scales: {
          x:{ stacked:true, grid:{display:false}, ticks:{color:'#8b90a0',font:{size:11}}, border:{color:'rgba(255,255,255,0.05)'} },
          y:{ stacked:true, max:100, grid:{color:'rgba(255,255,255,0.04)'}, ticks:{color:'#8b90a0',font:{size:11},callback:v=>v+'%'}, border:{color:'rgba(255,255,255,0.05)'} },
        },
        plugins:{ legend:{display:false} },
      },
    });
  }, 100);
}

/* ── Called by row onclick in index.html ──────────────────────────── */
function openCoinDetail(symbol) {
  window.selectedCoin = symbol;
  navigate('coin-detail');
}

/* ── Called by auto-refresh in index.html ─────────────────────────── */
window.refreshDashboard = async () => {
  const coins = await fetchScoredCoins();
  renderCoinTable(coins);
};
