# Polymarket US paper trades (NHL)

Updated 2026-11-05 10:02 ET by `polymarket.py --grade`. Nothing here was actually bet: these are the trades the model would have made on Polymarket US. 1 unit = $1 spent (price plus fee). Taker = bought at the best offer; maker = a limit bid at the highest price with 6%+ expected value. maker (strict) = the best offer later dropped below our price before the game, so we would have been filled; maker (touch only) = the offer only reached our price, so a fill is not certain (sellers may have traded with bids ahead of us); maker (old rule) = logged before Nov 4, 2026, when any touch counted. Judge limit orders on the strict rows. CLV = the side's last mid price before the start minus the price paid, in cents (positive = the market moved toward us).

| model | market | kind | trades | W-L | units | ROI | avg EV at entry | avg CLV (cents) |
|---|---|---|---|---|---|---|---|---|
| goals | moneyline | maker (old rule) | 1 | 0-1 | -1.00 | -100.0% | +7.5% | -2.50 |
| goals | moneyline | taker | 16 | 6-10 | -1.54 | -9.6% | +11.7% | -1.00 |
| xg | moneyline | maker (old rule) | 3 | 0-3 | -3.00 | -100.0% | +6.5% | -1.17 |
| xg | moneyline | taker | 12 | 8-4 | +4.47 | +37.2% | +9.8% | +0.42 |

Limit orders: 39 of 41 reached our price before the game. Since the stricter rule (Nov 4, 2026): 2 of 3 filled for certain (offer dropped below our price), 1 only touched it.

Same bet at DraftKings at the moment of the trade (same line): Polymarket was cheaper on 74% of 38 taker trades (average +0.4 cents per $1 contract in Polymarket's favor).

Waiting to be graded: 45. Open limit orders: 37.

## Order book depth (books saved in the last 7 days)

Contracts you could buy on the long side within 1 / 3 / 5 cents of the best offer, and the extra cost of buying 1,000 and 5,000 contracts by walking the book (median cents above the best offer). Split by when the book was seen: on the game's own date versus days ahead, since the early books are much thinner. Full levels are in `research/polymarket/book_YYYY-MM-DD.csv`.

| market | when | snapshots | within 1c | within 3c | within 5c | 1,000: extra cents | 5,000: extra cents | deep enough for 5,000 |
|---|---|---|---|---|---|---|---|---|
| moneyline | days ahead | 8520 | 151 | 328 | 642 | +8.8 | +39.7 | 98% |
| moneyline | game day | 657 | 107261 | 174749 | 191189 | +0.0 | +0.0 | 100% |

Contracts or events the tracker couldn't read: 23 (see `research/polymarket/unmatched.csv`).
