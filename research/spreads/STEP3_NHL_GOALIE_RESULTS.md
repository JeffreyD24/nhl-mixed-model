# NHL step 3: confirmed starting goalies and lineups vs the DraftKings price on game day — results (Nov 4, 2026)

Pre-registration: `research/spreads/STEP3_NHL_GOALIE_PREREG.md` (pushed first, commit 1fc0e04). Script `research/spreads/step3_nhl_goalie.py`,
output `research/spreads/step3_nhl_goalie_output.txt`, bets `research/spreads/step3_nhl_goalie_bets.csv`. 6,549 games 2021-22..2025-26 with a DK
price 60-180 min before puck drop (median 64 min). "Pretip" model = shot model with the actual starting goalies and the actual missing skaters;
"opener model" = expected goalies (last-10 mix). Fix after the first run: a dtype error in section E (no effect on rows A-D).

## Main table (T60 = DK price ~1 h before puck drop; units at that price)
| Row | Bets | Win % | Units | Per 100 [90%] | CLV | Seasons negative |
|---|---|---|---|---|---|---|
| **A: ML, pretip model (PRIMARY)** | 1,330 | 52.0% | +58.2 | +4.4 [-0.5, +9.4] | -3.49% | 2/5 |
| A-open: ML, opener model, same price | 1,158 | 50.4% | +43.8 | +3.8 [-1.1, +9.1] | -3.75% | 2/5 |
| B: PL, pretip model, EV 9%+ | 827 | 48.1% | +78.5 | +9.5 [+2.9, +16.0] | -3.54% | 0/5 |
| B-open: PL, opener model | 652 | 43.3% | -5.4 | -0.8 [-8.2, +6.9] | -3.77% | 3/5 |

Information test (does the model add to the DK price at T60?): pretip w = **+0.45 [+0.30, +0.59]**; opener model w = +0.34 [+0.17, +0.50].
Log loss: DK at T60 0.6581, DK close 0.6579, pretip blend 0.6564, opener-model blend 0.6575.

## Verdict (pre-registered rule)
Row A: the information test is above 0 but CLV is not, so **no game-day betting tier**. Row E (opener bets whose own starter was a
surprise and the game-day re-check says no): ML 234 bets +33.8u, CLV +0.53%; PL 55 bets -1.8u. Not losing with negative CLV, so
**no game-day DON'T BET either.** Nothing live changes.

Two flaws in my own pre-registration, both confirmed by Fable:
- **CLV over 1-3 hours can't be positive here.** With so little time left the line barely moves, so CLV sits near minus the vig (-3.5%) by
  construction. Rule A was effectively impossible to pass; the information test is the meaningful measure.
- **The pretip model knows things that aren't public 1 h before puck drop.** Its skater lineup comes from who actually played (it differs from the
  opener model in 84% of games), and game-time scratches are announced at warmups, ~30 min out. Fable fit both models together: the price at T60
  has priced almost none of the pretip-minus-opener difference (w 0.79 [0.46, 1.12]), which is the signature of look-ahead, not of a slow market.
  The puck line gap (+78.5u vs -5.4u) is plausibly mostly look-ahead; it persists in goalie-only games (+9.3 vs -8.2 per 100) but on ~100 bets each.

## Exploratory (added after seeing results)
- "Surprise" as pre-registered (not the team's most-used recent goalie) covers 65% of games: NHL tandems are common, so it's not news. Strict
  surprise (a goalie with < 3 of the last 10 starts): 35% of games; pretip w +0.52 [+0.28, +0.76] vs opener +0.38.
- **Opener moneyline bets where our own goalie turned out to be a surprise have negative CLV** (all surprises: 503 bets, CLV -0.98%; strict:
  234 bets, CLV -1.22%), vs +1.02% / +0.56% when the expected goalie started. The market does move against us when our backup starts. Units are
  still positive (+61u / +18u), so this is a watch item, not a rule.

## Takeaways
1. **History can't answer the goalie question honestly**: we know who started, but not when it was public. The only clean test is live: log the
   moment each starter is confirmed (Bluesky / Daily Faceoff, already collected) and the DK price at that minute.
2. **Proposal (needs your OK, then a Fable check):** a TEST-only game-day re-check (logged, never pushed): when both starters are confirmed,
   re-run the shot model with them (opener's skater picture, so no lineup look-ahead) and log moneyline EV 4%+ / puck line EV 9%+ at DK's price
   that minute. Graded with CLV to the close. This mirrors the overs goalie test already running (`GOALIE_OVER_TEST`).
3. Opener bets stay as they are. Watch the CLV of opener moneylines whose own goalie is a surprise (about -1% so far).
4. Even the opener model has information the game-day price lacks (w +0.34): the blend's value isn't only at the opener.
