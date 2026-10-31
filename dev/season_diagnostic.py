"""
Cold-stretch diagnostic: fit mixed models on THIS SEASON's games only (in-sample, for description, not prediction),
compare them with what the live models believe, and break down where the live models' bets are losing.

Writes research/cold_stretch/YYYY-MM-DD/: season-only team and goalie ratings, model-vs-season comparisons, loss
breakdowns, and summary.json. Rerun any time a model goes cold:  python dev/season_diagnostic.py WORKDIR
"""
import os, sys, json, datetime as dt
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_data as nd, nhl_mixed_model as nm, nhl_xg_model as xm, build_features as bf, espn

SEASON, TRAIN = 2027, [2022, 2023, 2024, 2025, 2026]
TODAY = pd.Timestamp(dt.date.today())
OUT = os.path.join(W, "research", "cold_stretch", str(TODAY.date())); os.makedirs(OUT, exist_ok=True)
ST = os.path.join(W, "state")
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))

# ---------------------------------------------------------------- this season's games, features, xG
P0 = pd.read_csv(os.path.join(ST, "picks_log.csv"), parse_dates=["date"])
games = P0[["game_id", "date", "home", "away"]].copy(); games["season"] = SEASON
sb = {}
for d in sorted(games.date.unique()):
    for r in nd.scoreboard(d): sb[r["game_id"]] = r
for c in ("home_goals", "away_goals", "home_reg", "away_reg", "ending"):
    games[c] = games.game_id.map(lambda g: sb.get(g, {}).get(c, np.nan))
games = games[games.home_goals.notna()].reset_index(drop=True)
T = pd.read_csv(os.path.join(W, "data", "training_games.csv"), parse_dates=["date"])
box = pd.read_csv(os.path.join(ST, "box_2026_27.csv")); prior_box = pd.read_csv(os.path.join(W, "data", "box_2025_26.csv"))
allg = pd.concat([T[T.season == 2026][["game_id", "date", "season", "home", "away"]], games[["game_id", "date", "season", "home", "away"]]])
allg["date"] = pd.to_datetime(allg.date)
F, _ = bf.build(allg, pd.concat([prior_box, box]))
F = F[F.season == SEASON].set_index("game_id")
for c in F.columns:
    if c.startswith(("home_", "away_")) and c not in games: games[c] = games.game_id.map(F[c])
S = pd.read_csv(os.path.join(ST, "shots_2026_27.csv"), low_memory=False)
TG = xm.team_game_xg(xm.apply_xg(S, games, json.load(open(os.path.join(W, "data", "xg_model.json")))), games).set_index("game_id")
for c in ("home_xg", "away_xg", "home_att", "away_att"): games[c] = games.game_id.map(TG[c])
games = nm.add_rest(games)
names = dict(zip(pd.concat([prior_box, box]).playerid, pd.concat([prior_box, box]).player))

# ---------------------------------------------------------------- 1. season-only mixed models (in-sample)
# Ratings estimated from THIS season's games only (no carry-over from last season). How much teams and goalies are allowed
# to differ (the variance components) comes from the training seasons: 200-odd games are too few to estimate it (REML
# on this season alone pushes the defense variance to zero).
Ttr = pd.concat([nm.add_rest(T[T.season == s]) for s in TRAIN], ignore_index=True)
fa_tr, fb_tr, _, _ = xm.fit_block(Ttr, TRAIN)                              # shot-model variance ratios
fitg, O, D, GG, _ = nm.fit_season_block(Ttr, TRAIN)                        # goals-model variance ratios
L = xm.rows(games); L = L[L.goals.notna()].reset_index(drop=True)
gk = lambda L: [int(g) if not pd.isna(g) else None for g in L.goalie]
Zg, ig = xm.zblocks(L, [("off", lambda L: list(L.off)), ("def", lambda L: list(L["def"])), ("goalie", gk)])
Xg = np.column_stack([np.ones(len(L)), L.home, L.b2b_off, L.b2b_def]).astype(float)
def blup(X, Zs, y, a):
    Z = np.hstack(Zs); W_ = np.hstack([X, Z]); p = X.shape[1]; C = W_.T @ W_
    C[p:, p:] += np.diag(np.concatenate([np.full(z.shape[1], ai) for z, ai in zip(Zs, a)]))
    sol = np.linalg.solve(C, W_.T @ y); u, out, k = sol[p:], [], 0
    for z in Zs: out.append(u[k:k + z.shape[1]]); k += z.shape[1]
    return dict(b=sol[:p], u=out)
fg = blup(Xg, Zg, L.goals.values.astype(float), fitg["a"])
reml_season = xm.fit(Xg, Zg, L.goals.values.astype(float))                # for reference only
Lx = L[L.xg.notna()].reset_index(drop=True)
Zx, ix = xm.zblocks(Lx, [("off", lambda L: list(L.off)), ("def", lambda L: list(L["def"]))])
fx = blup(np.column_stack([np.ones(len(Lx)), Lx.home, Lx.b2b_off, Lx.b2b_def]).astype(float), Zx, Lx.xg.values.astype(float), fa_tr["a"])
Lx["resid"] = Lx.goals - Lx.xg
Zc, ic = xm.zblocks(Lx, [("off", lambda L: list(L.off)), ("goalie", gk)])
fc = blup(np.ones((len(Lx), 1)), Zc, Lx.resid.values.astype(float), fb_tr["a"])
eff = lambda f, idx, j: {k: f["u"][j][i] for k, i in idx[j].items()}
season = pd.DataFrame({"goals_off": eff(fg, ig, 0), "goals_def": eff(fg, ig, 1), "xg_off": eff(fx, ix, 0), "xg_def": eff(fx, ix, 1),
                       "finishing": eff(fc, ic, 0)})
season["goals_net"] = season.goals_off - season.goals_def; season["xg_net"] = season.xg_off - season.xg_def
gseason = pd.DataFrame({"season_goals_allowed_effect": eff(fg, ig, 2), "season_gsax_effect": eff(fc, ic, 1)})
gp = L.groupby("goalie").size()
gseason["starts"] = gseason.index.map(lambda k: int(gp.get(k, 0))); gseason["goalie"] = gseason.index.map(lambda k: names.get(int(k), k))

# ---------------------------------------------------------------- 2. what the live models believe now (lag 0)
cur = games.drop(columns=[c for c in games.columns if c in ("tip_et",)])
sg, Pg, eg = nm.run(pd.concat([T, cur], ignore_index=True), TRAIN, SEASON)
sx, Px, ex = xm.run(pd.concat([T, cur], ignore_index=True), TRAIN, SEASON)
# starting point of the goals model = rho x last season's ratings
live = pd.DataFrame({"goals_model_net_now": {t: eg["effects"]["O"][t] - eg["effects"]["D"][t] for t in eg["effects"]["O"]},
                     "shot_model_xg_net_now": {t: ex["effects"]["O"][t] - ex["effects"]["D"][t] for t in ex["effects"]["O"]},
                     "goals_model_net_start": {t: sg["rho"]["offense"] * O.get((2026, t), 0) - sg["rho"]["defense"] * D.get((2026, t), 0) for t in season.index}})
comp = season.join(live)
rec = pd.concat([games.assign(team=games.home, gf=games.home_goals, ga=games.away_goals), games.assign(team=games.away, gf=games.away_goals, ga=games.home_goals)])
rec["w"] = (rec.gf > rec.ga).astype(int)
comp = comp.join(rec.groupby("team").agg(gp=("w", "size"), wins=("w", "sum"), gf=("gf", "sum"), ga=("ga", "sum")))
comp["gap_goals_model"] = comp.goals_net - comp.goals_model_net_now        # + = team is better this season than the goals model thinks
comp["gap_shot_model"] = comp.xg_net - comp.shot_model_xg_net_now
comp.round(3).sort_values("goals_net", ascending=False).to_csv(os.path.join(OUT, "team_ratings_season_vs_models.csv"))
gnow = pd.DataFrame({"goals_model_now": eg["effects"]["goalies"], "shot_model_now": ex["effects"]["goalies"]})
gcomp = gseason.join(gnow, how="left").sort_values("starts", ascending=False)
gcomp.round(3).to_csv(os.path.join(OUT, "goalie_ratings_season_vs_models.csv"))

# ---------------------------------------------------------------- 3. where the live models' rule bets lose
def rule_bets(path, name):
    p = pd.read_csv(path, parse_dates=["date"])
    out = []
    for mk in ("moneyline", "puck line"):
        ev = pd.to_numeric(p[f"open_{mk}_ev"], errors="coerce")
        s = p[(ev >= 0.06) & p[f"open_{mk}_result"].isin(["W", "L", "P"])].copy()
        s["market"], s["model"] = mk, name
        s["side"], s["price"] = s[f"open_{mk}_bet"], pd.to_numeric(s[f"open_{mk}_price"])
        s["p_model"], s["ev"] = pd.to_numeric(s[f"open_{mk}_p"]), pd.to_numeric(s[f"open_{mk}_ev"])
        s["profit"], s["clv"] = pd.to_numeric(s[f"open_{mk}_profit"]), pd.to_numeric(s[f"open_{mk}_clv"])
        out.append(s[["game_id", "date", "home", "away", "model", "market", "side", "price", "p_model", "ev", "profit", "clv", "open_home_ml", "open_away_ml"]])
    return pd.concat(out)
R = pd.concat([rule_bets(os.path.join(ST, "picks_log.csv"), "goals"), rule_bets(os.path.join(ST, "picks_log_xg.csv"), "shot")])
R["team_bet"] = np.where(R.side == "home", R.home, R.away); R["team_against"] = np.where(R.side == "home", R.away, R.home)
R["dog"] = R.price > 0
R["p_implied"] = 1 / dec(R.price)
R["price_band"] = pd.cut(R.price, [-1000, -150, -101, 149, 249, 2000], labels=["fav -150+", "fav -101..-149", "dog +100..+149", "dog +150..+249", "dog +250+"])
R["week"] = R.date.dt.to_period("W").astype(str)
R.to_csv(os.path.join(OUT, "rule_bets.csv"), index=False)
agg = lambda g: pd.Series(dict(bets=len(g), wins=int((g.profit > 0).sum()), units=round(g.profit.sum(), 1), roi=round(g.profit.mean(), 3),
                               model_win_prob=round(g.p_model.mean(), 3), price_needs=round(g.p_implied.mean(), 3),
                               actual_win_rate=round((g.profit > 0).mean(), 3), avg_clv=round(g.clv.mean(), 4)))
tables = {k: R.groupby(["model", k], observed=True).apply(agg) for k in ("market", "dog", "price_band", "week")}
by_team = R.groupby(["model", "team_bet"]).apply(agg).reset_index().sort_values("units")
by_against = R.groupby(["model", "team_against"]).apply(agg).reset_index().sort_values("units")
for k, t in tables.items(): t.to_csv(os.path.join(OUT, f"losses_by_{k}.csv"))
by_team.to_csv(os.path.join(OUT, "losses_by_team_bet_on.csv"), index=False); by_against.to_csv(os.path.join(OUT, "losses_by_team_bet_against.csv"), index=False)

# ---------------------------------------------------------------- 4. the market and the league this season vs before
P = pd.read_csv(os.path.join(ST, "picks_log.csv"))
P = P[P.home_goals.notna() & P.open_home_ml.notna()]
ih, ia = 1 / dec(P.open_home_ml), 1 / dec(P.open_away_ml); P["p_home_mkt"] = ih / (ih + ia)
P["fav_won"] = np.where(P.p_home_mkt >= 0.5, P.home_goals > P.away_goals, P.away_goals > P.home_goals)
P["p_fav"] = np.maximum(P.p_home_mkt, 1 - P.p_home_mkt)
P["fav_band"] = pd.cut(P.p_fav, [0.5, 0.55, 0.6, 0.65, 0.7, 1], include_lowest=True)
fav_now = P.groupby("fav_band", observed=True).agg(games=("fav_won", "size"), market_said=("p_fav", "mean"), fav_won=("fav_won", "mean")).round(3)
H = pd.concat([pd.read_csv(os.path.join(W, "_tmp", f"backtest_{t}.csv")) for t in (2025, 2026)]) if os.path.exists(os.path.join(W, "_tmp", "backtest_2025.csv")) else T[T.season.isin([2025, 2026])]
H = H[H.open_home_ml.notna()]
ih, ia = 1 / dec(H.open_home_ml), 1 / dec(H.open_away_ml); H["p_home_mkt"] = ih / (ih + ia)
H["fav_won"] = np.where(H.p_home_mkt >= 0.5, H.home_goals > H.away_goals, H.away_goals > H.home_goals); H["p_fav"] = np.maximum(H.p_home_mkt, 1 - H.p_home_mkt)
H["fav_band"] = pd.cut(H.p_fav, [0.5, 0.55, 0.6, 0.65, 0.7, 1], include_lowest=True)
fav_before = H.groupby("fav_band", observed=True).agg(games=("fav_won", "size"), market_said=("p_fav", "mean"), fav_won=("fav_won", "mean")).round(3)
pd.concat({"this season": fav_now, "2024-26": fav_before}, axis=1).to_csv(os.path.join(OUT, "favorites_vs_market.csv"))
Tl = T[T.season.isin(TRAIN)]
league = pd.DataFrame({
    "this season": dict(goals_per_game=(games.home_goals + games.away_goals).mean(), reg_goals_per_game=(games.home_reg + games.away_reg).mean(),
                        xg_per_game=(games.home_xg + games.away_xg).mean(), home_win_pct=(games.home_goals > games.away_goals).mean(),
                        overtime_pct=(games.home_reg == games.away_reg).mean(), shooting_vs_xg=((games.home_reg + games.away_reg).sum() / (games.home_xg + games.away_xg).sum())),
    "training seasons": dict(goals_per_game=(Tl.home_goals + Tl.away_goals).mean(), reg_goals_per_game=(Tl.home_reg + Tl.away_reg).mean(),
                             xg_per_game=(Tl.home_xg + Tl.away_xg).mean(), home_win_pct=(Tl.home_goals > Tl.away_goals).mean(),
                             overtime_pct=(Tl.home_reg == Tl.away_reg).mean(), shooting_vs_xg=((Tl.home_reg + Tl.away_reg).sum() / (Tl.home_xg + Tl.away_xg).sum()))}).round(3)
league.to_csv(os.path.join(OUT, "league_this_season_vs_training.csv"))
fixed = dict(season_only=dict(zip(["intercept", "home", "b2b_off", "b2b_def"], np.round(fg["b"], 3).tolist())),
             goals_model=sg["fixed_effects"], season_reml_sd=dict(team_off=reml_season["sd"][0], team_def=reml_season["sd"][1], goalie=reml_season["sd"][2], resid=reml_season["s2e"] ** .5),
             goals_model_sd=dict(team_off=sg["sd_offense"], team_def=sg["sd_defense"], goalie=sg["sd_goalie"]))
mg = Pg.home_goals - Pg.away_goals
acc = dict(games=int(len(P)), market_open_brier=float(((P.p_home_mkt - (P.home_goals > P.away_goals)) ** 2).mean()),
           goals_model_brier=float(((Pg.p_home_win_open - (mg > 0)) ** 2).mean()), shot_model_brier=float(((Px.p_home_win_open - (mg > 0)) ** 2).mean()))
json.dump(dict(date=str(TODAY.date()), games=int(len(games)), fixed_effects=fixed, accuracy=acc, league=league.to_dict()),
          open(os.path.join(OUT, "summary.json"), "w"), indent=1, default=float)

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 80); pd.set_option("display.max_columns", 30)
print(league); print(json.dumps(fixed, indent=1, default=float)); print(json.dumps(acc, indent=1))
print(pd.concat({"this season": fav_now, "2024-26": fav_before}, axis=1))
for k, t in tables.items(): print(t)
print(by_team.groupby("model").head(5)); print(by_against.groupby("model").head(5))
print(comp[["gp", "wins", "gf", "ga", "goals_net", "xg_net", "finishing", "goals_model_net_now", "shot_model_xg_net_now", "goals_model_net_start", "gap_goals_model", "gap_shot_model"]].round(2).sort_values("gap_goals_model"))
print(gcomp.head(25).round(3))
