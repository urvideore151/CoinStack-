from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import json
import os
import time
import threading
import requests as req

app = Flask(__name__)
CORS(app)

CSV_PATH     = "scored_coins.csv"
ALERTS_PATH  = "alerts.json"



_price_cache     = {}          # { "BTC": {"usd": 70000, "change_24h": 1.2}, ... }
_price_cache_ts  = 0.0
_price_lock      = threading.Lock()
PRICE_TTL        = 30          # seconds

# symbol → CoinGecko id
GECKO_IDS = {
    "BTC" : "bitcoin",        "ETH" : "ethereum",
    "SOL" : "solana",         "BNB" : "binancecoin",
    "XRP" : "ripple",         "DOGE": "dogecoin",
    "SHIB": "shiba-inu",      "PEPE": "pepe",
    "WIF" : "dogwifcoin",     "BONK": "bonk",
    "ADA" : "cardano",        "AVAX": "avalanche-2",
    "DOT" : "polkadot",       "LINK": "chainlink",
    "MATIC":"matic-network",  "LTC" : "litecoin",
    "UNI" : "uniswap",        "ATOM": "cosmos",
    "FIL" : "filecoin",       "APT" : "aptos",
}

def _refresh_prices_if_stale():
    """Fetch live prices from CoinGecko if cache is older than PRICE_TTL."""
    global _price_cache, _price_cache_ts
    now = time.time()
    with _price_lock:
        if now - _price_cache_ts < PRICE_TTL:
            return  # still fresh

        ids_str = ",".join(GECKO_IDS.values())
        try:
            resp = req.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids"               : ids_str,
                    "vs_currencies"     : "usd",
                    "include_24hr_change": "true",
                },
                timeout=8,
                headers={"User-Agent": "CoinStack/1.0"},
            )
            if resp.status_code != 200:
                print(f"[prices] CoinGecko HTTP {resp.status_code}")
                return

            data = resp.json()
            new_cache = {}
            for sym, gecko_id in GECKO_IDS.items():
                entry = data.get(gecko_id, {})
                if entry:
                    new_cache[sym] = {
                        "usd"       : float(entry.get("usd", 0) or 0),
                        "change_24h": float(
                            entry.get("usd_24h_change", 0) or 0
                        ),
                    }
            _price_cache    = new_cache
            _price_cache_ts = now
            print(f"[prices] Updated {len(new_cache)} coins from CoinGecko ✅")

        except Exception as e:
            print(f"[prices] CoinGecko fetch failed: {e}")


def hydrate_coins_with_prices(coins: list) -> list:
    """
    Merge live CoinGecko prices into coin dicts.
    Always overwrites price_usd and change_24h
    with live data when available.
    """
    _refresh_prices_if_stale()
    result = []
    for coin in coins:
        sym  = str(coin.get("coin", "")).upper()
        live = _price_cache.get(sym)
        if live and live["usd"] > 0:
            coin = dict(coin)           # don't mutate original
            coin["price_usd"]  = live["usd"]
            # keep 24h pct columns consistent
            coin["change_24h"] = live["change_24h"]
            coin["change_24h_pct"] = live["change_24h"]
        result.append(coin)
    return result


def load_csv():
    """Load scored_coins.csv, normalise all fields, hydrate prices."""
    if not os.path.exists(CSV_PATH):
        return []

    try:
        df = pd.read_csv(CSV_PATH)

        # sparkline
        if "sparkline" not in df.columns:
            df["sparkline"] = [[] for _ in range(len(df))]
        else:
            def parse_spark(v):
                try:
                    return json.loads(v) if isinstance(v, str) else []
                except Exception:
                    return []
            df["sparkline"] = df["sparkline"].apply(parse_spark)

        # engagement alias
        if "engagement_24h" in df.columns:
            df["engagement"] = df["engagement_24h"]
        elif "engagement" not in df.columns:
            df["engagement"] = 0

        # numeric cleanup
        numeric_cols = [
            "hype_score", "sentiment_avg", "sentiment_pct",
            "mention_count", "engagement_24h", "engagement",
            "news_count", "price_usd",
            "change_1h_pct", "change_24h_pct", "change_7d_pct",
            "volume_24h",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col], errors="coerce"
                ).fillna(0)

        # column aliases for frontend compatibility
        if "change_1h_pct" in df.columns:
            df["change_1h"]  = df["change_1h_pct"]
            df["change_24h"] = df["change_24h_pct"]
            df["change_7d"]  = df["change_7d_pct"]

        # strip emoji from trend_label
        if "trend_label" in df.columns:
            df["trend_label"] = (
                df["trend_label"]
                .str.replace("🔥 ", "", regex=False)
                .str.replace("➡️ ", "", regex=False)
                .str.replace("❄️ ", "", regex=False)
                .str.strip()
            )

        df = df.fillna(0)
        coins = df.to_dict(orient="records")

        # ── Hydrate with live USD prices ──────────────────
        return hydrate_coins_with_prices(coins)

    except Exception as e:
        print(f"[api.py] CSV read error: {e}")
        return []


BTC_CORR = {
    "PEPE": -0.82,
    "DOGE": -0.71,
    "SHIB": -0.65,
    "BONK": -0.60,
    "WIF" : -0.58,
}

_rotation_cache    = None
_rotation_cache_ts = 0.0
ROTATION_TTL       = 60        # seconds

def _fetch_btc_dominance():
    """Fetch BTC dominance % from CoinGecko /global."""
    try:
        resp = req.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=8,
            headers={"User-Agent": "CoinStack/1.0"},
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}) \
                       .get("market_cap_percentage", {}) \
                       .get("btc", None)
    except Exception as e:
        print(f"[rotation] BTC dominance fetch failed: {e}")
    return None


def compute_rotation_radar():
    """
    Build the Market Rotation Radar payload.
    Cached for ROTATION_TTL seconds.
    """
    global _rotation_cache, _rotation_cache_ts
    now = time.time()

    if _rotation_cache and (now - _rotation_cache_ts < ROTATION_TTL):
        return _rotation_cache

    # Ensure price cache is fresh
    _refresh_prices_if_stale()

    btc  = _price_cache.get("BTC", {"usd": 0, "change_24h": 0})
    eth  = _price_cache.get("ETH", {"usd": 0, "change_24h": 0})
    btc_chg = btc["change_24h"]
    eth_chg = eth["change_24h"]

    btc_hard_drop = btc_chg < -3.0
    btc_mod_drop  = -3.0 <= btc_chg < -1.5
    eth_drop      = eth_chg < -3.0

    btc_dominance = _fetch_btc_dominance()
    dom_falling   = btc_dominance is not None and btc_dominance < 52
    dom_rising    = btc_dominance is not None and btc_dominance > 56

    # Per-meme-coin signal
    meme_coins = []
    for sym, base_corr in BTC_CORR.items():
        live     = _price_cache.get(sym, {})
        live_chg = live.get("change_24h", 0)

        # Real-time boost: if BTC falls AND meme pumps → stronger inverse signal
        boost = 0.0
        if btc_hard_drop and live_chg > 0:
            boost = -0.05
        elif btc_hard_drop and live_chg < 0:
            boost = +0.08

        corr = max(-1.0, min(-0.1, base_corr + boost))

        if btc_hard_drop and corr < -0.70:
            signal       = "BUY SIGNAL"
            signal_emoji = "🚀"
        elif (btc_hard_drop or btc_mod_drop) and corr < -0.60:
            signal       = "ALERT"
            signal_emoji = "⚡"
        else:
            signal       = "WATCH"
            signal_emoji = "👀"

        meme_coins.append({
            "coin"        : sym,
            "corr"        : round(corr, 2),
            "signal"      : signal,
            "signal_emoji": signal_emoji,
            "live_change" : round(live_chg, 2),
            "price_usd"   : live.get("usd", 0),
        })

    # Overall prediction
    prediction = None
    confidence = 0
    if btc_hard_drop and dom_falling:
        prediction = "PEPE/DOGE/BONK likely to spike in next 2–4 hours"
        confidence = 82
    elif btc_hard_drop:
        prediction = "Meme spike possible — watch BTC dominance"
        confidence = 64
    elif btc_mod_drop or eth_drop:
        prediction = "Moderate rotation signal — monitor closely"
        confidence = 48
    elif dom_falling:
        prediction = "Capital rotating to altcoins — meme momentum building"
        confidence = 55

    def btc_signal_label(chg):
        if chg < -3:  return "Meme spike likely"
        if chg < -1.5: return "Moderate signal"
        return "Stable"

    _rotation_cache = {
        "btc": {
            "change_24h": round(btc_chg, 2),
            "price_usd" : btc["usd"],
            "signal"    : btc_signal_label(btc_chg),
        },
        "eth": {
            "change_24h": round(eth_chg, 2),
            "price_usd" : eth["usd"],
            "signal"    : btc_signal_label(eth_chg),
        },
        "btc_dominance": round(btc_dominance, 2) if btc_dominance else None,
        "dom_trend"    : (
            "Falling ✅" if dom_falling else
            "Rising ⚠️"  if dom_rising  else
            "Stable"
        ),
        "dom_falling"  : dom_falling,
        "btc_alert"    : btc_hard_drop or btc_mod_drop,
        "meme_coins"   : meme_coins,
        "prediction"   : prediction,
        "confidence"   : confidence,
        "ts"           : time.strftime("%H:%M:%S"),
    }
    _rotation_cache_ts = now
    return _rotation_cache



def load_alerts():
    """Load alerts from alerts.json."""
    if not os.path.exists(ALERTS_PATH):
        return []
    try:
        with open(ALERTS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_alerts(alerts: list):
    """Persist alerts to alerts.json."""
    try:
        with open(ALERTS_PATH, "w") as f:
            json.dump(alerts, f, indent=2)
    except Exception as e:
        print(f"[alerts] Save failed: {e}")


def evaluate_alerts_against_coins(coins: list, radar: dict):
    """
    Check each active/untriggered alert against live data.
    Returns list of (alert, message) pairs that just fired.
    Mutates alerts in-place (sets triggered=True).
    """
    alerts  = load_alerts()
    fired   = []
    updated = False

    for alert in alerts:
        if not alert.get("active", True):
            continue
        if alert.get("triggered", False):
            continue

        coin_sym = alert.get("coin", "").upper()
        atype    = alert.get("type", "")
        thresh   = float(alert.get("threshold", 0))
        coin     = next(
            (c for c in coins
             if str(c.get("coin", "")).upper() == coin_sym),
            None,
        )
        message = None

        if atype == "hype_above" and coin:
            if coin.get("hype_score", 0) > thresh:
                message = (
                    f"{coin_sym} hype score hit "
                    f"{coin['hype_score']:.1f} (above {thresh})"
                )
        elif atype == "hype_below" and coin:
            if coin.get("hype_score", 0) < thresh:
                message = (
                    f"{coin_sym} hype dropped to "
                    f"{coin['hype_score']:.1f} (below {thresh})"
                )
        elif atype == "sentiment_drop" and coin:
            if coin.get("sentiment_pct", 100) < thresh:
                message = (
                    f"{coin_sym} sentiment at "
                    f"{coin['sentiment_pct']}% (below {thresh}%)"
                )
        elif atype == "price_above" and coin:
            if coin.get("price_usd", 0) > thresh:
                message = (
                    f"{coin_sym} price hit "
                    f"${coin['price_usd']:.6f} (above ${thresh})"
                )
        elif atype == "price_below" and coin:
            p = coin.get("price_usd", 0)
            if 0 < p < thresh:
                message = (
                    f"{coin_sym} price dropped to "
                    f"${p:.6f} (below ${thresh})"
                )
        elif atype == "rotation_signal":
            if radar and radar.get("btc_alert"):
                chg = radar["btc"]["change_24h"]
                message = (
                    f"BTC rotation signal fired! "
                    f"BTC {chg:+.1f}% — {coin_sym} spike expected"
                )

        if message:
            fired.append({"alert": alert, "message": message})
            alert["triggered"]   = True
            alert["triggered_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            updated = True

    if updated:
        save_alerts(alerts)

    return fired

@app.route("/api/coins", methods=["GET"])
def get_all_coins():
    """Return all scored coins sorted by hype score (with live prices)."""
    data = load_csv()
    data.sort(key=lambda x: x.get("hype_score", 0), reverse=True)
    return jsonify(data)


@app.route("/api/coins/<symbol>", methods=["GET"])
def get_coin(symbol):
    """Return a single coin by symbol (with live price)."""
    data   = load_csv()
    symbol = symbol.upper()
    coin   = next(
        (c for c in data if str(c.get("coin", "")).upper() == symbol),
        None,
    )
    if coin:
        return jsonify(coin)
    return jsonify({"error": f"{symbol} not found"}), 404


@app.route("/api/top", methods=["GET"])
def get_top():
    """Return top N coins by hype score."""
    data = load_csv()
    data.sort(key=lambda x: x.get("hype_score", 0), reverse=True)
    n = int(request.args.get("n", 3))
    return jsonify(data[:n])


@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify(load_csv())


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Return global dashboard metrics."""
    data = load_csv()
    if not data:
        return jsonify({
            "total_mentions" : 0,   "total_change"   : 0,
            "avg_hype_score" : 0,   "hype_meter"     : 50,
            "hype_label"     : "Low Hype",
            "sentiment_pct"  : 50,  "sentiment_label": "Neutral",
            "trend_strength" : 50,  "trend_label"    : "STEADY",
        })

    scores    = [c.get("hype_score", 0)     for c in data]
    mentions  = [c.get("mention_count", 0)  for c in data]
    sent_pcts = [c.get("sentiment_pct", 50) for c in data]

    avg_hype = round(sum(scores) / len(scores), 1) if scores else 0
    avg_sent = round(sum(sent_pcts) / len(sent_pcts))      if sent_pcts else 50
    top_change = round(data[0].get("change_24h_pct", 0), 1) if data else 0

    return jsonify({
        "total_mentions" : int(sum(mentions)),
        "total_change"   : top_change,
        "avg_hype_score" : avg_hype,
        "hype_meter"     : min(100, int(avg_hype)),
        "hype_label"     : (
            "High Hype" if avg_hype >= 65 else
            "Moderate"  if avg_hype >= 40 else "Low Hype"
        ),
        "sentiment_pct"  : avg_sent,
        "sentiment_label": "Bullish" if avg_sent >= 60 else "Neutral",
        "trend_strength" : min(100, int(avg_hype * 1.1)),
        "trend_label"    : "SURGING" if avg_hype >= 70 else "STEADY",
    })


@app.route("/api/news", methods=["GET"])
def get_news():
    """
    Serve live posts from NewsAPI + Reddit public JSON.
    Pass ?coin=PEPE to filter, or omit for all crypto news.
    """
    coin    = request.args.get("coin", "").upper()
    api_key = "1016246d34a04562909f1d9edf842803"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36"
        )
    }
    posts = []

    # NewsAPI
    query = coin if coin else "cryptocurrency meme coin"
    try:
        resp = req.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query, "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 10, "apiKey": api_key,
            },
            timeout=10,
        )
        for a in resp.json().get("articles", []):
            posts.append({
                "title"    : a.get("title") or "",
                "coin"     : coin or None,
                "subreddit": (a.get("source") or {}).get("name", "News"),
                "upvotes"  : 0,
                "sentiment": "neutral",
                "time"     : (a.get("publishedAt") or "")[:10],
                "url"      : a.get("url", ""),
                "source"   : "news",
            })
    except Exception as e:
        print(f"[api/news] NewsAPI error: {e}")

    # Reddit public JSON
    reddit_q = f"{coin}+crypto" if coin else "meme+coin+crypto"
    try:
        r = req.get(
            f"https://www.reddit.com/search.json"
            f"?q={reddit_q}&sort=new&limit=10&t=day",
            headers=headers, timeout=10,
        )
        if r.status_code == 200:
            for item in r.json().get("data", {}).get("children", []):
                d = item["data"]
                posts.append({
                    "title"    : d.get("title", ""),
                    "coin"     : coin or None,
                    "subreddit": d.get("subreddit_name_prefixed", "r/crypto"),
                    "upvotes"  : int(d.get("ups", 0)),
                    "sentiment": "neutral",
                    "time"     : "Reddit",
                    "url"      : f"https://reddit.com{d.get('permalink','')}",
                    "source"   : "reddit",
                })
    except Exception as e:
        print(f"[api/news] Reddit error: {e}")

    posts.sort(key=lambda x: x.get("upvotes", 0), reverse=True)
    return jsonify(posts)

@app.route("/api/rotation", methods=["GET"])
def get_rotation():
    """
    Full Market Rotation Radar.
    Returns BTC/ETH change, BTC dominance, meme correlations,
    and a natural-language prediction with confidence %.
    """
    radar = compute_rotation_radar()
    return jsonify(radar)


@app.route("/api/rotation/memes", methods=["GET"])
def get_rotation_memes():
    """
    Just the meme-coin correlation + signal table.
    Useful for the coin table column without full radar payload.
    """
    radar = compute_rotation_radar()
    return jsonify({
        "meme_coins": radar.get("meme_coins", []),
        "btc_alert" : radar.get("btc_alert", False),
        "ts"        : radar.get("ts", ""),
    })



@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Return all saved alerts."""
    return jsonify(load_alerts())


@app.route("/api/alerts", methods=["POST"])
def create_alert():
    """
    Create a new alert.
    Body JSON:
    {
        "coin"         : "PEPE",
        "type"         : "hype_above" | "hype_below" | "sentiment_drop"
                       | "price_above" | "price_below"
                       | "mention_spike" | "rotation_signal",
        "threshold"    : 75,
        "notify_popup" : true,
        "notify_ticker": true,
        "notify_browser": false
    }
    """
    body = request.get_json(silent=True) or {}
    if not body.get("coin") or not body.get("type"):
        return jsonify({"error": "coin and type are required"}), 400

    alert = {
        "id"            : int(time.time() * 1000),
        "coin"          : str(body["coin"]).upper(),
        "type"          : body["type"],
        "threshold"     : float(body.get("threshold", 0)),
        "notify_popup"  : bool(body.get("notify_popup", True)),
        "notify_ticker" : bool(body.get("notify_ticker", True)),
        "notify_browser": bool(body.get("notify_browser", False)),
        "active"        : True,
        "triggered"     : False,
        "created_at"    : time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    alerts = load_alerts()
    alerts.append(alert)
    save_alerts(alerts)
    return jsonify(alert), 201


@app.route("/api/alerts/<int:alert_id>", methods=["PATCH"])
def update_alert(alert_id):
    """
    Toggle active/reset triggered.
    Body: { "active": true/false }  or  { "triggered": false }
    """
    body   = request.get_json(silent=True) or {}
    alerts = load_alerts()
    target = next((a for a in alerts if a["id"] == alert_id), None)
    if not target:
        return jsonify({"error": "not found"}), 404

    if "active" in body:
        target["active"]    = bool(body["active"])
    if "triggered" in body:
        target["triggered"] = bool(body["triggered"])

    save_alerts(alerts)
    return jsonify(target)


@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
def delete_alert(alert_id):
    """Delete an alert by id."""
    alerts  = load_alerts()
    updated = [a for a in alerts if a["id"] != alert_id]
    if len(updated) == len(alerts):
        return jsonify({"error": "not found"}), 404
    save_alerts(updated)
    return jsonify({"deleted": alert_id})


@app.route("/api/alerts/evaluate", methods=["POST"])
def evaluate_alerts():
    """
    Manually trigger alert evaluation (also called by background thread).
    Returns list of alerts that fired in this run.
    """
    coins = load_csv()
    radar = compute_rotation_radar()
    fired = evaluate_alerts_against_coins(coins, radar)
    return jsonify({
        "checked": len(load_alerts()),
        "fired"  : [
            {"alert_id": f["alert"]["id"], "message": f["message"]}
            for f in fired
        ],
    })


def _background_evaluator():
    """Evaluate alerts every 30s in the background."""
    while True:
        time.sleep(30)
        try:
            coins = load_csv()
            radar = compute_rotation_radar()
            fired = evaluate_alerts_against_coins(coins, radar)
            if fired:
                for f in fired:
                    print(
                        f"[alert fired] {f['alert']['coin']} — "
                        f"{f['message']}"
                    )
        except Exception as e:
            print(f"[alert thread] Error: {e}")


@app.route("/health", methods=["GET"])
def health():
    csv_exists = os.path.exists(CSV_PATH)
    rows       = len(load_csv()) if csv_exists else 0
    alerts     = len(load_alerts())
    return jsonify({
        "status"       : "ok",
        "csv_exists"   : csv_exists,
        "coins"        : rows,
        "alerts_saved" : alerts,
        "price_cache"  : len(_price_cache),
        "price_cache_age_s": round(time.time() - _price_cache_ts, 1),
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  CoinStack API — http://localhost:5000")
    print("=" * 50)
    print(f"  CSV path   : {CSV_PATH}")
    print(f"  CSV found  : {os.path.exists(CSV_PATH)}")
    print(f"  Alerts file: {ALERTS_PATH}")
    print("=" * 50)
    print("  NEW endpoints:")
    print("    GET  /api/rotation          Market Rotation Radar")
    print("    GET  /api/rotation/memes    Meme correlation table")
    print("    GET  /api/alerts            List alerts")
    print("    POST /api/alerts            Create alert")
    print("    PATCH/DELETE /api/alerts/:id")
    print("    POST /api/alerts/evaluate   Manual eval run")
    print("=" * 50)

    # Start background alert evaluator
    t = threading.Thread(target=_background_evaluator, daemon=True)
    t.start()
    print("  Background alert evaluator started ✅")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=False)
