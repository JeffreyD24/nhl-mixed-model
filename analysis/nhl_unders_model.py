"""
NHL UNDERS: is there a dedicated model or rule that beats DraftKings on unders? (Nov 4, 2026; analysis only, nothing live uses it)

Design (written before looking at holdout results):
  - Target: the under wins at the line (pushes on whole-number lines count 0 units). Graded at DK prices available at bet time.
  - Market as prior: logistic regression of "under won" (decided games) with logit(DK no-vig under chance) as an OFFSET, so the
    features only have to explain what the price misses.
  - Choose on DK 2021-22..2023-24; report 2024-25..2025-26 untouched; replicate on SBR 2011-12..2020-21 (openers; closing price for
    goalie features) with the features that exist there.
  - Pre-registered candidate rules (U1-U7) plus one combined logistic model per timing (opener / post-confirmation).
  - CLV: did the closing total fall below the bet line (clv_points = line - close)?
Reuses all data built by analysis/nhl_totals_research.py (same WORK folder; see its header for how WORK was built).

  python analysis/nhl_unders_model.py WORK NBA_REPO > analysis/nhl_unders_model_output.txt
"""
import os, sys, io, runpy, contextlib, warnings
import numpy as np, pandas as pd
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    R = runpy.run_path(os.path.join(HERE, "nhl_totals_research.py"), run_name="totals_research")
H, SEA, TOT, T0, OV0, UN0 = R["H"], R["SEA"], R["TOT"], R["T0"], R["OV0"], R["UN0"]
dec, nv, grade, lg, logit_fit, model_ou, PRE = R["dec"], R["nv"], R["grade"], R["lg"], R["logit_fit"], R["model_ou"], R["PRE"]
FD, FS, XD, XS, Hd, SB, Gq = R["FD"], R["FS"], R["XD"], R["XS"], R["Hd"], R["SB"], R["Gq"]
DK_SEAS, TRAIN, TEST = R["DK_SEAS"], R["TRAIN"], R["TEST"]
SB_SEAS = tuple(sorted(SB.season.unique())); sS = SB.season.values
NV = []


def line(label, m, u, res, seas, seasons, clvp=None):
    m = np.asarray(m, bool) & ~np.isnan(u); n = int(m.sum()); NV.append(label)
    w, l = (res[m] > 0).sum(), (res[m] < 0).sum()
    per = [u[m & (seas == s)].sum() for s in seasons]
    tr = u[m & np.isin(seas, TRAIN)].sum() if seasons == DK_SEAS else np.nan
    te = u[m & np.isin(seas, TEST)].sum() if seasons == DK_SEAS else np.nan
    c = "" if clvp is None else f" clv {np.nanmean(clvp[m]):+.2f}g fell {np.nanmean(clvp[m] > 0):4.0%} rose {np.nanmean(clvp[m] < 0):4.0%}"
    split = f" [choose {tr:+6.1f} / holdout {te:+6.1f}]" if seasons == DK_SEAS else ""
    print(f"  {label:54s} {n:5d} {w / max(w + l, 1):6.1%} {u[m].sum():+7.1f}u ({u[m].sum() / max(n, 1):+6.1%}){split} | "
          + " ".join(f"{x:+5.1f}" for x in per) + f" neg {sum(x < 0 for x in per)}/{len(seasons)}" + c)


def hdr(t, seasons):
    print("\n" + "=" * 150 + f"\n{t}\n" + "-" * 150 + f"\n  {'':54s} {'bets':>5s}   win%   units     ROI   " +
          ("[choose 21-24 / holdout 24-26] " if seasons == DK_SEAS else "") + "| by season " + " ".join(f"{str(s)[2:]}" for s in seasons))


# ------------------------------------------------------------------ DK opener basics
u_un, r_un = grade(T0, OV0, UN0, TOT, False)
mkt_u = 1 - nv(OV0, UN0)
Tc, ovc, unc = PRE["close"]; clv_dk = T0 - Tc                         # + = closing total fell below our line (good for an under)
po0, pu0, pp0 = model_ou(H.lam_home_open, H.lam_away_open, T0)
pmu = pu0 / np.clip(po0 + pu0, 1e-9, None)                            # shot model's chance of under (given no push)
ev_model_u = pu0 * dec(UN0) + pp0 - 1; ev_model_o = po0 * dec(OV0) + pp0 - 1

# features known at DK's opener (results through 2 days before; schedule; expected goalies)
X = pd.DataFrame(index=H.index)
X["model_disagree"] = lg(pmu) - lg(mkt_u)
X["goals_form"] = XD.goals_form; X["xg_form"] = XD.xg_form; X["att_form"] = XD.att_form
X["xg_level"] = XD.xg_level; X["att_level"] = FD.h_att_lvl + FD.a_att_lvl; X["pp_level"] = XD.pp_level
X["b2b_both"] = XD.b2b_both; X["b2b_any"] = XD.b2b_any; X["late"] = XD.late; X["divisional"] = XD.divisional
X["line_65plus"] = (T0 >= 6.5).astype(float)
X["q_exp"] = Hd.q_exp.values                                           # expected starters' goals saved above expected (+ = good goalies)
OPEN_F = list(X.columns)
y = (r_un > 0).astype(float); dcd = r_un != 0

# ------------------------------------------------------------------ 0. baselines
hdr("0. BASELINES at DK's opener (CLV = goals the closing total fell below the bet line)", DK_SEAS)
line("blind unders, all", np.ones(len(H), bool), u_un, r_un, SEA, DK_SEAS, clv_dk)
for T in (5.5, 6.0, 6.5, 7.0):
    line(f"blind unders at {T}", T0 == T, u_un, r_un, SEA, DK_SEAS, clv_dk)
for lo, hi in ((-1000, -131), (-130, -116), (-115, -101), (100, 1000)):
    line(f"blind unders, under price {lo:+d}..{hi:+d}", (UN0 >= lo) & (UN0 <= hi), u_un, r_un, SEA, DK_SEAS, clv_dk)
line("current shot model unders EV 6%+", (ev_model_u >= 0.06) & (ev_model_u > ev_model_o), u_un, r_un, SEA, DK_SEAS, clv_dk)

# ------------------------------------------------------------------ 1. one-feature screen (market offset), choose seasons only
hdr("1. FEATURE SCREEN on 2021-24 only: logistic under ~ offset(logit DK under) + feature (coef per SD; + = more unders than priced)", DK_SEAS)
tr = dcd & np.isin(SEA, TRAIN); te = dcd & np.isin(SEA, TEST)
MU = {f: (np.nanmean(X[f][np.isin(SEA, TRAIN)]), np.nanstd(X[f][np.isin(SEA, TRAIN)]) or 1) for f in OPEN_F}
Z = pd.DataFrame({f: (X[f] - MU[f][0]) / MU[f][1] for f in OPEN_F})
keep = []
print(f"  {'feature':16s} {'choose 21-24':>16s} {'holdout 24-26':>16s}")
for f in OPEN_F:
    out = []
    for m in (tr, te):
        mm = m & Z[f].notna().values
        b, se = logit_fit(y[mm], lg(mkt_u[mm]), Z[f].values[mm]); out.append((b[1], se[1]))
    NV.append(f"screen {f}")
    flag = abs(out[0][0] / out[0][1]) >= 2
    if flag: keep.append(f)
    print(f"  {f:16s} {out[0][0]:+.3f} ({out[0][1]:.3f}) {out[1][0]:+.3f} ({out[1][1]:.3f})  {'<- kept (|z|>=2 on 21-24)' if flag else ''}")
print(f"  Kept for the combined model (chosen on 2021-24 only): {keep or 'none'}")

# ------------------------------------------------------------------ 2. pre-registered rules
gf_hi = np.nanquantile(X.goals_form[np.isin(SEA, TRAIN)], 0.8)
qe_hi = np.nanquantile(X.q_exp[np.isin(SEA, TRAIN)], 0.8)
att_lo = np.nanquantile(X.att_level[np.isin(SEA, TRAIN)], 0.2)
pp_lo = np.nanquantile(X.pp_level[np.isin(SEA, TRAIN)], 0.2)
hdr("2. PRE-REGISTERED UNDER RULES at DK's opener (thresholds = 2021-24 quintiles)", DK_SEAS)
U = {"U1 line 6.5+ (market over-shades high totals?)": T0 >= 6.5,
     "U2 both teams' last-10 goals well above season (top 20%)": X.goals_form.values >= gf_hi,
     "U3 strong expected starters at the open (top 20%)": X.q_exp.values >= qe_hi,
     "U4 low-event matchup: shot attempts level bottom 20%": X.att_level.values <= att_lo,
     "U5 low penalty matchup: power-play level bottom 20%": X.pp_level.values <= pp_lo,
     "U6 both teams on a back-to-back": X.b2b_both.values == 1,
     "U7 March-April divisional game": (X.late.values == 1) & (X.divisional.values == 1)}
for k, m in U.items():
    line(k, m, u_un, r_un, SEA, DK_SEAS, clv_dk)
    line("   + shot model also leans under (model under chance > market)", m & (pmu > mkt_u), u_un, r_un, SEA, DK_SEAS, clv_dk)

# ------------------------------------------------------------------ 3. follow the opener's move (bet at the later price)
hdr("3. MARKET MOVE: total moved DOWN from the opener -> under at the later DK price (and the reverse)", DK_SEAS)
for lab in ("+60 min", "+3 h", "game day 10 AM ET"):
    T1, ov1, un1 = PRE[lab]; u1, r1 = grade(T1, ov1, un1, TOT, False); c1 = T1 - Tc
    mv = (T1 - T0) + ((1 - nv(ov1, un1)) - mkt_u) * -2          # in goals; negative = market moved toward the under
    line(f"{lab}: moved toward under by 0.25+ goals, bet under then", mv <= -0.25, u1, r1, SEA, DK_SEAS, c1)
    line(f"{lab}: moved toward over by 0.25+ goals, bet under then (fade)", mv >= 0.25, u1, r1, SEA, DK_SEAS, c1)

# ------------------------------------------------------------------ 4. combined logistic model (opener)
def fit_predict(feats, Zs, yv, offv, train_mask):
    mm = train_mask & Zs[feats].notna().all(1).values
    b, se = logit_fit(yv[mm], offv[mm], Zs[feats].values[mm])
    p = 1 / (1 + np.exp(-(offv + b[0] + Zs[feats].fillna(0).values @ b[1:])))
    return p, b


hdr("4. COMBINED UNDERS MODEL at DK's opener (features kept in section 1; EV bar chosen on 2021-24)", DK_SEAS)
feats = keep if keep else ["model_disagree"]
p_u, b = fit_predict(feats, Z, y, lg(mkt_u), tr)
print(f"  features {feats}; coefficients " + ", ".join(f"{n} {v:+.3f}" for n, v in zip(["intercept"] + feats, b)))
ev_c = p_u * (1 - pp0) * dec(UN0) + pp0 - 1
best = max((0.02, 0.04, 0.06), key=lambda t: u_un[(ev_c >= t) & np.isin(SEA, TRAIN)].sum())
for t in (0.02, 0.04, 0.06):
    line(f"combined model unders EV {t:.0%}+" + ("  <- chosen bar" if t == best else ""), ev_c >= t, u_un, r_un, SEA, DK_SEAS, clv_dk)
feats_nm = [f for f in feats if f != "model_disagree"] or ["goals_form"]
p_nm, b_nm = fit_predict(feats_nm, Z, y, lg(mkt_u), tr)
ev_nm = p_nm * (1 - pp0) * dec(UN0) + pp0 - 1
line(f"same without the shot model ({'+'.join(feats_nm)}), EV {best:.0%}+", ev_nm >= best, u_un, r_un, SEA, DK_SEAS, clv_dk)

# ------------------------------------------------------------------ 5. post-confirmation (starters known), DK price 1 h before
hdr("5. POST-CONFIRMATION unders: DK price 1 h before puck drop, actual starters (mild lineup look-ahead: the model uses the real lineup)", DK_SEAS)
Tp, ovp, unp = PRE["1 h before"]; up, rp = grade(Tp, ovp, unp, TOT, False); cp = Tp - Tc
mkt_up = 1 - nv(ovp, unp)
po, pu, pp = model_ou(H.lam_home, H.lam_away, Tp); pmu_p = pu / np.clip(po + pu, 1e-9, None)
Xp = pd.DataFrame({"model_disagree_pre": lg(pmu_p) - lg(mkt_up), "q_act": Hd.q_act.values, "q_surprise": Hd.q_surprise.values,
                   "goals_form": X.goals_form, "att_level": X.att_level})
Zp = (Xp - Xp[np.isin(SEA, TRAIN)].mean()) / Xp[np.isin(SEA, TRAIN)].std()
yp = (rp > 0).astype(float); trp = (rp != 0) & np.isin(SEA, TRAIN) & ~np.isnan(mkt_up)
for f in Zp.columns:
    mm = trp & Zp[f].notna().values; b1, s1 = logit_fit(yp[mm], lg(mkt_up[mm]), Zp[f].values[mm]); NV.append(f"pretip {f}")
    mm2 = (rp != 0) & np.isin(SEA, TEST) & Zp[f].notna().values & ~np.isnan(mkt_up); b2, s2 = logit_fit(yp[mm2], lg(mkt_up[mm2]), Zp[f].values[mm2])
    print(f"  {f:20s} choose {b1[1]:+.3f} ({s1[1]:.3f})  holdout {b2[1]:+.3f} ({s2[1]:.3f})")
qa_hi = np.nanquantile(Hd.q_act.values[np.isin(SEA, TRAIN)], 0.8)
line("both actual starters strong (sum top 20%), under at 1-h price", Hd.q_act.values >= qa_hi, up, rp, SEA, DK_SEAS, cp)
line("shot model with actual starters: under EV 6%+", (pu * dec(unp) + pp - 1 >= 0.06), up, rp, SEA, DK_SEAS, cp)
line("  + both starters strong", (pu * dec(unp) + pp - 1 >= 0.06) & (Hd.q_act.values >= qa_hi), up, rp, SEA, DK_SEAS, cp)
ok = ~np.isnan(mkt_up)
pfeat = ["model_disagree_pre", "q_act", "goals_form"]
Zp2 = Zp.copy(); Zp2.loc[~ok, :] = np.nan
pp_u, bp = fit_predict(pfeat, Zp2, yp, np.where(ok, lg(mkt_up), 0), trp)
ev_p = pp_u * (1 - pp) * dec(unp) + pp - 1
for t in (0.02, 0.04, 0.06):
    line(f"combined pretip model ({'+'.join(pfeat)}) EV {t:.0%}+", ok & (ev_p >= t), up, rp, SEA, DK_SEAS, cp)

# ------------------------------------------------------------------ 6. SBR replication 2011-21
sT, sOV, sUN = SB.open_total.values, SB.open_over_odds.values, SB.open_under_odds.values
s_uu, s_ru = grade(sT, sOV, sUN, SB.total.values, False); s_mu = 1 - nv(sOV, sUN); s_clv = sT - SB.close_total.values
XSs = pd.DataFrame({"goals_form": XS.goals_form, "xg_form": XS.xg_form, "att_form": XS.att_form, "xg_level": XS.xg_level,
                    "att_level": FS.h_att_lvl + FS.a_att_lvl, "pp_level": XS.pp_level, "b2b_both": XS.b2b_both, "b2b_any": XS.b2b_any,
                    "late": XS.late, "divisional": XS.divisional, "line_65plus": (sT >= 6.5).astype(float)})
qx = Gq.set_index("game_id")
XSs["q_exp"] = qx.q_exp.reindex(SB.game_id).values
hdr(f"6. SBR {SB_SEAS[0] - 1}-{SB_SEAS[-1]} openers (out of sample; over price rebuilt; DK-era thresholds and coefficients)", SB_SEAS)
line("blind unders, all", np.ones(len(SB), bool), s_uu, s_ru, sS, SB_SEAS, s_clv)
for T in (5.0, 5.5, 6.0, 6.5):
    line(f"blind unders at {T}", sT == T, s_uu, s_ru, sS, SB_SEAS, s_clv)
SU = {"U1 line 6.5+": sT >= 6.5, "U2 goals form top 20% (DK cut)": XSs.goals_form.values >= gf_hi,
      "U3 strong expected starters (DK cut)": XSs.q_exp.values >= qe_hi, "U4 low attempts level (DK cut)": XSs.att_level.values <= att_lo,
      "U6 both teams on a back-to-back": XSs.b2b_both.values == 1, "U7 March-April divisional": (XSs.late.values == 1) & (XSs.divisional.values == 1)}
for k, m in SU.items(): line(k, m, s_uu, s_ru, sS, SB_SEAS, s_clv)
fs = [f for f in feats_nm if f in XSs]
if fs:
    Zs = pd.DataFrame({f: (XSs[f] - MU[f][0]) / MU[f][1] for f in fs})
    p_s = 1 / (1 + np.exp(-(lg(s_mu) + b_nm[0] + Zs.fillna(0).values @ b_nm[1:len(fs) + 1])))
    pps = np.where(sT == np.round(sT), 0.12, 0.0)                       # rough push chance on whole-number lines
    ev_s = p_s * (1 - pps) * dec(sUN) + pps - 1
    line(f"DK-fitted unders model without shot model ({'+'.join(fs)}), EV {best:.0%}+", ev_s >= best, s_uu, s_ru, sS, SB_SEAS, s_clv)
print("  (SBR has no shot-model under probability for every game, so the model_disagree feature can't be replicated there.)")
# SBR closing price with actual starters
GS = Gq[(Gq.season <= 2021) & Gq.close_total.notna() & Gq.close_under_odds.notna() & (Gq.close_total_ok == 1)].reset_index(drop=True)
cu, cr = grade(GS.close_total.values, GS.close_over_odds.values, GS.close_under_odds.values, GS.total.values, False)
qa_cut = np.nanquantile(GS.q_act.values, 0.8)
line("SBR close: both actual starters strong (top 20%), under", GS.q_act.values >= qa_cut, cu, cr, GS.season.values, SB_SEAS)

print(f"\nVariants with a printed record or coefficient: {len(NV)} (at 5% per test, ~{0.05 * len(NV):.0f} false positives expected).")
