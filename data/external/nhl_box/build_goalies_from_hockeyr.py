"""Job B fallback: NHL starting goalies 2010-11 .. 2022-23 from the hockeyR-data play-by-play (nhle.com does not answer GitHub's servers).
One row per goalie who was on the ice, per game: starter flag, approximate time on ice, shots on goal faced, goals allowed.
  python3 -I build_goalies_from_hockeyr.py RAW_DIR OUT_CSV_GZ [CHECKS_TXT]
RAW_DIR holds play_by_play_YYYY_YY_lite.csv.gz (download: https://raw.githubusercontent.com/danmorse314/hockeyR-data/main/data/<file>; about 30 MB each,
see ../hockeyr/fetch_raw_pbp.sh). Raw files are not redistributed (no license); this output is derived, aggregated facts only.

Definitions
- starter = the goalie on the ice at the opening faceoff of period 1 (home_goalie / away_goalie on that row).
- toi_sec = sum of time deltas between consecutive events while that goalie is listed on the ice (event-level, so approximate: a few seconds per stoppage).
  A missing goalie on the ice (empty net) adds no time to anyone. Regular season counts regulation + overtime only (the shootout is excluded); playoffs count all periods.
- shots_against = SHOT + GOAL events (shots on goal) by the other team while this goalie is listed on the ice; goals_against = the GOAL events among them
  (empty-net goals have no goalie on the ice and are not counted here).
- goalie_id = the NHL player id from event_goalie_id when that goalie faced any shot in the season file, else blank (join on the name then).
"""
import glob, os, sys
import numpy as np, pandas as pd

RAW = sys.argv[1]; OUT = sys.argv[2]; CHK = sys.argv[3] if len(sys.argv) > 3 else None
COLS = ["game_id", "season", "season_type", "game_date", "event_idx", "event_type", "period", "game_seconds", "home_goalie", "away_goalie",
        "event_goalie_name", "event_goalie_id", "event_team_type", "home_name", "away_name", "home_abbreviation", "away_abbreviation"]
SKIP = {"GAME_SCHEDULED", "PERIOD_END", "GAME_END", "SHOOTOUT_COMPLETE", "EARLY_INT_START", "EARLY_INT_END", "PERIOD_READY", "PERIOD_OFFICIAL"}


def one_game(g, season_type):
    g = g.sort_values("event_idx")
    reg = g[g.period <= 4] if season_type == "R" else g          # regular season: drop the shootout (period 5)
    ev = reg[~reg.event_type.isin(SKIP)]
    if ev.empty: return []
    end = reg.game_seconds.max()                                  # includes PERIOD_END / GAME_END rows
    t = ev.game_seconds.to_numpy(float); nxt = np.append(t[1:], max(end, t[-1])); dt = np.clip(nxt - t, 0, 600)
    fo = ev[(ev.event_type == "FACEOFF") & (ev.period == 1)]
    first = fo.iloc[0] if len(fo) else ev.iloc[0]
    out = []
    r0 = g.iloc[0]
    for side, name_col, abbr_col, tm_col, is_home in (("home", "home_goalie", "home_abbreviation", "home_name", 1), ("away", "away_goalie", "away_abbreviation", "away_name", 0)):
        gl = ev[name_col].to_numpy(object)
        starter = first[name_col] if isinstance(first[name_col], str) else next((x for x in gl if isinstance(x, str)), None)
        names = sorted({x for x in gl if isinstance(x, str)})
        # shots faced by this side's goalies: SHOT + GOAL events taken by the OTHER team, charged to the goalie listed on the ice for this side on that row
        # (by side, not by event_goalie_name, so name-spelling differences between columns cannot drop shots)
        other = "away" if side == "home" else "home"
        sog = ev[ev.event_type.isin(["SHOT", "GOAL"]) & (ev.event_team_type == other)]
        for n in names:
            on = sog[sog[name_col] == n]
            ids = on.event_goalie_id.dropna()
            m = np.array([x == n for x in gl])
            out.append(dict(game_id=int(r0.game_id), season=int(r0.season), season_type=season_type, date=str(r0.game_date)[:10],
                            team=r0[abbr_col], team_name=r0[tm_col], is_home=is_home, goalie=n,
                            goalie_id=(int(ids.mode().iloc[0]) if len(ids) else np.nan), starter=int(n == starter),
                            toi_sec=int(round(dt[m].sum())),
                            shots_against=int(len(on)),
                            goals_against=int((on.event_type == "GOAL").sum()),
                            game_sec=int(end)))
    return out


rows = []
files = sorted(glob.glob(os.path.join(RAW, "play_by_play_20*_lite.csv.gz")))
files = [f for f in files if not f.endswith("2023_24_lite.csv.gz")]
for f in files:
    d = pd.read_csv(f, encoding="latin-1", usecols=lambda c: c in COLS, low_memory=False)
    d = d[d.season_type.isin(["R", "P"])]
    n0 = len(rows)
    for (gid, st), g in d.groupby(["game_id", "season_type"], sort=False):
        rows += one_game(g, st)
    print(os.path.basename(f), "games", d.game_id.nunique(), "goalie rows added", len(rows) - n0, flush=True)

G = pd.DataFrame(rows).sort_values(["game_id", "is_home", "starter"], ascending=[True, False, False]).reset_index(drop=True)
# goalie_toi_share: team's goalie time (all its goalies) / game length. Below ~0.9 the source file is missing the goalie column for part of the game
# (about 1% of team-games), so toi_sec / shots_against / goals_against are unreliable there; the starter flag (opening faceoff) is usually still right.
G["goalie_toi_share"] = (G.groupby(["game_id", "is_home"]).toi_sec.transform("sum") / G.game_sec.clip(lower=1)).round(3)
G.to_csv(OUT, index=False)
print("wrote", OUT, len(G))

# ---- checks (compared with ../hockeyr/team_game_xg_2010_2023.csv.gz, built from the same files but by a separate shot/goal count)
if CHK:
    T = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hockeyr", "team_game_xg_2010_2023.csv.gz")); T = T[T.season_type.isin(["R", "P"])]
    tg = G.groupby(["game_id", "is_home"]).size(); st = G[G.starter == 1].groupby(["game_id", "is_home"]).size()
    a = G.groupby(["game_id", "team_name"]).agg(sa=("shots_against", "sum"), ga=("goals_against", "sum"), share=("goalie_toi_share", "first")).reset_index()
    m = a.merge(T[["game_id", "team", "sog_against", "goals_against", "season_type"]], left_on=["game_id", "team_name"], right_on=["game_id", "team"]); r = m[m.season_type == "R"]; d = r.sa - r.sog_against
    s_ = G[(G.starter == 1) & (G.season_type == "R")]
    L = [f"goalie rows {len(G)}; games {G.game_id.nunique()} of {T.game_id.nunique()} in the hockeyR team-game table",
         f"team-games with goalie rows: {len(tg)} of {len(T)} ({100 * len(tg) / len(T):.2f}%); exactly one starter: {100 * (st == 1).mean():.2f}%",
         f"starter (regular season): median TOI {s_.toi_sec.median():.0f}s; played 55+ min {100 * (s_.toi_sec >= 3300).mean():.1f}%; out before 40 min {100 * (s_.toi_sec < 2400).mean():.1f}%",
         f"goalie time / game length: mean {r.share.mean():.3f}; team-games below 0.90: {(r.share < 0.9).sum()} of {len(r)} ({100 * (r.share < 0.9).mean():.1f}%)",
         f"shots on goal faced vs team-game table (regular season): exact {100 * (d == 0).mean():.1f}%, within 1 {100 * (d.abs() <= 1).mean():.1f}%, within 3 {100 * (d.abs() <= 3).mean():.1f}%, mean signed {d.mean():+.2f} (empty-net shots are not charged to a goalie)",
         f"same, restricted to team-games with goalie_toi_share >= 0.90: exact {100 * (d[r.share >= .9] == 0).mean():.1f}%, within 1 {100 * (d[r.share >= .9].abs() <= 1).mean():.1f}%",
         f"goals against equal to table: {100 * (r.ga == r.goals_against).mean():.1f}% (differences: empty-net and shootout goals)",
         f"goalie_id missing: {100 * G.goalie_id.isna().mean():.1f}% of rows"]
    open(CHK, "w").write("\n".join(L) + "\n"); print("\n".join(L))
