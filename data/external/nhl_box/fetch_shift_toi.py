"""Skater (and goalie) time on ice per game, 2010-11 .. 2022-23, from the NHL shift-chart feed (api.nhle.com/stats/rest/en/shiftcharts).
  python fetch_shift_toi.py 2014 2015 ...      season START years; run from this folder in GitHub Actions (the Claude workspace cannot reach nhle.com).
Game list = ../hockeyr/team_game_xg_2010_2023.csv.gz (regular season + playoffs). One output row per player per game: shifts and total shift seconds
(typeCode 517 = a real shift; 505 rows are goal markers and are skipped). Raw shifts are NOT stored (the repo's research/shifts/ is already 570 MB for 5 seasons).
Writes parts_toi/{season}.csv.gz and is safe to rerun (games already saved are skipped). Stops early with the real error if the first 25 requests all fail.
Players are not tagged by position here; goalies show up as one very long shift total, join ../nhl_box/goalies_hockeyr_2010_2023.csv.gz on goalie_id to flag them.
"""
import os, sys, time, json, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

os.makedirs("parts_toi", exist_ok=True)
T = pd.read_csv("../hockeyr/team_game_xg_2010_2023.csv.gz", usecols=["game_id", "season", "season_type", "game_date"])
T = T[T.season_type.isin(["R", "P"])].drop_duplicates("game_id")


def secs(s):
    try: m, x = str(s).split(":"); return int(m) * 60 + int(x)
    except Exception: return 0


def one(gid):
    url = f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={gid}"
    err = None
    for k in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r: js = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code in (404, 400): return gid, [], err
            time.sleep(2 * (k + 1))
        except Exception as e:
            err = f"{type(e).__name__} {str(e)[:60]}"; time.sleep(2 * (k + 1))
    else:
        return gid, None, err
    agg = {}
    for x in js.get("data") or []:
        if x.get("typeCode") != 517 or x.get("playerId") is None: continue
        a = agg.setdefault(x["playerId"], dict(team=str(x.get("teamAbbrev") or ""), player=f"{x.get('firstName') or ''} {x.get('lastName') or ''}".strip(), shifts=0, toi_sec=0))
        a["shifts"] += 1; a["toi_sec"] += secs(x.get("duration"))
    return gid, [dict(game_id=gid, player_id=p, **a) for p, a in agg.items()], None


for season in [int(x) for x in sys.argv[1:]]:
    path = f"parts_toi/{season}.csv.gz"
    G = T[T.season == season * 10000 + season + 1]
    old = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
    done = set(old.game_id) if len(old) else set()
    todo = [g for g in G.game_id if g not in done]
    print(f"{season}: {len(G)} games, {len(done)} saved, {len(todo)} to fetch", flush=True)
    rows, errs, empty, t0, fails_in_a_row = [], [], 0, time.time(), 0
    with ThreadPoolExecutor(5) as ex:
        for i, (gid, r, e) in enumerate(ex.map(one, todo), 1):
            if r is None:
                errs.append(f"{gid}: {e}"); fails_in_a_row += 1
                if i <= 25 and fails_in_a_row == i: print(f"  request failing: {gid} {e}", flush=True)
                if fails_in_a_row >= 25 and not rows: print("  STOP: first 25 requests all failed, last error:", e, flush=True); break
                continue
            fails_in_a_row = 0
            if not r: empty += 1; errs.append(f"{gid}: empty feed ({e})") if e else errs.append(f"{gid}: empty feed")
            rows += r
            if i % 100 == 0: print(f"  {i}/{len(todo)} {time.time() - t0:.0f}s", flush=True)
            time.sleep(0.1)
    if rows:
        D = pd.concat([old, pd.DataFrame(rows)], ignore_index=True) if len(old) else pd.DataFrame(rows)
        D.to_csv(path, index=False)
    print(f"{season}: saved {len({r['game_id'] for r in rows})} games, {len(rows)} player-games, empty feeds {empty}, errors {len(errs)} {errs[:3]}", flush=True)
