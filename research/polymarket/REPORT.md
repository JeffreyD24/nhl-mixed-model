# Polymarket US paper trades (NHL)

Updated 2026-11-02 10:02 ET by `polymarket.py --grade`. Nothing here was actually bet: these are the trades the model would have made on Polymarket US. 1 unit = $1 spent (price plus fee). Taker = bought at the best offer; maker = a limit bid at the highest price with 6%+ expected value, counted as filled if the best offer later fell to it before the game (approximate). CLV = the side's last mid price before the start minus the price paid, in cents (positive = the market moved toward us).

| model | market | kind | trades | W-L | units | ROI | avg EV at entry | avg CLV (cents) |
|---|---|---|---|---|---|---|---|---|
| goals | moneyline | taker | 2 | 2-0 | +2.56 | +128.1% | +11.9% | -0.50 |
| xg | moneyline | taker | 1 | 1-0 | +0.88 | +87.8% | +9.6% | +0.50 |

Same bet at DraftKings at the moment of the trade (same line): Polymarket was cheaper on 71% of 7 taker trades (average +0.6 cents per $1 contract in Polymarket's favor).

Waiting to be graded: 4. Open limit orders: 0.

Contracts or events the tracker couldn't read: 4 (see `research/polymarket/unmatched.csv`).
