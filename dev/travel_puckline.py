"""Does the schedule/travel adjustment (back-to-backs, westward travel) also help the shot model's PUCK LINE bets?
The moneyline adjustment (home win chance) is turned into a shift of expected goals (home up, away down by the same amount)
that moves the home win chance by that much, then the puck line chances are recomputed. Weights fit leaving the season out.
DraftKings openers, EV 6%+, 2021-22..2025-26.   python dev/travel_puckline.py WORKDIR TRACKER"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); TRK = os.path.abspath(sys.argv[2]); sys.path.insert(0, W)
import nhl_mixed_model as nm
H = pd.concat([pd.read_csv(os.path.join(W, "_tmp", f"dk_holdout_{s}.csv")) for s in (2022, 2023, 2024, 2025, 2026)])
TN = pd.read_csv(os.path.join(TRK, "analysis", "travel_nhl_games.csv"))
H = H.merge(TN[["date", "home", "away", "h_rest", "a_rest", "a_tz_move"]], on=["date", "home", "away"]).dropna(subset=["lam_home_open", "lam_away_open", "open_home_pl", "open_home_pl_odds", "open_away_pl_odds"]).reset_index(drop=True)
H["f_ab2b"] = ((H.a_rest == 1) & (H.h_rest > 1)).astype(float); H["f_hb2b"] = ((H.h_rest == 1) & (H.a_rest > 1)).astype(float)
H["f_west"] = (-H.a_tz_move).clip(lower=0); H["hw"] = (H.home_goals > H.away_goals).astype(float)
dec = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
F = ["f_ab2b", "f_hb2b", "f_west"]
def probs(lh, la):
    r = nm.raw_probs(lh, la, nm.H_OT_DEFAULT); return r["home_win"], r["home_by2"], r["away_by2"]
lh0, la0 = H.lam_home_open.values, H.lam_away_open.values
p0, hb0, ab0 = probs(lh0, la0)
eps = 0.05; p1, _, _ = probs(lh0 + eps, la0 - eps); slope = (p1 - p0) / eps        # home win chance per goal shifted
out = {"current": [], "with schedule/travel": []}
for s in sorted(H.season.unique()):
    te = (H.season == s).values
    X = np.column_stack([H.loc[~te, F].values, np.ones((~te).sum())]); b = np.linalg.lstsq(X, (H.hw - H.p_home_win_open)[~te].values, rcond=None)[0][:-1]
    adj = H.loc[te, F].values @ b; shift = adj / slope[te]
    for lab, (lh, la) in (("current", (lh0[te], la0[te])), ("with schedule/travel", (lh0[te] + shift, la0[te] - shift))):
        _, hb2, ab2 = probs(lh, la); h = H[te]; hl = h.open_home_pl.values
        hb2 = np.clip(h.p_home_by2_open.values + hb2 - hb0[te], 0.001, 0.999); ab2 = np.clip(h.p_away_by2_open.values + ab2 - ab0[te], 0.001, 0.999)   # stored (calibrated) + change
        p_hc = np.where(hl < 0, hb2, 1 - ab2); margin = (h.home_goals - h.away_goals).values
        home_cover = np.where(hl < 0, margin >= 2, margin >= -1)
        dh, da = dec(h.open_home_pl_odds.values), dec(h.open_away_pl_odds.values)
        evh, eva = p_hc * dh - 1, (1 - p_hc) * da - 1; home = evh >= eva; ev = np.maximum(evh, eva)
        u = np.where(np.where(home, home_cover, ~home_cover), np.where(home, dh, da) - 1, -1.0); k = ev >= 0.06
        out[lab].append((k.sum(), u[k].sum()))
for lab, v in out.items():
    print(f"  puck line, {lab:22s}: " + " ".join(f"{u:+.1f}" for n, u in v) + f" | {sum(n for n, u in v)} bets {sum(u for n, u in v):+.1f}u")
