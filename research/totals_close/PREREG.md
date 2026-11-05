# Pre-registration: does the NHL shot model still beat DraftKings' CLOSING total price? (Nov 5, 2026)

Written and pushed before any result is computed. Source of the question: betting-goals daily/2026-11-04.md, explore #1
(SBR 2017-22 absorption test, points only: the team/shot part of the model total is ~45% absorbed by the close and still
predicts results vs the close, +0.43 se 0.055). Yesterday's NHL totals research (analysis/nhl_totals_research_output.txt)
already graded the bet rule at every bet time on DK 2021-26 (close: 434 bets +5.3u, 3/5 seasons negative) and fit the
model's weight against DK's OPENING price (0.48, se 0.13). The one number not yet measured is the weight against DK's
CLOSING price. That is this test.

Data: research/spreads/nhl_holdout/dk_holdout_lag1_{2022..2026}.csv (walk-forward shot model, one-day information lag, as
live; DK totals and prices at open and close from the hourly snapshots). Model over chance at a line: nhl_mixed_model.over_prob
with lam_home_open, lam_away_open (the model as it stood at the open; no later information enters the model).

Test: logistic, decided games (pushes dropped), over at DK's closing line ~ offset(logit DK no-vig close) +
w x (logit model over chance at the closing line - logit DK no-vig close). Same fit at DK's opening line for comparison.
- Report w (se) at the open and at the close: train seasons 2021-22..2023-24, test seasons 2024-25 and 2025-26 pooled,
  and per season.
- **Pass** if, on the test seasons pooled, the close weight's 90% interval is above 0.
- Pass means "part of the model's information survives DK's close" (supports a late/game-day re-price rule being worth a
  side-by-side record). It is not a bet rule; no live rule or threshold changes from this test.
- Sanity check: the open weight on all five seasons pooled should be close to yesterday's 0.48.

Leakage: the model uses only the opener-time inputs; DK's closing price is the market's, never fed to the model. Seasons are
walk-forward predictions; the weights are reported per season, with no tuning.
