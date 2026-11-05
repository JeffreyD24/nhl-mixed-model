# Pre-registration: rested team vs a back-to-back team, 2011-12 to 2015-16 (NHL)

Written Nov 5, 2026, BEFORE any 2011-16 outcome was looked at. Lead: catalog X02 (`research/stats_catalog/`).
Code: `dev/rest_b2b_test.py` (`run 2012 2016`). Data: `derived/oos_games.csv.gz` (no rebuild needed; RULE 4).
Season labels are END-year: 2012 = 2011-12 ... 2016 = 2015-16 (2010-11 has no odds).

## Claim being tested
Teams not on a back-to-back win more often than the no-vig CLOSING moneyline says when they play a team that is on one. Seen in
2016-22 (won 57.7% vs 55.4% no-vig close, n=1,520) and 2024-26 (59.7% vs 55.8%, n=538). The price moves toward the rested team
by the close (CLV about +1 point) but not enough to remove the gap. It came out of a catalog of ~98 checks, so it needs a clean test.
Validation (done before this file, on 2017-22 only): `dev/rest_b2b_test.py validate` reproduces 1,520 games, +33.6u at the open, and
the per-season ROIs of the catalog, so the b2b definition below matches the catalog.

## Fixed definitions
- b2b: the team played a game on the previous calendar day (from the full schedule in `oos_games`, odds or not).
- Eligible game: exactly one team on a b2b; trusted SBR row (`open_ml_ok`, `close_ml_ok`, `ml_move_ok` all 1); decided (home goals != away goals).
- Rested side = the team NOT on a b2b. win = 1 if it won the game (OT/SO counts). Price = SBR opening moneyline for that side.
- No-vig probability: two-way, 1/dec(a) normalized. q = at the open, qc = at the close.
- Seasons: END-year 2012 to 2016 (2011-12 .. 2015-16, including the 48-game 2012-13 lockout season).
- Expected n = 1,424 eligible games (counted before any outcome was read: 310 / 180 / 325 / 297 / 312 by season).

## Primary test (the only pass/fail test)
D = mean over eligible games of (win - qc), the rested team's actual win rate minus the no-vig closing chance.
- One-sided test of D > 0 (one-sample t on the per-game residuals), alpha = 0.05.
- **PASS:** D > 0 with one-sided p < 0.05 AND D > 0 in at least 3 of 5 seasons.
- **INCONCLUSIVE:** D > 0 but p >= 0.05 or fewer than 3 seasons positive.
- **FAIL:** D <= 0.
Power: SE about 0.0131. If the true gap is the 2016-22 size (+2.4 pts) power is about 57%; at half that (+1.2) about 23%; at the
2024-26 size (+3.9) about 91%. So an INCONCLUSIVE result is likely even if the effect is real; it is not evidence against it.

## Secondary (reported, not pass/fail)
win - open price (q); ROI at the opening price and units; price move to the rested team (qc - q) and in how many seasons it is positive;
split by rested side home/away; by-season table; pooled estimate of 2011-22 (11 seasons) as a descriptive number only.

## Rules for this test
- Run once, on exactly the definitions above. No changes to the definition, seasons or filters after seeing results. Any other cut
  (favorite/dog, month, goalie, rest days) is labeled exploratory, run after, and not used for the verdict.
- Not tested here: whether it is a bettable edge at the opener after the vig (needs thousands of bets; see the 80%-power note in the
  catalog). This test only asks whether the market, even at the close, misprices a b2b.
- No change to live rules or alerts follows from this test alone. The live TEST log (`state/rest_b2b_test.csv`, `alert.py` REST_TEST)
  keeps running as it is.
