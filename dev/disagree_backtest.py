"""When the goals model and the shot (xG) model back DIFFERENT teams in the same game (moneyline or puck line, opening
prices, EV at the live bar), how did each side do? Walk-forward test seasons 2023-2026, same splits as backtest_xg.py.
  python dev/disagree_backtest.py WORKDIR     -> backtests/disagree_bets.csv and a printed summary"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm

T = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
S = pd.read_csv(os.path.join(W, "data", "shots_hist.csv.gz"), low_memory=False)
SPLITS = ((2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]), (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
BAR, TEAM = 0.06, ("moneyline", "puck line")
rows = []
for test, train in SPLITS:
    sg, PG, xg_ = nm.run(T, train, test)
    xmod = xm.xg_model(S, T, train); F = xm.apply_xg(S, T, xmod); TG = xm.team_game_xg(F, T)
    D = T.drop(columns=[c for c in TG.columns if c != "game_id" and c in T]).merge(TG, on="game_id", how="left")
    sx, PX, xx = xm.run(D, train, test, tot_cal="none")
    for name, P, cal, h in (("goals", PG, sg["calibration"]["open"], sg["h_ot"]), ("xg", PX, xx["cal"]["open"], sx["h_ot"])):
        B = nm.bets(P.reset_index(drop=True), "open", "_open", cal, h)
        B = B[B.market.isin(TEAM) & (B.ev >= BAR) & B.profit.notna()].copy()
        B["game_id"] = P.reset_index(drop=True).loc[B.idx, "game_id"].values
        B["team"] = np.where(B.side == "home", P.reset_index(drop=True).loc[B.idx, "home"].values, P.reset_index(drop=True).loc[B.idx, "away"].values)
        B["model"], B["season"] = name, test
        rows.append(B.drop(columns=["idx"]))
    print(test, "done", flush=True)
A = pd.concat(rows, ignore_index=True)
teams = A.groupby("game_id").side.nunique()
A["conflict"] = A.game_id.map(teams) > 1          # some bet in this game (either model, ML or PL) backs the other team
A.to_csv(os.path.join(W, "backtests", "disagree_bets.csv"), index=False)
def line(x, label):
    n = len(x); w = int((x.profit > 0).sum())
    return f"  {label:46s} {n:4d} bets, won {w / n if n else 0:.1%}, {x.profit.sum():+7.1f} units, ROI {x.profit.sum() / n if n else 0:+.1%}"
print("\nAll team bets at the bar (opening prices), 2023-2026:")
for m in ("goals", "xg"):
    print(line(A[A.model == m], f"{m} model, all"))
    print(line(A[(A.model == m) & ~A.conflict], f"{m} model, models agree or only one bets"))
    print(line(A[(A.model == m) & A.conflict], f"{m} model, when the models back different teams"))
C = A[A.conflict]
print(f"\nGames where they disagreed: {C.game_id.nunique()} (of {A.game_id.nunique()} games with any team bet)")
# pick the one bet with the higher EV in each conflicting game
best = C.sort_values("ev", ascending=False).drop_duplicates("game_id")
print(line(best, "conflict games: only the single highest-EV bet"))
print(line(C, "conflict games: every bet (both sides)"))
for s, g in A.groupby("season"):
    c = g[g.conflict]; b = c.sort_values("ev", ascending=False).drop_duplicates("game_id")
    print(f"  {s}: conflict bets {len(c)}, {c.profit.sum():+.1f}u; best-EV only {len(b)}, {b.profit.sum():+.1f}u; "
          f"no-conflict bets {len(g) - len(c)}, {g[~g.conflict].profit.sum():+.1f}u")
