# NHL holdout tests with goalies + underdog recalibration: pre-registration
Written Nov 3, 2026, 7:30 PM ET, BEFORE any of these variants was run on the holdout. Git history is the proof (this commit precedes the results).
Follows `backtests/OOS_SBR_PREREG.md` / `OOS_SBR_RESULTS.md` (team-only shot model, no goalies) and the Nov 3 morning plan:
(1) recalibrate win chances (the model overrates underdogs), (2) heavier market weight for underdogs than favorites.
Scope: the **shot model** only (the live NHL moneyline/overs rules use the shot model since Nov 2).

## Data (all already in the repo)
- Same game table as OOS_SBR: hockeyR team-game xG + SBR lines, `dev/oos_sbr_build.py` (unchanged), trusted-row flags unchanged
  (including the `ml_move_ok` swapped-price flag, now fixed in advance).
- **New: starting goalies** from `data/external/nhl_box/goalies_hockeyr_2010_2023.csv.gz` (starter = goalie on ice at the opening faceoff;
  99.96% agreement with the NHL's official flag).
  - Training rows use the actual starter (as the live model does for finished games).
  - **Opening-price predictions use the expected starter**, built exactly like `build_features.py` with `lag_days=1`: each goalie's
    share of the team's last 10 starts known two days before the game; the usual starter down-weighted (x0.1) on the second night of a
    back-to-back. The actual starter is NOT used for anything graded at the opener.
  - Confirmed-starter predictions are reported only at CLOSING prices (starters are announced after the opener).
- Still missing vs live: missing-skater term (zero), Pinnacle check, live b2b/travel adjustments.

## Seasons (unchanged)
Pipeline check 2015, 2016 (bugs only). HOLDOUT 2017-2022 (headline). Training = up to 4 seasons before each test season, one-day lag.

## Variants
- **G0** = no goalies (the existing OOS_SBR predictions, re-run here only to confirm the pipeline reproduces them).
- **G1** = with goalies (expected starter at the open). Same code, same rules.
Recalibration is applied on top of G1 (the closer copy of the live model). Each is fit only on seasons BEFORE the test season, using that
earlier season's own out-of-sample G1 predictions (2017 is fit on 2015-16; 2018 on 2015-17; ... expanding window). Never on closing prices.
- **R1 log-odds recalibration**: logit(p') = a + b·logit(p), fit by maximum likelihood on home-win outcomes.
- **R2 underdog market weight**: p' = w_k·model + (1 − w_k)·no-vig opener, with separate w for the side priced as underdog and as favorite
  (k = dog / fav, by the opening no-vig price; the other side gets 1 − p'), fit by log loss. Compared with R2s = one shared w
  (the live 55/45 idea, refit the same way).

## Rules scored (same as OOS_SBR)
1. ML plain: model (or R1) probability, EV >= 6% at the opening price.
2. ML blend: G1 with the live fixed 55/45 blend; and R2 / R2s with their fitted weights; EV >= 4% at the opening price, skip a team on the
   second night of a back-to-back.
3. Overs: EV >= 6% at the opening total price (rebuilt over price, as in OOS_SBR), G0 vs G1 only (recalibration is moneyline-only).
Trusted rows are the headline (as decided in OOS_SBR); all rows reported too.

## Measures
- Bets, win %, units, ROI, 90% bootstrap (resampling game days).
- **CLV (primary)**: for each opening-price bet, de-vigged closing win chance of the bet side minus de-vigged opening win chance
  (win-% points). Positive = the market moved toward the bet. (Pinnacle CLV does not exist before 2026.)
- Accuracy on every game: log loss and Brier of each variant vs the no-vig opener.
- Long-shot check: predicted vs actual win rate for bets priced +150 to +249.

## Decision rules (set now)
1. **Goalies help** if G1's ML-blend CLV is higher than G0's and the 90% bootstrap interval of the paired difference (same game days) excludes 0.
2. A recalibration (R1 vs G1 plain; R2 vs R2s) **improves** the model if its CLV is higher with the paired 90% interval excluding 0,
   AND its holdout log loss is lower. Higher ROI alone does not count.
3. Any opening-price rule counts as a **confirmed edge** only if its average CLV > 0 AND its 90% ROI interval excludes 0 (as in OOS_SBR).
4. Anything else = "not shown". No thresholds, weights or windows are changed after seeing the holdout. Anything tried after this
   commit is labeled exploratory.
5. Nothing live changes from this test without the user's approval; a change would go in as a new model version with its own record.
