"""Probe which NHL endpoints answer from GitHub's servers, and how fast / with what status, for games from different seasons.
Prints one line per URL: status or error, seconds, bytes. Run from this folder in GitHub Actions (the Claude workspace cannot reach nhle.com).
Context: fetch_nhl_box.py hung on 2011-12 boxscores (no progress for 6+ minutes), yet shifts.py (api-web score + api shiftcharts) works from Actions for 2021+.
"""
import time, urllib.request, urllib.error

GAMES = [2011020001, 2013020500, 2015020001, 2018020001, 2020020010, 2021020001, 2024020001]
URLS = ["https://api-web.nhle.com/v1/gamecenter/{g}/boxscore", "https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={g}",
        "https://api-web.nhle.com/v1/gamecenter/{g}/play-by-play"]
for g in GAMES:
    for u in URLS:
        url = u.format(g=g); t0 = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r: b = r.read(); print(f"{g} OK {r.status} {len(b)}B {time.time() - t0:.1f}s {url.split('//')[1][:70]}", flush=True)
        except urllib.error.HTTPError as e: print(f"{g} HTTP {e.code} {time.time() - t0:.1f}s {url.split('//')[1][:70]}", flush=True)
        except Exception as e: print(f"{g} FAIL {type(e).__name__} {str(e)[:50]} {time.time() - t0:.1f}s {url.split('//')[1][:70]}", flush=True)
