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
# Nov 6, 2026 (laptop run): paginate every status and report the earliest/latest close_time of settled markets (dates + counts only).
# Markets settled before Kalshi's historical cutoff (GET historical/cutoff; Sep 7, 2026 on Nov 6) are only in historical/markets.
import sys
def scan(ticker, st, path="markets"):
    n, lo, hi, cur = 0, None, None, None
    while True:
        q = dict(series_ticker=ticker, limit=1000)
        if st: q["status"] = st
        if cur: q["cursor"] = cur
        d = get(path, **q); m = d.get("markets", []); n += len(m)
        for x in m:
            c = (x.get("close_time") or "")[:10]
            if c: lo = min(lo or c, c); hi = max(hi or c, c)
        cur = d.get("cursor"); time.sleep(0.3)
        if not cur or not m: return n, lo, hi
if len(sys.argv) > 2 and sys.argv[1] == "--historical":   # e.g. --historical KXNHLGOAL,KXNHLPTS
    print("cutoff", get("historical/cutoff"))
    for t in sys.argv[2].split(","):
        n, lo, hi = scan(t, None, "historical/markets"); print(f"{t}\thistorical={n}\t{lo}..{hi}", flush=True)
    raise SystemExit
S = get("series", category="Sports").get("series", []) or get("series").get("series", [])
print("series total", len(S))
nhl = [s for s in S if "NHL" in (s.get("ticker", "") + s.get("title", "")).upper() or "HOCKEY" in s.get("title", "").upper()]
for s in nhl:
    ns, lo, hi = scan(s["ticker"], "settled"); no, _, _ = scan(s["ticker"], "open")
    print(f"{s['ticker']}\t{s.get('title')}\tsettled={ns}\t{lo}..{hi}\topen={no}", flush=True)
