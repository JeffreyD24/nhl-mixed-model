"""
Spreads plan step 1 (NHL): grade the live moneyline / puck line rules (v4 and v3.1) at DraftKings' opener, 2021-22..2025-26, with
opener-time information (lag 1) and with one night of look-ahead (lag 0). Pre-registration: research/spreads/STEP1_NHL_PREREG.md.

  python research/spreads/step1_nhl.py . > research/spreads/step1_nhl_output.txt
Inputs: research/spreads/nhl_holdout/dk_holdout_lag{0,1}_{season}.csv (built by step1_nhl_build.py),
        research/spreads/inputs/travel_nhl_games.csv, state/alerts.csv.
"""
import os, sys
import numpy as np, pandas as pd

W = os.path.abspath(sys.argv[1]); HO = os.path.join(W, "research", "spreads", "nhl_holdout")
SEASONS = (2022, 2023, 2024, 2025, 2026)
ML_BLEND, ML_THR, PL_THR_V4, PL_THR_V31 = 0.55, 0.04, 0.09, 0.06
W_AWAY_B2B, W_HOME_B2B, W_WEST = 0.0253, -0.0307, -0.0226
RNG = np.random.default_rng(20261104); NBOOT = 2000


def dec(o):
    o = np.asarray(o, float); return np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))


def nv(a, b):
    ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)


def load(lag):
    H = pd.concat([pd.read_csv(os.path.join(HO, f"dk_holdout_lag{lag}_{s}.csv")) for s in SEASONS], ignore_index=True)
    TN = pd.read_csv(os.path.join(W, "research", "spreads", "inputs", "travel_nhl_games.csv"))[["date", "home", "away", "h_rest", "a_rest", "a_tz_move"]]
    H = H.merge(TN, on=["date", "home", "away"], how="left")
    H = H[H.open_home_ml.notna() & H.home_goals.notna() & H.p_home_win_open.notna()].reset_index(drop=True)
    ab = ((H.a_rest == 1) & (H.h_rest > 1)).astype(float); hb = ((H.h_rest == 1) & (H.a_rest > 1)).astype(float)
    west = (-H.a_tz_move).clip(lower=0).fillna(0)
    H["p0"] = (H.p_home_win_open + W_AWAY_B2B * ab + W_HOME_B2B * hb + W_WEST * west).clip(0.02, 0.98)
    H["mkt_open"] = nv(H.open_home_ml, H.open_away_ml); H["mkt_close"] = nv(H.close_home_ml, H.close_away_ml)
    H["pml"] = ML_BLEND * H.p0 + (1 - ML_BLEND) * H.mkt_open
    H["b2b_h"] = H.h_rest == 1; H["b2b_a"] = H.a_rest == 1
    return H


def ml_bets(H):
    hw = (H.home_goals > H.away_goals).values; p = H.pml.values
    dh, da = dec(H.open_home_ml), dec(H.open_away_ml); evh, eva = p * dh - 1, (1 - p) * da - 1
    home = evh >= eva; d = np.where(home, dh, da); win = np.where(home, hw, ~hw)
    po = np.where(home, H.mkt_open, 1 - H.mkt_open); pc = np.where(home, H.mkt_close, 1 - H.mkt_close)
    return pd.DataFrame(dict(season=H.season, date=H.date, home_team=H.home, away_team=H.away, market="ML", home=home,
                             team=np.where(home, H.home, H.away), price=np.where(home, H.open_home_ml, H.open_away_ml),
                             ev=np.where(home, evh, eva), dec=d, win=win, u=np.where(win, d - 1, -1.0),
                             clv=d * pc - 1, clv_pts=pc - po, b2b=np.where(home, H.b2b_h, H.b2b_a)))


def pl_bets(H):
    margin = (H.home_goals - H.away_goals).values; hpt = H.open_home_pl.values.astype(float)
    pc_ = np.where(hpt < 0, H.p_home_by2_open, 1 - H.p_away_by2_open)
    dh, da = dec(H.open_home_pl_odds), dec(H.open_away_pl_odds); evh, eva = pc_ * dh - 1, (1 - pc_) * da - 1
    home = evh >= eva; d = np.where(home, dh, da)
    cov = np.where(hpt < 0, margin >= 2, margin >= -1); win = np.where(home, cov, ~cov)
    same = H.close_home_pl.values == hpt
    nvo = nv(H.open_home_pl_odds, H.open_away_pl_odds); nvc = nv(H.close_home_pl_odds, H.close_away_pl_odds)
    po = np.where(home, nvo, 1 - nvo); pcl = np.where(same, np.where(home, nvc, 1 - nvc), np.nan)
    pt = np.where(home, hpt, -hpt)
    return pd.DataFrame(dict(season=H.season, date=H.date, home_team=H.home, away_team=H.away, market="PL", home=home,
                             team=np.where(home, H.home, H.away), price=np.where(home, H.open_home_pl_odds, H.open_away_pl_odds),
                             point=pt, ev=np.where(home, evh, eva), dec=d, win=win, u=np.where(win, d - 1, -1.0),
                             clv=d * pcl - 1, clv_pts=pcl - po, b2b=np.where(home, H.b2b_h, H.b2b_a),
                             ok_pl=np.abs(hpt) == 1.5))   # fix after Fable review: -2.5 lines were priced/graded as -1.5


def select(H, ver):
    M, P = ml_bets(H), pl_bets(H)
    mq = M.ev.notna() & (M.ev >= ML_THR); pthr = PL_THR_V4 if ver == "v4" else PL_THR_V31
    pq = P.ok_pl & P.ev.notna() & (P.ev >= pthr) & ~P.b2b
    if ver == "v3.1": mq &= ~M.b2b
    both = mq & pq & (M.home.values == P.home.values)
    if ver == "v4": pq &= ~both
    else:
        ml_wins = M.ev.values > P.ev.values
        mq &= ~(both & ~ml_wins); pq &= ~(both & ml_wins)
    return M[mq.values], P[pq.values], P


def boot(x, f=np.mean):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 5: return (np.nan, np.nan)
    idx = RNG.integers(0, len(x), (NBOOT, len(x))); v = f(x[idx], axis=1) if f is np.mean else np.array([f(r) for r in x[idx]])
    return tuple(np.percentile(v, [5, 95]))


def line(label, B, full=True):
    n = len(B)
    if n == 0: print(f"  {label:44s}     0 bets"); return
    u = B.u.values; c = B.clv.values; cn = np.isnan(c).sum()
    lo, hi = boot(u * 100); clo, chi = boot(c * 100)
    per = [B.u[B.season == s].sum() for s in SEASONS]
    s = (f"  {label:44s} {n:5d} bets {B.win.mean():5.1%} {u.sum():+7.1f}u  {u.mean() * 100:+5.1f}/100 [{lo:+5.1f},{hi:+5.1f}]"
         f"  CLV {np.nanmean(c) * 100:+5.2f}% [{clo:+5.2f},{chi:+5.2f}] pts {np.nanmean(B.clv_pts) * 100:+5.2f} beat {np.nanmean(c[~np.isnan(c)] > 0):4.0%}")
    if cn: s += f" (CLV n/a {cn})"
    print(s)
    if full:
        print(f"  {'':44s} by season " + " ".join(f"{x:+6.1f}" for x in per) + f"  neg {sum(x < 0 for x in per)}/5   CLV by season "
              + " ".join(f"{np.nanmean(B.clv[B.season == s_]) * 100:+5.2f}" for s_ in SEASONS))


def hdr(t): print("\n" + "=" * 150 + "\n" + t + "\n" + "-" * 150)


def ll(y, p): p = np.clip(p, 1e-6, 1 - 1e-6); return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


out_rows = []
HS = {lag: load(lag) for lag in (1, 0)}
H = HS[1]
print(f"Games with DK opener + lag-1 prediction: {len(H)} ({', '.join(f'{s}: {(H.season == s).sum()}' for s in SEASONS)}); "
      f"lag 0: {len(HS[0])}")

hdr("0. OPENER TIMING (is lag 1 = results through two days before honest?)")
t0 = pd.to_datetime(H.t0, utc=True).dt.tz_convert("America/New_York"); gd = pd.to_datetime(H.date)
day_before = (t0.dt.normalize().dt.tz_localize(None) == gd - pd.Timedelta(days=1))
print(f"  opener posted 2+ days before: {(t0.dt.normalize().dt.tz_localize(None) < gd - pd.Timedelta(days=1)).mean():.1%}; "
      f"day before before 7 PM ET: {(day_before & (t0.dt.hour < 19)).mean():.1%}; day before 7 PM or later: {(day_before & (t0.dt.hour >= 19)).mean():.1%}; "
      f"game day: {(t0.dt.normalize().dt.tz_localize(None) == gd).mean():.1%}")
hrs = (pd.to_datetime(H.tip, utc=True) - pd.to_datetime(H.t0, utc=True)).dt.total_seconds() / 3600
print(f"  hours from opener snapshot to puck drop: median {hrs.median():.1f}, 10th pct {hrs.quantile(.1):.1f}, 90th {hrs.quantile(.9):.1f}")

for lag in (1, 0):
    for ver in ("v4", "v3.1"):
        M, P, _ = select(HS[lag], ver)
        hdr(f"{'1' if ver == 'v4' else '2'}{'' if lag == 1 else 'b'}. {ver} at DK opener, lag {lag}" + ("  [PRIMARY]" if (lag, ver) == (1, "v4") else ""))
        line("moneyline", M); line("puck line", P); line("combined", pd.concat([M, P]))
        if lag == 1:
            out_rows += [M.assign(version=ver), P.assign(version=ver)]

hdr("4. v4 BREAKDOWNS (lag 1)")
M, P, Pall = select(H, "v4")
line("ML favorites", M[M.price < 0]); line("ML dogs +100..+149", M[(M.price >= 100) & (M.price < 150)]); line("ML +150 and longer", M[M.price >= 150])
line("ML home", M[M.home]); line("ML away", M[~M.home])
line("ML on b2b team (blocked in v3.1)", M[M.b2b])
line("PL favorite -1.5", P[P.point < 0]); line("PL underdog +1.5", P[P.point > 0])
band = Pall[Pall.ok_pl & (Pall.ev >= PL_THR_V31) & (Pall.ev < PL_THR_V4) & ~Pall.b2b]
line("PL EV 6-9% band (TEST rows live)", band)
for lo_, hi_ in ((0.04, 0.06), (0.06, 0.09), (0.09, 0.15), (0.15, 9)):
    line(f"ML EV {lo_:.0%}-{hi_ if hi_ < 9 else 'up':}", M[(M.ev >= lo_) & (M.ev < hi_)], full=False)

hdr("3. ACCURACY: home-win probability (same games), log loss / Brier")
y = (H.home_goals > H.away_goals).astype(float).values; ok = H.mkt_close.notna().values
for nm_, p in (("raw shot model", H.p_home_win_open), ("model + travel", H.p0), ("live blend 0.55", H.pml),
               ("DK no-vig opener", H.mkt_open), ("DK no-vig close", H.mkt_close)):
    p = np.asarray(p, float)[ok]; print(f"  {nm_:20s} log loss {ll(y[ok], p):.4f}  Brier {np.mean((p - y[ok]) ** 2):.4f}")
H0 = HS[0]; y0 = (H0.home_goals > H0.away_goals).astype(float).values; ok0 = H0.mkt_close.notna().values
print(f"  {'lag-0 blend':20s} log loss {ll(y0[ok0], H0.pml.values[ok0]):.4f}  (lag-0 games {ok0.sum()})")

hdr("6. LIVE 2026-27 SO FAR (state/alerts.csv; descriptive only)")
A = pd.read_csv(os.path.join(W, "state", "alerts.csv"))
A = A[A.market.isin(["moneyline", "puck line"]) & A.skipped.isna() & A.profit.notna()]
for mk in ("moneyline", "puck line"):
    a = A[A.market == mk]
    print(f"  {mk:10s} {len(a):3d} graded bets  {a.profit.sum():+6.1f}u  mean CLV field {pd.to_numeric(a.clv, errors='coerce').mean():+.3f}")

pd.concat(out_rows).to_csv(os.path.join(W, "research", "spreads", "step1_nhl_bets.csv"), index=False)
