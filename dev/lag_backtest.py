"""
Backtests with the information the models really have when DraftKings posts its line (~31 hours before the game):
results and lineups only through two days before the game (lag_days=1), versus the original setup (lag_days=0).
Both models, all four test seasons, at opening, halfway and closing prices.

  python dev/lag_backtest.py WORKDIR
"""
import os, sys, json
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W); sys.path.insert(0, os.path.join(W, "dev"))
import nhl_mixed_model as nm, nhl_xg_model as xm, build_features as bf

T0 = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
G = pd.read_csv(os.path.join(W, "data", "games_hist.csv"), parse_dates=["date"])
B = pd.read_csv(os.path.join(W, "data", "box_hist.csv.gz"))
S = pd.read_csv(os.path.join(W, "data", "shots_hist.csv.gz"), low_memory=False)
F1, _ = bf.build(G, B, lag_days=1)
T1 = T0.copy().set_index("game_id")
for c in ("home_gmix", "away_gmix", "home_miss_off_open", "away_miss_off_open", "home_n_out_open", "away_n_out_open"):
    T1[c] = F1.set_index("game_id")[c].reindex(T1.index)
T1 = T1.reset_index()

exec(open(os.path.join(W, "dev", "midpoint_backtest.py")).read().split("rows = []")[0].split("import nhl_mixed_model as nm")[1])   # dec, amer, add_mid
SPLITS = ((2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]), (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
rows = []
for test, train in SPLITS:
    xmod = xm.xg_model(S, T0, train)
    TG = xm.team_game_xg(xm.apply_xg(S, T0, xmod), T0)
    for lag, T in ((0, T0), (1, T1)):
        D = T.drop(columns=[c for c in TG.columns if c != "game_id" and c in T]).merge(TG, on="game_id", how="left")
        sg, Pg, xg_ = nm.run(T, train, test, lag_days=lag)
        sx, Px, xx_ = xm.run(D, train, test, tot_cal="none", lag_days=lag)
        for name, P, cal, h in (("goals", Pg, xg_["cal"]["open"], xg_["h_ot"]), ("shot", Px, {}, xx_["h_ot"])):
            P = add_mid(P) if P.open_home_ml.notna().any() else P
            mg = P.home_goals - P.away_goals
            brier = float(((P.p_home_win_open - (mg > 0)) ** 2).mean())
            for ln in ("open", "mid", "close"):
                if f"{ln}_home_ml" not in P or not P[f"{ln}_home_ml"].notna().any(): continue
                Bt = nm.bets(P, ln, "_open", cal, h)
                s = Bt[Bt.market.isin(["moneyline", "puck line"]) & (Bt.ev >= 0.06) & Bt.profit.notna()]
                rows.append(dict(season=test, lag=lag, model=name, price=ln, bets=len(s), units=round(s.profit.sum(), 1),
                                 ml_units=round(s[s.market == "moneyline"].profit.sum(), 1), pl_units=round(s[s.market == "puck line"].profit.sum(), 1),
                                 brier=round(brier, 4)))
        print(test, "done", flush=True)
R = pd.DataFrame(rows); R.to_csv(os.path.join(W, "backtests", "lag_backtests.csv"), index=False)
pd.set_option("display.width", 220)
print(R.pivot_table(index=["model", "price", "season"], columns="lag", values=["units", "bets"]).round(1))
print(R.groupby(["model", "lag"]).brier.mean().round(4))
t = R[R.price.isin(["open", "mid"])].groupby(["model", "price", "lag"])[["bets", "units"]].sum(); t["roi"] = (t.units / t.bets).round(4); print(t)
