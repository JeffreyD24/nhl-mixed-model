"""
Separate EV bars for -1.5 and +1.5 puck lines: tests T1-T3 pre-registered in research/spreads/PL_SIDE_BARS_PREREG.md (Nov 5, 2026).
Analysis only: nothing here is imported by the live code.

  python dev/oos_sbr_build.py WORK && python dev/goalie_recal_test.py WORK build \
      && python dev/goalie_recal_test.py WORK predict G1 2015 2016 2017 2018 2019 2020 2021      (older-season predictions)
  python analysis/pl_ev_bands.py WORK --build                                                    (DK 2021-26 predictions)
  python analysis/pl_side_bars.py WORK > analysis/pl_side_bars_output.txt

T1  leave-one-season-out on DK openers 2021-22..2025-26 (shared bar vs one bar per side, grid 4-12%)
T2  older seasons 2014-15..2020-21 (END-year 2015-2021) at SBR CLOSING puck lines, goalie-aware shot model (G1)
T3  same seasons at an APPROXIMATE opening puck line price rebuilt from SBR's opening moneyline (mapping fit on DK openers 2021-26)
"""
import os, sys, json
import numpy as np, pandas as pd

WORK = os.path.abspath(sys.argv[1]); TMP = os.path.join(WORK, "_tmp")
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def novig(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)
GRID = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12]


def pl_rows(hpt, hodds, aodds, pby2_h, pby2_a, margin, b2b_h, b2b_a, season):
    """better-EV side per game at a +/-1.5 puck line. fav = our side is the -1.5 side"""
    hpt = np.asarray(hpt, float)
    pc = np.where(hpt < 0, pby2_h, 1 - np.asarray(pby2_a, float))           # chance the HOME side covers its line
    dh, da = dec(hodds), dec(aodds); evh, eva = pc * dh - 1, (1 - pc) * da - 1
    home = evh >= eva; ev = np.where(home, evh, eva); d = np.where(home, dh, da)
    cov = np.where(hpt < 0, margin >= 2, margin >= -1); win = np.where(home, cov, ~cov)
    u = np.where(win, d - 1, -1.0)
    fav = np.where(home, hpt < 0, hpt > 0)
    b2b = np.where(home, b2b_h, b2b_a).astype(bool)
    ok = ~np.isnan(ev) & (np.abs(hpt) == 1.5) & ~b2b & ~np.isnan(np.asarray(margin, float))
    return pd.DataFrame(dict(season=season, ev=ev, u=u, win=win, fav=fav, price=d))[ok].reset_index(drop=True)


def line(lab, B, seasons):
    n = len(B); uu = B.u.sum(); per = [B.u[B.season == s].sum() for s in seasons]
    return (f"  {lab:40s} {n:5d} bets  {B.win.mean() if n else 0:5.1%}  {uu:+7.1f}u  ({uu / max(n, 1):+6.1%})  | "
            + " ".join(f"{x:+6.1f}" for x in per) + f"  neg {sum(x < 0 for x in per)}/{len(seasons)}")


def bands(B, seasons, title):
    print(f"\n{title}\n  " + " " * 40 + " bets   win%     units      ROI    | by season " + " ".join(f"{s:>6d}" for s in seasons))
    for side_lab, m in (("-1.5", B.fav), ("+1.5", ~B.fav)):
        for lo, hi in ((0.04, 0.06), (0.06, 0.09), (0.09, 9)):
            lab = f"{side_lab} EV {lo:.0%}-{hi:.0%}" if hi < 9 else f"{side_lab} EV {lo:.0%}+"
            print(line(lab, B[m & (B.ev >= lo) & (B.ev < hi)], seasons))


sys.path.insert(0, WORK)
import derived                                   # saved build products (derived/MANIFEST.md)
_miss = derived.ensure(WORK, [f"dk_holdout_{s}.csv" for s in (2022, 2023, 2024, 2025, 2026)] + [f"gr_G1_{k}_{s}.{e}" for s in range(2015, 2022) for k, e in (("pred", "csv"), ("meta", "json"))])
if _miss and '--build' not in sys.argv: sys.exit(f'missing saved build products {_miss}: build them, then python derived.py . --save')
# ================================================================ T1: leave-one-season-out on DK openers 2021-26
DKS = (2022, 2023, 2024, 2025, 2026)
H = pd.concat([pd.read_csv(os.path.join(TMP, f"dk_holdout_{s}.csv")) for s in DKS], ignore_index=True)
H = H[H.open_home_ml.notna() & H.home_goals.notna() & H.p_home_win_open.notna()].reset_index(drop=True)
G = pd.read_csv(os.path.join(WORK, "data", "games_hist.csv"))
L = pd.concat([G[["date", "home"]].rename(columns={"home": "team"}), G[["date", "away"]].rename(columns={"away": "team"})])
L["date"] = pd.to_datetime(L.date); L = L.drop_duplicates().sort_values(["team", "date"])
L["rest"] = L.groupby("team").date.diff().dt.days; L["date"] = L.date.dt.strftime("%Y-%m-%d")
R = L.set_index(["date", "team"]).rest
b2bh = R.reindex(list(zip(H.date, H.home))).values == 1; b2ba = R.reindex(list(zip(H.date, H.away))).values == 1
DK = pl_rows(H.open_home_pl, H.open_home_pl_odds, H.open_away_pl_odds, H.p_home_by2_open, H.p_away_by2_open,
             (H.home_goals - H.away_goals).values, b2bh, b2ba, H.season.values)

print("T1. Leave-one-season-out, DK openers 2021-22..2025-26 (shot model, +/-1.5, b2b removed)")
print("    bar chosen on the other 4 seasons by max units from {4..12}%, then graded on the held-out season")
print(f"  {'held out':>8s}  {'shared bar':>10s} {'units':>7s} {'bets':>5s}   {'-1.5 bar':>8s} {'+1.5 bar':>8s} {'units':>7s} {'bets':>5s}   per-side better?")
tot_sh = tot_ps = 0.0; wins = 0; picks = []
for s in DKS:
    tr, te = DK[DK.season != s], DK[DK.season == s]
    units = lambda D, t: D.u[D.ev >= t].sum()
    t_sh = max(GRID, key=lambda t: units(tr, t))
    t_f = max(GRID, key=lambda t: units(tr[tr.fav], t)); t_d = max(GRID, key=lambda t: units(tr[~tr.fav], t))
    u_sh, n_sh = units(te, t_sh), int((te.ev >= t_sh).sum())
    u_ps = units(te[te.fav], t_f) + units(te[~te.fav], t_d); n_ps = int((te.fav & (te.ev >= t_f)).sum() + (~te.fav & (te.ev >= t_d)).sum())
    tot_sh += u_sh; tot_ps += u_ps; wins += u_ps > u_sh; picks.append(t_d)
    print(f"  {s:>8d}  {t_sh:>10.0%} {u_sh:+7.1f} {n_sh:5d}   {t_f:>8.0%} {t_d:>8.0%} {u_ps:+7.1f} {n_ps:5d}   {'yes' if u_ps > u_sh else 'no'}")
print(f"  {'total':>8s}  {'':>10s} {tot_sh:+7.1f}         {'':>8s} {'':>8s} {tot_ps:+7.1f}         per-side better in {wins}/5 folds")
print(f"  +1.5 bar picked per fold: {', '.join(f'{x:.0%}' for x in picks)}")
T1_pass = tot_ps > tot_sh and wins >= 3
bands(DK, DKS, "T1 context: the same DK seasons by side and band (in-sample, from pl_ev_bands)")

# ================================================================ older seasons (G1: shot model with goalies)
OLD = (2015, 2016, 2017, 2018, 2019, 2020, 2021)
P = pd.concat([pd.read_csv(os.path.join(TMP, f"gr_G1_pred_{s}.csv")).assign(season=s) for s in OLD], ignore_index=True)
P = P[P.home_goals.notna() & P.p_home_win_open.notna()].reset_index(drop=True)
P["ml_move_ok"] = P.get("ml_move_ok", 1)
mg = (P.home_goals - P.away_goals).values
print(f"\nOlder seasons: {len(P)} games with predictions, END-year {OLD[0]}-{OLD[-1]} (2014-15..2020-21)")

# ---------------------------------------------------------------- T2: SBR closing puck lines
okc = (P.close_ml_ok == 1) & (P.ml_move_ok == 1)
T2 = pl_rows(np.where(okc, P.close_home_pl, np.nan), P.close_home_pl_odds, P.close_away_pl_odds, P.p_home_by2_open, P.p_away_by2_open,
             mg, P.b2b_home.values, P.b2b_away.values, P.season.values)
bands(T2, OLD, "T2. Older seasons at SBR CLOSING puck lines (supporting only; closing prices are not where we bet)")

# ---------------------------------------------------------------- T3: approximate opening puck line from the opening moneyline
# mapping: favorite's no-vig win chance -> DK decimal price of the favorite at -1.5 and the underdog at +1.5 (DK openers 2021-26,
# rows where the -1.5 side is the moneyline favorite). Cubic polynomial in the favorite's chance, on implied probability.
f_dk = np.maximum(novig(H.open_home_ml, H.open_away_ml), 1 - novig(H.open_home_ml, H.open_away_ml))
hfav = novig(H.open_home_ml, H.open_away_ml) >= 0.5
m = (np.abs(H.open_home_pl) == 1.5) & ((H.open_home_pl < 0) == hfav) & H.open_home_pl_odds.notna()
fav_odds = np.where(hfav, H.open_home_pl_odds, H.open_away_pl_odds); dog_odds = np.where(hfav, H.open_away_pl_odds, H.open_home_pl_odds)
cf = np.polyfit(f_dk[m], 1 / dec(fav_odds[m]), 3); cd = np.polyfit(f_dk[m], 1 / dec(dog_odds[m]), 3)
to_amer = lambda d: np.where(d >= 2, (d - 1) * 100, -100 / (d - 1))
def rebuild(hml, aml):
    ph = novig(hml, aml); f = np.maximum(ph, 1 - ph); hf = ph >= 0.5
    fo, do_ = to_amer(1 / np.polyval(cf, f)), to_amer(1 / np.polyval(cd, f))
    return np.where(hf, -1.5, 1.5), np.where(hf, fo, do_), np.where(hf, do_, fo)
res = 1 / dec(fav_odds[m]) - np.polyval(cf, f_dk[m])
print(f"\nT3 mapping, fit on {m.sum()} DK openers: favorite -1.5 implied prob residual sd {res.std():.4f} (in-sample)")
# validation: rebuild SBR CLOSING puck line prices from SBR CLOSING moneylines and compare with the real ones
vh, vho, vao = rebuild(P.close_home_ml, P.close_away_ml)
vm = okc & (np.abs(P.close_home_pl) == 1.5) & (np.sign(P.close_home_pl) == np.sign(vh)) & P.close_home_pl_odds.notna()
err_h = (1 / dec(vho[vm]) - 1 / dec(P.close_home_pl_odds[vm]))
err_a = (1 / dec(vao[vm]) - 1 / dec(P.close_away_pl_odds[vm]))
print(f"T3 validation on {vm.sum()} SBR closing lines: rebuilt minus real implied prob, home side mean {err_h.mean():+.4f} sd {err_h.std():.4f}; "
      f"away side mean {err_a.mean():+.4f} sd {err_a.std():.4f}")
print(f"   (SBR's -1.5 side was the moneyline favorite in {(np.sign(P.close_home_pl[okc & P.close_home_pl.notna()]) == np.sign(vh[okc & P.close_home_pl.notna()])).mean():.1%} of games)")
oko = (P.open_ml_ok == 1) & (P.ml_move_ok == 1) & P.open_home_ml.notna()
rh, rho, rao = rebuild(P.open_home_ml, P.open_away_ml)
T3 = pl_rows(np.where(oko, rh, np.nan), rho, rao, P.p_home_by2_open, P.p_away_by2_open, mg, P.b2b_home.values, P.b2b_away.values, P.season.values)
bands(T3, OLD, "T3. Older seasons at an APPROXIMATE opening puck line (rebuilt from SBR's opening moneyline)")

# ---------------------------------------------------------------- decision rule (PL_SIDE_BARS_PREREG.md)
d6 = lambda B, fav: B[(B.fav == fav) & (B.ev >= 0.06) & (B.ev < 0.09)]
t3d, t3f = d6(T3, False), d6(T3, True); t2d, t2f = d6(T2, False), d6(T2, True)
roi = lambda B: B.u.sum() / max(len(B), 1)
c2 = t3d.u.sum() > 0 and sum(t3d.u[t3d.season == s].sum() > 0 for s in OLD) >= 4 and roi(t3d) > roi(t3f)
c3 = roi(t2d) >= roi(t2f)
print("\nDecision rule (pre-registered)")
print(f"  1. T1 per-side bars beat the shared bar in total and in 3+/5 folds: {'PASS' if T1_pass else 'FAIL'} ({tot_ps:+.1f}u vs {tot_sh:+.1f}u, {wins}/5 folds)")
print(f"  2. T3 +1.5 at 6-9%: units > 0, positive in 4+/7 seasons, ROI above -1.5 at 6-9%: {'PASS' if c2 else 'FAIL'} "
      f"({t3d.u.sum():+.1f}u, {sum(t3d.u[t3d.season == s].sum() > 0 for s in OLD)}/7 seasons, ROI {roi(t3d):+.1%} vs {roi(t3f):+.1%})")
print(f"  3. T2 does not contradict (+1.5 6-9% ROI >= -1.5 6-9% ROI at the close): {'PASS' if c3 else 'FAIL'} ({roi(t2d):+.1%} vs {roi(t2f):+.1%})")
print(f"  => H (+1.5 deserves a lower bar) {'SUPPORTED' if (T1_pass and c2 and c3) else 'NOT SUPPORTED'}")
