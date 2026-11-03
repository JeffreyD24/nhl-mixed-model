"""One-off probe: which Polymarket US public endpoint returns the full order book (all price levels)?
Tries candidate paths for one live market and saves every reply to research/polymarket/samples/book_probe.json."""
import json, glob, urllib.request, urllib.parse, urllib.error, pandas as pd, os, sys
BASE = "https://gateway.polymarket.us"
f = sorted(glob.glob("research/polymarket/20*.csv"))[-1]
slug = pd.read_csv(f).slug.dropna().iloc[-1]
q = urllib.parse.quote(slug, safe="")
paths = [f"/v1/markets/{q}/book", f"/v1/markets/{q}/orderbook", f"/v1/markets/{q}/order-book", f"/v1/markets/{q}/depth",
         f"/v1/markets/{q}/l2", f"/v1/markets/{q}/levels", f"/v1/markets/{q}/trades", f"/v1/markets/{q}", f"/v1/markets/slug/{q}",
         f"/v1/orderbook/{q}", f"/v1/book/{q}", f"/v1/markets/{q}/bbo", "/openapi.json", "/v1/openapi.json", "/swagger.json", "/docs", "/"]
out = {"slug": slug}
for p in paths:
    for sfx in ("", "?depth=50"):
        if sfx and not p.endswith(("book", "orderbook", "order-book", "depth")): continue
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + p + sfx, headers={"User-Agent": "research probe", "Accept": "application/json"}), timeout=15) as r:
                body = r.read().decode(errors="replace"); out[p + sfx] = dict(status=r.status, body=body[:6000])
        except urllib.error.HTTPError as e:
            out[p + sfx] = dict(status=e.code, body=e.read().decode(errors="replace")[:300])
        except Exception as e:
            out[p + sfx] = dict(status="err", body=str(e)[:200])
        print(p + sfx, out[p + sfx]["status"], flush=True)
os.makedirs("research/polymarket/samples", exist_ok=True)
json.dump(out, open("research/polymarket/samples/book_probe.json", "w"), indent=1)
