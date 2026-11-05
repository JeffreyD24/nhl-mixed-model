"""NHL shot model weight against DraftKings' opening and closing total price (research/totals_close/PREREG.md).
python research/totals_close/close_weight.py > research/totals_close/output.txt"""
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, HERE)
import nhl_mixed_model as nm
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
def nv(a, b): ia, ib = 1 / dec(a), 1 / dec(b); return ia / (ia + ib)
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
def logit_fit(y, off, x):
    X = np.column_stack([np.ones(len(y)), x]); b = np.zeros(2)
    for _ in range(60):
        p = 1 / (1 + np.exp(-(off + X @ b))); W = p * (1 - p); Hs = X.T @ (X * W[:, None])
        st = np.linalg.solve(Hs, X.T @ (y - p)); b += st
        if np.abs(st).max() < 1e-9: break
    return b, np.sqrt(np.diag(np.linalg.inv(Hs)))
H = pd.concat([pd.read_csv(os.path.join(HERE, "research/spreads/nhl_holdout", f"dk_holdout_lag1_{s}.csv")) for s in range(2022, 2027)])
H = H[H.home_goals.notna() & H.lam_home_open.notna()].copy(); H["tot"] = H.home_goals + H.away_goals
print(f"games with a result and an opener-time model: {len(H)}")
TRAIN, TEST = [2022, 2023, 2024], [2025, 2026]
out = {}
for when in ["open", "close"]:
    T, OV, UN = H[f"{when}_total"].values, H[f"{when}_over_odds"].values, H[f"{when}_under_odds"].values
    ok = ~np.isnan(T) & ~np.isnan(OV) & ~np.isnan(UN)
    po, pu, pp = nm.over_prob(H.lam_home_open.values, H.lam_away_open.values, np.nan_to_num(T, nan=6.0), nm.H_OT_DEFAULT, {})
    pm = po / np.clip(po + pu, 1e-9, None); mk = nv(OV, UN)
    dcd = ok & (H.tot.values != T); y = (H.tot.values > T).astype(float)
    dis = lg(pm) - lg(mk)
    print(f"\n===== at DK's {when.upper()}: decided games {dcd.sum()}, mean |model - market| {np.mean(np.abs(pm[dcd] - mk[dcd])) * 100:.2f} pts of chance")
    def fit(mask, label):
        m = dcd & mask; b, se = logit_fit(y[m], lg(mk[m]), dis[m])
        print(f"  {label:28s} n {m.sum():5d}   w {b[1]:+.3f} (se {se[1]:.3f})  90% [{b[1] - 1.645 * se[1]:+.3f}, {b[1] + 1.645 * se[1]:+.3f}]   intercept {b[0]:+.3f}")
        return b[1], se[1]
    out[when] = {"all": fit(np.ones(len(H), bool), "all five seasons"),
                 "train": fit(H.season.isin(TRAIN).values, "train 2021-22..2023-24"),
                 "test": fit(H.season.isin(TEST).values, "TEST 2024-25 + 2025-26")}
    for s in range(2022, 2027): fit((H.season == s).values, f"  {s - 1}-{str(s)[2:]}")
w, se = out["close"]["test"]
print(f"\nPRE-REGISTERED VERDICT: close weight on test seasons {w:+.3f}, 90% lower bound {w - 1.645 * se:+.3f} -> {'PASS' if w - 1.645 * se > 0 else 'NO PASS'}")
wo = out["open"]["all"][0]; wc = out["close"]["all"][0]
print(f"Share of the model's opener information left at the close (all seasons, descriptive): {wc / wo:.2f}" if wo > 0 else "")
