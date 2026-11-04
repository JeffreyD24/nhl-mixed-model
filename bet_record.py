"""
Bet record by model version. Every logged bet (state/my_bets.csv) is tagged with the model version that was live when it was
placed (state/bet_versions.csv: one row per version and market, with the ET time it went live). Writes
  state/bet_record.csv          every bet with its version, result, profit ($) and units (profit / stake)
  state/record_by_version.csv   W-L-P, units, ROI per version (and per market), plus an OVERALL row
Add a row to bet_versions.csv whenever a model or betting rule changes; bets placed after that time start a new record.
  python bet_record.py WORKDIR
"""
import os, re, sys
import numpy as np, pandas as pd
ML_EV_SPLIT = 0.09      # same as alert.py: moneyline record buckets EV 4-9% / 9%+

W = os.path.abspath(sys.argv[1]); STATE = os.path.join(W, "state")
MON = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def placed_at(r):
    """when the bet was placed (ET): 'placed Nov 2 11:35 AM' / 'placed 2:05 PM' in the notes, else when it was logged"""
    logged = pd.Timestamp(r.logged_at_et)
    m = re.search(r"placed (?:(\w{3}) (\d{1,2}) )?~?(\d{1,2}:\d{2}) ?([AP]M)", str(r.notes))
    if not m: return logged
    mon, day, hm, ap = m.groups()
    d = pd.Timestamp(logged.year, MON[mon], int(day)) if mon in MON else logged.normalize()
    t = pd.to_datetime(f"{hm} {ap}", format="%I:%M %p")
    ts = d + pd.Timedelta(hours=t.hour, minutes=t.minute)
    return ts - pd.Timedelta(days=1) if ts > logged + pd.Timedelta(minutes=5) else ts      # 'placed 11:47 PM' logged after midnight


def main():
    B = pd.read_csv(os.path.join(STATE, "my_bets.csv"))
    V = pd.read_csv(os.path.join(STATE, "bet_versions.csv"), parse_dates=["live_from_et"])
    B["placed_et"] = [placed_at(r) for r in B.itertuples()]
    def version(r):
        v = V[(V.market == r.market) & (V.live_from_et <= r.placed_et)].sort_values("live_from_et")
        return v.iloc[-1].version if len(v) else "before tracking"
    B["version"] = [version(r) for r in B.itertuples()]
    B.loc[B.notes.astype(str).str.contains("OFF-MODEL"), "version"] = "off-model (no alert)"      # bets the model did not call for
    # Nov 4, 2026: moneyline bets from NHL v4 on are recorded in two EV buckets (EV at the alert; 4-9% vs 9%+), graded separately
    A = pd.read_csv(os.path.join(STATE, "alerts.csv"))
    A = A[(A.market == "moneyline") & A.skipped.isna() & A.sent.astype(str).isin(["True", "quiet"])]
    A = A[A.model.astype(str) == "xg"]          # the shot model's EV (the alerting model; goals model rows are side-by-side only)
    A["team"] = np.where(A.side == "home", A.home, A.away)
    ev_at_alert = A.drop_duplicates(["date", "home", "away", "team"]).set_index(["date", "home", "away", "team"]).ev
    def bucket(r):
        if r.market != "moneyline" or not str(r.version).startswith("NHL v4"): return None
        ev = ev_at_alert.get((r.date, r.home, r.away, str(r.pick).lower()), r.model_ev_at_your_price)
        return None if pd.isna(ev) else ("EV 9%+" if ev >= ML_EV_SPLIT else "EV 4-9%")
    B["ev_bucket"] = [bucket(r) for r in B.itertuples()]
    B.loc[B.ev_bucket.notna(), "version"] = B.version + " [ML " + B.ev_bucket + "]"
    B["status"] = np.where(B.result.isin(["W", "L", "P"]), B.result, "pending")
    B["units"] = np.where(B.status == "pending", np.nan, B.profit / B.stake)
    keep = ["placed_et", "issue", "date", "away", "home", "market", "pick", "line", "odds", "stake", "version", "status", "profit", "units"]
    B[keep].sort_values("placed_et").to_csv(os.path.join(STATE, "bet_record.csv"), index=False)
    rows = []
    def summ(g, label, market):
        d = g[g.status != "pending"]; w, l, p = (d.status == "W").sum(), (d.status == "L").sum(), (d.status == "P").sum()
        base = str(label).split(" [ML ")[0]
        desc = V[V.version == base].description.iloc[0] if base in set(V.version) else ""
        rows.append(dict(version=label, market=market, bets=len(g), graded=len(d), wins=int(w), losses=int(l), pushes=int(p),
                         pending=int((g.status == "pending").sum()), units=round(d.units.sum(), 2),
                         roi=round(d.units.sum() / len(d), 4) if len(d) else None, description=desc))
    for (ver, mk), g in B.groupby(["version", "market"]): summ(g, ver, mk)
    summ(B, "OVERALL", "all")
    R = pd.DataFrame(rows); R.to_csv(os.path.join(STATE, "record_by_version.csv"), index=False)
    # every moneyline BET alert since NHL v4 (whether or not you placed it), split by EV bucket: the clean test of the split
    v4 = V[(V.version == "NHL v4") & (V.market == "moneyline")].live_from_et.min()
    G = A[pd.to_datetime(A.alerted_at_et) >= v4].copy() if pd.notna(v4) else A.iloc[0:0].copy()
    G["bucket"] = np.where(G.ev >= ML_EV_SPLIT, "EV 9%+", "EV 4-9%"); G["clv"] = pd.to_numeric(G.clv, errors="coerce")
    S = [dict(bucket=b, alerts=len(g), graded=int(g.profit.notna().sum()), units=round(g.profit.sum(), 2),
              avg_clv=round(g.clv.mean(), 4) if g.clv.notna().any() else None) for b, g in G.groupby("bucket")]
    pd.DataFrame(S, columns=["bucket", "alerts", "graded", "units", "avg_clv"]).to_csv(os.path.join(STATE, "ml_ev_buckets.csv"), index=False)
    for x in S: print(f"ML alerts since v4, {x['bucket']:8s} {x['graded']}/{x['alerts']} graded  {x['units']:+.2f}u  avg CLV {x['avg_clv']}")
    for r in R.itertuples():
        print(f"{r.version:28s} {r.market:10s} {r.wins}-{r.losses}-{r.pushes} ({r.pending} pending)  {r.units:+.2f}u")


if __name__ == "__main__":
    main()
