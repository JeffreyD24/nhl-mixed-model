# NHL starting goalies, 2010-11 .. 2022-23 (job B)

**Status Nov 3, 2026: done from the hockeyR play-by-play, not from nhle.com.** api-web.nhle.com does not answer GitHub's servers (the `fetch-nhl-box.yml` run hung with no output for 6+ minutes and was cancelled),
so `fetch_nhl_box.py` is kept but not used. Goalies are built by `build_goalies_from_hockeyr.py` from the hockeyR-data files (about 30 MB per season, plain curl from raw.githubusercontent.com works; see `../hockeyr/fetch_raw_pbp.sh`).

- `goalies_hockeyr_2010_2023.csv.gz`: 35,082 rows, one per goalie who was on the ice, 16,350 games (regular season + playoffs, 2010-11 to 2022-23). Columns: game_id, season, season_type, date, team (abbrev), team_name, is_home, goalie (name, `First.Last`), goalie_id (NHL id, 0.1% blank), **starter** (goalie on the ice at the opening faceoff), toi_sec (approximate), shots_against, goals_against, game_sec, goalie_toi_share.
- Checks in `checks_hockeyr.txt`: 100% of team-games have exactly one starter; starters play 55+ minutes in 92.3% of games and are out before 40 minutes in 5.0%; season start counts for well-known goalies match their games played.
- **Filter on `goalie_toi_share >= 0.9`** before using toi_sec / shots_against / goals_against (0.6% of team-games are below it: the source file lacks the goalie column for part of the game). The starter flag is usually still right there.
- Shots against exclude empty-net shots (no goalie on the ice); about 77% of team-games equal the independent team-game table exactly, 90% within one shot.
- Not covered: skater ice time (no free source; the play-by-play only lists who is on the ice at each event), 2023-24 onward.
- 2 of 16,352 games in the team-game table have no goalie rows (2013020971, 2015020497).

The raw hockeyR files have no license and are not committed; the output here is derived, aggregated facts only.

---
## Original plan (nhle.com; did not work from GitHub)

Not yet fetched: the Claude workspace cannot reach nhle.com, so `fetch_nhl_box.py` runs in GitHub Actions
(`.github/workflows/fetch-nhl-box.yml`, manual run; saves and pushes after each season; safe to rerun). README is updated with counts after the run.

- Source: NHL public API `api-web.nhle.com/v1/gamecenter/{game_id}/boxscore` (undocumented but public; private research use). Game list = hockeyR table regular-season games.
- `goalies_2011_2023.csv`: one row per goalie who played, with `starter` (1 = API `starter` flag; where the flag is absent in older seasons, the first-listed goalie who played, marked `starter_source = first_listed`), shots against, goals against, TOI seconds.
- `skaters_2011_2023.csv.gz`: every forward and defenseman who played, TOI seconds. (Scratches are not in the box score: "missed" = not listed.)
- Checks written to `checks.txt` (one starter per team-game, join rate to hockeyR). Known risk: `first_listed` may mis-pick the starter if the API lists goalies by sweater number; if the share
  of `first_listed` is large, Opus should check it against pulled-goalie games (starter TOI < 1800 s) before using older seasons.
