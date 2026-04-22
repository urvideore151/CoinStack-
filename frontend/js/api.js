const API_BASE = 'http://localhost:5000';

// Strict meme coin allowlist — only these show on dashboard
const MEME_COINS = [
  'DOGE','SHIB','PEPE','WIF','BONK','FLOKI','MEME','BRETT',
  'POPCAT','MOG','TURBO','MYRO','BOME','SLERF','WEN','NEIRO',
  'PNUT','GOAT','MOODENG','DEGEN','LADYS','KISHU','ELON',
  'BABYDOGE','SAMO','COPE','HOGE','AKITA','SAITAMA','LEASH'
];

// Normalize a coin object — maps scorer column names to frontend names
function normalizeCoin(coin) {
  // engagement_24h is post count in last 24h — must be positive integer
  // Guard against backend sending sentiment_avg (-1 to 1) in this field
  const engRaw = Math.max(0, parseFloat(coin.engagement_24h || 0));
  const engStr = engRaw > 0
    ? (engRaw >= 1000 ? (engRaw/1000).toFixed(1)+'K posts' : Math.round(engRaw) + ' posts')
    : (coin.engagement || '—');

  // price formatting — small coins need many decimals
  const price = parseFloat(coin.price_usd || 0);

  return {
    coin:           coin.coin             || '???',
    hype_score:     parseFloat(coin.hype_score)     || 0,
    sentiment_avg:  parseFloat(coin.sentiment_avg)  || 0,
    // sentiment_pct from scorer = sentiment_avg * 100 (range: -100 to +100)
    // Convert to 0-100 scale for display: (val + 100) / 2
    sentiment_pct:  (() => {
      const raw = parseFloat(coin.sentiment_pct || 0);
      const avg = parseFloat(coin.sentiment_avg || 0);
      // If pct is in 0-100 range already, use it
      if (raw >= 0 && raw <= 100) return raw;
      // If it's in -100 to +100 range, convert to 0-100
      if (raw >= -100 && raw <= 100) return Math.round((raw + 100) / 2);
      // Fallback: derive from sentiment_avg (-1 to 1) → 0-100
      return Math.round((avg + 1) / 2 * 100);
    })(),
    mention_count:  parseInt(coin.mention_count)    || 0,
    trend_label:    coin.trend_label      || 'Flat',

    // scorer uses _pct suffix — map both variants
    change_1h:      parseFloat(coin.change_1h_pct  || coin.change_1h)  || 0,
    change_24h:     parseFloat(coin.change_24h_pct || coin.change_24h) || 0,
    change_7d:      parseFloat(coin.change_7d_pct  || coin.change_7d)  || 0,

    // price — keep raw for display
    price_usd:      price,

    // engagement — raw number AND formatted string
    engagement_24h: engRaw,
    engagement:     engStr,

    // volume
    volume_24h:     parseFloat(coin.volume_24h)     || 0,

    // news
    news_count:     parseInt(coin.news_count)       || 0,

    // BTC comparison signal (new scorer columns)
    btc_signal:     coin.btc_signal      || 'N/A',
    btc_confidence: parseFloat(coin.btc_confidence) || 0,

    // sparkline — scorer doesn't output this, frontend generates it
    sparkline:      Array.isArray(coin.sparkline) && coin.sparkline.length >= 2
                      ? coin.sparkline : [],

    timestamp:      coin.timestamp       || new Date().toISOString(),
  };
}

// Filter to meme coins only
function filterMemesOnly(coins) {
  const memes = coins.filter(c => MEME_COINS.includes(c.coin.toUpperCase()));
  // If backend returns no recognised meme coins, show all (dev/fallback mode)
  return memes.length > 0 ? memes : coins;
}

async function fetchScoredCoins() {
  try {
    const res = await fetch(`${API_BASE}/api/coins`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error('Bad response');
    const data = await res.json();
    return filterMemesOnly(data.map(normalizeCoin));
  } catch {
    return DEMO_DATA;
  }
}

async function fetchGlobalMetrics() {
  try {
    const res = await fetch(`${API_BASE}/api/metrics`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error();
    return await res.json();
  } catch {
    return GLOBAL_METRICS;
  }
}

async function fetchCoinDetail(symbol) {
  try {
    const res = await fetch(`${API_BASE}/api/coins/${symbol}`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error();
    return normalizeCoin(await res.json());
  } catch {
    // fallback — search all coins and find by symbol
    try {
      const res2 = await fetch(`${API_BASE}/api/coins`, { signal: AbortSignal.timeout(3000) });
      if (res2.ok) {
        const all = await res2.json();
        const found = all.find(c => c.coin.toUpperCase() === symbol.toUpperCase());
        if (found) return normalizeCoin(found);
      }
    } catch {}
    const found = DEMO_DATA.find(c => c.coin === symbol);
    return found ? normalizeCoin(found) : null;
  }
}

async function fetchNewsPosts(symbol) {
  try {
    const url = symbol && symbol !== 'ALL'
      ? `${API_BASE}/api/news?coin=${symbol}`
      : `${API_BASE}/api/news`;
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) throw new Error();
    return await res.json();
  } catch {
    const sym = symbol || 'CRYPTO';
    return [
      { title: `${sym} analysis — what traders are watching`, subreddit: 'CoinDesk',   upvotes: 0, sentiment: 'neutral', time: 'just now' },
      { title: `Is ${sym} a buy right now?`,                  subreddit: 'CryptoNews', upvotes: 0, sentiment: 'neutral', time: '5m ago'   },
      { title: `${sym} price prediction — analysts weigh in`, subreddit: 'Decrypt',    upvotes: 0, sentiment: 'neutral', time: '10m ago'  },
    ];
  }
}
