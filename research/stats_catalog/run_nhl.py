"""Apply every course concept to the NHL shot model (moneyline first, totals where the concept fits).
In-sample data (DK): live shot model setup (goalie effects, one-day lag) 2024-25 and 2025-26 at DraftKings opening prices.
Out-of-sample data (SBR): the pre-registered holdout, team-only shot model, 2016-17..2021-22 at SBR openers (trusted rows).
  python run_nhl.py   (needs nhl_games.csv from build_nhl.py) -> results.json, oos.json"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.outliers_influence import variance_inflation_factor, OLSInfluence
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.proportion import proportion_confint, proportions_ztest
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
rng = np.random.default_rng(2026)
R = {}; PV = {}
def rec(k, txt, p=None):
    R[k] = txt; print(f"\n[{k}] {txt}")
    if p is not None and np.isfinite(p): PV[k] = float(p)
dec = lambda o: np.where(np.asarray(o, float) > 0, 1 + np.asarray(o, float) / 100, 1 + 100 / np.abs(np.asarray(o, float)))
lg = lambda p: np.log(p / (1 - p))

def prep(G):
    G = G.dropna(subset=["home_goals", "open_home_ml", "open_away_ml", "close_home_ml", "close_away_ml"]).copy()
    G["date"] = pd.to_datetime(G.date); G["month"] = G.date.dt.month; G["mname"] = G.date.dt.strftime("%b")
    G["hw"] = (G.home_goals > G.away_goals).astype(int)
    G["tot"] = G.home_goals + G.away_goals
    G["ot"] = (G.home_reg == G.away_reg).astype(int)
    G["edge"] = G.p_home - G.nv_open                     # model minus market, home side
    G["res"] = G.hw - G.nv_open                           # outcome minus market, home side
    G["move"] = G.nv_close - G.nv_open
    for side in ("home", "away"):
        p = G.p_home if side == "home" else 1 - G.p_home
        G[f"ev_{side}"] = p * dec(G[f"open_{side}_ml"]) - 1
    G["side"] = np.where(G.ev_home >= G.ev_away, "home", "away"); G["ev"] = G[["ev_home", "ev_away"]].max(axis=1)
    G["sgn"] = np.where(G.side == "home", 1, -1)
    G["k"] = G.sort_values("date").groupby(["season", "home"]).cumcount()  # placeholder
    return G
def bets(G):
    B = G[G.ev >= 0.06].copy()
    B["win"] = np.where(B.side == "home", B.hw, 1 - B.hw)
    B["price"] = np.where(B.side == "home", B.open_home_ml, B.open_away_ml)
    B["d"] = dec(B.price); B["profit"] = np.where(B.win == 1, B.d - 1, -1.0)
    B["q"] = np.where(B.side == "home", B.nv_open, 1 - B.nv_open)          # market prob of our side at the open
    B["qc"] = np.where(B.side == "home", B.nv_close, 1 - B.nv_close)
    B["pm"] = np.where(B.side == "home", B.p_home, 1 - B.p_home)
    B["clv"] = B.qc - B.q; B["r"] = B.win - B.q
    B["fav"] = np.where(B.q >= 0.5, "fav", "dog"); B["b2b"] = np.where(B.side == "home", B.b2b_home, B.b2b_away)
    B["be"] = 1 / B.d
    return B.sort_values(["date", "home"]).reset_index(drop=True)
def overs(G):
    O = G.dropna(subset=["open_total", "open_over_odds", "p_over"]).copy()
    O["ev_o"] = O.p_over * dec(O.open_over_odds) + O.p_push - 1
    O = O[O.ev_o >= 0.06].copy(); O = O[O.tot != O.open_total]
    O["win"] = (O.tot > O.open_total).astype(int); O["profit"] = np.where(O.win == 1, dec(O.open_over_odds) - 1, -1.0)
    O["tmove"] = O.close_total - O.open_total
    return O

ALL = pd.read_csv("nhl_games.csv")
G = prep(ALL[ALL.src == "dk"]); B = bets(G); OV = overs(G)
G["fav_h0"] = (G.nv_open >= 0.5).astype(int); GT = G.dropna(subset=["open_total"]).assign(tres=lambda d: d.tot - d.open_total)
H = prep(ALL[(ALL.src == "sbr") & (ALL.season >= 2017)]); H = H[H.trusted == 1]; BH = bets(H); OVH = overs(H[H.tot_ok == 1])
n, w = len(B), int(B.win.sum()); ph = w / n
print("DK games", len(G), "ML bets", n, "units", B.profit.sum(), "overs", len(OV), OV.profit.sum())
print("SBR games", len(H), "ML bets", len(BH), BH.profit.sum(), "overs", len(OVH), OVH.profit.sum())
OOS = {}
def oos(k, txt): OOS[k] = txt; print(f"   OOS[{k}] {txt}")

# ===== study design
both = pd.concat([G.assign(era="2024-26"), H.assign(era="2016-22")])
t, p = stats.ttest_1samp(both.res, 0); sea = both.groupby("season").res.mean()
fav_res = np.where(both.nv_open >= 0.5, both.res, -both.res)
rec("A01", f"Population = every NHL game the market prices; sample = {len(both):,} games 2016-17..2021-22 (SBR) + 2024-26 (DraftKings). Home teams won {both.hw.mean():.1%} vs a no-vig opener price of "
    f"{both.nv_open.mean():.1%}: bias {both.res.mean():+.3f} (t={t:.2f}, p={p:.2f}). By season {sea.min():+.3f} to {sea.max():+.3f}. Favorites vs their price: {np.mean(fav_res):+.3f}. "
    "The no-vig opener is close to unbiased; there's no free home or favorite lean.", p)
pos, neg = B[B.clv > 0.005], B[B.clv < -0.005]
rec("A02", f"Observational: bets where the price later moved toward us (no-vig chance up 0.5+ pts) won {pos.win.mean():.1%} at an average market price of {pos.q.mean():.1%} (n={len(pos)}); moved against "
    f"{neg.win.mean():.1%} vs {neg.q.mean():.1%} (n={len(neg)}). ROI {pos.profit.mean():+.1%} vs {neg.profit.mean():+.1%}. The move doesn't cause the win; both come from news (goalies, lineups).")
G["b2b_diff"] = G.b2b_home - G.b2b_away
a1 = smf.ols("hw ~ b2b_diff", G).fit(); a2 = smf.ols("res ~ b2b_diff", G).fit(); a3 = smf.ols("I(hw - p_home) ~ b2b_diff", G).fit()
rec("A03", f"Back-to-backs (home minus away b2b): raw home win rate {a1.params.b2b_diff:+.3f} per b2b (p={a1.pvalues.b2b_diff:.3f}); vs the market {a2.params.b2b_diff:+.3f} (p={a2.pvalues.b2b_diff:.3f}); "
    f"vs the model {a3.params.b2b_diff:+.3f} (p={a3.pvalues.b2b_diff:.3f}). The raw effect is partly confounded with goalie choice (backups start b2bs), but the opener does NOT fully price it here; the shot model (which knows the likely goalie and b2b) mostly does.", a2.pvalues.b2b_diff)
H["b2b_diff"] = H.b2b_home - H.b2b_away; ah = smf.ols("res ~ b2b_diff", H).fit(); ahm = smf.ols("I(hw - p_home) ~ b2b_diff", H).fit()
oos("A03", f"2016-22: vs the market {ah.params.b2b_diff:+.3f} per b2b (p={ah.pvalues.b2b_diff:.3f}); vs the team-only model {ahm.params.b2b_diff:+.3f} (p={ahm.pvalues.b2b_diff:.3f}); b2b games {int((H.b2b_diff!=0).sum())}")
def persist(D):
    tl = pd.concat([D[["season", "date", "home", "res"]].rename(columns={"home": "t"}), D[["season", "date", "away", "res"]].rename(columns={"away": "t"}).assign(res=lambda d: -d.res)]).sort_values("date")
    tl["k"] = tl.groupby(["season", "t"]).cumcount()
    X = pd.concat([tl[tl.k < 41].groupby(["season", "t"]).res.mean(), tl[tl.k >= 41].groupby(["season", "t"]).res.mean()], axis=1, keys=["h1", "h2"]).dropna()
    top = X[X.h1 >= X.h1.quantile(0.8)]; r_ = stats.pearsonr(X.h1, X.h2)
    return X, top, r_
X, top, r_ = persist(G)
rec("A04", f"Selection on past success: teams in the top 20% for beating the moneyline in their first 41 games (+{top.h1.mean():.3f} wins/game above price) were {top.h2.mean():+.3f} the rest of the way; "
    f"first-half vs second-half r={r_[0]:+.2f} (p={r_[1]:.2f}, {len(X)} team-seasons). 'Teams that beat the books' mostly stop.", r_[1])
X2, top2, r2 = persist(H); oos("A04", f"2016-22: top-20% teams {top2.h1.mean():+.3f} -> {top2.h2.mean():+.3f}, r={r2[0]:+.2f} (p={r2[1]:.2f}, {len(X2)} team-seasons)")
se_srs = B.profit.std(ddof=1) / np.sqrt(n)
gd = B.groupby("date").profit.agg(["sum", "count"]).values
bc = np.array([(lambda i: gd[i, 0].sum() / gd[i, 1].sum())(rng.integers(0, len(gd), len(gd))) for _ in range(4000)])
rec("A05", f"ROI {B.profit.mean():+.2%}. SE as a simple random sample {se_srs:.2%}; cluster bootstrap by game night {bc.std():.2%} (ratio {bc.std()/se_srs:.2f}). Same-night bets behave as independent.")
G["early"] = (G.k < 10).astype(int)
br = lambda D, c: ((D[c] - D.hw) ** 2).mean()
e_, l_ = G[G.early == 1], G[G.early == 0]
rec("A06", f"Who's in the test set: {len(e_)} games among a home team's first 10 home games vs {len(l_)} later. Brier early: model {br(e_,'p_home'):.4f}, opener {br(e_,'nv_open'):.4f}; later: model {br(l_,'p_home'):.4f}, opener {br(l_,'nv_open'):.4f}. "
    f"ROI of model bets in those early games {B[B.set_index(['date','home']).index.isin(e_.set_index(['date','home']).index)].profit.mean():+.1%} (n={B.set_index(['date','home']).index.isin(e_.set_index(['date','home']).index).sum()}) vs later {B[~B.set_index(['date','home']).index.isin(e_.set_index(['date','home']).index)].profit.mean():+.1%}. "
    "Like the Literary Digest poll, a result on 'all games' can hide a subgroup the model handles differently.")
perm = []
od, uo = np.where(B.side == "home", B.open_away_ml, B.open_home_ml), None
lose_alt = np.where(B.side == "home", 1 - B.hw, B.hw)
d_alt = dec(od)
for _ in range(5000):
    f = rng.random(n) < 0.5
    pr = np.where(f, np.where(lose_alt == 1, d_alt - 1, -1.0), B.profit.values); perm.append(pr.mean())
perm = np.array(perm); pp = (np.sum(perm >= B.profit.mean()) + 1) / 5001
rec("A07", f"Randomization test: same {n} games, side picked by coin flip at the real opening prices, 5,000 times: mean ROI {perm.mean():+.2%}, 99th pct {np.percentile(perm,99):+.2%}; model {B.profit.mean():+.2%}. p={pp:.4f}.", pp)
B["eb"] = pd.cut(B.ev, [0.06, 0.09, 0.12, 0.20, 9], right=False, labels=["6-9%", "9-12%", "12-20%", "20%+"])
f0 = anova_lm(smf.ols("profit ~ C(eb)", B).fit()); f1 = anova_lm(smf.ols("profit ~ C(eb) + C(season)", B).fit())
rec("A08", f"Edge (EV) bucket as treatment, profit as response. No blocks: F={f0.F.iloc[0]:.2f}, p={f0['PR(>F)'].iloc[0]:.3f}; blocked by season: p={f1['PR(>F)'].iloc[0]:.3f}. ROI by bucket: "
    + ", ".join(f"{k} {v:+.1%} (n={c})" for k, v, c in zip(B.groupby('eb').profit.mean().index, B.groupby('eb').profit.mean(), B.groupby('eb').size())) + ".", f1['PR(>F)'].iloc[0])
BH["eb"] = pd.cut(BH.ev, [0.06, 0.09, 0.12, 0.20, 9], right=False, labels=["6-9%", "9-12%", "12-20%", "20%+"])
oos("A08", "2016-22 ROI by EV bucket: " + ", ".join(f"{k} {v:+.1%}" for k, v in BH.groupby('eb').profit.mean().items()))
B["wd"] = B.date.dt.dayofweek
al = anova_lm(smf.ols("r ~ C(fav) + C(season) + C(wd)", B).fit(), typ=2)
rec("A09", f"Two blocking factors (season, weekday), Latin-square idea: favorite vs underdog bets after both blocks p={al['PR(>F)']['C(fav)']:.3f}; weekday p={al['PR(>F)']['C(wd)']:.3f}.", al['PR(>F)']['C(wd)'])
fx = anova_lm(smf.ols("r ~ C(fav) * C(side)", B).fit(), typ=2); cell = B.groupby(["fav", "side"]).agg(roi=("profit", "mean"), n=("profit", "size"))
rec("A10", "2x2 factorial, favorite/underdog x home/away (response: won minus market price): ROI " + "; ".join(f"{f} {s} {r.roi:+.1%} (n={int(r.n)})" for (f, s), r in cell.iterrows())
    + f". Interaction p={fx['PR(>F)']['C(fav):C(side)']:.3f}.", fx['PR(>F)']['C(fav):C(side)'])
fc = smf.ols("r ~ C(fav) + q", B).fit(); fd = smf.ols("r ~ C(fav)", B).fit()
rec("A11", f"ANCOVA: favorite-vs-underdog gap in (won - market price) unadjusted {fd.params['C(fav)[T.fav]']:+.3f} (p={fd.pvalues['C(fav)[T.fav]']:.3f}); adjusted for the price itself {fc.params['C(fav)[T.fav]']:+.3f} "
    f"(p={fc.pvalues['C(fav)[T.fav]']:.3f}).", fc.pvalues['C(fav)[T.fav]'])
rc = np.corrcoef(G.home_reg - G.lam_home, G.away_reg - G.lam_away)[0, 1]
rec("A12", f"Experimental unit = game; the two team scores are measurements within it. Regulation goals above expectation correlate r={rc:+.2f} between the two teams "
    "(slightly negative: score effects and empty nets, a team that falls behind pulls its goalie and gives up more). Counting team-games as independent would double n falsely.")

# ===== description
end = pd.Series(np.where(G.ot == 1, "OT/SO", "regulation")).value_counts(normalize=True)
rec("A13", f"Bar chart: {end.get('regulation',0):.1%} of games end in regulation, {end.get('OT/SO',0):.1%} go to OT/shootout. Moneyline bets: {w} wins, {n-w} losses (no pushes on a moneyline).")
sh = B.groupby(["fav", "side"]).size() / n
rec("A14", "Pie shares of bets: " + ", ".join(f"{f} {s} {v:.0%}" for (f, s), v in sh.items()) + f". Underdogs are {np.mean(B.fav=='dog'):.0%} of bets: the model's value mostly lives on dogs.")
rec("A15", f"Histogram of total goals: mean {G.tot.mean():.2f}, median {G.tot.median():.0f}, skew {stats.skew(G.tot):+.2f}, excess kurtosis {stats.kurtosis(G.tot):+.2f}. Right-skewed count data with a floor at 0.")
vc = G.tot.value_counts(normalize=True).sort_index()
rec("A16", "Relative frequency of total goals: " + ", ".join(f"{int(k)}: {v:.1%}" for k, v in vc.items() if v > 0.01) + f". At 5.5/6/6.5 lines one goal moves a total bet from loss to win; a 6 total pushes {np.mean(G.tot==6):.1%} of the time.")
mm = B.groupby("mname").profit.agg(["mean", "size"]).reindex(["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]).dropna()
B["cum"] = B.profit.cumsum()
rec("A17", "Time series: moneyline ROI by month " + ", ".join(f"{m} {r['mean']:+.1%} (n={int(r['size'])})" for m, r in mm.iterrows()) + f". Cumulative units low {B.cum.min():+.1f}, high {B.cum.max():+.1f}, final {B.cum.iloc[-1]:+.1f}; worst drawdown {(B.cum.cummax()-B.cum).max():.1f}u.")
rec("A18", f"Profit per bet: mean {B.profit.mean():+.3f}u, median {B.profit.median():+.2f}u (every bet is either a loss of 1 or a win of {B[B.win==1].profit.mean():.2f} on average), 10% trimmed mean {stats.trim_mean(B.profit,0.1):+.3f}. "
    f"Total goals: mean {G.tot.mean():.2f}, median {G.tot.median():.0f}, mode {G.tot.mode().iloc[0]:.0f}. With dog-heavy bets, the median bet loses: the profit comes from a few big payouts.")
rec("A19", f"Quantiles of the model's EV on bets: 25th {B.ev.quantile(.25):.1%}, median {B.ev.median():.1%}, 75th {B.ev.quantile(.75):.1%}, 95th {B.ev.quantile(.95):.1%}. Prices: median {B.price.median():+.0f}, 90th pct {B.price.quantile(.9):+.0f}.")
z_res = (G.tot - G.pred_total) / np.sqrt(G.pred_total)
sw = stats.shapiro(rng.choice(z_res.values, 2000, replace=False))
rec("A20", f"Q-Q of standardized total-goals errors ((goals - model)/sqrt(model), the Poisson scale): Shapiro-Wilk W={sw.statistic:.4f}, p={sw.pvalue:.2g}. Goals are discrete counts, so they can't be normal; use Poisson (A39) not a bell curve.", sw.pvalue)
q1, q3 = G.tot.quantile([.25, .75]); iqr = q3 - q1
rec("A21", f"Boxplot of total goals: Q1 {q1:.0f}, Q3 {q3:.0f}, IQR {iqr:.0f}, fences {q1-1.5*iqr:.1f} / {q3+1.5*iqr:.1f}; {np.mean(G.tot > q3+1.5*iqr):.1%} of games are high outliers (10+ goals type).")
rec("A22", f"SD of profit per bet {B.profit.std():.3f}u (larger than at -110 because of dog prices). SD of total goals {G.tot.std():.2f} vs sqrt(mean) {np.sqrt(G.tot.mean()):.2f} (what Poisson implies).")
zt = (G.tot - G.tot.mean()) / G.tot.std()
rec("A23", f"Empirical rule on total goals: within 1 SD {np.mean(zt.abs()<=1):.1%}, 2 SD {np.mean(zt.abs()<=2):.1%}, 3 SD {np.mean(zt.abs()<=3):.1%}. Discrete counts make the 68% figure lumpy.")
rec("A24", f"Coefficient of variation: total goals {G.tot.std()/G.tot.mean():.1%}, one team's goals {G.home_goals.std()/G.home_goals.mean():.1%} (NBA total: 8.8%). Hockey scores are ~5x noisier relative to their size.")
bm = G.assign(tres=G.tot - G.open_total).groupby("mname").tres.median()
rec("A25", "Side-by-side boxplots of (goals - opening total) by month, medians: " + ", ".join(f"{m} {bm.get(m,np.nan):+.1f}" for m in ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"] if m in bm) + ".")
ct = pd.crosstab([B.season, B.fav], B.win)
rec("A26", "Contingency table wins-losses: " + "; ".join(f"{s} {f} {int(r.get(1,0))}-{int(r.get(0,0))}" for (s, f), r in ct.iterrows()))
r1 = stats.pearsonr(G.edge, G.res); r2 = stats.pearsonr(H.edge, H.res)
rec("A27", f"Correlation of model edge (model minus no-vig opener, home side) with (home win - opener): r={r1[0]:+.3f} (p={r1[1]:.3f}, n={len(G)}).", r1[1])
oos("A27", f"2016-22 team-only model: r={r2[0]:+.3f} (p={r2[1]:.3f}, n={len(H)})")
G["edec"] = pd.qcut(G.edge, 10, labels=False); bdm = G.groupby("edec").agg(e=("edge", "mean"), y=("res", "mean"))
quad = smf.ols("res ~ edge + I(edge**2)", G).fit()
rec("A28", "Mean (home win - opener) by edge decile: " + ", ".join(f"{r.e:+.3f}->{r.y:+.3f}" for _, r in bdm.iterrows()) + f". Quadratic p={quad.pvalues['I(edge ** 2)']:.3f}.", quad.pvalues['I(edge ** 2)'])

# ===== probability
rec("A29", f"Break-even = 1/decimal odds. Our bets' average break-even {B.be.mean():.1%}, actual win rate {ph:.1%}; market's own (no-vig) chance {B.q.mean():.1%}; model's claimed chance {B.pm.mean():.1%}. "
    f"P(lose 5 straight) at a {ph:.0%} win rate = {(1-ph)**5:.1%}.")
def ll(p, y): p = np.clip(p, 1e-6, 1 - 1e-6); return -(y * np.log(p) + (1 - y) * np.log(1 - p))
F = {"model": G.p_home, "opener": G.nv_open, "close": G.nv_close, "blend55": 0.55 * G.p_home + 0.45 * G.nv_open}
hh = {}
for i in F:
    for j in F:
        if i < j: d = ll(F[i], G.hw) - ll(F[j], G.hw); hh[(i, j)] = np.mean(d[d != 0] < 0)
rec("A30", "Head-to-head, which probability had lower log loss per game (share for the first): " + ", ".join(f"{i} vs {j} {v:.1%}" for (i, j), v in hh.items()) + ". Look for cycles: none means the ranking is transitive.")
sea_fd = B.groupby(["season", "fav"]).profit.mean().unstack()
rec("A31", f"Simpson check, ROI favorites vs underdogs pooled: fav {B[B.fav=='fav'].profit.mean():+.1%}, dog {B[B.fav=='dog'].profit.mean():+.1%}; by season " + "; ".join(f"{s}: fav {r.fav:+.1%} dog {r.dog:+.1%}" for s, r in sea_fd.iterrows()) + ".")
z0 = B[B.clv.abs() <= 0.005]
rec("A32", f"Conditional probability: P(win | price moved toward us) {pos.win.mean():.1%}, P(win | no move) {z0.win.mean():.1%}, P(win | moved against) {neg.win.mean():.1%}; P(move toward us | bet) {len(pos)/n:.1%}, against {len(neg)/n:.1%}.")
pairs = []
for d, x in B.groupby("date"):
    v = x.r.values
    for i in range(len(v)):
        for j in range(i + 1, len(v)): pairs.append((v[i], v[j]))
pairs = np.array(pairs); rp_ = np.corrcoef(pairs[:, 0], pairs[:, 1])[0, 1]
seq = B.win.values; runs = 1 + np.sum(seq[1:] != seq[:-1]); n1, n0 = seq.sum(), len(seq) - seq.sum()
mu = 2 * n1 * n0 / (n1 + n0) + 1; vr = (mu - 1) * (mu - 2) / (n1 + n0 - 1); zr = (runs - mu) / np.sqrt(vr); prun = 2 * stats.norm.sf(abs(zr))
rec("A33", f"Independence: same-night bet results (vs price) r={rp_:+.3f} ({len(pairs)} pairs); runs test {runs} runs vs {mu:.0f} expected, p={prun:.3f}.", prun)
pw = (pairs[:, 0] + B.q.mean() > 0.5)
rec("A34", f"Multiplication law: two average bets (win {ph:.1%} each, average price {B.price.median():+.0f}) both win {ph**2:.1%} if independent. Same-game parlays are only fair if the legs are independent. "
    f"Check P(over | home win) {GT[GT.hw==1].tot.gt(GT[GT.hw==1].open_total).mean():.1%} vs P(over) {GT.tot.gt(GT.open_total).mean():.1%}; P(over | favorite wins) {GT[(GT.hw==GT.fav_h0)].tot.gt(GT[(GT.hw==GT.fav_h0)].open_total).mean():.1%} vs P(over | underdog wins) {GT[(GT.hw!=GT.fav_h0)].tot.gt(GT[(GT.hw!=GT.fav_h0)].open_total).mean():.1%}.")
sens = ((G.edge > 0) & (G.hw == 1)).sum() / (G.hw == 1).sum(); spec = ((G.edge < 0) & (G.hw == 0)).sum() / (G.hw == 0).sum()
rec("A35", f"Sensitivity/specificity, 'model likes home more than the market' as a test for 'home wins': sensitivity {sens:.1%}, specificity {spec:.1%}. Barely better than a coin, which is expected: the market already uses most of the information.")
mu_p, sd_p = B.profit.mean(), se_srs
rec("A36", f"Bayes: with a skeptical prior on ROI (mean 0, SD 3%, i.e. most bettors have no edge) and the data (mean {mu_p:+.2%}, SE {sd_p:.2%}), the posterior ROI is "
    f"{(mu_p/sd_p**2)/(1/0.03**2+1/sd_p**2):+.2%} (SD {np.sqrt(1/(1/0.03**2+1/sd_p**2)):.2%}); P(ROI > 0) = {stats.norm.sf(0, (mu_p/sd_p**2)/(1/0.03**2+1/sd_p**2), np.sqrt(1/(1/0.03**2+1/sd_p**2))):.3f}. "
    "The prior pulls a two-season record about halfway back to zero.")
dm = B.d.median(); EX = ph * (dm - 1) - (1 - ph); VX = ph * (dm - 1) ** 2 + (1 - ph) - EX ** 2; kel = (ph * dm - 1) / (dm - 1)
rec("A37", f"At the median price ({B.price.median():+.0f}, decimal {dm:.2f}) and {ph:.1%} win rate: E[X]={EX:+.3f}u, SD {np.sqrt(VX):.2f}u. Full Kelly {kel:.1%} of bankroll; using the market-blended probability instead "
    f"({0.55*B.pm.mean()+0.45*B.q.mean():.1%}) Kelly is {((0.55*B.pm.mean()+0.45*B.q.mean())*dm-1)/(dm-1):.1%}.")
sim = np.array([(rng.random(n) < B.q.values).sum() for _ in range(20000)]); pbin = (np.sum(sim >= w) + 1) / 20001
rec("A38", f"Wins vs the market's own chances (a 'Poisson-binomial', each bet its own p): expected {B.q.sum():.0f} wins, SD {np.sqrt((B.q*(1-B.q)).sum()):.1f}; observed {w}. P(at least {w}) = {pbin:.4f}.", pbin)
hg = pd.concat([G.home_reg, G.away_reg]); lam = hg.mean()
rec("A39", f"Poisson is the natural model for hockey goals. Regulation goals per team: mean {lam:.2f}, variance {hg.var():.2f} (dispersion {hg.var()/lam:.2f}; Poisson = 1). P(0 goals) Poisson {np.exp(-lam):.1%} vs actual {np.mean(hg==0):.1%}; "
    f"P(5+) {stats.poisson.sf(4,lam):.1%} vs {np.mean(hg>=5):.1%}. Rate scaling: {lam/60:.3f} goals per minute -> {lam/60*5:.2f} in a 5-minute OT for one team.")
hh2 = pd.concat([H.home_reg, H.away_reg]); oos("A39", f"2016-22 regulation goals mean {hh2.mean():.2f}, variance {hh2.var():.2f}, dispersion {hh2.var()/hh2.mean():.2f}")
p10 = np.mean(G.tot >= 10)
rec("A40", f"Rare events: games with 10+ goals are {p10:.2%}. In a 82-game team season, number of 10+ goal games ~ Binomial(82, {p10:.4f}) ~ Poisson({82*p10:.2f}): P(none) {stats.binom.pmf(0,82,p10):.3f} vs {stats.poisson.pmf(0,82*p10):.3f}.")
OVa = G.dropna(subset=["p_over"]); OVa = OVa[OVa.tot != OVa.open_total]; cal_o = OVa.groupby(pd.qcut(OVa.p_over / (1 - OVa.p_push), 5)).apply(lambda d: pd.Series(dict(p=(d.p_over/(1-d.p_push)).mean(), o=(d.tot > d.open_total).mean())))
rec("A41", "Probability as area: P(over) = sum of the Poisson score grid above the line (plus OT). Model P(over) vs actual by quintile: " + ", ".join(f"{r.p:.1%}/{r.o:.1%}" for _, r in cal_o.iterrows()) + ".")
zrec = (w - B.q.sum()) / np.sqrt((B.q * (1 - B.q)).sum())
rec("A42", f"z-score of the record vs market prices: z = (wins - sum q)/sqrt(sum q(1-q)) = {zrec:+.2f}.")
rec("A43", f"Quantiles: with total goals ~ Poisson(model mean ~{G.pred_total.mean():.2f}), the 95th percentile is {stats.poisson.ppf(.95, G.pred_total.mean()):.0f} goals; normal approximation gives {G.pred_total.mean()+1.645*np.sqrt(G.pred_total.mean()):.1f}. "
    f"Observed share of games at or above 10: {np.mean(G.tot>=10):.1%} (Poisson {stats.poisson.sf(9,G.pred_total.mean()):.1%}).")
sub = np.array([rng.choice(B.profit.values, 300, replace=False).mean() for _ in range(4000)])
rec("A44", f"Random 300-bet samples: ROI 95% range {np.percentile(sub,2.5):+.1%} to {np.percentile(sub,97.5):+.1%}; {np.mean(sub<0):.1%} negative (understates risk; see A45).")
rec("A45", f"SE of ROI = {B.profit.std():.3f}/sqrt({n}) = {se_srs:.2%}; one season (~{n//2} bets) SE {B.profit.std()/np.sqrt(n/2):.2%} vs ROI {B.profit.mean():+.2%}: one season is {B.profit.mean()/(B.profit.std()/np.sqrt(n/2)):.1f} SEs from zero.")
blk = B.profit.values[: (n // 50) * 50].reshape(-1, 50).sum(axis=1)
rec("A46", f"CLT: units per 50-bet block ({len(blk)} blocks) mean {blk.mean():+.2f}, SD {blk.std(ddof=1):.2f} (theory {np.sqrt(50*B.profit.var()):.2f}), skew {stats.skew(blk):+.2f}, Shapiro p={stats.shapiro(blk).pvalue:.2f}.")
qb = B.q.mean(); cc = stats.norm.sf((w - 0.5 - n * qb) / np.sqrt(n * qb * (1 - qb)))
rec("A47", f"Normal approximation with continuity correction using the average market chance {qb:.3f}: P(X >= {w}) ~ {cc:.4f} (simulation in A38: {pbin:.4f}).")

# ===== inference
ci = stats.t.interval(0.95, n - 1, B.profit.mean(), se_srs); tb = stats.ttest_1samp(G.tot - G.pred_total, 0)
rec("B48", f"Point estimates: ROI {B.profit.mean():+.4f}u/bet; win rate {ph:.4f}; model total-goals bias {np.mean(G.tot-G.pred_total):+.3f} goals/game; opener total bias {np.mean(G.tot-G.open_total):+.3f}.")
rec("B49", f"95% t CI for ROI: {ci[0]:+.2%} to {ci[1]:+.2%}. Total-goals bias {np.mean(G.tot-G.pred_total):+.3f} +/- {1.96*(G.tot-G.pred_total).std()/np.sqrt(len(G)):.3f} (t={tb.statistic:.2f}, p={tb.pvalue:.3f}).", tb.pvalue)
sdu = B.profit.std()
rec("B50", f"Bets needed for ROI +/-2% (95%): (1.96 x {sdu:.2f}/0.02)^2 = {int(np.ceil((1.96*sdu/0.02)**2)):,}; +/-5%: {int(np.ceil((1.96*sdu/0.05)**2)):,}. Dog-heavy betting is noisier than NBA -110 bets (SD {sdu:.2f} vs 0.95).")
t1 = stats.ttest_1samp(B.profit, 0, alternative="greater")
rec("B51", f"H0 ROI <= 0 vs Ha ROI > 0: t={t1.statistic:.2f}, one-sided p={t1.pvalue:.4f}. In-sample (these seasons shaped the 6% rule).", t1.pvalue)
def pw(roi, nn): return stats.norm.sf(1.645 - roi / (sdu / np.sqrt(nn)))
nn80 = next(k for k in range(50, 50000, 50) if pw(0.04, k) >= 0.8)
rec("B52", f"Power for a true +4% ROI: 300 bets {pw(.04,300):.0%}, {n} bets {pw(.04,n):.0%}; 80% power needs ~{nn80:,} bets. For +8%: {next(k for k in range(50,50000,50) if pw(0.08,k)>=0.8):,}.")
rec("B53", f"p-values here: permutation {pp:.4f}, simulation vs market {pbin:.4f}, t-test {t1.pvalue:.4f}. Each is P(this good | no edge), on seasons that helped pick the rule.")
rec("B54", f"t distribution: df={n-1}, t(0.975)={stats.t.ppf(.975,n-1):.3f}. One-sample t on (won - market price): mean {B.r.mean():+.3f}, t={stats.ttest_1samp(B.r,0).statistic:.2f}.", stats.ttest_1samp(B.r, 0).pvalue)
fv, dg = B[B.fav == "fav"].profit, B[B.fav == "dog"].profit
tp_ = stats.ttest_ind(fv, dg, equal_var=True)
rec("B55", f"Pooled t: ROI favorites {fv.mean():+.1%} (n={len(fv)}) vs underdogs {dg.mean():+.1%} (n={len(dg)}): t={tp_.statistic:+.2f}, p={tp_.pvalue:.3f}.", tp_.pvalue)
oos("B55", f"2016-22: favorites {BH[BH.fav=='fav'].profit.mean():+.1%} (n={int((BH.fav=='fav').sum())}), dogs {BH[BH.fav=='dog'].profit.mean():+.1%} (n={int((BH.fav=='dog').sum())}), p={stats.ttest_ind(BH[BH.fav=='fav'].profit, BH[BH.fav=='dog'].profit).pvalue:.3f}")
tw_ = stats.ttest_ind(fv, dg, equal_var=False); bb = B[B.b2b == 1].r; nb = B[B.b2b == 0].r; tw2 = stats.ttest_ind(bb, nb, equal_var=False)
rec("B56", f"Welch t (variances differ: dog profits swing more, SD {dg.std():.2f} vs {fv.std():.2f}): t={tw_.statistic:+.2f}, p={tw_.pvalue:.3f}. Bets on a team on a back-to-back (won - price {bb.mean():+.3f}, n={len(bb)}) vs rested ({nb.mean():+.3f}): p={tw2.pvalue:.3f}.", tw2.pvalue)
dl = ll(G.nv_open, G.hw) - ll(G.p_home, G.hw); dc = ll(G.nv_close, G.hw) - ll(G.p_home, G.hw)
tpa, tpc = stats.ttest_1samp(dl, 0), stats.ttest_1samp(dc, 0)
rec("B57", f"Paired t on per-game log loss (opener minus model; positive = model better): {dl.mean():+.4f}, t={tpa.statistic:+.2f}, p={tpa.pvalue:.3f}; close minus model {dc.mean():+.4f}, p={tpc.pvalue:.3f}.", tpa.pvalue)
dlh = ll(H.nv_open, H.hw) - ll(H.p_home, H.hw); oos("B57", f"2016-22 team-only model: opener minus model log loss {dlh.mean():+.4f}, p={stats.ttest_1samp(dlh,0).pvalue:.3f}")
ea, la = G[G.month.isin([10, 11, 12])].tot, G[G.month.isin([2, 3, 4])].tot; Fv = ea.var() / la.var()
pf = 2 * min(stats.f.sf(Fv, len(ea) - 1, len(la) - 1), stats.f.cdf(Fv, len(ea) - 1, len(la) - 1))
rec("B58", f"F test, variance of total goals Oct-Dec ({ea.var():.2f}) vs Feb-Apr ({la.var():.2f}): F={Fv:.3f}, p={pf:.3f}.", pf)
G["tres"] = G.tot - G.open_total
GT = G.dropna(subset=["tres"])
am = anova_lm(smf.ols("tres ~ C(mname)", GT).fit())
rec("B59", f"One-way ANOVA, (goals - opening total) across months: F={am.F.iloc[0]:.2f}, p={am['PR(>F)'].iloc[0]:.3f}. Means: " + ", ".join(f"{m} {v:+.2f}" for m, v in GT.groupby('mname').tres.mean().reindex(['Oct','Nov','Dec','Jan','Feb','Mar','Apr']).dropna().items())
    + f". Model bets' profit by month: p={anova_lm(smf.ols('profit ~ C(mname)', B).fit())['PR(>F)'].iloc[0]:.3f}.", am['PR(>F)'].iloc[0])
H["tres"] = H.tot - H.open_total; oos("B59", f"2016-22 month ANOVA on (goals - opener) p={anova_lm(smf.ols('tres ~ C(mname)', H).fit())['PR(>F)'].iloc[0]:.3f}; means " + ", ".join(f"{m} {v:+.2f}" for m, v in H.groupby('mname').tres.mean().reindex(['Oct','Nov','Dec','Jan','Feb','Mar','Apr']).dropna().items()))
grp = [x.tres.values for _, x in GT.groupby("mname")]; lev = stats.levene(*grp, center="median")
rec("B60", f"ANOVA assumptions: Brown-Forsythe/Levene equal-variance p={lev.pvalue:.3f}, Bartlett p={stats.bartlett(*grp).pvalue:.3f}; residuals are discrete counts but n is large, so the F test is robust.", lev.pvalue)
rec("B61", f"Transformation: for Poisson counts the square root stabilizes the variance. Var of total goals by opener: " + ", ".join(f"{k}: {v:.2f}" for k, v in G.groupby('open_total').tot.var().items()) +
    "; var of sqrt(goals): " + ", ".join(f"{k}: {v:.3f}" for k, v in np.sqrt(G.tot).groupby(G.open_total).var().items()) + ".")
mo = GT.groupby("mname").tres.agg(["mean", "count"]).reindex(["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]).dropna(); kk = len(mo)
mse_ = am.sum_sq.iloc[1] / am.df.iloc[1]
c_ = np.array([1 if m in ("Oct", "Nov", "Dec") else (-1 if m in ("Feb", "Mar", "Apr") else 0) for m in mo.index], float); c_ = c_ / np.abs(c_).sum() * 2
L_ = (c_ * mo["mean"]).sum(); seL = np.sqrt(mse_ * ((c_ ** 2) / mo["count"]).sum()); tL = L_ / seL; pL = 2 * stats.t.sf(abs(tL), am.df.iloc[1])
rec("B62", f"Planned contrast early (Oct-Dec) minus late (Feb-Apr) in (goals - opener): {L_:+.3f} goals, t={tL:+.2f}, p={pL:.3f}.", pL)
ssb = am.sum_sq.iloc[0]
c2 = np.array([1 if m == "Jan" else 0 for m in mo.index], float); c2 = c2 - c2.mean()
rec("B63", f"Orthogonal contrasts: early-vs-late SS {(c_*mo['mean']).sum()**2/((c_**2)/mo['count']).sum():.1f} of SSB {ssb:.1f}; the remaining month-to-month SS is spread across the other {kk-2} orthogonal pieces.")
tk = pairwise_tukeyhsd(GT.tres, GT.mname); tkd = pd.DataFrame(tk.summary().data[1:], columns=tk.summary().data[0])
rec("B67", f"Tukey HSD, all {len(tkd)} month pairs: {int((tkd.reject==True).sum())} significant; smallest adjusted p={tkd['p-adj'].astype(float).min():.3f}.")
lsd = []
for i_, a in enumerate(mo.index):
    for b_ in mo.index[i_ + 1:]:
        d = mo.loc[a, "mean"] - mo.loc[b_, "mean"]; se = np.sqrt(mse_ * (1 / mo.loc[a, "count"] + 1 / mo.loc[b_, "count"])); lsd.append(2 * stats.t.sf(abs(d / se), am.df.iloc[1]))
rec("B66", f"Fisher's LSD: {sum(p < 0.05 for p in lsd)} of {len(lsd)} month pairs at unadjusted 5% (only allowed if the overall F is significant; here p={am['PR(>F)'].iloc[0]:.3f}).")
Fs = (kk - 1) * stats.f.ppf(0.95, kk - 1, am.df.iloc[1]); tmax = (mo['mean'].max() - mo['mean'].min()) / np.sqrt(mse_ * (1 / mo.loc[mo['mean'].idxmax(), 'count'] + 1 / mo.loc[mo['mean'].idxmin(), 'count']))
rec("B68", f"Scheffe bar for an after-the-fact contrast: t > {np.sqrt(Fs):.2f}; best-minus-worst month t={tmax:.2f}: " + ("clears it." if tmax > np.sqrt(Fs) else "doesn't clear it."))
pr = proportion_confint(w, n, method="wilson")
rec("B69", f"One proportion: win rate {ph:.1%} (Wilson 95% CI {pr[0]:.1%}-{pr[1]:.1%}) vs the market's average chance for these bets {B.q.mean():.1%}. Games over the opening total: {np.mean(G.tot>G.open_total):.1%}, under {np.mean(G.tot<G.open_total):.1%}.",
    proportions_ztest(w, n, B.q.mean(), alternative="larger")[1])
rec("B70", f"Sample size for a win rate at +/-2% (p~0.45): {int(np.ceil(1.96**2*.45*.55/.02**2)):,} bets; +/-3%: {int(np.ceil(1.96**2*.45*.55/.03**2)):,}.")
s_ = B.groupby("season").agg(w=("win", "sum"), n=("win", "size"), q=("q", "mean"))
z2 = proportions_ztest(s_.w.values, s_.n.values)
rec("B71", f"Two proportions: win rate 2024-25 {s_.w.iloc[0]/s_.n.iloc[0]:.1%} vs 2025-26 {s_.w.iloc[1]/s_.n.iloc[1]:.1%} (market chance {s_.q.iloc[0]:.1%} / {s_.q.iloc[1]:.1%}): z={z2[0]:+.2f}, p={z2[1]:.3f}.", z2[1])
ld = B[B.price >= 200]; tbl = pd.crosstab(ld.side, ld.win)
fe = stats.fisher_exact(tbl.values) if tbl.shape == (2, 2) else (np.nan, np.nan)
rec("B72", f"Fisher's exact, long shots (+200 or longer, {len(ld)} bets) home vs away: " + "; ".join(f"{s} {int(r.get(1,0))}-{int(r.get(0,0))}" for s, r in tbl.iterrows()) + f"; p={fe[1]:.3f}. Long-shot record {ld.win.mean():.1%} vs market {ld.q.mean():.1%}, ROI {ld.profit.mean():+.1%}.", fe[1])
def gofreg(D):
    reg = (D.home_reg + D.away_reg).clip(upper=10); lamr = D.lam_home + D.lam_away
    obs = reg.value_counts().sort_index()
    exp = pd.Series({k: (stats.poisson.pmf(k, lamr).sum() if k < 10 else stats.poisson.sf(9, lamr).sum()) for k in obs.index}); exp = exp * obs.sum() / exp.sum()
    return obs, exp, stats.chisquare(obs.values, exp.values)
obs, exp, gof = gofreg(G); odd = np.mean(G.tot % 2 == 1); oddr = np.mean((G.home_reg + G.away_reg) % 2 == 1)
rec("B73", f"Chi-square goodness of fit, REGULATION total goals vs Poisson at the model's game-by-game mean: chi2={gof.statistic:.1f}, df={len(obs)-1}, p={gof.pvalue:.3g}. Observed/expected: " + ", ".join(f"{int(k)}:{int(o)}/{e:.0f}" for k, o, e in zip(obs.index, obs.values, exp.values)) + ". "
    f"FINAL totals are a different story: every regulation tie adds exactly one goal (OT or shootout winner), so finals are odd {odd:.1%} of the time vs {oddr:.1%} in regulation. A plain Poisson on final goals would misprice every total.", gof.pvalue)
oh, eh, gh = gofreg(H); oos("B73", f"2016-22 regulation totals vs Poisson chi2={gh.statistic:.1f}, p={gh.pvalue:.3g} (" + ", ".join(f"{int(k)}:{int(o)}/{e:.0f}" for k, o, e in zip(oh.index, oh.values, eh.values)) + f"); finals odd {np.mean(H.tot % 2 == 1):.1%} vs regulation {np.mean((H.home_reg + H.away_reg) % 2 == 1):.1%}")
c1 = stats.chi2_contingency(pd.crosstab(B.season, B.win)); c2_ = stats.chi2_contingency(pd.crosstab(G.month, G.ot))
rec("B74", f"Chi-square independence: season x win p={c1[1]:.3f}; month x overtime p={c2_[1]:.3f} (OT rate by month " + ", ".join(f"{m}:{v:.0%}" for m, v in G.groupby('mname').ot.mean().items()) + ").", c1[1])
o1, o2 = pos.win.mean(), neg.win.mean(); OR = (o1 / (1 - o1)) / (o2 / (1 - o2)); tb2 = pd.crosstab(B.clv > 0, B.win); se_or = np.sqrt((1 / pd.crosstab(np.r_[np.ones(len(pos)), np.zeros(len(neg))], np.r_[pos.win, neg.win]).values).sum())
rec("B75", f"Odds ratio of winning, price moved toward us vs against: {OR:.2f} (95% CI {np.exp(np.log(OR)-1.96*se_or):.2f}-{np.exp(np.log(OR)+1.96*se_or):.2f}). Note the price itself changes: what matters is won {pos.win.mean():.1%} vs market {pos.q.mean():.1%} "
    f"and {neg.win.mean():.1%} vs {neg.q.mean():.1%}.", 2 * stats.norm.sf(abs(np.log(OR) / se_or)))
posh, negh = BH[BH.clv > 0.005], BH[BH.clv < -0.005]
oos("B75", f"2016-22: moved toward us {len(posh)} bets ROI {posh.profit.mean():+.1%} (won {posh.win.mean():.1%} vs market {posh.q.mean():.1%}); against {len(negh)} bets ROI {negh.profit.mean():+.1%} ({negh.win.mean():.1%} vs {negh.q.mean():.1%}); share moving toward {len(posh)/len(BH):.0%} vs against {len(negh)/len(BH):.0%}")

# ===== regression
s1 = smf.ols("res ~ edge", G).fit(); sh_ = smf.ols("res ~ edge", H).fit()
st_ = smf.ols("tres ~ I(pred_total - open_total)", G).fit()
rec("B76", f"Least squares: (home win - no-vig opener) = {s1.params.Intercept:+.3f} + {s1.params.edge:.3f} x (model - opener) (SE {s1.bse.edge:.3f}, p={s1.pvalues.edge:.3f}). Slope 1 = the model's disagreements are fully right; "
    f"{s1.params.edge:.2f} means trust about {s1.params.edge:.0%} of them (live blend: 55%). Totals: (goals - opener) on (model - opener) slope {st_.params.iloc[1]:.2f} (SE {st_.bse.iloc[1]:.2f}, p={st_.pvalues.iloc[1]:.3f}).", s1.pvalues.edge)
oos("B76", f"2016-22 team-only model: slope {sh_.params.edge:.3f} (SE {sh_.bse.edge:.3f}, p={sh_.pvalues.edge:.3f}); totals slope {smf.ols('tres ~ I(pred_total - open_total)', H).fit().params.iloc[1]:.2f} (SE {smf.ols('tres ~ I(pred_total - open_total)', H).fit().bse.iloc[1]:.2f})")
rec("B77", f"R^2 of (home win - opener) on edge: {s1.rsquared:.4f}. Brier-style 'R^2' of probabilities: model {1-br(G,'p_home')/G.hw.var():.4f}, opener {1-br(G,'nv_open')/G.hw.var():.4f}, close {1-br(G,'nv_close')/G.hw.var():.4f}. Hockey is close to a coin flip; even the close explains ~{1-br(G,'nv_close')/G.hw.var():.0%}.")
rec("B78", f"Regression F: F(1,{int(s1.df_resid)})={s1.fvalue:.2f}, p={s1.f_pvalue:.3f}.", s1.f_pvalue)
pi = s1.get_prediction(pd.DataFrame({"edge": [0.03, 0.06, 0.15]})).summary_frame()
rec("B79", f"Prediction vs extrapolation: at edge +3 pts the expected (win - market) is {pi['mean'].iloc[0]:+.3f} (CI {pi.mean_ci_lower.iloc[0]:+.3f} to {pi.mean_ci_upper.iloc[0]:+.3f}); a single game is win or lose (prediction interval covers everything). "
    f"Edges of 15+ pts ({np.mean(G.edge.abs()>=.15):.1%} of games) are outside where the fit has data.")
cd = OLSInfluence(s1).cooks_distance[0]
rec("B80", f"Cook's distance: {np.sum(cd>4/len(G))} games above 4/n, max {cd.max():.4f}; slope without them {smf.ols('res ~ edge', G[cd<4/len(G)]).fit().params.edge:.3f} vs {s1.params.edge:.3f}.")
G["fav_h"] = (G.nv_open >= 0.5).astype(int)
mr = smf.ols("res ~ edge + b2b_diff + fav_h", G).fit()
rec("B81", "Multiple regression of (home win - opener): " + ", ".join(f"{k} {v:+.3f} (p={mr.pvalues[k]:.3f})" for k, v in mr.params.items() if k != "Intercept") + f". R^2 {mr.rsquared:.4f}.", mr.pvalues["edge"])
st = OLSInfluence(mr).resid_studentized_external
rec("B82", f"Studentized residuals: {np.mean(np.abs(st)>2):.1%} beyond |2|; max |t| {np.abs(st).max():.2f}. A binary response has bounded residuals (upsets of big favorites are the 'outliers'), so a linear model is a rough tool here; B98 is the right one.")
rec("B83", f"Residual Q-Q: bimodal (win/lose), Q-Q correlation {stats.probplot(mr.resid)[1][2]:.3f}. Normal-error inference is still fine for the slope at n={len(G)} by the CLT, but use logistic regression for probabilities.")
bp = het_breuschpagan(mr.resid, mr.model.exog); dw = durbin_watson(smf.ols("res ~ edge", G.sort_values("date")).fit().resid)
bpt = het_breuschpagan(GT.tres - GT.tres.mean(), sm.add_constant(GT[["open_total"]]))
rec("B84", f"Homoscedasticity: Breusch-Pagan p={bp[1]:.3f} (binary outcome: variance p(1-p) is highest for even games, as expected). Totals: spread of (goals - opener) vs the opener p={bpt[1]:.3f}. Durbin-Watson {dw:.3f}.", bpt[1])
G["pres"] = mr.resid + mr.params.edge * G.edge
rec("B85", "Component + residual for edge: binned " + ", ".join(f"{iv.mid:+.3f}->{v:+.3f}" for iv, v in G.groupby(pd.qcut(G.edge, 8)).pres.mean().items()) + ".")
rx = smf.ols("b2b_diff ~ edge + fav_h", G).fit().resid; ry = smf.ols("res ~ edge + fav_h", G).fit().resid; av = smf.ols("ry ~ rx", pd.DataFrame({"rx": rx, "ry": ry})).fit()
rec("B86", f"Added-variable plot for back-to-backs: slope {av.params.rx:+.3f} (p={av.pvalues.rx:.3f}) after removing edge and favorite status.", av.pvalues.rx)
spl = GT.groupby("open_total").tres.agg(["std", "size"]); spl = spl[spl["size"] > 50]
bsl = np.polyfit(np.log(spl.index.values), np.log(spl["std"].values), 1)[0] if len(spl) > 1 else np.nan
rec("B87", "Spread-level: SD of (goals - opener) by opening total " + ", ".join(f"{k}: {v:.2f} (n={int(c)})" for k, (v, c) in spl.iterrows()) + f"; log-log slope {bsl:.2f} (Poisson predicts 0.5 -> square-root transform, B61).")
Xv = G[["p_home", "nv_open", "nv_close"]].assign(c=1.0)
vif = {c: variance_inflation_factor(Xv.values, i) for i, c in enumerate(Xv.columns) if c != "c"}
rec("B88", "VIF with raw probabilities as predictors: " + ", ".join(f"{k} {v:.1f}" for k, v in vif.items()) + ". The model, opener and close all measure 'how good is the home team'; working with differences (edge, move) removes it: "
    + ", ".join(f"{c} {variance_inflation_factor(G[['edge','move']].assign(c=1.0).values, i):.1f}" for i, c in enumerate(['edge', 'move'])) + ".")
bxc = stats.boxcox(G.tot + 1)[1]
rec("B89", f"Box-Cox on (total goals + 1): lambda = {bxc:.2f} (0.5 = square root, as Poisson theory says).")
xx = G.nv_open; bt = smf.ols("hw ~ x + xl", pd.DataFrame({"hw": G.hw, "x": xx, "xl": xx * np.log(xx)})).fit()
rec("B90", f"Box-Tidwell, opener chance as a predictor of home wins: x*log(x) term p={bt.pvalues.xl:.3f} (linear in the market's chance is fine across this range).", bt.pvalues.xl)
cut = B.price.quantile(0.95); Bt_ = B[B.price < cut]
rec("B91", f"Deleting observations: dropping the 5% longest-priced bets (>= {cut:+.0f}) changes ROI {B.profit.mean():+.1%} -> {Bt_.profit.mean():+.1%}. " + ("The record leans on long shots." if Bt_.profit.mean() < B.profit.mean() - 0.02 else "The record doesn't hinge on a few long shots."))
ix = smf.ols("res ~ edge * fav_h", G).fit()
rec("B92", f"Interaction edge x home favorite: {ix.params['edge:fav_h']:+.3f} (p={ix.pvalues['edge:fav_h']:.3f}); edge slope when home is the dog {ix.params.edge:.3f}, when favorite {ix.params.edge+ix.params['edge:fav_h']:.3f}.", ix.pvalues['edge:fav_h'])
pq = smf.ols("res ~ edge + I(edge**2) + I(edge**3)", G).fit()
rec("B93", f"Polynomial: edge^2 p={pq.pvalues['I(edge ** 2)']:.3f}, edge^3 p={pq.pvalues['I(edge ** 3)']:.3f}.", pq.pvalues['I(edge ** 3)'])
n0 = smf.ols("res ~ edge", G).fit(); nt = anova_lm(n0, mr)
rec("B94", f"Nested F: adding back-to-back and favorite terms to edge: F={nt.F.iloc[1]:.2f}, p={nt['Pr(>F)'].iloc[1]:.3f}.", nt['Pr(>F)'].iloc[1])
G["lo"] = lg(G.nv_open.clip(.01, .99)); G["lm"] = lg(G.p_home.clip(.01, .99)); H["lo"] = lg(H.nv_open.clip(.01, .99)); H["lm"] = lg(H.p_home.clip(.01, .99))
mods = {"opener only": smf.logit("hw ~ lo", G).fit(disp=0), "model only": smf.logit("hw ~ lm", G).fit(disp=0), "opener + model": smf.logit("hw ~ lo + lm", G).fit(disp=0)}
mh = {"opener only": smf.logit("hw ~ lo", H).fit(disp=0), "model only": smf.logit("hw ~ lm", H).fit(disp=0), "opener + model": smf.logit("hw ~ lo + lm", H).fit(disp=0)}
rec("B95", "AIC/BIC (logistic, home win), 2024-26: " + "; ".join(f"{k} AIC {m.aic:.1f} BIC {m.bic:.1f}" for k, m in mods.items()) + ". In these two seasons the model alone beats the opener (lower AIC) and adding the opener doesn't help.")
oos("B95", "2016-22 team-only model: " + "; ".join(f"{k} AIC {m.aic:.1f}" for k, m in mh.items()) + " (opener beats the model alone; the combination is best)")
Z = G[["edge", "b2b_diff", "fav_h", "res"]].apply(lambda c: (c - c.mean()) / c.std()); zs = smf.ols("res ~ edge + b2b_diff + fav_h", Z).fit()
rec("B96", "Standardized coefficients: " + ", ".join(f"{k} {zs.params[k]:+.3f}" for k in zs.params.drop('Intercept').abs().sort_values(ascending=False).index) + ".")
rec("B97", f"Adjusted R^2: edge only {n0.rsquared_adj:.4f}; + b2b + favorite {mr.rsquared_adj:.4f}.")
lm2 = mods["opener + model"]; wgt = lm2.params.lm / (lm2.params.lm + lm2.params.lo)
lmh = smf.logit("hw ~ lo + lm", H).fit(disp=0)
rec("B98", f"Logistic regression, home win on logit(opener) and logit(model): coefficients opener {lm2.params.lo:.3f} (p={lm2.pvalues.lo:.3g}), model {lm2.params.lm:.3f} (p={lm2.pvalues.lm:.3g}). "
    f"Implied weight on the model {wgt:.0%} (live blend uses 55%).", lm2.pvalues.lm)
oos("B98", f"2016-22 team-only model: opener {lmh.params.lo:.3f}, model {lmh.params.lm:.3f} (p={lmh.pvalues.lm:.3g}); weight on model {lmh.params.lm/(lmh.params.lm+lmh.params.lo):.0%}")
# overs section (the market that held up out of sample)
for lab, O_ in (("2024-26 DK", OV), ("2016-22 SBR", OVH)):
    print(lab, len(O_), O_.win.mean(), O_.profit.sum(), O_.profit.mean(), (O_.tmove > 0).mean(), (O_.tmove < 0).mean())
mv_all = (G.close_total - G.open_total)
rec("X01", f"Overs (live v1.1 rule, EV >= 6% at the open): 2024-26 {len(OV)} bets, {OV.win.mean():.1%}, {OV.profit.sum():+.1f}u ({OV.profit.mean():+.1%}); closing total rose after {np.mean(OV.tmove>0):.1%} of bets, fell {np.mean(OV.tmove<0):.1%} "
    f"(all games: {np.mean(mv_all>0):.1%} / {np.mean(mv_all<0):.1%}).", stats.ttest_1samp(OV.profit, 0).pvalue if len(OV) > 2 else None)
oos("X01", f"2016-22 overs {len(OVH)} bets, {OVH.win.mean():.1%}, {OVH.profit.sum():+.1f}u ({OVH.profit.mean():+.1%}); total rose {np.mean(OVH.tmove>0):.1%}, fell {np.mean(OVH.tmove<0):.1%}")
oos("A33", f"2016-22 runs test p={(lambda s: 2*stats.norm.sf(abs(((1+np.sum(s[1:]!=s[:-1]))-(2*s.sum()*(len(s)-s.sum())/len(s)+1))/np.sqrt(((2*s.sum()*(len(s)-s.sum())/len(s))*((2*s.sum()*(len(s)-s.sum())/len(s))-1))/(len(s)-1)))))(BH.win.values):.3f}")
oos("ML", f"2016-22 moneyline EV>=6% at the open (trusted): {len(BH)} bets, {BH.profit.sum():+.1f}u, ROI {BH.profit.mean():+.1%}; avg price move toward us {BH.clv.mean():+.4f}")
def rested(D):
    d = D.b2b_home - D.b2b_away; X = D[d != 0].copy(); X["side"] = np.where(d[d != 0] > 0, "away", "home")
    X["win"] = np.where(X.side == "home", X.hw, 1 - X.hw); X["price"] = np.where(X.side == "home", X.open_home_ml, X.open_away_ml)
    X["q"] = np.where(X.side == "home", X.nv_open, 1 - X.nv_open); X["qc"] = np.where(X.side == "home", X.nv_close, 1 - X.nv_close)
    X["profit"] = np.where(X.win == 1, dec(X.price) - 1, -1.0); return X
XR, XRH = rested(G), rested(H)
sea = lambda X: ", ".join(f"{s}: {g.profit.mean():+.1%} (price move {(g.qc-g.q).mean():+.3f})" for s, g in X.groupby("season"))
rec("X02", f"Market-only rule, back the rested team against a team on a back-to-back at the opening price: 2024-26 {len(XR)} bets, {XR.profit.sum():+.1f}u ({XR.profit.mean():+.1%}), won {XR.win.mean():.1%} vs price {XR.q.mean():.1%}. By season {sea(XR)}.",
    stats.ttest_1samp(XR.profit, 0).pvalue)
oos("X02", f"2016-22 holdout {len(XRH)} bets, {XRH.profit.sum():+.1f}u ({XRH.profit.mean():+.1%}), won {XRH.win.mean():.1%} vs price {XRH.q.mean():.1%}; the close moved toward the rested team in {sum((g.qc-g.q).mean()>0 for _, g in XRH.groupby('season'))} of {XRH.season.nunique()} seasons. By season {sea(XRH)}")
keys = list(PV); pv = np.array([PV[k] for k in keys]); bon = multipletests(pv, 0.05, "bonferroni"); bh = multipletests(pv, 0.05, "fdr_bh")
raw = [k for k, p in zip(keys, pv) if p < 0.05]
rec("B64", f"{len(pv)} hypothesis tests. Raw p<0.05: {len(raw)} ({', '.join(raw)}); ~{0.05*len(pv):.1f} expected by chance. After Benjamini-Hochberg: {', '.join(k for k, r in zip(keys, bh[0]) if r) or 'none'}.")
rec("B65", f"Bonferroni (p < {0.05/len(pv):.4f}): {', '.join(k for k, r in zip(keys, bon[0]) if r) or 'none'}.")
json.dump({"results": R, "pvalues": PV, "n_bets": n, "wins": w}, open("results_nhl.json", "w"), indent=1); json.dump(OOS, open("oos_nhl.json", "w"), indent=1)
print("DONE", len(R))
