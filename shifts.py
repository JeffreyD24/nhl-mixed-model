"""
NHL shift charts: every player's every shift (period, start, end, length), plus the goal events the NHL lists with them,
for each finished game. Source: the NHL's public stats API (no key). The NBA equivalent is research/minutes/.
Writes research/shifts/YYYY-MM-DD.csv (one file per game date, ET) and skips games already saved.
  python shifts.py WORKDIR                 yesterday and the day before (run by the morning workflow)
  python shifts.py WORKDIR --from 2026-10-07   every date from then to yesterday (backfill)
"""
import os, sys, json, time, urllib.request
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd

W = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.getcwd()
OUT = os.path.join(W, "research", "shifts"); os.makedirs(OUT, exist_ok=True)
ET = ZoneInfo("America/New_York")
TODAY = pd.Timestamp(dt.datetime.now(ET).date())


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: return json.loads(r.read())
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    print("Fetch failed:", url, type(err).__name__); return None


def secs(s):
    try: m, x = str(s).split(":"); return int(m) * 60 + int(x)
    except Exception: return None


def day(d):
    path = os.path.join(OUT, f"{d.date()}.csv")
    old = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(columns=["nhl_game_id"])
    have = set(old.nhl_game_id.astype(int)) if len(old) else set()
    sc = get(f"https://api-web.nhle.com/v1/score/{d.date()}")
    if not sc: return 0
    rows = []
    for g in sc.get("games", []):
        if g.get("gameType") not in (2, 3) or g.get("gameState") not in ("OFF", "FINAL") or int(g["id"]) in have: continue
        js = get(f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={g['id']}")
        if not js or not js.get("data"): print(f"  {d.date()} game {g['id']}: no shift chart yet"); continue
        home, away = g["homeTeam"]["abbrev"].lower(), g["awayTeam"]["abbrev"].lower()
        for x in js["data"]:
            rows.append(dict(date=str(d.date()), nhl_game_id=int(g["id"]), away=away, home=home,
                             team=str(x.get("teamAbbrev") or "").lower(), player_id=x.get("playerId"),
                             player=f"{x.get('firstName') or ''} {x.get('lastName') or ''}".strip(), period=x.get("period"),
                             shift_number=x.get("shiftNumber"), start=x.get("startTime"), end=x.get("endTime"),
                             start_sec=secs(x.get("startTime")), end_sec=secs(x.get("endTime")), duration_sec=secs(x.get("duration")),
                             type_code=x.get("typeCode"), event=x.get("eventDescription"), event_detail=x.get("detailCode")))
        time.sleep(0.3)
    if rows:
        D = pd.concat([old, pd.DataFrame(rows)], ignore_index=True) if len(old) else pd.DataFrame(rows)
        D.to_csv(path, index=False)
    n = len({r["nhl_game_id"] for r in rows})
    print(f"{d.date()}: {n} new games, {len(rows)} shift rows")
    return n


def main():
    if "--from" in sys.argv:
        start = pd.Timestamp(sys.argv[sys.argv.index("--from") + 1])
        days = pd.date_range(start, TODAY - pd.Timedelta(days=1))
    else:
        days = [TODAY - pd.Timedelta(days=2), TODAY - pd.Timedelta(days=1)]
    total = sum(day(d) for d in days)
    print(f"Shift charts: {total} games saved.")


if __name__ == "__main__":
    main()
