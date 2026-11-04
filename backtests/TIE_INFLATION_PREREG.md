# Tie-inflated score matrix: pre-registration (written Nov 4, 2026, BEFORE any holdout result)

Why: the statistics catalog (research/stats_catalog/README.md, B73) found regulation ties happen 22.5-22.8% of the time, vs 16-17%
predicted by the independent-Poisson score matrix (`nhl_mixed_model.score_matrix`), in both 2016-22 and 2024-26.

## Model change being tested
M'(i,j) = (1 - w) * M(i,j) + w * T(i,j), where M is the current independent-Poisson matrix and T keeps only M's diagonal (ties),
rescaled to sum to 1. One parameter, w (Dixon-Coles idea: extra probability on draws). w > 0 raises the tie rate and takes the same share
from every non-tie score.

## Data and fitting (no peeking)
- Predictions: the pre-registered team-only shot model (`_tmp/oos_pred_<season>.csv` from dev/oos_sbr_backtest.py), lam_home_open / lam_away_open.
- **w is fit once, on the pipeline seasons 2014-15 and 2015-16 only** (labels 2015, 2016), by matching the average predicted tie rate to the
  observed regulation tie rate. It is then frozen.
- **Holdout A: 2016-17 .. 2021-22** (labels 2017-2022), SBR trusted rows. **Holdout B: 2024-25, 2025-26** (live shot model with goalies,
  DraftKings), using the same frozen w.
- Both versions (current and tie-inflated) get the same logistic recalibration the live code uses, fit on the previous season only
  (season s-1 predictions, `nhl_mixed_model.fit_calibration`), separately for each market.

## Markets and metric
- Puck line: P(home wins by 2+), P(away wins by 2+) in regulation-or-final terms as the live code (`home_by2`, `away_by2`).
- Totals: P(final total > 5.5) and P(final total > 6.5), final = regulation total + 1 if tied after regulation.
- Moneyline: P(home wins), ties split by h_ot.
- Metric: log loss on outcomes, paired per game (current minus inflated, positive = inflated better), 95% bootstrap interval by game date.

## Decision rule (set now)
- "Better" for a market = holdout A paired log-loss gain > 0 with the 95% interval excluding 0, AND gain > 0 in holdout B.
- Recommend the change for the live model only if puck line OR totals is "better" and the moneyline is not worse (interval excludes a loss).
- Betting results (puck line EV 9%+ at SBR close and DK open; overs EV 6%+ at the open) are reported as descriptive only.
- Nothing live changes without the user's approval; an adopted change starts a new NHL version record.
