"""Walk-forward predictions for the NHL autopsy: shot model (live) and goals model (research), one-day lag, 2021-22..2025-26.
Prices: DraftKings from The Odds API history (2021-24) or the training opener/close (2024-26).  -> _tmp/autopsy_{model}_{season}.csv"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm, build_features as bf
T0 = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
G = pd.read_csv(os.path.join(W, "data", "games_hist.csv"), parse_dates=["date"]); B = pd.read_csv(os.path.join(W, "data", "box_hist.csv"))
S = pd.read_csv(os.path.join(W, "data", "shots_hist.csv"), low_memory=False)
F1, _ = bf.build(G, B, lag_days=1)
T1 = T0.copy().set_index("game_id")
for c in ("home_gmix", "away_gmix", "home_miss_off_open", "away_miss_off_open", "home_n_out_open", "away_n_out_open"):
    T1[c] = F1.set_index("game_id")[c].reindex(T1.index)
T1 = T1.reset_index()
DK = pd.read_csv(os.path.join(W, "data", "nhl_prices.csv.gz")); DK = DK[DK.book == "draftkings"].drop(columns=["book", "event_id"])
SPLITS = ((2022, [2020, 2021]), (2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]), (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
for test, train in SPLITS:
    xmod = xm.xg_model(S, T0, train)
    TG = xm.team_game_xg(xm.apply_xg(S, T0, xmod), T0)
    D = T1.drop(columns=[c for c in TG.columns if c != "game_id" and c in T1]).merge(TG, on="game_id", how="left")
    for name in ("shot", "goals"):
        if name == "shot": s, P, ex = xm.run(D, train, test, tot_cal="none", lag_days=1, halflives=(None, 60)); cal = {}
        else: s, P, ex = nm.run(T1, train, test, lag_days=1, halflives=(None, 60)); cal = ex["cal"]["open"]
        P["date"] = pd.to_datetime(P.date).dt.strftime("%Y-%m-%d")
        if test <= 2024:
            P = P.drop(columns=[c for c in P if c.startswith(("open_", "close_"))]).merge(DK, on=["date", "home", "away"], how="left")
        Bt = nm.bets(P, "open", "_open", cal, ex["h_ot"])
        Bt = Bt.merge(P.reset_index().rename(columns={"index": "idx"}), on="idx", how="left")
        Bt["season"] = test; Bt["model"] = name
        Bt.to_csv(os.path.join(W, "_tmp", f"autopsy_{name}_{test}.csv"), index=False)
        print(test, name, "bets EV6+", int(((Bt.ev >= .06) & Bt.market.isin(["moneyline", "puck line"])).sum()), flush=True)
