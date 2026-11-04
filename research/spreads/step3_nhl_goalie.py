"""
NHL step 3: confirmed starting goalies / lineups vs the DraftKings price on game day (pre-registration:
research/spreads/STEP3_NHL_GOALIE_PREREG.md).

  python research/spreads/step3_nhl_goalie.py . NBA_REPO > research/spreads/step3_nhl_goalie_output.txt
"""
import os, sys, glob, json
import numpy as np, pandas as pd

W = os.path.abspath(sys.argv[1]); NBA = os.path.abspath(sys.argv[2])
HO = os.path.join(W, "research", "spreads", "nhl_holdout"); SEASONS = (2022, 2023, 2024, 2025, 2026)
ML_BLEND, ML_THR, PL_THR = 0.55, 0.04, 0.09
W_AWAY_B2B, W_HOME_B2B, W_WEST = 0.0253, -0.0307, -0.0226
RNG = np.random.default_rng(20261104); NBOOT = 2000
NAME = {"Anaheim Ducks": "ana", "Arizona Coyotes": "uta", "Utah Hockey Club": "uta", "Utah Mammoth": "uta", "Boston Bruins": "bos",
        "Buffalo Sabres": "buf", "Carolina Hurricanes": "car", "Columbus Blue Jackets": "cbj", "Calgary Flames": "cgy",
        "Chicago Blackhawks": "chi", "Colorado Avalanche": "col", "Dallas Stars": "dal", "Detroit Red Wings": "det",
        "Edmonton Oilers": "edm", "Florida Panthers": "fla", "Los Angeles Kings": "la", "Minnesota Wild": "min",
        "Montréal Canadiens": "mtl", "Montreal Canadiens": "mtl", "New Jersey Devils": "nj", "Nashville Predators": "nsh",
        "New York Islanders": "nyi", "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
        "Pittsburgh Penguins": "pit", "Seattle Kraken": "sea", "San Jose Sharks": "sj", "St Louis Blues": "stl", "St. Louis Blues": "stl",
        "Tampa Bay Lightning": "tb", "Toronto Maple Leafs": "tor", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk",
        "Winnipeg Jets": "wpg", "Washington Capitals": "wsh"}


def dec(o): o = np.asarray(o, float); return np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
def nv(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)
def logit(p): p = np.clip(p, 1e-4, 1 - 1e-4); return np.log(p / (1 - p))


# ------------------------------------------------------------------ games
H = pd.concat([pd.read_csv(os.path.join(HO, f"dk_holdout_lag1_{s}.csv")) for s in SEASONS], ignore_index=True)
TN = pd.read_csv(os.path.join(W, "research", "spreads", "inputs", "travel_nhl_games.csv"))[["date", "home", "away", "h_rest", "a_rest", "a_tz_move"]]
H = H.merge(TN, on=["date", "home", "away"], how="left")
H = H[H.home_goals.notna() & H.p_home_win.notna() & H.p_home_win_open.notna() & H.tip.notna()].reset_index(drop=True)
H["tip_utc"] = pd.to_datetime(H.tip, utc=True)
ab = ((H.a_rest == 1) & (H.h_rest > 1)).astype(float); hb = ((H.h_rest == 1) & (H.a_rest > 1)).astype(float)
west = (-H.a_tz_move).clip(lower=0).fillna(0); TRAV = (W_AWAY_B2B * ab + W_HOME_B2B * hb + W_WEST * west).values
H["b2b_h"] = H.h_rest == 1; H["b2b_a"] = H.a_rest == 1


def top(gm):
    try: m = json.loads(gm) if isinstance(gm, str) else {}
    except Exception: m = {}
    return int(max(m, key=m.get)) if m else None


for s in ("home", "away"):
    t = H[f"{s}_gmix"].map(top)
    H[f"{s}_surprise"] = [(g is None) or pd.isna(a) or int(a) != g for g, a in zip(t, H[f"{s}_goalie"])]
H["surprise"] = H.home_surprise | H.away_surprise

# ------------------------------------------------------------------ DK snapshots at T60 / T180
rows = []
for f in sorted(glob.glob(os.path.join(NBA, "data", "odds_history", "nhl", "*.csv.gz"))):
    d = pd.read_csv(f, usecols=["snapshot_utc", "home", "away", "book", "market", "outcome", "price", "point"])
    d = d[(d.book == "draftkings") & d.market.isin(["h2h", "spreads"])]
    if not len(d): continue
    d["is_home"] = d.outcome == d.home
    p = d.pivot_table(index=["snapshot_utc", "home", "away"], columns=["market", "is_home"], values=["price", "point"], aggfunc="first")
    p.columns = [f"{a}_{m}_{'h' if ih else 'a'}" for a, m, ih in p.columns]
    rows.append(p.reset_index())
S = pd.concat(rows, ignore_index=True)
S["t"] = pd.to_datetime(S.snapshot_utc, utc=True); S["h"] = S.home.map(NAME); S["a"] = S.away.map(NAME)
S = S[S.h.notna() & S.a.notna()].sort_values("t")
print(f"DK snapshots: {len(S)} rows, unmapped teams none" if True else "")
idx = {k: g for k, g in S.groupby(["h", "a"])}


def at(r, lo_min, hi_min):
    g = idx.get((r.home, r.away))
    if g is None: return None
    m = (g.t <= r.tip_utc - pd.Timedelta(minutes=lo_min)) & (g.t >= r.tip_utc - pd.Timedelta(minutes=hi_min))
    m &= g.price_h2h_h.notna()
    return g[m].iloc[-1] if m.any() else None


def snap_cols(lo, hi, lab):
    out = {c: [] for c in ("hml", "aml", "hpl", "hpl_o", "apl_o", "t")}
    for r in H.itertuples():
        x = at(r, lo, hi)
        if x is None:
            for c in out: out[c].append(np.nan)
            continue
        out["hml"].append(x.price_h2h_h); out["aml"].append(x.price_h2h_a)
        out["hpl"].append(x.get("point_spreads_h", np.nan)); out["hpl_o"].append(x.get("price_spreads_h", np.nan))
        out["apl_o"].append(x.get("price_spreads_a", np.nan)); out["t"].append(x.t)
    for c, v in out.items(): H[f"{lab}_{c}"] = v


snap_cols(60, 180, "T60"); snap_cols(180, 360, "T180")
H["mkt_close"] = nv(H.close_home_ml, H.close_away_ml)
for lab in ("T60", "T180"):
    print(f"{lab}: DK price found for {H[f'{lab}_hml'].notna().sum()} of {len(H)} games; median minutes before puck drop "
          f"{((H.tip_utc - pd.to_datetime(H[f'{lab}_t'], utc=True)).dt.total_seconds() / 60).median():.0f}")
print(f"Surprise starter games: {H.surprise.mean():.1%} (home {H.home_surprise.mean():.1%}, away {H.away_surprise.mean():.1%})")

hw = (H.home_goals > H.away_goals).values; margin = (H.home_goals - H.away_goals).values; SEA = H.season.values


def ml(lab, pcol):
    mk = nv(H[f"{lab}_hml"], H[f"{lab}_aml"]); p = ML_BLEND * np.clip(H[pcol].values + TRAV, 0.02, 0.98) + (1 - ML_BLEND) * mk
    dh, da = dec(H[f"{lab}_hml"]), dec(H[f"{lab}_aml"]); evh, eva = p * dh - 1, (1 - p) * da - 1
    home = evh >= eva; d = np.where(home, dh, da); win = np.where(home, hw, ~hw)
    pc = np.where(home, H.mkt_close, 1 - H.mkt_close)
    return pd.DataFrame(dict(season=SEA, date=H.date, home_team=H.home, away_team=H.away, home=home, ev=np.where(home, evh, eva), dec=d,
                             win=win, u=np.where(win, d - 1, -1.0), clv=d * pc - 1, our_surprise=np.where(home, H.home_surprise, H.away_surprise),
                             surprise=H.surprise.values))


def pl(lab, suf):
    hpt = H[f"{lab}_hpl"].values.astype(float); ok = np.abs(hpt) == 1.5
    pc_ = np.where(hpt < 0, H[f"p_home_by2{suf}"], 1 - H[f"p_away_by2{suf}"])
    dh, da = dec(H[f"{lab}_hpl_o"]), dec(H[f"{lab}_apl_o"]); evh, eva = pc_ * dh - 1, (1 - pc_) * da - 1
    home = evh >= eva; d = np.where(home, dh, da)
    cov = np.where(hpt < 0, margin >= 2, margin >= -1); win = np.where(home, cov, ~cov)
    same = H.close_home_pl.values == hpt; nvc = nv(H.close_home_pl_odds, H.close_away_pl_odds)
    pcl = np.where(same, np.where(home, nvc, 1 - nvc), np.nan)
    return pd.DataFrame(dict(season=SEA, home=home, ev=np.where(ok, np.where(home, evh, eva), np.nan), dec=d, win=win,
                             u=np.where(win, d - 1, -1.0), clv=d * pcl - 1, b2b=np.where(home, H.b2b_h, H.b2b_a),
                             our_surprise=np.where(home, H.home_surprise, H.away_surprise), surprise=H.surprise.values))


def boot(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 5: return (np.nan, np.nan)
    v = x[RNG.integers(0, len(x), (NBOOT, len(x)))].mean(1); return tuple(np.percentile(v, [5, 95]))


def line(label, B):
    n = len(B)
    if not n: print(f"  {label:52s}     0 bets"); return
    lo, hi = boot(B.u * 100); clo, chi = boot(B.clv * 100); per = [B.u[B.season == s].sum() for s in SEASONS]
    print(f"  {label:52s} {n:5d} bets {B.win.mean():5.1%} {B.u.sum():+7.1f}u {B.u.mean() * 100:+5.1f}/100 [{lo:+5.1f},{hi:+5.1f}]"
          f"  CLV {np.nanmean(B.clv) * 100:+5.2f}% [{clo:+5.2f},{chi:+5.2f}]")
    print(f"  {'':52s} by season " + " ".join(f"{x:+6.1f}" for x in per) + f"  neg {sum(x < 0 for x in per)}/5")


def info(lab, pcol, mask, name):
    m = mask & H[f"{lab}_hml"].notna().values
    y = hw[m].astype(float); base = logit(nv(H[f"{lab}_hml"], H[f"{lab}_aml"])[m])
    x = logit(np.clip(H[pcol].values[m] + TRAV[m], 0.02, 0.98)) - base
    def fit(ix):
        w = 0.0
        for _ in range(25):                                                    # Newton steps, offset logistic, one slope
            p = 1 / (1 + np.exp(-(base[ix] + w * x[ix]))); g = ((y[ix] - p) * x[ix]).sum(); h = (p * (1 - p) * x[ix] ** 2).sum()
            w += g / max(h, 1e-9)
        return w
    w0 = fit(np.arange(m.sum())); bs = [fit(RNG.integers(0, m.sum(), m.sum())) for _ in range(500)]
    lo, hi = np.percentile(bs, [5, 95])
    print(f"  {name:52s} n {m.sum():5d}  w = {w0:+.3f} [{lo:+.3f}, {hi:+.3f}]")


def ll(y, p): p = np.clip(p, 1e-6, 1 - 1e-6); return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


out = []
for lab in ("T60", "T180"):
    print("\n" + "=" * 150 + f"\n{lab}" + ("  [PRIMARY]" if lab == "T60" else "  (secondary; more look-ahead risk)") + "\n" + "-" * 150)
    MP, MO = ml(lab, "p_home_win"), ml(lab, "p_home_win_open")
    qp = MP.ev.notna() & (MP.ev >= ML_THR); qo = MO.ev.notna() & (MO.ev >= ML_THR)
    line("A  ML pretip (actual starters), EV 4%+", MP[qp]); line("A-open  ML opener model (expected goalies), EV 4%+", MO[qo])
    line("C  A, surprise games", MP[qp & MP.surprise]); line("D  A, non-surprise games", MP[qp & ~MP.surprise])
    line("   A-open, surprise games", MO[qo & MO.surprise])
    line("   A, EV 9%+", MP[qp & (MP.ev >= 0.09)])
    PP, PO = pl(lab, ""), pl(lab, "_open")
    pp = PP.ev.notna() & (PP.ev >= PL_THR) & ~PP.b2b; po = PO.ev.notna() & (PO.ev >= PL_THR) & ~PO.b2b
    line("B  PL pretip, EV 9%+, no b2b", PP[pp]); line("B-open  PL opener model", PO[po])
    line("   B, surprise games", PP[pp & PP.surprise])
    print("  information test (logistic slope on model minus DK, offset DK no-vig at " + lab + ")")
    allm = np.ones(len(H), bool)
    info(lab, "p_home_win", allm, "pretip, all games"); info(lab, "p_home_win_open", allm, "opener model, all games")
    info(lab, "p_home_win", H.surprise.values, "pretip, surprise games"); info(lab, "p_home_win_open", H.surprise.values, "opener model, surprise games")
    m = H[f"{lab}_hml"].notna().values & H.mkt_close.notna().values; y = hw[m].astype(float)
    mk = nv(H[f"{lab}_hml"], H[f"{lab}_aml"])[m]
    for nm_, p in (("DK no-vig at " + lab, mk), ("DK no-vig close", H.mkt_close.values[m]),
                   ("pretip blend at " + lab, ML_BLEND * np.clip(H.p_home_win.values[m] + TRAV[m], .02, .98) + (1 - ML_BLEND) * mk),
                   ("opener-model blend at " + lab, ML_BLEND * np.clip(H.p_home_win_open.values[m] + TRAV[m], .02, .98) + (1 - ML_BLEND) * mk)):
        sm = H.surprise.values[m]
        print(f"  log loss {nm_:32s} all {ll(y, p):.4f}   surprise games {ll(y[sm], p[sm]):.4f}  (n {m.sum()}, {sm.sum()})")
    if lab == "T60":
        out.append(MP[qp].assign(rule="A ML pretip T60")); out.append(PP[pp].assign(rule="B PL pretip T60"))
        T60_MP, T60_PP = MP, PP

# ------------------------------------------------------------------ E: opener bets and surprise starters
print("\n" + "=" * 150 + "\nE. STEP-1 v4 OPENER BETS (lag 1, graded at the opener) by our starter and the pretip re-check at T60\n" + "-" * 150)
B = pd.read_csv(os.path.join(W, "research", "spreads", "step1_nhl_bets.csv")); B = B[B.version == "v4"].copy()
key = H.set_index(["date", "home", "away"])
B = B.join(key[["home_surprise", "away_surprise"]], on=["date", "home_team", "away_team"])
B["our_surprise"] = np.where(B.home, B.home_surprise, B.away_surprise).astype(bool)
pos = {k: i for i, k in enumerate(zip(H.date, H.home, H.away))}
ix = np.array([pos.get(k, -1) for k in zip(B.date, B.home_team, B.away_team)])
evm = np.where(ix >= 0, T60_MP.ev.values[np.clip(ix, 0, None)], np.nan); sidem = np.where(ix >= 0, T60_MP.home.values[np.clip(ix, 0, None)], True)
evp = np.where(ix >= 0, T60_PP.ev.values[np.clip(ix, 0, None)], np.nan); sidep = np.where(ix >= 0, T60_PP.home.values[np.clip(ix, 0, None)], True)
B["still"] = np.where(B.market == "ML", (sidem == B.home) & (evm >= ML_THR), (sidep == B.home) & (evp >= PL_THR))
B.loc[np.isnan(np.where(B.market == "ML", evm, evp)), "still"] = np.nan
for mk in ("ML", "PL"):
    X = B[B.market == mk]
    line(f"{mk} opener bets, our starter as expected", X[~X.our_surprise]); line(f"{mk} opener bets, our starter a SURPRISE", X[X.our_surprise])
    line(f"{mk}   surprise and pretip at T60 below the bar / flipped", X[X.our_surprise & (X.still == False)])
    line(f"{mk}   surprise and pretip at T60 still a bet", X[X.our_surprise & (X.still == True)])
    line(f"{mk} any starter, pretip at T60 below the bar / flipped", X[X.still == False])

pd.concat(out).to_csv(os.path.join(W, "research", "spreads", "step3_nhl_goalie_bets.csv"), index=False)
