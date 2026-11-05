"""Rested team vs a back-to-back team (catalog X02), market-only rule.
Usage: python dev/rest_b2b_test.py validate   # reproduce the 2016-22 numbers (no 2011-16 outcomes touched)
       python dev/rest_b2b_test.py run 2012 2016   # the pre-registered test (END-year season labels)
Data: derived/oos_games.csv.gz (hockeyR schedule + SBR lines, END-year season labels; 2012 = 2011-12)."""
import sys, numpy as np, pandas as pd
from scipy import stats
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def novig(a, b):
    pa, pb = 1 / dec(a), 1 / dec(b); return pa / (pa + pb)
def load(path="derived/oos_games.csv.gz"):
    d = pd.read_csv(path); d["date"] = pd.to_datetime(d.date)
    # b2b from the full schedule: team played the previous calendar day (all rows count, odds or not)
    t = pd.concat([d[["game_id", "date", "home"]].rename(columns={"home": "team"}), d[["game_id", "date", "away"]].rename(columns={"away": "team"})])
    played = set(zip(t.team, t.date))
    d["b2b_home"] = [int((h, dt - pd.Timedelta(days=1)) in played) for h, dt in zip(d.home, d.date)]
    d["b2b_away"] = [int((a, dt - pd.Timedelta(days=1)) in played) for a, dt in zip(d.away, d.date)]
    d["trusted"] = ((d.open_ml_ok == 1) & (d.close_ml_ok == 1) & (d.ml_move_ok == 1)).astype(int)
    d["hw"] = (d.home_goals > d.away_goals).astype(int)
    d["nv_open"] = novig(d.open_home_ml, d.open_away_ml); d["nv_close"] = novig(d.close_home_ml, d.close_away_ml)
    return d
def rested(D):
    D = D[(D.trusted == 1) & D.home_goals.notna() & (D.home_goals != D.away_goals)]
    x = D.b2b_home - D.b2b_away; X = D[x != 0].copy(); home = (x[x != 0] < 0).values   # rested side = the team NOT on a b2b
    X["side"] = np.where(home, "home", "away")
    X["win"] = np.where(home, X.hw, 1 - X.hw)
    X["price"] = np.where(home, X.open_home_ml, X.open_away_ml)
    X["q"] = np.where(home, X.nv_open, 1 - X.nv_open); X["qc"] = np.where(home, X.nv_close, 1 - X.nv_close)
    X["profit"] = np.where(X.win == 1, dec(X.price) - 1, -1.0)
    X["res_close"] = X.win - X.qc; X["res_open"] = X.win - X.q; X["move"] = X.qc - X.q
    return X
def report(X, label):
    n = len(X); r = X.res_close
    t = stats.ttest_1samp(r, 0); p1 = t.pvalue / 2 if t.statistic > 0 else 1 - t.pvalue / 2
    se = r.std(ddof=1) / np.sqrt(n)
    print(f"\n== {label}: {n} games ==")
    print(f"won {X.win.mean():.1%} vs no-vig close {X.qc.mean():.1%} vs no-vig open {X.q.mean():.1%}")
    print(f"PRIMARY win - close: {r.mean():+.4f} (SE {se:.4f}, 90% CI [{r.mean()-1.645*se:+.4f}, {r.mean()+1.645*se:+.4f}], one-sided p={p1:.3f})")
    ro = X.res_open; print(f"win - open: {ro.mean():+.4f} | ROI at open {X.profit.mean():+.1%} ({X.profit.sum():+.1f}u) | price move to rested (close-open) {X.move.mean():+.4f}")
    rows = []
    for s, g in X.groupby("season"):
        rows.append((s, len(g), g.win.mean(), g.qc.mean(), g.res_close.mean(), g.profit.mean(), g.move.mean()))
    print(pd.DataFrame(rows, columns=["season_end", "n", "won", "nv_close", "win-close", "ROI_open", "move"]).round(4).to_string(index=False))
    for side, g in X.groupby("side"): print(f"  rested side = {side}: n={len(g)}, win-close {g.res_close.mean():+.4f}, ROI {g.profit.mean():+.1%}")
    return r.mean(), p1, int((X.groupby('season').res_close.mean() > 0).sum()), X.season.nunique()
if __name__ == "__main__":
    d = load()
    if sys.argv[1] == "validate":
        report(rested(d[d.season.between(2017, 2022)]), "VALIDATION 2016-17..2021-22 (known: 1520 games, won 57.7% vs open 54.2%, ROI +2.2%)")
    else:
        a, b = int(sys.argv[2]), int(sys.argv[3]); report(rested(d[d.season.between(a, b)]), f"TEST END-year {a}..{b}")
