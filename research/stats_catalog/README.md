# Statistics concept catalog: NHL shot model

*Nov 4, 2026. Same 98 concepts, same IDs and papers as the NBA catalog (`nba-mixed-model/research/stats_catalog/`), applied to the NHL
shot model. Living document: add new concepts here and in the NBA file with the same ID.*

**Model tested:** the live shot model (expected-goals mixed model + goalie effects, one-day lag), moneyline bets at EV 6%+ against
DraftKings opening prices, 2024-25 and 2025-26: **2,425 games, 693 bets, 372-321, +79.3u (+11.4%)**. Totals: the overs-only rule.
**Out of sample:** the pre-registered holdout (team-only shot model, no goalies) on 2016-17 to 2021-22 SBR openers, trusted rows:
6,994 games, 2,853 moneyline bets (+29.9u, +1.0%), 293 overs.

Why moneyline: it's the NHL market the model bets most, and the one with a real out-of-sample record. The 2024-26 seasons were used to
choose the 6% rule, so in-sample tests are descriptive; "Confirmed out of sample" means the 2016-22 holdout shows it too.

Status key: same as the NBA catalog (Confirmed out of sample / Confirmed in-sample / Suggestive / No trend / Warning / Tool; ⇄ = carries
over to other markets).

## What came out of it

**1. Regulation ties happen far more often than the model's Poisson math says (B73, A39). New, confirmed in both eras.** Goals per team
are almost exactly Poisson (variance/mean 1.01, and 1.02 in 2016-22). But the two teams' scores aren't independent near the end of games:
regulation ties are **22.8% (2024-26) and 22.5% (2016-22) vs 16.2% / 17.0% predicted by independent Poisson**. The score matrix in
`nhl_mixed_model.score_matrix` multiplies two independent Poissons, so it under-counts ties by about 6 points every season. The calibration
layer may absorb part of this for moneylines (not checked here), but it matters most for puck lines (every tie is a puck-line loss for the favorite at -1.5)
and totals (every tie adds a goal, which is why finals are odd 68% of the time). **Next test:** a tie-inflated score matrix (the Dixon-Coles
idea: inflate the diagonal), checked on 2016-22 puck lines and totals before anything changes live.

**2. The opener under-prices back-to-backs (A03). Confirmed out of sample.** Per back-to-back, the home team wins 6.4 pts less than the
opening price says in 2024-26 and 3.6 pts less in 2016-22 (p = 0.005). The model already has it (residual vs model n.s. in both eras).
A market-only check (X02): backing the rested team against a back-to-back team at the opener made +2.2% on 1,520 holdout bets in 2016-22
(positive in 4 of 6 seasons) and +7.8% on 538 in 2024-26, and **the price moved toward the rested team by the close in every season** (6 of 6 holdout, 2 of 2 recent). It's thin, but it's the cleanest
market-wide lead in either catalog. Worth a pre-registered test as a filter or a standalone rule.

**3. Line movement marks winners in hockey too (B75, A02, A32).** 2024-26: bets whose price moved our way won 55.4% vs a 47.0% market price
(+14.9% ROI); moved against, 43.8% vs 46.1% (-11.3%). 2016-22: the same split (+4.9% vs -8.8%), and the no-vig price moved toward the
team-only model's picks 55% of the time vs 29% against. **Correction to the Nov 3 read:** its negative CLV (-1.7%) measured value
including the vig; the price *did* move toward the picks more often than not, just not by enough to cover the vig.

**4. How much to trust the model depends on the goalie information (B76, B98, B95).** Fitting home win on the opener and the model:
2024-26 (live model, with goalies) gives the model **82%** of the weight; 2016-22 (team-only, no goalies) gives it **28%**. The live blend
uses 55%, in between. Two seasons are too few to raise it, but this is the measurement to repeat each season.

**5. The edge isn't luck (A07, A38) but it's not proven either (A36, B52).** Coin-flip sides at the same prices: -2.6% ROI; the model beat
all but 1 in 5,000. With a skeptical prior (most bettors have no edge), the two-season +11.4% shrinks to about +4% (P(ROI > 0) = 0.95).
80% power to detect a true +4% ROI takes ~4,600 bets (dog prices are noisy, SD 1.09u per bet).

**6. Overs: the totals lead holds (X01).** 2024-26: +3.1% on 198 bets, and the total rose after 36% of bets vs fell 8% (all games: 17% /
16%). 2016-22: +18.4% on 293, rose 33% vs fell 3%.

**7. What didn't hold up:**
- Underdogs made most of the 2024-26 profit (+16.8% vs +3.7% for favorites), but in 2016-22 dogs made +0.6% vs +2.5%. Don't tilt toward dogs.
- Bigger EV didn't win more in 2016-22 (12%+ EV: about -1%), same as the NBA. Bet flat.
- The month pattern in totals (p = 0.04 in-sample) is gone in 2016-22 (p = 0.29).
- The team-only model is *less* accurate than the opener in 2016-22 (log loss p = 0.015); the live model is roughly tied with the opener
  (p = 0.17) and worse than the close (p = 0.049). As in the NBA, the profit is in timing at the open, not a better number.

**8. NBA findings that do NOT carry over:** noise growing with the line (B84/B87): NHL totals sit at 5.5-6.5 and the spread of misses is
flat (2.30 / 2.36 / 2.32). Right-skew in the NBA came from overtime; in the NHL, OT shows up as the odd-total effect instead.

**9. Multiple testing (B64, B65):** 41 tests, 17 with p < 0.05, 10 pass Bonferroni. Several test the same win rate (A38, B51, B54, B69).

### Out-of-sample checks (2016-17 to 2021-22 holdout)
| Concept | 2016-22 result |
|---|---|
| A03 | 2016-22: vs the market -0.036 per b2b (p=0.005); vs the team-only model -0.016 (p=0.218); b2b games 1520 |
| A04 | 2016-22: top-20% teams +0.106 -> +0.007, r=+0.06 (p=0.40, 186 team-seasons) |
| A08 | 2016-22 ROI by EV bucket: 6-9% +2.5%, 9-12% +4.3%, 12-20% -1.4%, 20%+ -0.7% |
| A27 | 2016-22 team-only model: r=+0.030 (p=0.011, n=6994) |
| A39 | 2016-22 regulation goals mean 2.87, variance 2.92, dispersion 1.02 |
| B55 | 2016-22: favorites +2.5% (n=697), dogs +0.6% (n=2156), p=0.699 |
| B57 | 2016-22 team-only model: opener minus model log loss -0.0034, p=0.015 |
| B59 | 2016-22 month ANOVA on (goals - opener) p=0.292; means Oct +0.28, Nov +0.10, Dec +0.26, Jan +0.25, Feb +0.14, Mar +0.13, Apr +0.34 |
| B73 | 2016-22 regulation totals vs Poisson chi2=80.9, p=3.35e-13 (0:33/27, 1:96/146, 2:414/404, 3:605/748, 4:1118/1042, 5:1067/1168, 6:1229/1095, 7:910/884, 8:672/628, 9:399/398, 10:445/448); finals odd 68.9% vs regulation 46.2% |
| B75 | 2016-22: moved toward us 1582 bets ROI +4.9% (won 49.2% vs market 45.1%); against 827 bets ROI -8.8% (39.5% vs 41.7%); share moving toward 55% vs against 29% |
| B76 | 2016-22 team-only model: slope 0.258 (SE 0.101, p=0.011); totals slope 0.69 (SE 0.08) |
| B95 | 2016-22 team-only model: opener only AIC 9303.5; model only AIC 9356.6; opener + model AIC 9295.3 (opener beats the model alone; the combination is best) |
| B98 | 2016-22 team-only model: opener 0.865, model 0.339 (p=0.00142); weight on model 28% |
| X01 | 2016-22 overs 293 bets, 62.1%, +53.9u (+18.4%); total rose 32.8%, fell 3.1% |
| A33 | 2016-22 runs test p=0.097 |
| ML | 2016-22 moneyline EV>=6% at the open (trusted): 2853 bets, +29.9u, ROI +1.0%; avg price move toward us +0.0097 |
| X02 | 2016-22 holdout 1520 bets, +33.6u (+2.2%), won 57.7% vs price 54.2%; the close moved toward the rested team in 6 of 6 seasons. By season 2017: -6.1% (price move +0.010), 2018: +2.6% (price move +0.009), 2019: +1.7% (price move +0.010), 2020: -4.1% (price move +0.010), 2021: +22.9% (price move +0.016), 2022: +11.0% (price move +0.017) |

## How to read each entry
**Formula**, **Paper** (same as the NBA catalog; see its file for the NBA-specific lesson), **Applied to the NHL model**, and the 2016-22 check where one was run.
Scripts: `research/stats_catalog/build_nhl.py` (per-game data), `run_nhl.py` (all tests), `make_catalog_nhl.py` (this file).


## Study design and data collection

### A01. Population vs sample  ·  *Tool*
- **Formula / idea:** Population = all units of interest; sample = the subset observed. Statistic (e.g. x̄) estimates a parameter (μ).
- **Paper:** Gandar, J., Zuber, R., O'Brien, T., & Russo, B. (1988). Testing rationality in the point spread betting market. *The Journal of Finance, 43*(4), 995-1008. https://doi.org/10.2307/2328148
  - *How they used it:* They treated a sample of NFL seasons as evidence about the whole market of games. Standard regression tests on that sample did not reject that closing spreads are unbiased, but economic tests of betting rules found apparent inefficiencies.
- **Applied to the NHL model:** Population = every NHL game the market prices; sample = 9,419 games 2016-17..2021-22 (SBR) + 2024-26 (DraftKings). Home teams won 54.5% vs a no-vig opener price of 54.3%: bias +0.002 (t=0.32, p=0.75). By season -0.020 to +0.022. Favorites vs their price: +0.006. The no-vig opener is close to unbiased; there's no free home or favorite lean.

### A02. Observational study vs experiment; correlation is not causation  ·  *Confirmed out of sample*
- **Formula / idea:** Observational: we watch X and Y. Experiment: we assign X at random. Only randomization licenses 'X causes Y'.
- **Paper:** Levitt, S. D. (2004). Why are gambling markets organised so differently from financial markets? *The Economic Journal, 114*(495), 223-246. https://doi.org/10.1111/j.1468-0297.2004.00207.x
  - *How they used it:* He studied 19,770 observational bets by 285 bettors in an online-sportsbook NFL handicapping contest (2001-02), plus 21 seasons of results against the spread. Favourites drew about 61% of bets but covered less than half the time, and from this he inferred (rather than tested experimentally) that bookmakers shade lines to exploit bettor bias.
- **Applied to the NHL model:** Observational: bets where the price later moved toward us (no-vig chance up 0.5+ pts) won 55.4% at an average market price of 47.0% (n=507); moved against 43.8% vs 46.1% (n=121). ROI +14.9% vs -11.3%. The move doesn't cause the win; both come from news (goalies, lineups).

### A03. Confounding variables  ·  *Confirmed out of sample*  ⇄
- **Formula / idea:** A confounder Z is associated with both X and Y; the X–Y link can be partly or fully Z.
- **Paper:** Price, J., & Wolfers, J. (2010). Racial discrimination among NBA referees. *The Quarterly Journal of Economics, 125*(4), 1859-1887. https://doi.org/10.1162/qjec.2010.125.4.1859
  - *How they used it:* They used NBA box scores (1991-2004) to show that players get more fouls when the referee crew is of the opposite race. They controlled for player, referee and game characteristics so that playing style and matchup would not confound the race effect.
- **Applied to the NHL model:** Back-to-backs (home minus away b2b): raw home win rate -0.080 per b2b (p=0.000); vs the market -0.064 (p=0.003); vs the model -0.033 (p=0.122). The raw effect is partly confounded with goalie choice (backups start b2bs), but the opener does NOT fully price it here; the shot model (which knows the likely goalie and b2b) mostly does.
- **2016-22 check:** 2016-22: vs the market -0.036 per b2b (p=0.005); vs the team-only model -0.016 (p=0.218); b2b games 1520
- **Carries over:** A known, scheduled handicap (fatigue) that the opening price under-weights and the closing price fixes: same pattern as slow-to-price scheduled events in markets.

### A04. Survivorship bias  ·  *Confirmed out of sample*  ⇄
- **Formula / idea:** Survivorship bias: analyzing only units that passed a filter (planes that returned, funds that survived).
- **Paper:** Brown, S. J., Goetzmann, W., Ibbotson, R. G., & Ross, S. A. (1992). Survivorship bias in performance studies. *The Review of Financial Studies, 5*(4), 553-580. https://ideas.repec.org/a/oup/rfinst/v5y1992i4p553-80.html (DOI not confirmed)
  - *How they used it:* Using numerical examples of mutual-fund returns, they showed that dropping funds that died makes past performance look like it predicts future performance even when it does not.
- **Applied to the NHL model:** Selection on past success: teams in the top 20% for beating the moneyline in their first 41 games (+0.110 wins/game above price) were +0.020 the rest of the way; first-half vs second-half r=+0.25 (p=0.05, 64 team-seasons). 'Teams that beat the books' mostly stop.
- **2016-22 check:** 2016-22: top-20% teams +0.106 -> +0.007, r=+0.06 (p=0.40, 186 team-seasons)
- **Carries over:** Hot streaks regress (same as NBA, and fund-manager persistence).

### A05. Sampling designs / clustered standard errors  ·  *No trend*
- **Formula / idea:** SRS: SE = s/√n. Cluster sampling: units within a cluster are correlated, inflating SE. Stratified: sample within strata.
- **Paper:** Moulton, B. R. (1990). An illustration of a pitfall in estimating the effects of aggregate variables on micro units. *The Review of Economics and Statistics, 72*(2), 334-338. https://doi.org/10.2307/2109724
  - *How they used it:* In a regression of individual workers' wages on state-level variables, OLS that ignored within-state error correlation understated standard errors badly.
- **Applied to the NHL model:** ROI +11.44%. SE as a simple random sample 4.13%; cluster bootstrap by game night 4.13% (ratio 1.00). Same-night bets behave as independent.

### A06. Selection / nonresponse bias  ·  *Tool*
- **Formula / idea:** Selection / nonresponse bias: the units you observe differ systematically from those you don't (1936 Literary Digest).
- **Paper:** Squire, P. (1988). Why the 1936 Literary Digest poll failed. *Public Opinion Quarterly, 52*(1), 125-133. https://doi.org/10.1086/269085
  - *How they used it:* Using a 1937 Gallup survey that asked people whether they had received and returned the Digest ballot, he showed that the sampling frame was biased but that nonresponse bias (Landon supporters were more likely to reply) was the main cause of the error.
- **Applied to the NHL model:** Who's in the test set: 640 games among a home team's first 10 home games vs 1785 later. Brier early: model 0.2406, opener 0.2420; later: model 0.2387, opener 0.2400. ROI of model bets in those early games +14.7% (n=244) vs later +9.7%. Like the Literary Digest poll, a result on 'all games' can hide a subgroup the model handles differently.

### A07. Randomization / permutation test  ·  *Confirmed (in-sample)*  ⇄
- **Formula / idea:** Randomization: assign treatments by chance; the randomization (permutation) distribution gives an exact p-value.
- **Paper:** Ritzwoller, D. M., & Romano, J. P. (2022). Uncertainty in the hot hand fallacy: Detecting streaky alternatives to random Bernoulli sequences. *The Review of Economic Studies, 89*(2), 976-1007. https://doi.org/10.1093/restud/rdab020
  - *How they used it:* They built permutation tests that compare make rates after streaks with rates under reshuffled shot sequences, then applied them to four controlled basketball shooting experiments. Much larger datasets were needed to detect streakiness, and only one shooter's sequence significantly departed from randomness.
- **Applied to the NHL model:** Randomization test: same 693 games, side picked by coin flip at the real opening prices, 5,000 times: mean ROI -2.57%, 99th pct +6.20%; model +11.44%. p=0.0002.
- **Carries over:** Permutation test of a signal vs random sides.

### A08. Completely randomized vs randomized block design  ·  *Warning*
- **Formula / idea:** CRD: y_ij = μ + τ_i + ε_ij. RBD: y_ij = μ + τ_i + β_j + ε_ij (block β removes nuisance variation).
- **Paper:** Gadeken, D. L., & Casper, D. P. (2017). Evaluation of a high forage total mixed ration on the lactational performance of late lactation dairy cows. *Translational Animal Science, 1*(1), 108-115. https://doi.org/10.2527/tas2016.0011
  - *How they used it:* They blocked 20 Holstein cows by parity, milk yield and days in milk, then randomized two rations within blocks. The 80%-forage ration cut milk yield (24.1 vs 28.1 kg/d) and dry matter intake.
- **Applied to the NHL model:** Edge (EV) bucket as treatment, profit as response. No blocks: F=1.46, p=0.225; blocked by season: p=0.226. ROI by bucket: 6-9% +14.1% (n=261), 9-12% -2.4% (n=148), 12-20% +11.7% (n=203), 20%+ +27.7% (n=81).
- **2016-22 check:** 2016-22 ROI by EV bucket: 6-9% +2.5%, 9-12% +4.3%, 12-20% -1.4%, 20%+ -0.7%

### A09. Latin square design  ·  *No trend*
- **Formula / idea:** Latin square: two blocking factors (rows, columns), each treatment once per row and column.
- **Paper:** Zanton, G. I. (2019). Effect of experimental design on responses to 2 concentrations of metabolizable protein in multiparous dairy cows. *Journal of Dairy Science, 102*(6), 5094-5108. https://doi.org/10.3168/jds.2018-15730
  - *How they used it:* The same two protein diets were tested on 54 cows with either a Latin square (16 cows, switched across periods) or a continuous randomized complete block design (38 cows). Most production results agreed between designs, but the Latin square showed carryover effects on milk fat.
- **Applied to the NHL model:** Two blocking factors (season, weekday), Latin-square idea: favorite vs underdog bets after both blocks p=0.365; weekday p=0.403.

### A10. Factorial design and interaction  ·  *Warning*
- **Formula / idea:** Factorial: all combinations of factor levels; interaction = effect of A depends on level of B.
- **Paper:** ISIS-2 (Second International Study of Infarct Survival) Collaborative Group. (1988). Randomised trial of intravenous streptokinase, oral aspirin, both, or neither among 17,187 cases of suspected acute myocardial infarction: ISIS-2. *The Lancet, 332*(8607), 349-360. https://doi.org/10.1016/S0140-6736(88)92833-4
  - *How they used it:* A 2x2 factorial trial randomized 17,187 patients to streptokinase or placebo and to aspirin or placebo, estimating both drugs and their combination in one trial. Each drug cut vascular mortality, and the combination did better than either alone.
- **Applied to the NHL model:** 2x2 factorial, favorite/underdog x home/away (response: won minus market price): ROI dog away +24.6% (n=226); dog home +7.1% (n=182); fav away +3.3% (n=67); fav home +3.8% (n=218). Interaction p=0.355.

### A11. ANCOVA / covariates  ·  *No trend*
- **Formula / idea:** ANCOVA: y = μ + τ_i + β(x − x̄) + ε; compares groups after adjusting for a covariate x.
- **Paper:** Vickers, A. J., & Altman, D. G. (2001). Analysing controlled trials with baseline and follow up measurements. *BMJ, 323*(7321), 1123. https://doi.org/10.1136/bmj.323.7321.1123
  - *How they used it:* Using a 52-patient trial of acupuncture for shoulder pain, they showed that ANCOVA (follow-up score adjusted for baseline) handles baseline imbalance and has more power than analysing change scores or follow-up scores alone.
- **Applied to the NHL model:** ANCOVA: favorite-vs-underdog gap in (won - market price) unadjusted -0.033 (p=0.391); adjusted for the price itself -0.020 (p=0.763).

### A12. Experimental unit vs measurement unit / pseudoreplication  ·  *Confirmed out of sample*
- **Formula / idea:** Experimental unit = what gets the treatment; measurement unit = what is measured. Treating sub-measurements as independent = pseudoreplication.
- **Paper:** Hurlbert, S. H. (1984). Pseudoreplication and the design of ecological field experiments. *Ecological Monographs, 54*(2), 187-211. https://doi.org/10.2307/1942661
  - *How they used it:* He reviewed 176 published ecological experiments and found that many (about half of those that used inferential statistics) treated repeated measurements on the same unit as independent replicates.
- **Applied to the NHL model:** Experimental unit = game; the two team scores are measurements within it. Regulation goals above expectation correlate r=-0.06 between the two teams (slightly negative: score effects and empty nets, a team that falls behind pulls its goalie and gives up more). Counting team-games as independent would double n falsely.


## Describing data

### A13. Bar charts / categorical summaries  ·  *Tool*
- **Formula / idea:** Bar chart: counts or percentages per category.
- **Paper:** Cleveland, W. S., & McGill, R. (1984). Graphical perception: Theory, experimentation, and application to the development of graphical methods. *Journal of the American Statistical Association, 79*(387), 531-554. https://www.jstor.org/stable/2288400
  - *How they used it:* In perception experiments, they ranked how accurately people decode graphs. Position along a common scale (as in bar and dot charts) was judged best, ahead of angle, area and shading.
- **Applied to the NHL model:** Bar chart: 77.8% of games end in regulation, 22.2% go to OT/shootout. Moneyline bets: 372 wins, 321 losses (no pushes on a moneyline).

### A14. Pie charts  ·  *Warning*
- **Formula / idea:** Pie chart: category shares of a whole (sum to 100%).
- **Paper:** Spence, I., & Lewandowsky, S. (1991). Displaying proportions and percentages. *Applied Cognitive Psychology, 5*(1), 61-77. https://doi.org/10.1002/acp.2350050106
  - *How they used it:* In experiments where people judged proportions from pie charts, bar charts and tables, pies did about as well as bars for part-to-whole judgments, contrary to common advice.
- **Applied to the NHL model:** Pie shares of bets: dog away 33%, dog home 26%, fav away 10%, fav home 31%. Underdogs are 59% of bets: the model's value mostly lives on dogs.

### A15. Histogram & distribution shape (skewness, kurtosis)  ·  *Tool*
- **Formula / idea:** Histogram; shape: modality, skewness, tails.
- **Paper:** Mandelbrot, B. (1963). The variation of certain speculative prices. *The Journal of Business, 36*(4), 394-419. https://doi.org/10.1086/294632
  - *How they used it:* Using histograms of cotton price changes, he showed that they are far more peaked and fat-tailed than a normal distribution, and proposed stable Paretian laws instead.
- **Applied to the NHL model:** Histogram of total goals: mean 6.18, median 6, skew +0.39, excess kurtosis +0.03. Right-skewed count data with a floor at 0.

### A16. Relative frequency histogram / density  ·  *Tool*
- **Formula / idea:** Relative frequency = count / n; relative frequency histogram approximates the density.
- **Paper:** Freedman, D., & Diaconis, P. (1981). On the histogram as a density estimator: L2 theory. *Zeitschrift für Wahrscheinlichkeitstheorie und Verwandte Gebiete, 57*(4), 453-476. https://doi.org/10.1007/BF01025868
  - *How they used it:* They derived the bin width that minimizes integrated squared error when a histogram estimates a density. This gives the rule of a bin width of about 2·IQR·n^(-1/3).
- **Applied to the NHL model:** Relative frequency of total goals: 1: 1.2%, 2: 1.4%, 3: 10.6%, 4: 8.7%, 5: 22.7%, 6: 10.8%, 7: 19.5%, 8: 7.5%, 9: 10.0%, 10: 2.9%, 11: 3.1%. At 5.5/6/6.5 lines one goal moves a total bet from loss to win; a 6 total pushes 10.8% of the time.

### A17. Time-series plot / trends  ·  *Suggestive*
- **Formula / idea:** Time-series plot: value vs time to show trend, seasonality, drift.
- **Paper:** Berry, S. M., Reese, C. S., & Larkey, P. D. (1999). Bridging different eras in sports. *Journal of the American Statistical Association, 94*(447), 661-676. https://www.vanderbilt.edu/psychological_sciences/graduate/programs/quantitative-methods/quantitative-content/berry_reese_larkey_1999.pdf (author-hosted copy; DOI not confirmed)
  - *How they used it:* They modelled hockey, golf and baseball careers (for example NHL forwards 1948-1996) and plotted estimated year effects over time. NHL scoring rose after 1969, peaked in the 1970s and early 1980s, and declined from 1983.
- **Applied to the NHL model:** Time series: moneyline ROI by month Oct +20.1% (n=117), Nov +9.2% (n=149), Dec +13.5% (n=130), Jan +10.8% (n=99), Feb +15.4% (n=39), Mar -5.8% (n=102), Apr +24.1% (n=57). Cumulative units low -2.4, high +82.3, final +79.3; worst drawdown 9.3u.

### A18. Mean, median, mode, trimmed mean  ·  *Tool*
- **Formula / idea:** Mean x̄ = Σx/n; median = middle value; mode = most common; trimmed mean drops top/bottom k%.
- **Paper:** Stigler, S. M. (1977). Do robust estimators work with real data? *The Annals of Statistics, 5*(6), 1055-1098. https://doi.org/10.1214/aos/1176343997
  - *How they used it:* He compared 11 location estimators on historical scientific data sets (solar parallax, mean density of the earth, speed of light) with known true values. Light trimming beat the mean slightly, but the plain mean held up well against newer estimators.
- **Applied to the NHL model:** Profit per bet: mean +0.114u, median +0.54u (every bet is either a loss of 1 or a win of 1.08 on average), 10% trimmed mean +0.042. Total goals: mean 6.18, median 6, mode 5. With dog-heavy bets, the median bet loses: the profit comes from a few big payouts.

### A19. Percentiles / quantiles  ·  *Tool*
- **Formula / idea:** pth percentile: p% of data at or below it; quartiles Q1, Q2, Q3.
- **Paper:** Koenker, R., & Bassett, G., Jr. (1978). Regression quantiles. *Econometrica, 46*(1), 33-50. https://www.jstor.org/stable/1913643
  - *How they used it:* They extended sample quantiles to linear models (regression quantiles). The resulting estimators are nearly as efficient as least squares under normal errors and much better under heavy-tailed errors.
- **Applied to the NHL model:** Quantiles of the model's EV on bets: 25th 7.8%, median 10.3%, 75th 15.2%, 95th 24.3%. Prices: median +105, 90th pct +175.

### A20. Q-Q plot / normality (Shapiro-Wilk)  ·  *Tool*
- **Formula / idea:** Q-Q plot: sample quantiles vs normal quantiles; straight line = normal. Shapiro-Wilk W tests it.
- **Paper:** Shapiro, S. S., & Wilk, M. B. (1965). An analysis of variance test for normality (complete samples). *Biometrika, 52*(3-4), 591-611. https://doi.org/10.1093/biomet/52.3-4.591
  - *How they used it:* They introduced the W statistic, which measures how closely ordered sample values line up with expected normal order statistics (the Q-Q plot idea). In comparisons with other normality tests it had good power.
- **Applied to the NHL model:** Q-Q of standardized total-goals errors ((goals - model)/sqrt(model), the Poisson scale): Shapiro-Wilk W=0.9880, p=7.1e-12. Goals are discrete counts, so they can't be normal; use Poisson (A39) not a bell curve.

### A21. IQR, boxplot, outlier fences  ·  *Tool*
- **Formula / idea:** IQR = Q3 − Q1; inner fences Q1 − 1.5·IQR, Q3 + 1.5·IQR; points outside = potential outliers.
- **Paper:** Hoaglin, D. C., Iglewicz, B., & Tukey, J. W. (1986). Performance of some resistant rules for outlier labeling. *Journal of the American Statistical Association, 81*(396), 991-999. https://doi.org/10.2307/2289073
  - *How they used it:* They worked out how often the boxplot fence rule (quartiles ± k·IQR) labels points "outside" in clean normal samples of different sizes, so analysts know the false-alarm rate.
- **Applied to the NHL model:** Boxplot of total goals: Q1 5, Q3 7, IQR 2, fences 2.0 / 10.0; 4.6% of games are high outliers (10+ goals type).

### A22. Variance and standard deviation  ·  *Tool*
- **Formula / idea:** s² = Σ(x − x̄)²/(n − 1); s = √s².
- **Paper:** Markowitz, H. (1952). Portfolio selection. *The Journal of Finance, 7*(1), 77-91. https://doi.org/10.1111/j.1540-6261.1952.tb01525.x
  - *How they used it:* He defined investment risk as the variance of portfolio return and showed how covariances between assets set the trade-off between expected return and variance.
- **Applied to the NHL model:** SD of profit per bet 1.086u (larger than at -110 because of dog prices). SD of total goals 2.31 vs sqrt(mean) 2.49 (what Poisson implies).

### A23. Empirical rule (68-95-99.7)  ·  *Tool*
- **Formula / idea:** Mound-shaped data: ~68% within x̄ ± s, ~95% within ± 2s, ~99.7% within ± 3s.
- **Paper:** Pukelsheim, F. (1994). The three sigma rule. *The American Statistician, 48*(2), 88-91. https://doi.org/10.2307/2684253
  - *How they used it:* Using the Vysochanskii-Petunin inequality, he proved that any unimodal distribution keeps at least about 95% of its mass within 3 standard deviations, so the 3-sigma rule holds well beyond the normal case.
- **Applied to the NHL model:** Empirical rule on total goals: within 1 SD 69.2%, 2 SD 94.2%, 3 SD 99.8%. Discrete counts make the 68% figure lumpy.

### A24. Coefficient of variation  ·  *Tool*
- **Formula / idea:** CV = s / x̄ (relative variability).
- **Paper:** Hopkins, W. G., Hawley, J. A., & Burke, L. M. (1999). Design and analysis of research on sport performance enhancement. *Medicine & Science in Sports & Exercise, 31*(3), 472-485. https://doi.org/10.1097/00005768-199903000-00018
  - *How they used it:* They expressed an elite athlete's competition-to-competition variability as a within-athlete coefficient of variation. They set the smallest worthwhile performance gain as a fraction (about 0.4-0.7) of that variation and derived the sample sizes needed to detect it.
- **Applied to the NHL model:** Coefficient of variation: total goals 37.4%, one team's goals 55.0% (NBA total: 8.8%). Hockey scores are ~5x noisier relative to their size.

### A25. Side-by-side boxplots comparing groups  ·  *Suggestive (does not replicate)*
- **Formula / idea:** Side-by-side boxplots compare center and spread across groups.
- **Paper:** McGill, R., Tukey, J. W., & Larsen, W. A. (1978). Variations of box plots. *The American Statistician, 32*(1), 12-16. https://doi.org/10.2307/2683468
  - *How they used it:* They introduced variable-width box plots (width showing group size) and notched box plots (notches giving a rough test of whether two medians differ) for comparing several groups side by side.
- **Applied to the NHL model:** Side-by-side boxplots of (goals - opening total) by month, medians: Oct +0.5, Nov -0.5, Dec -0.5, Jan -0.5, Feb +0.5, Mar -0.5, Apr +0.5.

### A26. Contingency tables / stacked bar  ·  *Tool*
- **Formula / idea:** Contingency table: counts for two categorical variables; stacked/grouped bar charts.
- **Paper:** Nevill, A. M., Balmer, N. J., & Williams, A. M. (2002). The influence of crowd noise and experience upon refereeing decisions in football. *Psychology of Sport and Exercise, 3*(4), 261-272. https://wlv.openrepository.com/items/2a37e72f-d492-4e51-aaec-76f45dcba34f (DOI not confirmed)
  - *How they used it:* Qualified referees judged videotaped soccer challenges with or without crowd noise, and the authors cross-tabulated decisions by condition (then used logistic regression). Referees hearing crowd noise called about 15.5% fewer fouls against the home team.
- **Applied to the NHL model:** Contingency table wins-losses: 2025 dog 110-122; 2025 fav 81-49; 2026 dog 89-87; 2026 fav 92-63

### A27. Scatterplot & Pearson correlation  ·  *Confirmed out of sample*
- **Formula / idea:** r = Σ(x − x̄)(y − ȳ) / √[Σ(x − x̄)² Σ(y − ȳ)²], −1 ≤ r ≤ 1.
- **Paper:** Hall, S., Szymanski, S., & Zimbalist, A. (2002). Testing causality between team performance and payroll: The cases of Major League Baseball and English soccer. *Journal of Sports Economics, 3*(2), 149-168. https://doi.org/10.1177/152700250200300204
  - *How they used it:* Using MLB payrolls (1980-2000) and English soccer wage data, they found that the payroll-win correlation in MLB rose in the 1990s, yet Granger tests showed no causality from payroll to performance in MLB (unlike soccer).
- **Applied to the NHL model:** Correlation of model edge (model minus no-vig opener, home side) with (home win - opener): r=+0.080 (p=0.000, n=2425).
- **2016-22 check:** 2016-22 team-only model: r=+0.030 (p=0.011, n=6994)

### A28. Zero/low correlation does not mean no relationship (Anscombe)  ·  *No trend*
- **Formula / idea:** r measures only LINEAR association; r ≈ 0 can hide a strong curved pattern.
- **Paper:** Anscombe, F. J. (1973). Graphs in statistical analysis. *The American Statistician, 27*(1), 17-21. https://doi.org/10.1080/00031305.1973.10478966
  - *How they used it:* He built four data sets with identical means, variances, correlations and regression lines whose scatterplots look completely different (linear, curved, outlier-driven).
- **Applied to the NHL model:** Mean (home win - opener) by edge decile: -0.078->-0.087, -0.041->-0.084, -0.022->+0.065, -0.008->-0.028, +0.005->+0.036, +0.016->+0.037, +0.028->-0.046, +0.042->+0.030, +0.061->+0.030, +0.102->+0.070. Quadratic p=0.909.


## Probability and sampling distributions

### A29. Probability rules, complement, break-even probability  ·  *Tool*
- **Formula / idea:** 0 ≤ P(E) ≤ 1; P(Eᶜ) = 1 − P(E); P(A ∪ B) = P(A) + P(B) − P(A ∩ B).
- **Paper:** Vergin, R. C., & Scriabin, M. (1978). Winning strategies for wagering on National Football League games. *Management Science, 24*(8), 809-818. https://doi.org/10.1287/mnsc.24.8.809
  - *How they used it:* Using NFL point spreads from 1969-1974, they tested betting rules for biases and found some that won often enough to exceed the break-even rate required after the bookmaker's fee.
- **Applied to the NHL model:** Break-even = 1/decimal odds. Our bets' average break-even 48.8%, actual win rate 53.7%; market's own (no-vig) chance 46.8%; model's claimed chance 54.8%. P(lose 5 straight) at a 54% win rate = 2.1%.

### A30. Intransitive (nontransitive) dice / rankings  ·  *Tool*
- **Formula / idea:** Nontransitive dice: A beats B, B beats C, C beats A (pairwise 'better' need not be transitive).
- **Paper:** Savage, R. P., Jr. (1994). The paradox of nontransitive dice. *The American Mathematical Monthly, 101*(5), 429-436. DOI not confirmed (citation confirmed via reference list at https://www.math.uci.edu/~mfinkels/dice9.pdf)
  - *How they used it:* He analysed sets of dice where A beats B, B beats C and C beats A, each with probability above 1/2, and explained when such cycles arise.
- **Applied to the NHL model:** Head-to-head, which probability had lower log loss per game (share for the first): model vs opener 53.2%, close vs model 50.8%, close vs opener 55.2%, blend55 vs model 46.8%, blend55 vs opener 53.2%, blend55 vs close 47.5%. Look for cycles: none means the ranking is transitive.

### A31. Simpson's paradox  ·  *Warning*
- **Formula / idea:** Simpson's paradox: a relationship within every group reverses when groups are pooled.
- **Paper:** Bickel, P. J., Hammel, E. A., & O'Connell, J. W. (1975). Sex bias in graduate admissions: Data from Berkeley. *Science, 187*(4175), 398-404. https://doi.org/10.1126/science.187.4175.398
  - *How they used it:* Aggregate fall-1973 Berkeley admissions seemed to favour men, but department-by-department tables showed no bias against women. The aggregate gap came from women applying to more selective departments.
- **Applied to the NHL model:** Simpson check, ROI favorites vs underdogs pooled: fav +3.7%, dog +16.8%; by season 2025: fav +5.6% dog +12.0%; 2026: fav +2.2% dog +23.2%.

### A32. Conditional probability  ·  *Confirmed out of sample*
- **Formula / idea:** P(A | B) = P(A ∩ B) / P(B).
- **Paper:** Stern, H. (1991). On the probability of winning a football game. *The American Statistician, 45*(3), 179-183. https://doi.org/10.1080/00031305.1991.10475798 *(citation details partly unverified)*
  - *How they used it:* Using NFL games, he estimated P(favourite wins \
- **Applied to the NHL model:** Conditional probability: P(win | price moved toward us) 55.4%, P(win | no move) 58.5%, P(win | moved against) 43.8%; P(move toward us | bet) 73.2%, against 17.5%.

### A33. Independence of events / hot hand  ·  *Confirmed out of sample*
- **Formula / idea:** Independent iff P(A ∩ B) = P(A)P(B), i.e. P(A | B) = P(A).
- **Paper:** Miller, J. B., & Sanjurjo, A. (2018). Surprised by the hot hand fallacy? A truth in the law of small numbers. *Econometrica, 86*(6), 2019-2047. https://doi.org/10.3982/ECTA14943
  - *How they used it:* They showed that the standard measure (hit rate after streaks within finite sequences) is biased toward finding independence. After correcting this bias in the Gilovich et al. shooting data, the evidence reversed toward a hot hand.
- **Applied to the NHL model:** Independence: same-night bet results (vs price) r=-0.016 (837 pairs); runs test 353 runs vs 346 expected, p=0.573.
- **2016-22 check:** 2016-22 runs test p=0.097

### A34. Multiplication law (joint probability, parlays)  ·  *No trend*
- **Formula / idea:** Multiplication law: P(A ∩ B) = P(A | B)P(B); = P(A)P(B) if independent.
- **Paper:** Snowberg, E., & Wolfers, J. (2010). Explaining the favorite-long shot bias: Is it risk-love or misperceptions? *Journal of Political Economy, 118*(4), 723-746. https://doi.org/10.1086/655844
  - *How they used it:* Using US horse-race data, they built prices for compound bets (exacta, quinella, trifecta) from win-pool probabilities multiplied through. Comparing these with actual exotic prices showed that probability misperception, not risk-love, explains the favourite-longshot bias.
- **Applied to the NHL model:** Multiplication law: two average bets (win 53.7% each, average price +105) both win 28.8% if independent. Same-game parlays are only fair if the legs are independent. Check P(over | home win) 49.5% vs P(over) 49.3%; P(over | favorite wins) 49.0% vs P(over | underdog wins) 49.6%.

### A35. Sensitivity and specificity  ·  *Tool*
- **Formula / idea:** Sensitivity = P(+ | condition); specificity = P(− | no condition).
- **Paper:** Altman, D. G., & Bland, J. M. (1994). Diagnostic tests 1: Sensitivity and specificity. *BMJ, 308*(6943), 1552. https://www.bmj.com/content/308/6943/1552 (DOI not confirmed)
  - *How they used it:* Using liver scan results checked against pathology as the true diagnosis, they showed how to compute the proportion of true positives detected (sensitivity) and true negatives detected (specificity).
- **Applied to the NHL model:** Sensitivity/specificity, 'model likes home more than the market' as a test for 'home wins': sensitivity 61.0%, specificity 43.9%. Barely better than a coin, which is expected: the market already uses most of the information.

### A36. Bayes' formula / Bayesian updating  ·  *Tool*  ⇄
- **Formula / idea:** Bayes: P(A | B) = P(B | A)P(A) / [P(B | A)P(A) + P(B | Aᶜ)P(Aᶜ)].
- **Paper:** Glickman, M. E., & Stern, H. S. (1998). A state-space model for National Football League scores. *Journal of the American Statistical Association, 93*(441), 25-35. https://doi.org/10.2307/2669599
  - *How they used it:* They fitted a Bayesian state-space model to NFL scores (1988-1993) in which team strengths evolve week to week and season to season, updating posteriors by simulation. Out-of-sample predictions for late-1993 games were competitive with the Las Vegas line.
- **Applied to the NHL model:** Bayes: with a skeptical prior on ROI (mean 0, SD 3%, i.e. most bettors have no edge) and the data (mean +11.44%, SE 4.13%), the posterior ROI is +3.96% (SD 2.43%); P(ROI > 0) = 0.949. The prior pulls a two-season record about halfway back to zero.
- **Carries over:** A skeptical prior pulls a short good record halfway back to zero.

### A37. Expected value & variance of a discrete random variable (EV of a bet)  ·  *Tool*
- **Formula / idea:** E[X] = Σ x·p(x); Var(X) = Σ (x − μ)²·p(x).
- **Paper:** Kelly, J. L., Jr. (1956). A new interpretation of information rate. *Bell System Technical Journal, 35*(4), 917-926. https://archive.org/details/bstj35-4-917 (DOI not confirmed)
  - *How they used it:* He modelled a gambler with a private information edge and showed that betting a fixed fraction of wealth, set by the edge and the odds, maximizes expected log growth of the bankroll.
- **Applied to the NHL model:** At the median price (+105, decimal 2.05) and 53.7% win rate: E[X]=+0.100u, SD 1.02u. Full Kelly 9.6% of bankroll; using the market-blended probability instead (51.2%) Kelly is 4.7%.

### A38. Binomial distribution  ·  *Confirmed (in-sample)*
- **Formula / idea:** Binomial: P(X = k) = C(n,k)pᵏ(1 − p)ⁿ⁻ᵏ; μ = np, σ² = np(1 − p).
- **Paper:** Mosteller, F. (1952). The World Series competition. *Journal of the American Statistical Association, 47*(259), 355-380. DOI not confirmed (citation confirmed via JASA reference lists)
  - *How they used it:* He modelled World Series games as independent trials with a fixed win probability and used binomial-based series probabilities on historical Series results to ask how often the better team wins a 7-game series.
- **Applied to the NHL model:** Wins vs the market's own chances (a 'Poisson-binomial', each bet its own p): expected 324 wins, SD 12.9; observed 372. P(at least 372) = 0.0004.

### A39. Poisson distribution / overdispersion  ·  *Confirmed out of sample*
- **Formula / idea:** Poisson: P(Y = k) = e^(−λ)λᵏ/k!; μ = σ² = λ; rate scaling λ = r·(t/t₀).
- **Paper:** Maher, M. J. (1982). Modelling association football scores. *Statistica Neerlandica, 36*(3), 109-118. https://doi.org/10.1111/j.1467-9574.1982.tb00782.x
  - *How they used it:* He fitted independent Poisson models with team attack and defence parameters to English league scores and checked goodness of fit. Poisson fitted reasonably well, and a bivariate Poisson (correlation about 0.2) improved it.
- **Applied to the NHL model:** Poisson is the natural model for hockey goals. Regulation goals per team: mean 2.98, variance 3.01 (dispersion 1.01; Poisson = 1). P(0 goals) Poisson 5.1% vs actual 5.1%; P(5+) 18.1% vs 19.2%. Rate scaling: 0.050 goals per minute -> 0.25 in a 5-minute OT for one team.
- **2016-22 check:** 2016-22 regulation goals mean 2.87, variance 2.92, dispersion 1.02

### A40. Poisson approximation to binomial (rare events)  ·  *Tool*
- **Formula / idea:** Binomial(n, p) ≈ Poisson(λ = np) when n large and p small.
- **Paper:** Hanley, J. A., & Bhatnagar, S. (2022). The "Poisson" distribution: History, reenactments, adaptations. *The American Statistician, 76*(4), 363-371. https://doi.org/10.1080/00031305.2022.2046159
  - *How they used it:* They traced the Poisson law from its derivation as a limit of the binomial for rare events through original biological and physical applications, and showed how to handle extra-Poisson variation in counts of human behaviour.
- **Applied to the NHL model:** Rare events: games with 10+ goals are 7.51%. In a 82-game team season, number of 10+ goal games ~ Binomial(82, 0.0751) ~ Poisson(6.15): P(none) 0.002 vs 0.002.

### A41. Continuous densities, probability as area  ·  *Tool*
- **Formula / idea:** Continuous X: P(a ≤ X ≤ b) = area under the density f(x) between a and b.
- **Paper:** Stern, H. S. (1994). A Brownian motion model for the progress of sports scores. *Journal of the American Statistical Association, 89*(427), 1128-1134. https://doi.org/10.1080/01621459.1994.10476851
  - *How they used it:* He modelled the home-minus-away score as Brownian motion with drift and fitted it to 493 NBA games from 1991-92. The win probability at any moment is the area under a normal density beyond the current lead.
- **Applied to the NHL model:** Probability as area: P(over) = sum of the Poisson score grid above the line (plus OT). Model P(over) vs actual by quintile: 41.1%/45.9%, 45.9%/45.7%, 49.1%/47.2%, 52.5%/52.0%, 57.5%/58.1%.

### A42. Normal distribution / z-scores of game outcomes  ·  *Tool*
- **Formula / idea:** X ~ N(μ, σ²); Z = (X − μ)/σ ~ N(0, 1).
- **Paper:** Harville, D. (1980). Predictions for National Football League games via linear-model methodology. *Journal of the American Statistical Association, 75*(371), 516-524. https://doi.org/10.1080/01621459.1980.10477504
  - *How they used it:* He predicted NFL score differences (1,320 games, 1971-1977) with a mixed linear model that had team-year effects (autoregressive across years) and home advantage. Mean absolute error was 10.68 versus 10.49 for bookmakers.
- **Applied to the NHL model:** z-score of the record vs market prices: z = (wins - sum q)/sqrt(sum q(1-q)) = +3.70.

### A43. Normal quantiles  ·  *Tool*
- **Formula / idea:** Quantile x_p = μ + z_p·σ, where P(Z ≤ z_p) = p.
- **Paper:** Jorion, P. (1996). Risk2: Measuring the risk in value at risk. *Financial Analysts Journal, 52*(6), 47-56. https://doi.org/10.2469/faj.v52.n6.2039
  - *How they used it:* He analysed value at risk, a loss quantile computed (under normality) as a normal quantile times portfolio SD, and showed that VaR estimates carry sampling error that must be measured.
- **Applied to the NHL model:** Quantiles: with total goals ~ Poisson(model mean ~6.13), the 95th percentile is 10 goals; normal approximation gives 10.2. Observed share of games at or above 10: 7.5% (Poisson 9.3%).

### A44. Random sampling / bootstrap resampling  ·  *Tool*
- **Formula / idea:** Random sample: every subset of size n equally likely.
- **Paper:** Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *The Annals of Statistics, 7*(1), 1-26. https://doi.org/10.1214/aos/1176344552
  - *How they used it:* He introduced the bootstrap: resample the observed data with replacement to approximate the sampling distribution of a statistic, and showed that it generalizes the jackknife.
- **Applied to the NHL model:** Random 300-bet samples: ROI 95% range +2.4% to +20.5%; 0.9% negative (understates risk; see A45).

### A45. Sampling distribution of the mean / standard error  ·  *Tool*
- **Formula / idea:** Sampling distribution of x̄: mean μ, standard error σ/√n.
- **Paper:** Tversky, A., & Kahneman, D. (1971). Belief in the law of small numbers. *Psychological Bulletin, 76*(2), 105-110. https://doi.org/10.1037/h0031322
  - *How they used it:* Surveying research psychologists, they found that people treat small samples as highly representative of the population, underestimating sampling variability and overestimating the odds that a result replicates.
- **Applied to the NHL model:** SE of ROI = 1.086/sqrt(693) = 4.13%; one season (~346 bets) SE 5.84% vs ROI +11.44%: one season is 2.0 SEs from zero.

### A46. Central limit theorem  ·  *Tool*
- **Formula / idea:** CLT: x̄ (and sums) approximately normal for large n (n ≥ 30), whatever the population shape.
- **Paper:** Fama, E. F. (1965). The behavior of stock-market prices. *The Journal of Business, 38*(1), 34-105. https://doi.org/10.1086/294743
  - *How they used it:* Using daily returns of the 30 Dow Jones stocks, he found fat-tailed, leptokurtic distributions consistent with stable Paretian laws. This is the case where the finite-variance CLT does not give normal sums.
- **Applied to the NHL model:** CLT: units per 50-bet block (13 blocks) mean +4.77, SD 4.66 (theory 7.68), skew +0.20, Shapiro p=0.85.

### A47. Normal approximation to binomial with continuity correction  ·  *Confirmed (in-sample)*
- **Formula / idea:** Normal approx to binomial if np ≥ 10, n(1 − p) ≥ 10: P(X ≤ k) ≈ P(Z ≤ (k + 0.5 − np)/√(np(1 − p))).
- **Paper:** Emura, T., & Liao, Y. T. (2018). Critical review and comparison of continuity correction methods: The normal approximation to the binomial distribution. *Communications in Statistics - Simulation and Computation, 47*(8), 2266-2285. https://doi.org/10.1080/03610918.2017.1341527
  - *How they used it:* They compared Yates' ±0.5 continuity correction with Cressie's finely tuned correction for approximating binomial probabilities and confidence limits, with industrial and medical data examples. Yates' correction performed poorly in extreme tails.
- **Applied to the NHL model:** Normal approximation with continuity correction using the average market chance 0.468: P(X >= 372) ~ 0.0002 (simulation in A38: 0.0004).


## Estimation and tests for one or two populations

### B48. Point estimation  ·  *Tool*
- **Formula / idea:** Point estimate: a single number (x̄, p̂) for a parameter.
- **Paper:** Efron, B., & Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. *Journal of the American Statistical Association, 70*(350), 311-319. https://doi.org/10.1080/01621459.1975.10479864
  - *How they used it:* Took the batting averages of 18 MLB players after their first 45 at-bats of 1970 and predicted their rest-of-season averages. Shrinking each player toward the group mean (James-Stein) cut total squared prediction error from 17.56 (raw averages) to 5.01, and it beat the raw average for 15 of 18 players.
- **Applied to the NHL model:** Point estimates: ROI +0.1144u/bet; win rate 0.5368; model total-goals bias +0.046 goals/game; opener total bias +0.181.

### B49. Confidence interval for a mean (t)  ·  *Tool*
- **Formula / idea:** CI for μ: x̄ ± t(n−1, 1−α/2)·s/√n.
- **Paper:** Hopkins, W. G. (2000). Measures of reliability in sports medicine and science. *Sports Medicine, 30*(1), 1-15. https://doi.org/10.2165/00007256-200030010-00001
  - *How they used it:* Showed how to report test-retest data in sport science as a within-athlete "typical error" and a mean change between trials, each with t-based confidence limits, so readers can see how precisely the mean change is estimated rather than just whether it is significant.
- **Applied to the NHL model:** 95% t CI for ROI: +3.34% to +19.54%. Total-goals bias +0.046 +/- 0.092 (t=0.99, p=0.323).

### B50. Sample size for a margin of error  ·  *Tool*
- **Formula / idea:** n ≈ (z_(α/2)·σ / E)², round up.
- **Paper:** Lenth, R. V. (2001). Some practical guidelines for effective sample size determination. *The American Statistician, 55*(3), 187-193. https://doi.org/10.1198/000313001317098149
  - *How they used it:* Methods/practice paper (no single dataset). It argues that sample size should come from a scientifically meaningful effect size or margin of error and realistic variance inputs, and it criticises "canned" standardized effect sizes and retrospective power calculations.
- **Applied to the NHL model:** Bets needed for ROI +/-2% (95%): (1.96 x 1.09/0.02)^2 = 11,331; +/-5%: 1,813. Dog-heavy betting is noisier than NBA -110 bets (SD 1.09 vs 0.95).

### B51. Hypothesis test framework / one- vs two-sided  ·  *Confirmed (in-sample)*
- **Formula / idea:** Test: H0, Ha, test statistic, rejection region, conclusion. One-sided vs two-sided Ha.
- **Paper:** Pankoff, L. D. (1968). Market efficiency and football betting. *The Journal of Business, 41*(2), 203-214. https://doi.org/10.1086/295077
  - *How they used it:* An early efficiency test of the NFL point-spread market. It asked whether spreads were unbiased forecasts of game margins and whether published experts could beat them, setting the null as "the line is efficient" against inefficiency alternatives, and found little exploitable inefficiency.
- **Applied to the NHL model:** H0 ROI <= 0 vs Ha ROI > 0: t=2.77, one-sided p=0.0028. In-sample (these seasons shaped the 6% rule).

### B52. Type I / Type II error and power  ·  *Tool*  ⇄
- **Formula / idea:** Type I (reject true H0, rate α); Type II (miss false H0, rate β); power = 1 − β.
- **Paper:** Button, K. S., Ioannidis, J. P. A., Mokrysz, C., Nosek, B. A., Flint, J., Robinson, E. S. J., & Munafo, M. R. (2013). Power failure: Why small sample size undermines the reliability of neuroscience. *Nature Reviews Neuroscience, 14*(5), 365-376. https://doi.org/10.1038/nrn3475
  - *How they used it:* Pooled meta-analyses across neuroscience and estimated a median statistical power of about 20%. Low power both misses real effects and means that the significant results that do appear tend to be false positives or overstated (the "winner's curse").
- **Applied to the NHL model:** Power for a true +4% ROI: 300 bets 16%, 693 bets 25%; 80% power needs ~4,600 bets. For +8%: 1,150.
- **Carries over:** Small edges need thousands of trials, any market.

### B53. p-values  ·  *Confirmed (in-sample)*
- **Formula / idea:** p-value = P(statistic at least as extreme as observed | H0); reject if p ≤ α.
- **Paper:** Brodeur, A., Le, M., Sangnier, M., & Zylberberg, Y. (2016). Star Wars: The empirics strike back. *American Economic Journal: Applied Economics, 8*(1), 1-32. https://doi.org/10.1257/app.20150044
  - *How they used it:* Replaces the ASA statement candidate (a policy statement, not a standard peer-reviewed study). Collected about 50,000 test statistics from AER, JPE and QJE and found a two-humped distribution: too few p-values between 0.10 and 0.25 and an excess just below 0.05. They attribute 10-20% of marginally significant results to specification searching.
- **Applied to the NHL model:** p-values here: permutation 0.0002, simulation vs market 0.0004, t-test 0.0028. Each is P(this good | no edge), on seasons that helped pick the rule.

### B54. Student t distribution / one-sample t test  ·  *Confirmed (in-sample)*
- **Formula / idea:** t = (x̄ − μ0)/(s/√n), df = n − 1; heavier tails than Z for small n.
- **Paper:** Student. (1908). The probable error of a mean. *Biometrika, 6*(1), 1-25. https://doi.org/10.1093/biomet/6.1.1
  - *How they used it:* Derived the small-sample distribution of (mean - mu)/(s/sqrt(n)), checked it empirically, and applied it to Cushny and Peebles' paired data on the extra hours of sleep gained from two hypnotic drugs (10 patients), showing how to judge a mean difference when n is tiny.
- **Applied to the NHL model:** t distribution: df=692, t(0.975)=1.963. One-sample t on (won - market price): mean +0.069, t=3.68.

### B55. Pooled two-sample t test (comparing two group means)  ·  *Warning*
- **Formula / idea:** Pooled t = (x̄1 − x̄2)/(s_p√(1/n1 + 1/n2)), s_p² = [(n1−1)s1² + (n2−1)s2²]/(n1 + n2 − 2).
- **Paper:** Edmans, A., Garcia, D., & Norli, O. (2007). Sports sentiment and stock returns. *The Journal of Finance, 62*(4), 1967-1998. https://doi.org/10.1111/j.1540-6261.2007.01262.x
  - *How they used it:* Compared mean next-day national stock-market returns after international soccer losses vs wins (1,162 matches in 39 countries). Losses averaged -18.4 bp and wins +5.0 bp. The formal test is a dummy-variable regression, equivalent to a two-sample mean comparison, with panel-corrected rather than pooled-variance SEs. Loss days showed significant negative abnormal returns (-21 bp, t = -3.3); win days showed none.
- **Applied to the NHL model:** Pooled t: ROI favorites +3.7% (n=285) vs underdogs +16.8% (n=408): t=-1.57, p=0.118.
- **2016-22 check:** 2016-22: favorites +2.5% (n=697), dogs +0.6% (n=2156), p=0.699

### B56. Welch t test  ·  *No trend*
- **Formula / idea:** Welch t = (x̄1 − x̄2)/√(s1²/n1 + s2²/n2), Satterthwaite df.
- **Paper:** Welch, B. L. (1947). The generalization of "Student's" problem when several different population variances are involved. *Biometrika, 34*(1-2), 28-35. https://doi.org/10.1093/biomet/34.1-2.28
  - *How they used it:* Canonical methods source. It derived the approximate degrees of freedom for comparing means when the groups have unequal variances, which is the basis of the Welch t test that R's `t.test()` uses by default.
- **Applied to the NHL model:** Welch t (variances differ: dog profits swing more, SD 1.23 vs 0.84): t=-1.67, p=0.096. Bets on a team on a back-to-back (won - price -0.025, n=62) vs rested (+0.078): p=0.113.

### B57. Paired t test / comparing forecast accuracy  ·  *Warning*
- **Formula / idea:** Paired: d_i = x1i − x2i; t = d̄/(s_d/√n), df = n − 1.
- **Paper:** Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics, 13*(3), 253-263. https://doi.org/10.1080/07350015.1995.10524599 (RePEc: https://econpapers.repec.org/RePEc:bes:jnlbes:v:13:y:1995:i:3:p:253-63)
  - *How they used it:* Proposed testing whether two forecasts are equally accurate by treating the per-period loss differential as a paired series and testing its mean, with a long-run variance correction for serial correlation. Size and power were checked by Monte Carlo.
- **Applied to the NHL model:** Paired t on per-game log loss (opener minus model; positive = model better): +0.0030, t=+1.37, p=0.171; close minus model -0.0041, p=0.049.
- **2016-22 check:** 2016-22 team-only model: opener minus model log loss -0.0034, p=0.015

### B58. F test / ratio of two variances  ·  *No trend*
- **Formula / idea:** F = s1²/s2², df (n1 − 1, n2 − 1).
- **Paper:** Lo, A. W., & MacKinlay, A. C. (1988). Stock market prices do not follow random walks: Evidence from a simple specification test. *The Review of Financial Studies, 1*(1), 41-66. https://doi.org/10.1093/rfs/1.1.41 (RePEc: https://ideas.repec.org/a/oup/rfinst/v1y1988i1p41-66.html)
  - *How they used it:* Used a variance-ratio statistic (variance of q-week returns over q times the variance of 1-week returns) on CRSP weekly returns from 1962 to 1985. Ratios well above 1 rejected the random walk, especially for small-stock portfolios, showing positive autocorrelation. (A ratio-of-variances test rather than the textbook two-sample F.)
- **Applied to the NHL model:** F test, variance of total goals Oct-Dec (5.29) vs Feb-Apr (5.51): F=0.960, p=0.521.


## ANOVA and multiple comparisons

### B59. One-way ANOVA  ·  *Suggestive (does not replicate)*
- **Formula / idea:** One-way ANOVA: SST = SSB + SSW; F = MSB/MSW, df (t − 1, N − t).
- **Paper:** Gibbons, M. R., & Hess, P. (1981). Day of the week effects and asset returns. *The Journal of Business, 54*(4), 579-596. https://doi.org/10.1086/296147
  - *How they used it:* Tested whether mean daily returns on stock indices (S&P 500, CRSP) and Treasury bills are equal across the five weekdays (one factor, five levels). They rejected equality, driven by strongly negative Monday means.
- **Applied to the NHL model:** One-way ANOVA, (goals - opening total) across months: F=2.19, p=0.041. Means: Oct +0.36, Nov -0.16, Dec +0.16, Jan +0.09, Feb +0.36, Mar +0.25, Apr +0.37. Model bets' profit by month: p=0.643.
- **2016-22 check:** 2016-22 month ANOVA on (goals - opener) p=0.292; means Oct +0.28, Nov +0.10, Dec +0.26, Jan +0.25, Feb +0.14, Mar +0.13, Apr +0.34

### B60. Equal-variance assumption (Levene / Brown-Forsythe)  ·  *No trend*
- **Formula / idea:** ANOVA assumes normal errors with equal variance; check by Q-Q plots and residual-vs-fitted spread (Levene/Brown-Forsythe, Bartlett).
- **Paper:** Brown, M. B., & Forsythe, A. B. (1974). Robust tests for the equality of variances. *Journal of the American Statistical Association, 69*(346), 364-367. https://doi.org/10.1080/01621459.1974.10482955
  - *How they used it:* Used Monte Carlo to compare Levene-type tests and showed that the median-centred version keeps its nominal size under skewed and heavy-tailed data, where Bartlett's test fails.
- **Applied to the NHL model:** ANOVA assumptions: Brown-Forsythe/Levene equal-variance p=0.402, Bartlett p=0.135; residuals are discrete counts but n is large, so the F test is robust.

### B61. Transformations (log, sqrt)  ·  *No trend*
- **Formula / idea:** Transform y (log, √, power) to fix skew or unequal variance.
- **Paper:** Bartlett, M. S. (1947). The use of transformations. *Biometrics, 3*(1), 39-52. https://doi.org/10.2307/3001536
  - *How they used it:* Reviewed variance-stabilising transformations (square root for Poisson-like counts, log for multiplicative data, angular for proportions) with worked examples, showing when they make ANOVA assumptions hold.
- **Applied to the NHL model:** Transformation: for Poisson counts the square root stabilizes the variance. Var of total goals by opener: 5.5: 5.28, 6.0: 5.59, 6.5: 5.38; var of sqrt(goals): 5.5: 0.227, 6.0: 0.264, 6.5: 0.226.

### B62. Contrasts  ·  *Suggestive (does not replicate)*
- **Formula / idea:** Contrast L = Σc_iμ_i with Σc_i = 0; SE = √(MSE·Σc_i²/n_i).
- **Paper:** French, K. R. (1980). Stock returns and the weekend effect. *Journal of Financial Economics, 8*(1), 55-69. https://doi.org/10.1016/0304-405X(80)90021-5
  - *How they used it:* Used daily S&P 500 returns (1953-1977) to test planned comparisons: Monday vs other days under a "calendar-time" hypothesis (Monday should be about 3x a normal day) and a "trading-time" hypothesis (all days equal). Monday's mean was significantly negative, rejecting both.
- **Applied to the NHL model:** Planned contrast early (Oct-Dec) minus late (Feb-Apr) in (goals - opener): -0.205 goals, t=-1.88, p=0.061.

### B63. Orthogonal contrasts (incl. orthogonal polynomials)  ·  *Tool*
- **Formula / idea:** Orthogonal contrasts: Σc_i d_i/n_i = 0; their SS partition SSB.
- **Paper:** Lowry, S. R. (1992). Use and misuse of multiple comparisons in animal experiments. *Journal of Animal Science, 70*(6), 1971-1977. https://doi.org/10.2527/1992.7061971x
  - *How they used it:* Re-analysed data from three *Journal of Animal Science* papers. It showed that structured or factorial treatments should be broken into planned orthogonal contrasts, and quantitative dose levels into orthogonal polynomial (linear/quadratic) contrasts, instead of running all-pairs multiple-comparison tests.
- **Applied to the NHL model:** Orthogonal contrasts: early-vs-late SS 19.4 of SSB 72.5; the remaining month-to-month SS is spread across the other 5 orthogonal pieces.

### B67. Tukey HSD  ·  *Suggestive (does not replicate)*
- **Formula / idea:** Tukey HSD: all pairwise differences, familywise α via the studentized range q.
- **Paper:** Kramer, C. Y. (1956). Extension of multiple range tests to group means with unequal numbers of replications. *Biometrics, 12*(3), 307-310. https://doi.org/10.2307/3001469
  - *How they used it:* Replaces the Tukey (1949) candidate: Tukey 1949 is the gap-straggling procedure, and HSD itself first appeared in an unpublished 1953 manuscript. Kramer extended Tukey's studentized-range test to unequal group sizes (Tukey-Kramer), which is what R's `TukeyHSD()` computes.
- **Applied to the NHL model:** Tukey HSD, all 21 month pairs: 0 significant; smallest adjusted p=0.069.

### B66. Fisher LSD  ·  *Suggestive (does not replicate)*
- **Formula / idea:** Fisher LSD: unadjusted pairwise t-tests, only after a significant overall F.
- **Paper:** Carmer, S. G., & Swanson, M. R. (1973). An evaluation of ten pairwise multiple comparison procedures by Monte Carlo methods. *Journal of the American Statistical Association, 68*(341), 66-74. https://doi.org/10.1080/01621459.1973.10481335
  - *How they used it:* Simulated Type I, Type III and correct-decision rates for ten pairwise procedures. They recommended the restricted (protected) LSD, i.e. unadjusted pairwise t tests run only after a significant ANOVA F, over the Scheffe, Tukey and SNK tests on power grounds.
- **Applied to the NHL model:** Fisher's LSD: 4 of 21 month pairs at unadjusted 5% (only allowed if the overall F is significant; here p=0.041).

### B68. Scheffe method  ·  *Suggestive (does not replicate)*
- **Formula / idea:** Scheffé: any (incl. unplanned) contrast; reject if t² > (t − 1)·F(α; t − 1, N − t).
- **Paper:** Scheffe, H. (1953). A method for judging all contrasts in the analysis of variance. *Biometrika, 40*(1-2), 87-110. https://doi.org/10.1093/biomet/40.1-2.87
  - *How they used it:* Derived simultaneous intervals, based on the F distribution, that remain valid for every possible contrast, including ones chosen after seeing the data, at the cost of wider intervals.
- **Applied to the NHL model:** Scheffe bar for an after-the-fact contrast: t > 3.55; best-minus-worst month t=2.75: doesn't clear it.


## Categorical data

### B69. One-proportion CI (Wilson / Agresti-Coull)  ·  *Confirmed (in-sample)*
- **Formula / idea:** π̂ ± z·√(π̂(1 − π̂)/n) (Wilson/Agresti-Coull better); z = (π̂ − π0)/√(π0(1 − π0)/n).
- **Paper:** Agresti, A., & Coull, B. A. (1998). Approximate is better than "exact" for interval estimation of binomial proportions. *The American Statistician, 52*(2), 119-126. https://doi.org/10.1080/00031305.1998.10480550
  - *How they used it:* Compared coverage of the Wald, Clopper-Pearson "exact" and score intervals for a binomial p. The Wald interval undercovers badly, while the Wilson score and "add 2 successes and 2 failures" intervals have near-nominal coverage and are shorter than exact.
- **Applied to the NHL model:** One proportion: win rate 53.7% (Wilson 95% CI 50.0%-57.4%) vs the market's average chance for these bets 46.8%. Games over the opening total: 49.2%, under 49.6%.

### B70. Sample size for a proportion  ·  *Tool*
- **Formula / idea:** n = z²·π(1 − π)/E².
- **Paper:** Lachin, J. M. (1981). Introduction to sample size determination and power analysis for clinical trials. *Controlled Clinical Trials, 2*(2), 93-113. https://doi.org/10.1016/0197-2456(81)90001-5
  - *How they used it:* Gave the standard normal-approximation formulas, with worked clinical-trial examples, for the sample size and power needed to detect differences in proportions (and in means and survival) at a given alpha and power.
- **Applied to the NHL model:** Sample size for a win rate at +/-2% (p~0.45): 2,377 bets; +/-3%: 1,057.

### B71. Two-proportion z test  ·  *No trend*
- **Formula / idea:** z = (π̂1 − π̂2)/√(π̂(1 − π̂)(1/n1 + 1/n2)) with pooled π̂.
- **Paper:** Pope, D. G., & Schweitzer, M. E. (2011). Is Tiger Woods loss averse? Persistent bias in the face of experience, competition, and high stakes. *American Economic Review, 101*(1), 129-157. https://doi.org/10.1257/aer.101.1.129 (RePEc: https://econpapers.repec.org/RePEc:aea:aecrev:v:101:y:2011:i:1:p:129-57)
  - *How they used it:* Compared make rates for PGA Tour par putts vs birdie putts of the same distance using about 2.5 million laser-measured putts. Par putts were made about 2-3 percentage points more often, a difference in two proportions that held up with controls (distance, player and hole effects).
- **Applied to the NHL model:** Two proportions: win rate 2024-25 52.8% vs 2025-26 54.7% (market chance 46.0% / 47.7%): z=-0.51, p=0.613.

### B72. Fisher's exact test  ·  *No trend*
- **Formula / idea:** Fisher's exact test: hypergeometric probability of tables with fixed margins.
- **Paper:** Henriksson, R. D., & Merton, R. C. (1981). On market timing and investment performance. II. Statistical procedures for evaluating forecasting skills. *The Journal of Business, 54*(4), 513-533. https://doi.org/10.1086/296144
  - *How they used it:* Built a nonparametric test of market-timing skill. Under no skill, the number of correct "up" calls given the totals in a 2x2 table follows a hypergeometric distribution, which is Fisher's exact test, and they applied it to evaluate fund managers' and forecasters' calls.
- **Applied to the NHL model:** Fisher's exact, long shots (+200 or longer, 34 bets) home vs away: away 9-18; home 4-3; p=0.387. Long-shot record 38.2% vs market 28.6%, ROI +27.9%.

### B73. Chi-square goodness of fit  ·  *Confirmed out of sample*  ⇄
- **Formula / idea:** χ² = Σ(O − E)²/E, df = k − 1 − (estimated parameters).
- **Paper:** Reep, C., & Benjamin, B. (1968). Skill and chance in association football. *Journal of the Royal Statistical Society. Series A (General), 131*(4), 581-585. https://doi.org/10.2307/2343726 (JSTOR: https://www.jstor.org/stable/2343726)
  - *How they used it:* Fitted a negative binomial distribution to the frequencies of passing-move lengths recorded in English League and World Cup matches and compared observed with expected counts. The fit was close, implying that a large share of football outcomes behaves like a chance process.
- **Applied to the NHL model:** Chi-square goodness of fit, REGULATION total goals vs Poisson at the model's game-by-game mean: chi2=35.9, df=10, p=8.69e-05. Observed/expected: 0:7/7, 1:23/39, 2:114/113, 3:177/222, 4:377/328, 5:385/388, 6:438/385, 7:298/329, 8:257/246, 9:167/164, 10:182/204. FINAL totals are a different story: every regulation tie adds exactly one goal (OT or shootout winner), so finals are odd 67.8% of the time vs 45.6% in regulation. A plain Poisson on final goals would misprice every total.
- **2016-22 check:** 2016-22 regulation totals vs Poisson chi2=80.9, p=3.35e-13 (0:33/27, 1:96/146, 2:414/404, 3:605/748, 4:1118/1042, 5:1067/1168, 6:1229/1095, 7:910/884, 8:672/628, 9:399/398, 10:445/448); finals odd 68.9% vs regulation 46.2%
- **Carries over:** Outcomes that bunch at a 'tie' point more than an independence model says (pinning near round numbers / option strikes is the market cousin).

### B74. Chi-square test of independence  ·  *No trend*
- **Formula / idea:** Independence: E_ij = (row_i·col_j)/n; χ² with df (r − 1)(c − 1).
- **Paper:** Pesaran, M. H., & Timmermann, A. (1992). A simple nonparametric test of predictive performance. *Journal of Business & Economic Statistics, 10*(4), 561-565. https://doi.org/10.1080/07350015.1992.10509922 (RePEc: https://econpapers.repec.org/RePEc:bes:jnlbes:v:10:y:1992:i:4:p:561-65)
  - *How they used it:* Proposed a test of whether a forecast predicts the direction of change, based on the predicted-vs-actual contingency table, and related it to the chi-square test of independence (which it shows is more conservative). It was applied to CBI and INSEE survey expectations of price and demand changes.
- **Applied to the NHL model:** Chi-square independence: season x win p=0.667; month x overtime p=0.814 (OT rate by month Apr:21%, Dec:20%, Feb:21%, Jan:22%, Mar:24%, Nov:24%, Oct:23%).

### B75. Odds and odds ratios  ·  *Confirmed out of sample*  ⇄
- **Formula / idea:** Odds = p/(1 − p); OR = odds1/odds2; log(OR) SE = √(Σ1/n_ij).
- **Paper:** Bland, J. M., & Altman, D. G. (2000). Statistics notes: The odds ratio. *BMJ, 320*(7247), 1468. https://doi.org/10.1136/bmj.320.7247.1468
  - *How they used it:* Explained odds and the odds ratio with a 2x2 table of hay fever and eczema in 11-year-old children. It showed why the OR is symmetric and is the natural output of logistic regression, and how it differs from the relative risk.
- **Applied to the NHL model:** Odds ratio of winning, price moved toward us vs against: 1.60 (95% CI 1.07-2.38). Note the price itself changes: what matters is won 55.4% vs market 47.0% and 43.8% vs 46.1%.
- **2016-22 check:** 2016-22: moved toward us 1582 bets ROI +4.9% (won 49.2% vs market 45.1%); against 827 bets ROI -8.8% (39.5% vs 41.7%); share moving toward 55% vs against 29%
- **Carries over:** Price moving toward your position after entry marks skill, in both sports now.


## Regression, diagnostics and model choice

### B76. Simple linear regression / least squares  ·  *Confirmed out of sample*  ⇄
- **Formula / idea:** y = β0 + β1x + ε; b1 = Sxy/Sxx, b0 = ȳ − b1x̄ minimizes SSE = Σ(y − ŷ)².
- **Paper:** Paul, R. J., & Weinbach, A. P. (2008). Price setting in the NBA gambling market: Tests of the Levitt model of sportsbook behavior. *International Journal of Sport Finance, 3*(3), 137-145. https://ideas.repec.org/a/jsf/intjsf/v3y2008i3p137-145.html
  - *How they used it:* Used betting-percentage data from four sportsbooks for the 2004-05 to 2006-07 NBA seasons. An OLS regression of the share of bets on the over against the posted total gave a slope of about 0.12 (t of about 5.6): the public bets the over more as totals rise. Simple "bet the under" rules were then tested against a 50% win rate and the 52.38% break-even, and none were significant.
- **Applied to the NHL model:** Least squares: (home win - no-vig opener) = -0.006 + 0.775 x (model - opener) (SE 0.196, p=0.000). Slope 1 = the model's disagreements are fully right; 0.78 means trust about 78% of them (live blend: 55%). Totals: (goals - opener) on (model - opener) slope 0.92 (SE 0.10, p=0.000).
- **2016-22 check:** 2016-22 team-only model: slope 0.258 (SE 0.101, p=0.011); totals slope 0.69 (SE 0.08)
- **Carries over:** Regress outcome on your edge; slope = how much to trust it vs the market.

### B77. R squared  ·  *Tool*
- **Formula / idea:** R² = 1 − SSE/SST = share of variation explained.
- **Paper:** Berri, D. J. (1999). Who is "most valuable"? Measuring the player's production of wins in the National Basketball Association. *Managerial and Decision Economics, 20*(8), 411-427. https://doi.org/10.1002/1099-1468(199912)20:8<411::AID-MDE957>3.0.CO;2-G
  - *How they used it:* Regressed NBA team wins on team box-score statistics (points, possessions, rebounds, turnovers, etc.). The high R-squared showed the box score explains most of the variation in team wins, and the coefficients were then used to assign wins to individual players.
- **Applied to the NHL model:** R^2 of (home win - opener) on edge: 0.0064. Brier-style 'R^2' of probabilities: model 0.0365, opener 0.0311, close 0.0445. Hockey is close to a coin flip; even the close explains ~4%.

### B78. Regression F test (joint test)  ·  *Confirmed (in-sample)*
- **Formula / idea:** Regression F = MSR/MSE; tests all slopes = 0.
- **Paper:** Zuber, R. A., Gandar, J. M., & Bowers, B. D. (1985). Beating the spread: Testing the efficiency of the gambling market for National Football League games. *Journal of Political Economy, 93*(4), 800-806. https://doi.org/10.1086/261332
  - *How they used it:* Regressed actual NFL point differentials on the point spread (alongside a team-statistics forecasting model) and used an F test of the joint restriction intercept = 0, slope = 1 to test market efficiency. They argued their model identified profitable deviations, which prompted a well-known comment-and-reply debate in JPE.
- **Applied to the NHL model:** Regression F: F(1,2423)=15.66, p=0.000.

### B79. Prediction intervals  ·  *Tool*
- **Formula / idea:** Prediction interval (one new y) is wider than CI for the mean; extrapolation = predicting outside the observed x range.
- **Paper:** Christoffersen, P. F. (1998). Evaluating interval forecasts. *International Economic Review, 39*(4), 841-862. https://doi.org/10.2307/2527341
  - *How they used it:* Developed likelihood-ratio tests of unconditional coverage, independence of interval "hits", and conditional coverage, then applied them to interval forecasts of exchange rates used in risk management.
- **Applied to the NHL model:** Prediction vs extrapolation: at edge +3 pts the expected (win - market) is +0.018 (CI -0.003 to +0.039); a single game is win or lose (prediction interval covers everything). Edges of 15+ pts (0.6% of games) are outside where the fit has data.

### B80. Cook's distance / influential observations  ·  *Tool*
- **Formula / idea:** Cook's D_i = (r_i²/p)·h_ii/(1 − h_ii)²; flag if D > 4/n or > 1.
- **Paper:** Cook, R. D. (1977). Detection of influential observation in linear regression. *Technometrics, 19*(1), 15-18. https://doi.org/10.1080/00401706.1977.10489493
  - *How they used it:* Introduced the distance D_i, which measures how far the fitted coefficients move when observation i is deleted, combining residual size and leverage. It was demonstrated on a small published regression dataset in which one point dominated the fit.
- **Applied to the NHL model:** Cook's distance: 45 games above 4/n, max 0.0051; slope without them 0.966 vs 0.775.

### B81. Multiple linear regression  ·  *Suggestive*
- **Formula / idea:** y = β0 + β1x1 + … + βkxk + ε; each β = effect holding the others fixed.
- **Paper:** Scully, G. W. (1974). Pay and performance in Major League Baseball. *American Economic Review, 64*(6), 915-930. https://www.jstor.org/stable/1815242
  - *How they used it:* Regressed MLB team winning percentage on team slugging average and strikeout-to-walk ratio (with league and contention controls), then revenue on win percentage. This gave each player's marginal revenue product, which was well above salary under the reserve clause.
- **Applied to the NHL model:** Multiple regression of (home win - opener): edge +0.655 (p=0.001), b2b_diff -0.045 (p=0.047), fav_h -0.016 (p=0.462). R^2 0.0082.

### B82. Studentized residuals / outlier tests  ·  *Tool*
- **Formula / idea:** Studentized residual = e_i / (s_(i)√(1 − h_ii)); |t| > 2–3 flags outliers; Bonferroni outlier test.
- **Paper:** Beckman, R. J., & Cook, R. D. (1983). Outlier..........s. *Technometrics, 25*(2), 119-149. https://doi.org/10.1080/00401706.1983.10487840
  - *How they used it:* Canonical review, with discussion, of outlier detection in samples and regression. It covers internally vs externally studentized residuals, Bonferroni-bounded outlier tests (the basis of `car::outlierTest`) and masking/swamping, illustrated with classic datasets.
- **Applied to the NHL model:** Studentized residuals: 0.0% beyond |2|; max |t| 1.70. A binary response has bounded residuals (upsets of big favorites are the 'outliers'), so a linear model is a rough tool here; B98 is the right one.

### B83. Residual / normal Q-Q plots  ·  *Tool*
- **Formula / idea:** Q-Q plot of residuals checks normal errors.
- **Paper:** Fama, E. F. (1965). The behavior of stock-market prices. *The Journal of Business, 38*(1), 34-105. https://doi.org/10.1086/294743
  - *How they used it:* Plotted daily price changes for each of the 30 Dow Jones stocks (about 1957-1962) on normal probability paper (a Q-Q plot). The S-shaped departures showed tails much fatter than normal, supporting stable-Paretian (Mandelbrot) models.
- **Applied to the NHL model:** Residual Q-Q: bimodal (win/lose), Q-Q correlation 0.896. Normal-error inference is still fine for the slope at n=2425 by the CLT, but use logistic regression for probabilities.

### B84. Homoscedasticity test (Breusch-Pagan) and error independence  ·  *No trend*
- **Formula / idea:** Constant variance (Breusch-Pagan / ncvTest) and independent errors (Durbin-Watson ≈ 2).
- **Paper:** Breusch, T. S., & Pagan, A. R. (1979). A simple test for heteroscedasticity and random coefficient variation. *Econometrica, 47*(5), 1287-1294. https://doi.org/10.2307/1911963 (JSTOR: https://www.jstor.org/stable/1911963)
  - *How they used it:* Derived a Lagrange-multiplier test for heteroscedasticity computed from OLS residuals (regress squared residuals on candidate variables) and gave finite-sample evidence on its behaviour. (For serial independence, the companion classic is Durbin & Watson, 1950, *Biometrika*.)
- **Applied to the NHL model:** Homoscedasticity: Breusch-Pagan p=0.009 (binary outcome: variance p(1-p) is highest for even games, as expected). Totals: spread of (goals - opener) vs the opener p=0.844. Durbin-Watson 1.985.

### B85. Component + residual (partial residual) plots  ·  *Tool*
- **Formula / idea:** Component + residual (partial residual) plot: e + b_j·x_j vs x_j checks linearity of x_j.
- **Paper:** Larsen, W. A., & McCleary, S. J. (1972). The use of partial residual plots in regression analysis. *Technometrics, 14*(3), 781-790. https://doi.org/10.2307/1267305
  - *How they used it:* Introduced plots of each predictor's component plus the residual against that predictor, to reveal nonlinearity in one predictor after the others are accounted for, with worked regression examples.
- **Applied to the NHL model:** Component + residual for edge: binned -0.104->-0.080, -0.034->-0.007, -0.013->+0.020, +0.003->+0.028, +0.018->+0.018, +0.033->-0.004, +0.054->+0.035, +0.186->+0.044.

### B86. Added-variable plots  ·  *Suggestive*
- **Formula / idea:** Added-variable plot: residuals of y on others vs residuals of x_j on others; slope = b_j.
- **Paper:** Johnson, B. W., & McCulloch, R. E. (1987). Added-variable plots in linear regression. *Technometrics, 29*(4), 427-433. https://doi.org/10.1080/00401706.1987.10488270
  - *How they used it:* Reviewed three graphical methods for judging what an extra explanatory variable adds to a linear regression (including the added-variable / partial-regression plot) and proposed a new variant.
- **Applied to the NHL model:** Added-variable plot for back-to-backs: slope -0.045 (p=0.047) after removing edge and favorite status.

### B87. Spread-level plot  ·  *No trend*
- **Formula / idea:** Spread-level plot: log|resid spread| vs log(fitted); power transform ≈ 1 − slope.
- **Paper:** Emerson, J. D., & Stoto, M. A. (1982). Exploratory methods for choosing power transformations. *Journal of the American Statistical Association, 77*(377), 103-108. UNVERIFIED DOI; record: https://scilit.com/publications/9d66efb6a394f9649018dd9a424da9cd *(citation details partly unverified)*
  - *How they used it:* Extended Tukey's diagnostic plots, including the spread-vs-level plot for batches at different levels. When log(spread) vs log(level) is roughly linear with slope b, the suggested power transformation is p = 1 - b. (The title and abstract were confirmed. Volume/issue/pages are from recall and the DOI was not confirmed.)
- **Applied to the NHL model:** Spread-level: SD of (goals - opener) by opening total 5.5: 2.30 (n=1137), 6.0: 2.36 (n=148), 6.5: 2.32 (n=1137); log-log slope 0.06 (Poisson predicts 0.5 -> square-root transform, B61).

### B88. Multicollinearity / VIF  ·  *Tool*
- **Formula / idea:** VIF_j = 1/(1 − R_j²); > 5–10 = problem collinearity.
- **Paper:** O'Brien, R. M. (2007). A caution regarding rules of thumb for variance inflation factors. *Quality & Quantity, 41*(5), 673-690. https://doi.org/10.1007/s11135-006-9018-6
  - *How they used it:* Showed that the "VIF > 10 (or > 4) means trouble" rules are arbitrary. Inflated variance can be offset by larger samples or more variable predictors, and dropping variables to reduce VIF can bias the remaining estimates.
- **Applied to the NHL model:** VIF with raw probabilities as predictors: p_home 5.6, nv_open 7.1, nv_close 8.5. The model, opener and close all measure 'how good is the home team'; working with differences (edge, move) removes it: edge 1.3, move 1.3.

### B89. Box-Cox transformation  ·  *Tool*
- **Formula / idea:** Box-Cox: y^(λ) = (y^λ − 1)/λ (log if λ = 0); choose λ by likelihood.
- **Paper:** Box, G. E. P., & Cox, D. R. (1964). An analysis of transformations. *Journal of the Royal Statistical Society: Series B (Methodological), 26*(2), 211-252. https://doi.org/10.1111/j.2517-6161.1964.tb00553.x
  - *How they used it:* Estimated the power lambda by maximum likelihood. Animal survival times in a 3x4 poison-by-treatment experiment gave lambda of about -0.75 (near reciprocal, a "rate of dying"), and a 3^3 textile experiment gave lambda of about 0, a log transform that removed second-order terms.
- **Applied to the NHL model:** Box-Cox on (total goals + 1): lambda = 0.58 (0.5 = square root, as Poisson theory says).

### B90. Box-Tidwell transformation  ·  *No trend*
- **Formula / idea:** Box-Tidwell: test x^α for a predictor via the x·log(x) term.
- **Paper:** Box, G. E. P., & Tidwell, P. W. (1962). Transformation of the independent variables. *Technometrics, 4*(4), 531-550. https://doi.org/10.1080/00401706.1962.10490038
  - *How they used it:* Developed an iterative linearisation method to estimate power transformations of the predictors (rather than the response) in least-squares regression, with worked examples (implemented in `car::boxTidwell`).
- **Applied to the NHL model:** Box-Tidwell, opener chance as a predictor of home wins: x*log(x) term p=0.552 (linear in the market's chance is fine across this range).

### B91. Deleting observations / robustness  ·  *Tool*
- **Formula / idea:** Deleting observations: refit without flagged points to check robustness (only drop for real errors).
- **Paper:** Knez, P. J., & Ready, M. J. (1997). On the robustness of size and book-to-market in cross-sectional regressions. *The Journal of Finance, 52*(4), 1355-1382. https://ideas.repec.org/a/bla/jfinan/v52y1997i4p1355-82.html (DOI not located)
  - *How they used it:* Re-ran Fama-French cross-sectional regressions with a robust (least trimmed squares) estimator. Trimming the most extreme 1% of observations each month made the size premium vanish, and the negative average size coefficient came entirely from 16 extreme months.
- **Applied to the NHL model:** Deleting observations: dropping the 5% longest-priced bets (>= +196) changes ROI +11.4% -> +10.8%. The record doesn't hinge on a few long shots.

### B92. Interaction terms  ·  *No trend*
- **Formula / idea:** Interaction: y = β0 + β1x1 + β2x2 + β3x1x2; slope of x1 is β1 + β3x2.
- **Paper:** Brambor, T., Clark, W. R., & Golder, M. (2006). Understanding interaction models: Improving empirical analyses. *Political Analysis, 14*(1), 63-82. https://doi.org/10.1093/pan/mpi014 (RePEc: https://ideas.repec.org/a/cup/polals/v14y2006i01p63-82_00.html)
  - *How they used it:* Surveyed articles in the top three political science journals (1998-2002) and found widespread errors in multiplicative interaction models: omitted constitutive terms, and main effects read as unconditional. Only about 10% followed their checklist, and they showed how to plot conditional marginal effects with CIs.
- **Applied to the NHL model:** Interaction edge x home favorite: +0.294 (p=0.476); edge slope when home is the dog 0.576, when favorite 0.870.

### B93. Polynomial regression  ·  *No trend*
- **Formula / idea:** Polynomial: y = β0 + β1x + β2x² + β3x³ + ε.
- **Paper:** Fair, R. C. (2008). Estimated age effects in baseball. *Journal of Quantitative Analysis in Sports, 4*(1), Article 1. https://doi.org/10.2202/1559-0410.1074
  - *How they used it:* Fitted a fixed-effects model in which MLB performance (players with 10+ seasons, 1921-2004) rises quadratically to an estimated peak age and then declines quadratically at a separate rate. Peak age was in the late 20s, and aging effects were larger for pitchers than batters.
- **Applied to the NHL model:** Polynomial: edge^2 p=0.338, edge^3 p=0.130.

### B94. Nested model F test  ·  *No trend*
- **Formula / idea:** Nested F = [(SSE_r − SSE_f)/q] / [SSE_f/(n − p)].
- **Paper:** Chow, G. C. (1960). Tests of equality between sets of coefficients in two linear regressions. *Econometrica, 28*(3), 591-605. https://doi.org/10.2307/1910133 (JSTOR: https://www.jstor.org/stable/1910133)
  - *How they used it:* Derived the F test comparing a restricted model (one set of coefficients for both samples) with an unrestricted one (separate coefficients), the basis of the Chow structural-break test, illustrated with economic demand regressions.
- **Applied to the NHL model:** Nested F: adding back-to-back and favorite terms to edge: F=2.15, p=0.117.

### B95. AIC (and BIC)  ·  *Warning*
- **Formula / idea:** AIC = 2k − 2 log L; BIC = k log n − 2 log L; lower is better.
- **Paper:** Akaike, H. (1974). A new look at the statistical model identification. *IEEE Transactions on Automatic Control, 19*(6), 716-723. https://doi.org/10.1109/TAC.1974.1100705
  - *How they used it:* Introduced AIC = -2 log L + 2k as an estimate of expected predictive (Kullback-Leibler) discrepancy, and applied it to choosing the order of time-series (autoregressive / ARMA) models in place of sequential hypothesis tests.
- **Applied to the NHL model:** AIC/BIC (logistic, home win), 2024-26: opener only AIC 3271.3 BIC 3282.9; model only AIC 3256.2 BIC 3267.8; opener + model AIC 3257.6 BIC 3274.9. In these two seasons the model alone beats the opener (lower AIC) and adding the opener doesn't help.
- **2016-22 check:** 2016-22 team-only model: opener only AIC 9303.5; model only AIC 9356.6; opener + model AIC 9295.3 (opener beats the model alone; the combination is best)

### B96. Standardized coefficients / relative importance  ·  *Tool*
- **Formula / idea:** Standardized β = b·(s_x/s_y); ranks predictors on a common scale.
- **Paper:** Johnson, J. W., & LeBreton, J. M. (2004). History and use of relative importance indices in organizational research. *Organizational Research Methods, 7*(3), 238-257. https://doi.org/10.1177/1094428104266510
  - *How they used it:* Reviewed indices for apportioning R-squared among correlated predictors (standardized betas, structure coefficients, dominance analysis, relative weights) and showed that standardized betas mislead when predictors are correlated, as is common in organizational data.
- **Applied to the NHL model:** Standardized coefficients: edge +0.068, b2b_diff -0.042, fav_h -0.015.

### B97. Adjusted R squared  ·  *Tool*
- **Formula / idea:** Adjusted R² = 1 − (1 − R²)(n − 1)/(n − p − 1).
- **Paper:** Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics, 33*(1), 3-56. https://doi.org/10.1016/0304-405X(93)90023-5 (RePEc: https://econpapers.repec.org/RePEc:eee:jfinec:v:33:y:1993:i:1:p:3-56)
  - *How they used it:* Ran time-series regressions of 25 size/book-to-market portfolios on market, SMB and HML factors and reported degrees-of-freedom-adjusted R-squared. Adding SMB and HML raised it from the market-only level to above 0.9 for most portfolios, which was the paper's evidence that the factors add explanatory power.
- **Applied to the NHL model:** Adjusted R^2: edge only 0.0060; + b2b + favorite 0.0070.

### B98. Logistic regression (calibrated win probabilities)  ·  *Warning*  ⇄
- **Formula / idea:** Logistic: log[p/(1 − p)] = β0 + β1x; e^β1 = odds ratio per unit x.
- **Paper:** Lopez, M. J., & Matthews, G. J. (2015). Building an NCAA men's basketball predictive model and quantifying its success. *Journal of Quantitative Analysis in Sports, 11*(1), 5-12. https://doi.org/10.1515/jqas-2014-0058
  - *How they used it:* Fitted logistic regressions combining Las Vegas point spreads with possession-based efficiency ratings to give game-win probabilities for the 2014 NCAA tournament. The model ranked first by log loss among about 400 Kaggle entries, and simulations showed even the best model had only about a 12% chance of winning the contest.
- **Applied to the NHL model:** Logistic regression, home win on logit(opener) and logit(model): coefficients opener 0.170 (p=0.43), model 0.775 (p=7.89e-05). Implied weight on the model 82% (live blend uses 55%).
- **2016-22 check:** 2016-22 team-only model: opener 0.865, model 0.339 (p=0.00142); weight on model 28%
- **Carries over:** The weight a forecast deserves against the market depends on what private information it has (goalies here): measure it, don't assume it.


## NHL-specific rules (overs, rest)

### X01. Overs (the NHL totals rule)  ·  *Confirmed out of sample*
- **Formula / idea:** Overs-only totals rule: EV = P(over) x decimal odds + P(push) - 1 >= 6% at the opening total.
- **Applied to the NHL model:** Overs (live v1.1 rule, EV >= 6% at the open): 2024-26 198 bets, 54.0%, +6.1u (+3.1%); closing total rose after 35.9% of bets, fell 8.1% (all games: 16.5% / 15.5%).
- **2016-22 check:** 2016-22 overs 293 bets, 62.1%, +53.9u (+18.4%); total rose 32.8%, fell 3.1%

### X02. Rested team vs a back-to-back team (market-only rule)  ·  *Confirmed out of sample*
- **Formula / idea:** Bet the team NOT on a back-to-back when the other team is, at the opening moneyline. Uses no model, only the schedule.
- **Applied to the NHL model:** Market-only rule, back the rested team against a team on a back-to-back at the opening price: 2024-26 538 bets, +41.9u (+7.8%), won 59.7% vs price 53.5%. By season 2025: +12.7% (price move +0.023), 2026: +2.5% (price move +0.024).
- **2016-22 check:** 2016-22 holdout 1520 bets, +33.6u (+2.2%), won 57.7% vs price 54.2%; the close moved toward the rested team in 6 of 6 seasons. By season 2017: -6.1% (price move +0.010), 2018: +2.6% (price move +0.009), 2019: +1.7% (price move +0.010), 2020: -4.1% (price move +0.010), 2021: +22.9% (price move +0.016), 2022: +11.0% (price move +0.017)


## ANOVA and multiple comparisons

### B64. Familywise error / multiple testing  ·  *Tool*
- **Formula / idea:** Familywise error: P(≥ 1 false rejection) = 1 − (1 − α)^m for m independent tests.
- **Paper:** Harvey, C. R., Liu, Y., & Zhu, H. (2016). ... and the cross-section of expected returns. *The Review of Financial Studies, 29*(1), 5-68. https://doi.org/10.1093/rfs/hhv059
  - *How they used it:* Catalogued 316 published return "factors" and applied Bonferroni, Holm and BHY (FDR) adjustments. They argue a new factor today needs a t-statistic above about 3.0, not 2.0, and that many published factors are probably false discoveries.
- **Applied to the NHL model:** 41 hypothesis tests. Raw p<0.05: 17 (A03, A04, A07, A20, A27, A38, B51, B54, B59, B69, B73, B75, B76, B78, B81, B86, B98); ~2.1 expected by chance. After Benjamini-Hochberg: A03, A07, A20, A27, A38, B51, B54, B69, B73, B76, B78, B81, B98.

### B65. Bonferroni  ·  *Tool*
- **Formula / idea:** Bonferroni: test each at α/m.
- **Paper:** Dunn, O. J. (1961). Multiple comparisons among means. *Journal of the American Statistical Association, 56*(293), 52-64. https://www.jstor.org/stable/2282330
  - *How they used it:* Canonical source of the Bonferroni (Dunn) t-intervals for m pre-planned comparisons. Applied to two-way layouts, the t-intervals were shorter than Scheffe's whenever m was modest, but Tukey's were shorter for pure pairwise differences.
- **Applied to the NHL model:** Bonferroni (p < 0.0012): A07, A20, A27, A38, B54, B69, B73, B76, B78, B98.

## Adding a new concept
Same procedure as the NBA catalog: give it the next ID in both files, add a block to `run_nhl.py` (and `run_all.py` for the NBA), rerun so
the multiple-testing bar updates, and check anything that passes on the 2016-22 holdout before calling it real.
