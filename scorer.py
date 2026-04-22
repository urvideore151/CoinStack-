NEWS_API_KEY        = "1016246d34a04562909f1d9edf842803"
CRYPTOPANIC_API_KEY = "8407a519ca947c504a0424060292dbd026c0d36c"

REDDIT_POST_LIMIT  = 200
NEWS_TOP_N         = 20
UPDATE_INTERVAL    = 60
NEWS_REFRESH_EVERY = 300

SUBREDDITS = [
    "CryptoCurrency", "dogecoin", "SatoshiStreetBets",
    "CryptoMoonShots", "binance", "ethtrader",
    "memecoin", "shib", "pepecoin", "WIF_coin"
]

# ── MEME COIN MASTER LIST ────────────────────────────────────
# These are fetched from CoinGecko by exact ID (not market cap rank)
# This guarantees all 40 meme coins are always fetched regardless of rank
MEME_COIN_IDS = [
    "dogecoin", "shiba-inu", "pepe", "dogwifcoin", "bonk",
    "floki", "meme-coin-2", "popcat", "mog-coin", "turbo",
    "myro", "book-of-meme", "slerf", "neiro-on-eth",
    "peanut-the-squirrel", "goatseus-maximus", "moodeng",
    "brett", "wen-4", "degen-base", "cats-in-a-dogs-world",
    "baby-doge-coin", "samoyedcoin", "hoge-finance",
    "kishu-inu", "akita-inu", "milady-meme-coin",
    "coq-inu", "ponke", "gigachad-2", "fwog", "sundog",
    "retardio", "billy-2", "mew", "maneki-404",
    "sats-ordinals", "rats-ordinals", "mochi-2", "landwolf"
]

# Symbol lookup used throughout scorer
MEME_SYMBOLS = [
    "DOGE","SHIB","PEPE","WIF","BONK","FLOKI","MEME","POPCAT",
    "MOG","TURBO","MYRO","BOME","SLERF","NEIRO","PNUT","GOAT",
    "MOODENG","BRETT","WEN","DEGEN","LADYS","BABYDOGE","SAMO",
    "HOGE","KISHU","AKITA","COQ","PONKE","GIGA","FWOG",
    "SUNDOG","RETARDIO","BILLY","MEW","MANEKI","SATS","RATS",
    "MOCHI","LANDWOLF","ELON"
]

print("✅ Config loaded")


import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install",
                "requests", "nltk", "pandas", "numpy", "-q"])

import requests
import pandas as pd
import numpy as np
import nltk
import time
import json
from datetime import datetime
from nltk.sentiment import SentimentIntensityAnalyzer

nltk.download('vader_lexicon', quiet=True)

sia = SentimentIntensityAnalyzer()
sia.lexicon.update({
    "moon":3.0,"mooning":3.0,"bullish":2.0,"bearish":-2.0,
    "pump":1.5,"dump":-1.5,"rekt":-2.5,"wagmi":2.5,
    "ngmi":-2.5,"hodl":1.5,"fud":-2.0,"gem":2.0,
    "rugged":-3.0,"ape":1.5,"shill":-1.0,"degen":1.0,
    "🚀":2.0,"💎":1.5,"📉":-2.0,"📈":2.0,"🔥":1.5,"🐸":1.5,
})

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

EMPTY_POSTS = pd.DataFrame(columns=[
    'coin_name','text','upvotes','comments','source','timestamp'
])

print(f"All imports ready ✅  VADER: {len(sia.lexicon)} words")


MEME_FALLBACK = [
    {"coin":"DOGE","price_usd":0.16,    "change_1h_pct":1.2, "change_24h_pct":18.5,"change_7d_pct":22.3,"volume_24h":2000000000},
    {"coin":"SHIB","price_usd":0.000009,"change_1h_pct":-0.5,"change_24h_pct":-4.2,"change_7d_pct":5.6, "volume_24h":800000000},
    {"coin":"PEPE","price_usd":0.000008,"change_1h_pct":2.1, "change_24h_pct":34.7,"change_7d_pct":42.1,"volume_24h":1200000000},
    {"coin":"WIF", "price_usd":2.3,     "change_1h_pct":-1.2,"change_24h_pct":-11.3,"change_7d_pct":12.8,"volume_24h":300000000},
    {"coin":"BONK","price_usd":0.00002, "change_1h_pct":0.8, "change_24h_pct":8.1, "change_7d_pct":15.2,"volume_24h":500000000},
    {"coin":"FLOKI","price_usd":0.00015,"change_1h_pct":0.5, "change_24h_pct":5.2, "change_7d_pct":12.1,"volume_24h":200000000},
    {"coin":"MEME","price_usd":0.012,   "change_1h_pct":1.1, "change_24h_pct":7.3, "change_7d_pct":18.4,"volume_24h":150000000},
    {"coin":"POPCAT","price_usd":0.85,  "change_1h_pct":-0.8,"change_24h_pct":3.1, "change_7d_pct":9.2, "volume_24h":180000000},
    {"coin":"MOG",  "price_usd":0.0000018,"change_1h_pct":1.3,"change_24h_pct":12.4,"change_7d_pct":28.6,"volume_24h":120000000},
    {"coin":"TURBO","price_usd":0.008,  "change_1h_pct":-0.3,"change_24h_pct":2.8, "change_7d_pct":7.1, "volume_24h":90000000},
    {"coin":"BRETT","price_usd":0.12,   "change_1h_pct":0.9, "change_24h_pct":6.5, "change_7d_pct":14.3,"volume_24h":250000000},
    {"coin":"NEIRO","price_usd":0.00082,"change_1h_pct":2.1, "change_24h_pct":15.2,"change_7d_pct":35.8,"volume_24h":300000000},
    {"coin":"PNUT", "price_usd":0.65,   "change_1h_pct":-1.5,"change_24h_pct":-8.3,"change_7d_pct":22.1,"volume_24h":450000000},
    {"coin":"GOAT", "price_usd":0.45,   "change_1h_pct":0.7, "change_24h_pct":4.2, "change_7d_pct":18.5,"volume_24h":200000000},
    {"coin":"MOODENG","price_usd":0.28, "change_1h_pct":1.8, "change_24h_pct":9.7, "change_7d_pct":32.4,"volume_24h":280000000},
    {"coin":"BABYDOGE","price_usd":0.0000000028,"change_1h_pct":0.4,"change_24h_pct":3.1,"change_7d_pct":8.6,"volume_24h":80000000},
    {"coin":"SLERF","price_usd":0.065,  "change_1h_pct":-0.6,"change_24h_pct":1.9, "change_7d_pct":5.3, "volume_24h":60000000},
    {"coin":"MYRO", "price_usd":0.035,  "change_1h_pct":1.2, "change_24h_pct":8.4, "change_7d_pct":19.2,"volume_24h":70000000},
    {"coin":"BOME", "price_usd":0.0085, "change_1h_pct":-0.9,"change_24h_pct":-3.2,"change_7d_pct":4.8, "volume_24h":110000000},
    {"coin":"WEN",  "price_usd":0.00012,"change_1h_pct":0.3, "change_24h_pct":2.1, "change_7d_pct":6.4, "volume_24h":40000000},
    {"coin":"DEGEN","price_usd":0.0042, "change_1h_pct":0.8, "change_24h_pct":5.6, "change_7d_pct":12.8,"volume_24h":55000000},
    {"coin":"LADYS","price_usd":0.00000085,"change_1h_pct":1.4,"change_24h_pct":7.8,"change_7d_pct":16.3,"volume_24h":45000000},
    {"coin":"SAMO", "price_usd":0.025,  "change_1h_pct":-0.2,"change_24h_pct":1.5, "change_7d_pct":4.2, "volume_24h":25000000},
    {"coin":"HOGE", "price_usd":0.00035,"change_1h_pct":0.6, "change_24h_pct":3.8, "change_7d_pct":9.1, "volume_24h":20000000},
    {"coin":"KISHU","price_usd":0.0000000012,"change_1h_pct":0.9,"change_24h_pct":4.5,"change_7d_pct":11.2,"volume_24h":18000000},
    {"coin":"AKITA","price_usd":0.00000042,"change_1h_pct":-0.4,"change_24h_pct":2.1,"change_7d_pct":6.8,"volume_24h":15000000},
    {"coin":"COQ",  "price_usd":0.0000015,"change_1h_pct":1.1,"change_24h_pct":6.3,"change_7d_pct":14.7,"volume_24h":35000000},
    {"coin":"PONKE","price_usd":0.18,   "change_1h_pct":2.3, "change_24h_pct":11.5,"change_7d_pct":25.3,"volume_24h":85000000},
    {"coin":"GIGA", "price_usd":0.042,  "change_1h_pct":0.5, "change_24h_pct":4.8, "change_7d_pct":13.6,"volume_24h":42000000},
    {"coin":"FWOG", "price_usd":0.085,  "change_1h_pct":-1.2,"change_24h_pct":-2.4,"change_7d_pct":8.9, "volume_24h":38000000},
    {"coin":"SUNDOG","price_usd":0.095, "change_1h_pct":1.7, "change_24h_pct":8.2, "change_7d_pct":20.5,"volume_24h":62000000},
    {"coin":"RETARDIO","price_usd":0.52,"change_1h_pct":0.8, "change_24h_pct":5.4, "change_7d_pct":15.8,"volume_24h":48000000},
    {"coin":"BILLY","price_usd":0.038,  "change_1h_pct":-0.7,"change_24h_pct":3.2, "change_7d_pct":9.4, "volume_24h":32000000},
    {"coin":"MEW",  "price_usd":0.0065, "change_1h_pct":1.4, "change_24h_pct":7.6, "change_7d_pct":17.2,"volume_24h":55000000},
    {"coin":"MANEKI","price_usd":0.00028,"change_1h_pct":0.9,"change_24h_pct":4.1, "change_7d_pct":10.8,"volume_24h":28000000},
    {"coin":"SATS", "price_usd":0.00000048,"change_1h_pct":0.3,"change_24h_pct":2.5,"change_7d_pct":7.3,"volume_24h":22000000},
    {"coin":"RATS", "price_usd":0.00082,"change_1h_pct":-0.5,"change_24h_pct":1.8, "change_7d_pct":5.6, "volume_24h":18000000},
    {"coin":"MOCHI","price_usd":0.0018, "change_1h_pct":1.6, "change_24h_pct":9.3, "change_7d_pct":21.4,"volume_24h":30000000},
    {"coin":"LANDWOLF","price_usd":0.0052,"change_1h_pct":0.7,"change_24h_pct":5.1,"change_7d_pct":13.2,"volume_24h":25000000},
    {"coin":"ELON", "price_usd":0.00000014,"change_1h_pct":0.4,"change_24h_pct":3.6,"change_7d_pct":9.8,"volume_24h":16000000},
]

BTC_FALLBACK = {"coin":"BTC","price_usd":94000,"change_1h_pct":0.1,"change_24h_pct":1.2,"change_7d_pct":3.1,"volume_24h":50000000000}


def _parse_gecko_coin(c):
    """Parse one CoinGecko market item into our schema."""
    return {
        "coin":           c["symbol"].upper(),
        "gecko_id":       c["id"],
        "price_usd":      float(c.get("current_price") or 0),
        "change_1h_pct":  float(c.get("price_change_percentage_1h_in_currency")  or 0),
        "change_24h_pct": float(c.get("price_change_percentage_24h_in_currency") or 0),
        "change_7d_pct":  float(c.get("price_change_percentage_7d_in_currency")  or 0),
        "volume_24h":     float(c.get("total_volume")  or 0),
        "market_cap":     float(c.get("market_cap")    or 0),
    }


def fetch_meme_prices():
    """
    FIX: Fetch meme coins BY EXACT COINGECKO ID.
    This guarantees all 40 meme coins are fetched regardless of
    market cap rank. Previously fetching top-100 by market cap
    meant many meme coins (ranked 100-500) were never fetched.
    Also fetches BTC separately for the BTC rotation signal.
    """
    print("Fetching meme coin prices from CoinGecko by ID...")
    all_coins = []

    # Split into batches of 20 (CoinGecko URL length limit)
    batch_size = 20
    batches = [MEME_COIN_IDS[i:i+batch_size]
               for i in range(0, len(MEME_COIN_IDS), batch_size)]

    for batch in batches:
        ids_str = ",".join(batch)
        for attempt in range(3):
            try:
                resp = requests.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency":             "usd",
                        "ids":                     ids_str,
                        "order":                   "market_cap_desc",
                        "per_page":                50,
                        "page":                    1,
                        "sparkline":               False,
                        "price_change_percentage": "1h,24h,7d"
                    },
                    timeout=20
                )
                data = resp.json()
                if isinstance(data, dict):
                    # Rate limited
                    print(f"  Rate limited — waiting 30s...")
                    time.sleep(30)
                    continue
                for c in data:
                    all_coins.append(_parse_gecko_coin(c))
                print(f"  Batch of {len(batch)} ✅ ({len(all_coins)} total)")
                time.sleep(2)
                break
            except Exception as e:
                print(f"  Batch attempt {attempt+1} failed: {e}")
                time.sleep(5)

    # Always fetch BTC separately for BTC signal calculation
    try:
        resp_btc = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd", "ids": "bitcoin",
                "sparkline": False,
                "price_change_percentage": "1h,24h,7d"
            },
            timeout=15
        )
        btc_data = resp_btc.json()
        if isinstance(btc_data, list) and btc_data:
            all_coins.append(_parse_gecko_coin(btc_data[0]))
            print("  BTC fetched ✅")
    except Exception as e:
        print(f"  BTC fetch failed: {e} — using fallback")
        all_coins.append(BTC_FALLBACK)

    if not all_coins:
        print("  ⚠️  CoinGecko unreachable — using full fallback")
        all_coins = MEME_FALLBACK + [BTC_FALLBACK]

    df = pd.DataFrame(all_coins).drop_duplicates(subset='coin').reset_index(drop=True)

    # Force all numeric columns to float, fill NaN with 0
    for col in ['price_usd','change_1h_pct','change_24h_pct','change_7d_pct','volume_24h']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    try:
        df.to_csv('coins_cache.csv', index=False)
    except:
        pass

    print(f"Total coins fetched: {len(df)} ✅")
    print(df[['coin','price_usd','change_24h_pct']].to_string(index=False))
    return df


def fetch_reddit(coin_list, limit=REDDIT_POST_LIMIT):
    print(f"Reddit single-pass scan — {len(coin_list)} coins...")
    rows     = []
    coin_set = set(coin_list)

    for sub in SUBREDDITS:
        try:
            url  = f"https://www.reddit.com/r/{sub}/new.json?limit={limit}"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 429:
                print(f"  r/{sub} rate limited — skipping")
                time.sleep(5)
                continue
            if resp.status_code != 200:
                continue

            children = resp.json().get("data", {}).get("children", [])
            for item in children:
                d          = item["data"]
                text_raw   = (d.get("title","") + " " + d.get("selftext","")).replace('\n',' ').strip()
                text_upper = text_raw.upper()
                for coin in coin_set:
                    if f" {coin} " in f" {text_upper} ":
                        rows.append({
                            "coin_name": coin,
                            "text":      text_raw[:500],
                            "upvotes":   int(d.get("ups", 0)),
                            "comments":  int(d.get("num_comments", 0)),
                            "source":    "reddit",
                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })

            print(f"  r/{sub} ✅ — {len(children)} posts scanned")
            time.sleep(1.5)
        except Exception as e:
            print(f"  r/{sub} error: {e}")

    df     = pd.DataFrame(rows) if rows else EMPTY_POSTS.copy()
    active = df['coin_name'].nunique() if not df.empty else 0
    print(f"Reddit done — {len(df)} mentions across {active} coins ✅")
    return df


def fetch_news(top_coins, n=NEWS_TOP_N):
    print(f"NewsAPI — {n} coins...")
    rows = []
    for coin in top_coins[:n]:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": coin, "language": "en", "sortBy": "publishedAt",
                        "pageSize": 5, "apiKey": NEWS_API_KEY},
                timeout=10
            )
            for article in resp.json().get("articles", []):
                title = article.get("title") or ""
                desc  = article.get("description") or ""
                text  = (title + " " + desc).replace('\n',' ').strip()
                if text:
                    rows.append({
                        "coin_name": coin, "text": text,
                        "upvotes": 0, "comments": 0,
                        "source": "news",
                        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            time.sleep(0.5)
        except Exception as e:
            print(f"  News error ({coin}): {e}")

    df = pd.DataFrame(rows) if rows else EMPTY_POSTS.copy()
    print(f"NewsAPI done — {len(df)} articles ✅")
    return df


def fetch_stocktwits(coin_list, n=NEWS_TOP_N):
    print(f"StockTwits — {n} coins...")
    rows = []
    symbol_map = {
        "DOGE":"DOGE.X","SHIB":"SHIB.X","PEPE":"PEPE.X",
        "WIF":"WIF.X",  "BONK":"BONK.X","FLOKI":"FLOKI.X",
        "BRETT":"BRETT.X","MOG":"MOG.X","TURBO":"TURBO.X",
    }
    for coin in coin_list[:n]:
        st_symbol = symbol_map.get(coin)
        if not st_symbol:
            continue
        try:
            resp = requests.get(
                f"https://api.stocktwits.com/api/2/streams/symbol/{st_symbol}.json",
                timeout=10
            )
            if resp.status_code != 200:
                continue
            for msg in resp.json().get("messages", []):
                body = msg.get("body","").strip()
                if body:
                    rows.append({
                        "coin_name": coin, "text": body[:500],
                        "upvotes": msg.get("likes",{}).get("total",0),
                        "comments": 0, "source": "stocktwits",
                        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            time.sleep(1)
        except Exception as e:
            print(f"  StockTwits error ({coin}): {e}")

    df = pd.DataFrame(rows) if rows else EMPTY_POSTS.copy()
    print(f"StockTwits done — {len(df)} messages ✅")
    return df


print("All fetcher functions ready ✅")

def score_coins(df_posts, df_prices, coin_list):
    print(f"Scoring {len(coin_list)} coins...")

    def get_sentiment(text):
        try:
            return sia.polarity_scores(str(text))['compound']
        except:
            return 0.0

    base = pd.DataFrame({'coin': [c for c in coin_list if c != 'BTC']})

    if not df_posts.empty:
        df_posts = df_posts.copy()
        df_posts['compound']       = df_posts['text'].apply(get_sentiment)
        # sentiment_norm is 0-1: compound(-1,+1) → (compound+1)/2
        df_posts['sentiment_norm'] = (df_posts['compound'] + 1) / 2
    else:
        df_posts = EMPTY_POSTS.copy()
        df_posts['compound']       = 0.0
        df_posts['sentiment_norm'] = 0.5

    # Signal 1 — Mentions
    m  = df_posts.groupby('coin_name').size().reset_index(name='mention_count')
    m.columns = ['coin','mention_count']
    mx = m['mention_count'].max()
    m['mentions_norm'] = m['mention_count'] / mx if mx > 0 else 0

    # Signal 2 — Sentiment (0-1 range)
    s  = df_posts.groupby('coin_name')['sentiment_norm'].mean().reset_index()
    s.columns = ['coin','sentiment_avg']
    s['sentiment_norm'] = s['sentiment_avg']

    # Signal 3 — Engagement (avg upvotes)
    r  = df_posts[df_posts['source'].isin(['reddit','stocktwits'])]
    e  = r.groupby('coin_name')['upvotes'].mean().reset_index()
    e.columns = ['coin','avg_upvotes']
    ex = e['avg_upvotes'].max()
    e['engagement_norm'] = e['avg_upvotes'] / ex if ex > 0 else 0

    # Signal 4 — News count
    nc = df_posts[df_posts['source'] == 'news'].groupby('coin_name').size().reset_index(name='news_count')
    nc.columns = ['coin','news_count']
    nx = nc['news_count'].max()
    nc['news_norm'] = nc['news_count'] / nx if nx > 0 else 0

    # Engagement 24h
    try:
        df_posts['ts'] = pd.to_datetime(df_posts['timestamp'], errors='coerce')
        cutoff         = pd.Timestamp.now() - pd.Timedelta(hours=24)
        df_24h         = df_posts[df_posts['ts'] >= cutoff]
        eng24          = df_24h.groupby('coin_name').size().reset_index(name='engagement_24h')
        eng24.columns  = ['coin','engagement_24h']
    except:
        eng24 = pd.DataFrame(columns=['coin','engagement_24h'])

    # ── FIX 8: all LEFT joins so 0-mention coins still get price data ──
    result = base \
        .merge(m [['coin','mention_count','mentions_norm']], on='coin', how='left') \
        .merge(s [['coin','sentiment_avg','sentiment_norm']], on='coin', how='left') \
        .merge(e [['coin','avg_upvotes','engagement_norm']], on='coin', how='left') \
        .merge(nc[['coin','news_count','news_norm']],        on='coin', how='left') \
        .merge(eng24,                                         on='coin', how='left') \
        .merge(df_prices[['coin','price_usd','change_1h_pct',
                          'change_24h_pct','change_7d_pct','volume_24h']],
               on='coin', how='left')

    # Force all numeric to float, fill NaN with 0
    num_cols = [
        'mention_count','mentions_norm','sentiment_avg','sentiment_norm',
        'avg_upvotes','engagement_norm','news_count','news_norm',
        'engagement_24h','price_usd','change_1h_pct',
        'change_24h_pct','change_7d_pct','volume_24h'
    ]
    for col in num_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0).round(6)

    # Fill missing sentiment with neutral (0.5 = neutral on 0-1 scale)
    result['sentiment_avg']  = result['sentiment_avg'].replace(0, 0.5)
    result['sentiment_norm'] = result['sentiment_norm'].replace(0, 0.5)

    # Signal 5 — Volume (normalised 0-1)
    vmin = result['volume_24h'].min()
    vmax = result['volume_24h'].max()
    result['volume_norm'] = ((result['volume_24h'] - vmin) / (vmax - vmin)).clip(0,1) \
                             if vmax != vmin else 0.5

    # Signal 6 — Price momentum (normalised 0-1)
    result['momentum_norm'] = ((result['change_24h_pct'] + 50) / 100).clip(0, 1)

    # ── FIX 6: sentiment_pct = sentiment_avg * 100 → 0-100 range ──
    # sentiment_avg is 0-1 (not -1 to +1), so *100 gives correct 0-100%
    result['sentiment_pct'] = (result['sentiment_avg'] * 100).round(1)

    # Hype score (weighted 6-signal formula)
    result['hype_score'] = ((
        result['mentions_norm']   * 0.25 +
        result['sentiment_norm']  * 0.20 +
        result['volume_norm']     * 0.20 +
        result['momentum_norm']   * 0.15 +
        result['engagement_norm'] * 0.10 +
        result['news_norm']       * 0.10
    ) * 100).round(1)

    def classify(score):
        if score >= 65: return "Rising"
        if score >= 40: return "Flat"
        return "Falling"

    result['trend_label'] = result['hype_score'].apply(classify)
    result['timestamp']   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # ── BTC ROTATION SIGNAL ──────────────────────────────────
    # Get BTC 24h change from df_prices (BTC is kept in df_prices for this)
    btc_row    = df_prices[df_prices['coin'].str.upper() == 'BTC']
    btc_change = float(btc_row['change_24h_pct'].values[0]) if not btc_row.empty else 0.0
    print(f"  BTC 24h change: {btc_change:+.2f}%")

    def calc_btc_signal(row):
        hype  = row['hype_score']
        # ── FIX 7: sentiment_avg is 0-1, thresholds adjusted accordingly ──
        sent  = row['sentiment_avg']   # 0-1 range (0.5 = neutral)
        chg24 = row['change_24h_pct']
        if btc_change < -3:
            if hype >= 60 and sent >= 0.55:
                return '🚀 BUY',  min(95, 70 + abs(btc_change) * 3)
            elif hype >= 45:
                return '👀 WATCH', min(75, 50 + abs(btc_change) * 2)
            else:
                return '😐 HOLD',  30
        elif btc_change < -1.5:
            if hype >= 65 and sent >= 0.60:
                return '🚀 BUY',  65
            elif hype >= 50:
                return '👀 WATCH', 45
            else:
                return '😐 HOLD',  25
        else:
            if hype >= 70 and chg24 > 5:
                return '🚀 BUY',  60
            elif hype >= 55 and chg24 > 0:
                return '👀 WATCH', 40
            elif hype < 40 or chg24 < -5:
                return '❌ AVOID', 15
            else:
                return '😐 HOLD',  25

    signals               = result.apply(calc_btc_signal, axis=1)
    result['btc_signal']      = [s[0] for s in signals]
    result['btc_confidence']  = [round(s[1], 1) for s in signals]

    # Final safety pass
    result = result.replace([np.inf, -np.inf], 0).fillna(0)

    final_cols = [
        'coin','hype_score','sentiment_avg','sentiment_pct',
        'mention_count','engagement_24h','news_count',
        'price_usd','change_1h_pct','change_24h_pct',
        'change_7d_pct','volume_24h','trend_label',
        'btc_signal','btc_confidence','timestamp'
    ]

    out = result[final_cols].sort_values('hype_score', ascending=False).reset_index(drop=True)
    print(f"Scoring done — {len(out)} coins ✅")
    return out


print("Scorer function ready ✅")

# ============================================================
# SECTION 6 — INITIAL DATA LOAD
# ============================================================

# FIX: use fetch_meme_prices() — fetches by ID not market cap rank
df_coins  = fetch_meme_prices()
COINS     = [c for c in df_coins['coin'].tolist() if c != 'BTC']
df_prices = df_coins[['coin','price_usd','change_1h_pct',
                       'change_24h_pct','change_7d_pct','volume_24h']].copy()

print(f"\nMeme coins loaded: {COINS}")

# ============================================================
# SECTION 7 — SINGLE TEST RUN
# ============================================================

print("\nRunning test score...")
print("=" * 45)

# FIX: use all MEME_SYMBOLS not COINS[:20]
# COINS already contains only meme coins now
TEST_COINS = COINS

df_reddit_t     = fetch_reddit(TEST_COINS)
df_news_t       = fetch_news(TEST_COINS, n=20)
df_stocktwits_t = fetch_stocktwits(TEST_COINS, n=10)

df_posts_t = pd.concat([df_reddit_t, df_news_t, df_stocktwits_t], ignore_index=True)

result_t = score_coins(df_posts_t, df_prices, TEST_COINS)

if not result_t.empty:
    print(f"\n✅ Test successful — {len(result_t)} coins scored")
    print("\nTop 15 Hype Scores:")
    print("=" * 60)
    print(result_t.head(15)[[
        'coin','hype_score','trend_label','sentiment_pct','change_24h_pct'
    ]].to_string(index=False))

    nan_count = result_t.isnull().sum().sum()
    print(f"\nNaN values: {nan_count} {'✅' if nan_count == 0 else '❌'}")

    result_t.to_csv('scored_coins.csv', index=False, encoding='utf-8')
    print("scored_coins.csv saved ✅")
    print(f"Columns: {result_t.columns.tolist()}")
else:
    print("❌ No results")

# ============================================================
# SECTION 8 — LIVE UPDATE LOOP
# ============================================================

print("\n" + "=" * 45)
print("  CryptoSense LIVE ENGINE STARTING")
print("=" * 45)
print("Press Ctrl+C to stop\n")

df_news_cache       = pd.DataFrame()
df_stocktwits_cache = pd.DataFrame()
last_news_time      = 0
update_count        = 0

while True:
    try:
        loop_start    = time.time()
        update_count += 1
        print(f"\n[Update #{update_count}] {datetime.now().strftime('%H:%M:%S')}")

        # Refresh meme coin prices from CoinGecko by ID
        df_coins  = fetch_meme_prices()
        COINS     = [c for c in df_coins['coin'].tolist() if c != 'BTC']
        df_prices = df_coins[['coin','price_usd','change_1h_pct',
                               'change_24h_pct','change_7d_pct','volume_24h']].copy()

        # Reddit every cycle
        df_reddit = fetch_reddit(COINS, REDDIT_POST_LIMIT)

        # News + StockTwits every 5 minutes
        if time.time() - last_news_time > NEWS_REFRESH_EVERY:
            print("Refreshing news + StockTwits...")
            df_news_cache       = fetch_news(COINS, NEWS_TOP_N)
            df_stocktwits_cache = fetch_stocktwits(COINS, NEWS_TOP_N)
            last_news_time = time.time()
        else:
            mins = int((NEWS_REFRESH_EVERY - (time.time() - last_news_time)) / 60)
            print(f"News cache valid — refreshes in ~{mins} min")

        df_posts = pd.concat([df_reddit, df_news_cache, df_stocktwits_cache], ignore_index=True)
        result   = score_coins(df_posts, df_prices, COINS)

        if not result.empty:
            result.to_csv('scored_coins.csv', index=False, encoding='utf-8')
            print(f"\nTop 10 ({len(result)} coins):")
            print("─" * 50)
            print(result.head(10)[['coin','hype_score','trend_label','btc_signal']].to_string(index=False))
            print("─" * 50)
            nan_check = result.isnull().sum().sum()
            print(f"NaN: {nan_check} {'✅' if nan_check == 0 else '❌'}")
            print("scored_coins.csv updated ✅")

        elapsed = time.time() - loop_start
        sleep_t = max(0, UPDATE_INTERVAL - elapsed)
        print(f"Next update in {sleep_t:.1f}s...")
        time.sleep(sleep_t)

    except KeyboardInterrupt:
        print(f"\nStopped ✅  Total updates: {update_count}")
        break
    except Exception as e:
        print(f"Error: {e} — retrying in {UPDATE_INTERVAL}s...")
        time.sleep(UPDATE_INTERVAL)
