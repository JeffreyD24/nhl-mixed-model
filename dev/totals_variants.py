# compare totals variants: adaptive baseline on/off x totals calibration (pooled / per-line / none)
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "."); import nhl_mixed_model as nm
F = pd.read_csv("data/training_games.csv")
SPLITS = ((2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]), (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
out = []
for adapt in ((None,), (None, 400, 1500, 5000)):
    for tc in ("pooled", "per_line", "none"):
        for test, train in SPLITS:
            s, P, x = nm.run(F, train, test, adapt_grid=adapt, tot_cal=tc)
            row = dict(adapt=adapt != (None,), tot_cal=tc, test=test, n0=s["chosen_adapt_n0"], hl=s["chosen_halflife"])
            tot = P.home_goals + P.away_goals
            for ln in ("open", "close"):
                if not P[f"{ln}_total"].notna().any(): continue
                ok = P[f"{ln}_total"].notna() & (tot != P[f"{ln}_total"])
                po, pu, pp = nm.over_prob(P.lam_home_open[ok].values, P.lam_away_open[ok].values, P[f"{ln}_total"][ok].values, x["h_ot"], x["cal"]["open"])
                pc = po / (po + pu); y = (tot[ok] > P[f"{ln}_total"][ok]).values
                row[f"{ln}_logloss"] = round(float(-np.mean(y * np.log(pc) + (1 - y) * np.log(1 - pc))), 4)
                Bt = nm.bets(P, ln, "_open", x["cal"]["open"], x["h_ot"]); b = Bt[(Bt.market == "total") & (Bt.ev >= 0.06) & Bt.profit.notna()]
                row[f"{ln}_tot6"] = f"{(b.side=='over').sum()}o/{(b.side=='under').sum()}u {b.profit.sum():+.1f}u n={len(b)}"
                for mk in ("moneyline", "puck line"):
                    bb = Bt[(Bt.market == mk) & (Bt.ev >= 0.06) & Bt.profit.notna()]; row[f"{ln}_{mk}6"] = round(bb.profit.sum(), 1)
            row["bias_total"] = round(float((P.pred_total_open - tot).mean()), 3)
            out.append(row); print(row, flush=True)
pd.DataFrame(out).to_csv("_tmp/totals_variants.csv", index=False)
