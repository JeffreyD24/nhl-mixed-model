"""
Tests the ideas from the Oct 31 cold-stretch review on the past seasons (one-day information lag, as live):
  base       current models
  adapt      home ice and back-to-back effects re-estimated during the season (shrinkage chosen on the last training season)
  cal2       probability calibration fit on the last two training seasons instead of one
  adapt+cal2 both
and, applied to each, a betting filter: skip underdogs priced +150 or longer.
Also checks whether a hot run by favorites predicts the next week (the "favorites-run monitor" idea).

  python dev/idea_tests.py WORKDIR
"""
import os, sys, json
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
src = open(os.path.join(W, "dev", "midpoint_backtest.py")).read()
exec(src.split("rows = []")[0].split("import nhl_mixed_model as nm")[1])        # dec, amer, add_mid

SPLITS = ((2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]), (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
VARIANTS = {"base": {}, "adapt": dict(adapt_idx=[1, 2, 3], adapt_grid=(None, 300, 1000, 3000)), "cal2": dict(cal_seasons=2),
            "adapt+cal2": dict(adapt_idx=[1, 2, 3], adapt_grid=(None, 300, 1000, 3000), cal_seasons=2)}
rows, cal_rows, chosen = [], [], []
for test, train in SPLITS:
    xmod = xm.xg_model(S, T0, train)
    TG = xm.team_game_xg(xm.apply_xg(S, T0, xmod), T0)
    D = T1.drop(columns=[c for c in TG.columns if c != "game_id" and c in T1]).merge(TG, on="game_id", how="left")
    for vname, kw in VARIANTS.items():
        sg, Pg, eg = nm.run(T1, train, test, lag_days=1, halflives=(None, 60), **kw)
        sx, Px, ex = xm.run(D, train, test, tot_cal="none", lag_days=1, halflives=(None, 60), **kw)
        chosen.append(dict(season=test, variant=vname, goals_n0=sg.get("chosen_adapt_n0"), shot_n0=sx.get("adapt_n0")))
        for name, P, cal, h in (("goals", Pg, eg["cal"]["open"], eg["h_ot"]), ("shot", Px, {}, ex["h_ot"])):
            if P.open_home_ml.notna().any(): P = add_mid(P)
            mg = P.home_goals - P.away_goals; y = (mg > 0).astype(float); p = P.p_home_win_open.clip(1e-4, 1 - 1e-4)
            acc = dict(brier=float(((p - y) ** 2).mean()), logloss=float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()))
            for ln in ("open", "mid", "close"):
                if f"{ln}_home_ml" not in P or not P[f"{ln}_home_ml"].notna().any(): continue
                Bt = nm.bets(P, ln, "_open", cal, h)
                s = Bt[Bt.market.isin(["moneyline", "puck line"]) & (Bt.ev >= 0.06) & Bt.profit.notna()].copy()
                for filt, ss_ in (("all bets", s), ("no dogs +150", s[~(s.price >= 150)])):
                    rows.append(dict(season=test, variant=vname, model=name, price=ln, filter=filt, bets=len(ss_),
                                     units=round(ss_.profit.sum(), 2), **acc))
                if ln in ("open", "close"):
                    s["band"] = pd.cut(s.price, [-1000, -101, 149, 2000], labels=["favorite", "dog +100..+149", "dog +150+"])
                    for bnd, g in s.groupby("band", observed=True):
                        cal_rows.append(dict(season=test, variant=vname, model=name, price=ln, band=bnd, bets=len(g), said=g.p.mean(),
                                             won=g.win.mean(), needed=(1 / g.dec).mean(), units=g.profit.sum()))
        print(test, vname, "done", flush=True)
R = pd.DataFrame(rows); C = pd.DataFrame(cal_rows)
R.to_csv(os.path.join(W, "backtests", "idea_tests.csv"), index=False); C.to_csv(os.path.join(W, "backtests", "idea_tests_bands.csv"), index=False)
pd.DataFrame(chosen).to_csv(os.path.join(W, "backtests", "idea_tests_chosen.csv"), index=False)

# favorites-run monitor: does a week where favorites beat the market predict the next week?
P = pd.concat([pd.read_csv(os.path.join(W, "_tmp", f"backtest_{t}.csv")) for t in (2025, 2026)])
P = P[P.open_home_ml.notna() & P.home_goals.notna()].copy(); P["date"] = pd.to_datetime(P.date)
ih, ia = 1 / dec(P.open_home_ml), 1 / dec(P.open_away_ml); ph = ih / (ih + ia)
P["pf"] = np.maximum(ph, 1 - ph); P["fw"] = np.where(ph >= .5, P.home_goals > P.away_goals, P.away_goals > P.home_goals).astype(float)
P["wk"] = P.date.dt.to_period("W")
wk = P.groupby([P.season, "wk"]).apply(lambda g: pd.Series(dict(n=len(g), surplus=(g.fw - g.pf).sum() / len(g)))).reset_index()
wk["next"] = wk.groupby("season").surplus.shift(-1)
mon = dict(weeks=int(wk.next.notna().sum()), corr_week_to_next=float(wk[["surplus", "next"]].dropna().corr().iloc[0, 1]))
json.dump(mon, open(os.path.join(W, "backtests", "idea_tests_favorites_monitor.json"), "w"), indent=1)

pd.set_option("display.width", 230); pd.set_option("display.max_rows", 200)
acc = R.drop_duplicates(["season", "variant", "model"]).groupby(["model", "variant"])[["brier", "logloss"]].mean().round(5)
print(acc)
t = R.groupby(["model", "variant", "price", "filter"])[["bets", "units"]].sum(); t["roi"] = (t.units / t.bets).round(4)
print(t)
print(C.groupby(["model", "variant", "price", "band"], observed=True).apply(lambda g: pd.Series(dict(bets=g.bets.sum(), said=(g.said * g.bets).sum() / g.bets.sum(),
      won=(g.won * g.bets).sum() / g.bets.sum(), needed=(g.needed * g.bets).sum() / g.bets.sum(), units=g.units.sum()))).round(3))
print(pd.DataFrame(chosen)); print(mon)
