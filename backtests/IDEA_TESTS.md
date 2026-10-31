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
