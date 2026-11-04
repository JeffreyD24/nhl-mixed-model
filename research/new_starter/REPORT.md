# NHL new-starter tag (live record; no rule changed)

A game is tagged when an expected or alerted starting goalie has no regular-season start in the three previous seasons.
Background and backtests: betting-goals models/tests/NHL_NEW_STARTER_DK_RESULTS.md. Judge it by CLV first, then units, after a
few dozen tagged bets; it is a side record only.

Goalies with a start in 2024-2026 (END years): 132; matched to a name: 103. An expected goalie not matched counts as new, so unmatched veterans could be mis-tagged; check the names in state/new_starter_tags.csv.

| Bets | n | W-L | Units | ROI | CLV, win-% pts (n) |
|---|---|---|---|---|---|
| sent alert (goals, moneyline): NEW starter | 0 | | | | |
| sent alert (goals, moneyline): other | 19 | 8-11 | -0.93 | -4.9% | -4.07 (19) |
| sent alert (goals, puck line): NEW starter | 0 | | | | |
| sent alert (goals, puck line): other | 16 | 8-8 | -3.99 | -24.9% | -2.94 (15) |
| sent alert (goals, total): NEW starter | 0 | | | | |
| sent alert (goals, total): other | 2 | 0-2 | -2.00 | -100.0% | +0.89 (2) |
| sent alert (xg, moneyline): NEW starter | 0 | | | | |
| sent alert (xg, moneyline): other | 9 | 4-5 | -0.69 | -7.7% | +0.17 (9) |
| sent alert (xg, puck line): NEW starter | 0 | | | | |
| sent alert (xg, puck line): other | 9 | 5-4 | -0.57 | -6.4% | +0.84 (8) |
| sent alert (xg, total): NEW starter | 0 | | | | |
| sent alert (xg, total): other | 3 | 1-2 | -1.23 | -41.0% | -0.22 (3) |
| shot model side at the open, every game: NEW starter | 0 | | | | |
| shot model side at the open, every game: other | 203 | 90-113 | -28.48 | -14.0% | -1.26 (203) |
| shot model side at the open, every game: ACTUAL starter new (after the fact, descriptive) | 3 | 2-1 | +1.13 | +37.6% | -2.11 (3) |

The 'every game' rows are the model's side in every game, not the alert rule; they show direction, not a bettable record.

Tagged games so far (shot-model picks log): 0 of 218.

