"""Follow-ups to the rested-vs-b2b result. Rules: backtests/REST_B2B_FOLLOWUPS_PREREG.md (read it first).
Usage (from the repo root):
  python dev/rest_b2b_followups.py dry   # sample sizes only, no outcomes printed
  python dev/rest_b2b_followups.py run   # both follow-ups, once
Data (already saved, RULE 4): derived/oos_games_g.csv.gz, derived/gr_G1_pred_{2015..2021}.csv.gz."""
import sys, numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from rest_b2b_test import load, rested, novig

lg = lambda p: np.log(np.clip(p, .01, .99) / (1 - np.clip(p, .01, .99)))

def main_starters(d):
    a = d[["season", "home", "home_goalie"]].set_axis(["season", "team", "g"], axis=1)
    b = d[["season", "away", "away_goalie"]].set_axis(["season", "team", "g"], axis=1)
    c = pd.concat([a, b]).dropna().groupby(["season", "team", "g"]).size().reset_index(name="n")
    c = c.sort_values(["season", "team", "n", "g"], ascending=[True, True, False, True]).drop_duplicates(["season", "team"])
    return {(s, t): g for s, t, g in zip(c.season, c.team, c.g)}

def f1_frame(d):
    ms = main_starters(d)
    X = rested(d[d.season.between(2012, 2022)]); hr = (X.side == "home").values
    X["b2b_team"] = np.where(hr, X.away, X.home); X["b2b_goalie"] = np.where(hr, X.away_goalie, X.home_goalie)
    n0 = len(X); X = X.dropna(subset=["b2b_goalie"]).copy()
    X["main"] = [ms.get((s, t)) for s, t in zip(X.season, X.b2b_team)]
    X["grp"] = np.where(X.b2b_goalie == X.main, "STARTER", "BACKUP"); X["period"] = np.where(X.season <= 2016, "A 2012-16", "B 2017-22")
    return X, n0 - len(X)

def line(X):
    n = len(X); r = X.res_close; se = r.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    t = stats.ttest_1samp(r, 0) if n > 2 else None
    p1 = (t.pvalue / 2 if t.statistic > 0 else 1 - t.pvalue / 2) if t is not None else np.nan
    return dict(n=n, won=X.win.mean(), nv_close=X.qc.mean(), gap=r.mean(), se=se, p1=p1, roi_open=X.profit.mean())

def f1(d, dry):
    X, dropped = f1_frame(d)
    print(f"F1 eligible b2b games 2012-22 with a goalie id: {len(X)} (dropped for no goalie id: {dropped})")
    print(X.groupby(["period", "grp"]).size().unstack().to_string()); print("share backup by period:", X.groupby("period").grp.apply(lambda s: (s == "BACKUP").mean()).round(3).to_dict())
    if dry: return
    rows = []
    for (per, g), Y in list(X.groupby(["period", "grp"])) + [(("ALL", g), Y) for g, Y in X.groupby("grp")] + [(("ALL", "ALL"), X)]:
        rows.append(dict(period=per, grp=g, **line(Y)))
    T = pd.DataFrame(rows); print(T.round(4).to_string(index=False))
    S = X[X.grp == "STARTER"]; B = X[X.grp == "BACKUP"]; ls = line(S)
    dif = B.res_close.mean() - S.res_close.mean(); se = np.sqrt(B.res_close.var(ddof=1) / len(B) + S.res_close.var(ddof=1) / len(S))
    print(f"\nD_B - D_S = {dif:+.4f} (90% CI [{dif-1.645*se:+.4f}, {dif+1.645*se:+.4f}])")
    pos = all(line(S[S.period == p])["gap"] > 0 for p in S.period.unique())
    print(f"PRIMARY F1: D_S = {ls['gap']:+.4f} (SE {ls['se']:.4f}), one-sided p = {ls['p1']:.3f}, positive in both periods: {pos}")
    print("VERDICT F1:", "PASS (gap is not only backup starts)" if (ls["gap"] > 0 and ls["p1"] < .05 and pos) else "NOT SHOWN without backups (could be mostly backup starts; not proof)")

def f2(dry):
    d = load("derived/oos_games_g.csv.gz"); b2b = d[["game_id", "b2b_home", "b2b_away"]]
    P = pd.concat([pd.read_csv(f"derived/gr_G1_pred_{s}.csv.gz") for s in range(2015, 2022)], ignore_index=True)
    P = P.drop(columns=["b2b_home", "b2b_away"]).merge(b2b, on="game_id", how="left")
    P["date"] = pd.to_datetime(P.date); P["trusted"] = ((P.open_ml_ok == 1) & (P.close_ml_ok == 1) & (P.ml_move_ok == 1)).astype(int)
    P = P[(P.trusted == 1) & P.home_goals.notna() & (P.home_goals != P.away_goals) & P.p_home_win_open.notna() & P.b2b_home.notna()].copy()
    P["hw"] = (P.home_goals > P.away_goals).astype(int)
    P["nv_open"] = novig(P.open_home_ml, P.open_away_ml); P["nv_close"] = novig(P.close_home_ml, P.close_away_ml)
    P["adv"] = P.b2b_away - P.b2b_home
    E = rested(P); E["pm"] = np.where(E.side == "home", E.p_home_win_open, 1 - E.p_home_win_open)
    print(f"\nF2 all trusted decided games 2015-21: {len(P)}; eligible b2b games: {len(E)}; seasons {sorted(P.season.unique())}")
    if dry: return
    def reg(cols, label):
        X = sm.add_constant(pd.DataFrame({c: f(P) for c, f in cols.items()})); m = sm.Logit(P.hw, X).fit(disp=0)
        z = m.params["adv"] / m.bse["adv"]; p1 = stats.norm.sf(z)
        print(f"{label}: adv coef {m.params['adv']:+.4f} (SE {m.bse['adv']:.4f}), one-sided p = {p1:.3f}; " + ", ".join(f"{k} {m.params[k]:+.3f}" for k in cols if k != "adv"))
        return m.params["adv"], p1
    adv = lambda D: D.adv
    reg({"lo": lambda D: lg(D.nv_open), "adv": adv}, "REFERENCE opener only")
    c, p1 = reg({"lo": lambda D: lg(D.nv_open), "lm": lambda D: lg(D.p_home_win_open), "adv": adv}, "PRIMARY opener + model")
    reg({"lc": lambda D: lg(D.nv_close), "lm": lambda D: lg(D.p_home_win_open), "adv": adv}, "SECONDARY close + model")
    r = lambda x: f"{x.mean():+.4f} (SE {x.std(ddof=1)/np.sqrt(len(x)):.4f})"
    print(f"\nEligible b2b games ({len(E)}), rested side: won {E.win.mean():.1%}; model {E.pm.mean():.1%}; open {E.q.mean():.1%}; close {E.qc.mean():.1%}")
    print("win - model:", r(E.win - E.pm), "| win - open:", r(E.win - E.q), "| win - close:", r(E.win - E.qc), "| model - open:", r(E.pm - E.q))
    print("VERDICT F2:", "PASS: the shot model does NOT already price it" if (c > 0 and p1 < .05) else "PRICED by the model or not distinguishable")

if __name__ == "__main__":
    dry = sys.argv[1] != "run"
    d = load("derived/oos_games_g.csv.gz"); f1(d, dry); f2(dry)
