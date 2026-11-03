"""NHL: how much weight does the shot model deserve against the opening price? (Nov 3, 2026, job 3 of research/HANDOFF_TO_OPUS.md)
Data: the out-of-sample SBR seasons 2014-15..2021-22 (dev/oos_sbr_backtest.py predictions; team-only shot model, no goalies),
trusted rows. Logistic regression with the market as an offset:
    logit P(win) = logit(no-vig opener) + w x (logit(model) - logit(no-vig opener))
w = 0: the opener already knows everything; w = 1: trust the model fully. Same for overs (P(over) at the opening total).
Bet rule is NOT tuned: bet when the shrunk chance beats the posted price (EV > 0). Each season uses w fit on the other seasons.
Also checked on this season's live picks (state/picks_log_xg.csv, full live model with goalies), which are few.
  python dev/shrink_weights.py WORKDIR   -> backtests/shrink_weights_output.txt, data/shrink_weights.json"""
import os, sys, json
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm
SEAS = list(range(2015, 2023))
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
ex = lambda z: 1 / (1 + np.exp(-z))
out = []
def say(*a): out.append(" ".join(str(x) for x in a)); print(*a, flush=True)

rows = []
for s in SEAS:
    P = pd.read_csv(os.path.join(W, "_tmp", f"oos_pred_{s}.csv")); M = json.load(open(os.path.join(W, "_tmp", f"oos_meta_{s}.json")))
    ok = (P.open_ml_ok == 1) & (P.close_ml_ok == 1) & (P.ml_move_ok == 1) & P.home_goals.notna()
    P = P[ok].copy()
    hi, ai = 1 / dec(P.open_home_ml), 1 / dec(P.open_away_ml); P["nv"] = hi / (hi + ai)
    P["y"] = (P.home_goals > P.away_goals).astype(float)
    # over at the opening total (rebuilt over price; see backtests/OOS_SBR_RESULTS.md)
    po, pu, pp = nm.over_prob(P.lam_home_open.values, P.lam_away_open.values, P.open_total.values, M["h_ot"], M["cal"]["open"])
    P["p_over_model"] = po / np.clip(po + pu, 1e-9, None)
    oi, ui = 1 / dec(P.open_over_odds), 1 / dec(P.open_under_odds); P["nv_over"] = oi / (oi + ui)
    tot = P.home_goals + P.away_goals; P["y_over"] = np.where(tot == P.open_total, np.nan, (tot > P.open_total).astype(float))
    P["season"] = s; rows.append(P)
D = pd.concat(rows, ignore_index=True)

def fit_w(base, model, y):
    m = ~np.isnan(y) & ~np.isnan(base) & ~np.isnan(model); b, d, y = lg(base[m]), lg(model[m]) - lg(base[m]), y[m]
    nll = lambda w: -np.sum(y * np.log(ex(b + w * d)) + (1 - y) * np.log(1 - ex(b + w * d)))
    w = minimize_scalar(nll, bounds=(-1, 2), method="bounded").x
    h = (nll(w + 1e-3) - 2 * nll(w) + nll(w - 1e-3)) / 1e-6       # curvature -> standard error
    return w, 1 / np.sqrt(h)

cfg = {}
for mk, base, model, y in (("moneyline", "nv", "p_home_win_open", "y"), ("overs", "nv_over", "p_over_model", "y_over")):
    w, se = fit_w(D[base].values, D[model].values, D[y].values)
    per = " | ".join(f"{s}: {fit_w(g[base].values, g[model].values, g[y].values)[0]:+.2f}" for s, g in D.groupby("season"))
    say(f"\n== {mk.upper()}: weight on the model vs the opener, 2015-2022 pooled: {w:.2f} (+/- {se:.2f})"); say("   by season: " + per)
    tot = {k: [0, 0.0] for k in ("shrunk", "live_rule")}
    for s in SEAS:
        tr, te = D[D.season != s], D[D.season == s]
        ws, _ = fit_w(tr[base].values, tr[model].values, tr[y].values)
        p = ex(lg(te[base].values) + ws * (lg(te[model].values) - lg(te[base].values)))
        if mk == "moneyline":
            cand = [(p, te.open_home_ml.values, te.y.values), (1 - p, te.open_away_ml.values, 1 - te.y.values)]
            pm = te[model].values; live = [(0.55 * pm + 0.45 * te.nv.values, te.open_home_ml.values, te.y.values),
                                           (1 - (0.55 * pm + 0.45 * te.nv.values), te.open_away_ml.values, 1 - te.y.values)]
            thr_live = 0.04
        else:
            cand = [(p, te.open_over_odds.values, te.y_over.values)]
            live = [(te[model].values, te.open_over_odds.values, te.y_over.values)]; thr_live = 0.06
        for key, cs, thr in (("shrunk", cand, 0.0), ("live_rule", live, thr_live)):
            ev = np.array([c[0] * dec(c[1]) - 1 for c in cs])         # sides x games
            best = ev.argmax(0); evb = ev.max(0)
            yy = np.array([c[2] for c in cs])[best, np.arange(len(te))]; od = dec(np.array([c[1] for c in cs])[best, np.arange(len(te))])
            m = (evb > thr) & ~np.isnan(yy)
            prof = np.where(yy[m] == 1, od[m] - 1, -1.0)
            tot[key][0] += m.sum(); tot[key][1] += prof.sum()
    say(f"   out of season, bet when shrunk chance beats the price: {tot['shrunk'][0]} bets, {tot['shrunk'][1]:+.1f}u"
        f" ({tot['shrunk'][1] / max(tot['shrunk'][0], 1):+.1%})")
    lr = "55/45 blend, EV 4%+" if mk == "moneyline" else "model only, EV 6%+"
    say(f"   live rule on the same games ({lr}): {tot['live_rule'][0]} bets, {tot['live_rule'][1]:+.1f}u ({tot['live_rule'][1] / max(tot['live_rule'][0], 1):+.1%})")
    cfg[mk] = dict(weight=round(float(w), 3), weight_se=round(float(se), 3), rule="bet when shrunk win chance x decimal odds > 1")

# live 2026-27 picks (full model with goalies): how does its weight look so far?
L = pd.read_csv(os.path.join(W, "state", "picks_log_xg.csv"))
L = L[L.home_goals.notna() & L.open_home_ml.notna()].copy()
hi, ai = 1 / dec(L.open_home_ml), 1 / dec(L.open_away_ml)
wl, sel = fit_w(np.asarray(hi / (hi + ai)), L.p_home_win.values, (L.home_goals > L.away_goals).astype(float).values)
say(f"\nThis season's live shot-model picks (with goalies), moneyline weight vs DraftKings' opener: {wl:.2f} (+/- {sel:.2f}), n={len(L)}")
say("   (live 55/45 blend = weight 0.55 in probability terms; fitted 0.51-0.61 on 2021-26 in backtests/IDEA_TESTS.md)")
cfg["fit"] = dict(seasons="2014-15..2021-22 (SBR openers, out of sample)", model="team-only shot model fed hockeyR xG, no goalies",
                  set_on="2026-11-03", note="the live model has goalies, so its true weight is likely higher; re-fit on live 2026-27 picks after the season")
json.dump(cfg, open(os.path.join(W, "data", "shrink_weights.json"), "w"), indent=1)
open(os.path.join(W, "backtests", "shrink_weights_output.txt"), "w").write("\n".join(out) + "\n")
