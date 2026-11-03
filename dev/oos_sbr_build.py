"""Build the 2011-2022 game table for the out-of-sample test: hockeyR team-game xG joined with SportsbookReview lines.
  python dev/oos_sbr_build.py WORKDIR      -> _tmp/oos_games.csv and backtests/oos_sbr_join_report.txt
See backtests/OOS_SBR_PREREG.md. Season label = END year (2012 = 2011-12), as in the rest of the repo."""
import os, sys
import numpy as np, pandas as pd

W = os.path.abspath(sys.argv[1])
X = pd.read_csv(os.path.join(W, "data/external/hockeyr/team_game_xg_2010_2023.csv.gz"))
S = pd.read_csv(os.path.join(W, "data/external/sbr/sbr_nhl_2011_2021_clean.csv.gz"))

# hockeyR full names -> codes (relocations kept as one franchise: Atlanta -> wpg, Phoenix -> ari)
FULL = {"Anaheim Ducks": "ana", "Arizona Coyotes": "ari", "Phoenix Coyotes": "ari", "Atlanta Thrashers": "wpg", "Boston Bruins": "bos",
        "Buffalo Sabres": "buf", "Calgary Flames": "cgy", "Carolina Hurricanes": "car", "Chicago Blackhawks": "chi", "Colorado Avalanche": "col",
        "Columbus Blue Jackets": "cbj", "Dallas Stars": "dal", "Detroit Red Wings": "det", "Edmonton Oilers": "edm", "Florida Panthers": "fla",
        "Los Angeles Kings": "la", "Minnesota Wild": "min", "Montréal Canadiens": "mtl", "MontrÃ©al Canadiens": "mtl", "Nashville Predators": "nsh",
        "New Jersey Devils": "nj", "New York Islanders": "nyi", "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
        "Pittsburgh Penguins": "pit", "San Jose Sharks": "sj", "Seattle Kraken": "sea", "St. Louis Blues": "stl", "Tampa Bay Lightning": "tb",
        "Toronto Maple Leafs": "tor", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk", "Washington Capitals": "wsh", "Winnipeg Jets": "wpg"}
NICK = {"Ducks": "ana", "Coyotes": "ari", "Arizonas": "ari", "Phoenix": "ari", "Bruins": "bos", "Sabres": "buf", "Flames": "cgy",
        "Hurricanes": "car", "Blackhawks": "chi", "Avalanche": "col", "Blue Jackets": "cbj", "Stars": "dal", "Red Wings": "det", "Oilers": "edm",
        "Panthers": "fla", "Kings": "la", "Wild": "min", "Canadiens": "mtl", "Predators": "nsh", "Devils": "nj", "Islanders": "nyi",
        "NY Islanders": "nyi", "Rangers": "nyr", "Senators": "ott", "Flyers": "phi", "Penguins": "pit", "Sharks": "sj", "Kraken": "sea",
        "SeattleKraken": "sea", "St.Louis": "stl", "Lightning": "tb", "Tampa": "tb", "Tampa Bay": "tb", "Maple Leafs": "tor", "Canucks": "van",
        "Golden Knights": "vgk", "Capitals": "wsh", "Jets": "wpg", "WinnipegJets": "wpg"}
rep = []

X = X[X.season_type == "R"].copy()
X["team_c"] = X.team.map(FULL); X["opp_c"] = X.opp.map(FULL)
assert X.team_c.notna().all() and X.opp_c.notna().all(), X[X.team_c.isna()].team.unique()
H = X[X.is_home == 1]; A = X[X.is_home == 0]
G = H[["game_id", "season", "game_date", "team_c", "opp_c", "final_for", "final_against", "xg_all_for", "att_for"]].merge(
    A[["game_id", "xg_all_for", "att_for"]], on="game_id", suffixes=("_h", "_a"))
G = G.rename(columns={"team_c": "home", "opp_c": "away", "final_for": "home_goals", "final_against": "away_goals",
                      "xg_all_for_h": "home_xg", "xg_all_for_a": "away_xg", "att_for_h": "home_att", "att_for_a": "away_att", "game_date": "date"})
G["season"] = G.season % 10000                      # 20112012 -> 2012 (END year)
rep.append(f"hockeyR regular-season games: {len(G)} ({G.season.min()}-{G.season.max()})")

S = S.copy()
S["home"] = S.home_team.map(NICK); S["away"] = S.away_team.map(NICK)
assert S.home.notna().all() and S.away.notna().all(), set(S.home_team[S.home.isna()]) | set(S.away_team[S.away.isna()])
S["home_reg"] = S.home_1stPeriod + S.home_2ndPeriod + S.home_3rdPeriod
S["away_reg"] = S.away_1stPeriod + S.away_2ndPeriod + S.away_3rdPeriod
L = S.rename(columns={"home_open_ml": "open_home_ml", "away_open_ml": "open_away_ml", "home_close_ml": "close_home_ml",
                      "away_close_ml": "close_away_ml", "open_over_under": "open_total", "close_over_under": "close_total",
                      "home_close_spread": "close_home_pl", "home_close_spread_odds": "close_home_pl_odds",
                      "away_close_spread_odds": "close_away_pl_odds", "home_final": "sbr_home_final", "away_final": "sbr_away_final"})
# SBR stores ONE price per total and it is the UNDER price: at 5.5, games posted at -121 or shorter went over only 43.6%,
# games posted at +106 or longer 54.1% (checked Nov 3, 2026). The over price is not recorded; it is rebuilt assuming the pair
# sums to 104.8% implied (a 20-cent line, e.g. under -130 -> over +110). An approximation, reported as such.
for ln in ("open", "close"):
    u = L[f"{ln}_over_under_odds"].astype(float).replace(0, np.nan)
    iu = np.where(u > 0, 100 / (u + 100), np.abs(u) / (np.abs(u) + 100))      # implied prob of the under
    io = np.clip(1.0476 - iu, 0.05, 0.95)                                      # over so the pair sums to ~104.8%
    L[f"{ln}_under_odds"] = u
    L[f"{ln}_over_odds"] = np.where(np.isnan(iu), np.nan, np.where(io >= 0.5, -100 * io / (1 - io), 100 * (1 - io) / io))
for c in ("open_home_ml", "open_away_ml", "close_home_ml", "close_away_ml", "close_home_pl_odds", "close_away_pl_odds"):
    L[c] = L[c].replace(0, np.nan)
L.loc[L.close_home_pl == 0, ["close_home_pl", "close_home_pl_odds", "close_away_pl_odds"]] = np.nan
L["date"] = pd.to_datetime(L.date)
# SBR quirk: the 2020-21 season (SBR label 2020) dates its January-March 2021 games as 2020. Shift those a year.
yr = (L.season == 2020) & (L.date < "2020-07-01")
rep.append(f"SBR 2020-21 rows dated a year early, shifted +1 year: {yr.sum()}")
L.loc[yr, "date"] = L.loc[yr, "date"] + pd.DateOffset(years=1)
G["date"] = pd.to_datetime(G.date)
dup = L.duplicated(["home", "away", "date"], keep=False)
rep.append(f"SBR duplicate team/date rows dropped: {dup.sum()}")
L = L[~dup]

# match on teams and date (allow +-1 day: SBR dates are sometimes the US date of a late game)
keep = ["home", "away", "date", "home_reg", "away_reg", "sbr_home_final", "sbr_away_final", "open_home_ml", "open_away_ml",
        "close_home_ml", "close_away_ml", "close_home_pl", "close_home_pl_odds", "close_away_pl_odds", "open_total", "open_over_odds",
        "open_under_odds", "close_total", "close_over_odds", "close_under_odds", "open_ml_ok", "close_ml_ok", "open_total_ok", "close_total_ok"]
M = G.merge(L[keep], on=["home", "away", "date"], how="left", indicator=True)
miss = M._merge == "left_only"
for shift in (1, -1):
    Ls = L[keep].copy(); Ls["date"] = Ls.date + pd.Timedelta(days=shift)
    m2 = G[miss.values].merge(Ls, on=["home", "away", "date"], how="left")
    ok = m2.home_reg.notna().values
    idx = np.where(miss.values)[0][ok]
    for c in keep[3:]: M.loc[M.index[idx], c] = m2.loc[ok, c].values
    miss = M.home_reg.isna()
M = M.drop(columns="_merge")
M["match"] = M.home_reg.notna().astype(int)
M["score_agree"] = ((M.sbr_home_final == M.home_goals) & (M.sbr_away_final == M.away_goals)).astype(int)
for s, g in M.groupby("season"):
    rep.append(f"  {s}: games {len(g)}, matched to SBR {g.match.sum()} ({g.match.mean():.1%}), final score agrees {g[g.match == 1].score_agree.mean():.1%}")
sb_unmatched = L[(L.date >= "2011-10-01") & (L.date <= "2022-05-01")].merge(M[["home", "away", "date"]], on=["home", "away", "date"], how="left", indicator=True)
rep.append(f"SBR rows (Oct 2011 - Apr 2022, incl. playoffs) not in hockeyR regular season: {(sb_unmatched._merge == 'left_only').sum()} (playoffs, ±1 day shifts)")

# finals: SBR's final counts the shootout winner's goal (the official result); hockeyR's goal-event count does not.
# So: matched games take SBR's final and SBR's period scores (regulation). Disagreements are checked to be shootout-only.
d = (M.match == 1) & (M.score_agree == 0)
so_only = d & ((M.sbr_home_final + M.sbr_away_final) - (M.home_goals + M.away_goals) == 1) & (M.home_goals == M.away_goals) & (M.home_reg == M.away_reg)
rep.append(f"matched games whose finals differ: {d.sum()}; explained by one shootout goal: {so_only.sum()}; other: {(d & ~so_only).sum()} (regulation set missing)")
M.loc[d & ~so_only, ["home_reg", "away_reg"]] = np.nan
m = M.match == 1
M.loc[m, "home_goals"] = M.loc[m, "sbr_home_final"]; M.loc[m, "away_goals"] = M.loc[m, "sbr_away_final"]
# unmatched games (2010-11, 2022-23, a few others): regulation = final only when the margin is 2+ (cannot be OT/SO);
# one-goal and tied finals stay missing as results (still counted for rest days). hockeyR ties = shootout games: final +1 unknown side.
um = M.match == 0
fill = um & ((M.home_goals - M.away_goals).abs() >= 2)
M.loc[fill, "home_reg"] = M.loc[fill, "home_goals"]; M.loc[fill, "away_reg"] = M.loc[fill, "away_goals"]
M.loc[um & ~fill, ["home_goals", "away_goals"]] = np.nan
rep.append(f"unmatched games given regulation = final (margin 2+): {fill.sum()}; unmatched games with no usable result: {(um & ~fill).sum()}")
reg_ok = M.home_reg.notna()
tie = (M.home_reg == M.away_reg) & reg_ok
rep.append(f"regulation ties among games with regulation scores: {tie[reg_ok].mean():.1%} (real NHL ~22-24%)")
rep.append(f"games with xG missing: {(M.home_xg.isna() | M.away_xg.isna()).sum()}")

# Swapped-side rows: the opener or closer has the teams' prices reversed (e.g. VAN-BOS open -320/+250, close +100/-120).
# Flag from the lines alone (no results): open-to-close move in the de-vigged home win chance over 10 points (the 99th
# percentile of real moves is ~7.8). Added Nov 3, 2026 after the holdout showed +250 bets with +26% "CLV".
dv = lambda o: np.where(o > 0, 1 + o / 100, 1 + 100 / np.abs(o))
nvo = (1 / dv(M.open_home_ml)) / (1 / dv(M.open_home_ml) + 1 / dv(M.open_away_ml))
nvc = (1 / dv(M.close_home_ml)) / (1 / dv(M.close_home_ml) + 1 / dv(M.close_away_ml))
M["ml_move_ok"] = (np.abs(nvo - nvc) <= 0.10).astype(int)
rep.append(f"moneyline rows with an open-to-close move over 10 win-% points (likely swapped sides), flagged ml_move_ok=0: {((M.match == 1) & (M.ml_move_ok == 0) & M.open_home_ml.notna() & M.close_home_ml.notna()).sum()}")

# columns the repo's model code expects
for side in ("home", "away"):
    M[f"{side}_goalie"] = np.nan; M[f"{side}_gmix"] = np.nan
    for c in ("miss_off", "miss_off_open", "n_out", "n_out_open"): M[f"{side}_{c}"] = 0.0
M["open_home_pl"] = np.nan; M["open_home_pl_odds"] = np.nan; M["open_away_pl_odds"] = np.nan
M["game_id"] = M.game_id.astype(int)
M["date"] = M.date.dt.strftime("%Y-%m-%d")
os.makedirs(os.path.join(W, "_tmp"), exist_ok=True)
M.to_csv(os.path.join(W, "_tmp", "oos_games.csv"), index=False)
open(os.path.join(W, "backtests", "oos_sbr_join_report.txt"), "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
