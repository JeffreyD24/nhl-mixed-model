"""
Past NHL player-prop lines from BettingPros' public web API (the same calls their site makes; free, no account). Personal research use,
paced politely (about 1 request per 1.5 s). Copied from nfl-mixed-model props_bettingpros_nfl.py (Nov 7, 2026, NHL player props model).
Probe (Nov 7, 2026): NHL player-prop markets 318 goals, 319 points, 320 assists, 321 shots, 322 saves, 362 blocked shots (from Nov 2023).
History starts in April 2022 (Jan/Mar 2022 dates return 0 offers). Books seen: DK 12, FD 10, Caesars 13, BetMGM 19, BetRivers 18,
theScore 33, Hard Rock 49, ... plus the BettingPros consensus (0).
For every NHL regular-season game date (data/box_hist.csv.gz + state/box_2026_27.csv dates; preseason dates before Oct 1 dropped):
  - each book's last line + price before the game (with its update time) = the close
  - the opening line + price + which book + when it was first posted (ONE opener per selection, the first book to post)
  python props_bettingpros_nhl.py WORKDIR [--from 2022-04-01] [--to 2026-04-20] [--max-dates 40] [--newest-first]
Writes data/props_history/bettingpros_nhl/{date}.csv.gz (one row per game x market x player x side x book); dates saved are skipped.
"""
import os, sys, json, time, random, urllib.request, urllib.parse, urllib.error
import datetime as dt
import pandas as pd

W = os.path.abspath(sys.argv[1])
ARG = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
OUT = os.path.join(W, "data", "props_history", "bettingpros_nhl"); os.makedirs(OUT, exist_ok=True)
KEY = "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh"      # BettingPros' public web-client key (what bettingpros.com itself sends)
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36", "Accept": "application/json",
       "x-api-key": KEY, "Origin": "https://www.bettingpros.com", "Referer": "https://www.bettingpros.com/"}
MARKETS = {318: "goals", 319: "points", 320: "assists", 321: "shots", 322: "saves", 362: "blocks"}
BOOKS = {0: "consensus", 12: "draftkings", 10: "fanduel", 19: "betmgm", 13: "caesars", 18: "betrivers", 24: "bet365", 14: "fanatics",
         33: "thescore", 49: "hardrock", 15: "sugarhouse", 27: "partycasino", 2: "pinnacle", 36: "underdog", 37: "prizepicks", 63: "sleeper"}


def get(path, params):
    url = f"https://api.bettingpros.com/v3/{path}?" + urllib.parse.urlencode(params)
    for i in range(5):
        time.sleep(1.2 + random.random() * 0.6)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=40) as r: return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504): time.sleep(20 * (i + 1)); continue
            raise
        except Exception:
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"gave up on {path}")


def one_date(day):
    ev = get("events", dict(sport="NHL", date=day)).get("events", [])
    if not ev: return pd.DataFrame(), 0
    info = {e["id"]: e for e in ev}
    rows = []
    for k in range(0, len(ev), 3):
        ids = ":".join(str(e["id"]) for e in ev[k:k + 3]); page = 1
        while True:
            d = get("offers", dict(sport="NHL", market_id=":".join(map(str, MARKETS)), event_id=ids, location="ALL", limit=50, page=page))
            for o in d.get("offers", []):
                e = info.get(o.get("event_id"), {}); parts = {str(q.get("id")): q for q in (o.get("participants") or [])}
                for s in o.get("selections", []):
                    op = s.get("opening_line") or {}
                    # anytime TD: one offer per game, one selection per player (selection.participant = player id, label = name, no side);
                    # over/under markets: one offer per player, selections over/under. Nov 6, 2026 fix (was participants[0] for every row).
                    sp = str(s.get("participant") or "")
                    p = parts.get(sp) or (o.get("participants") or [{}])[0]
                    pid = int(sp) if sp.isdigit() else o.get("player_id")
                    side = s.get("selection") or "yes"
                    for b in s.get("books", []):
                        for ln in b.get("lines", []):
                            if not ln.get("main", True): continue
                            rows.append(dict(date=day, event_id=o.get("event_id"), home=e.get("home"), away=e.get("visitor"),
                                             scheduled=e.get("scheduled"), stat=MARKETS.get(o.get("market_id")), bp_player_id=pid,
                                             player=p.get("name") or s.get("label"), team=(p.get("player") or {}).get("team"), side=side,
                                             book=BOOKS.get(b.get("id"), str(b.get("id"))), line=ln.get("line"), price=ln.get("cost"),
                                             updated=ln.get("updated"), open_line=op.get("line"), open_price=op.get("cost"),
                                             open_book=BOOKS.get(op.get("book_id"), str(op.get("book_id"))), open_time=op.get("created")))
            pg = d.get("_pagination") or {}
            if page >= (pg.get("total_pages") or 1): break
            page += 1
    return pd.DataFrame(rows), len(ev)


def main():
    ds = set(pd.read_csv(os.path.join(W, "data", "box_hist.csv.gz"), usecols=["date"]).date)
    cur = os.path.join(W, "state", "box_2026_27.csv")
    if os.path.exists(cur): ds |= set(pd.read_csv(cur, usecols=["date"]).date)
    dates = sorted(d for d in ds if isinstance(d, str) and d[5:7] not in ("07", "08", "09"))   # no preseason
    y = (dt.date.today() - dt.timedelta(days=1))
    lo, hi = ARG("--from", "2022-04-01"), ARG("--to", str(y))
    todo = [d for d in dates if lo <= d <= hi and d <= str(y) and not os.path.exists(os.path.join(OUT, f"{d}.csv.gz"))]
    if "--newest-first" in sys.argv: todo = todo[::-1]
    todo = todo[: int(ARG("--max-dates", "40"))]
    if not todo: print("all dates already saved"); return
    for d in todo:
        try:
            R, n = one_date(d)
        except Exception as e:
            print(f"{d}: failed ({e}); will retry next run", flush=True); continue
        R.to_csv(os.path.join(OUT, f"{d}.csv.gz"), index=False)
        print(f"{d}: {n} games, {len(R)} rows, {R.bp_player_id.nunique() if len(R) else 0} players, "
              f"markets {sorted(R.stat.dropna().unique()) if len(R) else []}, books {sorted(R.book.unique()) if len(R) else []}", flush=True)


if __name__ == "__main__":
    main()
