"""Job B: NHL starting goalies and skater TOI, 2011-12 .. 2022-23, from the public NHL API (api-web.nhle.com).
python fetch_nhl_box.py [season_start_years...]   run from this folder, in GitHub Actions (the Claude workspace cannot reach nhle.com).
Game list = regular-season games in ../hockeyr/team_game_xg_2010_2023.csv.gz. Safe to rerun: games already in parts/ are skipped.
Writes parts/{season}_goalies.csv, parts/{season}_skaters.csv, then combines into goalies_2011_2023.csv and skaters_2011_2023.csv.gz."""
import os, sys, glob, json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
os.makedirs("parts", exist_ok=True)
H = pd.read_csv("../hockeyr/team_game_xg_2010_2023.csv.gz", usecols=["game_id", "season", "season_type", "game_date"])
H = H[H.season_type == "R"].drop_duplicates("game_id")
SEASONS = [int(x) for x in sys.argv[1:]] or list(range(2011, 2023))

def toi(s):
    try: m, sec = str(s).split(":"); return int(m) * 60 + int(sec)
    except Exception: return 0

def one(gid):
    url = f"https://api-web.nhle.com/v1/gamecenter/{gid}/boxscore"
    for k in range(5):
        try:
            with urllib.request.urlopen(url, timeout=40) as r: b = json.loads(r.read()); break
        except Exception as e:
            if k == 4: return gid, None, None, f"{gid}: {type(e).__name__} {str(e)[:60]}"
            time.sleep(3 * (k + 1))
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
            if e: errs.append(e); continue
            G += g; S += sk
            if n % 300 == 0: print(f"  {n}/{len(todo)} {time.time() - t0:.0f}s", flush=True)
    for rows, path in ((G, gp), (S, sp)):
        if rows:
            new = pd.DataFrame(rows)
            pd.concat([pd.read_csv(path), new]).to_csv(path, index=False) if os.path.exists(path) else new.to_csv(path, index=False)
    print(f"{s}: errors {len(errs)} {errs[:3]}", flush=True)

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
     "starter share of team shots against >= 50% of game TOI: %.1f%%" % (100 * (Gs.toi_sec >= 1800).mean())]
open("checks.txt", "w").write("\n".join(L) + "\n"); print("\n".join(L))
