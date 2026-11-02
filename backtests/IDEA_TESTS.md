# Testing the Oct 31 cold-stretch ideas on past seasons

`dev/idea_tests.py`; full tables in `idea_tests.csv`, `idea_tests_bands.csv`, `idea_tests_chosen.csv`,
`idea_tests_favorites_monitor.json`. All runs use the one-day information lag (as live). Rule: moneyline + puck line,
EV >= 6%, 1 unit per bet. Opening and halfway prices: 2024-25 and 2025-26. Closing prices: 2022-23 to 2025-26.

| Idea | Result | Verdict |
|---|---|---|
| Home ice and back-to-back effects updating during the season | The tuning on the last training season chose "don't update" in 7 of 8 fits (once a heavily damped update). Results identical to the current models. | No gain: these effects didn't drift enough within past seasons to help. Not adopted. |
| Calibration fit on two seasons instead of one | Accuracy change in the 5th decimal. Opening prices: shot +132.8 vs +119.0, goals +53.9 vs +72.0. Closing prices worse for both. | Mixed, no clear gain. Not adopted. |
| Goals model: skip underdogs at +150 or longer | Opening: +58.5u on 1,155 bets (+5.1%) vs +72.0u on 1,796 (+4.0%). Halfway: +19.4u (+1.8%) vs +5.4u (+0.3%). Closing: -35.5u vs -176.4u. | Helps the goals model, most at later prices (where alerts usually land). |
| Shot model: same filter | Opening: +69.4u vs +119.0u; halfway +8.9u vs +41.0u. | Hurts: the shot model's long shots are profitable (said 39.9%, won 38.3%, needed 34.6% at the open). Keep them. |
| Favorites-run monitor | Week-to-week correlation of favorites' wins above market expectation: -0.29 over 52 weeks. | Favorites' hot streaks don't carry over (if anything they reverse slightly). Useful context: the current run is not a reason to change anything. |

Goals model long shots (+150 or longer), all four seasons at closing prices: said 39.9%, won 30.4%, needed 34.4% (-141u on
1,126 bets). At opening prices: said 40.0%, won 35.3%, needed 34.4% (+13.5u on 641 bets). The goals model's win chances for
big underdogs are about 5 points too high; it only gets away with it at the opening price.

## Rush shots and pre-shot movement in the shot model (Nov 1, 2026) — not adopted yet
`dev/xg_v2_backtest.py`, results `backtests/xg_v2_backtest.csv`. New xG inputs from the previous play (ESPN play-by-play, re-downloaded
with previous-play fields): seconds since it, rush (within 4 s of a play in the neutral/defensive zone), puck speed between the two
locations, cross-ice (sides of the ice flipped within 3 s), after a faceoff / turnover / hit. Raw goal rates: rush shots 16.4% vs 6.9%;
shots within 1 s of the previous play 24%.
| Test season | xG log-loss V1 → V2 | Game Brier V1 → V2 | Team bets at open (EV 6%+) V1 → V2 |
|---|---|---|---|
| 2023 | 0.24196 → 0.24145 | 0.23109 → 0.23124 | no opening prices |
| 2024 | 0.23396 → 0.23466 | 0.23313 → 0.23323 | no opening prices |
| 2025 | 0.23442 → 0.23436 | 0.23577 → 0.23578 | +43.9u → +52.5u (620 bets) |
| 2026 | 0.24014 → 0.23808 | 0.24520 → 0.24510 | +67.2u → +71.6u (614 bets) |
Better shot-level accuracy in 3 of 4 seasons and +13u at opening prices, but game-level accuracy is unchanged, so most of the gain
is in which shots are dangerous, not who wins. Kept as `nhl_xg_model.V2 = False`; re-test at the next refit with shooter skill added.

## Shooter finishing skill (Nov 1, 2026) — not adopted
`dev/shooter_backtest.py`, results `backtests/shooter_backtest.csv`. Each shooter's goals vs xG in the training seasons, shrunk
((goals + 40) / (xG + 40), capped 0.6-1.6), multiplies his shots' xG in the test season.
| Version | xG log-loss 2025 / 2026 | Game Brier 2025 / 2026 | Team bets at open, units (2025+26) |
|---|---|---|---|
| current | 0.23442 / 0.24014 | 0.23577 / 0.24520 | +111.1 on 1,237 |
| shooter skill | 0.23395 / 0.23980 | 0.23567 / 0.24515 | +94.8 on 1,238 |
| rush+movement + shooter skill | 0.23390 / 0.23776 | 0.23572 / 0.24507 | +95.1 on 1,234 |
More accurate at every level, but less profitable: the market already prices who the good shooters are, so knowing it moves
our number toward the line rather than away from it. The edge is in what the market is slow on (goalies, injuries, timing), not
in general accuracy. Lesson for future tests: judge by profit at opening prices and by accuracy vs the opener, not accuracy alone.

## Holdout seasons 2021-22 to 2023-24 at real DraftKings prices (Nov 2, 2026)
`dev/dk_holdout.py`, table `backtests/dk_holdout.csv`. Shot model with live settings (one-day lag), trained only on earlier
seasons, graded at DraftKings prices from The Odds API history (data/nhl_prices.csv.gz): opener, +15/30/60 min, halfway, close.
Moneyline + puck line at EV 6%+:
| Season | Open | +60 min | Halfway | Close |
|---|---|---|---|---|
| 2021-22 | +52.2u (609 bets) | +57.4u | +48.4u | -1.3u |
| 2022-23 | +39.0u (971) | +38.6u | +12.0u | -11.1u |
| 2023-24 | +14.6u (588) | +10.5u | -5.3u | -16.3u |
Total at the open: +105.7u on 2,168 bets (+4.9%). With 2024-25 and 2025-26 (+111u on 1,237): five seasons in a row profitable
at the opening price, and the edge is gone by the close every season. Confirms the current rules (6% near the open, 9% once the
price moves). Totals at the open: +23.9u on 889 bets but -6.5u in 2021-22; still not alerted.

## Autopsy of wins and losses, both models, 2021-22 to 2025-26 at the opener (Nov 2, 2026)
`dev/autopsy_preds.py`, `dev/autopsy.py`, full output `backtests/autopsy_output.txt`. Moneyline + puck line, EV 6%+.
- Shot model (live): 3,463 bets, +224.6u (+6.5%), positive all five seasons (+52, +39, +15, +46, +73). Goals model (research):
  4,015 bets, -38.4u; lost 2021-22..2023-24, won 2024-25 and 2025-26. Confirms shot model only.
- **Betting a team on the second night of a back-to-back loses for both models, every season.** Shot model: 144 bets, said
  53.3%, won 36.1%, -40.1u (-4, -14, -4, -5, -12); worst on puck line underdogs (86 bets, won 23% vs said 44%, -33.0u). Goals
  model: 283 bets, -43.6u. Betting AGAINST a back-to-back team is fine (+89.4u). The model's back-to-back penalty is too small,
  most likely the tired team's backup goalie, which isn't known at the open.
- Shot model is profitable at every price band, both markets, home and away (away stronger: +164.6u vs +60.0u), every EV band.
- Price moving our way by the close: +235.5u; no move or against: about break-even (same as the DON'T BET logic).
- Games decided in OT/shootout: -89.1u (coin flips); not knowable before the game.

## Schedule/travel adjustment on the puck line (Nov 2, 2026) — not adopted
`dev/travel_puckline.py`. The moneyline adjustment (back-to-backs, westward travel; live since Nov 2) turned into an equal
expected-goals shift and applied to puck line bets at DraftKings openers, EV 6%+, weights fit leaving the season out:
current +49.4u (1,378 bets: +10.9, +31.8, -1.4, +7.2, +0.9) vs adjusted +43.4u (1,666 bets: +14.4, +32.6, -8.8, +11.4, -6.2).
Worse overall and in 2 of 5 seasons, so the adjustment stays moneyline-only (moneyline: +159.6u vs +96.1u).

## NHL totals rework (Nov 2, 2026)
`dev/totals_rework.py` (output `backtests/totals_rework_output.txt`). Shot model totals at DraftKings openers, EV 6%+, 2021-22..2025-26.
- Current (both sides): 1,597 bets +50.2u but 3 of 5 seasons negative (-6.5, -0.4, +30.7, -2.3, +28.6).
- Added pieces (each fit leaving the season out) did NOT help: league scoring drift +7.9u, shooting/goalie luck +32.5u,
  last-10 form +39.6u, schedule +32.8u, all together -37.2u.
- **The problem is the unders.** Overs: 515 bets, said 56.3%, won 56.9%, +57.6u (+11.2%), positive all five seasons
  (+10.6, +8.6, +6.5, +7.1, +24.8), every line (5.5 / 6 / 6.5). Unders: 1,082 bets, said 54.9%, won 48.5%, -7.5u. The model's
  total runs 0.13-0.40 goals low every season (Poisson from regulation xG misses empty-net goals and fat tails), so it
  overrates unders; when it still likes the over, it's right.
- Overs timing: open +57.6u, +15 min +55.6u, +60 min +60.7u, halfway +40.8u, close +14.5u (still positive).
- Pinnacle's first total agrees/same: 418 bets +46.4u (all five seasons positive); against: 96 bets +12.3u (mixed).

## Why the puck line was flat in 2023-24 (Nov 2, 2026)
Puck line bets at DraftKings openers (shot model, EV 6%+), 2021-22..2025-26, back-to-back bets removed (live rule):
1,264 bets +117.2u (+13.1, +41.5, -2.4, +20.1, +44.9).
- 2023-24 has no single cause: -1.5 and +1.5 bets, price bands and EV bands are all near zero that season. With ~250 bets a
  season at the expected ~9% return, a season's result has a spread of about +/-17u, so a flat season is ~1-in-10 noise.
- Bets on a team on a back-to-back: 136 bets -34.0u (already removed by the live rule).
- Overconfident zones (+1.5 when the model says 70%+, -1.5 when it says 50%+): +8.8u on 371; removing them doesn't fix 2023-24.
- Pinnacle's first moneyline agrees/same: 991 bets +88.7u, positive all five seasons (+2.2, +39.3, +8.3, +10.0, +28.9);
  disagrees: 273 bets +28.5u (2023-24 -10.7u). Not adopted for the puck line: the disagree bets still made money in 4 of 5 seasons.

## One bet per game, and games where only one market had value (Nov 2, 2026)
Shot model at DraftKings openers 2021-26, back-to-back bets removed. Live since Nov 2: one alert per game (the higher-value of
moneyline / puck line; 849 same-team games: +67.5u on 849 units, every season positive, vs +114.6u on 1,698 units betting both).
- Only one market showing value does better per unit: moneyline only 1,025 bets +8.9% (+91.5u); puck line only 414 bets +16.0%
  (+66.4u, positive all five seasons; -1.5 only: 312 bets +18.1%, all five positive). When both show value: moneyline +7.3%,
  puck line +6.0%.
- "Both" games are the model's strongest opinions, mostly on favorites, and that is where it runs hot: moneyline favorites in
  those games said 68.5%, won 64.0% (+3.9%). By win chance, the model is ~3-5 points too high above 60% but still profitable
  (65-70%: +21.0u, 70-75%: +6.0u, 75%+: +11.3u).
