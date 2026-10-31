# Shot-based (xG) model: backtest results

Branch `shots-model`. Code: `build_shots.py` (ESPN play-by-play → shots), `nhl_xg_model.py` (xG + mixed models),
`dev/backtest_xg.py` (these backtests). Full numbers: `backtests/xg_backtests.json`.

**Model.** An expected-goals (xG) model, fit only on each backtest's training seasons, gives every unblocked shot a goal
chance from distance, angle, power play/shorthanded, rebound, shot type and score state. Then two mixed models on
regulation play: (a) xG created ~ home + back-to-backs + missing skaters + team offense + team defense; (b) goals minus xG
~ team finishing + goalie (goals allowed above expected). Expected goals = (a) + (b), then the same Poisson + overtime step.

**Moneyline accuracy (Brier, lower is better), model the day before vs. goals model:**
2022-23 0.2311 vs 0.2324 · 2023-24 0.2331 vs 0.2359 · 2024-25 0.2358 vs 0.2370 · 2025-26 0.2452 vs 0.2482.
Better every season; about level with DraftKings' opening prices (0.2361, 0.2452), still behind closing prices.

**Betting at EV ≥ 6%, 1 unit per bet (xG model / original goals model):**

| Season | Prices | Moneyline | Puck line | Totals (uncalibrated xG) |
|---|---|---|---|---|
| 2022-23 | close | +17.8 / −24.8 | −5.7 / −28.4 | +18.0 |
| 2023-24 | close | −17.1 / −26.2 | −21.0 / −21.4 | +17.1 |
| 2024-25 | open | **+30.1 / +16.2** | **+13.8 / +7.2** | +5.8 |
| 2024-25 | close | −34.0 / −14.2 | +6.1 / +5.4 | +25.3 |
| 2025-26 | open | **+45.2 / +23.1** | **+21.9 / +13.6** | +24.7 |
| 2025-26 | close | +13.4 / −31.1 | −14.8 / −30.6 | +2.3 |

**Caveats.** Totals were profitable only with the calibration step turned off, a choice made after seeing results, and
the model's totals probabilities are still no more accurate than the market's (log-loss 0.689-0.698 vs market 0.688-0.695).
The link between the model's disagreement with the line and the outcome is weak (correlation 0.01-0.07). Treat totals as
promising, not proven. Empty-net status was dropped from the xG model because ESPN only tags empty-net shots that score.
