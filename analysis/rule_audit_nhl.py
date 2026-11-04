"""
Audit of every rule in the NHL alert path that blocks, delays, downgrades or stops pushing a bet (Nov 4, 2026). Analysis only:
nothing here is imported by the live code.

Question asked of each rule: what is the record (bets, win %, units at the price you could actually get) of the bets it blocks
vs the bets it keeps, using only information available at the moment the bet would be placed?

Data
  - Shot model walk-forward predictions at DraftKings' opener, 2021-22..2025-26, one-day information lag (as live):
    WORK/_tmp/dk_holdout_{2022..2026}.csv. Built by dev/dk_holdout.py with SPLITS extended to 2025 ([2021-24]) and 2026
    ([2022-25]); run this script with --build to make them (needs data/box_hist.csv and data/shots_hist.csv, gitignored).
    Reproduces nba-mixed-model analysis/sharp_nhl_output.txt exactly for 2021-22..2024-25 (2025-26 is close: 330 vs 298 bets).
  - Hourly snapshots of DraftKings and Pinnacle, every market (nba-mixed-model data/odds_history/nhl/*.csv.gz): prices at
    DK's open, +60 min, halfway to puck drop, and at the moment Pinnacle first posts.
  - Schedule/travel features: nba-mixed-model analysis/travel_nhl_games.csv (rest days, time-zone moves).
  - Live season: state/alerts.csv in this repo.
Live rules replicated (alert.py, Nov 4): moneyline chance = 0.55 x (shot model + travel adj.) + 0.45 x DK no-vig opener, EV 4%+;
puck line shot model EV 6%+; totals overs only EV 6%+; no bet on a team on the 2nd night of a back-to-back; Pinnacle filter.
"Opener" = the first hourly snapshot that has DK's moneyline (up to ~1 h after DK actually posts).

  python analysis/rule_audit_nhl.py WORK NBA_REPO [--build]  > analysis/rule_audit_nhl_output.txt
"""
import os, sys, glob, pickle
import warnings
import numpy as np, pandas as pd
warnings.simplefilter("ignore", pd.errors.PerformanceWarning)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.abspath(sys.argv[1]); NBA = os.path.abspath(sys.argv[2])
sys.path.insert(0, WORK)
import nhl_mixed_model as nm                                                     # noqa: E402

SEASONS = (2022, 2023, 2024, 2025, 2026)
ML_BLEND, ML_THR, THR, THR_MOVED, NEAR_OPEN, PIN_DIS = 0.55, 0.04, 0.06, 0.09, 0.015, 0.005
W_AWAY_B2B, W_HOME_B2B, W_WEST = 0.0253, -0.0307, -0.0226
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def nv(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)


# ------------------------------------------------------------------------------------------------ holdout predictions
def build_holdout():
    import nhl_xg_model as xm, build_features as bf
    T0 = pd.read_csv(os.path.join(WORK, "data", "training_games.csv"))
    G = pd.read_csv(os.path.join(WORK, "data", "games_hist.csv"), parse_dates=["date"])
    B = pd.read_csv(os.path.join(WORK, "data", "box_hist.csv")); S = pd.read_csv(os.path.join(WORK, "data", "shots_hist.csv"), low_memory=False)
    F1, _ = bf.build(G, B, lag_days=1); T1 = T0.copy().set_index("game_id")
    for c in ("home_gmix", "away_gmix", "home_miss_off_open", "away_miss_off_open", "home_n_out_open", "away_n_out_open"):
        T1[c] = F1.set_index("game_id")[c].reindex(T1.index)
    T1 = T1.reset_index()
    DK = pd.read_csv(os.path.join(WORK, "data", "nhl_prices.csv.gz")); DK = DK[DK.book == "draftkings"].drop(columns=["book", "event_id"])
    for test, train in ((2022, [2020, 2021]), (2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]),
                        (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025])):
        xmod = xm.xg_model(S, T0, train); TG = xm.team_game_xg(xm.apply_xg(S, T0, xmod), T0)
        D = T1.drop(columns=[c for c in TG.columns if c != "game_id" and c in T1]).merge(TG, on="game_id", how="left")
        _, P, _ = xm.run(D, train, test, tot_cal="none", lag_days=1, halflives=(None, 60))
        P["date"] = pd.to_datetime(P.date).dt.strftime("%Y-%m-%d")
        P = P.drop(columns=[c for c in P if c.startswith(("open_", "close_", "mid_"))]).merge(DK, on=["date", "home", "away"], how="left")
        P.to_csv(os.path.join(WORK, "_tmp", f"dk_holdout_{test}.csv"), index=False)


if "--build" in sys.argv: build_holdout()
H = pd.concat([pd.read_csv(os.path.join(WORK, "_tmp", f"dk_holdout_{s}.csv")) for s in SEASONS], ignore_index=True)
TN = pd.read_csv(os.path.join(NBA, "analysis", "travel_nhl_games.csv"))[["date", "home", "away", "h_rest", "a_rest", "a_tz_move"]]
H = H.merge(TN, on=["date", "home", "away"], how="left")
H = H[H.open_home_ml.notna() & H.home_goals.notna() & H.p_home_win_open.notna()].reset_index(drop=True)
H["t0"] = pd.to_datetime(H.t0, utc=True); H["tip"] = pd.to_datetime(H.tip, utc=True)

# ------------------------------------------------------------------------------------------------ DK + Pinnacle snapshots
NAME = {"Anaheim Ducks": "ana", "Arizona Coyotes": "uta", "Utah Hockey Club": "uta", "Utah Mammoth": "uta", "Boston Bruins": "bos",
        "Buffalo Sabres": "buf", "Carolina Hurricanes": "car", "Columbus Blue Jackets": "cbj", "Calgary Flames": "cgy",
        "Chicago Blackhawks": "chi", "Colorado Avalanche": "col", "Dallas Stars": "dal", "Detroit Red Wings": "det",
        "Edmonton Oilers": "edm", "Florida Panthers": "fla", "Los Angeles Kings": "la", "Minnesota Wild": "min",
        "Montréal Canadiens": "mtl", "Montreal Canadiens": "mtl", "New Jersey Devils": "nj", "Nashville Predators": "nsh",
        "New York Islanders": "nyi", "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
        "Pittsburgh Penguins": "pit", "Seattle Kraken": "sea", "San Jose Sharks": "sj", "St Louis Blues": "stl", "St. Louis Blues": "stl",
        "Tampa Bay Lightning": "tb", "Toronto Maple Leafs": "tor", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk",
        "Winnipeg Jets": "wpg", "Washington Capitals": "wsh"}
cache = os.path.join(WORK, "_tmp", "rule_audit_snaps.pkl")
if os.path.exists(cache):
    SN = pickle.load(open(cache, "rb"))
else:
    parts = []
    for f in sorted(glob.glob(os.path.join(NBA, "data", "odds_history", "nhl", "*.csv.gz"))):
        d = pd.read_csv(f); d = d[d.book.isin(["draftkings", "pinnacle"]) & d.home.isin(NAME) & d.away.isin(NAME)]
        if not len(d): continue
        d["t"] = pd.to_datetime(d.snapshot_utc, utc=True)
        d["tip"] = pd.to_datetime(d.commence_et).dt.tz_localize("America/New_York").dt.tz_convert("UTC")
        d = d[d.t < d.tip]
        d["date"] = d.commence_et.str[:10]; d["h"] = d.home.map(NAME); d["a"] = d.away.map(NAME)
        d["col"] = np.select([(d.market == "h2h") & (d.outcome == d.home), d.market == "h2h",
                              (d.market == "spreads") & (d.outcome == d.home), d.market == "spreads",
                              d.outcome == "Over"], ["hml", "aml", "hpl", "apl", "ov"], "un")
        pr = d.pivot_table(index=["book", "date", "h", "a", "t"], columns="col", values="price", aggfunc="first")
        pt = d[d.col.isin(["hpl", "ov"])].pivot_table(index=["book", "date", "h", "a", "t"], columns="col", values="point", aggfunc="first")
        pt.columns = [{"hpl": "hpl_pt", "ov": "tot_pt"}[c] for c in pt.columns]
        parts.append(pr.join(pt, how="left").reset_index())
    SN = pd.concat(parts, ignore_index=True).sort_values(["book", "date", "h", "a", "t"])
    SN = SN.rename(columns={"h": "home", "a": "away"})
    for c in ("hml", "aml", "hpl", "apl", "ov", "un", "hpl_pt", "tot_pt"):
        if c not in SN: SN[c] = np.nan
    pickle.dump(SN, open(cache, "wb"))
DKS = SN[(SN.book == "draftkings") & SN.hml.notna()].copy(); PNS = SN[(SN.book == "pinnacle") & SN.hml.notna()].copy()
key = ["date", "home", "away"]
pf = PNS.groupby(key).head(1)[key + ["t", "hml", "aml", "ov", "un", "tot_pt"]].rename(columns={"t": "pin_t", "hml": "pin_hml", "aml": "pin_aml", "ov": "pin_ov", "un": "pin_un", "tot_pt": "pin_tot"})
H = H.merge(pf, on=key, how="left")
H["pin_p"] = nv(H.pin_hml, H.pin_aml)


def dk_at(times, label):
    """DK's prices in the last snapshot at or before each game's time (NaT -> NaN)"""
    q = H[key].copy(); q["tq"] = times; q["_i"] = np.arange(len(H)); q = q.dropna(subset=["tq"])
    out = pd.DataFrame(index=np.arange(len(H)))
    m = pd.merge_asof(q.sort_values("tq"), DKS.sort_values("t").rename(columns={"t": "tq"}), on="tq", by=key, direction="backward")
    m = m.set_index("_i")
    for c in ("hml", "aml", "hpl_pt", "hpl", "apl", "tot_pt", "ov", "un"):
        out[f"{label}_{c}"] = m[c].reindex(out.index).values
    return out


H = pd.concat([H, dk_at(H.pin_t, "atpin")], axis=1)
pa = pd.merge_asof(H[key + ["t0"]].assign(_i=np.arange(len(H))).sort_values("t0"),
                   PNS.sort_values("t")[key + ["t", "hml", "aml"]].rename(columns={"t": "t0"}), on="t0", by=key, direction="backward").set_index("_i").sort_index()
H["pin_p_at_open"] = nv(pa.hml.values, pa.aml.values)
H["pin_lag_h"] = (H.pin_t - H.t0).dt.total_seconds() / 3600

# ------------------------------------------------------------------------------------------------ live-rule probabilities
hw = (H.home_goals > H.away_goals).values; margin = (H.home_goals - H.away_goals).values; total = (H.home_goals + H.away_goals).values
ab = ((H.a_rest == 1) & (H.h_rest > 1)).astype(float); hb = ((H.h_rest == 1) & (H.a_rest > 1)).astype(float)
west = (-H.a_tz_move).clip(lower=0).fillna(0)
H["p0"] = (H.p_home_win_open + W_AWAY_B2B * ab + W_HOME_B2B * hb + W_WEST * west).clip(0.02, 0.98).values
H["mkt_open"] = nv(H.open_home_ml, H.open_away_ml)
H["pml"] = ML_BLEND * H.p0 + (1 - ML_BLEND) * H.mkt_open           # live moneyline chance (fixed after the opener)
H["b2b_h"] = (H.h_rest == 1).values; H["b2b_a"] = (H.a_rest == 1).values
SEA = H.season.values


def ml_bets(hml, aml, p=None, label=""):
    p = H.pml.values if p is None else p
    dh, da = dec(hml), dec(aml); evh, eva = p * dh - 1, (1 - p) * da - 1
    home = evh >= eva; ev = np.where(home, evh, eva); d = np.where(home, dh, da)
    win = np.where(home, hw, margin < 0); u = np.where(win, d - 1, -1.0)
    return pd.DataFrame(dict(home=home, ev=ev, dec=d, win=win, u=u, ok=~np.isnan(ev), imp=1 / d, b2b=np.where(home, H.b2b_h, H.b2b_a)))


def pl_bets(hpt, hodds, aodds):
    hpt = np.asarray(hpt, float); pc = np.where(hpt < 0, H.p_home_by2_open, 1 - H.p_away_by2_open)
    dh, da = dec(hodds), dec(aodds); evh, eva = pc * dh - 1, (1 - pc) * da - 1
    home = evh >= eva; ev = np.where(home, evh, eva); d = np.where(home, dh, da)
    cov = np.where(hpt < 0, margin >= 2, margin >= -1); win = np.where(home, cov, ~cov); u = np.where(win, d - 1, -1.0)
    return pd.DataFrame(dict(home=home, ev=ev, dec=d, win=win, u=u, ok=~np.isnan(ev) & ~np.isnan(hpt), imp=1 / d, pt=hpt,
                             b2b=np.where(home, H.b2b_h, H.b2b_a)))


def tot_bets(T, ov, un):
    T = np.asarray(T, float); ok = ~np.isnan(T) & H.lam_home_open.notna().values
    po, pu, pp = nm.over_prob(H.lam_home_open.fillna(3).values, H.lam_away_open.fillna(3).values, np.nan_to_num(T, nan=6.0), nm.H_OT_DEFAULT, {})
    do, du = dec(ov), dec(un); evo, evu = po * do + pp - 1, pu * du + pp - 1
    over = evo >= evu; ev = np.where(over, evo, evu); d = np.where(over, do, du)
    res = np.where(total > T, 1, np.where(total < T, -1, 0)) * np.where(over, 1, -1)
    u = np.where(res > 0, d - 1, np.where(res < 0, -1.0, 0.0))
    return pd.DataFrame(dict(over=over, ev=ev, dec=d, win=res > 0, push=res == 0, u=u, ok=ok & ~np.isnan(ev), imp=1 / d, T=T))


def rep(label, m, B, show_season=True):
    m = np.asarray(m, bool) & B.ok.values
    n = int(m.sum()); u = B.u.values[m]; w = B.win.values[m]
    s = f"  {label:58s} {n:5d} bets  {w.mean() if n else 0:5.1%}  {u.sum():+7.1f}u  ({u.sum() / max(n, 1):+6.1%})"
    if show_season:
        per = [B.u.values[m & (SEA == y)].sum() for y in SEASONS]
        s += "  | " + " ".join(f"{x:+6.1f}" for x in per) + f"  neg {sum(x < 0 for x in per)}/5"
    print(s)
    return n, u.sum()


def hdr(t): print("\n" + "=" * 130 + f"\n{t}\n" + "-" * 130 + f"\n  {'':58s} {'bets':>5s}  {'win%':>5s}  {'units':>8s}  {'ROI':>8s}  | by season 21-22 22-23 23-24 24-25 25-26")


print(f"Games with DK opener + shot model prediction: {len(H)} ({', '.join(f'{y}: {(SEA == y).sum()}' for y in SEASONS)})")
print(f"Pinnacle first moneyline seen for {H.pin_t.notna().mean():.0%} of games; posted after DK's opener in "
      f"{(H.pin_lag_h > 0).mean():.0%}; median lag {H.pin_lag_h.median():.1f} h; Pinnacle already up at DK's opener {H.pin_p_at_open.notna().mean():.0%}")

O_ML = ml_bets(H.open_home_ml, H.open_away_ml)
O_PL = pl_bets(H.open_home_pl, H.open_home_pl_odds, H.open_away_pl_odds)
O_T = tot_bets(H.open_total, H.open_over_odds, H.open_under_odds)
ml_q = O_ML.ok & (O_ML.ev >= ML_THR); pl_q = O_PL.ok & (O_PL.ev >= THR); ov_q = O_T.ok & O_T.over & (O_T.ev >= THR)
# Pinnacle relative to our moneyline side (+ = Pinnacle likes our side more than DK's opener)
pin_diff_first = np.where(O_ML.home, H.pin_p - H.mkt_open, H.mkt_open - H.pin_p)
pin_diff_open = np.where(O_ML.home, H.pin_p_at_open - H.mkt_open, H.mkt_open - H.pin_p_at_open)
pin_up_at_open = H.pin_p_at_open.notna().values
pin_block_live = pin_up_at_open & (pin_diff_open < -PIN_DIS)

hdr("0. THE LIVE RULES AT DK'S OPENER (2021-22..2025-26)")
rep("moneyline: blend EV 4%+, all", ml_q, O_ML)
rep("moneyline: + no b2b + Pinnacle (only if up at DK open)", ml_q & ~O_ML.b2b & ~pin_block_live, O_ML)
rep("puck line: EV 6%+, all", pl_q, O_PL)
rep("puck line: + no b2b", pl_q & ~O_PL.b2b, O_PL)
rep("overs: EV 6%+", ov_q, O_T)

# ------------------------------------------------------------------------------------------------ 1. back-to-back skip
hdr("1. SKIP_B2B: no bet on a team playing the 2nd night of a back-to-back (b2b known from the schedule: no timing issue)")
rep("ML (live blend, incl. travel adj.) kept: not b2b", ml_q & ~O_ML.b2b, O_ML)
rep("ML (live blend) BLOCKED: our team on b2b", ml_q & O_ML.b2b, O_ML)
raw = ml_bets(H.open_home_ml, H.open_away_ml, p=H.p_home_win_open.values)
rep("ML raw shot model EV 6%+ BLOCKED (no travel adj, as originally tested)", raw.ok & (raw.ev >= THR) & raw.b2b, raw)
rep("PL kept: not b2b", pl_q & ~O_PL.b2b, O_PL)
rep("PL BLOCKED: our team on b2b", pl_q & O_PL.b2b, O_PL)
both_b2b = (H.b2b_h & H.b2b_a).values
rep("  of which both teams on b2b (ML)", ml_q & O_ML.b2b & both_b2b, O_ML)
rep("  of which both teams on b2b (PL)", pl_q & O_PL.b2b & both_b2b, O_PL)
rep("overs with either team on b2b (rule does not apply)", ov_q & (H.b2b_h | H.b2b_a).values, O_T)

# ------------------------------------------------------------------------------------------------ 2-3. Pinnacle
hdr("2. PINNACLE at alert time (USE_PINNACLE_RULE): Pinnacle already posted when DK opens and gives our side 0.5+ pts less -> NO BET")
rep("ML: Pinnacle up at DK open, agrees/same (kept)", ml_q & pin_up_at_open & ~pin_block_live, O_ML)
rep("ML: Pinnacle up at DK open, disagrees (BLOCKED)", ml_q & pin_block_live, O_ML)
rep("ML: Pinnacle not up yet at DK open (alert goes out)", ml_q & ~pin_up_at_open, O_ML)

hdr("3. PINNACLE after the alert (DON'T BET follow-up): bet alerted at DK open, Pinnacle posts later and disagrees")
late = ml_q & ~pin_up_at_open & H.pin_t.notna().values & (H.pin_lag_h > 0).values & ~O_ML.b2b
dis = late & (pin_diff_first < -PIN_DIS); agr = late & (pin_diff_first >= -PIN_DIS)
print("  (a) graded at DK's OPENING price with Pinnacle's later verdict = the quoted record (LOOK-AHEAD: cannot both bet the open and filter)")
rep("    Pinnacle first price agrees/same", agr, O_ML)
rep("    Pinnacle first price disagrees", dis, O_ML)
A_ML = ml_bets(H.atpin_hml, H.atpin_aml)                                            # same blended chance, DK price when Pinnacle posts
same_side = A_ML.home.values == O_ML.home.values
dis_w = np.where(A_ML.home, H.pin_p - nv(H.atpin_hml, H.atpin_aml), nv(H.atpin_hml, H.atpin_aml) - H.pin_p)
near_pin = np.abs(A_ML.imp.values - O_ML.imp.values) <= NEAR_OPEN
bar_pin = np.where(near_pin, ML_THR, THR_MOVED)
still = same_side & (A_ML.ev.values >= bar_pin)
print("  (b) bettable: you did NOT bet the open; you look again when Pinnacle posts (median "
      f"{np.nanmedian(H.pin_lag_h[late]):.1f} h later) and bet DK's price THEN")
rep("    all opener alerts, at DK's price when Pinnacle posts", late & same_side, A_ML)
rep("    still a bet then (live bar) & Pinnacle agrees/same -> REMINDER", late & still & (dis_w >= -PIN_DIS), A_ML)
rep("    still a bet then & Pinnacle disagrees -> DON'T BET (blocked)", late & still & (dis_w < -PIN_DIS), A_ML)
rep("    no longer a bet then (DON'T BET for EV anyway)", late & same_side & ~still, A_ML)
rep("    AS CODED (Pinnacle vs DK's OPENER): still a bet, Pinnacle disagrees -> DON'T BET", late & still & (pin_diff_first < -PIN_DIS), A_ML)
rep("    AS CODED: still a bet, Pinnacle agrees/same -> REMINDER", late & still & (pin_diff_first >= -PIN_DIS), A_ML)
print("  (c) the same opener alerts if simply bet at the open (what the follow-up costs a bettor who bets immediately: nothing)")
rep("    all late-Pinnacle opener alerts, at the opener", late, O_ML)
print("  (d) Pinnacle disagreeing vs DK's CURRENT price (what the live follow-up actually compares: Pinnacle vs DK's OPENER)")
rep("    disagrees with DK opener but NOT with DK's price at that time", late & still & (pin_diff_first < -PIN_DIS) & (dis_w >= -PIN_DIS), A_ML)
rep("    agrees with DK opener but disagrees with DK's price at that time", late & still & (pin_diff_first >= -PIN_DIS) & (dis_w < -PIN_DIS), A_ML)
# Pinnacle for the other markets (not applied live) at the bettable price
A_PL = pl_bets(H.atpin_hpl_pt, H.atpin_hpl, H.atpin_apl); A_T = tot_bets(H.atpin_tot_pt, H.atpin_ov, H.atpin_un)
pl_late = pl_q & ~O_PL.b2b & H.pin_t.notna().values & (H.pin_lag_h > 0).values
pl_pin_dis = np.where(O_PL.home, H.pin_p - H.mkt_open, H.mkt_open - H.pin_p) < -PIN_DIS
print("  (e) other markets (no Pinnacle rule live). Puck line: Pinnacle's first MONEYLINE vs DK opener for our team")
rep("    PL at open, Pinnacle agrees/same", pl_late & ~pl_pin_dis, O_PL)
rep("    PL at open, Pinnacle disagrees (look-ahead grade)", pl_late & pl_pin_dis, O_PL)
pl_same = (A_PL.home.values == O_PL.home.values) & (A_PL.pt.values == O_PL.pt.values) & (A_PL.ev.values >= THR)
rep("    PL at DK price when Pinnacle posts, still EV 6%+, Pinnacle disagrees", pl_late & pl_same & pl_pin_dis, A_PL)
rep("    PL at DK price when Pinnacle posts, still EV 6%+, Pinnacle agrees", pl_late & pl_same & ~pl_pin_dis, A_PL)
ov_late = ov_q & H.pin_t.notna().values & (H.pin_lag_h > 0).values & H.pin_tot.notna().values
ov_pin_dis = H.pin_tot.values < H.open_total.values
rep("    overs at open, Pinnacle's first total lower (disagrees)", ov_late & ov_pin_dis, O_T)
rep("    overs at open, Pinnacle's first total same/higher", ov_late & ~ov_pin_dis, O_T)

# ------------------------------------------------------------------------------------------------ 4. overs only
hdr("4. TOTAL_SIDES = over only (unders never alerted)")
rep("overs EV 6%+ (kept)", ov_q, O_T)
rep("unders EV 6%+ (BLOCKED)", O_T.ok & ~O_T.over & (O_T.ev >= THR), O_T)
rep("unders EV 9%+ (BLOCKED)", O_T.ok & ~O_T.over & (O_T.ev >= 0.09), O_T)

# ------------------------------------------------------------------------------------------------ 5. EV bars at the opener
hdr("5. EV bars at the opener (ML_THRESHOLD 4% on the blend; THRESHOLD 6% puck line / overs)  [b2b removed]")
for lo, hi in ((0.0, 0.02), (0.02, 0.04), (0.04, 0.06), (0.06, 0.09), (0.09, 9)):
    rep(f"ML blended EV {lo:.0%}-{hi:.0%}" + ("  (BLOCKED)" if hi <= ML_THR else ""), O_ML.ok & (O_ML.ev >= lo) & (O_ML.ev < hi) & ~O_ML.b2b, O_ML)
for lo, hi in ((0.02, 0.04), (0.04, 0.06), (0.06, 0.09), (0.09, 9)):
    rep(f"PL EV {lo:.0%}-{hi:.0%}" + ("  (BLOCKED)" if hi <= THR else ""), O_PL.ok & (O_PL.ev >= lo) & (O_PL.ev < hi) & ~O_PL.b2b, O_PL)
for lo, hi in ((0.02, 0.04), (0.04, 0.06), (0.06, 0.09), (0.09, 9)):
    rep(f"overs EV {lo:.0%}-{hi:.0%}" + ("  (BLOCKED)" if hi <= THR else ""), O_T.ok & O_T.over & (O_T.ev >= lo) & (O_T.ev < hi), O_T)

# ------------------------------------------------------------------------------------------------ 6. moved prices
for lab, LB in (("m60", "+60 min"), ("mid", "halfway to puck drop")):
    hdr(f"6. MOVED_SKIP / NEAR_OPEN / THRESHOLD_MOVED at DK's price {LB} (bets placed AT that price)")
    X_ML = ml_bets(H[f"{lab}_home_ml"], H[f"{lab}_away_ml"])
    X_PL = pl_bets(H[f"{lab}_home_pl"], H[f"{lab}_home_pl_odds"], H[f"{lab}_away_pl_odds"])
    X_T = tot_bets(H[f"{lab}_total"], H[f"{lab}_over_odds"], H[f"{lab}_under_odds"])
    oimp_ml = np.where(X_ML.home, 1 / dec(H.open_home_ml), 1 / dec(H.open_away_ml))
    oimp_pl = np.where(X_PL.home, 1 / dec(H.open_home_pl_odds), 1 / dec(H.open_away_pl_odds))
    oimp_pl = np.where(H[f"{lab}_home_pl"].values == H.open_home_pl.values, oimp_pl, np.nan)
    oimp_t = np.where(X_T.over, 1 / dec(H.open_over_odds), 1 / dec(H.open_under_odds))
    oimp_t = np.where(H[f"{lab}_total"].values == H.open_total.values, oimp_t, np.nan)
    for nm_, X, oimp, bar, extra, q0 in (("ML", X_ML, oimp_ml, ML_THR, ~X_ML.b2b.values, ml_q.values),
                                         ("PL", X_PL, oimp_pl, THR, ~X_PL.b2b.values, pl_q.values),
                                         ("overs", X_T, oimp_t, THR, X_T.over.values, ov_q.values)):
        mv = X.imp.values - oimp          # + = our side got more expensive since open (market moved toward us)
        near = np.abs(mv) <= NEAR_OPEN
        rep(f"{nm_} near open (within 1.5 pts), EV>={bar:.0%} -> alert", extra & near & (X.ev.values >= bar), X)
        rep(f"{nm_} moved TOWARD us >1.5 pts, EV 9%+ -> INFO ONLY (blocked)", extra & (mv > NEAR_OPEN) & (X.ev.values >= THR_MOVED), X)
        rep(f"{nm_} moved AGAINST us >1.5 pts, EV 9%+ -> INFO ONLY (blocked)", extra & (mv < -NEAR_OPEN) & (X.ev.values >= THR_MOVED), X)
        rep(f"{nm_} moved (either way), EV {bar:.0%}-9% -> silent", extra & ~near & (X.ev.values >= bar) & (X.ev.values < THR_MOVED), X)
        if nm_ != "ML":
            rep(f"{nm_} line NUMBER changed since open, EV 9%+ (treated as moved)", extra & np.isnan(oimp) & (X.ev.values >= THR_MOVED), X)
        rep(f"{nm_} NEW (no bet at the open), moved, EV>={bar:.0%} (blocked/silent)", extra & ~q0 & ~near & (X.ev.values >= bar), X)
        rep(f"{nm_} NEW (no bet at the open), moved, EV 9%+ (blocked)", extra & ~q0 & ~near & (X.ev.values >= THR_MOVED), X)

# ------------------------------------------------------------------------------------------------ 7. DON'T BET follow-up on EV
hdr("7. DON'T BET / REMINDER follow-up: bets alerted at DK's opener, not yet placed, re-checked later (graded at the LATER price)")
for lab, LB in (("m60", "+60 min"), ("mid", "halfway")):
    for nm_, OB, q, mk in (("ML", O_ML, ml_q & ~O_ML.b2b & ~pin_block_live, "ml"), ("PL", O_PL, pl_q & ~O_PL.b2b, "pl"), ("overs", O_T, ov_q, "t")):
        if mk == "ml": X = ml_bets(H[f"{lab}_home_ml"], H[f"{lab}_away_ml"]); same = X.home.values == OB.home.values; bar = ML_THR
        elif mk == "pl":
            X = pl_bets(H[f"{lab}_home_pl"], H[f"{lab}_home_pl_odds"], H[f"{lab}_away_pl_odds"]); bar = THR
            same = (X.home.values == OB.home.values) & (H[f"{lab}_home_pl"].values == H.open_home_pl.values)
        else:
            X = tot_bets(H[f"{lab}_total"], H[f"{lab}_over_odds"], H[f"{lab}_under_odds"]); bar = THR
            same = X.over.values & (H[f"{lab}_total"].values == H.open_total.values)
        # EV of OUR opener side at the later price (X picks the best side; for ML/PL the opposite side rarely qualifies)
        mv = X.imp.values - OB.imp.values
        near = np.abs(mv) <= NEAR_OPEN
        ok_now = same & (X.ev.values >= np.where(near, bar, THR_MOVED))
        base = np.asarray(q, bool) & same
        rep(f"{nm_} @{LB}: unmoved (within 1.5), still a bet -> REMINDER", base & near & ok_now, X)
        rep(f"{nm_} @{LB}: unmoved, below bar -> DON'T BET", base & near & ~ok_now, X)
        rep(f"{nm_} @{LB}: moved toward us, EV 9%+ left -> REMINDER", base & (mv > NEAR_OPEN) & ok_now, X)
        rep(f"{nm_} @{LB}: moved toward us, EV <9% -> DON'T BET", base & (mv > NEAR_OPEN) & ~ok_now, X)
        rep(f"{nm_} @{LB}: moved against us (better price), EV 9%+ -> REMINDER", base & (mv < -NEAR_OPEN) & ok_now, X)
        rep(f"{nm_} @{LB}: moved against us (better price), EV <9% -> DON'T BET", base & (mv < -NEAR_OPEN) & ~ok_now, X)
        if mk != "ml": rep(f"{nm_} @{LB}: line number changed (not graded at a comparable price)", np.asarray(q, bool) & ~same, OB)

# ------------------------------------------------------------------------------------------------ 8. one bet per game
hdr("8. ONE BET PER GAME: ML and PL on the same team both qualify at the open -> only the higher EV (blended ML EV vs raw PL EV)")
both = ml_q & pl_q & ~O_ML.b2b & ~O_PL.b2b & (O_ML.home.values == O_PL.home.values)
pick_pl = both & (O_PL.ev.values > O_ML.ev.values)
print(f"  same-team games: {int(both.sum())}; puck line chosen in {int(pick_pl.sum())} ({pick_pl.sum() / max(both.sum(), 1):.0%})")
rep("chosen leg: PL (ML dropped)", pick_pl, O_PL); rep("dropped leg: ML", pick_pl, O_ML)
rep("chosen leg: ML (PL dropped)", both & ~pick_pl, O_ML); rep("dropped leg: PL", both & ~pick_pl, O_PL)
u_ch = np.where(pick_pl, O_PL.u, O_ML.u); u_dr = np.where(pick_pl, O_ML.u, O_PL.u)
print(f"  chosen legs {u_ch[both].sum():+.1f}u on {int(both.sum())}; dropped legs {u_dr[both].sum():+.1f}u on {int(both.sum())} "
      f"(by season dropped: {' '.join(f'{u_dr[both & (SEA == y)].sum():+.1f}' for y in SEASONS)})")
alt = both & (O_ML.ev.values >= O_PL.ev.values)     # same comparison is what live does; alternative: always the ML / always the PL
rep("alternative: always the ML in these games", both, O_ML); rep("alternative: always the PL in these games", both, O_PL)
u_both = O_ML.u.values + O_PL.u.values
print(f"  alternative: bet both legs: {u_both[both].sum():+.1f}u on {2 * int(both.sum())} units "
      f"(by season {' '.join(f'{u_both[both & (SEA == y)].sum():+.1f}' for y in SEASONS)})")

hdr("9. MODELS DISAGREE / both sides: ML and PL qualify on OPPOSITE teams -> NO BET on either")
opp = ml_q & pl_q & (O_ML.home.values != O_PL.home.values)
rep("ML leg (blocked)", opp & ~O_ML.b2b, O_ML); rep("PL leg (blocked)", opp & ~O_PL.b2b, O_PL)

# ------------------------------------------------------------------------------------------------ 10. second chance
hdr("10. SECOND CHANCE (adds bets): raw shot model EV<6% at DK open, 6%+ at DK's price when Pinnacle posts, Pinnacle agrees/same")
rawA = ml_bets(H.atpin_hml, H.atpin_aml, p=H.p_home_win_open.values)
dA = np.where(rawA.home, H.pin_p - nv(H.atpin_hml, H.atpin_aml), nv(H.atpin_hml, H.atpin_aml) - H.pin_p)
sc = rawA.ok & (raw.ev.values < THR) & (rawA.ev.values >= THR) & (dA >= -PIN_DIS) & H.pin_t.notna().values & (H.pin_lag_h > 0).values
rep("as coded (raw model, 6%), incl. b2b teams", sc, rawA)
rep("as coded, b2b teams removed (the b2b skip applies live)", sc & ~rawA.b2b.values, rawA)
rep("  of which the live blended ML ALREADY alerted at the open (duplicate)", sc & ~rawA.b2b.values & ml_q.values, rawA)
scb = A_ML.ok & (O_ML.ev.values < ML_THR) & (A_ML.ev.values >= ML_THR) & (dis_w >= -PIN_DIS) & H.pin_t.notna().values & (H.pin_lag_h > 0).values & ~A_ML.b2b.values
rep("consistent version: blended EV<4% at open, 4%+ when Pinnacle posts", scb, A_ML)

# ------------------------------------------------------------------------------------------------ 11. MAX_MOVE
hdr("11. MAX_MOVE caution (moneyline moved 5+ win-% pts against the bet since open): reachable only for non-opener bets")
mv5 = np.abs(nv(H.m60_home_ml, H.m60_away_ml) - H.mkt_open) * 100 >= 5
print(f"  games whose ML moved 5+ pts by +60 min: {int(np.nansum(mv5))} of {len(H)}; an opener-price bet (within 1.5 pts) can't trigger it, "
      "so it only applies to SECOND CHANCE bets.")

# ------------------------------------------------------------------------------------------------ live season counts
print("\n" + "=" * 130 + "\nLIVE 2026-27: how often each gate fired (state/alerts.csv, shot model rows; one row per game/market/model)\n" + "-" * 130)
A = pd.read_csv(os.path.join(HERE, "state", "alerts.csv"))
A["t"] = pd.to_datetime(A.alerted_at_et)
def reason(s):
    if pd.isna(s): return "BET (pushed)"
    s = str(s)
    for k, v in (("back-to-back", "SKIP_B2B"), ("Pinnacle", "Pinnacle disagrees"), ("one bet per game", "one bet per game"),
                 ("goalies", "goalie caution (removed Nov 1)"), ("disagree", "models disagree"), ("already bet", "already bet other side"),
                 ("opening number", "MOVED_SKIP"), ("against this side", "MAX_MOVE caution")):
        if k in s: return v
    return s[:40]
A["gate"] = A.skipped.map(reason)
for lab, sub in (("all shot-model rows since Oct 30", A[A.model == "xg"]), ("v3 rules (since 2026-11-02 11:08)", A[(A.model == "xg") & (A.t >= "2026-11-02 11:08")])):
    print(f"  {lab}:")
    g = sub.groupby("gate").agg(n=("game_id", "size"), graded=("result", lambda r: r.isin(["W", "L"]).sum()),
                                w=("result", lambda r: (r == "W").sum()), units=("profit", "sum"))
    for k, r in g.iterrows(): print(f"    {k:34s} {int(r.n):3d} rows, graded {int(r.graded)}: {int(r.w)}-{int(r.graded - r.w)}, {r.units:+.2f}u")
xs = A[A.model == "xg"]
dont = xs[xs.reminded_at_et.notna()].drop_duplicates(["game_id", "market"]) if "reminded_at_et" in xs else xs.iloc[:0]
print(f"  DON'T BET follow-ups sent: {len(dont)} game-markets; their results at the alert price: "
      + "; ".join(f"{r.home}/{r.away} {r.market} {r.side} {r.result} ({r.alerted_at_et[11:16]} -> DON'T BET {r.reminded_at_et[11:16]})" for r in dont.itertuples()))
rem = xs[xs.get("last_reminder_at_et", pd.Series(dtype=object)).notna()] if "last_reminder_at_et" in xs else xs.iloc[:0]
res = xs[xs.get("resumed_at_et", pd.Series(dtype=object)).notna()] if "resumed_at_et" in xs else xs.iloc[:0]
print(f"  REMINDER rows: {len(rem)}; BACK IN RANGE rows: {len(res)}; second-chance alerts: {int(xs.second_chance.astype(str).eq('True').sum())}")
for f, lab in (("market_moves.csv", "'market agrees' info notes"), ("line_jumps.csv", "line jumps logged")):
    p = os.path.join(HERE, "state", f)
    if os.path.exists(p): print(f"  {lab}: {len(pd.read_csv(p))}")

# ------------------------------------------------------------------------------------------------ verdicts (hand-written Nov 4, 2026
# from the numbers above; re-read them if the data or rules change)
print("""
==================================================================================================================================
VERDICTS (written Nov 4, 2026 from the tables above; all records 2021-22..2025-26 at DK prices you could actually take)
----------------------------------------------------------------------------------------------------------------------------------
SKIP_B2B            PL: KEEP (blocked 137 bets -37.3u, 4/5 seasons negative). ML: no longer earns its place under the live blend +
                    travel adj. (blocked 77 bets +0.9u; the quoted -40u is a puck-line-sized figure / raw model). CHANGE: puck line only.
Pinnacle at alert   KEEP (bettable; 27 bets -8.8u, small, 2 seasons with no cases).
Pinnacle DON'T BET  Quoted -42u (405 bets) is the raw model graded at DK's OPENER with Pinnacle's later price (look-ahead). Under the live
  follow-up         blend, at the price you could get when Pinnacle posts: blocked 187 bets +9.1u as coded (vs DK's opener), +0.2u on 124
                    if compared with DK's current price. Saves nothing. CHANGE (low stakes): compare Pinnacle with DK's CURRENT price, or
                    DROP; the real fix is to bet the opener at once (reminders) since waiting costs ~11u per 1,000 bets.
Overs only          KEEP (unders 1,096 bets -6.0u, 3/5 negative).
ML_THRESHOLD 4%     KEEP (2-4% band 783 bets +12.5u, 3/5 negative; 4-6% +49.5u).
THRESHOLD 6% (PL)   CHANGE to 9% (6-9% band 514 bets -11.1u, 4/5 negative; 9%+ 754 bets +90.2u). In-sample choice: re-test on 2026-27.
THRESHOLD 6% overs  KEEP (6-9% +19.9u, 0/5 negative).
MOVED_SKIP          PL and overs: KEEP (new moved-price bets halfway: PL 189 -10.5u, overs 49 -0.6u). ML: CHANGE: push moved-price
                    moneylines at blended EV 9%+ (new bets halfway: 50 bets +18.5u, 0/5 negative; EV 4%+ 266 bets +35.0u).
DON'T BET on EV     ML: CHANGE: don't stop an opener alert while the price is within 1.5 pts of the alert price (those 'below bar'
                    bets at halfway: 113 bets +26.0u, 4/5 positive). Overs moved toward us: KEEP the stop (101 bets -11.6u, 5/5 neg).
One bet per game    CHANGE: the live comparison (blended ML EV vs raw PL EV) picks the puck line 79% of the time and the dropped ML
                    legs made more (+57.3u on 470). Always the ML in those games +69.7u vs +54.2u as now (597 games).
Models disagree     KEEP (inert: 1 case in five seasons).  MAX_MOVE caution: inert (opener bets can't trigger it).
Goalie caution      already removed for opener bets (Nov 1).  ALERT_MODELS / OPEN_ONLY_LONGSHOTS: not re-tested (goals model).
""")
