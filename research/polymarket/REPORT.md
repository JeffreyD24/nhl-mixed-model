# Polymarket US paper trades (NHL)

Updated 2026-11-04 18:18 ET by `polymarket.py --grade`. Nothing here was actually bet: these are the trades the model would have made on Polymarket US. 1 unit = $1 spent (price plus fee). Taker = bought at the best offer; maker = a limit bid at the highest price with 6%+ expected value. maker (strict) = the best offer later dropped below our price before the game, so we would have been filled; maker (touch only) = the offer only reached our price, so a fill is not certain (sellers may have traded with bids ahead of us); maker (old rule) = logged before Nov 4, 2026, when any touch counted. Judge limit orders on the strict rows. CLV = the side's last mid price before the start minus the price paid, in cents (positive = the market moved toward us).

| model | market | kind | trades | W-L | units | ROI | avg EV at entry | avg CLV (cents) |
|---|---|---|---|---|---|---|---|---|
| goals | moneyline | taker | 14 | 6-8 | +0.46 | +3.3% | +11.4% | -0.93 |
| xg | moneyline | maker (old rule) | 3 | 0-3 | -3.00 | -100.0% | +6.5% | -1.17 |
| xg | moneyline | taker | 10 | 6-4 | +2.65 | +26.5% | +10.0% | +0.20 |

Limit orders: 31 of 33 reached our price before the game. Since the stricter rule (Nov 4, 2026): 0 of 0 filled for certain (offer dropped below our price), 0 only touched it.

Same bet at DraftKings at the moment of the trade (same line): Polymarket was cheaper on 72% of 32 taker trades (average +0.4 cents per $1 contract in Polymarket's favor).

Waiting to be graded: 36. Open limit orders: 28.

## Order book depth (books saved in the last 7 days)

Contracts you could buy on the long side within 1 / 3 / 5 cents of the best offer, and the extra cost of buying 1,000 and 5,000 contracts by walking the book (median cents above the best offer). Split by when the book was seen: on the game's own date versus days ahead, since the early books are much thinner. Full levels are in `research/polymarket/book_YYYY-MM-DD.csv`.

| market | when | snapshots | within 1c | within 3c | within 5c | 1,000: extra cents | 5,000: extra cents | deep enough for 5,000 |
|---|---|---|---|---|---|---|---|---|
| moneyline | days ahead | 6884 | 154 | 343 | 656 | +9.5 | +40.3 | 100% |
| moneyline | game day | 271 | 165841 | 300472 | 318840 | +0.0 | +0.0 | 100% |

Contracts or events the tracker couldn't read: 19 (see `research/polymarket/unmatched.csv`).
