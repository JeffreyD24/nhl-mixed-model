"""
Shot-level data from ESPN play-by-play, for the expected-goals (xG) model. Writes data/shots_hist.csv.gz
(or state/shots_2026_27.csv with --season 2027 for the live season).

One row per shot attempt (on goal, missed, blocked, goal): game, period, seconds into the period, shooting team,
x/y in feet (center ice = 0, nets near x = +/-89), strength (even / power play / shorthanded), score before the shot,
shot type when ESPN gives it (wrist, snap, slap, backhand, tip-in, deflected, wrap-around).

  python build_shots.py WORKDIR [CACHE_DIR]
"""
import os, sys, re, pickle
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
sys.path.insert(0, os.path.abspath(sys.argv[1]))
import nhl_data as nd

TYPES = {"Shot": "shot", "Missed": "missed", "Blocked": "blocked", "Goal": "goal"}
STYPE = re.compile(r"(Wrist|Snap|Slap|Backhand|Tip-In|Deflected|Wrap-around|Poke|Bat|Between Legs|Cradle)", re.I)


def shots(game_id):
    d = nd.get(f"{nd.ESPN}/summary?event={game_id}")
    tid = {}
    for t in (d.get("boxscore") or {}).get("teams", []):
        tid[str(t["team"]["id"])] = nd.code(t["team"]["abbreviation"])
    out, prev_h, prev_a = [], 0, 0
    last = None                       # the previous play with a location (for rush shots and pre-shot movement)
    for p in d.get("plays", []):
        typ = TYPES.get((p.get("type") or {}).get("text"))
        hs, as_ = p.get("homeScore", prev_h), p.get("awayScore", prev_a)
        if typ and p.get("coordinate") and p.get("team"):
            per = (p.get("period") or {}).get("number")
            try:
                m, s = (p.get("clock") or {}).get("displayValue", "0:00").split(":"); sec = int(m) * 60 + int(s)
            except ValueError:
                sec = None
            st = STYPE.search(p.get("text") or "")
            before_h, before_a = (prev_h, prev_a)
            parts = p.get("participants") or []
            who = lambda *ts: next((str((x.get("athlete") or {}).get("id")) for x in parts if x.get("type") in ts), None)
            team = tid.get(str(p["team"]["id"]))
            out.append(dict(game_id=int(game_id), period=per, sec=sec, team=team, event=typ,
                            x=p["coordinate"].get("x"), y=p["coordinate"].get("y"),
                            strength=((p.get("strength") or {}).get("abbreviation") or ""),
                            home_score=before_h, away_score=before_a,
                            shot_type=st.group(1).lower() if st else "", empty_net=int("empty net" in (p.get("text") or "").lower()),
                            shooter_id=who("shooter", "scorer") or (str((parts[0].get("athlete") or {}).get("id")) if parts else None),
                            goalie_id=who("goalie"),
                            prev_type=last["type"] if last and last["period"] == per else None,
                            prev_x=last["x"] if last and last["period"] == per else None,
                            prev_y=last["y"] if last and last["period"] == per else None,
                            prev_sec=last["sec"] if last and last["period"] == per else None,
                            prev_same_team=(int(last["team"] == team) if last and last["period"] == per and last["team"] else None)))
        if p.get("coordinate") and p.get("coordinate").get("x") is not None:
            try:
                m_, s_ = (p.get("clock") or {}).get("displayValue", "0:00").split(":"); sec_ = int(m_) * 60 + int(s_)
            except ValueError:
                sec_ = None
            last = dict(type=((p.get("type") or {}).get("text") or "").lower(), x=p["coordinate"].get("x"), y=p["coordinate"].get("y"),
                        sec=sec_, period=(p.get("period") or {}).get("number"),
                        team=tid.get(str((p.get("team") or {}).get("id"))) if p.get("team") else None)
        prev_h, prev_a = hs, as_
    return out


def main():
    W = os.path.abspath(sys.argv[1]); cache = sys.argv[2] if len(sys.argv) > 2 else os.path.join(W, "_tmp", "shots_cache")
    os.makedirs(cache, exist_ok=True)
    G = pd.read_csv(os.path.join(W, "data", "games_hist.csv"))

    def one(g):
        p = os.path.join(cache, f"{g}.pkl")
        if os.path.exists(p): return pickle.load(open(p, "rb"))
        try: v = shots(g)
        except Exception: return []
        pickle.dump(v, open(p, "wb")); return v
    with ThreadPoolExecutor(24) as ex:
        rows = list(ex.map(one, G.game_id))
    S = pd.DataFrame([r for rs in rows for r in rs])
    S.to_csv(os.path.join(W, "data", "shots_hist.csv.gz"), index=False)
    print(len(S), "shot attempts in", S.game_id.nunique(), "of", len(G), "games")
    print(S.event.value_counts().to_dict()); print(S.strength.value_counts().to_dict()); print(S.shot_type.value_counts().head(10).to_dict())


if __name__ == "__main__":
    main()
