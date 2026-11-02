"""
Extra NHL data for future model work (records only; nothing here feeds alerts yet). Public NHL APIs, no key.
  1. Play-by-play from the NHL itself (richer than ESPN's: zone, on-ice situation code, every event's players and
     coordinates): research/nhl_pbp/YYYY-MM-DD.csv, one row per event, for each finished game.
  2. NHL EDGE tracking stats, a daily snapshot per team (season to date): skating speed, shot speed, zone time,
     shots and goals by area, distance skated in each of the last 10 games: research/edge/YYYY-MM-DD.csv (every
     number flattened into columns) plus research/edge/raw/YYYY-MM-DD.json.gz (the full replies).
  python nhl_extra.py WORKDIR                  yesterday's and the day before's games + today's EDGE snapshot
  python nhl_extra.py WORKDIR --from DATE      play-by-play backfill from DATE to yesterday (no EDGE backfill:
                                               the NHL only serves EDGE as of today)
"""
import os, sys, json, gzip, time, urllib.request
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd

W = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.getcwd()
R = os.path.join(W, "research")
ET = ZoneInfo("America/New_York")
TODAY = pd.Timestamp(dt.datetime.now(ET).date())
API = "https://api-web.nhle.com/v1"
EDGE_TEAM = ("team-detail", "team-zone-time-details", "team-shot-location-detail", "team-shot-speed-detail",
             "team-skating-speed-detail", "team-skating-distance-detail")


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: return json.loads(r.read())
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    print("Fetch failed:", url, type(err).__name__); return None


def pbp_day(d):
    out = os.path.join(R, "nhl_pbp"); os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"{d.date()}.csv")
    old = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(columns=["nhl_game_id"])
    have = set(old.nhl_game_id.astype(int)) if len(old) else set()
    sc = get(f"{API}/score/{d.date()}")
    if not sc: return 0
    rows = []
    for g in sc.get("games", []):
        if g.get("gameType") not in (2, 3) or g.get("gameState") not in ("OFF", "FINAL") or int(g["id"]) in have: continue
        js = get(f"{API}/gamecenter/{g['id']}/play-by-play")
        if not js: continue
        home, away = js["homeTeam"]["abbrev"].lower(), js["awayTeam"]["abbrev"].lower()
        team_of = {js["homeTeam"]["id"]: home, js["awayTeam"]["id"]: away}
        for p in js.get("plays", []):
            det = p.get("details") or {}
            rows.append(dict(date=str(d.date()), nhl_game_id=int(g["id"]), away=away, home=home, event_id=p.get("eventId"),
                             sort_order=p.get("sortOrder"), period=(p.get("periodDescriptor") or {}).get("number"),
                             period_type=(p.get("periodDescriptor") or {}).get("periodType"), time_in_period=p.get("timeInPeriod"),
                             situation_code=p.get("situationCode"), home_defending_side=p.get("homeTeamDefendingSide"),
                             event=p.get("typeDescKey"), team=team_of.get(det.get("eventOwnerTeamId")), x=det.get("xCoord"),
                             y=det.get("yCoord"), zone=det.get("zoneCode"), shot_type=det.get("shotType"), reason=det.get("reason"),
                             shooter_id=det.get("shootingPlayerId") or det.get("scoringPlayerId"), goalie_id=det.get("goalieInNetId"),
                             player_id=det.get("playerId") or det.get("hittingPlayerId") or det.get("winningPlayerId")
                             or det.get("committedByPlayerId") or det.get("blockingPlayerId"),
                             other_player_id=det.get("hitteePlayerId") or det.get("losingPlayerId") or det.get("drawnByPlayerId"),
                             assist1_id=det.get("assist1PlayerId"), assist2_id=det.get("assist2PlayerId"),
                             penalty_type=det.get("descKey"), penalty_min=det.get("duration"),
                             home_score=det.get("homeScore"), away_score=det.get("awayScore"),
                             home_sog=det.get("homeSOG"), away_sog=det.get("awaySOG")))
        time.sleep(0.5)
    if rows:
        D = pd.concat([old, pd.DataFrame(rows)], ignore_index=True) if len(old) else pd.DataFrame(rows)
        D.to_csv(path, index=False)
    n = len({r["nhl_game_id"] for r in rows}); print(f"play-by-play {d.date()}: {n} new games, {len(rows)} events"); return n


def flat(x, pre=""):
    """every number in a reply as {path: value}; lists of records keyed by their label (area, strength code...) or position"""
    out = {}
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ("team", "player", "homeTeam", "awayTeam", "teamLogo", "headshot", "seasonsWithEdgeStats", "gameCenterLink"): continue
            out.update(flat(v, f"{pre}{k}."))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            lab = next((str(v[k]) for k in ("area", "strengthCode", "gameDate") if isinstance(v, dict) and k in v), str(i))
            out.update(flat(v, f"{pre}{lab}."))
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        out[pre.rstrip(".")] = x
    return out


def edge_snapshot():
    teams = get("https://api.nhle.com/stats/rest/en/team")
    sc = get(f"{API}/standings/now")
    if not teams or not sc: print("EDGE: team list unavailable"); return
    active = {s["teamAbbrev"]["default"] for s in sc.get("standings", [])}
    ids = {t["id"]: t["triCode"] for t in teams.get("data", []) if t.get("triCode") in active}
    raw, rows = {}, []
    for tid, abbr in sorted(ids.items(), key=lambda x: x[1]):
        row = dict(date=str(TODAY.date()), team=abbr.lower(), nhl_team_id=tid)
        for ep in EDGE_TEAM:
            js = get(f"{API}/edge/{ep}/{tid}/now")
            if js is None: continue
            raw[f"{abbr}|{ep}"] = js
            if ep not in ("team-skating-speed-detail", "team-shot-speed-detail"):       # those two are leaderboards of single plays
                row.update({f"{ep}.{k}": v for k, v in flat(js).items()})
            time.sleep(0.3)
        rows.append(row)
    for ep in ("skater-landing", "goalie-landing", "team-landing"):
        js = get(f"{API}/edge/{ep}/now")
        if js is not None: raw[ep] = js
    d = os.path.join(R, "edge"); os.makedirs(os.path.join(d, "raw"), exist_ok=True)
    pd.DataFrame(rows).to_csv(os.path.join(d, f"{TODAY.date()}.csv"), index=False)
    with gzip.open(os.path.join(d, "raw", f"{TODAY.date()}.json.gz"), "wt") as f: json.dump(raw, f)
    print(f"EDGE: {len(rows)} teams, {max((len(r) for r in rows), default=0)} numbers per team")


def edge_seasons():
    """season totals of the EDGE team numbers for past seasons (2021-22 is the first): research/edge/seasons/SEASON.csv"""
    teams = get("https://api.nhle.com/stats/rest/en/team")
    if not teams: return
    d = os.path.join(R, "edge", "seasons"); os.makedirs(d, exist_ok=True)
    for y in range(2021, int(TODAY.year) + (0 if TODAY.month < 9 else 1) - 1):
        season = f"{y}{y + 1}"; path = os.path.join(d, f"{season}.csv")
        if os.path.exists(path): continue
        sc = get(f"https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId={season}%20and%20gameTypeId=2")
        ids = {r["teamId"] for r in (sc or {}).get("data", [])}
        tri = {t["id"]: t["triCode"] for t in teams.get("data", [])}
        rows = []
        for tid in sorted(ids):
            row = dict(season=season, team=str(tri.get(tid, tid)).lower(), nhl_team_id=tid)
            for ep in ("team-detail", "team-zone-time-details", "team-shot-location-detail", "team-skating-distance-detail"):
                js = get(f"{API}/edge/{ep}/{tid}/{season}/2")
                if js is not None: row.update({f"{ep}.{k}": v for k, v in flat(js).items()})
                time.sleep(0.3)
            rows.append(row)
        pd.DataFrame(rows).to_csv(path, index=False); print(f"EDGE season {season}: {len(rows)} teams")


def main():
    if "--from" in sys.argv:
        end = pd.Timestamp(sys.argv[sys.argv.index("--to") + 1]) if "--to" in sys.argv else TODAY - pd.Timedelta(days=1)
        days = pd.date_range(pd.Timestamp(sys.argv[sys.argv.index("--from") + 1]), end)
    else:
        days = [TODAY - pd.Timedelta(days=2), TODAY - pd.Timedelta(days=1)]
    print("play-by-play games saved:", sum(pbp_day(d) for d in days))
    if "--from" not in sys.argv or "--edge" in sys.argv: edge_snapshot()
    if "--edge-seasons" in sys.argv: edge_seasons()


if __name__ == "__main__":
    main()
