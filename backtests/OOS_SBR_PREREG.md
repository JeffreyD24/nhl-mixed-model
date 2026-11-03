# NHL out-of-sample test on 2011-2022: pre-registration (written Nov 3, 2026, BEFORE any holdout result was run)

This file is committed before the holdout seasons are scored, so the rules below cannot be adjusted to fit them.
Git history is the proof: this commit comes before the results commit.

## Data
- Shot quality: hockeyR team-game xG (`data/external/hockeyr/team_game_xg_2010_2023.csv.gz`), regular season only.
- Lines and regulation scores: SportsbookReview NHL (`data/external/sbr/sbr_nhl_2011_2021_clean.csv.gz`), matched on date + teams.
  Regulation goals = sum of the three period scores from SBR.
- Season label = END year, as in the repo (2012 = 2011-12). 2010-11 has no SBR lines or period scores, so it is not used.

## Model (no tuning beyond what the live code already does)
- `nhl_xg_model.run` unchanged: chance-creation mixed model on xG, conversion model on goals − xG, REML, walk-forward,
  carry-over rho, half-life chosen on the last training season, logistic calibration on the last training season.
- Training window: the (up to) 4 seasons before each test season, as in `dev/backtest_xg.py`.
- One-day lag (`lag_days=1`): only results through two days before the game, like the live opener rule.
- Known differences from the live model: no goalie effects (hockeyR table has no starters), no missing-skater term,
  xG includes overtime shots, hockeyR's xG model instead of ours.
  So this tests the TEAM part of the shot model, which is a weaker model than the live one.

## Seasons
- Pipeline check (bugs only, nothing tuned): 2015, 2016.
- HOLDOUT: 2017, 2018, 2019, 2020, 2021, 2022 (6 seasons). Reported separately and as the headline.

## Rules scored (copied from the live system, alert.py, Nov 2-3, 2026)
1. **ML plain**: moneyline, model probability, EV ≥ 6% at the opening price (the v2 scorecard rule).
2. **ML blend (v3.1)**: p = 0.55 × model + 0.45 × no-vig opener, EV ≥ 4% at the opening price, no bet on a team on the
   second night of a back-to-back. (The live b2b/travel probability adjustments and the Pinnacle check are not reproducible here.)
3. **Overs**: totals, overs only, EV ≥ 6% at the opening price.
4. **Puck line, close only**: EV ≥ 6% at the closing puck-line price (SBR has no opening puck line; 2015+).
Each rule also graded at CLOSING prices (same probability, closing price) as a sanity check: we expect losses there.

## What gets reported
- Bets, win %, units (1 unit flat), ROI, and a 90% bootstrap interval (resample bets within each season, 2,000 draws),
  plus share of draws below zero.
- CLV: for each opening-price bet, EV of the opening price at the de-vigged CLOSING probability
  (p_close_fair × open decimal − 1). Positive average CLV = the bets beat the close.
- All rows vs trusted rows (`open_ml_ok`, `close_ml_ok`, `open_total_ok`, `close_total_ok` = 1).
- Calibration (model vs market Brier) per season.
- Agreement check between hockeyR xG and our own xG in the overlap seasons (2021-22, 2022-23).

## Decision rule (set now)
- The opening-price edge counts as confirmed out of sample only if ML blend or ML plain shows average CLV > 0 in the holdout
  AND its 90% ROI interval excludes zero. Positive ROI with an interval that crosses zero = "not disproven, not confirmed".
- Nothing in the live system changes because of this test without the user's approval.
