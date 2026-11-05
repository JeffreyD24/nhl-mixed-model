# Pre-registration: two follow-ups to the rested-vs-back-to-back result (NHL)

Written Nov 5, 2026, BEFORE either test was run. Parent: `backtests/REST_B2B_PREREG.md` and `REST_B2B_RESULTS.md` (rested team beat the
no-vig close by +2.7 pts in 2011-16; +2.3 in 2016-22; +3.9 in 2024-26). Code: `dev/rest_b2b_followups.py` (`run`). Data already saved in `derived/` (RULE 4):
`oos_games_g.csv.gz` (schedule, SBR lines, actual starting goalie ids) and `gr_G1_pred_{2015..2021}.csv.gz` (goalie-aware shot model G1,
walk-forward predictions with the opening win chance). Season labels are END-year (2012 = 2011-12).
Same eligible-game definition as the parent test: exactly one team on a back-to-back (played the previous calendar day, from the full
schedule), trusted SBR row, decided game. Rested side = the team NOT on the b2b. win - qc = rested team's result minus its no-vig close.

## Follow-up 1: is it just backup goalies?
Question: when the back-to-back team starts its regular goalie, does the rested team still beat the close?
- Seasons: 2012-2022 (2011-12 .. 2021-22), split into period A = 2012-2016 and period B = 2017-2022. Same seasons as the parent
  results, so this is a new split of seen games, not new data; the verdict is about the split, and is labeled as such.
- b2b team's goalie = the actual starter listed for that team in `oos_games_g` (hockeyR). Games with no goalie id are dropped and counted.
- Team's main starter = the goalie with the most starts for that team in that season (all games in the table, odds or not; ties by lower id).
  Group STARTER = the b2b team's goalie is its main starter; group BACKUP = anyone else. (The classification uses the whole season, so it is
  hindsight at the start of the season, but who actually played is known by puck drop and is in the closing price.)
- D_S = mean(win - qc) in STARTER games; D_B = same in BACKUP games.
- **Primary question (decides the verdict):** D_S > 0, one-sided t-test p < 0.05 pooled over 2012-22, AND D_S > 0 in both periods.
  - Yes -> "the gap is not only backup starts" (fatigue or something else that goes with a b2b).
  - No -> "not shown without backups": the gap could be mostly backup starts. This is NOT proof that backups cause it.
- Reported, not pass/fail: D_B and n by period, share of b2b games where the b2b team starts a backup, D_B - D_S with a 90% interval
  (Welch), ROI at the opening price per group.
- Sample sizes (from the dry run, no outcomes): 2,936 b2b games with a goalie id (8 dropped); STARTER 644 (A) + 596 (B) = 1,240; BACKUP 778 + 918 = 1,696;
  the b2b team starts a backup in 54.7% (A) and 60.6% (B) of these games.
- Power: with 1,240 STARTER games (SE about 0.014), if D_S is the same +2.5 pts as overall, power is about 57%; a half-size effect (+1.2) about 22%.
  So "not shown" is a likely result even if the gap is real.

## Follow-up 2: does the shot model already price it?
Question: given the opener and the goalie-aware shot model, does rest still predict who wins?
- Seasons: 2015-2021 (2014-15 .. 2020-21), all trusted decided games (not only b2b games), model G1 `p_home_win_open`
  (open-time information, the number the live model bets from). Probabilities clipped to [0.01, 0.99].
- Logistic regression: home win ~ logit(no-vig open) + logit(model p_home_win_open) + adv, adv = (away b2b) - (home b2b), in {-1, 0, +1}
  (+1 = the home team is the rested one).
- **Primary question (decides the verdict):** adv coefficient > 0 with one-sided p < 0.05.
  - Yes -> "the shot model does NOT already price it": rest adds information beyond the opener and the model.
  - No -> "priced by the model or not distinguishable".
- Reported, not pass/fail: the same regression with the no-vig CLOSE in place of the open; the adv coefficient with the opener only (reference,
  expected > 0); among eligible b2b games, the rested side's win rate minus the model's probability, minus the open, minus the close, and
  model minus open (does the model lean toward the rested team).
- Sample sizes (dry run, no outcomes): 8,142 trusted decided games in 2015-21, of which 1,814 have exactly one team on a b2b.
- Power note: an adv coefficient of about 0.10 (roughly +2.4 pts) has SE about 0.047, so about 70% power. A "no" is likely even if the model only partly prices it.

## Rules
- Each test is run once, on the definitions above. Any other cut (home/away, favorite/dog, month, rest days) is labeled exploratory, run after,
  and not used for a verdict. No live rules or alerts change from these tests alone.
- A "dry" run (`dev/rest_b2b_followups.py dry`) prints only sample sizes, to catch bugs before the run; it reads no outcomes into the output.
