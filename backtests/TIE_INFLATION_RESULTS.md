# Tie-inflated score matrix: results (Nov 4, 2026)

Pre-registration: `backtests/TIE_INFLATION_PREREG.md` (commit d548d7a, pushed before this was run). Code: `dev/tie_inflation_test.py`.
Full output: `backtests/tie_inflation_output.txt`.

## Bottom line: don't change the live matrix
- The undercount is real: regulation ties 21-25% every season vs ~16-17% from the independent-Poisson matrix. One parameter (w = 0.074,
  fit on 2014-16 only) fixes the tie rate in every holdout season (e.g. 2017: 23.4% observed, 17.6% current, 23.7% inflated).
- **But it doesn't improve any bet probability.** After the per-market recalibration the live code already does, the log-loss difference is
  0.00-0.04 per 1,000 games in every market, in both holdouts. No market meets the pre-registered "better" bar. Puck lines at DK openers
  2024-26 (EV 9%+): current +20.3u on 355 bets, inflated +15.7u on 357.
- **Why:** the recalibration step is already absorbing the shape error. Without it, inflating ties makes puck lines clearly worse
  (home -1.5: -5.2 per 1,000; away -1.5: -2.9), because real hockey has *both* more ties *and* more 2-goal margins (empty-net goals) than
  Poisson, at the expense of 1-goal regulation wins. Moving probability onto ties alone fixes one and worsens the other.

## Takeaway
The independent-Poisson grid is wrong in a known way, and the existing calibration layer is what keeps the bet probabilities right. Keep
the calibration step in any future model change. If the score model is ever rebuilt, it needs a late-game term that adds ties AND
empty-net 2-goal wins together (a bivariate or game-state model), not tie inflation alone. Not worth doing for betting now.
