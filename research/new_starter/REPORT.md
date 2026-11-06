# NHL new-starter tag (live record; no rule changed)

A game is tagged when an expected or alerted starting goalie has no regular-season start in the three previous seasons.
Background and backtests: betting-goals models/tests/NHL_NEW_STARTER_DK_RESULTS.md. Judge it by CLV first, then units, after a
few dozen tagged bets; it is a side record only.

Goalies with a start in 2024-2026 (END years): 132; matched to a name: 103. An expected goalie not matched counts as new, so unmatched veterans could be mis-tagged; check the names in state/new_starter_tags.csv.

| Bets | n | W-L | Units | ROI | CLV, win-% pts (n) |
|---|---|---|---|---|---|
| sent alert (goals, moneyline): NEW starter | 0 | | | | |
| sent alert (goals, moneyline): other | 21 | 10-11 | +2.26 | +10.8% | -3.52 (21) |
| sent alert (goals, puck line): NEW starter | 0 | | | | |
| sent alert (goals, puck line): other | 16 | 8-8 | -3.99 | -24.9% | -2.94 (15) |
| sent alert (goals, total): NEW starter | 0 | | | | |
| sent alert (goals, total): other | 3 | 1-2 | -1.05 | -34.9% | +1.50 (3) |
| sent alert (xg, moneyline): NEW starter | 0 | | | | |
| sent alert (xg, moneyline): other | 11 | 6-5 | +2.50 | +22.7% | +0.46 (11) |
| sent alert (xg, puck line): NEW starter | 0 | | | | |
| sent alert (xg, puck line): other | 12 | 7-5 | +1.47 | +12.2% | +0.86 (11) |
| sent alert (xg, total): NEW starter | 0 | | | | |
| sent alert (xg, total): other | 5 | 3-2 | +0.54 | +10.8% | +0.51 (4) |
| shot model side at the open, every game: NEW starter | 0 | | | | |
| shot model side at the open, every game: other | 218 | 97-121 | -29.12 | -13.4% | -1.41 (218) |
| shot model side at the open, every game: ACTUAL starter new (after the fact, descriptive) | 3 | 2-1 | +1.13 | +37.6% | -2.11 (3) |

The 'every game' rows are the model's side in every game, not the alert rule; they show direction, not a bettable record.

Tagged games so far (shot-model picks log): 0 of 233.

