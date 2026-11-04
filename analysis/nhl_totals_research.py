"""
NHL totals research (Nov 4, 2026). Analysis only: nothing here is imported by the live code.

Questions
  1. Where does the overs edge come from? Blind "bet every over" vs the model's overs, by line and over price; is it structural?
     Any structural rule is checked out of sample on SportsbookReview (SBR) 2011-12..2020-21.
  2. Starting goalies: once the starter is known (DK price 1 h before puck drop / SBR closing price), do goalie quality or a
     surprise starter give over/under edges, and does the price already move for them? Includes unders.
  3. Other features at the opener (rest, travel, recent xG / shot volume / goals, power play, early/late season, divisional):
     chosen on DK 2021-22..2023-24, checked on DK 2024-25..2025-26 and SBR 2011-12..2020-21.
  4. Timing: the overs edge at +15/+30/+60 min, halfway, game-day 10 AM, 3 h before and at the close.

Data (WORK = a copy of this repo with the gitignored files rebuilt; see analysis/rule_audit_nhl.py):
  WORK/_tmp/dk_holdout_{2022..2026}.csv   shot model walk-forward predictions, one-day lag, DK prices (rule_audit_nhl.py --build)
  WORK/_tmp/rule_audit_snaps.pkl          every hourly DK/Pinnacle snapshot (built by rule_audit_nhl.py)
  WORK/_tmp/oos_games.csv                 SBR lines + hockeyR xG + NHL starters 2011-23 (dev/oos_sbr_build.py)
  WORK/data/shots_hist.csv                ESPN shots (power-play attempts)
  NBA/analysis/travel_nhl_games.csv       rest days and time-zone moves (DK era)
  backtests/oos_sbr_bets.csv              the shot model's SBR overs (from dev/oos_sbr_backtest.py)
How WORK was built (Nov 4, 2026): a copy of this repo; data/box_hist.csv and data/shots_hist.csv re-fetched from ESPN with the repo's own
parsers (nhl_data.box, build_shots.shots); _tmp/dk_holdout_*.csv from analysis/rule_audit_nhl.py --build; _tmp/oos_games.csv from
dev/oos_sbr_build.py; DK/Pinnacle snapshots from nba-mixed-model data/odds_history/nhl/*.csv.gz; SBR starters from
data/external/nhl_box/goalies_2011_2023.csv; hockeyR xG from data/external/hockeyr.
Every bet is graded at the over/under price available at that moment; whole-number totals push (0 units).
SBR stores ONE total price, the under's; the over price is rebuilt (pair = 104.8% implied), as in backtests/OOS_SBR_RESULTS.md.

  python analysis/nhl_totals_research.py WORK NBA_REPO > analysis/nhl_totals_research_output.txt
"""
import os, sys, json, pickle, warnings
import numpy as np, pandas as pd
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.abspath(sys.argv[1]); NBA = os.path.abspath(sys.argv[2]); sys.path.insert(0, WORK)
import nhl_mixed_model as nm                                                          # noqa: E402

pd.set_option("display.width", 220)
DK_SEAS = (2022, 2023, 2024, 2025, 2026); TRAIN = (2022, 2023, 2024); TEST = (2025, 2026)
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def nv(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)
N_VARIANTS = []          # every rule/feature variant looked at, for the multiple-testing count


def grade(T, ov, un, total, over):
    """units for an over (over=True) or under bet at total line T and prices ov/un; pushes 0"""
    T = np.asarray(T, float); d = np.where(over, dec(ov), dec(un))
    res = np.where(total > T, 1, np.where(total < T, -1, 0)) * np.where(over, 1, -1)
    return np.where(res > 0, d - 1, np.where(res < 0, -1.0, 0.0)), res


def line(label, m, u, res, seas, seasons, count=True):
    m = np.asarray(m, bool) & ~np.isnan(u); n = int(m.sum())
    if count: N_VARIANTS.append(label)
    dec_ = res[m]; w = (dec_ > 0).sum(); l = (dec_ < 0).sum()
    per = [u[m & (seas == s)].sum() for s in seasons]
    print(f"  {label:60s} {n:5d} bets {w / max(w + l, 1):6.1%} {u[m].sum():+7.1f}u ({u[m].sum() / max(n, 1):+6.1%}) | "
          + " ".join(f"{x:+6.1f}" for x in per) + f"  neg {sum(x < 0 for x in per)}/{len(seasons)}")
    return n, u[m].sum()


def hdr(t, seasons):
    print("\n" + "=" * 140 + f"\n{t}\n" + "-" * 140 + f"\n  {'':60s} {'bets':>5s}      win%    units      ROI   | by season "
          + " ".join(f"{s - 1}-{str(s)[2:]}" for s in seasons))


# ============================================================================================== DK era data
H = pd.concat([pd.read_csv(os.path.join(WORK, "_tmp", f"dk_holdout_{s}.csv")) for s in DK_SEAS], ignore_index=True)
TN = pd.read_csv(os.path.join(NBA, "analysis", "travel_nhl_games.csv"))[["date", "home", "away", "h_rest", "a_rest", "a_tz_move", "h_tz_move"]]
H = H.merge(TN, on=["date", "home", "away"], how="left")
H = H[H.open_total.notna() & H.open_over_odds.notna() & H.open_under_odds.notna() & H.home_goals.notna() & H.lam_home_open.notna()]
H = H.sort_values(["date", "game_id"]).reset_index(drop=True)
H["t0"] = pd.to_datetime(H.t0, utc=True); H["tip"] = pd.to_datetime(H.tip, utc=True)
H["total"] = H.home_goals + H.away_goals
SEA = H.season.values; TOT = H.total.values

SN = pickle.load(open(os.path.join(WORK, "_tmp", "rule_audit_snaps.pkl"), "rb"))
DKT = SN[(SN.book == "draftkings") & SN.tot_pt.notna() & SN.ov.notna() & SN.un.notna()][["date", "home", "away", "t", "tot_pt", "ov", "un"]]
KEY = ["date", "home", "away"]


def dk_total_at(times):
    q = H[KEY].copy(); q["tq"] = pd.Series(times).reset_index(drop=True).values; q["tq"] = pd.to_datetime(q.tq, utc=True); q["_i"] = np.arange(len(H)); q = q.dropna(subset=["tq"])
    m = pd.merge_asof(q.sort_values("tq"), DKT.sort_values("t").rename(columns={"t": "tq"}), on="tq", by=KEY, direction="backward").set_index("_i")
    return (m.tot_pt.reindex(range(len(H))).values, m.ov.reindex(range(len(H))).values, m.un.reindex(range(len(H))).values)


def model_ou(lh, la, T):
    T = np.asarray(T, float); ok = ~np.isnan(T)
    po, pu, pp = nm.over_prob(np.asarray(lh, float), np.asarray(la, float), np.nan_to_num(T, nan=6.0), nm.H_OT_DEFAULT, {})
    po[~ok] = np.nan; pu[~ok] = np.nan; pp[~ok] = np.nan
    return po, pu, pp


print(f"DK era: {len(H)} games with DK opening total and a shot-model prediction ({', '.join(f'{s}: {(SEA == s).sum()}' for s in DK_SEAS)})")
print(f"Opening total lines: {H.open_total.value_counts().sort_index().to_dict()}")

# ============================================================================================== 1. structural vs model
T0, OV0, UN0 = H.open_total.values, H.open_over_odds.values, H.open_under_odds.values
po0, pu0, pp0 = model_ou(H.lam_home_open, H.lam_away_open, T0)
ev_o = po0 * dec(OV0) + pp0 - 1; ev_u = pu0 * dec(UN0) + pp0 - 1
u_over, r_over = grade(T0, OV0, UN0, TOT, True); u_under, r_under = grade(T0, OV0, UN0, TOT, False)
mkt_o = nv(OV0, UN0)                                       # no-vig chance of over (pushes ignored)
model_over = (ev_o >= 0.06) & (ev_o >= ev_u)
hdr("1a. BLIND OVERS vs THE MODEL'S OVERS at DK's opener (all games)", DK_SEAS)
line("blind: every over", np.ones(len(H), bool), u_over, r_over, SEA, DK_SEAS)
line("blind: every under", np.ones(len(H), bool), u_under, r_under, SEA, DK_SEAS)
line("model overs, EV 6%+ (live rule)", model_over, u_over, r_over, SEA, DK_SEAS)
for T in (5.5, 6.0, 6.5, 7.0):
    line(f"blind overs at {T}", T0 == T, u_over, r_over, SEA, DK_SEAS)
    line(f"   model overs at {T}", model_over & (T0 == T), u_over, r_over, SEA, DK_SEAS)
bands = [(-1000, -131), (-130, -116), (-115, -101), (100, 119), (120, 1000)]
for lo, hi in bands:
    b = (OV0 >= lo) & (OV0 <= hi)
    line(f"blind overs, over price {lo:+d}..{hi:+d}", b, u_over, r_over, SEA, DK_SEAS)
    line(f"   model overs in that price band", model_over & b, u_over, r_over, SEA, DK_SEAS)
print("\n  Over rate vs DK's no-vig over chance, by line (decided games only):")
dcd = r_over != 0
for T in (5.5, 6.0, 6.5):
    m = (T0 == T) & dcd
    print(f"    {T}: {m.sum():5d} games, over won {(r_over[m] > 0).mean():.1%}, DK no-vig said {mkt_o[m].mean():.1%}")
# bucket-matched baseline: what would blind overs have made in the same line x price cells as the model's picks?
cell = pd.Series(list(zip(T0, pd.cut(OV0, [-1000, -131, -116, -101, 119, 1000]).astype(str))))
cell_roi = pd.Series(u_over).groupby(cell).mean()
exp_u = cell.map(cell_roi).values
print(f"\n  Model overs: {model_over.sum()} bets {u_over[model_over].sum():+.1f}u; blind overs in the SAME line x price cells would expect "
      f"{exp_u[model_over].sum():+.1f}u -> the model adds {u_over[model_over].sum() - exp_u[model_over].sum():+.1f}u beyond the cell")
# logistic: over ~ offset(logit market) + b * (logit model - logit market)
from scipy.optimize import minimize
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
def logit_fit(y, off, X):
    """logistic regression with an offset (Newton-Raphson); returns coefficients and standard errors"""
    X = np.column_stack([np.ones(len(y)), X]); b = np.zeros(X.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-(off + X @ b))); W = p * (1 - p)
        Hs = X.T @ (X * W[:, None]); step = np.linalg.solve(Hs, X.T @ (y - p)); b += step
        if np.abs(step).max() < 1e-8: break
    return b, np.sqrt(np.diag(np.linalg.inv(Hs)))
pmo = po0 / np.clip(po0 + pu0, 1e-9, None)
m = dcd & ~np.isnan(pmo)
b, se = logit_fit((r_over[m] > 0).astype(float), lg(mkt_o[m]), lg(pmo[m]) - lg(mkt_o[m]))
print(f"  Logistic over ~ DK no-vig (offset) + model's disagreement: intercept {b[0]:+.3f} (se {se[0]:.3f}), "
      f"model weight {b[1]:+.3f} (se {se[1]:.3f}) [1 = trust the model fully, 0 = no information]")
for s in DK_SEAS:
    mm = m & (SEA == s); bs, ss = logit_fit((r_over[mm] > 0).astype(float), lg(mkt_o[mm]), lg(pmo[mm]) - lg(mkt_o[mm]))
    print(f"    {s - 1}-{str(s)[2:]}: intercept {bs[0]:+.3f}  model weight {bs[1]:+.3f} (se {ss[1]:.3f})")
# the model's bias: average model total minus the line
print(f"  Model expected total minus the line: mean {np.nanmean(H.pred_total_open - T0):+.2f} goals; actual minus line {np.mean(TOT - T0):+.2f}")
print("  Model over chance vs result, by model over chance (decided):")
for lo, hi in ((0, .45), (.45, .5), (.5, .55), (.55, .6), (.6, 1)):
    mm = m & (pmo >= lo) & (pmo < hi)
    print(f"    model {lo:.2f}-{hi:.2f}: {mm.sum():5d} games, over won {(r_over[mm] > 0).mean():.1%}, DK no-vig {mkt_o[mm].mean():.1%}, "
          f"blind over units {u_over[mm].sum():+.1f}")

# 1b. structural rules and the model's own variants
hdr("1b. CANDIDATE STRUCTURAL / MODEL RULES at DK's opener", DK_SEAS)
line("overs at 5.5 priced -115 or longer (plus side)", (T0 == 5.5) & (OV0 >= -115), u_over, r_over, SEA, DK_SEAS)
line("overs at 5.5 priced +100 or longer", (T0 == 5.5) & (OV0 >= 100), u_over, r_over, SEA, DK_SEAS)
line("overs at 6.5 (any price)", T0 == 6.5, u_over, r_over, SEA, DK_SEAS)
line("overs, DK no-vig over chance under 47%", mkt_o < 0.47, u_over, r_over, SEA, DK_SEAS)
line("overs, DK no-vig over chance under 45%", mkt_o < 0.45, u_over, r_over, SEA, DK_SEAS)
for bar in (0.03, 0.06, 0.09, 0.12):
    line(f"model overs EV {bar:.0%}+", (ev_o >= bar) & (ev_o >= ev_u), u_over, r_over, SEA, DK_SEAS)
line("model overs EV 6%+ AND model total > line", model_over & (H.pred_total_open.values > T0), u_over, r_over, SEA, DK_SEAS)
line("model overs EV 6%+ but model total <= line (price-driven)", model_over & (H.pred_total_open.values <= T0), u_over, r_over, SEA, DK_SEAS)

# ============================================================================================== SBR era
G = pd.read_csv(os.path.join(WORK, "_tmp", "oos_games.csv"))
G = G[G.match == 1].copy() if "match" in G else G
G["date"] = pd.to_datetime(G.date)
G = G.sort_values(["date", "game_id"]).reset_index(drop=True)
G["total"] = G.home_goals + G.away_goals
SB = G[G.open_total.notna() & G.open_under_odds.notna() & (G.open_total_ok == 1) & G.total.notna() & (G.season <= 2021)].reset_index(drop=True)
SB_SEAS = tuple(sorted(SB.season.unique()))
sT, sOV, sUN = SB.open_total.values, SB.open_over_odds.values, SB.open_under_odds.values
s_uo, s_ro = grade(sT, sOV, sUN, SB.total.values, True); s_uu, s_ru = grade(sT, sOV, sUN, SB.total.values, False)
sS = SB.season.values
hdr(f"1c. OUT OF SAMPLE: SBR openers {SB_SEAS[0] - 1}-{SB_SEAS[-1]} (over price rebuilt from the under price)", SB_SEAS)
line("blind: every over", np.ones(len(SB), bool), s_uo, s_ro, sS, SB_SEAS)
line("blind: every under", np.ones(len(SB), bool), s_uu, s_ru, sS, SB_SEAS)
for T in (5.0, 5.5, 6.0, 6.5):
    line(f"blind overs at {T}", sT == T, s_uo, s_ro, sS, SB_SEAS)
line("overs at 5.5, under priced -115 or shorter (over plus-ish)", (sT == 5.5) & (sUN <= -115), s_uo, s_ro, sS, SB_SEAS)
line("overs at 5.5, under -121 or shorter", (sT == 5.5) & (sUN <= -121), s_uo, s_ro, sS, SB_SEAS)
line("overs at 6.5 (any price)", sT == 6.5, s_uo, s_ro, sS, SB_SEAS)
smk = nv(sOV, sUN)
line("overs, no-vig over chance under 47%", smk < 0.47, s_uo, s_ro, sS, SB_SEAS)
line("overs, no-vig over chance under 45%", smk < 0.45, s_uo, s_ro, sS, SB_SEAS)
OB = pd.read_csv(os.path.join(HERE, "backtests", "oos_sbr_bets.csv")); OB = OB[OB.rule == "Overs @open"].copy()
OB["date"] = pd.to_datetime(OB.date)
SBm = SB.merge(OB[["date", "home", "away", "ev"]].rename(columns={"ev": "model_ev"}), on=["date", "home", "away"], how="left")
mo = SBm.model_ev.notna().values
line("shot model's SBR overs (team-only model, EV 6%+)", mo, s_uo, s_ro, sS, SB_SEAS)
cellS = pd.Series(list(zip(sT, pd.cut(sOV, [-1000, -131, -116, -101, 119, 1000]).astype(str))))
expS = cellS.map(pd.Series(s_uo).groupby(cellS).mean()).values
print(f"  SBR model overs: {mo.sum()} bets {s_uo[mo].sum():+.1f}u; blind overs in the same line x price cells expect {expS[mo].sum():+.1f}u "
      f"-> model adds {s_uo[mo].sum() - expS[mo].sum():+.1f}u")
sd = s_ro != 0
for T in (5.0, 5.5, 6.0, 6.5):
    mm = (sT == T) & sd
    print(f"    {T}: {mm.sum():5d} games, over won {(s_ro[mm] > 0).mean():.1%}, no-vig said {smk[mm].mean():.1%}")

# ============================================================================================== 4. timing (before goalies: uses only opener info)
hdr("4. TIMING: the overs rule (shot model, EV 6%+) at later DK prices", DK_SEAS)
tip = H.tip
times = {"open": H.t0, "+15 min": H.t0 + pd.Timedelta(minutes=15), "+30 min": H.t0 + pd.Timedelta(minutes=30),
         "+60 min": H.t0 + pd.Timedelta(minutes=60), "+3 h": H.t0 + pd.Timedelta(hours=3), "halfway": H.t0 + (tip - H.t0) / 2,
         "game day 10 AM ET": pd.to_datetime(H.date + " 10:00").dt.tz_localize("America/New_York").dt.tz_convert("UTC"),
         "3 h before": tip - pd.Timedelta(hours=3), "1 h before": tip - pd.Timedelta(hours=1), "close": tip - pd.Timedelta(minutes=1)}
PRE = {}
for lab, tt in times.items():
    tt = tt.where(tt >= H.t0, H.t0)
    T, ov, un = dk_total_at(tt); PRE[lab] = (T, ov, un)
    po, pu, pp = model_ou(H.lam_home_open, H.lam_away_open, T)
    evo = po * dec(ov) + pp - 1; evu = pu * dec(un) + pp - 1
    u, r = grade(T, ov, un, TOT, True)
    line(f"{lab:18s}: rule re-applied (EV 6%+ at this price)", (evo >= 0.06) & (evo >= evu), u, r, SEA, DK_SEAS)
    same = model_over & (T == T0)
    line(f"{lab:18s}: opener picks, same line still up, at this price", same, u, r, SEA, DK_SEAS)
    print(f"  {'':18s}  opener picks whose line moved off by then: {(model_over & (T != T0) & ~np.isnan(T)).sum()} "
          f"(up {(model_over & (T > T0)).sum()}, down {(model_over & (T < T0)).sum()})")

# ============================================================================================== goalie quality (both eras)
def goalie_quality(df, gcol_h, gcol_a, xg_h, xg_a, gl_h, gl_a, k=30, last=60):
    """rolling goals saved above expected per start for each goalie, from starts strictly before the game date
    (shrunk: sum over the last `last` starts / (n + k)). Returns per-game q for the actual starters and the expected (gmix) starters."""
    rows = []
    for r in df.itertuples():
        for side, g, xa, ga in (("h", getattr(r, gcol_h), getattr(r, xg_a), getattr(r, gl_a)), ("a", getattr(r, gcol_a), getattr(r, xg_h), getattr(r, gl_h))):
            if pd.isna(g): continue
            rows.append((r.Index, side, int(g), r.date, xa - ga))
    L = pd.DataFrame(rows, columns=["i", "side", "g", "date", "sv"]).sort_values(["g", "date"])
    L["date"] = pd.to_datetime(L.date)
    # cumulative over starts strictly before this start's date
    L["n"] = L.groupby("g").cumcount()
    L["cs"] = L.groupby("g").sv.transform(lambda v: v.rolling(last, min_periods=1).sum().shift().fillna(0))
    L["cn"] = L.n.clip(upper=last)
    L["q"] = L.cs / (L.cn + k)
    hist = {g: (d.date.values, d.q.values, d.sv.values) for g, d in L.groupby("g")}
    def q_before(g, date):
        """quality of goalie g using starts before `date` (for expected starters who may not start this game)"""
        h = hist.get(int(g))
        if h is None: return 0.0
        j = np.searchsorted(h[0], np.datetime64(date)) - 1
        if j < 0: return 0.0
        s = h[2][max(0, j - last + 1): j + 1].sum(); n = min(j + 1, last)
        return s / (n + k)
    qa = L.pivot_table(index="i", columns="side", values="q")
    return qa, q_before


def add_goalie_feats(df, q_before, qa, date_col="date"):
    df = df.copy()
    df["q_act_h"] = qa["h"].reindex(df.index).values; df["q_act_a"] = qa["a"].reindex(df.index).values
    for side in ("h", "a"):
        col = "home_gmix" if side == "h" else "away_gmix"; gcol = "home_goalie" if side == "h" else "away_goalie"
        qe, share = [], []
        for r in df[[col, gcol, date_col]].itertuples(index=False):
            try: mix = {int(float(k)): v for k, v in json.loads(r[0]).items()}
            except Exception: mix = {}
            tot = sum(mix.values()) or 1
            qe.append(sum(w / tot * q_before(g, r[2]) for g, w in mix.items()) if mix else np.nan)
            share.append(mix.get(int(r[1]), 0.0) / tot if mix and not pd.isna(r[1]) else np.nan)
        df[f"q_exp_{side}"] = qe; df[f"share_{side}"] = share
    df["q_act"] = df.q_act_h + df.q_act_a; df["q_exp"] = df.q_exp_h + df.q_exp_a
    df["q_surprise"] = df.q_act - df.q_exp                       # + = better goalies than expected at the open -> fewer goals
    df["backup"] = ((df.share_h < 0.4) | (df.share_a < 0.4)).astype(int)
    return df


Hd = H.copy(); Hd["date"] = pd.to_datetime(Hd.date)
qaD, qbD = goalie_quality(Hd, "home_goalie", "away_goalie", "home_xg", "away_xg", "home_goals", "away_goals")
# history before 2021-22 for goalies: include the 2019-20/2020-21 training games so early-season quality isn't empty
TG = pd.read_csv(os.path.join(WORK, "data", "training_games.csv")); TG["date"] = pd.to_datetime(TG.date)
TG = TG.sort_values("date").reset_index(drop=True)
qaT, qbT = goalie_quality(TG, "home_goalie", "away_goalie", "home_xg", "away_xg", "home_goals", "away_goals")
TG = add_goalie_feats(TG, qbT, qaT)
Hd = Hd.merge(TG[["game_id", "q_act", "q_exp", "q_surprise", "backup", "q_act_h", "q_act_a", "share_h", "share_a"]], on="game_id", how="left")
# SBR era: starters from the official NHL box scores (data/external/nhl_box); expected starter = share of the team's last 10 starts
GB = pd.read_csv(os.path.join(WORK, "data", "external", "nhl_box", "goalies_2011_2023.csv"))
GB = GB[GB.starter == 1][["game_id", "date", "team", "is_home", "goalie_id"]].sort_values(["team", "date"])
mix = {}
for t, g in GB.groupby("team"):
    ids = g.goalie_id.values
    for j, gid in enumerate(g.game_id.values):
        last = ids[max(0, j - 10):j]
        mix[gid, g.is_home.values[j]] = json.dumps({str(int(k)): float((last == k).mean()) for k in set(last)}) if len(last) else "{}"
st = GB.set_index(["game_id", "is_home"]).goalie_id
G["home_goalie"] = [st.get((i, 1), np.nan) for i in G.game_id]; G["away_goalie"] = [st.get((i, 0), np.nan) for i in G.game_id]
G["home_gmix"] = [mix.get((i, 1), "{}") for i in G.game_id]; G["away_gmix"] = [mix.get((i, 0), "{}") for i in G.game_id]
Gq = G[G.total.notna() & G.home_xg.notna() & G.home_goalie.notna() & G.away_goalie.notna()].copy().reset_index(drop=True)
qaS, qbS = goalie_quality(Gq, "home_goalie", "away_goalie", "home_xg", "away_xg", "home_goals", "away_goals")
Gq = add_goalie_feats(Gq, qbS, qaS)

# ============================================================================================== 2. goalies
hdr("2a. GOALIES, DK era: price 1 h before puck drop (starters known), model with the ACTUAL starters (+ actual lineup)", DK_SEAS)
Tp, ovp, unp = PRE["1 h before"]
po, pu, pp = model_ou(H.lam_home, H.lam_away, Tp)
evo_p = po * dec(ovp) + pp - 1; evu_p = pu * dec(unp) + pp - 1
uo_p, ro_p = grade(Tp, ovp, unp, TOT, True); uu_p, ru_p = grade(Tp, ovp, unp, TOT, False)
po_o, pu_o, pp_o = model_ou(H.lam_home_open, H.lam_away_open, Tp)
evo_po = po_o * dec(ovp) + pp_o - 1; evu_po = pu_o * dec(unp) + pp_o - 1
line("blind overs at the 1-h price", ~np.isnan(Tp), uo_p, ro_p, SEA, DK_SEAS)
line("model (actual starters) overs EV 6%+", (evo_p >= 0.06) & (evo_p >= evu_p), uo_p, ro_p, SEA, DK_SEAS)
line("model (actual starters) unders EV 6%+", (evu_p >= 0.06) & (evu_p > evo_p), uu_p, ru_p, SEA, DK_SEAS)
line("model (opener info only) overs EV 6%+ at the 1-h price", (evo_po >= 0.06) & (evo_po >= evu_po), uo_p, ro_p, SEA, DK_SEAS)
line("model (opener info only) unders EV 6%+ at the 1-h price", (evu_po >= 0.06) & (evu_po > evo_po), uu_p, ru_p, SEA, DK_SEAS)
chg = (np.abs(H.lam_home + H.lam_away - H.lam_home_open - H.lam_away_open) >= 0.15).values
line("  goalie/lineup changed the model total 0.15+: actual-starter overs", chg & (evo_p >= 0.06) & (evo_p >= evu_p), uo_p, ro_p, SEA, DK_SEAS)
line("  actual-starter overs NOT already bet at the opener (new bets)", (evo_p >= 0.06) & (evo_p >= evu_p) & ~model_over, uo_p, ro_p, SEA, DK_SEAS)
line("  same, goalie/lineup changed the model total 0.15+", chg & (evo_p >= 0.06) & (evo_p >= evu_p) & ~model_over, uo_p, ro_p, SEA, DK_SEAS)
line("  same, EV 9%+", (evo_p >= 0.09) & (evo_p >= evu_p) & ~model_over, uo_p, ro_p, SEA, DK_SEAS)
line("  opener overs bet AND still EV 6%+ with actual starters at the 1-h price", (evo_p >= 0.06) & (evo_p >= evu_p) & model_over, uo_p, ro_p, SEA, DK_SEAS)
line("  opener overs whose actual-starter EV at the 1-h price fell under 0 (graded at the OPENER)", model_over & (evo_p < 0), u_over, r_over, SEA, DK_SEAS)
line("  goalie/lineup changed the model total 0.15+: actual-starter unders", chg & (evu_p >= 0.06) & (evu_p > evo_p), uu_p, ru_p, SEA, DK_SEAS)

qs = Hd.q_surprise.values; qa_ = Hd.q_act.values; bk = Hd.backup.values == 1
move = Tp - T0 + (nv(ovp, unp) - mkt_o) * 2          # crude: line change + price change (~0.5 goal per 25 pts of over chance)
okq = ~np.isnan(qs) & ~np.isnan(Tp)
print(f"\n  Does the price react to the starters? corr(goalie surprise, open->1h total move) = {np.corrcoef(qs[okq], move[okq])[0, 1]:+.3f}; "
      f"corr(goalie surprise, actual goals minus 1-h line) = {np.corrcoef(qs[okq], (TOT - Tp)[okq])[0, 1]:+.3f}; "
      f"corr(starters' quality, goals minus 1-h line) = {np.corrcoef(qa_[okq & ~np.isnan(qa_)], (TOT - Tp)[okq & ~np.isnan(qa_)])[0, 1]:+.3f}")
for lab, mm in (("backup / unexpected starter (share < 40%) in net", bk), ("both expected starters", ~bk & ~np.isnan(Hd.share_h.values))):
    mm = mm & okq
    print(f"    {lab:48s}: {mm.sum():5d} games, total moved open->1h {np.nanmean(move[mm]):+.3f}, goals minus 1-h line {np.nanmean((TOT - Tp)[mm]):+.3f}, "
          f"over won {(ro_p[mm] > 0).sum() / max((ro_p[mm] != 0).sum(), 1):.1%}")
qcut = np.nanquantile(qs[okq], [0.2, 0.8]); acut = np.nanquantile(Hd[["q_act_h", "q_act_a"]].values, [0.33, 0.67])
strong2 = (Hd.q_act_h.values >= acut[1]) & (Hd.q_act_a.values >= acut[1]); weak2 = (Hd.q_act_h.values <= acut[0]) & (Hd.q_act_a.values <= acut[0])
line("overs: goalies much WORSE than expected (surprise bottom 20%)", okq & (qs <= qcut[0]), uo_p, ro_p, SEA, DK_SEAS)
line("unders: goalies much BETTER than expected (surprise top 20%)", okq & (qs >= qcut[1]), uu_p, ru_p, SEA, DK_SEAS)
line("overs: a backup/unexpected starter in net", okq & bk, uo_p, ro_p, SEA, DK_SEAS)
line("unders: two strong starters (both top third)", okq & strong2, uu_p, ru_p, SEA, DK_SEAS)
line("overs: two weak starters (both bottom third)", okq & weak2, uo_p, ro_p, SEA, DK_SEAS)
line("unders: two strong starters AND model (actual) EV 3%+ under", okq & strong2 & (evu_p >= 0.03), uu_p, ru_p, SEA, DK_SEAS)
line("overs at the OPENER: goalies worse than expected (known only later)", okq & (qs <= qcut[0]), u_over, r_over, SEA, DK_SEAS, count=False)

hdr("2b. GOALIES, SBR era: CLOSING price (starters known), out of sample", SB_SEAS)
GS = Gq[Gq.close_total.notna() & Gq.close_under_odds.notna() & (Gq.close_total_ok == 1) & (Gq.season <= 2021)].reset_index(drop=True)
cT, cOV, cUN = GS.close_total.values, GS.close_over_odds.values, GS.close_under_odds.values
cuo, cro = grade(cT, cOV, cUN, GS.total.values, True); cuu, cru = grade(cT, cOV, cUN, GS.total.values, False)
gS = GS.season.values; qsS = GS.q_surprise.values; okS = ~np.isnan(qsS)
qcS = np.nanquantile(qsS[okS], [0.2, 0.8]); acS = np.nanquantile(GS[["q_act_h", "q_act_a"]].values, [0.33, 0.67])
st2 = (GS.q_act_h.values >= acS[1]) & (GS.q_act_a.values >= acS[1]); wk2 = (GS.q_act_h.values <= acS[0]) & (GS.q_act_a.values <= acS[0])
bkS = GS.backup.values == 1
line("blind overs at the close", np.ones(len(GS), bool), cuo, cro, gS, SB_SEAS)
line("overs: goalies much WORSE than expected (bottom 20%)", okS & (qsS <= qcS[0]), cuo, cro, gS, SB_SEAS)
line("unders: goalies much BETTER than expected (top 20%)", okS & (qsS >= qcS[1]), cuu, cru, gS, SB_SEAS)
line("overs: a backup/unexpected starter in net", okS & bkS, cuo, cro, gS, SB_SEAS)
line("unders: two strong starters (both top third)", okS & st2, cuu, cru, gS, SB_SEAS)
line("overs: two weak starters (both bottom third)", okS & wk2, cuo, cro, gS, SB_SEAS)
oT = GS.open_total.values; mvS = (cT - oT) + (nv(cOV, cUN) - nv(GS.open_over_odds.values, GS.open_under_odds.values)) * 2
okm = okS & ~np.isnan(mvS)
print(f"  corr(goalie surprise, open->close total move) = {np.corrcoef(qsS[okm], mvS[okm])[0, 1]:+.3f}; "
      f"corr(surprise, goals minus closing line) = {np.corrcoef(qsS[okm], (GS.total.values - cT)[okm])[0, 1]:+.3f}")
for lab, mm in (("backup / unexpected starter", bkS), ("both expected starters", ~bkS & ~np.isnan(GS.share_h.values))):
    mm = mm & okm
    print(f"    {lab:30s}: {mm.sum():5d} games, total moved open->close {np.nanmean(mvS[mm]):+.3f}, goals minus close {np.nanmean((GS.total.values - cT)[mm]):+.3f}")

# ============================================================================================== 3. other features at the opener
def team_feats(df, xgh, xga, atth, atta, extra=None):
    """per game: rest (from the schedule), and both teams' last-10 vs season-to-date form using games through 2 days before
    (the opener is posted ~31 h ahead: yesterday's games are not known)."""
    rows = []
    for r in df.itertuples():
        for side, t, gf, ga, xf, xa, af, aa in (("h", r.home, r.home_goals, r.away_goals, getattr(r, xgh), getattr(r, xga), getattr(r, atth), getattr(r, atta)),
                                                ("a", r.away, r.away_goals, r.home_goals, getattr(r, xga), getattr(r, xgh), getattr(r, atta), getattr(r, atth))):
            d = dict(i=r.Index, side=side, season=r.season, date=r.date, team=t, tot=gf + ga, xg=xf + xa, att=af + aa)
            if extra is not None: d["pp"] = extra[side][r.Index]
            rows.append(d)
    L = pd.DataFrame(rows).sort_values(["team", "date"]); L["date"] = pd.to_datetime(L.date)
    L["rest"] = L.groupby("team").date.diff().dt.days
    L["gnum"] = L.groupby(["season", "team"]).cumcount()
    out = {}
    cols = ["tot", "xg", "att"] + (["pp"] if extra is not None else [])
    for (s, t), g in L.groupby(["season", "team"]):
        g = g.sort_values("date"); dts = g.date.values
        for c in cols:
            v = g[c].values; cs = np.concatenate([[0], np.cumsum(v)])
            for j, (ix, dt_) in enumerate(zip(g.index, dts)):
                k = np.searchsorted(dts, dt_ - np.timedelta64(1, "D"), side="left")     # games strictly before yesterday
                if k < 6: out[(ix, c)] = np.nan; continue
                season_avg = cs[k] / k; last10 = (cs[k] - cs[max(0, k - 10)]) / min(k, 10)
                out[(ix, c)] = last10 - season_avg
                out[(ix, c + "_lvl")] = season_avg
    for c in cols:
        L[f"{c}_form"] = [out.get((ix, c), np.nan) for ix in L.index]
        L[f"{c}_lvl"] = [out.get((ix, c + "_lvl"), np.nan) for ix in L.index]
    F = pd.DataFrame(index=df.index)
    for c in ["rest", "gnum"] + [f"{c}_form" for c in cols] + [f"{c}_lvl" for c in cols]:
        pv = L.pivot_table(index="i", columns="side", values=c); F[f"h_{c}"] = pv["h"]; F[f"a_{c}"] = pv["a"]
    return F


DIV4 = {"Atlantic": "bos buf det fla mtl ott tb tor", "Metro": "car cbj nj nyi nyr phi pit wsh",
        "Central": "chi col dal min nsh stl wpg uta", "Pacific": "ana cgy edm la sj sea van vgk ari"}
DIV = {t: d for d, ts in DIV4.items() for t in ts.split()}
def divisional(df):
    """same division (4-division NHL from 2013-14; Arizona/Utah Central from 2021-22); NaN before 2013-14 and in 2020-21"""
    def dv(t, season):
        if t in ("ari", "uta"): return "Central" if season >= 2022 else "Pacific"
        return DIV.get(t)
    d = np.array([float(dv(h, s) == dv(a, s)) if (s >= 2014 and s != 2021) else np.nan for h, a, s in zip(df.home, df.away, df.season)])
    return pd.Series(d, index=df.index)


# power-play attempts per game (DK era, ESPN shots)
SH = pd.read_csv(os.path.join(WORK, "data", "shots_hist.csv"), usecols=["game_id", "team", "strength"], low_memory=False)
ppg = SH[SH.strength.astype(str).str.lower().isin(["power-play", "short-handed"])].groupby(["game_id", "team"]).size()
ppH = {"h": {}, "a": {}}
for i, r in H[["game_id", "home", "away"]].iterrows():
    ppH["h"][i] = ppg.get((r.game_id, r.home), 0) + ppg.get((r.game_id, r.away), 0); ppH["a"][i] = ppH["h"][i]
FD = team_feats(H, "home_xg", "away_xg", "home_att", "away_att", extra=ppH)
G2 = SB.copy()
HX = pd.read_csv(os.path.join(WORK, "data", "external", "hockeyr", "team_game_xg_2010_2023.csv.gz"), usecols=["game_id", "is_home", "xg_pp_for", "xg_pp_against"])
pps = HX[HX.is_home == 1].set_index("game_id")
G2["ppx"] = (pps.xg_pp_for + pps.xg_pp_against).reindex(G2.game_id).values
ppS = {"h": dict(zip(G2.index, G2.ppx)), "a": dict(zip(G2.index, G2.ppx))}
FS = team_feats(G2, "home_xg", "away_xg", "home_att", "away_att", extra=ppS)


def build_X(df, F):
    X = pd.DataFrame(index=df.index)
    X["b2b_any"] = ((F.h_rest == 1) | (F.a_rest == 1)).astype(float)
    X["b2b_both"] = ((F.h_rest == 1) & (F.a_rest == 1)).astype(float)
    X["rested_both"] = ((F.h_rest >= 3) & (F.a_rest >= 3)).astype(float)
    X["goals_form"] = F.h_tot_form + F.a_tot_form
    X["xg_form"] = F.h_xg_form + F.a_xg_form
    X["att_form"] = F.h_att_form + F.a_att_form
    X["xg_level"] = F.h_xg_lvl + F.a_xg_lvl
    X["goals_level"] = F.h_tot_lvl + F.a_tot_lvl
    X["pp_level"] = F.h_pp_lvl + F.a_pp_lvl
    X["early"] = ((F.h_gnum < 15) | (F.a_gnum < 15)).astype(float)
    X["late"] = (pd.to_datetime(df.date).dt.month.isin([3, 4])).astype(float)
    X["divisional"] = divisional(df)
    return X


XD = build_X(H, FD); XS = build_X(SB, FS)
XD["west_travel"] = (-H.a_tz_move).clip(lower=0).fillna(0).values; XD["east_travel"] = H.a_tz_move.clip(lower=0).fillna(0).values
FEATS = list(XD.columns)
hdr("3. OTHER FEATURES at DK's opener: does the feature predict the over beyond DK's price? (logistic, DK no-vig as offset)", DK_SEAS)
print("  Coefficient per 1 SD of the feature (binary: per 1). Choose on 2021-24; check on 2024-26 (DK) and SBR 2011-21 (opener).")
print(f"  {'feature':16s} {'train 21-24':>18s} {'test 24-26':>18s} {'SBR 11-21':>18s}   over-bet units when the feature points over (train / test / SBR)")
ydk = (r_over > 0).astype(float); dk_ok = r_over != 0
ysb = (s_ro > 0).astype(float); sb_ok = s_ro != 0
res3 = []
for f in FEATS:
    x = XD[f].values.astype(float); bin_ = set(np.unique(x[~np.isnan(x)])) <= {0.0, 1.0}
    mu, sd_ = (0, 1) if bin_ else (np.nanmean(x[np.isin(SEA, TRAIN)]), np.nanstd(x[np.isin(SEA, TRAIN)]))
    out = []
    for nm_, msk, y, off, xx in (("train", dk_ok & np.isin(SEA, TRAIN), ydk, lg(mkt_o), x), ("test", dk_ok & np.isin(SEA, TEST), ydk, lg(mkt_o), x),
                                 ("sbr", sb_ok, ysb, lg(smk), XS[f].values.astype(float) if f in XS else np.full(len(SB), np.nan))):
        z = (xx - mu) / sd_ if not bin_ else xx
        mm = msk & ~np.isnan(z) & ~np.isnan(off)
        if mm.sum() < 200: out.append((np.nan, np.nan)); continue
        b, se = logit_fit(y[mm], off[mm], z[mm]); out.append((b[1], se[1]))
    sgn = np.sign(out[0][0]) if not np.isnan(out[0][0]) else 0
    def units(u, msk, xx):
        z = (xx - mu) / sd_ if not bin_ else xx
        sel = msk & (((z > 0.5) if not bin_ else (z == 1)) if sgn > 0 else ((z < -0.5) if not bin_ else (z == 1)))
        return u[sel].sum(), int(sel.sum())
    ut = units(u_over if sgn > 0 else u_under, np.isin(SEA, TRAIN), x); ue = units(u_over if sgn > 0 else u_under, np.isin(SEA, TEST), x)
    us = units(s_uo if sgn > 0 else s_uu, np.ones(len(SB), bool), XS[f].values.astype(float)) if f in XS else (np.nan, 0)
    N_VARIANTS.append(f"feature {f}")
    fmt = lambda t: f"{t[0]:+.3f} ({t[1]:.3f})" if not np.isnan(t[0]) else "      n/a       "
    print(f"  {f:16s} {fmt(out[0]):>18s} {fmt(out[1]):>18s} {fmt(out[2]):>18s}   {'over ' if sgn > 0 else 'under'} "
          f"{ut[0]:+6.1f}u/{ut[1]} | {ue[0]:+6.1f}u/{ue[1]} | {us[0]:+6.1f}u/{us[1]}")
    res3.append((f, out))
print("  (z = coef/se; |z| >= 2 in train AND same sign in both checks would count as a lead.)")
leads = [f for f, o in res3 if not np.isnan(o[0][0]) and abs(o[0][0] / o[0][1]) >= 2 and np.sign(o[1][0]) == np.sign(o[0][0])
         and (np.isnan(o[2][0]) or np.sign(o[2][0]) == np.sign(o[0][0]))]
print(f"  Leads passing train |z|>=2 and same sign in both checks: {leads or 'none'}")

# 3b. the leads added to the model's overs (filter), chosen on train
hdr("3b. LEADS as filters on the live overs rule (model overs EV 6%+ at the opener)", DK_SEAS)
line("live overs rule (reference)", model_over, u_over, r_over, SEA, DK_SEAS, count=False)
for f in leads:
    x = XD[f].values.astype(float); o = dict(res3)[f]; sgn = np.sign(o[0][0])
    bin_ = set(np.unique(x[~np.isnan(x)])) <= {0.0, 1.0}
    against = (x == 1) if (bin_ and sgn < 0) else ((x == 0) if bin_ else (sgn * (x - np.nanmedian(x)) < 0))
    line(f"  live overs, drop when {f} points under", model_over & ~against, u_over, r_over, SEA, DK_SEAS)
    line(f"  dropped bets", model_over & against, u_over, r_over, SEA, DK_SEAS)

print(f"\nMultiple testing: {len(N_VARIANTS)} rule/feature variants printed with records above (plus the goalie correlations). "
      f"At 5% per test, ~{0.05 * len(N_VARIANTS):.0f} would look 'significant' by chance.")
