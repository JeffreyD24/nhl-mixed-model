# Cold-stretch review, Oct 31 2026 (216 games into 2026-27)

Season-only mixed models were fit on this season's games alone (in-sample, no carry-over from last season; variance
components from the training seasons because 216 games are too few to estimate them) and compared with the two live
models and the market. Files in this folder; rerun with `python dev/season_diagnostic.py .`.

## Where things stand
| | Rule bets (open, EV ≥ 6%, ML + PL) | Units | Avg closing line value | Moneyline Brier |
|---|---|---|---|---|
| Goals model | 68-96 | −29.0 | **−3.6%** | 0.2410 |
| Shot model | 63-75 | −13.7 | **+1.0%** | 0.2325 |
| DraftKings opening price | – | – | – | 0.2313 |

## What the season-only model shows

**1. Underdogs of +150 to +249 are where almost all the money went.**

| This season | Bets | Model said | Price needed | Won | Units |
|---|---|---|---|---|---|
| Goals model | 51 | 42.2% | 35.8% | 25.5% | −15.7 |
| Shot model | 43 | 40.4% | 35.4% | 25.6% | −12.3 |

Everything else combined: goals model −13.3u, shot model −1.4u (shot model's favorites −150 and shorter: 18-6, +2.5u).

**2. Favorites are beating the market this season.** At opening prices, favorites were expected to win 124.7 of 216
games and won 134 (z = 1.3). The 65–70% favorites won 16 of 19 (84%, market said 67%). Both models lean underdog
(goals 98 of 164 bets, shot 78 of 138), so a favorites run hits them directly. A z of 1.3 is within normal variation.

**3. The goals model overrates long-shot underdogs in every season, not just this one.** In the 2024-26 backtests its
+150..+249 bets won 35.1% when it said 40.4%: break-even (+4.6u on 610 bets) only because the market was slightly off too.
The shot model's were accurate (said 40.1%, won 39.2%, +57.4u). So:
- goals model: a structural bias (its win chances for big underdogs are too high), made worse by this season's favorites run;
- shot model: mostly the favorites run. Its closing line value is positive every week since Oct 5 (prices kept moving
  toward its bets), which is what bad luck, not a bad model, looks like.

**4. Team ratings are not the problem.** The live models' current team ratings are close to what this season's games
alone say. For the worst teams the goals model is even harsher than the season data (Vancouver −0.58 vs −0.36 goals per
game). Yet it kept betting them as underdogs: Chicago 1-12 (−11.3u), Vancouver 6-16 (−8.7u), Pittsburgh 1-9, Calgary
0-6, and against Vegas 1-13 (−12.2u). The issue is turning ratings into win chances for lopsided games, not stale ratings.

**5. Home ice is stronger this season, and both models lean away.** Home teams have won 57.4% (training seasons 53.7%;
124 wins vs 116.5 expected from opening prices, z = 1.0). The models bet away sides on 109 of 164 (goals) and 103 of 138
(shot) rule bets. In the backtests away bets were the profitable side (+74.8u goals, +93.7u shot), so this is a reversal
of a pattern the models have been exploiting. In goals terms the season-only home effect is +0.13 (models: +0.16), so
home teams are winning close games more than outscoring.

**6. Back-to-backs hurt more this season.** Season-only: a team on the second night scores 0.32 fewer goals (models use
0.19). Small sample, but worth watching.

**7. League-wide scoring is normal.** 6.34 goals per game (training 6.24), 6.19 xG per game (6.01), goals 98.6% of xG,
overtime 22.7% (22.2%). Goalies: the season-only goalie ratings agree closely with both models' current ratings.

## Ideas to test (on the backtests first, never mid-season rule changes)
1. **Goals model long-shot fix:** recalibrate its moneyline probabilities for big underdogs, or skip its bets at +150 and longer. Backtest evidence already points this way.
2. **In-season home-ice and back-to-back effects:** let these update during the season (the adaptive baseline idea, applied to home ice and fatigue), and check whether that would have helped in past seasons.
3. **Favorite/underdog run monitor:** track favorites' wins vs market expectation weekly; when they run hot, expect both models to cool. Purely a context indicator, not a bet signal.
4. **Keep judging the shot model by closing line value:** positive CLV while losing = likely variance; negative CLV (goals model) = a real problem.
