# NHL mixed-model tracker

Two mixed models (a goals model and a shot-based expected-goals model) run side by side. The original (team offense, team defense and **goalie** random effects, home ice, back-to-backs, and missing regular
skaters) that predicts NHL moneylines, puck lines and totals, runs itself on GitHub every day, and sends phone alerts
when it disagrees with the posted price. It is the NHL version of
[nba-mixed-model](https://github.com/JeffreyD24/nba-mixed-model): same machinery, same daily schedule, same alerts,
bet log, research database and workbook, adapted to hockey.

## Two models, side by side

Two models run every day, keep separate locked picks and both send phone alerts. Each alert is labeled **[Shot model]**,
**[Goals model]** or **[Both models]** (one alert when they want the same bet), and each model's alerts and picks are graded
separately, so the season shows which one actually wins. The **Models** sheet of `NHL_Live_Tracker.xlsx` and
`state/leaderboard.json` hold the side-by-side scorecard.

| | Goals model (`nhl_mixed_model.py`) | Shot model (`nhl_xg_model.py`) |
|---|---|---|
| Learns from | goals | expected goals (xG): every shot's chance of scoring from its distance, angle, power play, rebound, shot type and score state |
| Random effects | team offense, team defense, starting goalie | team chance creation, team chance prevention, team finishing, goalie goals saved above expected |
| Locked picks | `state/picks_log.csv` | `state/picks_log_xg.csv` |
| Backtest, opening prices, EV ≥ 6%, ML + puck line (2024-25 and 2025-26) | +60.1 units on 1,779 bets (+3.4%) | **+111.0 units on 1,237 bets (+9.0%)** |
| Moneyline accuracy (Brier, 4 backtest seasons) | 0.2324 / 0.2359 / 0.2370 / 0.2482 | **0.2311 / 0.2331 / 0.2358 / 0.2452** |

Full shot-model backtests: `backtests/XG_MODEL.md`. Shot data comes from ESPN's play-by-play (`build_shots.py`); the xG
coefficients are fit once on 2021-22..2025-26 (`make_xg_inputs.py` → `data/xg_model.json`), and each run adds the new
games' shots to `state/shots_2026_27.csv`.

## What's different from the NBA version, and why

| | NBA | NHL |
|---|---|---|
| Response | points | **regulation goals** (periods 1-3); overtime is modeled separately |
| Random effects | team offense, team defense | team offense, team defense, **starting goalie** (the biggest single-player effect in hockey) |
| Player absences | official NBA injury report PDFs × player EPM | no official report exists. **Open** (day before): regulars who missed the team's last game. **Pre-game**: the actual lineup (backtests) or ESPN's injury list (live). Player value = expected ice time × last season's points per 60 above replacement. |
| Goalie | – | **Open**: each goalie's share of the last 10 starts, with yesterday's starter down-weighted on back-to-backs (same goalie starts both nights only 14% of the time). **Live**: ESPN's probable/confirmed starter. |
| From model to bet | points vs. the spread | expected goals → Poisson score distribution + overtime (home wins OT/SO ~52%) → win %, win by 2+, final-total distribution → **calibrated** (empty-net goals make 2-goal margins more common than Poisson says) |
| Markets | spread, total | **moneyline, puck line** (±1.5 at varying prices), total |
| Edge | 3+ points from the line | **expected value ≥ 6%** at the posted price: model win % × decimal odds − 1 |
| Safeguards | no current injury report; team hasn't filed; line moved 3+ against | **starting goalies not both confirmed**; moneyline moved 5+ win-% points against the bet |

## What runs, and when

| Workflow | Schedule | What it does |
|---|---|---|
| **Evening model run** (`evening.yml`) | Daily, 9:33 PM EST / 10:33 PM EDT | Refits the model on 2021-22 to 2025-26, walks forward through 2026-27 with no lookahead, and **locks** predictions for the **next day's** games using what's known the day before (likely goalie, skaters who missed the last game). That's the same setup the opening-line backtests used, and it happens before most opening lines are posted. Locked picks are never changed. |
| **Morning run** (`morning.yml`) | Daily, 11:41 AM EDT / 10:41 AM EST | Adds last night's results and box scores, grades finished games, alerts and your bets, saves today's model for the line checks, and rebuilds `NHL_Live_Tracker.xlsx`. |
| **Line check and phone alerts** (`alerts.yml`) | All day, every 5 minutes | Each run checks every 5 minutes for about 50 minutes by itself (`alert_loop.sh`, because GitHub starts frequent jobs 30–60 minutes apart). Each check covers today's and tomorrow's games: pulls ESPN's probable/confirmed goalies, ESPN's injury list and the current DraftKings prices, re-predicts without refitting, and sends one ntfy push per game and market when the expected value is **6%+**. |

All three can also be started by hand from the **Actions** tab (**Run workflow**).

## How picks are tracked

**The scorecard:** every **moneyline and puck line** side where the locked model's expected value at the **opening
DraftKings price** is **6% or more** counts as a 1-unit bet at that price, even if the price moved before a bet could be
placed. That measures the model itself, not your timing. It's the highlighted rule on the **Summary** sheet. Totals
are tracked on the Summary sheet but are **not** in the rule: they lost money against opening lines in both backtest seasons.

## Backtests (walk-forward, no lookahead)

Model trained on the earlier seasons, then walked through the test season one day at a time. Opening lines exist for
2024-25 and 2025-26 only (Action Network's history); closing lines go back to 2021-22. 1 unit risked per bet, graded at
the actual price. Full tables in `backtests/`.

| Test season | Model (day before) vs **opening** prices, EV ≥ 6% | vs **closing** prices, EV ≥ 6% |
|---|---|---|
| 2022-23 | – | ML −24.8u, PL −28.4u, totals −27.2u |
| 2023-24 | – | ML −26.2u, PL −21.4u, totals +10.6u |
| 2024-25 | **ML 241-276, +16.2u (+3.1%)**; **PL 205-205, +7.2u (+1.8%)**; totals −32.4u | ML −14.3u, PL +5.4u, totals +6.1u |
| 2025-26 | **ML 240-249, +23.1u (+4.7%)**; **PL 176-187, +13.6u (+3.7%)**; totals −16.7u | ML −31.1u, PL −30.6u, totals −20.8u |

- The model's win probabilities are **less accurate than the market's** every season (Brier score 0.237 vs. 0.236 at the
  open and 0.233 at the close in 2024-25). Like the NBA model, its only profit came against **opening** prices.
- With the confirmed goalie and actual lineup, the model did much better against opening prices (ML +41.6u and +49.3u),
  but not against closing prices, which already know the goalie. That is why the alerts watch for goalie news: the edge,
  if any, is in prices that haven't caught up yet.
- The 6% threshold and the decision to leave totals out were chosen after seeing both opening-line seasons, so the
  backtest numbers above flatter the rule somewhat. The live season is the real test.
- **Totals, checked further (Oct 30):** the 2025-26 backtest bet 221 unders and 7 overs, so I tested two fixes on every
  backtest season: letting the scoring baseline update during the season, and changing how the total probabilities are
  calibrated (one shared correction, one per line, or none). None of them gave the model real information about totals.
  Its log-loss against the over/under outcome was 0.690-0.699 in every version, about a coin flip (0.693) and worse than
  the market's own prices (0.688 at the open). Which way it leaned, and whether it made or lost money, depended only on the
  calibration choice. That's noise, not an edge, so totals stay out of the rule and the alerts. Results:
  `backtests/totals_variants.csv`; code on the `totals-fix` branch (not merged).

## Alerts

- **What an alert says:** the bet and price, the model's win chance vs. the chance the price needs, the expected value
  (and what it was at the opening price), the model's expected score, the goalies (expected / confirmed / not announced),
  which regulars the model has as missing, the moneyline or total history with times, and the latest injury news.
- **Rule:** moneyline and puck line, expected value 6%+ at the current DraftKings price. One alert per game per market.
  Settings at the top of `alert.py`: `THRESHOLD`, `ALERT_MARKETS` (add `"total"` to get totals alerts), `MAX_MOVE`, `WINDOW`.
- **Caution alerts.** Sent with **CAUTION** in the title, at normal priority, when the edge is there but:
  - the starting goalies aren't both **confirmed** yet (ESPN lists them as "expected" for most of the day), or
  - the moneyline has moved 5+ win-% points **against** the bet since it opened (the market knows something).

  If a caution clears later (goalies confirmed, edge still there), a regular alert follows.
- **"Market agrees" alerts.** When the moneyline moves 5+ win-% points toward the model's side, you get a low-priority
  heads-up once per game and market (`state/market_moves.csv`).
- **Line history and line jumps.** Every 5-minute check records each price change with the time first seen
  (`state/line_history.csv`). Moneyline moves of **3+ win-% points within 60 minutes** and any change in the total are
  logged in `state/line_jumps.csv` with the news around them; moves of **5+ points** (or a full goal on a total) send a
  **Line jump** notification. The morning run grades each jump.
- Every alert goes into `state/alerts.csv` and the **Alerts** sheet, and is graded at its price after the game, with
  closing line value. Phone delivery uses [ntfy](https://ntfy.sh); the topic is the repository secret `NTFY_TOPIC`.

## Logging the bets you actually place

- **From an alert:** tap **Log this bet**. It opens the form with the game, market, pick, line and price filled in. Fix
  anything that differs, add your stake, and submit.
- **Any other bet:** [Log a bet](https://github.com/JeffreyD24/nhl-mixed-model/issues/new?template=log-bet.yml), or
  **Issues → New issue → Log a bet**. Markets: `moneyline`, `puck line`, `total`.
- A workflow adds it to `state/my_bets.csv`, replies, and closes the issue. Only bets you open are recorded.
- The morning run grades each bet at **your** price and stake, with the model's win chance and expected value at your price.

## Research database

Each 5-minute check also records market data that can't be recovered later, in `research/`: the full DraftKings market
with prices (`research/odds/`), ESPN's matchup predictor, the share of bets and money on each side and lines at nine
sportsbooks (Action Network), every injury note with the time first seen, **every change in the probable/confirmed
starting goalies** (`research/goalies.csv`), and the model's number whenever it changes. See
[`research/DATA_DICTIONARY.md`](research/DATA_DICTIONARY.md).

## Files

- `tracker.py`: morning and evening runs. `alert.py`: the 5-minute check. `espn.py`: lines, goalies, injuries. `log_bet.py`: bet form.
- `nhl_mixed_model.py`: the mixed model (Henderson's equations, REML with three variance components, walk-forward, probabilities, betting evaluation).
- `build_features.py`: goalie mix and missing-skater features from box scores. `nhl_data.py`: ESPN and Action Network feeds.
- `build_history.py` → `make_training.py`: rebuild the training data and rerun the backtests (`data/box_hist.csv` is
  rebuilt by `build_history.py`; it's too big to keep in the repo).
- `build_tracker_workbook.py`: builds `NHL_Live_Tracker.xlsx`.
- `data/`: training games with features and lines, last season's box scores, historical lines.
- `state/`: everything the runs build up (`picks_log.csv`, `alerts.csv`, `my_bets.csv`, `box_2026_27.csv`, `model_YYYY-MM-DD.json`).

## How to read the results, and what to expect

- **The honest test** is the scorecard on the **Summary** sheet. Hockey prices swing more per bet than -110 spreads, so
  judge it only after about **300 bets** (roughly half a season).
- **Alerts fire against later, sharper prices.** In every backtest the model lost against closing prices. Expect alerts
  near break-even unless the live data says otherwise; the goalie-news angle is the one worth watching.
- **Don't change thresholds mid-season** based on what has been hitting.
- **Treat it as a test, not a betting system,** until a full season of live results says otherwise.

## Notes

- Data: ESPN's public feeds (schedule, results, box scores, probable goalies, injuries, DraftKings odds) and Action
  Network (historical opening/closing lines, live splits and multi-book lines). No API keys needed.
- 2019-20 and 2020-21 are only used as earlier seasons in the oldest backtests; the live model trains on 2021-22 to 2025-26.
- Arizona (through 2023-24) is treated as the same franchise as Utah so team effects carry over.
- GitHub pauses scheduled workflows in public repos after 60 days without activity; the daily commits count as activity.
