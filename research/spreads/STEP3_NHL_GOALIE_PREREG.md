# Pre-registration: NHL step 3 — confirmed starting goalies and lineups vs the DraftKings price on game day

Written and pushed Nov 4, 2026, **before any result was computed**. Script: `research/spreads/step3_nhl_goalie.py`
(output `research/spreads/step3_nhl_goalie_output.txt`, per-bet rows `research/spreads/step3_nhl_goalie_bets.csv`, findings
`research/spreads/STEP3_NHL_GOALIE_RESULTS.md`). Plan: `research/SPREADS_HANDOFF_2026-11-04.md` step 3 ("NHL: confirmed starting goalie
before the line reacts (biggest measured gain)").

## Question
The opener model uses the *expected* goalies (mix of each team's last 10 starts) and missed-game history. On game day the actual
starter and lineup become known. Does the shot model re-run with the actual starters and lineup carry information the DraftKings
moneyline / puck line price at that moment does not have? And when the starter is a surprise (not the team's most likely starter),
does the price lag?

## Data
- Walk-forward shot-model predictions, lag 1, 2021-22..2025-26 (`research/spreads/nhl_holdout/dk_holdout_lag1_*.csv`, built by
  `step1_nhl_build.py`): `p_home_win`, `p_home_by2`, `p_away_by2` = **pretip** model (actual starters `home_goalie`/`away_goalie`,
  actual missing regulars); `*_open` = opener model (expected goalies `home_gmix`/`away_gmix`).
- DraftKings hourly snapshots (nba-mixed-model `data/odds_history/nhl/*.csv.gz`, The Odds API), moneyline and puck line.
- Travel table `research/spreads/inputs/travel_nhl_games.csv` (as in step 1).

## Timings
- **T60 (PRIMARY):** last DK snapshot taken 60-180 min before puck drop. Starters are normally confirmed by morning skate or warmups;
  a few late confirmations fall after T60, so this has a little look-ahead (acknowledged; cannot be measured historically).
- T180 (secondary, more look-ahead risk): last DK snapshot 180-360 min before puck drop.
- Close: last DK snapshot before puck drop (as in step 1).
Games without a DK snapshot in the window are dropped (count reported).

## Surprise starter
A team's starter is a **surprise** if the actual starter is not the goalie with the largest weight in that team's `gmix` (or gmix is
empty). A game is a surprise game if either team's starter is a surprise.

## Rules graded at T60 (1 unit at the DK price at T60)
| Row | Model | Rule |
|---|---|---|
| **A (PRIMARY)** | pretip | ML: 0.55 x (pretip p + travel adj.) + 0.45 x DK no-vig at T60, EV 4%+ (live v4 ML rule, re-run at T60) |
| A-open (control) | opener model | same rule, same T60 price: isolates what the actual starters/lineup add |
| B | pretip | PL: raw pretip, +/-1.5 only, EV 9%+, skip team on 2nd night of b2b (live v4.1 PL rule) |
| B-open (control) | opener model | same |
| C | pretip | Row A restricted to surprise games |
| D | pretip | Row A restricted to non-surprise games |
| E | — | **Opener bets with a surprise starter on our team:** the step-1 v4 ML and PL opener bets (`step1_nhl_bets.csv`, lag 1) split by whether our team's starter was a surprise, and by whether the pretip model at T60 still has EV 4%+ (ML) / 9%+ (PL) at the T60 price. Graded at the opener (the bet as placed) — tells whether a DON'T BET on a surprise starter would have helped unplaced opener bets. |
Same rows at T180 (secondary). Bootstrap 2,000 resamples of bets, 90% intervals.

## Measures (goals.md order)
1. **CLV (primary):** decimal price taken x DK no-vig close probability of the bet side - 1 (break-even 0); PL only where the close
   point equals the T60 point. CLV here covers only 1-3 hours of movement, so small values are expected.
2. **Units (second check):** per season, units per 100 with 90% interval, seasons negative out of 5.
3. **Accuracy / information:** home-win log loss of DK no-vig at T60, DK close, pretip blend at T60 and opener blend at T60, on all games
   and on surprise games. **Information test:** logistic fit of the home win on logit(DK T60) with offset, slope w on
   (logit(pretip p + travel) - logit(DK T60)); 90% bootstrap interval for w (resampling games). Same for the opener model.

## Decision rule (fixed now)
- Row A: CLV > 0 **and** w (pretip) 90% interval above 0 **and** units > 0 -> the confirmed-starter re-check is worth building as a live
  TEST tier (game-day re-check at the current price after starters are confirmed), then PROVISIONAL under the Nov 4 standing rule.
- w interval above 0 but CLV <= 0 or units <= 0 -> the model knows something the T60 price lacks but it doesn't pay at that price;
  no betting tier; keep as a DON'T BET input only if row E supports it.
- w interval includes 0 -> DK prices the starters by T60; no game-day goalie tier.
- Row E: if opener bets whose own starter was a surprise **and** whose T60 pretip EV is below the bar lose with negative CLV (<= 0)
  over 30+ bets, propose a game-day DON'T BET for unplaced opener bets in that case. Otherwise no change.
Nothing live changes without Jeffrey's approval and a Fable check; any change is a new row in `state/bet_versions.csv`.
