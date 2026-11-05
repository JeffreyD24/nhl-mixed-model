# Pre-registration: are -1.5 puck lines at EV 9%+ weaker than the DK record says? (Nov 5, 2026)

Written and pushed BEFORE the test below was run. Follows `PL_SIDE_BARS_RESULTS.md`, test T3: on approximate 2014-15..2020-21
openers, -1.5 bets at EV 9%+ lost (139 bets, -16.9u, -12.2%) while on DK openers 2021-26 they made +67.4u on 569 bets (+11.8%).
T3's rebuilt opening puck line price had ~3.2 implied-prob points of noise per game and a home/away bias (home side 1.5 pts too
expensive, away side 1.0 pt too cheap), so that result is not trusted yet. This test fixes the price rebuild and re-runs it.
Per CLAUDE.md RULE 2 it uses past seasons only.

## The fix: rebuild the opening puck line from SBR's own pricing
- Fit the moneyline -> puck line price mapping on **SBR's closing lines** (the only place SBR has both), not on DraftKings.
- Inputs: the favorite's no-vig win chance from the moneyline, and whether the favorite is the home team. Outputs: implied
  probability of the favorite at -1.5 and of the underdog at +1.5. Cubic polynomial in the favorite's chance, fit separately for
  home favorites and road favorites (4 fits). Rows: trusted closing lines (`close_ml_ok`, `ml_move_ok`), +/-1.5, -1.5 side = ML favorite.
- **Leave-one-season-out:** each season's opening prices are rebuilt with a mapping fit on the other six seasons' closes.
- Report the mapping's held-out error on closing lines (mean and sd, home and road side) next to T3's (+1.5/-1.0 mean, 3.2 sd).
- Apply to SBR's OPENING moneylines (`open_ml_ok`, `ml_move_ok`) to get the rebuilt opening puck line.

## Test (same model, seasons and bet rules as T3)
Goalie-aware shot model G1 predictions (`derived/gr_G1_pred_2015..2021`), seasons 2014-15..2020-21, better-EV side per game,
+/-1.5 only, team on the 2nd night of a back-to-back removed, 1 unit at the rebuilt price. Report both sides by EV band
(4-6, 6-9, 9-12, 12%+, 9%+) with per-season units, and a bootstrap 90% interval (2,000 resamples of game-days) for -1.5 at 9%+.

## Decision rule (fixed now), on -1.5 at EV 9%+
- **Lead confirmed** (the DK record overstates -1.5 at 9%+): ROI < 0 AND negative in at least 4 of 7 seasons.
  Then the next step is a proposal to Jeffrey (e.g. a higher bar or a TEST-only tier for -1.5), which needs its own test and approval.
- **Lead rejected** (DK record holds): ROI >= +3%.
- **Inconclusive**: anything else. Record it and stop; no live change.
No live rule changes from this test in any case. Results: `research/spreads/PL_FAV_9PLUS_RESULTS.md`, nba-mixed-model `analysis/FINDINGS.md`.

Code: `analysis/pl_fav_9plus.py`. Output: `analysis/pl_fav_9plus_output.txt`.
