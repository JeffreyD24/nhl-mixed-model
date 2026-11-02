"""
NHL shift charts: every player's every shift (period, start, end, length), plus the goal events the NHL lists with them,
for each finished game. Source: the NHL's public stats API (no key). The NBA equivalent is research/minutes/.
Writes research/shifts/YYYY-MM-DD.csv (one file per game date, ET) and skips games already saved.
  python shifts.py WORKDIR                 yesterday and the day before (run by the morning workflow)
  python shifts.py WORKDIR --from 2026-10-07   every date from then to yesterday (backfill)
"""
import os, sys, json, time, urllib.request
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd

W = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.getcwd()
OUT = os.path.join(W, "research", "shifts"); os.makedirs(OUT, exist_ok=True)
ET = ZoneInfo("America/New_York")
TODAY = pd.Timestamp(dt.datetime.now(ET).date())


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: return json.loads(r.read())
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    print("Fetch failed:", url, type(err).__name__); return None


def secs(s):
    try: m, x = str(s).split(":"); return int(m) * 60 + int(x)
    except Exception: return None


def toi_report(gid, home, away):
    """fallback when the shift-chart feed is empty (it is for some games): the NHL's official HTML time-on-ice reports,
    TH (home) and TV (visitor). They list each player's shifts by name and sweater number (no player id)."""
    import re, html as H
    season = f"{str(gid)[:4]}{int(str(gid)[:4]) + 1}"; num = str(gid)[-6:]
    rows = []
    for code, team in (("TH", home), ("TV", away)):
        try:
            req = urllib.request.Request(f"https://www.nhl.com/scores/htmlreports/{season}/{code}{num}.HTM", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as r: b = r.read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"  TOI report {code}{num} unavailable: {type(e).__name__}"); continue
        cells = [H.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", b, re.S)]
        clock = re.compile(r"^(\d+):(\d\d) / \d+:\d\d$"); name = re.compile(r"^(\d+) ([^,]+), (.+)$")
        player = number = None; i = 0
        while i < len(cells):
            c = cells[i]; m = name.match(c)
            if m and not clock.match(c):
                number, player = int(m.group(1)), f"{m.group(3).title()} {m.group(2).title()}"; i += 1; continue
            if player and c.isdigit() and i + 4 < len(cells) and clock.match(cells[i + 2]) and clock.match(cells[i + 3]):
                per = cells[i + 1]; per = 4 if per.upper() == "OT" else int(per) if per.isdigit() else None
                a, z = clock.match(cells[i + 2]), clock.match(cells[i + 3])
                st, en = int(a.group(1)) * 60 + int(a.group(2)), int(z.group(1)) * 60 + int(z.group(2))
                rows.append(dict(team=team, player_id=None, player=player, sweater=number, period=per, shift_number=int(c),
                                 start=cells[i + 2].split(" / ")[0], end=cells[i + 3].split(" / ")[0], start_sec=st, end_sec=en,
                                 duration_sec=secs(cells[i + 4]), type_code=517, event=cells[i + 5] if i + 5 < len(cells) else None,
                                 event_detail=None, source="toi_report"))
                i += 5; continue
            i += 1
        time.sleep(1)
    return rows


def day(d):
    path = os.path.join(OUT, f"{d.date()}.csv")
    old = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(columns=["nhl_game_id"])
    have = set(old.nhl_game_id.astype(int)) if len(old) else set()
    sc = get(f"https://api-web.nhle.com/v1/score/{d.date()}")
    if not sc: return 0
    rows = []
    for g in sc.get("games", []):
        if g.get("gameType") not in (2, 3) or g.get("gameState") not in ("OFF", "FINAL") or int(g["id"]) in have: continue
        js = get(f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={g['id']}")
        home, away = g["homeTeam"]["abbrev"].lower(), g["awayTeam"]["abbrev"].lower()
        if not js or not js.get("data"):
            # the feed is empty for some games for good (checked Nov 1, 2026): read the official time-on-ice reports instead
            fb = toi_report(g["id"], home, away)
            if fb:
                for x in fb: x.update(date=str(d.date()), nhl_game_id=int(g["id"]), away=away, home=home)
                rows += fb; print(f"  {d.date()} game {g['id']}: {len(fb)} shifts from the time-on-ice reports")
            else:
                print(f"  {d.date()} game {g['id']}: no shift chart yet")
            continue
        for x in js["data"]:
            rows.append(dict(date=str(d.date()), nhl_game_id=int(g["id"]), away=away, home=home,
                             team=str(x.get("teamAbbrev") or "").lower(), player_id=x.get("playerId"),
                             player=f"{x.get('firstName') or ''} {x.get('lastName') or ''}".strip(), period=x.get("period"),
                             shift_number=x.get("shiftNumber"), start=x.get("startTime"), end=x.get("endTime"),
                             start_sec=secs(x.get("startTime")), end_sec=secs(x.get("endTime")), duration_sec=secs(x.get("duration")),
                             type_code=x.get("typeCode"), event=x.get("eventDescription"), event_detail=x.get("detailCode"),
                             source="shift_feed"))
        time.sleep(1.5)
    if rows:
        D = pd.concat([old, pd.DataFrame(rows)], ignore_index=True) if len(old) else pd.DataFrame(rows)
        D.to_csv(path, index=False)
    n = len({r["nhl_game_id"] for r in rows})
    print(f"{d.date()}: {n} new games, {len(rows)} shift rows")
    return n


def main():
    if "--from" in sys.argv:
        start = pd.Timestamp(sys.argv[sys.argv.index("--from") + 1])
        days = pd.date_range(start, TODAY - pd.Timedelta(days=1))
    else:
        days = [TODAY - pd.Timedelta(days=2), TODAY - pd.Timedelta(days=1)]
    total = sum(day(d) for d in days)
    print(f"Shift charts: {total} games saved.")


if __name__ == "__main__":
    main()
