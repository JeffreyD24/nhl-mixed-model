"""NHL totals rework: everything learned so far applied to the shot model's totals, tested at DraftKings openers 2021-22..2025-26.
Pieces (each weight fit leaving the test season out, on the residual = actual goals - model total):
  drift    league scoring so far this season minus the model's average total so far (scoring levels change year to year)
  luck     both teams' goals minus xG, for and against, season to date (finishing / goaltending luck, as in the NBA)
  form     last-10 games' total goals vs season average (both teams)
  sched    back-to-backs (either team), away team moved west
Then: over/under chances from the adjusted expected goals (Poisson, ties to OT), EV at DraftKings' opening price, plus filters
learned elsewhere: bet only at the opener, EV bar, and Pinnacle's first total (agree / against).
  python dev/totals_rework.py WORKDIR TRACKER"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); TRK = os.path.abspath(sys.argv[2]); sys.path.insert(0, W)
import nhl_mixed_model as nm
H = pd.concat([pd.read_csv(os.path.join(W, "_tmp", f"dk_holdout_{s}.csv")) for s in (2022, 2023, 2024, 2025, 2026)], ignore_index=True)
TN = pd.read_csv(os.path.join(TRK, "analysis", "travel_nhl_games.csv"))
H = H.merge(TN[["date", "home", "away", "h_rest", "a_rest", "a_tz_move"]], on=["date", "home", "away"], how="left")
H = H.sort_values("date").reset_index(drop=True)
H["tot"] = H.home_goals + H.away_goals
# ---- season-to-date features (only earlier dates)
rows = []
for r in H.itertuples():
    rows += [dict(i=r.Index, season=r.season, date=r.date, team=r.home, side="h", gf=r.home_goals, ga=r.away_goals, xf=r.home_xg, xa=r.away_xg, tot=r.tot),
             dict(i=r.Index, season=r.season, date=r.date, team=r.away, side="a", gf=r.away_goals, ga=r.home_goals, xf=r.away_xg, xa=r.home_xg, tot=r.tot)]
L = pd.DataFrame(rows).sort_values(["season", "team", "date"]); g = L.groupby(["season", "team"])
sh = lambda c, f: g[c].transform(lambda v: f(v.shift()))
L["n"] = g.cumcount()
L["luck_f"] = sh("gf", lambda v: v.expanding().sum()) - sh("xf", lambda v: v.expanding().sum())
L["luck_a"] = sh("ga", lambda v: v.expanding().sum()) - sh("xa", lambda v: v.expanding().sum())
L["luck_f"] /= L.n.clip(lower=1); L["luck_a"] /= L.n.clip(lower=1)
L["form"] = sh("tot", lambda v: v.rolling(10, min_periods=6).mean()) - sh("tot", lambda v: v.expanding().mean())
for c in ("n", "luck_f", "luck_a", "form"):
    pv = L.pivot_table(index="i", columns="side", values=c); H[f"h_{c}"] = pv["h"]; H[f"a_{c}"] = pv["a"]
H["f_luck"] = (H.h_luck_f + H.h_luck_a + H.a_luck_f + H.a_luck_a).fillna(0)
H["f_form"] = (H.h_form + H.a_form).fillna(0)
# league drift: actual goals per game so far this season minus the model's average total so far (before this date)
d_ = H.groupby(["season", "date"]).agg(t=("tot", "sum"), p=("pred_total_open", "sum"), n=("tot", "size")).reset_index()
d_[["ct", "cp", "cn"]] = d_.groupby("season")[["t", "p", "n"]].cumsum() - d_[["t", "p", "n"]].values
d_["f_drift"] = np.where(d_.cn >= 100, (d_.ct - d_.cp) / d_.cn.clip(lower=1), 0.0)
H = H.merge(d_[["season", "date", "f_drift"]], on=["season", "date"], how="left")
H["f_b2b"] = ((H.h_rest == 1).astype(float) + (H.a_rest == 1).astype(float)).fillna(0)
H["f_west"] = (-H.a_tz_move).clip(lower=0).fillna(0)
H["early"] = (H.h_n < 10) | (H.a_n < 10)
H = H.dropna(subset=["open_total", "open_over_odds", "open_under_odds", "lam_home_open", "lam_away_open"]).reset_index(drop=True)
# Pinnacle's first total (and DK's at that time): from the odds tables
PR = pd.read_csv(os.path.join(W, "data", "nhl_prices.csv.gz"))
pin = PR[PR.book == "pinnacle"][["date", "home", "away", "open_total", "open_over_odds", "open_under_odds"]].rename(columns=lambda c: c if c in ("date", "home", "away") else "pin_" + c)
H = H.merge(pin, on=["date", "home", "away"], how="left")
dec = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
def novig_over(o, u): io, iu = 1 / dec(o), 1 / dec(u); return io / (io + iu)
def ou(lh, la, T):
    po, pu, pp = nm.over_prob(lh, la, T, nm.H_OT_DEFAULT, {}); return po, pu, pp
SEAS = sorted(H.season.unique())
def evaluate(feats, ev_bar=0.06, pin_filter=None, skip_early=False, label=""):
    out = []; tu = tn = 0
    for s in SEAS:
        te = (H.season == s).values
        adj = np.zeros(te.sum())
        if feats:
            X = np.column_stack([H.loc[~te, feats].values, np.ones((~te).sum())]); y = (H.tot - H.pred_total_open)[~te].values
            b = np.linalg.lstsq(X, y, rcond=None)[0]; adj = np.column_stack([H.loc[te, feats].values, np.ones(te.sum())]) @ b
        h = H[te]; base = (h.lam_home_open + h.lam_away_open).values
        scale = np.clip((base + adj) / base, 0.6, 1.6)
        po, pu, pp = ou(h.lam_home_open.values * scale, h.lam_away_open.values * scale, h.open_total.values)
        do, du = dec(h.open_over_odds.values), dec(h.open_under_odds.values)
        evo, evu = po * do + pp - 1, pu * du + pp - 1
        over = evo >= evu; ev = np.maximum(evo, evu)
        res = np.where(h.tot > h.open_total, 1, np.where(h.tot < h.open_total, -1, 0)) * np.where(over, 1, -1)
        u = np.where(res > 0, np.where(over, do, du) - 1, np.where(res < 0, -1.0, 0.0))
        k = ev >= ev_bar
        if skip_early: k &= ~h.early.values
        if pin_filter is not None:
            pv = h.pin_open_total.values; ok = ~np.isnan(pv)
            agree = np.where(over, pv >= h.open_total.values, pv <= h.open_total.values)       # Pinnacle's first total on our side or equal
            k &= (~ok) | (agree if pin_filter == "agree" else ~agree)
        out.append(u[k].sum()); tu += u[k].sum(); tn += k.sum()
    print(f"  {label:44s} " + " ".join(f"{x:+6.1f}" for x in out) + f" | {tn:5d} bets {tu:+7.1f}u ({tu / max(tn, 1):+.1%})")
print("seasons", SEAS, "| totals at DraftKings openers, units by season")
evaluate([], label="current shot model (uncalibrated)")
evaluate(["f_drift"], label="+ league scoring drift")
evaluate(["f_luck"], label="+ shooting/goalie luck")
evaluate(["f_form"], label="+ last-10 form")
evaluate(["f_b2b", "f_west"], label="+ schedule (b2b, west travel)")
evaluate(["f_drift", "f_luck", "f_form", "f_b2b", "f_west"], label="+ all")
evaluate(["pred_total_open", "f_drift", "f_luck", "f_form", "f_b2b", "f_west"], label="+ all + recalibrated level")
print("filters on '+ all + recalibrated level':")
F = ["pred_total_open", "f_drift", "f_luck", "f_form", "f_b2b", "f_west"]
for bar in (0.04, 0.06, 0.09, 0.12): evaluate(F, ev_bar=bar, label=f"EV {bar:.0%}+")
evaluate(F, skip_early=True, label="EV 6%+, both teams 10+ games")
evaluate(F, pin_filter="agree", label="EV 6%+, skip when Pinnacle's first total disagrees")
evaluate(F, pin_filter="disagree", label="EV 6%+, ONLY when Pinnacle's first total disagrees")
