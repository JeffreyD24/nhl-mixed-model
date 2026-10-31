# Cold-stretch reviews

When a model goes cold, run `python dev/season_diagnostic.py .`. It fits mixed models on the current season's games
only (team offense/defense, goalie, and the shot-model equivalents: xG created/allowed, finishing, goals saved above
expected), compares them with what the live models believe, and breaks down where the live models' rule bets are losing
(by market, price band, favorite/underdog, home/away, week, team bet on and against), plus how favorites and home teams
are doing against the market. Each run gets its own dated folder with a REPORT.md and the tables behind it, so cold
stretches can be compared over time and lessons carried into the models (after testing them on the backtests).

| Date | Games | Main finding |
|---|---|---|
| [2026-10-31](2026-10-31/REPORT.md) | 216 | Losses concentrated in +150..+249 underdogs during a favorites run; goals model also overrates long shots structurally; shot model's CLV still positive |
