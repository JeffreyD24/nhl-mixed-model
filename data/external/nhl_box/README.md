# NHL starting goalies and skater ice time, 2011-12 .. 2022-23 (job B)

Not yet fetched: the Claude workspace cannot reach nhle.com, so `fetch_nhl_box.py` runs in GitHub Actions
(`.github/workflows/fetch-nhl-box.yml`, manual run; saves and pushes after each season; safe to rerun). README is updated with counts after the run.

- Source: NHL public API `api-web.nhle.com/v1/gamecenter/{game_id}/boxscore` (undocumented but public; private research use). Game list = hockeyR table regular-season games.
- `goalies_2011_2023.csv`: one row per goalie who played, with `starter` (1 = API `starter` flag; where the flag is absent in older seasons, the first-listed goalie who played, marked `starter_source = first_listed`), shots against, goals against, TOI seconds.
- `skaters_2011_2023.csv.gz`: every forward and defenseman who played, TOI seconds. (Scratches are not in the box score: "missed" = not listed.)
- Checks written to `checks.txt` (one starter per team-game, join rate to hockeyR). Known risk: `first_listed` may mis-pick the starter if the API lists goalies by sweater number; if the share
  of `first_listed` is large, Opus should check it against pulled-goalie games (starter TOI < 1800 s) before using older seasons.
