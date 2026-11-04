# Polymarket US paper trades (NHL)

Updated 2026-11-04 10:00 ET by `polymarket.py --grade`. Nothing here was actually bet: these are the trades the model would have made on Polymarket US. 1 unit = $1 spent (price plus fee). Taker = bought at the best offer; maker = a limit bid at the highest price with 6%+ expected value, counted as filled if the best offer later fell to it before the game (approximate). CLV = the side's last mid price before the start minus the price paid, in cents (positive = the market moved toward us).

| model | market | kind | trades | W-L | units | ROI | avg EV at entry | avg CLV (cents) |
|---|---|---|---|---|---|---|---|---|
| goals | moneyline | taker | 14 | 6-8 | +0.46 | +3.3% | +11.4% | -0.93 |
| xg | moneyline | maker | 3 | 0-3 | -3.00 | -100.0% | +6.5% | -1.17 |
| xg | moneyline | taker | 10 | 6-4 | +2.65 | +26.5% | +10.0% | +0.20 |

Limit orders: 27 of 29 filled before the game.

Same bet at DraftKings at the moment of the trade (same line): Polymarket was cheaper on 68% of 28 taker trades (average +0.4 cents per $1 contract in Polymarket's favor).

Waiting to be graded: 28. Open limit orders: 17.

## Order book depth (last 3 days of saved books)

Contracts you could buy on the long side at the best offer plus 1 / 3 / 5 cents, and what it would cost to buy 1,000 contracts (about $300-700) by walking the book: average price above the best offer, in cents, and how often the book was deep enough. Full levels are in `research/polymarket/book_YYYY-MM-DD.csv`.

| market | snapshots | within 1c | within 3c | within 5c | 1,000 contracts: extra cents | deep enough for 1,000 |
|---|---|---|---|---|---|---|
| moneyline | 3082 | 5 | 120 | 135 | +36.8 | 100% |

Contracts or events the tracker couldn't read: 19 (see `research/polymarket/unmatched.csv`).
