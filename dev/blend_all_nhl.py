"""Blend with DraftKings' opening price for the other NHL bets: puck line (P(cover) blended with the no-vig puck line price) and
totals overs (P(over) blended with the no-vig over price). Weight fit leaving the test season out (log-loss), live rules.
  python dev/blend_all_nhl.py WORKDIR TRACKER"""
import os, sys
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
W = os.path.abspath(sys.argv[1]); TRK = os.path.abspath(sys.argv[2]); sys.path.insert(0, W)
import nhl_mixed_model as nm
H = pd.concat([pd.read_csv(os.path.join(W, "_tmp", f"dk_holdout_{s}.csv")) for s in (2022, 2023, 2024, 2025, 2026)], ignore_index=True)
TN = pd.read_csv(os.path.join(TRK, "analysis", "travel_nhl_games.csv"))[["date", "home", "away", "h_rest", "a_rest"]]
H = H.merge(TN, on=["date", "home", "away"], how="left").reset_index(drop=True)
dec = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
def nv(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)
ll = lambda p, y: -np.mean(y * np.log(np.clip(p, 1e-6, 1 - 1e-6)) + (1 - y) * np.log(np.clip(1 - p, 1e-6, 1 - 1e-6)))
SEAS = sorted(H.season.unique())
def run(name, p_model, p_mkt, y, d_yes, d_no, valid, pick_rule, bars, b2b_side=None):
    """p_* = chance of the 'yes' outcome; bet yes or no by EV; pick_rule(yes) -> allowed"""
    print(f"\n{name}")
    for kind in ("model", "blend"):
        p = p_model.copy(); ws = []
        if kind == "blend":
            for s in SEAS:
                tr = valid & (H.season != s).values; te = valid & (H.season == s).values
                w = minimize_scalar(lambda w: ll(w * p_model[tr] + (1 - w) * p_mkt[tr], y[tr]), bounds=(0, 1), method="bounded").x
                p[te] = w * p_model[te] + (1 - w) * p_mkt[te]; ws.append(round(w, 2))
        evy, evn = p * d_yes - 1, (1 - p) * d_no - 1; yes = evy >= evn; ev = np.maximum(evy, evn)
        won = np.where(yes, y == 1, y == 0); push = np.isnan(y)
        u = np.where(push, 0.0, np.where(won, np.where(yes, d_yes, d_no) - 1, -1.0))
        for bar in bars:
            k = valid & (ev >= bar) & pick_rule(yes)
            if b2b_side is not None: k &= ~np.where(yes, b2b_side[0], b2b_side[1])
            per = [u[k & (H.season == s).values].sum() for s in SEAS]
            print(f"  {kind:5s} EV {bar:.0%}+ " + " ".join(f"{x:+6.1f}" for x in per) + f" | {k.sum():4d} bets {u[k].sum():+6.1f}u ({u[k].sum() / max(k.sum(), 1):+.1%}) worst {min(per):+.1f}"
                  + (f"  weights {ws}" if kind == "blend" and bar == bars[0] else ""))
# ---- puck line: yes = home covers
hl = H.open_home_pl.values; ok = ~np.isnan(hl) & H.open_home_pl_odds.notna().values & H.open_away_pl_odds.notna().values
pm = np.where(hl < 0, H.p_home_by2_open, 1 - H.p_away_by2_open)
mg = (H.home_goals - H.away_goals).values; ycov = np.where(hl < 0, mg >= 2, mg >= -1).astype(float)
run("PUCK LINE", pm, nv(H.open_home_pl_odds, H.open_away_pl_odds), ycov, dec(H.open_home_pl_odds), dec(H.open_away_pl_odds), ok,
    lambda yes: np.ones(len(yes), bool), (0.04, 0.06, 0.09), b2b_side=((H.h_rest == 1).values, (H.a_rest == 1).values))
# ---- totals: yes = over (overs only, as live)
T = H.open_total.values; ok = ~np.isnan(T) & H.open_over_odds.notna().values & H.open_under_odds.notna().values & H.lam_home_open.notna().values
po, pu, pp = nm.over_prob(H.lam_home_open.fillna(3).values, H.lam_away_open.fillna(3).values, np.nan_to_num(T, nan=6.0), nm.H_OT_DEFAULT, {})
pov = po / np.clip(po + pu, 1e-9, None)               # chance of over given no push
tot = (H.home_goals + H.away_goals).values; yov = np.where(tot > T, 1.0, np.where(tot < T, 0.0, np.nan))
run("TOTALS (overs only)", pov, nv(H.open_over_odds, H.open_under_odds), yov, dec(H.open_over_odds), dec(H.open_under_odds), ok & ~np.isnan(yov) | (ok & np.isnan(yov)),
    lambda yes: yes, (0.04, 0.06, 0.09))
