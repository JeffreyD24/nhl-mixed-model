# Pre-registration: NHL moneyline and puck line, re-graded with opener-time information (spreads plan step 1, NHL)

Written and pushed Nov 4, 2026, **before any result was computed** (the per-game predictions this test needs do not exist yet; they
are rebuilt by `research/spreads/step1_nhl_build.py` in the `step1-nhl-build.yml` workflow after this file is pushed).
Grading script: `research/spreads/step1_nhl.py` (pushed with this file; output `research/spreads/step1_nhl_output.txt`, per-bet rows
`research/spreads/step1_nhl_bets.csv`, findings `research/spreads/STEP1_NHL_RESULTS.md`). Same plan as the NBA step 1
(nba-mixed-model `research/spreads/STEP1_NBA_PREREG.md`).

## Question
What is the record of the live NHL moneyline and puck line rules at DraftKings' opener, 2021-22..2025-26, when the model uses only
what was known when the opener posted, measured first by closing-line value?

DK's NHL opener posts about 31 h before puck drop, i.e. before the previous night's games are played. The live model (and the rule
audit) uses a one-day lag: results, goalie usage and missed-game history through **two days before** the game. This test checks that
setting holds up (opener post times vs the previous night's games) and measures what the look-ahead would have been worth (lag 0).

These seasons were used to choose the live rules (ML_BLEND 0.55, ML EV 4%, PL EV 9%, prefer-ML, b2b rules), so this test **cannot
confirm** them. It can only show whether the record survives honest timing and whether it beats the close. The ML rule's only
out-of-sample evidence remains the SBR 2016-17..2021-22 holdout (team-only model, +1.2%/bet, CLV -1.2%: not confirmed); it is quoted
alongside, not re-run.

## Data
- Walk-forward shot-model predictions (`nhl_xg_model.run`, halflives (None, 60), trained on the 2-4 seasons before each test season,
  same splits as `analysis/rule_audit_nhl.py`), rebuilt from ESPN box scores and play-by-play, at lag 1 (PRIMARY) and lag 0 (check).
- DraftKings prices from `data/nhl_prices.csv.gz` (The Odds API history): `open_*` (first snapshot with a DK price, up to ~1 h after
  DK posts) and `close_*` (last snapshot before puck drop).
- Rest days and time-zone moves: `research/spreads/inputs/travel_nhl_games.csv` (copy of nba-mixed-model
  `analysis/travel_nhl_games.csv`; schedule-only, no timing issue).

## Rules graded (units: 1 unit per bet at the actual DK opener price; pushes impossible on ML/PL)
Moneyline chance = 0.55 x (shot model + travel adjustment: away b2b +0.0253, home b2b -0.0307, -0.0226 per time zone moved west by the
away team) + 0.45 x DK no-vig opener. Puck line chance = raw shot model (P win by 2+ / lose by at most 1).
| Version | Moneyline | Puck line | One bet per game (same team) |
|---|---|---|---|
| **v4 (live since Nov 4) — PRIMARY** | blend EV 4%+, b2b allowed | EV 9%+, skip team on 2nd night of b2b | moneyline when it qualifies |
| v3.1 (the record quoted before Nov 4) | blend EV 4%+, skip b2b | EV 6%+, skip b2b | higher EV (blended ML vs raw PL) |
Not replicated: v3.1's Pinnacle filters (need hourly Pinnacle snapshots; the rule audit measured the at-alert one at 27 bets -8.8u),
v4's moved-price ML alerts (EV 9%+) and in-game re-checks. Opener bets only.

## Rows
1. v4 moneyline, v4 puck line, v4 combined (PRIMARY, lag 1).
2. v3.1 moneyline, puck line, combined (lag 1).
3. Same rules at lag 0 (look-ahead check; difference = what the extra night of results was worth).
4. Breakdowns of v4 (lag 1): moneyline favorites / underdogs +100..+149 / +150 and longer; puck line favorite -1.5 / underdog +1.5;
   puck line 6-9% band (TEST rows live).
5. Opener timing: share of DK openers posted before 7 PM ET the day before the game (previous night's games not yet played) and
   share posted on game day.
6. Live 2026-27 so far from `state/alerts.csv` (descriptive only; too few graded bets to judge).

## Measures (goals.md order)
1. **CLV (primary):** expected return of the bet at DK's no-vig closing probability: `CLV = decimal price taken x p_close(no-vig) - 1`.
   Break-even is **0** (the vig is already in the price taken). Also reported: win-% points the no-vig probability moved toward the bet
   (open to close) and % of bets that beat the close. Puck line CLV only where the close has the same -1.5/+1.5 point (count reported).
   90% bootstrap interval (2,000 resamples of bets).
2. **Units (second check):** per season and total; units per 100 bets with 90% bootstrap interval; seasons negative out of 5.
3. **Accuracy (alongside):** win %; log loss and Brier of the home-win probability for the raw model, the blend, the DK no-vig opener and
   close, on the same games.

## Decision rule (fixed now), applied separately to v4 moneyline and v4 puck line, lag 1
- CLV > 0 and units > 0: the record survives honest timing; keep live (still "not disproved", not proven).
- CLV > 0 and units <= 0: keep; the model finds value the market later agrees with; losses are likely variance.
- CLV <= 0 and units > 0: the profit is not backed by the close (likely luck or price-shopping value that the close does not show);
  mark the market PROVISIONAL under the Nov 4 standing rule and review monthly with this season's CLV.
- CLV <= 0 and units <= 0: no edge at honest timing; recommend test-only.
- If the 90% CLV interval lies entirely above 0, say so: that is the strongest statement these seasons allow.
- Lag 0 vs lag 1: if lag 0 is better by more than 1 point of CLV, flag that a meaningful leak existed in any record graded at lag 0.
Nothing live changes without Jeffrey's approval; any change is a new version row in `state/bet_versions.csv`.
