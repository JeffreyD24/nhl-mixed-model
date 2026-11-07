"""Nov 7, 2026 (NHL props model, RULE 9/12): which Kalshi series cover NHL player props? Runs on an Actions runner (api.kalshi.com and
api.elections.kalshi.com are blocked in the Claude workspace). Prints series tickers, titles and how many settled/open markets each has:
metadata and COUNTS only, no prices or trades (RULE 8: Kalshi data goes only to JeffreyD24/private)."""
import json, time, urllib.request, urllib.parse
HOSTS = ["https://api.elections.kalshi.com/trade-api/v2", "https://api.kalshi.com/trade-api/v2"]
def get(path, **q):
    for h in HOSTS:
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(f"{h}/{path}?" + urllib.parse.urlencode(q),
                                                     headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}), timeout=40).read())
        except Exception as e:
            err = e
    print("failed", path, str(err)[:80]); return {}
S = get("series", category="Sports").get("series", []) or get("series").get("series", [])
print("series total", len(S))
nhl = [s for s in S if "NHL" in (s.get("ticker", "") + s.get("title", "")).upper() or "HOCKEY" in s.get("title", "").upper()]
for s in nhl:
    n = {}
    for st in ("settled", "open"):
        d = get("markets", series_ticker=s["ticker"], status=st, limit=1000); n[st] = len(d.get("markets", [])) + (1000 if d.get("cursor") else 0) * 0
        time.sleep(0.5)
    print(f"{s['ticker']}\t{s.get('title')}\tsettled>={n['settled']}\topen={n['open']}")
