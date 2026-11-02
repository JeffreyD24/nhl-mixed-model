"""
Schedule / travel adjustment to the shot model's home win chance (moneyline), adopted Nov 2, 2026.
Fit on the shot model's opener predictions 2021-22..2025-26 (tracker repo analysis/travel_fixes.py, each season's weights fit
without it: +159.6u vs +96.1u, better in 4 of 5 seasons):
  only the away team on a back-to-back: +2.5 win-% pts for the home team
  only the home team on a back-to-back: -3.1
  away team moved west since its last game: -2.3 per time zone (teams flying west play better than priced)
"""
import os, json
import pandas as pd
from zoneinfo import ZoneInfo

W_AWAY_B2B, W_HOME_B2B, W_WEST = 0.0253, -0.0307, -0.0226
NY, CH, DE, LA, PH = "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Phoenix"
TZ = {"ana": LA, "bos": NY, "buf": NY, "car": NY, "cbj": NY, "cgy": DE, "chi": CH, "col": DE, "dal": CH, "det": NY, "edm": DE,
      "fla": NY, "la": LA, "min": CH, "mtl": NY, "nj": NY, "nsh": CH, "nyi": NY, "nyr": NY, "ott": NY, "phi": NY, "pit": NY,
      "sea": LA, "sj": LA, "stl": CH, "tb": NY, "tor": NY, "uta": DE, "van": LA, "vgk": LA, "wpg": CH, "wsh": NY}


def offset(team, day):
    tz = TZ.get(team)
    if tz is None: return None
    t = pd.Timestamp(day)
    return (t.tz_localize(ZoneInfo(tz)).utcoffset() - t.tz_localize(ZoneInfo(NY)).utcoffset()).total_seconds() / 3600


def last_games(nd, day, cache_path, back_days=14):
    """{team: (date of its last game before `day`, home team of that game)} from ESPN scoreboards; cached per day"""
    key = str(pd.Timestamp(day).date())
    try:
        c = json.load(open(cache_path))
        if c.get("day") == key: return {k: tuple(v) for k, v in c["last"].items()}
    except Exception:
        pass
    last = {}
    for k in range(1, back_days + 1):
        d = pd.Timestamp(day) - pd.Timedelta(days=k)
        try: rows = nd.scoreboard(d)
        except Exception: continue
        for r in rows:
            for t in (r["home"], r["away"]):
                if t not in last: last[t] = (str(d.date()), r["home"])
    try: json.dump(dict(day=key, last=last), open(cache_path, "w"))
    except Exception: pass
    return last


def adjustment(home, away, day, last):
    """(change to the home win chance, text) for this game"""
    d = pd.Timestamp(day)
    def b2b(t): return t in last and (d - pd.Timestamp(last[t][0])).days == 1
    adj, why = 0.0, []
    hb, ab = b2b(home), b2b(away)
    if ab and not hb: adj += W_AWAY_B2B; why.append(f"{away.upper()} on a back-to-back")
    if hb and not ab: adj += W_HOME_B2B; why.append(f"{home.upper()} on a back-to-back")
    if away in last:
        now_off, prev_off = offset(home, d), offset(last[away][1], d)
        if now_off is not None and prev_off is not None and now_off < prev_off:
            zones = prev_off - now_off
            adj += W_WEST * zones; why.append(f"{away.upper()} flew {zones:.0f} time zone{'s' if zones > 1 else ''} west")
    return adj, ", ".join(why)
