# Who covers each NHL team

- `nhl_media_list.csv`: beat writers and national reporters, from Claude's knowledge to mid-2026 (Nov 2, 2026; not re-checked,
  some may have changed jobs). Columns: `category`, `team`, `team_code`, `name`, `role`, `outlet`, `status`, `source`, `last_checked`.
- `bluesky_check.csv`: each of them looked up on Bluesky (handle, followers, last post, posts in the last 14 days, bio).
- `bluesky_starterpacks.csv`: members of public Bluesky starter packs of NHL reporters whose bio names a team or a reporting job,
  with recent activity (finds people the list doesn't have).
- `bluesky_watch.csv`: the accounts `bluesky_watch.py` reads every minute, picked by hand from the two files above: reporters
  who cover a team (or the league) and posted 3+ times in the 14 days before the check. Fan sites, podcasts without
  reporting, and writers on other sports were left out. Edit this file to add or drop accounts.

Re-run the check (Actions, "Check reporters on Bluesky (one-time)") before next season: reporters move.
