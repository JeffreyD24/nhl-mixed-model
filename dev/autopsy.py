"""NHL autopsy: shot model (live) and goals model (research), moneyline + puck line at the opener, EV 6%+, 2021-22..2025-26
(DraftKings openers 2021-24, training openers 2024-26). Wins vs losses by group, units per season.
  python dev/autopsy.py WORKDIR   (needs _tmp/autopsy_{model}_{season}.csv from dev/autopsy_preds.py)"""
import os, sys, glob
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1])
A = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(W, "_tmp", "autopsy_*_20*.csv"))], ignore_index=True)
dec = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
A = A[A.market.isin(["moneyline", "puck line"]) & (A.ev >= 0.06) & A.profit.notna()].copy()
home = A.side == "home"
A["fav"] = A.price < 0
ih, ia = 1 / dec(A.open_home_ml), 1 / dec(A.open_away_ml); A["mkt_home_p"] = ih / (ih + ia)
A["our_mkt_p"] = np.where(home, A.mkt_home_p, 1 - A.mkt_home_p)
A["our_b2b"] = np.where(home, A.b2b_home, A.b2b_away).astype(float); A["opp_b2b"] = np.where(home, A.b2b_away, A.b2b_home).astype(float)
A["our_gmix"] = np.where(home, A.home_gmix, A.away_gmix); A["opp_gmix"] = np.where(home, A.away_gmix, A.home_gmix)
A["our_out"] = np.where(home, A.home_n_out_open, A.away_n_out_open); A["opp_out"] = np.where(home, A.away_n_out_open, A.home_n_out_open)
A["our_miss"] = np.where(home, A.home_miss_off_open, A.away_miss_off_open); A["opp_miss"] = np.where(home, A.away_miss_off_open, A.home_miss_off_open)
cl = np.where(A.market == "moneyline", np.where(home, A.close_home_ml, A.close_away_ml), np.where(home, A.close_home_pl_odds, A.close_away_pl_odds))
A["clv"] = 1 / dec(pd.Series(cl).values) - 1 / A.dec      # + = price shortened (moved our way), implied-prob points
A["month"] = pd.to_datetime(A.date).dt.month
A["ot"] = A.ending.astype(str).str.upper().isin(["OT", "SO"])
SEAS = sorted(A.season.unique())
def u(g): return g.profit.sum()
def grp(B, lab, key):
    print(f"\n{lab}")
    for k, g in B.groupby(key, observed=True):
        per = " ".join(f"{s % 100}:{u(g[g.season == s]):+.0f}" for s in SEAS)
        print(f"  {str(k):30s} {len(g):4d} bets won {g.win.mean():.1%} (said {g.p.mean():.1%}, needed {(1 / g.dec).mean():.1%}) {u(g):+7.1f}u  [{per}]")
for model in ("shot", "goals"):
    B = A[A.model == model]
    print(f"\n==================== {model.upper()} MODEL: {len(B)} bets, {u(B):+.1f}u ({u(B) / len(B):+.1%})")
    grp(B, "Season", "season"); grp(B, "Market", "market"); grp(B, "Side", "side")
    grp(B, "Market x favorite/underdog", B.market + " " + np.where(B.fav, "favorite", "underdog"))
    grp(B, "Price", pd.cut(B.price, [-1000, -150, -101, 130, 180, 250, 2000]))
    grp(B, "EV size", pd.cut(B.ev, [0.06, 0.09, 0.12, 0.2, 5]))
    grp(B, "Price move by close", pd.cut(B.clv, [-1, -0.01, 0.01, 1], labels=["against", "none", "our way"]))
    grp(B, "Back-to-backs", np.where(B.our_b2b == 1, "we b2b", "") + np.where(B.opp_b2b == 1, " they b2b", ""))
    grp(B, "Their skaters out at open", pd.cut(B.opp_out, [-1, 0, 1, 2, 20]))
    grp(B, "Our skaters out at open", pd.cut(B.our_out, [-1, 0, 1, 2, 20]))
    grp(B, "Month", B.month)
    grp(B, "Game went to OT/SO", B.ot)
    B.to_csv(os.path.join(W, "_tmp", f"autopsy_bets_{model}.csv"), index=False)
