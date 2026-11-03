# NHL mixed-model tracker

Two mixed models, a goals model (team offense, team defense and **goalie** random effects, home ice, back-to-backs, missing
regular skaters) and a shot-based expected-goals model, predict NHL moneylines, puck lines and totals, run themselves on
GitHub every day, and send phone alerts when they disagree with the posted price. It is the NHL version of
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
| **Morning run** (`morning.yml`) | Daily, 10:11 AM EDT / 9:11 AM EST | Adds last night's results and box scores, grades finished games, alerts and your bets, refreshes today's games, then **locks tomorrow's picks**, because DraftKings posts NHL lines around 11:20 AM–12:30 PM the day before the game (about 31 hours ahead). Rebuilds `NHL_Live_Tracker.xlsx`. |
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
- **Information timing:** DraftKings posts lines about 31 hours before the game, before the previous day's games are
  played. Since Oct 30, both the backtests and the live picks use only results through two days before the game
  (`dev/lag_backtest.py`, `backtests/lag_backtests.csv`). Results held up: at opening prices, shot model +119.0 units on
  1,295 bets (+9.2%), goals model +72.0 on 1,796 (+4.0%); halfway prices +3.8% and +0.3%.
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

- **Bet on DraftKings button:** every alert has a **Bet on DraftKings** button that opens DraftKings with that exact bet
  (side, puck line or total) on your bet slip, plus **Log this bet**. You still confirm the bet yourself.
- **New lines within about a minute:** between the 5-minute checks, `opener_watch.py` looks every minute for games where
  DraftKings has just posted a line; a new line triggers a full check right away. If ESPN hasn't picked the line up yet,
  the check uses DraftKings' price from Action Network.
- **What an alert says:** the bet and price, the model's win chance vs. the chance the price needs, the expected value
  (and what it was at the opening price), the model's expected score, the goalies (expected / confirmed / not announced),
  which regulars the model has as missing, the moneyline or total history with times, and the latest injury news.
- **Rule:** moneyline and puck line. Expected value **6%+** while the DraftKings price is at (or within 1.5 win-% points of) its
  opening price; **9%+** once it has moved further or the line number changed. In the backtests most of the edge was gone
  by halfway between open and close (shot model +9.0% per bet at the open, +2.3% halfway, −2.2% at the close;
  `backtests/midpoint_prices.csv`), and bigger edges held up better. One alert per game, market and model.
  **Goals model long shots (+150 or longer): opening price only** (since Oct 31). These alerts go out only while the price is
  within 1.5 win-% points of the opening price, titled **OPENING PRICE ONLY**, with the shortest price still worth taking
  ("bet only at +165 or longer"). The goals model's underdog win chances run about 5 points high: these bets made +13.5u on
  641 at the open but lost once the price moved. Shot-model long shots alert normally (they're calibrated). Scorecard unchanged.
  Alerts carry an `open_only` column in `state/alerts.csv` so these can be graded separately.
  Settings at the top of `alert.py`: `THRESHOLD`, `THRESHOLD_MOVED`, `NEAR_OPEN`, `OPEN_ONLY_LONGSHOTS`, `ALERT_MARKETS` (add `"total"` for totals), `MAX_MOVE`, `WINDOW`.
- **Caution alerts.** Sent with **CAUTION** in the title, at normal priority, when the edge is there but:
  - the starting goalies aren't both **confirmed** yet (ESPN lists them as "expected" for most of the day), or
  - the moneyline has moved 5+ win-% points **against** the bet since it opened (the market knows something).

  If a caution clears later (goalies confirmed, edge still there), a regular alert follows, titled **UPDATE**, saying what
  cleared and how the expected value changed since the caution.
- **Reminder if you haven't logged the bet** (ported from the NBA tracker, Oct 31, 2026): 30 minutes after an alert
  (`REMIND_AFTER_MIN`), if no bet is logged for that game and market, one **REMINDER** goes out before puck drop with the price
  now and a verdict: **[BET]** if the expected value at today's price still meets the bar (6% near the opening price, 9% once it
  has moved; opening-price-only long shots need the price still near the open), **[PASS]** if not. It also says whether both
  goalies are confirmed yet. Only alerts sent since this change get reminders; it relies on you logging every bet you place.
- **Your logged bets are checked** (ported from the NBA tracker, Oct 31, 2026). If you already logged a bet on that game and
  market on the same side, the title starts with **ALREADY BET**, shows your bet, and comes at normal priority. If your logged
  bet is on the **other** side, the title starts with **YOU BET THE OTHER SIDE**. Bets on other markets of the game are listed at the end.
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

**Every line change is saved:** each morning and evening run stores the complete, to-the-second price history of every
game at nine sportsbooks (`research/line_moves/`), which Action Network only keeps for about a day. Each 5-minute check also
records market data that can't be recovered later, in `research/`: the full DraftKings market
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

## Opening-price bets only (since Nov 1, 2026)

- Bet alerts go out only while the price is at (or within 1.5 win-% points of) its opening number, and each one says
  **"Bet only at X or better"**: if DraftKings already shows a shorter price, skip it. The backtests made money only at
  opening prices and lost at closing prices every season.
- Once the price has moved, alerts are **INFO ONLY** (low priority, no DraftKings button, no reminder): don't bet them.
- The goalie caution no longer applies to opening-price alerts. Backtest openers (2024-25 and 2025-26, goals model) made
  +3.7% when the expected goalie started and +3.2% when someone else did, so waiting for confirmation adds nothing.

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

## Polymarket US tracking (paper trades only)

`polymarket.py` (the same file in the NHL, NBA and NFL repos) watches **Polymarket US**, the CFTC-regulated exchange, and
records what the model would do there. **It never trades.** Connecticut has ordered Polymarket to stop offering sports
contracts there, so this builds the record now for use from a state where it's allowed.

**Why an exchange is different:** you trade against other people, not a book, so winners don't get limited, and you can post
your own price (a limit order, no fee) instead of taking the best offer (taker fee ≈ 5% × price × (1 − price) per contract,
about 1.25¢ at 50¢; set in `TAKER_FEE_RATE`).

**What runs:** right after each 5-minute `alert.py` check (`alert_loop.sh`), so it uses the number alert.py just computed:
1. pulls this league's games from Polymarket's public data API (`gateway.polymarket.us`, no key) and matches them to
   `state/model_*.json`;
2. saves the best bid, best offer and depth of every moneyline, spread and total contract to
   `research/polymarket/YYYY-MM-DD.csv` (only when something changed);
3. turns the model's number into a probability for each contract: the repo's own Poisson model on the live expected goals, for **both** models (each gets its own paper trades). Only the ±1.5 puck line is priced.
4. logs paper trades on the moneyline and puck line (totals are saved but not traded, same as the alerts) to `state/poly_paper.csv`, one per game, market and model:
   - **taker**: buy at the best offer the first time expected value after the fee is **6%+**;
   - **maker**: a limit bid at the highest price that still has 6% expected value, counted as filled if the best
     offer later falls to it before the game (approximate: ignores who was first in line);
   - each with DraftKings' price on the same bet at that moment (from `research/odds/`), to see which is cheaper.

**Order books and early trades (added Nov 2, 2026).** Every check also saves the full order book (every price level and size, plus
when the contract opened and its opening price) to `research/polymarket/book_YYYY-MM-DD.csv`; `REPORT.md` summarizes the depth.
**NHL only:** Polymarket opens a game's contracts about four days ahead, so `.github/workflows/early.yml` (8:40 AM and 8:40 PM ET)
runs the normal tracker in a scratch copy for games 2-4 days out and saves just the model files to `state/early/`. The Polymarket
tracker paper-trades those numbers as separate `xg@early` / `goals@early` trades, until the regular model file for that day exists
(then the usual `xg` / `goals` trades take over). Early models don't know the starting goalies (they use the usual assumption).
Nothing in `state/early/` touches the picks logs, bet records or bet alerts.

The **morning run** grades finished trades from Polymarket's settlement prices (`--grade`), adds closing line value (last mid
price before the start minus the price paid, in cents) and rewrites `research/polymarket/REPORT.md`.

**First runs:** this was built from Polymarket US's documentation and tested against mock responses; it had not yet seen real
data. Each day it saves one raw event and one price reply to `research/polymarket/samples/`, and anything it can't read goes
to `research/polymarket/unmatched.csv` (the `line_source` column in the snapshots says whether a spread's sign came from the
side's own text or had to be assumed). Check those after the first day. To pause it, add a repository variable
`POLYMARKET_OFF` = `1` (Settings → Secrets and variables → Actions → Variables); delete it to resume.

Settings at the top of `polymarket.py`: `THRESHOLD`, `PAPER_MARKETS`, `TAKER_FEE_RATE`, `MAKER`, `MIN_DEPTH` (20 contracts).


## Phone alerts: bets only (since Nov 1, 2026)
`BET_ONLY = True` in `alert.py`: your phone gets only bet alerts (the EV bar is met with no caution) and **DON'T BET**
follow-ups (a bet alert you haven't logged whose EV fell below the bar before puck drop, or an opening-price-only long shot
whose price moved). Cautions, INFO ONLY, market-agrees and line-jump alerts are still logged in their files, just not pushed.
The 30-minute reminder was replaced by DON'T BET.
- **Never both sides (since Nov 1, 2026).** When the shot model and the goals model back different teams in the same game
  (moneyline or puck line, at the bet bar), or you already logged a bet on the other team, the alert is logged as
  **NO BET (both sides)** and not pushed. On Oct 31 both models alerted on UTA @ PHI from opposite sides (UTA ML -155 from the
  shot model, PHI ML +130 from the goals model), and both got bet. Bets on both teams pay the vig twice.
- **Only the shot model alerts (since Nov 1, 2026).** `ALERT_MODELS = ("xg",)` in `alert.py`. Backtest 2025-26 at opening
  prices (`backtests/disagree_bets.csv`): goals-model bets the shot model also made +76.7u on 753 (+10.2%); goals-model-only
  bets -16.6u on 1,026 (-1.6%, negative both seasons, worst at +150 and longer: -27.9u on 345). Shot model overall +111.1u on
  1,237 (+9.0%). The goals model still runs every check and is logged in `research/model/` for research.

## Reporter news from Bluesky: goalies and lineups (since Nov 2, 2026)

Ported from the NBA tracker, aimed at the NHL's biggest single-player effect: the starting goalie. Between the 5-minute checks,
`bluesky_watch.py` reads new posts every minute from the 54 NHL accounts in `research/media/bluesky_watch.csv` (beat writers for
24 teams, Daily Faceoff, AP, NHL.com, and accounts that mirror Friedman, LeBrun, Seravalli and Johnston from X; no active
reporter was found for Calgary, Detroit, Edmonton, Florida, Los Angeles, Nashville, Utah or Washington). Free, public API.

- **Every post is saved** (`research/bluesky/YYYY-MM-DD.csv`) with the time it was posted and first seen, the players it names,
  any starting goalie it reports and any clear skater decision.
- **Starting goalies.** A post naming one of a team's goalies with "will start", "gets the start", "in goal tonight"... is
  saved to `state/goalie_news.json` as **confirmed** (no hedge word) or **expected** ("expected to start", "first off the ice").
  The alert check uses a reporter-confirmed starter until ESPN confirms one (shown as "X (confirmed by [reporter] 10:42 AM)",
  and it counts as confirmed for the goalie caution), and an expected one only when ESPN lists nobody. ESPN's own confirmation
  always wins.
- **Skaters.** A clear decision in one sentence with the player's name and no hedge ("out tonight", "will not play",
  "scratched", "will play", "draws back in") is saved to `state/news_overrides.json` and used for that day's game.
- Goalie news that is confirmed or names someone other than the model's most likely starter, and skater decisions about a
  regular worth 0.25+, run a full check at once: if the news opens an edge, the bet alert goes out right away. The news itself
  is logged, not pushed (phone alerts are bets only; `NEWS_PUSH` in `bluesky_watch.py`).
- Who covers each team: `research/media/nhl_media_list.csv` (172 people, Claude's knowledge to mid-2026, not re-checked), plus
  the one-time Bluesky check, which also read public starter packs of NHL reporters (`tools/bluesky_check.py`,
  `research/media/bluesky_check.csv`, `bluesky_starterpacks.csv`).
- Goal: measure how much earlier reporters name the starter than ESPN confirms him (`research/goalies.csv` records when ESPN's
  status changes) and whether the moneyline has moved by then.
