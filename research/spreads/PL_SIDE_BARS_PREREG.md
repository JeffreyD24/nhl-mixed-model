# Pre-registration: separate EV bars for -1.5 and +1.5 puck lines (Nov 5, 2026)

Written and pushed BEFORE any of the tests below was run (git history is the proof). Per CLAUDE.md RULE 2, this is tested now on
past seasons, not on 2026-27.

## Where the idea came from (in-sample)
`analysis/pl_ev_bands_output.txt` (2021-22..2025-26, DK openers, shot model, b2b removed): at EV 6-8% the +1.5 side was mildly
profitable (6-7% +9.3%, 7-8% +3.6%) while the -1.5 side lost clearly (6-7% -12.2%, 7-8% -8.7%). Live bar for both sides: 9%.
Hypothesis H: the +1.5 side deserves a lower EV bar than the -1.5 side.

## Tests

**T1. Leave-one-season-out on 2021-22..2025-26 at DK openers** (same predictions as `analysis/pl_ev_bands.py`).
For each held-out season: choose a bar from {4,5,6,7,8,9,10,11,12}% by maximum units on the other four seasons, (a) one bar for
both sides, (b) one bar per side chosen independently. Grade the held-out season with the chosen bar(s). Sum over the 5 folds.

**T2. Older seasons at SBR CLOSING puck lines** (the only puck line price SportsbookReview stores). Model: the shot model with
goalies (`dev/goalie_recal_test.py` variant G1: actual starter for training, expected starter for predictions, one-day lag),
seasons 2014-15..2020-21 (END-year labels 2015-2021; 2021-22 excluded because it is in the DK sample). Report by side and EV band
(4-6, 6-9, 9%+). Supporting evidence only: closing prices are not where we bet and every closing-price rule has lost.

**T3. Older seasons at an APPROXIMATE opening puck line price.** SBR has opening moneylines but no opening puck line, so the opening
puck line price is rebuilt from the opening moneyline: a mapping from the favorite's no-vig win chance to the -1.5 and +1.5
decimal prices, fit on DK openers 2021-26 (flexible fit: binned means or a low-order polynomial, chosen once, not tuned on results).
The favorite is taken to be the -1.5 side. Accuracy of the mapping is reported by applying it to SBR CLOSING moneylines and comparing
with SBR's real closing puck line prices. Same model, seasons and bands as T2. **Labeled approximate in every result.**

All tests: better-EV side per game, 1 unit per bet, graded at the price used, b2b (team on the 2nd night of a back-to-back) removed
where the data allows.

## Decision rule (fixed now)
H is **supported** only if ALL of:
1. T1: per-side bars beat the shared bar in total held-out units AND in at least 3 of 5 folds.
2. T3: +1.5 bets at EV 6-9% have positive total units AND positive units in at least 4 of 7 seasons, AND beat -1.5 bets at EV 6-9% in ROI.
3. T2 does not contradict it (+1.5 at 6-9% not worse than -1.5 at 6-9% at the close).

If supported: propose a lower +1.5 bar to Jeffrey (the value T1 picks most often); a change needs his approval and starts a new
version record. If not supported: drop the lead and record it as tested and rejected. Either way, results go in
`research/spreads/PL_SIDE_BARS_RESULTS.md` and nba-mixed-model `analysis/FINDINGS.md`.

Code: `analysis/pl_side_bars.py`. Output: `analysis/pl_side_bars_output.txt`.
