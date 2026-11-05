# Results: -1.5 puck lines at EV 9%+ on 2014-15..2020-21, with a fixed price rebuild (Nov 5, 2026)

Pre-registration: `research/spreads/PL_FAV_9PLUS_PREREG.md` (commit e0107b5, pushed before the run).
Code: `analysis/pl_fav_9plus.py`. Full output: `analysis/pl_fav_9plus_output.txt`. Predictions: `derived/gr_G1_pred_2015..2021`.

## Verdict by the pre-registered rule: LEAD CONFIRMED. No live change (the prereg allows none).

-1.5 at EV 9%+: **654 bets, -6.6u, ROI -1.0%** (90% interval -9.8% to +7.9%), negative in 5 of 7 seasons.
Same rule on DK openers 2021-26: 569 bets, +67.4u, +11.8%.

## The price rebuild is now much better
Fitting the moneyline -> puck line mapping on SBR's own closing lines (home and road favorites separately, each season fit on the
other six) removed the bias and cut the noise by a third. Held-out error vs SBR's real closing puck lines:

| Mapping | Home side mean / sd | Road side mean / sd |
|---|---|---|
| T3 (fit on DK openers) | +1.47 / 3.26 pts | -1.01 / 3.23 pts |
| This test (fit on SBR closes, leave-one-season-out) | **+0.02 / 2.16 pts** | **-0.03 / 2.14 pts** |

The remaining 2.1 pts of noise is still about the width of one EV band, and SBR's opener is a consensus number, not DraftKings'.

## All bands, rebuilt openers 2014-15..2020-21

| | -1.5 | +1.5 |
|---|---|---|
| EV 4-6% | 267 bets +8.5% | 507 bets -0.1% |
| EV 6-9% | 314 bets +5.8% | 501 bets +4.0% |
| EV 9-12% | 238 bets -7.3% | 277 bets -0.2% |
| EV 12%+ | 416 bets +2.6% | 249 bets +2.7% |
| EV 9%+ | 654 bets -1.0% | 526 bets +1.2% |

## What it means (and how sure we are)
- **The DK record for -1.5 at 9%+ (+11.8%) looks too good to expect going forward.** On seven seasons it never saw, the same rule
  was about break-even. Pooling both eras: 1,223 bets, +60.8u, **+5.0%**: still profitable, but less than half the DK number.
- **It is not evidence that -1.5 at 9%+ loses.** The interval runs from -9.8% to +7.9%.
- [CORRELATION] **Model EV does not sort puck line profit reliably.** In the older seasons -1.5 at 4-9% made money and 9-12% lost;
  on DK seasons it was the reverse. No EV ordering repeats across the two eras, for either side. Any puck line bar chosen by EV
  band (9% included) is fitting noise more than signal. This is a correlation finding, not a cause.
- The +1.5 side is roughly break-even to slightly positive at every band in the older seasons, as before.

## Next steps (proposals for Jeffrey; nothing changes live without approval)
- [LEAD] Test whether the model's puck line EV predicts profit at all, using the pooled 12 seasons and a pre-registered test
  (e.g. slope of profit on EV, leave-one-season-out). If it doesn't, the puck line bar should come from something else (price
  range, side, goalie certainty) or the puck line should become TEST-only.
- [IDEA] Expect about +5% on -1.5 at 9%+ when sizing or judging live results, not +11.8%.
