import json, urllib.request, time
def raw(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}), timeout=30) as r:
            b = r.read(); return r.status, b
    except Exception as e: return type(e).__name__, str(e).encode()
for gid in (2026020180, 2026020100, 2026020060, 2026020217):
    for u in (f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={gid}",
              f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={gid}&exclude=eventDetails",
              f"https://www.nhl.com/scores/htmlreports/20262027/TH{str(gid)[-6:]}.HTM"):
        st, b = raw(u); print(gid, st, len(b), u.split('/')[-1][:60], b[:150])
        time.sleep(1)
