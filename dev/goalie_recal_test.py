"""NHL holdout tests with goalies + underdog recalibration (pre-registered: backtests/GOALIE_RECAL_PREREG.md, commits 85f062d and dc9ae9e).
  python dev/oos_sbr_build.py WORKDIR                       (once: _tmp/oos_games.csv)
  python dev/goalie_recal_test.py WORKDIR build             -> _tmp/oos_games_g.csv (actual starter + expected starter, one-day lag)
  python dev/goalie_recal_test.py WORKDIR predict G0|G1 [season ...]  -> _tmp/gr_<V>_pred_<season>.csv
  python dev/goalie_recal_test.py WORKDIR score             -> backtests/goalie_recal_output.txt, backtests/goalie_recal_bets.csv"""
import os, sys, json
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W); sys.path.insert(0, os.path.join(W, "dev"))
import nhl_mixed_model as nm, nhl_xg_model as xm
import oos_sbr_backtest as ob            # reuses its fit patch (all-zero injury column), train window, dec/novig helpers

TMP = os.path.join(W, "_tmp")
PIPELINE, HOLDOUT = ob.PIPELINE, ob.HOLDOUT
B2B_SAME_FACTOR = 0.1


def build():
    D = pd.read_csv(os.path.join(TMP, "oos_games.csv")); D["date"] = pd.to_datetime(D.date)
    Gl = pd.read_csv(os.path.join(W, "data/external/nhl_box/goalies_hockeyr_2010_2023.csv.gz"))
    Gl = Gl[(Gl.starter == 1) & (Gl.season_type == "R") & Gl.goalie_id.notna()]
    st = {(int(r.game_id), int(r.is_home)): int(r.goalie_id) for r in Gl.itertuples()}
    D["home_goalie"] = [st.get((g, 1)) for g in D.game_id]; D["away_goalie"] = [st.get((g, 0)) for g in D.game_id]
    # expected starter at the open, as build_features.py with lag_days=1
    long = pd.concat([pd.DataFrame(dict(i=D.index, date=D.date, team=D.home, side="home", starter=D.home_goalie)),
                      pd.DataFrame(dict(i=D.index, date=D.date, team=D.away, side="away", starter=D.away_goalie))]).sort_values(["team", "date"])
    gmix = {}
    for team, g in long.groupby("team"):
        full, prev_date = [], None
        for r in g.itertuples():
            hist = [h for h in full if h[0] < r.date - pd.Timedelta(days=1)]
            s = [x for _, x in hist[-10:] if x is not None and not pd.isna(x)]
            w = {}
            for x in s: w[int(x)] = w.get(int(x), 0) + 1
            if prev_date is not None and (r.date - prev_date).days == 1 and w:
                likely = max(w, key=w.get); w[likely] *= B2B_SAME_FACTOR     # yesterday's starter not known yet: assume the usual one
            tot = sum(w.values()) or 1
            gmix[(r.i, r.side)] = json.dumps({str(k): v / tot for k, v in w.items()})
            full.append((r.date, r.starter)); prev_date = r.date
    for side in ("home", "away"):
        D[f"{side}_gmix"] = [gmix[(i, side)] for i in D.index]
    D["date"] = D.date.dt.strftime("%Y-%m-%d")
    D.to_csv(os.path.join(TMP, "oos_games_g.csv"), index=False)
    ok = D.home_goalie.notna() & D.away_goalie.notna()
    # how often the expected starter (top of the mix) was the actual starter
    top = lambda m: (max(json.loads(m).items(), key=lambda kv: kv[1])[0] if m and json.loads(m) else None)
    hit = np.mean([str(int(a)) == top(m) for a, m in zip(D.home_goalie[ok], D.home_gmix[ok]) if top(m)])
    print(f"games {len(D)}, both starters known {ok.mean():.2%}; expected starter = actual starter {hit:.1%}")


def predict(V, seasons):
    D = pd.read_csv(os.path.join(TMP, "oos_games_g.csv"))
    if V == "G0":
        for side in ("home", "away"):
            D[f"{side}_goalie"] = 0; D[f"{side}_gmix"] = '{"0": 1.0}'
    for s in seasons:
        summ, P, x = xm.run(D[D.season.isin(ob.train_for(s) + [s])], ob.train_for(s), s, tot_cal="none", lag_days=1)
        P.to_csv(os.path.join(TMP, f"gr_{V}_pred_{s}.csv"), index=False)
        json.dump(dict(summary=summ, cal=x["cal"], h_ot=x["h_ot"]), open(os.path.join(TMP, f"gr_{V}_meta_{s}.json"), "w"), default=float)
        print(V, s, "half-life", summ["halflife"], "sd_goalie", round(summ["sd_goalie"], 3), flush=True)


# ---------------------------------------------------------------- scoring
dec, novig = ob.dec, ob.novig
lg = lambda p: np.log(p / (1 - p)); ex = lambda z: 1 / (1 + np.exp(-z))
def ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6); return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


def load(V):
    out = []
    for s in PIPELINE + HOLDOUT:
        f = os.path.join(TMP, f"gr_{V}_pred_{s}.csv")
        if os.path.exists(f):
            P = pd.read_csv(f); P["season"] = s
            m = json.load(open(os.path.join(TMP, f"gr_{V}_meta_{s}.json"))); P["_cal"] = json.dumps(m["cal"]["open"]); P["_hot"] = m["h_ot"]
            out.append(P)
    P = pd.concat(out, ignore_index=True)
    P["nv_open"] = novig(P.open_home_ml, P.open_away_ml); P["nv_close"] = novig(P.close_home_ml, P.close_away_ml)
    P["y"] = np.where(P.home_goals.isna(), np.nan, (P.home_goals > P.away_goals).astype(float))
    P["trusted"] = ((P.open_ml_ok == 1) & (P.close_ml_ok == 1) & (P.ml_move_ok == 1)).astype(int)
    return P


def fit_recal(P):
    from scipy.optimize import minimize
    Q = P.dropna(subset=["y", "p_home_win_open"])
    return minimize(lambda v: ll(ex(v[0] + v[1] * lg(Q.p_home_win_open.clip(.01, .99))), Q.y), [0, 1]).x


def fit_w(P, split):
    """R2: p = nv + w_k (model - nv); k by direction of disagreement (split) or one shared w"""
    from scipy.optimize import minimize_scalar
    Q = P.dropna(subset=["y", "p_home_win_open", "nv_open"]).copy()
    d = Q.p_home_win_open - Q.nv_open
    dog_home = Q.nv_open < 0.5
    toward_dog = np.where(dog_home, d > 0, d < 0)                      # model gives the underdog more than the opener does
    if not split:
        return {"all": minimize_scalar(lambda w: ll(Q.nv_open + w * d, Q.y), bounds=(0, 1.5), method="bounded").x}
    out = {}
    for k, m in (("dog", toward_dog), ("fav", ~toward_dog)):
        out[k] = minimize_scalar(lambda w: ll(Q.nv_open[m] + w * d[m], Q.y[m]), bounds=(0, 1.5), method="bounded").x
    return out


def apply_w(P, ws):
    d = P.p_home_win_open - P.nv_open
    if "all" in ws: return (P.nv_open + ws["all"] * d).clip(.01, .99)
    toward_dog = np.where(P.nv_open < 0.5, d > 0, d < 0)
    return (P.nv_open + np.where(toward_dog, ws["dog"], ws["fav"]) * d).clip(.01, .99)


def variants(P1):
    """walk-forward: each test season's recalibration fit on earlier seasons' out-of-sample predictions"""
    P1 = P1.copy(); P1["p_r1"] = np.nan; P1["p_r2"] = np.nan; P1["p_r2s"] = np.nan; fits = {}
    for s in HOLDOUT:
        tr = P1[P1.season < s]; te = P1.season == s
        a, b = fit_recal(tr); P1.loc[te, "p_r1"] = ex(a + b * lg(P1.loc[te, "p_home_win_open"].clip(.01, .99)))
        w2 = fit_w(tr, True); w1 = fit_w(tr, False)
        P1.loc[te, "p_r2"] = apply_w(P1[te], w2); P1.loc[te, "p_r2s"] = apply_w(P1[te], w1)
        fits[s] = dict(a=round(a, 3), b=round(b, 3), w_dog=round(w2["dog"], 3), w_fav=round(w2["fav"], 3), w_shared=round(w1["all"], 3))
    return P1, fits


def bets(P, pcol, thr, skip_b2b, rule):
    rows = []
    for side, opp, sgn in (("home", "away", 1), ("away", "home", -1)):
        p = P[pcol] if side == "home" else 1 - P[pcol]
        nvo = P.nv_open if side == "home" else 1 - P.nv_open
        nvc = P.nv_close if side == "home" else 1 - P.nv_close
        rows.append(pd.DataFrame(dict(season=P.season, date=P.date, home=P.home, away=P.away, side=side, p=p, nv_open=nvo, nv_close=nvc,
                                      price=P[f"open_{side}_ml"], b2b=P[f"b2b_{side}"],
                                      win=np.where(P.y.isna(), np.nan, (P.y == 1) if side == "home" else (P.y == 0)).astype(float),
                                      trusted=P.trusted)))
    R = pd.concat(rows, ignore_index=True).dropna(subset=["p", "price", "win", "nv_close"])
    R["ev"] = R.p * dec(R.price) - 1
    if skip_b2b: R = R[R.b2b == 0]
    R = R.sort_values("ev", ascending=False).drop_duplicates(["season", "date", "home", "away"])
    R = R[R.ev >= thr].copy()
    R["profit"] = np.where(R.win == 1, dec(R.price) - 1, -1.0)
    R["clv"] = (R.nv_close - R.nv_open) * 100                 # win-% points the market moved toward the bet
    R["rule"] = rule
    return R


def boot_days(B, stat, n=4000, seed=11):
    rng = np.random.default_rng(seed); days = B.date.unique(); grp = B.groupby("date").indices
    out = np.empty(n)
    for i in range(n):
        idx = np.concatenate([grp[d] for d in rng.choice(days, len(days))]); out[i] = stat(B.iloc[idx])
    return np.percentile(out, 5), np.percentile(out, 95)


def paired_clv(A, Bb, n=4000, seed=13):
    """difference in mean CLV (B - A), resampling the same game days for both bet sets"""
    rng = np.random.default_rng(seed); days = np.union1d(A.date.unique(), Bb.date.unique())
    ga, gb = A.groupby("date").clv.agg(["sum", "count"]), Bb.groupby("date").clv.agg(["sum", "count"])
    ga, gb = ga.reindex(days, fill_value=0).values, gb.reindex(days, fill_value=0).values
    out = np.empty(n)
    for i in range(n):
        k = rng.integers(0, len(days), len(days))
        out[i] = gb[k, 0].sum() / max(gb[k, 1].sum(), 1) - ga[k, 0].sum() / max(ga[k, 1].sum(), 1)
    return gb[:, 0].sum() / gb[:, 1].sum() - ga[:, 0].sum() / ga[:, 1].sum(), np.percentile(out, 5), np.percentile(out, 95)


def overs(P):
    out = []
    for s, Q in P.groupby("season"):
        cal = json.loads(Q._cal.iloc[0]); h_ot = Q._hot.iloc[0]
        tot = Q.home_goals + Q.away_goals
        ok = Q[["open_total", "open_over_odds"]].notna().all(axis=1) & tot.notna(); Q = Q[ok]; tq = tot[ok].values
        po, pu, pp = nm.over_prob(Q.lam_home_open.values, Q.lam_away_open.values, Q.open_total.values, h_ot, cal)
        d = dec(Q.open_over_odds); ev = po * d + pp - 1; T = Q.open_total.values
        b = pd.DataFrame(dict(season=s, date=Q.date.values, ev=ev, push=tq == T, win=(tq > T).astype(float), d=d,
                              trusted=((Q.open_total_ok == 1) & (Q.close_total_ok == 1)).astype(int).values,
                              move=(Q.close_total - Q.open_total).values))
        b = b[(b.ev >= 0.06)].copy(); b["profit"] = np.where(b.push, 0.0, np.where(b.win == 1, b.d - 1, -1.0)); out.append(b)
    return pd.concat(out, ignore_index=True)


def score():
    lines = []
    def say(*a):
        lines.append(" ".join(str(x) for x in a)); print(*a, flush=True)
    P0, P1 = load("G0"), load("G1")
    P1, fits = variants(P1)
    say("NHL holdout with goalies + recalibration (pre-registered: backtests/GOALIE_RECAL_PREREG.md). Holdout 2017-22, trusted rows unless noted.")
    say("Recalibration fits (each on earlier seasons only):", json.dumps(fits))
    H0, H1 = P0[P0.season.isin(HOLDOUT)], P1[P1.season.isin(HOLDOUT)]
    H1 = H1.assign(p_blend=0.55 * H1.p_home_win_open + 0.45 * H1.nv_open)
    H0 = H0.assign(p_blend=0.55 * H0.p_home_win_open + 0.45 * H0.nv_open)

    say("\n1. Accuracy on every holdout game (moneyline, home win): log loss / Brier; lower is better")
    for lab, P, c in (("opener (no-vig)", H1, "nv_open"), ("closer (no-vig)", H1, "nv_close"), ("G0 no goalies", H0, "p_home_win_open"),
                      ("G1 expected goalie", H1, "p_home_win_open"), ("G1 confirmed goalie (after the open)", H1, "p_home_win"),
                      ("G1 + R1 recal", H1, "p_r1"), ("G1 + R2 dog/fav weight", H1, "p_r2"), ("G1 + R2s shared weight", H1, "p_r2s"),
                      ("G1 + live 55/45 blend", H1, "p_blend")):
        Q = P.dropna(subset=["y", c, "nv_open", "nv_close"])
        by = " ".join(f"{str(s)[2:]}:{ll(x[c], x.y):.4f}" for s, x in Q.groupby("season"))
        say(f"  {lab:40s} logloss {ll(Q[c], Q.y):.4f}  Brier {np.mean((Q[c] - Q.y) ** 2):.4f}  n={len(Q)}  by season {by}")

    say("\n2. Bet rules at the opening price (1 unit). CLV = win-% points the de-vigged line moved toward the bet by the close.")
    B = {}
    spec = [("G0 ML plain EV6", H0, "p_home_win_open", .06, False), ("G1 ML plain EV6", H1, "p_home_win_open", .06, False),
            ("G1+R1 ML plain EV6", H1, "p_r1", .06, False),
            ("G0 ML blend55 EV4 noB2B", H0, "p_blend", .04, True), ("G1 ML blend55 EV4 noB2B", H1, "p_blend", .04, True),
            ("G1+R2s ML blend EV4 noB2B", H1, "p_r2s", .04, True), ("G1+R2 ML blend EV4 noB2B", H1, "p_r2", .04, True)]
    for tr in (True, False):
        say(f"  -- {'trusted rows (headline)' if tr else 'all rows'}")
        for name, P, c, thr, sk in spec:
            b = bets(P, c, thr, sk, name)
            if tr: b = b[b.trusted == 1]
            B[(name, tr)] = b
            lo, hi = boot_days(b, lambda x: x.profit.mean()); clo, chi = boot_days(b, lambda x: x.clv.mean())
            ls = b[(b.price >= 150) & (b.price < 250)]
            bys = " ".join(f"{str(s)[2:]}:{x.profit.sum():+.0f}" for s, x in b.groupby("season"))
            say(f"  {name:28s} {len(b):5d} bets {np.mean(b.profit > 0):.1%} {b.profit.sum():+7.1f}u ROI {b.profit.mean():+.1%} [{lo:+.1%},{hi:+.1%}]"
                f"  CLV {b.clv.mean():+.2f} [{clo:+.2f},{chi:+.2f}]  +150..+249: n={len(ls)} said {ls.p.mean():.1%} won {ls.win.mean():.1%}  by season {bys}")
    pd.concat([b.assign(trusted_only=k[1]) for k, b in B.items()]).to_csv(os.path.join(W, "backtests", "goalie_recal_bets.csv"), index=False)

    say("\n3. Pre-registered decisions (trusted rows; paired CLV difference, 90% interval resampling game days)")
    def dec_line(lab, a, bname, extra=""):
        d, lo, hi = paired_clv(B[(a, True)], B[(bname, True)])
        return d, lo, hi, f"  {lab}: CLV {bname} minus {a} = {d:+.2f} [{lo:+.2f},{hi:+.2f}] {extra}"
    d, lo, hi, t = dec_line("Goalies help?", "G0 ML blend55 EV4 noB2B", "G1 ML blend55 EV4 noB2B"); say(t)
    say(f"    -> {'YES (interval excludes 0)' if lo > 0 else 'NOT SHOWN'}")
    Hq = H1.dropna(subset=["y", "p_home_win_open", "p_r1", "p_r2", "p_r2s"])
    for lab, a, bname, ca, cb in (("R1 improves plain?", "G1 ML plain EV6", "G1+R1 ML plain EV6", "p_home_win_open", "p_r1"),
                                  ("R2 improves blend?", "G1+R2s ML blend EV4 noB2B", "G1+R2 ML blend EV4 noB2B", "p_r2s", "p_r2")):
        d, lo, hi, t = dec_line(lab, a, bname); lla, llb = ll(Hq[ca], Hq.y), ll(Hq[cb], Hq.y)
        say(t + f"; log loss {lla:.4f} -> {llb:.4f}")
        say(f"    -> {'IMPROVES' if lo > 0 and llb < lla else 'NOT SHOWN'}")
    say("  Confirmed edge (CLV > 0 and 90% ROI interval excludes 0):")
    for name, *_ in spec:
        b = B[(name, True)]; lo, hi = boot_days(b, lambda x: x.profit.mean())
        say(f"    {name:28s} CLV {b.clv.mean():+.2f}, ROI {b.profit.mean():+.1%} [{lo:+.1%},{hi:+.1%}] -> {'CONFIRMED' if b.clv.mean() > 0 and lo > 0 else 'not confirmed'}")

    say("\n4. Overs at the opening total, EV 6%+ (rebuilt over price), trusted rows: G0 vs G1")
    for lab, P in (("G0", P0), ("G1", P1)):
        o = overs(P[P.season.isin(HOLDOUT)]); o = o[o.trusted == 1]
        lo, hi = boot_days(o.assign(date=o.date), lambda x: x.profit.mean())
        say(f"  {lab}: {len(o)} bets {np.mean(o.profit > 0):.1%} {o.profit.sum():+.1f}u ROI {o.profit.mean():+.1%} [{lo:+.1%},{hi:+.1%}]  "
            f"total rose {np.mean(o.move > 0):.1%} fell {np.mean(o.move < 0):.1%}")
    open(os.path.join(W, "backtests", "goalie_recal_output.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    cmd = sys.argv[2]
    if cmd == "build": build()
    elif cmd == "predict": predict(sys.argv[3], [int(x) for x in sys.argv[4:]] or PIPELINE + HOLDOUT)
    else: score()
