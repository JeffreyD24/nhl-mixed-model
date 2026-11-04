"""Tie-inflated score matrix test (pre-registered: backtests/TIE_INFLATION_PREREG.md).
  python dev/tie_inflation_test.py WORKDIR  -> backtests/tie_inflation_output.txt"""
import os, sys, io, json, contextlib
import numpy as np, pandas as pd
from scipy import stats
from scipy.optimize import brentq
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm
rng = np.random.default_rng(1104); out = []
def say(*a): s = " ".join(str(x) for x in a); out.append(s); print(s, flush=True)
K = np.arange(nm.MAXG); DIFF = K[:, None] - K[None, :]; TOT = K[:, None] + K[None, :]; FIN = TOT + (DIFF == 0)

def probs(lh, la, h_ot, w):
    M = nm.score_matrix(lh, la)
    if w:
        D = M * (DIFF == 0); D = D / D.sum((1, 2), keepdims=True); M = (1 - w) * M + w * D
    tie = (M * (DIFF == 0)).sum((1, 2))
    return dict(tie=tie, ml=(M * (DIFF > 0)).sum((1, 2)) + h_ot * tie, hb2=(M * (DIFF >= 2)).sum((1, 2)), ab2=(M * (DIFF <= -2)).sum((1, 2)),
                o55=(M * (FIN > 5.5)).sum((1, 2)), o65=(M * (FIN > 6.5)).sum((1, 2)))
def outcomes(P):
    hg, ag = P.home_goals.values, P.away_goals.values; mg = hg - ag; tot = hg + ag
    return dict(ml=(mg > 0).astype(float), hb2=(mg >= 2).astype(float), ab2=(mg <= -2).astype(float), o55=(tot > 5.5).astype(float), o65=(tot > 6.5).astype(float))
def clean(P):
    P = P.dropna(subset=["home_goals", "away_goals", "home_reg", "away_reg", "lam_home_open", "lam_away_open"]).copy()
    if "open_ml_ok" in P: P = P[(P.open_ml_ok == 1) & (P.close_ml_ok == 1) & (P.ml_move_ok == 1)]
    return P.reset_index(drop=True)

# ---- data: SBR team-only predictions 2015..2022; live shot model 2024..2026 (DK)
SB = {s: clean(pd.read_csv(os.path.join(W, "_tmp", f"oos_pred_{s}.csv"))) for s in range(2015, 2023)}
HOT = {s: json.load(open(os.path.join(W, "_tmp", f"oos_meta_{s}.json")))["h_ot"] for s in range(2015, 2023)}
T0 = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
DK = {}
for test in (2024, 2025, 2026):
    train = list(range(test - 4, test))
    with contextlib.redirect_stdout(io.StringIO()):
        _, P, x = xm.run(T0[T0.season.isin(train + [test])], train, test, lag_days=1)
    DK[test] = clean(P); HOT[("dk", test)] = x["h_ot"]; say(f"live shot model {test}: {len(DK[test])} games")

# ---- fit w on the pipeline seasons only
pipe = pd.concat([SB[2015], SB[2016]], ignore_index=True)
obs_tie = float((pipe.home_reg == pipe.away_reg).mean())
f = lambda w: probs(pipe.lam_home_open.values, pipe.lam_away_open.values, 0.5, w)["tie"].mean() - obs_tie
w = brentq(f, 0.0, 0.9)
say(f"Fit on 2014-16 ({len(pipe)} games): observed regulation tie rate {obs_tie:.1%}, independent Poisson {f(0)+obs_tie:.1%} -> w = {w:.4f} (frozen)")

def ll(p, y): p = np.clip(p, 1e-6, 1 - 1e-6); return -(y * np.log(p) + (1 - y) * np.log(1 - p))
def evaluate(lab, frames, hot, prev):
    rows = []; res = {}
    for s, P in frames.items():
        Q = prev[s]; y = outcomes(P); yq = outcomes(Q)
        rec = dict(season=s, n=len(P), tie_obs=float((P.home_reg == P.away_reg).mean()))
        for name, ww in (("cur", 0.0), ("inf", w)):
            pr = probs(P.lam_home_open.values, P.lam_away_open.values, hot[s], ww)
            pq = probs(Q.lam_home_open.values, Q.lam_away_open.values, hot[s], ww)
            rec[f"tie_{name}"] = float(pr["tie"].mean())
            for m in ("ml", "hb2", "ab2", "o55", "o65"):
                c = nm.fit_calibration(pq[m], yq[m]); p = nm.calibrate(pr[m], c)
                res.setdefault((name, m), []).append(ll(p, y[m])); res.setdefault(("date", m), []).append(P.date.values) if name == "cur" else None
                res.setdefault((name, m, "p"), []).append(p)
        rows.append(rec)
    R = pd.DataFrame(rows)
    say(f"\n== {lab}: regulation tie rate by season (observed / current matrix / tie-inflated)")
    say("  " + "; ".join(f"{r.season}: {r.tie_obs:.1%} / {r.tie_cur:.1%} / {r.tie_inf:.1%}" for r in R.itertuples()))
    say(f"  log loss, current minus tie-inflated (positive = inflated better), per game x1000, 95% interval by date:")
    verdict = {}
    for m, nmn in (("ml", "moneyline"), ("hb2", "home -1.5"), ("ab2", "away -1.5"), ("o55", "over 5.5"), ("o65", "over 6.5")):
        d = np.concatenate(res[("cur", m)]) - np.concatenate(res[("inf", m)]); dates = np.concatenate(res[("date", m)])
        g = pd.DataFrame({"d": d, "date": dates}).groupby("date").d.agg(["sum", "count"]).values
        bs = np.array([(lambda i: g[i, 0].sum() / g[i, 1].sum())(rng.integers(0, len(g), len(g))) for _ in range(3000)])
        lo, hi = np.percentile(bs, [2.5, 97.5]); verdict[m] = (d.mean(), lo, hi)
        bys = pd.Series(d).groupby(np.concatenate([[s] * n for s, n in zip(R.season, R.n)])).mean()
        say(f"  {nmn:10s} {1000*d.mean():+.2f} [{1000*lo:+.2f}, {1000*hi:+.2f}]  by season " + ", ".join(f"{s}:{1000*v:+.1f}" for s, v in bys.items()))
    return verdict, res
VA, resA = evaluate("Holdout A: 2016-17..2021-22 (team-only model, SBR)", {s: SB[s] for s in range(2017, 2023)}, HOT, {s: SB[s - 1] for s in range(2017, 2023)})
VB, resB = evaluate("Holdout B: 2024-25, 2025-26 (live shot model, DK)", {s: DK[s] for s in (2025, 2026)}, {s: HOT[("dk", s)] for s in (2025, 2026)}, {s: DK[s - 1] for s in (2025, 2026)})

better = {m: VA[m][1] > 0 and VB[m][0] > 0 for m in VA}
ml_ok = VA["ml"][1] > 0 or VA["ml"][0] >= 0 and VA["ml"][1] > -1e9
ml_not_worse = VA["ml"][2] > 0 and VA["ml"][0] >= VA["ml"][1]   # interval upper > 0: no clear loss
ml_not_worse = not (VA["ml"][2] < 0)
say("\n== Decision (rule set in advance)")
say("  'better' (holdout A interval > 0 and holdout B gain > 0): " + ", ".join(f"{m}: {'yes' if v else 'no'}" for m, v in better.items()))
say(f"  moneyline not worse: {'yes' if ml_not_worse else 'no'}")
rec_ = (better["hb2"] or better["ab2"] or better["o55"] or better["o65"]) and ml_not_worse
say("  -> " + ("RECOMMEND the tie-inflated matrix for a live test (needs approval; new NHL version record)." if rec_ else "Do NOT change the live matrix."))

# ---- descriptive betting check: puck line at DK opening prices (holdout B), EV 9%+, current vs inflated
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
say("\n== Descriptive: puck line EV 9%+ at DraftKings opening prices, 2024-26 (favorite -1.5 / dog +1.5 as posted)")
for name in ("cur", "inf"):
    tot_u, nb = 0.0, 0
    for i, s in enumerate((2025, 2026)):
        P = DK[s]; ph2 = resB[(name, "hb2", "p")][i]; pa2 = resB[(name, "ab2", "p")][i]
        ok = P.open_home_pl.notna() & P.open_home_pl_odds.notna() & P.open_away_pl_odds.notna()
        hl = P.open_home_pl.values; mg = (P.home_goals - P.away_goals).values
        p_home = np.where(hl < 0, ph2, 1 - pa2); won_home = np.where(hl < 0, mg >= 2, mg >= -1)
        for side, p, odds, won in (("home", p_home, P.open_home_pl_odds.values, won_home), ("away", 1 - p_home, P.open_away_pl_odds.values, ~won_home)):
            ev = p * dec(odds) - 1; m = ok.values & (ev >= 0.09)
            tot_u += np.where(won[m], dec(odds[m]) - 1, -1.0).sum(); nb += m.sum()
    say(f"  {'current' if name=='cur' else 'tie-inflated'}: {nb} bets, {tot_u:+.1f}u ({tot_u/max(nb,1):+.1%})")
open(os.path.join(W, "backtests", "tie_inflation_output.txt"), "w").write("\n".join(out) + "\n")

# ---- why: the same comparison WITHOUT the recalibration step (raw matrix probabilities)
say("\n== Why (descriptive): same holdout A comparison without the per-market recalibration, x1000")
for m, nmn in (("ml", "moneyline"), ("hb2", "home -1.5"), ("ab2", "away -1.5"), ("o55", "over 5.5"), ("o65", "over 6.5")):
    d = []
    for s in range(2017, 2023):
        P = SB[s]; y = outcomes(P)[m]
        pc = probs(P.lam_home_open.values, P.lam_away_open.values, HOT[s], 0.0)[m]; pi_ = probs(P.lam_home_open.values, P.lam_away_open.values, HOT[s], w)[m]
        d.append(ll(pc, y) - ll(pi_, y))
    d = np.concatenate(d); say(f"  {nmn:10s} {1000*d.mean():+.2f} (raw)")
open(os.path.join(W, "backtests", "tie_inflation_output.txt"), "w").write("\n".join(out) + "\n")
