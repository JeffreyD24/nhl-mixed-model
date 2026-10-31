"""
How the models do at a price halfway between the opening and closing line (2024-25, 2025-26: the seasons with both).
There is no recorded mid-day price, so it is built: halfway between the open and close in no-vig win probability,
with the average of the open and close margin (vig) put back on. Puck line and totals only when the line number
(+/-1.5, 5.5, 6.5) is the same at open and close; otherwise that bet is skipped.

  python dev/midpoint_backtest.py WORKDIR
"""
import os, sys, json
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_mixed_model as nm

dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def amer(d):
    d = np.asarray(d, float); return np.where(d >= 2, (d - 1) * 100, -100 / (d - 1))


def mid_prices(P, a, b):
    """two-way prices halfway between open and close; a, b = column names of the two sides"""
    io_a, io_b = 1 / dec(P[f"open_{a}"]), 1 / dec(P[f"open_{b}"])
    ic_a, ic_b = 1 / dec(P[f"close_{a}"]), 1 / dec(P[f"close_{b}"])
    p = ((io_a / (io_a + io_b)) + (ic_a / (ic_a + ic_b))) / 2
    over = ((io_a + io_b) + (ic_a + ic_b)) / 2
    return amer(1 / (p * over)), amer(1 / ((1 - p) * over))


def add_mid(P):
    P = P.copy()
    P["mid_home_ml"], P["mid_away_ml"] = mid_prices(P, "home_ml", "away_ml")
    same = P.open_home_pl == P.close_home_pl
    h, a = mid_prices(P, "home_pl_odds", "away_pl_odds")
    P["mid_home_pl"] = np.where(same, P.open_home_pl, np.nan); P["mid_home_pl_odds"] = np.where(same, h, np.nan); P["mid_away_pl_odds"] = np.where(same, a, np.nan)
    same = P.open_total == P.close_total
    o, u = mid_prices(P, "over_odds", "under_odds")
    P["mid_total"] = np.where(same, P.open_total, np.nan); P["mid_over_odds"] = np.where(same, o, np.nan); P["mid_under_odds"] = np.where(same, u, np.nan)
    return P


rows = []
for t in (2025, 2026):
    G = add_mid(pd.read_csv(os.path.join(W, "_tmp", f"backtest_{t}.csv")))
    X = add_mid(pd.read_csv(os.path.join(W, "_tmp", f"xg_backtest_{t}.csv")))
    sg = json.load(open(os.path.join(W, "backtests", f"backtest_{t}.json")))
    hx = json.load(open(os.path.join(W, "backtests", "xg_backtests.json")))[str(t)]["summary"]["h_ot"]
    for name, P, cal, h in (("goals", G, sg["calibration"]["open"], sg["h_ot"]), ("shot", X, {}, hx)):
        for ln in ("open", "mid", "close"):
            Bt = nm.bets(P, ln, "_open", cal, h)
            for mk in ("moneyline", "puck line", "total"):
                for th in (0.03, 0.06, 0.09):
                    s = Bt[(Bt.market == mk) & (Bt.ev >= th) & Bt.profit.notna()]
                    rows.append(dict(season=f"{t - 1}-{str(t)[2:]}", model=name, price=ln, market=mk, ev=th, bets=len(s),
                                     wins=int((s.profit > 0).sum()), losses=int((s.profit < 0).sum()),
                                     units=round(s.profit.sum(), 1), roi=round(s.profit.mean(), 4) if len(s) else np.nan))
R = pd.DataFrame(rows)
R.to_csv(os.path.join(W, "backtests", "midpoint_prices.csv"), index=False)
pd.set_option("display.width", 200)
k = R[(R.ev == 0.06)]
print(k.pivot_table(index=["model", "market", "season"], columns="price", values="units", aggfunc="first")[["open", "mid", "close"]])
r = R[(R.ev == 0.06) & R.market.isin(["moneyline", "puck line"])].groupby(["model", "price"])[["bets", "units"]].sum()
r["roi"] = (r.units / r.bets).round(4); print(r)
print(R[R.market.isin(["moneyline", "puck line"])].groupby(["model", "price", "ev"])[["bets", "units"]].sum().assign(roi=lambda d: (d.units / d.bets).round(4)))
