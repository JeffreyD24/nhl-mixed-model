# NHL goals model vs shot model on the same holdout: pre-registration (written Nov 3, 2026, ~8:15 PM ET, before any holdout season was run for the goals model)

Question: on the seasons where the shot model was just tested (`GOALIE_RECAL_PREREG.md`, results in `goalie_recal_output.txt`), does the live
**goals model** (`nhl_mixed_model.run`, regulation goals, the model that stopped alerting on Nov 1) do better, worse or the same?
Live background: its own bets lost -16.6u on 1,026 bets in 2025-26 and its long shots ran about 5 points high.

## Design (identical to the shot model's G1 test, nothing new chosen)
- Games, lines, trusted-row flags, goalie data (actual starter for training, expected starter at the open with a one-day lag), training window
  (up to 4 earlier seasons), pipeline seasons 2015-16, **HOLDOUT 2017-2022**: all as in GOALIE_RECAL_PREREG.md.
- Model: `nhl_mixed_model.run` unchanged (half-lives None/60/30/15, calibration on the last training season, `lag_days=1`). The only change:
  the all-zero missing-skater column is dropped from the REML fit and given coefficient 0, because the historical table has no missing-skater data.
- Code: `dev/goalie_recal_test.py ... predict GM`, `dev/goals_model_holdout.py`. G1 predictions are the ones already scored.

## Disclosure (written honestly before the holdout run)
- The pipeline seasons 2015-16 were run and printed for the goals model while checking the scoring code for bugs. They look like the live finding
  (goals model less accurate than the shot model; its own bets lose), but those seasons decide nothing and no rule below was chosen from them.
- The goals model's goalie spread came out 0.000 in 2015 and 0.107 in 2016 (live: 0.27-0.30). The historical table identifies goalies only weakly
  for this model. The test is run as built; if it is about 0 in a holdout season, the goals model has effectively no goalie effect that season.

## Rules (same as G1)
Moneyline plain (EV 6%+) and blend (0.55 model + 0.45 no-vig opener, EV 4%+, no back-to-back) at the opening price; overs EV 6%+ at the opening total. 1 unit.

## Decisions (set now)
1. **Accuracy**: goals model is more accurate only if its holdout log loss is below the shot model's.
2. **Goals better / worse than shot**: paired CLV difference (GM minus G1, blend rule and plain rule, trusted rows, 90% interval resampling game days):
   interval above 0 = goals better; below 0 = goals worse; otherwise not shown.
3. **Live finding check**: the bets the goals model makes that the shot model does not (blend rule) are "consistent with the live finding" if their ROI < 0.
4. A rule counts as a **confirmed edge** only if its CLV > 0 and its 90% ROI interval excludes 0 (as before).
5. Nothing live changes; anything tried after this commit is exploratory.
