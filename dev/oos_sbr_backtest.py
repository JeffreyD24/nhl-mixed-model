"""NHL out-of-sample test on 2014-15 .. 2021-22 (pre-registered in backtests/OOS_SBR_PREREG.md).
  python dev/oos_sbr_build.py WORKDIR          (once: builds _tmp/oos_games.csv)
  python dev/oos_sbr_backtest.py WORKDIR predict [season ...]   -> _tmp/oos_pred_<season>.csv
  python dev/oos_sbr_backtest.py WORKDIR score                  -> backtests/OOS_SBR_RESULTS.md + backtests/oos_sbr_bets.csv
Model: the live shot model's machinery (nhl_xg_model.run), fed hockeyR xG, no goalies, one-day lag."""
import os, sys, json
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_xg_model as xm

PIPELINE = [2015, 2016]
HOLDOUT = [2017, 2018, 2019, 2020, 2021, 2022]
FIRST_TRAIN = 2012          # 2010-11 has no SBR regulation scores
TMP = os.path.join(W, "_tmp")

# The historical data has no missing-skater information, so that fixed-effect column is all zeros and the REML system is
# singular. Fit without all-zero columns and give them a coefficient of 0 (identical to the live model with no injuries).
_fit = xm.fit
def _fit_dropzero(X, Zs, y):
    keep = np.abs(X).sum(0) > 0
    r = _fit(X[:, keep], Zs, y)
    b = np.zeros(X.shape[1]); b[keep] = r["b"]; r["b"] = b
    return r
xm.fit = _fit_dropzero


def train_for(s): return [y for y in range(max(FIRST_TRAIN, s - 4), s)]


def predict(seasons):
    D = pd.read_csv(os.path.join(TMP, "oos_games.csv"))
    # No starting goalies in the historical data: every game gets one placeholder "league goalie" (id 0), so the goalie block
    # becomes a single league-level conversion effect per season (updated in season), and both prediction modes are identical.
    for side in ("home", "away"):
        D[f"{side}_goalie"] = 0; D[f"{side}_gmix"] = '{"0": 1.0}'
    for s in seasons:
        summ, P, x = xm.run(D[D.season.isin(train_for(s) + [s])], train_for(s), s, tot_cal="none", lag_days=1)
        P.to_csv(os.path.join(TMP, f"oos_pred_{s}.csv"), index=False)
        json.dump(dict(summary=summ, cal=x["cal"], h_ot=x["h_ot"]), open(os.path.join(TMP, f"oos_meta_{s}.json"), "w"), default=float)
        print(s, "train", train_for(s), "half-life", summ["halflife"], "rho", {k: round(v, 2) for k, v in summ["rho"].items()}, flush=True)


dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))


def novig(a, b):
    pa, pb = 1 / dec(a), 1 / dec(b); return pa / (pa + pb)


def ml_rows(P, s):
    """one row per game and side with model prob, open/close prices, no-vig probs, result"""
    out = []
    for side, opp, sign in (("home", "away", 1), ("away", "home", -1)):
        pm = P.p_home_win_open if side == "home" else 1 - P.p_home_win_open
        out.append(pd.DataFrame(dict(season=s, date=P.date, home=P.home, away=P.away, side=side, team=P[side], p_model=pm.values,
                                     open_price=P[f"open_{side}_ml"], close_price=P[f"close_{side}_ml"],
                                     nv_open=novig(P[f"open_{side}_ml"], P[f"open_{opp}_ml"]), nv_close=novig(P[f"close_{side}_ml"], P[f"close_{opp}_ml"]),
                                     b2b=P[f"b2b_{side}"], win=np.where(P.home_goals.isna(), np.nan, (sign * (P.home_goals - P.away_goals) > 0).astype(float)),
                                     trusted=((P.open_ml_ok == 1) & (P.close_ml_ok == 1) & (P.ml_move_ok == 1)).astype(int))))
    return pd.concat(out, ignore_index=True)


def pick(R, pcol, price_col, thr, extra=None):
    """best-EV side per game, kept when EV >= thr"""
    R = R.copy(); R["ev"] = R[pcol] * dec(R[price_col]) - 1
    if extra is not None: R = R[extra(R)]
    R = R.dropna(subset=["ev", "win"]).sort_values("ev", ascending=False).drop_duplicates(["season", "date", "home", "away"])
    R = R[R.ev >= thr].copy()
    R["profit"] = np.where(R.win == 1, dec(R[price_col]) - 1, -1.0)
    return R


def score():
    preds = {s: pd.read_csv(os.path.join(TMP, f"oos_pred_{s}.csv")) for s in PIPELINE + HOLDOUT if os.path.exists(os.path.join(TMP, f"oos_pred_{s}.csv"))}
    meta = {s: json.load(open(os.path.join(TMP, f"oos_meta_{s}.json"))) for s in preds}
    allbets, acc = [], []
    for s, P in preds.items():
        R = ml_rows(P, s)
        R["p_blend"] = 0.55 * R.p_model + 0.45 * R.nv_open
        R["p_blend_close"] = 0.55 * R.p_model + 0.45 * R.nv_close
        for name, pc, prc, thr, ex in (("ML plain @open", "p_model", "open_price", 0.06, None),
                                       ("ML plain @close", "p_model", "close_price", 0.06, None),
                                       ("ML blend @open", "p_blend", "open_price", 0.04, lambda r: r.b2b == 0),
                                       ("ML blend @close", "p_blend_close", "close_price", 0.04, lambda r: r.b2b == 0)):
            b = pick(R, pc, prc, thr, ex); b["rule"] = name
            b["clv"] = b.nv_close * dec(b.open_price) - 1 if "@open" in name else np.nan
            b["price"] = b[prc]
            allbets.append(b[["season", "date", "home", "away", "rule", "side", "team", "price", "ev", "win", "profit", "clv", "trusted"]])
        # overs at the opening total (SBR posts one price per total: taken as the over price; see OOS_SBR_RESULTS.md)
        cal, h_ot = meta[s]["cal"]["open"], meta[s]["h_ot"]
        tot = P.home_goals + P.away_goals
        for ln in ("open", "close"):
            ok = P[[f"{ln}_total", f"{ln}_over_odds"]].notna().all(axis=1) & tot.notna()
            Q = P[ok]
            po, pu, pp = nm.over_prob(Q.lam_home_open.values, Q.lam_away_open.values, Q[f"{ln}_total"].values, h_ot, cal)
            d = dec(Q[f"{ln}_over_odds"]); ev = po * d + pp - 1
            T = Q[f"{ln}_total"].values; tq = tot[ok].values
            b = pd.DataFrame(dict(season=s, date=Q.date, home=Q.home, away=Q.away, rule=f"Overs @{ln}", side="over", team="",
                                  price=Q[f"{ln}_over_odds"], ev=ev, win=np.where(tq == T, np.nan, (tq > T).astype(float)),
                                  trusted=((Q.open_total_ok == 1) & (Q.close_total_ok == 1)).astype(int).values,
                                  same_line=(Q.open_total == Q.close_total).values, push=(tq == T)))
            b = b[b.ev >= 0.06].copy()
            b["profit"] = np.where(b.push, 0.0, np.where(b.win == 1, d[b.index.map(lambda i: Q.index.get_loc(i))] - 1, -1.0))
            if ln == "open":
                ql = Q.loc[b.index]
                fair_close = novig(ql.close_over_odds, ql.close_under_odds)
                b["clv"] = np.where(b.same_line, fair_close * dec(ql.open_over_odds) - 1, np.nan)
                b["line_move"] = (ql.close_total - ql.open_total).values
            else:
                b["clv"] = np.nan
            allbets.append(b.drop(columns=["same_line", "push"]))
        # puck line at the close (no opening puck line in SBR)
        if P.close_home_pl.notna().any():
            Bt = nm.bets(P, "close", "_open", cal, h_ot)
            b = Bt[(Bt.market == "puck line") & (Bt.ev >= 0.06) & Bt.profit.notna()].copy()
            g = P.loc[b.idx]
            b = pd.DataFrame(dict(season=s, date=g.date.values, home=g.home.values, away=g.away.values, rule="Puck line @close",
                                  side=b.side.values, team="", price=b.price.values, ev=b.ev.values, win=b.win.values,
                                  profit=b.profit.values, clv=np.nan, trusted=((g.close_ml_ok == 1) & (g.ml_move_ok == 1)).astype(int).values))
            allbets.append(b)
        # accuracy: model vs market (moneyline, games with a result and both prices)
        okm = P.home_goals.notna() & P.open_home_ml.notna() & P.close_home_ml.notna()
        y = (P.home_goals > P.away_goals)[okm].astype(float)
        acc.append(dict(season=s, games=int(okm.sum()),
                        brier_model=float(((P.p_home_win_open[okm] - y) ** 2).mean()),
                        brier_open=float(((novig(P.open_home_ml[okm], P.open_away_ml[okm]) - y) ** 2).mean()),
                        brier_close=float(((novig(P.close_home_ml[okm], P.close_away_ml[okm]) - y) ** 2).mean()),
                        brier_blend=float(((0.55 * P.p_home_win_open[okm] + 0.45 * novig(P.open_home_ml[okm], P.open_away_ml[okm]) - y) ** 2).mean()),
                        halflife=meta[s]["summary"]["halflife"]))
    B = pd.concat(allbets, ignore_index=True)
    B.to_csv(os.path.join(W, "backtests", "oos_sbr_bets.csv"), index=False)
    pd.DataFrame(acc).to_csv(os.path.join(W, "backtests", "oos_sbr_accuracy.csv"), index=False)
    return B, pd.DataFrame(acc)


def boot(b, n=2000, seed=7):
    """resample bets within each season; returns 5th/95th percentile ROI and share of draws below 0"""
    rng = np.random.default_rng(seed); groups = [g.profit.values for _, g in b.groupby("season")]
    tot = len(b); r = np.empty(n)
    for i in range(n):
        r[i] = sum(rng.choice(g, len(g)).sum() for g in groups) / tot
    return np.percentile(r, 5), np.percentile(r, 95), (r < 0).mean()


def summarize(B, seasons, trusted_only=False):
    rows = []
    for rule, b in B[B.season.isin(seasons)].groupby("rule", sort=False):
        b = b[b.profit.notna()]
        if trusted_only: b = b[b.trusted == 1]
        if not len(b): continue
        lo, hi, pneg = boot(b)
        w, l = int((b.profit > 0).sum()), int((b.profit < 0).sum())
        rows.append(dict(rule=rule, bets=w + l, win_pct=w / max(w + l, 1), units=b.profit.sum(), roi=b.profit.sum() / len(b),
                         roi_lo=lo, roi_hi=hi, p_loss=pneg, avg_clv=b.clv.mean(), clv_pos=(b.clv > 0).mean() if b.clv.notna().any() else np.nan,
                         median_price=b.price.median()))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    if sys.argv[2] == "predict":
        predict([int(x) for x in sys.argv[3:]] or PIPELINE + HOLDOUT)
    else:
        B, A = score()
        pd.set_option("display.width", 200)
        for lab, ss in (("PIPELINE 2015-2016", PIPELINE), ("HOLDOUT 2017-2022", HOLDOUT)):
            for tr in (False, True):
                print(f"\n== {lab} {'trusted rows' if tr else 'all rows'}")
                print(summarize(B, ss, tr).round(3).to_string(index=False))
        print("\n== by season (holdout, all rows)")
        for rule in ("ML plain @open", "ML blend @open", "Overs @open", "Puck line @close"):
            t = B[(B.rule == rule) & B.season.isin(HOLDOUT) & B.profit.notna()].groupby("season").agg(
                bets=("profit", "size"), units=("profit", "sum"), clv=("clv", "mean"))
            print(rule); print(t.round(3).to_string())
        print("\n== accuracy (Brier, lower is better)"); print(A.round(4).to_string(index=False))
