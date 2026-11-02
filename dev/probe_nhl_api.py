import json, urllib.request
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
            b = r.read(); print("OK", len(b), u); return json.loads(b)
    except Exception as e: print("FAIL", u, type(e).__name__, str(e)[:80]); return None
sc = get("https://api-web.nhle.com/v1/score/2026-10-31")
gid = sc["games"][0]["id"] if sc else 2026020150
tid = sc["games"][0]["homeTeam"]["id"] if sc else 1
pbp = get(f"https://api-web.nhle.com/v1/gamecenter/{gid}/play-by-play")
if pbp:
    pl = pbp.get("plays", []); print("plays", len(pl)); print(json.dumps(pl[20])[:900])
    from collections import Counter; print(Counter(p.get("typeDescKey") for p in pl).most_common(20))
    print("keys", list(pbp.keys()))
for u in [f"https://api-web.nhle.com/v1/edge/team-landing/now", f"https://api-web.nhle.com/v1/edge/team-detail/{tid}/now",
          f"https://api-web.nhle.com/v1/edge/team-detail/{tid}/20262027/2", f"https://api-web.nhle.com/v1/edge/team-skating-speed-detail/{tid}/now",
          f"https://api-web.nhle.com/v1/edge/team-shot-speed-detail/{tid}/now", f"https://api-web.nhle.com/v1/edge/team-zone-time-details/{tid}/now",
          f"https://api-web.nhle.com/v1/edge/team-shot-location-detail/{tid}/now", f"https://api-web.nhle.com/v1/edge/skater-landing/now",
          f"https://api-web.nhle.com/v1/edge/goalie-landing/now", "https://api-web.nhle.com/v1/edge/team-skating-distance-detail/1/now",
          f"https://api-web.nhle.com/v1/gamecenter/{gid}/right-rail", f"https://api-web.nhle.com/v1/gamecenter/{gid}/boxscore",
          "https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20262027%20and%20gameTypeId=2",
          "https://api.nhle.com/stats/rest/en/skater/realtime?limit=5&cayenneExp=seasonId=20262027"]:
    d = get(u)
    if d is not None: print("   ", json.dumps(d)[:700])
