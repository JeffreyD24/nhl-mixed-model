"""Walk-forward backtests of the shot-based (xG) model, compared with the market and the original goals model.
  python dev/backtest_xg.py WORKDIR"""
import os, sys, json
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm

T = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
S = pd.read_csv(os.path.join(W, "data", "shots_hist.csv.gz"), low_memory=False)
SPLITS = ((2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]), (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
dec = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
out = {}
for test, train in SPLITS:
    xmod = xm.xg_model(S, T, train)
    F = xm.apply_xg(S, T, xmod)
    TG = xm.team_game_xg(F, T)
    D = T.drop(columns=[c for c in TG.columns if c != "game_id" and c in T]).merge(TG, on="game_id", how="left")
    s, P, x = xm.run(D, train, test, tot_cal="none")
    P.to_csv(os.path.join(W, "_tmp", f"xg_backtest_{test}.csv"), index=False)
    O = pd.read_csv(os.path.join(W, "_tmp", f"backtest_{test}.csv"))          # original model's backtest predictions
    s_old = json.load(open(os.path.join(W, "backtests", f"backtest_{test}.json")))
    res = dict(summary=s, xg_coef=dict(zip(xmod["cols"], np.round(xmod["coef"], 3))))
    tot = P.home_goals + P.away_goals
    for ln in ("open", "close"):
        ok = P[[f"{ln}_total", f"{ln}_over_odds", f"{ln}_under_odds"]].notna().all(axis=1) & (tot != P[f"{ln}_total"])
        if not ok.any(): continue
        y = (tot[ok] > P.loc[ok, f"{ln}_total"]).values
        o_, u_ = 1 / dec(P.loc[ok, f"{ln}_over_odds"]), 1 / dec(P.loc[ok, f"{ln}_under_odds"]); pm = np.asarray(o_ / (o_ + u_))
        ll = lambda p: float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
        r = {"market": ll(pm)}
        for name, PP, cal in (("xg_model", P, x["cal"]["open"]), ("goals_model", O, s_old["calibration"]["open"])):
            po, pu, pp = nm.over_prob(PP.loc[ok, "lam_home_open"].values, PP.loc[ok, "lam_away_open"].values, PP.loc[ok, f"{ln}_total"].values, s["h_ot"], cal)
            r[name] = ll(po / (po + pu))
            # raw (uncalibrated) model probability, for the information test
            po, pu, _ = nm.over_prob(PP.loc[ok, "lam_home_open"].values, PP.loc[ok, "lam_away_open"].values, PP.loc[ok, f"{ln}_total"].values, s["h_ot"], {})
            r[f"{name}_raw_p"] = (po / (po + pu)).tolist()
        r["y"] = y.astype(int).tolist(); r["pm"] = pm.tolist()
        r["mean_model_total"] = float(P.loc[ok, "pred_total_open"].mean()); r["mean_line"] = float(P.loc[ok, f"{ln}_total"].mean())
        r["mean_actual"] = float(tot[ok].mean())
        Bt = nm.bets(P, ln, "_open", x["cal"]["open"], s["h_ot"])
        r["bets"] = nm.evaluate(Bt)
        b = Bt[(Bt.market == "total") & (Bt.ev >= 0.06) & Bt.profit.notna()]
        r["total_sides_6"] = f"{(b.side == 'over').sum()} over / {(b.side == 'under').sum()} under"
        res[ln] = r
    mg = P.home_goals - P.away_goals
    res["ml_brier"] = dict(xg=float(((P.p_home_win_open - (mg > 0)) ** 2).mean()), goals=s_old["test"]["accuracy"]["ml_brier_open"])
    out[test] = res
    print(test, "totals log-loss", {ln: {k: round(v, 4) for k, v in res[ln].items() if k in ("market", "xg_model", "goals_model")} for ln in ("open", "close") if ln in res},
          "| ML brier", {k: round(v, 4) for k, v in res["ml_brier"].items()}, flush=True)
json.dump(out, open(os.path.join(W, "_tmp", "xg_backtests.json"), "w"), default=float)
