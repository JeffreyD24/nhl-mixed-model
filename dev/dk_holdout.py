"""Shot model (live settings: one-day information lag) on 2021-22..2023-24 graded at real DraftKings prices from The Odds API
history: the opener, +15/30/60 min, halfway and the close. Those seasons had no opening prices before.
  python dev/dk_holdout.py WORKDIR -> _tmp/dk_holdout_{season}.csv, backtests/dk_holdout.csv"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm, build_features as bf
T0 = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
G = pd.read_csv(os.path.join(W, "data", "games_hist.csv"), parse_dates=["date"])
B = pd.read_csv(os.path.join(W, "data", "box_hist.csv"))
S = pd.read_csv(os.path.join(W, "data", "shots_hist.csv"), low_memory=False)
F1, _ = bf.build(G, B, lag_days=1)
T1 = T0.copy().set_index("game_id")
for c in ("home_gmix", "away_gmix", "home_miss_off_open", "away_miss_off_open", "home_n_out_open", "away_n_out_open"):
    T1[c] = F1.set_index("game_id")[c].reindex(T1.index)
T1 = T1.reset_index()
DK = pd.read_csv(os.path.join(W, "data", "nhl_prices.csv.gz")); DK = DK[DK.book == "draftkings"].drop(columns=["book", "event_id"])
LABS = ("open", "m15", "m30", "m60", "mid", "close")
SPLITS = ((2022, [2020, 2021]), (2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]))
rows = []
for test, train in SPLITS:
    xmod = xm.xg_model(S, T0, train)
    TG = xm.team_game_xg(xm.apply_xg(S, T0, xmod), T0)
    D = T1.drop(columns=[c for c in TG.columns if c != "game_id" and c in T1]).merge(TG, on="game_id", how="left")
    sx, P, ex = xm.run(D, train, test, tot_cal="none", lag_days=1, halflives=(None, 60))
    P["date"] = pd.to_datetime(P.date).dt.strftime("%Y-%m-%d")
    P = P.drop(columns=[c for c in P if c.startswith(("open_", "close_", "mid_"))]).merge(DK, on=["date", "home", "away"], how="left")
    P.to_csv(os.path.join(W, "_tmp", f"dk_holdout_{test}.csv"), index=False)
    print(test, "games", len(P), "with DK opener", P.open_home_ml.notna().sum(), flush=True)
    for ln in LABS:
        if not P[f"{ln}_home_ml"].notna().any(): continue
        Bt = nm.bets(P, ln, "_open", {}, ex["h_ot"])
        for mk in ("moneyline", "puck line", "total"):
            for t in (0.04, 0.06, 0.09):
                s = Bt[(Bt.market == mk) & (Bt.ev >= t) & Bt.profit.notna()]
                rows.append(dict(season=test, price=ln, market=mk, ev=t, bets=len(s), won=round(s.win.mean(), 3) if len(s) else None,
                                 units=round(s.profit.sum(), 2), roi=round(s.profit.sum() / max(len(s), 1), 4)))
R = pd.DataFrame(rows); R.to_csv(os.path.join(W, "backtests", "dk_holdout.csv"), index=False)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 300)
print(R[R.ev == 0.06].pivot_table(index=["market", "price"], columns="season", values="units"))
