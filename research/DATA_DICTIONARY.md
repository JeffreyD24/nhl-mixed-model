# Research database: data dictionary

Everything the tracker records, so it can be analyzed later for edges in how books set and move NHL prices, how
goalie news reaches the market, and how the betting public behaves. All times are US Eastern (ET), `YYYY-MM-DD HH:MM`.
Every file is append-only and keyed by `game_id` (ESPN's game ID, the same one used in `state/picks_log.csv`).

Snapshots come from the 5-minute alert checks, so their timing is accurate to about 5 minutes (or however late GitHub
runs a check). A row is written only when something changed, so each row marks the first time a new value was seen.

## research/ (market and information snapshots)

### `research/odds/YYYY-MM-DD.csv`: the full DraftKings market, one file per game date
| column | meaning |
|---|---|
| seen_at_et | when this version of the market was first seen |
| game_id, date, book | game, game date, sportsbook (DraftKings via ESPN) |
| home_ml, away_ml | moneylines (American) |
| home_pl, home_pl_odds, away_pl_odds | puck line from the home side (-1.5 = home favored) and the prices on each side |
| total, over_odds, under_odds | total and its prices (hockey totals often move by price, not number: 6.5 at -130/+110) |
| open_* | DraftKings' opening values of the same columns |
| espn_event_id | ESPN's game ID (used to fetch the predictor) |

Why it matters: **in hockey the price is the line.** Most moves are in the moneyline and in the juice on a total, not in
the number. Convert prices to no-vig win chances to compare moves across games.

### `research/goalies.csv`: probable and confirmed starting goalies
`seen_at_et, game_id, date, side, team, goalie_id, goalie, status`. A new row each time ESPN changes the listed
goalie or the status (Expected → Confirmed). Compare with `odds/` to see how fast prices react to a goalie
announcement, and whether a backup getting the start is priced fully.

### `research/espn_predictor.csv`: ESPN's matchup predictor, about once an hour per game
`seen_at_et, game_id, date, home_win_pct, away_win_pct`. A public model many casual bettors see.

### `research/news.csv`: every injury and reporter note
`first_seen_et, posted_et, team, note, note_id`. ESPN's list only keeps each player's latest note, so this is the only
lasting record. Price moves ahead of `posted_et` mean the market knew first.

### `research/model/YYYY-MM-DD.csv`: the model's number through the day
`seen_at_et, game_id, date, away, home, model_home_win, lam_home, lam_away, model_total, away_goalie, home_goalie, missing`,
written when the model's number changes (a goalie announcement, a new injury). `lam_*` are expected regulation goals.

### `research/splits/YYYY-MM-DD.csv`: where the bets and the money are (Action Network)
| column | meaning |
|---|---|
| seen_at_et, game_id, date, away, home | when first seen, and the game |
| num_bets | bets in Action Network's sample on the game |
| consensus_home_pl, consensus_total | consensus puck line and total when the split was recorded |
| pl_home_bets_pct, pl_home_money_pct | % of puck line bets (tickets) and % of money on the home team |
| over_bets_pct, over_money_pct | % of total bets and money on the over |
| home_ml_bets_pct, home_ml_money_pct | % of moneyline bets and money on the home team |

**Bets % shows the crowd; money % shows the dollars.** Money % well above bets % means fewer, bigger bets on that side,
usually sharper bettors. A price moving against the popular side is "reverse line movement".

### `research/books/YYYY-MM-DD.csv`: prices at each sportsbook
`seen_at_et, game_id, date, away, home, book, home_pl, home_pl_odds, away_pl_odds, total, over_odds, under_odds, home_ml, away_ml`
for Consensus, Open, DraftKings, FanDuel, BetRivers, BetMGM, bet365, Caesars and Fanatics. Shows which book moves first and
which lag (the place to shop a price). Totals outside 3.5–9.5 (period or team totals) are left blank.

### `research/line_moves/YYYY-MM-DD.csv`: every price change at every book, with exact times
`game_id, date, away, home, book, market, side, line, price, changed_at_et, status, puck_drop_et, pre_game, an_game_id`.
One row per change to the moneyline, puck line or total at Consensus, Open, DraftKings, FanDuel, BetRivers, BetMGM, bet365,
Caesars and Fanatics, from Action Network's line history, timed to the second (not limited to our 5-minute checks). Action
Network keeps these only about a day after the game, so the morning and evening runs save yesterday's, today's and
tomorrow's games each time. `pre_game = 0` rows are in-game prices some books keep in the same history; filter them out
for pre-game work. This is the dataset for testing what a bet would have gotten at any time of day (for example, how much
of the opening-price edge is left two hours later).

## state/ (tracker records that also feed the research)

| file | what it holds |
|---|---|
| `picks_log.csv` | one row per game: locked model numbers (expected goals, win %, win-by-2 %), expected goalies, opening and closing DraftKings markets, and for each of moneyline / puck line / total at the open and at the close: the side the model prefers, price, expected value, result, units won, and (opening bets) **closing line value** |
| `line_history.csv` | every DraftKings moneyline, puck line and total change seen by the 5-minute checks, with the time first seen (`prob` = no-vig home win %, home puck line %, or over %) |
| `line_jumps.csv` | moneyline moves of 3+ win-% points (or any total change) within 60 minutes, with news in the window, then graded |
| `market_moves.csv` | moves of 5+ win-% points toward the model's side ("Market agrees") |
| `alerts.csv` | every phone alert, including caution alerts with reasons, graded at the alerted price, with closing line value |
| `my_bets.csv` | bets you logged, graded at your price and stake, with the model's win chance and EV at your price |
| `box_2026_27.csv` | box scores of this season's finished games (ice time, goals, assists, goalies) |
| `model_YYYY-MM-DD.json` | the fitted model state used by the 5-minute checks |

## Closing line value (CLV)
How much better your price was than the fair (no-vig) closing price, as an expected return: your decimal odds × the
closing no-vig chance − 1. Example: you took +120 (2.20) and the game closed at a fair 48%: 2.20 × 0.48 − 1 = +5.6%.
Left blank when the line number itself changed (a total that went from 5.5 to 6.5). CLV is the quickest test of a real
edge: it shows up in a few hundred bets, long before the win-loss record is reliable.

## Questions this data is meant to answer
- **Goalies:** how much does a confirmed backup move the price, how fast, and is the move the right size vs. the model's goalie effect?
- **How books move:** how big is a normal move, at what hours, how far from puck drop? Do early moves keep going?
- **Information vs. market:** how often does a price move before the news is posted?
- **Public behavior:** do prices drift toward popular teams and overs and then fail? Does ESPN's predictor pull prices?
- **Our timing:** at which hours is our edge vs. the current price largest, and does betting then produce positive CLV?

## Not recorded (yet)
Player props, period lines.
