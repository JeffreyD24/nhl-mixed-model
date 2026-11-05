# NHL new-starter tag (live record; no rule changed)

A game is tagged when an expected or alerted starting goalie has no regular-season start in the three previous seasons.
Background and backtests: betting-goals models/tests/NHL_NEW_STARTER_DK_RESULTS.md. Judge it by CLV first, then units, after a
few dozen tagged bets; it is a side record only.

Goalies with a start in 2024-2026 (END years): 132; matched to a name: 103. An expected goalie not matched counts as new, so unmatched veterans could be mis-tagged; check the names in state/new_starter_tags.csv.

| Bets | n | W-L | Units | ROI | CLV, win-% pts (n) |
|---|---|---|---|---|---|
| sent alert (goals, moneyline): NEW starter | 0 | | | | |
| sent alert (goals, moneyline): other | 20 | 9-11 | +0.31 | +1.6% | -3.75 (20) |
| sent alert (goals, puck line): NEW starter | 0 | | | | |
| sent alert (goals, puck line): other | 16 | 8-8 | -3.99 | -24.9% | -2.94 (15) |
| sent alert (goals, total): NEW starter | 0 | | | | |
| sent alert (goals, total): other | 2 | 0-2 | -2.00 | -100.0% | +0.89 (2) |
| sent alert (xg, moneyline): NEW starter | 0 | | | | |
| sent alert (xg, moneyline): other | 10 | 5-5 | +0.55 | +5.5% | +0.40 (10) |
| sent alert (xg, puck line): NEW starter | 0 | | | | |
| sent alert (xg, puck line): other | 10 | 6-4 | +0.97 | +9.7% | +0.29 (9) |
| sent alert (xg, total): NEW starter | 0 | | | | |
| sent alert (xg, total): other | 3 | 1-2 | -1.23 | -41.0% | -0.22 (3) |
| shot model side at the open, every game: NEW starter | 0 | | | | |
| shot model side at the open, every game: other | 207 | 93-114 | -27.24 | -13.2% | -1.23 (207) |
| shot model side at the open, every game: ACTUAL starter new (after the fact, descriptive) | 3 | 2-1 | +1.13 | +37.6% | -2.11 (3) |

The 'every game' rows are the model's side in every game, not the alert rule; they show direction, not a bettable record.

Tagged games so far (shot-model picks log): 0 of 221.

