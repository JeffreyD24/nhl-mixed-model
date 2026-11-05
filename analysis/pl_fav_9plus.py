"""
Are -1.5 puck lines at EV 9%+ weaker than the DK record says? Pre-registered in research/spreads/PL_FAV_9PLUS_PREREG.md (Nov 5, 2026).
Analysis only: nothing here is imported by the live code.

  python analysis/pl_fav_9plus.py WORK > analysis/pl_fav_9plus_output.txt

Rebuilds SBR's opening puck line price from SBR's opening moneyline with a mapping fit on SBR's own closing lines (home and road
favorites separately, leave-one-season-out), then grades the goalie-aware shot model's puck line bets 2014-15..2020-21 at it.
Uses the saved predictions in derived/ (gr_G1_pred_2015..2021).
"""
import os, sys
import numpy as np, pandas as pd

WORK = os.path.abspath(sys.argv[1]); sys.path.insert(0, WORK)
import derived                                   # saved build products (derived/MANIFEST.md)
OLD = (2015, 2016, 2017, 2018, 2019, 2020, 2021)
_miss = derived.ensure(WORK, [f"gr_G1_pred_{s}.csv" for s in OLD])
if _miss: sys.exit(f"missing saved build products {_miss}")
TMP = os.path.join(WORK, "_tmp")
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def novig(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)
to_amer = lambda d: np.where(d >= 2, (d - 1) * 100, -100 / (d - 1))

P = pd.concat([pd.read_csv(os.path.join(TMP, f"gr_G1_pred_{s}.csv")).assign(season=s) for s in OLD], ignore_index=True)
P = P[P.home_goals.notna() & P.p_home_win_open.notna()].reset_index(drop=True)
SEA = P.season.values

# ---------------------------------------------------------------- mapping from SBR closing lines (both ML and puck line stored)
ph_c = novig(P.close_home_ml, P.close_away_ml); hfav_c = ph_c >= 0.5; f_c = np.maximum(ph_c, 1 - ph_c)
fit_ok = ((P.close_ml_ok == 1) & (P.ml_move_ok == 1) & (np.abs(P.close_home_pl) == 1.5) & ((P.close_home_pl < 0) == hfav_c)
          & P.close_home_pl_odds.notna() & P.close_away_pl_odds.notna()).values
fav_ip = np.where(hfav_c, 1 / dec(P.close_home_pl_odds), 1 / dec(P.close_away_pl_odds))   # implied prob, favorite at -1.5
dog_ip = np.where(hfav_c, 1 / dec(P.close_away_pl_odds), 1 / dec(P.close_home_pl_odds))   # implied prob, underdog at +1.5


def fits(train):
    out = {}
    for hf in (True, False):
        m = train & fit_ok & (hfav_c == hf)
        out[hf] = (np.polyfit(f_c[m], fav_ip[m], 3), np.polyfit(f_c[m], dog_ip[m], 3), int(m.sum()))
    return out


def rebuild(f, hf, F):
    """implied probs (favorite -1.5, underdog +1.5) for each game from the fitted mapping F"""
    fav = np.where(hf, np.polyval(F[True][0], f), np.polyval(F[False][0], f))
    dog = np.where(hf, np.polyval(F[True][1], f), np.polyval(F[False][1], f))
    return fav, dog


# held-out error of the mapping on closing lines (each season rebuilt from the other six)
print("Mapping: SBR closing moneyline -> SBR closing puck line, home and road favorites fit separately, leave-one-season-out")
eh, ea = [], []
for s in OLD:
    F = fits(SEA != s); te = (SEA == s) & fit_ok
    fv, dg = rebuild(f_c, hfav_c, F)
    reb_h = np.where(hfav_c, fv, dg); reb_a = np.where(hfav_c, dg, fv)
    real_h = 1 / dec(P.close_home_pl_odds); real_a = 1 / dec(P.close_away_pl_odds)
    eh.append((reb_h - real_h)[te]); ea.append((reb_a - real_a)[te])
eh, ea = np.concatenate(eh), np.concatenate(ea)
print(f"  held-out error, rebuilt minus real implied prob: home side mean {eh.mean():+.4f} sd {eh.std():.4f}; "
      f"road side mean {ea.mean():+.4f} sd {ea.std():.4f}  ({len(eh)} games)")
print("  (previous T3 mapping fit on DK openers: home mean +0.0147 sd 0.0326; road mean -0.0101 sd 0.0323)")

# ---------------------------------------------------------------- rebuild opening puck lines, LOSO
ph_o = novig(P.open_home_ml, P.open_away_ml); hfav_o = ph_o >= 0.5; f_o = np.maximum(ph_o, 1 - ph_o)
oko = ((P.open_ml_ok == 1) & (P.ml_move_ok == 1) & P.open_home_ml.notna() & P.open_away_ml.notna()).values
reb_fav, reb_dog = np.full(len(P), np.nan), np.full(len(P), np.nan)
for s in OLD:
    F = fits(SEA != s); m = SEA == s
    fv, dg = rebuild(f_o, hfav_o, F); reb_fav[m], reb_dog[m] = fv[m], dg[m]
hpt = np.where(oko, np.where(hfav_o, -1.5, 1.5), np.nan)
h_odds = to_amer(1 / np.where(hfav_o, reb_fav, reb_dog)); a_odds = to_amer(1 / np.where(hfav_o, reb_dog, reb_fav))

# ---------------------------------------------------------------- bets (same rules as pl_side_bars.py T3)
margin = (P.home_goals - P.away_goals).values
pc = np.where(hpt < 0, P.p_home_by2_open, 1 - P.p_away_by2_open)
dh, da = dec(h_odds), dec(a_odds); evh, eva = pc * dh - 1, (1 - pc) * da - 1
home = evh >= eva; ev = np.where(home, evh, eva); d = np.where(home, dh, da)
cov = np.where(hpt < 0, margin >= 2, margin >= -1); win = np.where(home, cov, ~cov); u = np.where(win, d - 1, -1.0)
fav = np.where(home, hpt < 0, hpt > 0); b2b = np.where(home, P.b2b_home, P.b2b_away).astype(bool)
ok = ~np.isnan(ev) & ~np.isnan(hpt) & ~b2b
B = pd.DataFrame(dict(season=SEA, date=P.date, ev=ev, u=u, win=win, fav=fav, price=to_amer(d)))[ok].reset_index(drop=True)


def line(lab, X):
    n = len(X); uu = X.u.sum(); per = [X.u[X.season == s].sum() for s in OLD]
    return (f"  {lab:24s} {n:5d} bets  {X.win.mean() if n else 0:5.1%}  {uu:+7.1f}u  ({uu / max(n, 1):+6.1%})  avg price {np.median(X.price) if n else 0:+5.0f} | "
            + " ".join(f"{x:+6.1f}" for x in per) + f"  neg {sum(x < 0 for x in per)}/7")


print(f"\nBets at the rebuilt opening puck line, 2014-15..2020-21, shot model with goalies, b2b removed ({len(B)} games with a side)")
print("  " + " " * 24 + "  bets   win%     units      ROI   (median price)   | by season " + " ".join(f"{s:>6d}" for s in OLD))
for side, m in (("-1.5", B.fav), ("+1.5", ~B.fav)):
    for lo, hi in ((0.04, 0.06), (0.06, 0.09), (0.09, 0.12), (0.12, 9), (0.09, 9)):
        lab = f"{side} EV {lo:.0%}-{hi:.0%}" if hi < 9 else f"{side} EV {lo:.0%}+"
        print(line(lab, B[m & (B.ev >= lo) & (B.ev < hi)]))

# ---------------------------------------------------------------- bootstrap and decision for -1.5 at 9%+
X = B[B.fav & (B.ev >= 0.09)]
days = X.date.unique(); rng = np.random.default_rng(7); by_day = X.groupby("date").u.agg(["sum", "count"])
rois = []
for _ in range(2000):
    pick = by_day.loc[rng.choice(days, len(days))]; rois.append(pick["sum"].sum() / pick["count"].sum())
lo, hi = np.percentile(rois, [5, 95])
roi = X.u.sum() / max(len(X), 1); neg = sum(X.u[X.season == s].sum() < 0 for s in OLD)
print(f"\n-1.5 at EV 9%+: {len(X)} bets, ROI {roi:+.1%}, 90% interval {lo:+.1%} to {hi:+.1%}, negative in {neg}/7 seasons")
print("  (DK openers 2021-26, same rule: 569 bets, +11.8%)")
verdict = "LEAD CONFIRMED" if (roi < 0 and neg >= 4) else ("LEAD REJECTED" if roi >= 0.03 else "INCONCLUSIVE")
print(f"Decision rule (pre-registered): {verdict}")
