"""
Spreads plan step 1 (NHL): rebuild the gitignored history tables and the walk-forward shot-model predictions at DraftKings'
opener, 2021-22..2025-26, at two information lags. Runs in GitHub Actions (ESPN is not reachable from Claude's workspace).
Pre-registration: research/spreads/STEP1_NHL_PREREG.md.

  python research/spreads/step1_nhl_build.py .

Writes
  data/box_hist.csv, data/shots_hist.csv                    (gitignored; the workflow also pushes gzipped copies to the
                                                              `data-rebuild` branch so later audits do not need to refetch)
  research/spreads/nhl_holdout/dk_holdout_lag{1,0}_{season}.csv
      lag 1 = results and goalie/skater history through two days before the game (live setting; DK's opener posts ~31 h before
              puck drop, before the previous night's games are played)
      lag 0 = through the night before (look-ahead for an opener; used only to measure what that look-ahead was worth)

Each ESPN game summary is fetched once and shared by the box-score and shot parsers (one disk cache).
"""
import os, sys, json, pickle, hashlib
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_data as nd                                                            # noqa: E402

CACHE = os.path.join(W, "_tmp", "espn_summary_cache"); os.makedirs(CACHE, exist_ok=True)
os.makedirs(os.path.join(W, "_tmp"), exist_ok=True)
_raw_get = nd.get


def cached_get(url, tries=3, headers=None):
    p = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".json")
    if os.path.exists(p):
        return json.load(open(p))
    d = _raw_get(url, tries=6, headers=headers)
    json.dump(d, open(p, "w")); return d


nd.get = cached_get
import build_shots as bs                                                         # noqa: E402  (uses nd.get -> cached)

G = pd.read_csv(os.path.join(W, "data", "games_hist.csv"))
print("games", len(G), flush=True)


def one(g):
    try:
        return nd.box(g), bs.shots(g), None
    except Exception as e:                                                       # record and continue; counted below
        return [], [], f"{g}: {e}"


with ThreadPoolExecutor(16) as ex:
    out = list(ex.map(one, G.game_id))
errs = [e for _, _, e in out if e]
print("fetch errors", len(errs), errs[:10], flush=True)
B = pd.DataFrame([r for b, _, _ in out for r in b]).merge(G[["game_id", "date", "season"]], on="game_id")
S = pd.DataFrame([r for _, s, _ in out for r in s])
print("box rows", len(B), "games", B.game_id.nunique(), "| shots", len(S), "games", S.game_id.nunique(), flush=True)
if B.game_id.nunique() < 0.98 * len(G) or S.game_id.nunique() < 0.98 * len(G):
    sys.exit("ABORT: fewer than 98% of games fetched; not building predictions on partial data")
B.to_csv(os.path.join(W, "data", "box_hist.csv"), index=False)
S.to_csv(os.path.join(W, "data", "shots_hist.csv"), index=False)

# ------------------------------------------------------------------ walk-forward predictions (code from analysis/rule_audit_nhl.py)
import nhl_xg_model as xm, build_features as bf                                  # noqa: E402
T0 = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
GD = pd.read_csv(os.path.join(W, "data", "games_hist.csv"), parse_dates=["date"])
DK = pd.read_csv(os.path.join(W, "data", "nhl_prices.csv.gz")); DK = DK[DK.book == "draftkings"].drop(columns=["book", "event_id"])
OUT = os.path.join(W, "research", "spreads", "nhl_holdout"); os.makedirs(OUT, exist_ok=True)
SPLITS = ((2022, [2020, 2021]), (2023, [2020, 2021, 2022]), (2024, [2020, 2021, 2022, 2023]),
          (2025, [2021, 2022, 2023, 2024]), (2026, [2022, 2023, 2024, 2025]))
for lag in (1, 0):
    F1, _ = bf.build(GD, B, lag_days=lag); T1 = T0.copy().set_index("game_id")
    for c in ("home_gmix", "away_gmix", "home_miss_off_open", "away_miss_off_open", "home_n_out_open", "away_n_out_open"):
        T1[c] = F1.set_index("game_id")[c].reindex(T1.index)
    T1 = T1.reset_index()
    for test, train in SPLITS:
        xmod = xm.xg_model(S, T0, train); TG = xm.team_game_xg(xm.apply_xg(S, T0, xmod), T0)
        D = T1.drop(columns=[c for c in TG.columns if c != "game_id" and c in T1]).merge(TG, on="game_id", how="left")
        _, P, _ = xm.run(D, train, test, tot_cal="none", lag_days=lag, halflives=(None, 60))
        P["date"] = pd.to_datetime(P.date).dt.strftime("%Y-%m-%d")
        P = P.drop(columns=[c for c in P if c.startswith(("open_", "close_", "mid_"))]).merge(DK, on=["date", "home", "away"], how="left")
        P.to_csv(os.path.join(OUT, f"dk_holdout_lag{lag}_{test}.csv"), index=False)
        print("lag", lag, "season", test, "games", len(P), "with DK opener", int(P.open_home_ml.notna().sum()), flush=True)
