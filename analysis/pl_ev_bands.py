"""
Puck line EV in 1-point bands at DraftKings' opener (Nov 5, 2026). Analysis only: nothing here is imported by the live code.

Question: the Nov 4 rule audit (rule_audit_nhl.py section 5) lumped puck lines at EV 6-9% together (514 bets, -11.1u) and
raised the bar to 9%. Is the 6-9% band uniformly bad, or does the top of it (8-9%) behave like 9%+?

Same data and rules as rule_audit_nhl.py section 5: shot model walk-forward predictions at DK's opening puck line,
2021-22..2025-26, one-day information lag; better EV side of each game; team on the 2nd night of a back-to-back removed.
Rest days are taken from data/games_hist.csv here instead of the NBA repo's travel file.

  python analysis/pl_ev_bands.py WORK [--build]     (--build makes WORK/_tmp/dk_holdout_*.csv, same as rule_audit_nhl.py)
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.abspath(sys.argv[1]); sys.path.insert(0, WORK)
SEASONS = (2022, 2023, 2024, 2025, 2026)
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))


def build_holdout():          # copied from rule_audit_nhl.py so the two use identical predictions
    import nhl_xg_model as xm, build_features as bf
    os.makedirs(os.path.join(WORK, "_tmp"), exist_ok=True)
    T0 = pd.read_csv(os.path.join(WORK, "data", "training_games.csv"))
    G = pd.read_csv(os.path.join(WORK, "data", "games_hist.csv"), parse_dates=["date"])
    B = pd.read_csv(os.path.join(WORK, "data", "box_hist.csv.gz")); S = pd.read_csv(os.path.join(WORK, "data", "shots_hist.csv.gz"), low_memory=False)
    F1, _ = bf.build(G, B, lag_days=1); T1 = T0.copy().set_index("game_id")
    for c in ("home_gmix", "away_gmix", "home_miss_off_open", "away_miss_off_open", "home_n_out_open", "away_n_out_open"):
        T1[c] = F1.set_index("game_id")[c].reindex(T1.index)
    T1 = T1.reset_index()
    DK = pd.read_csv(os.path.join(WORK, "data", "nhl_prices.csv.gz")); DK = DK[DK.book == "draftkings"].drop(columns=["book", "event_id"])
    for test, train in ((2022, [2020, 2021]), (2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]),
                        (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025])):
        xmod = xm.xg_model(S, T0, train); TG = xm.team_game_xg(xm.apply_xg(S, T0, xmod), T0)
        D = T1.drop(columns=[c for c in TG.columns if c != "game_id" and c in T1]).merge(TG, on="game_id", how="left")
        _, P, _ = xm.run(D, train, test, tot_cal="none", lag_days=1, halflives=(None, 60))
        P["date"] = pd.to_datetime(P.date).dt.strftime("%Y-%m-%d")
        P = P.drop(columns=[c for c in P if c.startswith(("open_", "close_", "mid_"))]).merge(DK, on=["date", "home", "away"], how="left")
        P.to_csv(os.path.join(WORK, "_tmp", f"dk_holdout_{test}.csv"), index=False)
        print("built", test, len(P), flush=True)


sys.path.insert(0, WORK)
import derived                                   # saved build products (derived/MANIFEST.md)
_miss = derived.ensure(WORK, [f"dk_holdout_{s}.csv" for s in SEASONS])
if _miss and '--build' not in sys.argv: sys.exit(f'missing saved build products {_miss}: build them, then python derived.py . --save')
if "--build" in sys.argv: build_holdout()
H = pd.concat([pd.read_csv(os.path.join(WORK, "_tmp", f"dk_holdout_{s}.csv")) for s in SEASONS], ignore_index=True)
H = H[H.open_home_ml.notna() & H.home_goals.notna() & H.p_home_win_open.notna()].reset_index(drop=True)

# rest days (1 = second night of a back-to-back) from the full schedule
G = pd.read_csv(os.path.join(WORK, "data", "games_hist.csv"))
L = pd.concat([G[["date", "home"]].rename(columns={"home": "team"}), G[["date", "away"]].rename(columns={"away": "team"})])
L["date"] = pd.to_datetime(L.date); L = L.drop_duplicates().sort_values(["team", "date"])
L["rest"] = L.groupby("team").date.diff().dt.days; L["date"] = L.date.dt.strftime("%Y-%m-%d")
R = L.set_index(["date", "team"]).rest
H["b2b_h"] = R.reindex(list(zip(H.date, H.home))).values == 1
H["b2b_a"] = R.reindex(list(zip(H.date, H.away))).values == 1

margin = (H.home_goals - H.away_goals).values
hpt = H.open_home_pl.astype(float).values
pc = np.where(hpt < 0, H.p_home_by2_open, 1 - H.p_away_by2_open)
dh, da = dec(H.open_home_pl_odds), dec(H.open_away_pl_odds)
evh, eva = pc * dh - 1, (1 - pc) * da - 1
home = evh >= eva; ev = np.where(home, evh, eva); d = np.where(home, dh, da)
cov = np.where(hpt < 0, margin >= 2, margin >= -1); win = np.where(home, cov, ~cov); u = np.where(win, d - 1, -1.0)
b2b = np.where(home, H.b2b_h, H.b2b_a)
fav = np.where(home, hpt < 0, hpt > 0)                     # our side is the -1.5 side
ok = ~np.isnan(ev) & ~np.isnan(hpt) & ~b2b
SEA = H.season.values


def rep(label, m):
    m = m & ok; n = int(m.sum()); uu = u[m]
    per = [u[m & (SEA == y)].sum() for y in SEASONS]
    print(f"  {label:34s} {n:5d} bets  {win[m].mean() if n else 0:5.1%}  {uu.sum():+7.1f}u  ({uu.sum() / max(n, 1):+6.1%})  | "
          + " ".join(f"{x:+6.1f}" for x in per) + f"  neg {sum(x < 0 for x in per)}/5")


hdr = "  " + " " * 34 + " bets   win%     units      ROI    | by season 21-22  22-23  23-24  24-25  25-26"
for title, extra in (("All +/-1.5 puck lines", np.abs(hpt) == 1.5), ("Our side -1.5 (favorite to cover by 2)", (np.abs(hpt) == 1.5) & fav),
                     ("Our side +1.5", (np.abs(hpt) == 1.5) & ~fav)):
    print(f"\n{title}, shot model EV at DK's opener, b2b removed\n" + hdr)
    for lo, hi in ((0.04, 0.05), (0.05, 0.06), (0.06, 0.07), (0.07, 0.08), (0.08, 0.09), (0.09, 0.10), (0.10, 0.12), (0.12, 0.15), (0.15, 9)):
        rep(f"EV {lo:.0%}-{hi:.0%}" if hi < 9 else f"EV {lo:.0%}+", extra & (ev >= lo) & (ev < hi))
    for lo, hi in ((0.06, 0.09), (0.07, 0.09), (0.08, 0.09), (0.08, 9), (0.09, 9)):
        rep(f"EV {lo:.0%}-{hi:.0%}" if hi < 9 else f"EV {lo:.0%}+", extra & (ev >= lo) & (ev < hi))
