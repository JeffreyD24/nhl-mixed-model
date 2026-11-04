"""Per-game NHL shot-model predictions for the statistics catalog.
  dk : live shot model (nhl_xg_model.run, goalie effects, one-day lag) on 2024-25 and 2025-26, DraftKings open/close prices.
       Trained on the 4 seasons before (as dev/lag_backtest.py). The open-time goalie mix comes from training_games (lag 0), a small leak.
  sbr: pre-registered holdout predictions (dev/oos_sbr_backtest.py predict, team-only shot model, no goalies), 2015-16 .. 2021-22.
  python build_nhl.py NHL_REPO OUTDIR"""
import os, sys, io, json, contextlib
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); OUT = sys.argv[2]; sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def novig(a, b):
    pa, pb = 1 / dec(a), 1 / dec(b); return pa / (pa + pb)
def frame(P, src, s, cal, h_ot):
    ok = P[["open_total", "open_over_odds"]].notna().all(axis=1)
    po = np.full(len(P), np.nan); pp = np.full(len(P), np.nan)
    if ok.any():
        a, _, c = nm.over_prob(P.lam_home_open.values[ok], P.lam_away_open.values[ok], P.open_total.values[ok], h_ot, cal)
        po[ok.values] = a; pp[ok.values] = c
    g = lambda c: P[c] if c in P else np.nan
    return pd.DataFrame(dict(src=src, season=s, date=P.date, home=P.home, away=P.away, p_home=P.p_home_win_open,
        open_home_ml=P.open_home_ml, open_away_ml=P.open_away_ml, close_home_ml=P.close_home_ml, close_away_ml=P.close_away_ml,
        nv_open=novig(P.open_home_ml, P.open_away_ml), nv_close=novig(P.close_home_ml, P.close_away_ml),
        home_goals=P.home_goals, away_goals=P.away_goals, home_reg=g("home_reg"), away_reg=g("away_reg"),
        lam_home=P.lam_home_open, lam_away=P.lam_away_open, pred_total=P.pred_total_open,
        open_total=P.open_total, open_over_odds=P.open_over_odds, open_under_odds=P.open_under_odds,
        close_total=P.close_total, close_over_odds=P.close_over_odds, close_under_odds=P.close_under_odds,
        p_over=po, p_push=pp, b2b_home=g("b2b_home"), b2b_away=g("b2b_away"),
        trusted=(((g("open_ml_ok") == 1) & (g("close_ml_ok") == 1) & (g("ml_move_ok") == 1)).astype(int) if src == "sbr" else 1),
        tot_ok=(((g("open_total_ok") == 1) & (g("close_total_ok") == 1)).astype(int) if src == "sbr" else 1)))
rows = []
T0 = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
for test, train in ((2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025])):
    with contextlib.redirect_stdout(io.StringIO()):
        summ, P, x = xm.run(T0[T0.season.isin(train + [test])], train, test, lag_days=1)
    rows.append(frame(P, "dk", test, x["cal"]["open"], x["h_ot"])); print("dk", test, len(P), flush=True)
for s in range(2016, 2023):
    P = pd.read_csv(os.path.join(W, "_tmp", f"oos_pred_{s}.csv")); m = json.load(open(os.path.join(W, "_tmp", f"oos_meta_{s}.json")))
    rows.append(frame(P, "sbr", s, m["cal"]["open"], m["h_ot"])); print("sbr", s, len(P), flush=True)
G = pd.concat(rows, ignore_index=True); G.to_csv(os.path.join(OUT, "nhl_games.csv"), index=False); print(G.groupby("src").size())
