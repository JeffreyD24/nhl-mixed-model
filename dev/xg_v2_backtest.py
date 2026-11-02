"""Shot model with vs without rush shots and pre-shot movement (nhl_xg_model.V2). Walk-forward, same splits as
backtest_xg.py: xG log-loss on the test season's shots, game accuracy, and team bets at opening prices (EV 6%+).
  python dev/xg_v2_backtest.py WORKDIR"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm
T = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
S = pd.read_csv(os.path.join(W, "data", "shots_hist.csv"), low_memory=False)
SPLITS = ((2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]), (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
season_of = dict(zip(T.game_id, T.season))
out = []
for v2 in (False, True):
    xm.V2 = v2
    for test, train in SPLITS:
        xmod = xm.xg_model(S, T, train); F = xm.apply_xg(S, T, xmod)
        te = F[F.game_id.map(season_of) == test]; y = (te.event == "goal").values; p = te.xg.clip(1e-6, 1 - 1e-6).values
        ll = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
        TG = xm.team_game_xg(F, T)
        D = T.drop(columns=[c for c in TG.columns if c != "game_id" and c in T]).merge(TG, on="game_id", how="left")
        s, P, x = xm.run(D, train, test, tot_cal="none")
        mg = P.home_goals - P.away_goals
        brier = float(((P.p_home_win_open - (mg > 0)) ** 2).mean())
        B = nm.bets(P.reset_index(drop=True), "open", "_open", x["cal"]["open"], s["h_ot"])
        b = B[B.market.isin(["moneyline", "puck line"]) & (B.ev >= 0.06) & B.profit.notna()]
        out.append(dict(version="V2 rush+movement" if v2 else "V1 current", season=test, xg_logloss=round(ll, 5), ml_brier=round(brier, 5),
                        bets=len(b), units=round(b.profit.sum(), 1), roi=round(b.profit.sum() / len(b), 4) if len(b) else None))
        print(out[-1], flush=True)
R = pd.DataFrame(out); R.to_csv(os.path.join(W, "backtests", "xg_v2_backtest.csv"), index=False)
print(R.pivot(index="season", columns="version", values=["xg_logloss", "ml_brier", "units"]).to_string())
