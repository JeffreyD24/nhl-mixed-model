"""Shooter finishing skill on top of the shot model: each shooter's goals vs expected goals in the TRAINING seasons only,
shrunk toward average ((goals + C) / (xG + C), C = 40 expected goals), multiplies the xG of his shots in the test season.
Compared with the current model (and with the rush/movement version). Walk-forward, same splits as backtest_xg.py.
  python dev/shooter_backtest.py WORKDIR   -> backtests/shooter_backtest.csv"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm
T = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
S = pd.read_csv(os.path.join(W, "data", "shots_hist.csv.gz"), low_memory=False)
SPLITS = ((2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
season_of = dict(zip(T.game_id, T.season)); C = 40.0
out = []
for v2, shooter in ((False, False), (False, True), (True, True)):
    xm.V2 = v2
    for test, train in SPLITS:
        xmod = xm.xg_model(S, T, train); F = xm.apply_xg(S, T, xmod)
        F["season"] = F.game_id.map(season_of)
        if shooter:
            tr = F[F.season.isin(train)]
            g = tr.groupby("shooter_id").agg(goals=("event", lambda e: (e == "goal").sum()), xg=("xg", "sum"))
            mult = ((g.goals + C) / (g.xg + C)).clip(0.6, 1.6)
            m = F.shooter_id.map(mult).fillna(1.0)
            te = F.season == test
            F.loc[te, "xg"] = (F.loc[te, "xg"] * m[te]).clip(upper=0.99)
        te = F[F.season == test]; y = (te.event == "goal").values; p = te.xg.clip(1e-6, 1 - 1e-6).values
        ll = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
        TG = xm.team_game_xg(F.drop(columns=["season"]), T)
        D = T.drop(columns=[c for c in TG.columns if c != "game_id" and c in T]).merge(TG, on="game_id", how="left")
        s, P, x = xm.run(D, train, test, tot_cal="none")
        mg = P.home_goals - P.away_goals
        B = nm.bets(P.reset_index(drop=True), "open", "_open", x["cal"]["open"], s["h_ot"])
        b = B[B.market.isin(["moneyline", "puck line"]) & (B.ev >= 0.06) & B.profit.notna()]
        out.append(dict(version=("rush+movement " if v2 else "") + ("shooter skill" if shooter else "current"), season=test,
                        xg_logloss=round(ll, 5), ml_brier=round(float(((P.p_home_win_open - (mg > 0)) ** 2).mean()), 5),
                        bets=len(b), units=round(float(b.profit.sum()), 1)))
        print(out[-1], flush=True)
R = pd.DataFrame(out); R.to_csv(os.path.join(W, "backtests", "shooter_backtest.csv"), index=False)
print(R.groupby("version")[["bets", "units"]].sum())
