# NHL out-of-sample test on 2014-15 .. 2021-22: results (Nov 3, 2026)

Pre-registration: `backtests/OOS_SBR_PREREG.md` (commit 65a260b, pushed before any holdout result).
Code: `dev/oos_sbr_build.py` (join), `dev/oos_sbr_backtest.py` (predict + score). Outputs: `backtests/oos_sbr_bets.csv` (every bet),
`backtests/oos_sbr_accuracy.csv`, `backtests/oos_sbr_join_report.txt`, `backtests/oos_xg_agreement.txt`.

## Bottom line
- **Moneyline: no confirmed edge.** On six seasons the model never saw, the moneyline rules made +1.0% (plain) and +1.2% (blend) per bet,
  with 90% intervals of about −2% to +5% and **negative CLV (−1.7% and −1.2%)**: the opener tended to move against our picks.
  By the pre-registered rule this is "not confirmed", and the negative CLV leans toward "no edge" for the team-only model.
- **Overs at the opener: the one real signal.** +16.5% per bet on 295 holdout bets (90% interval +8% to +24%), positive in all six seasons.
  More convincing than the ROI: after we would have bet, the closing total **rose 33.5% of the time and fell 2.8%**, versus 10.9% / 7.8%
  for all games. The market moved toward the model's over picks. Caveat: the over price is rebuilt (see data notes), so the exact ROI is uncertain.
- **Closing prices lose, as always** (moneyline −1.6% to −1.9%, puck line −1.5%).
- **The model is less accurate than the opener** in 5 of 6 holdout seasons (Brier 0.2408 vs 0.2384 in 2016-17, etc.); it beat the opener only in 2021-22.

## What was tested
The live shot model's own code (`nhl_xg_model.run`), fed hockeyR xG, trained on the 4 seasons before each test season, one-day lag,
walk-forward with no lookahead. It has **no goalie effects and no injuries** (the historical table has neither), so it is the team part of the
shot model only. The live system's biggest measured gain was the confirmed goalie, so the live model should do better than this.
Opening lines are SBR's consensus opener, not DraftKings'.

## Holdout 2017-2022 (2016-17 .. 2021-22), trusted rows (headline)
| Rule (from live alert.py) | Bets | Win % | Units | ROI | 90% ROI interval | Chance of loss | Avg CLV |
|---|---|---|---|---|---|---|---|
| ML plain, EV 6%+ @open | 2,853 | 45.9% | +29.9 | +1.0% | −2.3% to +4.6% | 32% | −1.7% |
| ML blend 55/45, EV 4%+ @open, skip b2b | 1,499 | 44.6% | +18.1 | +1.2% | −3.6% to +6.2% | 34% | −1.2% |
| Overs, EV 6%+ @open | 295 | 62.0% | +53.7 | +16.5% | +8.2% to +24.4% | 0% | −1.1%* |
| ML plain @close | 3,181 | 43.9% | −53.5 | −1.7% | −5.2% to +1.8% | 79% | |
| ML blend @close | 1,810 | 42.5% | −34.5 | −1.9% | −6.5% to +2.6% | 76% | |
| Overs @close | 250 | 57.2% | +30.6 | +11.3% | +1.8% to +20.2% | 3% | |
| Puck line @close | 2,147 | 49.6% | −32.7 | −1.5% | −5.2% to +2.2% | 74% | |

*Totals CLV in price terms uses rebuilt over prices and only same-line games; the line-movement test above is the better measure.

All rows (no swapped-side filter): ML plain +82.4u (+2.9%, −0.8% to +6.6%), ML blend +57.7u (+3.8%). The difference is 28 bets on rows
with swapped team prices (see data notes): they looked like +64% ROI longshots. **Use the trusted numbers.**

By season (trusted, units): ML plain 2.2, 3.7, 16.8, 11.8, −17.8, 13.2. ML blend −10.1, 5.3, 26.9, −8.8, −11.4, 16.1.
Overs 11.5, 7.3, 1.4, 9.8, 1.7, 24.7 (2021-22: 144 of the 295 bets, the year scoring jumped to 6.29 goals a game).

Pipeline check seasons 2015-16 (used only to find bugs): ML plain +4.6%, ML blend +11.1%, overs −2.5% (217 bets, totals still moved up
15% vs down 7%).

## Does a bigger edge win more? (holdout, ML plain, all rows)
EV 6-9%: +2.4%; 9-12%: +4.1%; 12-20%: −1.1%; 20%+: −0.7%. No. Same finding as the NBA (Oct 31): bet flat, and big model edges are
mostly model error. By price (trusted): favorites +2.2%, +100..+149 +2.8%, +150..+249 −3.9%: the long-shot weakness seen live in the goals
model shows up here in the shot model too.

## Accuracy (Brier on moneyline, lower is better)
| Season | Model | Opener | Close | 55/45 blend |
|---|---|---|---|---|
| 2017 | 0.2408 | 0.2384 | 0.2373 | 0.2389 |
| 2018 | 0.2399 | 0.2376 | 0.2377 | 0.2380 |
| 2019 | 0.2431 | 0.2409 | 0.2399 | 0.2410 |
| 2020 | 0.2441 | 0.2441 | 0.2432 | 0.2434 |
| 2021 | 0.2340 | 0.2320 | 0.2304 | 0.2325 |
| 2022 | 0.2267 | 0.2283 | 0.2252 | 0.2264 |
The blend is never better than the opener alone except 2022: the team-only model adds little to the opener's moneyline.

## Data notes (found during this test; also added to data/external/sbr/README.md)
1. **SBR's single total price is the UNDER price.** At 5.5, games posted at −121 or shorter went over 43.6%; at +106 or longer, 54.1%.
   The over price is not stored; rebuilt assuming the pair totals 104.8% implied (e.g. under −130 → over +110).
2. **SBR dates Jan-Mar 2021 games as 2020** (548 rows of its 2020-21 season). Shifted a year in the build.
3. **SBR finals include the shootout goal; hockeyR's goal counts do not.** 1,277 of 1,285 score disagreements were exactly that.
   SBR finals and SBR period scores (regulation) are used.
4. **54 moneyline rows have swapped team prices** in the opener or closer (e.g. VAN-BOS open −320/+250, close +100/−120). Flagged
   `ml_move_ok = 0` when the de-vigged win chance moves more than 10 points open-to-close (the 99th percentile of real moves is 7.8).
   This flag uses lines only, not results, but it was added **after** seeing the holdout, so both versions are reported.
5. hockeyR xG vs our xG in 2021-22 and 2022-23: correlation 0.77-0.78 per team-game, 0.89-0.95 per team-season. Close enough as a stand-in;
   never mixed in one model.
6. Matched 99.7% of 2011-12 .. 2021-22 regular-season games.

## Personal note and takeaways
- **The honest read on moneylines:** without goalie knowledge, the shot model's team ratings do not beat the opener. The positive ROI is within
  luck, and the CLV is negative. This does not disprove the live model (which adds confirmed goalies, the biggest measured gain), but it does
  say the edge, if any, is in the goalie/news part, not the team ratings. That matches the Oct 31 lesson: "the edge is in absorbing player
  news faster than the line."
- **Overs are the surprise and the best lead.** The live system already bets NHL totals as overs only (v1.1), chosen on 2021-26. This test is on
  different seasons and a different opener source and still says the same thing, and the market moved toward the picks. I'd treat overs as the
  NHL market most worth watching with real money at small stakes. Two cautions: half the holdout bets came from one high-scoring season, and
  the over price here is estimated.
- **Data bugs nearly fooled the test twice** (the under price and the swapped rows). Both would have produced exciting, wrong numbers. Any
  future use of the SBR files should start from the flags in this build.
- **Nothing in the live system was changed.** Suggested next steps (your call): (1) when the overs record reaches ~150 live bets, compare its
  CLV in goals (did the total rise?) with this test's 33.5% / 2.8%; (2) add the same "did the line move toward us" measure to the live overs
  record now, since it gives a read long before win/loss does.
