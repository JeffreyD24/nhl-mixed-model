"""Replay the CURRENT NHL rules (Nov 2, 2026) on this season's finished games, at DraftKings' opening prices, using the shot
model's locked picks (state/picks_log_xg.csv, same one-day information lag as live). Pinnacle rules and second-chance bets
can't be replayed (Pinnacle recording started Nov 2).  python dev/season_replay.py WORKDIR"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm, nhl_travel as nt
P = pd.read_csv(os.path.join(W, "state", "picks_log_xg.csv"))
P = P[P.home_goals.notna() & (P.date >= "2026-10-06")].sort_values(["date", "tip_et"]).reset_index(drop=True)
dec = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
def nv(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)
# schedule features from this season's games (each team's previous game before the date)
allg = pd.read_csv(os.path.join(W, "state", "picks_log_xg.csv")); allg = allg[allg.date >= "2026-10-06"].sort_values("date")
rows = []
for r in P.itertuples():
    prev = allg[allg.date < r.date]
    last = {}
    for t in (r.home, r.away):
        g = prev[(prev.home == t) | (prev.away == t)]
        if len(g): last[t] = (g.date.iloc[-1], g.home.iloc[-1])
    adj, why = nt.adjustment(r.home, r.away, pd.Timestamp(r.date), last)
    hb2b = r.home in last and (pd.Timestamp(r.date) - pd.Timestamp(last[r.home][0])).days == 1
    ab2b = r.away in last and (pd.Timestamp(r.date) - pd.Timestamp(last[r.away][0])).days == 1
    rows.append((adj, hb2b, ab2b))
P["tadj"], P["hb2b"], P["ab2b"] = zip(*rows)
P["p_ml"] = (P.p_home_win + P.tadj).clip(0.02, 0.98)
P["mkt"] = nv(P.open_home_ml, P.open_away_ml)
P["p_bl"] = 0.55 * P.p_ml + 0.45 * P.mkt
mg = P.home_goals - P.away_goals; tot = P.home_goals + P.away_goals
bets = []
for i, r in P.iterrows():
    cand = []
    # moneyline (blend, EV 4%+)
    if not np.isnan(r.open_home_ml):
        for side, p, o in (("home", r.p_bl, r.open_home_ml), ("away", 1 - r.p_bl, r.open_away_ml)):
            ev = p * dec(o) - 1
            if ev >= 0.04 and not (r.hb2b if side == "home" else r.ab2b):
                won = mg[i] > 0 if side == "home" else mg[i] < 0
                cand.append(("moneyline", side, o, ev, float(dec(o) - 1) if won else -1.0))
    # puck line (plain model, EV 6%+)
    if not np.isnan(r.open_home_pl) and not np.isnan(r.open_home_pl_odds):
        hl = r.open_home_pl; p_hc = r.p_home_by2 if hl < 0 else 1 - r.p_away_by2
        hc = (mg[i] >= 2) if hl < 0 else (mg[i] >= -1)
        for side, p, o, won in (("home", p_hc, r.open_home_pl_odds, hc), ("away", 1 - p_hc, r.open_away_pl_odds, not hc)):
            ev = p * dec(o) - 1
            if ev >= 0.06 and not (r.hb2b if side == "home" else r.ab2b):
                cand.append(("puck line", side, o, ev, float(dec(o) - 1) if won else -1.0))
    # one bet per game among team markets: higher EV; never both teams
    if cand:
        best = max(cand, key=lambda c: c[3]); bets.append(dict(date=r.date, game=f"{r.away}@{r.home}", market=best[0], side=best[1], price=best[2], ev=best[3], units=best[4]))
    # overs (plain model, EV 6%+)
    if not np.isnan(r.open_total) and not np.isnan(r.open_over_odds):
        po, pu, pp = nm.over_prob(np.array([r.lam_home]), np.array([r.lam_away]), np.array([r.open_total]), nm.H_OT_DEFAULT, {})
        ev = po[0] * dec(r.open_over_odds) + pp[0] - 1
        if ev >= 0.06:
            res = 0.0 if tot[i] == r.open_total else (float(dec(r.open_over_odds) - 1) if tot[i] > r.open_total else -1.0)
            bets.append(dict(date=r.date, game=f"{r.away}@{r.home}", market="total (over)", side="over", price=r.open_over_odds, ev=ev, units=res))
B = pd.DataFrame(bets)
print(f"{len(P)} finished games {P.date.min()} .. {P.date.max()}")
for mk, g in B.groupby("market"):
    w, l = (g.units > 0).sum(), (g.units < 0).sum()
    print(f"  {mk:13s} {len(g):3d} bets {w}-{l}  {g.units.sum():+.2f}u ({g.units.sum() / len(g):+.1%})")
w, l = (B.units > 0).sum(), (B.units < 0).sum(); print(f"  ALL           {len(B):3d} bets {w}-{l}  {B.units.sum():+.2f}u ({B.units.sum() / len(B):+.1%})")
# compare: the old rules (plain model ML + PL at EV 6%+, both markets, no b2b skip, no blend)
old = []
for i, r in P.iterrows():
    for mk, pairs in (("moneyline", (("home", r.p_home_win, r.open_home_ml, mg[i] > 0), ("away", 1 - r.p_home_win, r.open_away_ml, mg[i] < 0))),
                      ("puck line", (("home", r.p_home_by2 if r.open_home_pl < 0 else 1 - r.p_away_by2, r.open_home_pl_odds, (mg[i] >= 2) if r.open_home_pl < 0 else (mg[i] >= -1)),
                                     ("away", 1 - (r.p_home_by2 if r.open_home_pl < 0 else 1 - r.p_away_by2), r.open_away_pl_odds, not ((mg[i] >= 2) if r.open_home_pl < 0 else (mg[i] >= -1)))))):
        evs = [(s, p * dec(o) - 1, o, won) for s, p, o, won in pairs if not np.isnan(o)]
        if not evs: continue
        s, ev, o, won = max(evs, key=lambda x: x[1])
        if ev >= 0.06: old.append(dict(market=mk, units=float(dec(o) - 1) if won else -1.0))
O = pd.DataFrame(old); print("  (old rules: plain shot model ML + PL at EV 6%+, both bets allowed:", f"{len(O)} bets {O.units.sum():+.2f}u)")
B.to_csv(os.path.join(W, "_tmp", "season_replay_bets.csv"), index=False)
