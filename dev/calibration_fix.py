"""Fix the shot model's overconfidence on strong favorites (moneyline), each fix fit leaving the test season out, 2021-26,
DraftKings openers, EV 6%+, live rules (no bets on back-to-back teams; schedule/travel adjustment included).
  recal  : logit(p) -> a + b * logit(p)  (b < 1 shrinks extreme chances toward 50%)
  blend  : w * model + (1 - w) * DraftKings' no-vig opener
  shrink60: only chances above 60% pulled toward 60% by a fitted factor
  python dev/calibration_fix.py WORKDIR TRACKER"""
import os, sys
import numpy as np, pandas as pd
from scipy.optimize import minimize, minimize_scalar
W = os.path.abspath(sys.argv[1]); TRK = os.path.abspath(sys.argv[2])
H = pd.concat([pd.read_csv(os.path.join(W, "_tmp", f"dk_holdout_{s}.csv")) for s in (2022, 2023, 2024, 2025, 2026)], ignore_index=True)
TN = pd.read_csv(os.path.join(TRK, "analysis", "travel_nhl_games.csv"))[["date", "home", "away", "h_rest", "a_rest", "a_tz_move"]]
H = H.merge(TN, on=["date", "home", "away"], how="left").dropna(subset=["open_home_ml", "open_away_ml", "p_home_win_open"]).reset_index(drop=True)
H["hw"] = (H.home_goals > H.away_goals).astype(float)
ab = ((H.a_rest == 1) & (H.h_rest > 1)).astype(float); hb = ((H.h_rest == 1) & (H.a_rest > 1)).astype(float); west = (-H.a_tz_move).clip(lower=0).fillna(0)
H["p0"] = (H.p_home_win_open + 0.0253 * ab - 0.0307 * hb - 0.0226 * west).clip(0.02, 0.98)        # live model incl. travel
dec = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
ih, ia = 1 / dec(H.open_home_ml), 1 / dec(H.open_away_ml); H["mkt"] = ih / (ih + ia)
lg = lambda p: np.log(p / (1 - p)); ex = lambda z: 1 / (1 + np.exp(-z))
ll = lambda p, y: -np.mean(y * np.log(np.clip(p, 1e-6, 1 - 1e-6)) + (1 - y) * np.log(np.clip(1 - p, 1e-6, 1 - 1e-6)))
SEAS = sorted(H.season.unique())
def fit_apply(kind, tr, te):
    if kind == "current": return te.p0.values
    if kind == "recal":
        f = lambda v: ll(ex(v[0] + v[1] * lg(tr.p0)), tr.hw); a, b = minimize(f, [0, 1]).x; return ex(a + b * lg(te.p0)).values
    if kind == "blend":
        w = minimize_scalar(lambda w: ll(w * tr.p0 + (1 - w) * tr.mkt, tr.hw), bounds=(0, 1), method="bounded").x; return (w * te.p0 + (1 - w) * te.mkt).values
    if kind == "shrink60":
        def sh(p, k): q = p.copy(); hi = q > 0.6; q[hi] = 0.6 + k * (q[hi] - 0.6); lo = q < 0.4; q[lo] = 0.4 - k * (0.4 - q[lo]); return q
        k = minimize_scalar(lambda k: ll(sh(tr.p0.values, k), tr.hw), bounds=(0, 1.5), method="bounded").x; return sh(te.p0.values, k)
for kind in ("current", "recal", "shrink60", "blend"):
    p = np.zeros(len(H)); per = []; tot_u = tot_n = 0
    for s in SEAS:
        te = H.season == s; p[te.values] = fit_apply(kind, H[~te], H[te])
    dh, da = dec(H.open_home_ml), dec(H.open_away_ml); evh, eva = p * dh - 1, (1 - p) * da - 1
    home = evh >= eva; ev = np.maximum(evh, eva)
    b2b_us = np.where(home, H.h_rest == 1, H.a_rest == 1)
    won = np.where(home, H.hw == 1, H.hw == 0); u = np.where(won, np.where(home, dh, da) - 1, -1.0)
    k = (ev >= 0.06) & ~b2b_us
    for s in SEAS: per.append(u[k & (H.season == s).values].sum())
    ps = np.where(home, p, 1 - p); fav = k & (ps > 0.6)
    print(f"  {kind:9s} Brier {np.mean((p - H.hw) ** 2):.4f} | " + " ".join(f"{x:+6.1f}" for x in per) + f" | {k.sum()} bets {u[k].sum():+6.1f}u ({u[k].sum() / k.sum():+.1%})"
          f" | bets said 60%+: said {ps[fav].mean():.1%} won {won[fav].mean():.1%} {u[fav].sum():+.1f}u")
print(f"  DK opener Brier {np.mean((H.mkt - H.hw) ** 2):.4f}")
