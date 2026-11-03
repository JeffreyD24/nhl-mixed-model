"""Job B: NHL starting goalies and skater TOI, 2011-12 .. 2022-23, from the public NHL API (api-web.nhle.com).
python fetch_nhl_box.py [season_start_years...]   run from this folder, in GitHub Actions (the Claude workspace cannot reach nhle.com).
Game list = regular-season games in ../hockeyr/team_game_xg_2010_2023.csv.gz. Safe to rerun: games already in parts/ are skipped.
Writes parts/{season}_goalies.csv, parts/{season}_skaters.csv, then combines into goalies_2011_2023.csv and skaters_2011_2023.csv.gz."""
import os, sys, glob, json, time, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
os.makedirs("parts", exist_ok=True)
H = pd.read_csv("../hockeyr/team_game_xg_2010_2023.csv.gz", usecols=["game_id", "season", "season_type", "game_date"])
H = H[H.season_type == "R"].drop_duplicates("game_id")
SEASONS = [int(x) for x in sys.argv[1:]] or list(range(2011, 2023))

def toi(s):
    try: m, sec = str(s).split(":"); return int(m) * 60 + int(sec)
    except Exception: return 0

MAX_CONSEC_FAIL = 20          # stop the whole run after this many failed games in a row
TIMEOUT, TRIES = 20, 3        # seconds per request, attempts per game
ABORT, LOCK = threading.Event(), threading.Lock()
consec, first_err = 0, []

def err_text(gid, e):
    msg = f"{gid}: {type(e).__name__} {str(e)[:150]}"
    if isinstance(e, urllib.error.HTTPError):
        try: msg += f" | HTTP {e.code} body: {e.read()[:150]!r}"
        except Exception: msg += f" | HTTP {e.code}"
    return msg

def one(gid):
    global consec
    if ABORT.is_set(): return gid, None, None, "skipped (aborted)"
    url = f"https://api-web.nhle.com/v1/gamecenter/{gid}/boxscore"
    for k in range(TRIES):
        try:
            # send a browser-style User-Agent: shifts.py and probe_nhle.py do, and they answer in 0.3 s from GitHub; the bare Python-urllib agent is the likely reason
            # the first run hung (Nov 3, 2026; not proven)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r: b = json.loads(r.read()); break
        except Exception as e:
            if isinstance(e, urllib.error.HTTPError) and e.code == 404: k = TRIES - 1   # missing game: don't retry
            if k >= TRIES - 1:
                msg = err_text(gid, e)
                with LOCK:
                    if not first_err: first_err.append(msg); print("FIRST ERROR:", msg, flush=True)
                    consec += 1
                    if consec >= MAX_CONSEC_FAIL and not ABORT.is_set():
                        ABORT.set(); print(f"ABORT: {consec} failed games in a row. Last error: {msg}", flush=True)
                return gid, None, None, msg
            time.sleep(2 * (k + 1))
    with LOCK: consec = 0
    G, S = [], []
    for side in ("homeTeam", "awayTeam"):
        t = b[side]; ps = b["playerByGameStats"][side]
        gs = [g for g in ps.get("goalies", []) if toi(g.get("toi")) > 0]
        flag = [g for g in gs if g.get("starter")]
        starter = flag[0] if flag else (gs[0] if gs else None); src = "flag" if flag else "first_listed"
        for g in gs:
            G.append(dict(game_id=gid, date=b.get("gameDate"), team=t.get("abbrev"), is_home=int(side == "homeTeam"), goalie_id=g["playerId"],
                          starter=int(starter is not None and g["playerId"] == starter["playerId"]), starter_source=src,
                          shots_against=g.get("shotsAgainst"), goals_against=g.get("goalsAgainst"), toi_sec=toi(g.get("toi"))))
        for grp in ("forwards", "defense"):
            for p in ps.get(grp, []):
                S.append(dict(game_id=gid, team=t.get("abbrev"), is_home=int(side == "homeTeam"), player_id=p["playerId"], pos=grp, toi_sec=toi(p.get("toi"))))
    return gid, G, S, None

for s in SEASONS:
    gp, sp = f"parts/{s}_goalies.csv", f"parts/{s}_skaters.csv"
    ids = H[H.season == s * 10000 + s + 1].game_id.tolist()
    done = set(pd.read_csv(gp).game_id) if os.path.exists(gp) else set()
    todo = [i for i in ids if i not in done]
    print(f"{s}: {len(ids)} games, {len(done)} saved, {len(todo)} to fetch", flush=True)
    G, S, errs, t0 = [], [], [], time.time()
    with ThreadPoolExecutor(6) as ex:
        for n, (gid, g, sk, e) in enumerate(ex.map(one, todo), 1):
            if n % 300 == 0: print(f"  {n}/{len(todo)} {time.time() - t0:.0f}s, {len(errs)} errors", flush=True)
            if e: errs.append(e); continue
            G += g; S += sk
    for rows, path in ((G, gp), (S, sp)):
        if rows:
            new = pd.DataFrame(rows)
            pd.concat([pd.read_csv(path), new]).to_csv(path, index=False) if os.path.exists(path) else new.to_csv(path, index=False)
    print(f"{s}: saved {len(G)} goalie rows, errors {len(errs)} {errs[:3]}", flush=True)
    if ABORT.is_set():
        print(f"STOPPED EARLY in season {s}: {MAX_CONSEC_FAIL} games failed in a row. First error: {first_err[:1]}", flush=True)
        sys.exit(2)

G = pd.concat([pd.read_csv(p) for p in sorted(glob.glob("parts/*_goalies.csv"))], ignore_index=True)
S = pd.concat([pd.read_csv(p) for p in sorted(glob.glob("parts/*_skaters.csv"))], ignore_index=True)
Gs = G[G.starter == 1]
G.to_csv("goalies_2011_2023.csv", index=False); S.to_csv("skaters_2011_2023.csv.gz", index=False)
allg = H[H.season.between(20112012, 20222023)].game_id
st = Gs.groupby(["game_id", "is_home"]).size()
L = [f"goalie rows {len(G)} (starters {len(Gs)}), skater rows {len(S)}",
     f"games in hockeyR 2011-12..2022-23: {allg.nunique()}; games with API data: {G.game_id.nunique()} ({G.game_id.nunique() / allg.nunique():.1%})",
     f"team-games with exactly one starter: {(st == 1).mean():.2%}; with 0 or 2+: {(st != 1).sum()}",
     "starter source: " + str(Gs.starter_source.value_counts().to_dict()),
     "starter share with >= 1800 s on ice (30 min): %.1f%%" % (100 * (Gs.toi_sec >= 1800).mean())]
open("checks.txt", "w").write("\n".join(L) + "\n"); print("\n".join(L))
