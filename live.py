"""
NHL live (in-game) recorder: run every minute by live_loop.sh while a game is in progress. Records only; no alerts.

Writes research/live/YYYY-MM-DD/ (date = game date, ET):
  situation.csv   ESPN: period, clock, score, each goalie's saves, the last play (goal, penalty, stoppage...)
  espn_odds.csv   ESPN's odds feeds for the game (whatever providers it lists in-game)
  books.csv       Action Network: full game and each period's puck line / total / moneyline / team totals at each book,
                  with is_live (True = an in-game price)
Rows are written only when a value changed, so each row marks the first poll that saw it.
Exit code: 0 = recorded at least one game in progress; 2 = nothing in progress but a game starts within 45 minutes
(or should have started in the last 45); 3 = nothing in progress or about to start (the loop stops).
  python live.py WORKDIR [--include-final]
"""
import os, sys, json, datetime as dt
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

W = os.path.abspath(sys.argv[1]); sys.path.insert(0, W)
import nhl_data as nd                                         # noqa: E402
import research                                               # noqa: E402

ET = ZoneInfo("America/New_York")
NOW = pd.Timestamp(dt.datetime.now(ET).replace(tzinfo=None))
INCLUDE_FINAL = "--include-final" in sys.argv
AN_BOOKS = nd.AN_BOOKS
AN_PERIODS = ("event", "firstperiod", "secondperiod", "thirdperiod")


def num(x):
    try: return float(x)
    except (TypeError, ValueError): return np.nan


def espn_games():
    evs = []
    for d in (NOW - pd.Timedelta(days=1), NOW):
        try: evs += nd.get(f"{nd.ESPN}/scoreboard?dates={d:%Y%m%d}&limit=50").get("events", [])
        except Exception as e: print("ESPN scoreboard unavailable:", type(e).__name__)
    seen, out = set(), []
    for ev in evs:
        if ev["id"] in seen: continue
        seen.add(ev["id"]); out.append(ev)
    return out


def situation_row(ev):
    comp = ev["competitions"][0]; st = comp.get("status", {}); typ = st.get("type", {})
    teams = {c["homeAway"]: c for c in comp["competitors"]}
    stat = lambda side, name: next((s.get("displayValue") for s in teams[side].get("statistics", []) if s.get("name") == name), None)
    lp = (comp.get("situation") or {}).get("lastPlay") or {}
    start = pd.to_datetime(comp.get("date"), utc=True).tz_convert(ET).tz_localize(None)
    return dict(seen_at_et=str(NOW)[:19], espn_event_id=int(ev["id"]), date=str(start.date()),
                away=nd.code(teams["away"]["team"]["abbreviation"]), home=nd.code(teams["home"]["team"]["abbreviation"]),
                state=typ.get("state"), detail=typ.get("shortDetail"), period=st.get("period"), clock=st.get("displayClock"),
                away_score=num(teams["away"].get("score")), home_score=num(teams["home"].get("score")),
                away_saves=num(stat("away", "saves")), home_saves=num(stat("home", "saves")),
                last_play_type=(lp.get("type") or {}).get("text"), last_play=(lp.get("text") or "")[:200])


def espn_odds_rows(ev, base):
    comp = ev["competitions"][0]; rows = []
    try:
        od = nd.get(f"{nd.CORE}/events/{ev['id']}/competitions/{comp['id']}/odds?limit=50")
    except Exception as e:
        print("ESPN odds unavailable:", type(e).__name__); return rows
    am = lambda d, *ks: nd.num(((((d or {}).get(ks[0]) or {}).get(ks[1]) or {}).get("american")))
    for it in od.get("items", []):
        h, w = it.get("homeTeamOdds") or {}, it.get("awayTeamOdds") or {}; cur = it.get("current") or {}
        rows.append(dict(base, provider=it.get("provider", {}).get("name"), provider_id=it.get("provider", {}).get("id"),
                         home_pl=am(h, "current", "pointSpread") if h.get("current") else nd.num(it.get("spread")),
                         home_pl_odds=am(h, "current", "spread"), away_pl_odds=am(w, "current", "spread"),
                         total=nd.num((cur.get("total") or {}).get("american")) if cur else nd.num(it.get("overUnder")),
                         over_odds=nd.num((cur.get("over") or {}).get("american")) if cur else nd.num(it.get("overOdds")),
                         under_odds=nd.num((cur.get("under") or {}).get("american")) if cur else nd.num(it.get("underOdds")),
                         home_ml=am(h, "current", "moneyLine") if h.get("current") else nd.num(h.get("moneyLine")),
                         away_ml=am(w, "current", "moneyLine") if w.get("current") else nd.num(w.get("moneyLine"))))
    return rows


def an_rows(live_games):
    rows = []
    for period in AN_PERIODS:        # one request per period: Action Network returns a different set for each
        try:
            d = research._an_get(f"https://api.actionnetwork.com/web/v2/scoreboard/nhl?bookIds={','.join(map(str, AN_BOOKS))}"
                                 f"&periods={period}")
        except Exception as e:
            print("Action Network unavailable:", period, type(e).__name__); continue
        for g in d.get("games", []):
            t = {x["id"]: (nd.FULL.get(x.get("full_name")) or nd.code(x.get("abbr"))) for x in g.get("teams", [])}
            base = live_games.get((t.get(g["home_team_id"]), t.get(g["away_team_id"])))
            if base is None: continue
            for bid, m in (g.get("markets") or {}).items():
                for per, mk in (m or {}).items():
                    for typ, outs in (mk or {}).items():
                        for o in outs or []:
                            side = o.get("side"); typ_ = typ
                            if typ == "core_bet_type_6_team_score":
                                typ_ = "team_total"; side = f"{'home' if o.get('team_id') == g['home_team_id'] else 'away'}_{side}"
                            rows.append(dict(base, book=AN_BOOKS.get(int(bid), bid), period=per, market=typ_, side=side,
                                             value=o.get("value"), odds=o.get("odds"), is_live=o.get("is_live"),
                                             line_status=o.get("line_status")))
    seen, out = set(), []
    for r in rows:
        k = (r["espn_event_id"], r["book"], r["period"], r["market"], r["side"])
        if k in seen: continue
        seen.add(k); out.append(r)
    return out


def main():
    live, soon = [], False
    for ev in espn_games():
        comp = ev["competitions"][0]; state = comp.get("status", {}).get("type", {}).get("state")
        start = pd.to_datetime(comp.get("date"), utc=True).tz_convert(ET).tz_localize(None)
        if state == "in" or (INCLUDE_FINAL and state == "post" and (NOW - start) < pd.Timedelta(hours=30)): live.append(ev)
        elif state == "pre" and pd.Timedelta(minutes=-45) <= start - NOW <= pd.Timedelta(minutes=45): soon = True
    if not live:
        print(f"{NOW:%a %H:%M} ET: no NHL game in progress" + ("; one starts soon." if soon else "."))
        return 2 if soon else 3
    research.init(W)
    sit, eo, keys = [], [], {}
    for ev in live:
        s = situation_row(ev); sit.append(s)
        base = {k: s[k] for k in ("seen_at_et", "espn_event_id", "date", "away", "home", "period", "clock", "away_score", "home_score")}
        eo += espn_odds_rows(ev, base); keys[(s["home"], s["away"])] = base
    bk = an_rows(keys)
    n = {}
    for name, rows, key, vals in (
            ("situation", sit, ["espn_event_id"], ["state", "period", "clock", "away_score", "home_score", "away_saves", "home_saves", "last_play"]),
            ("espn_odds", eo, ["espn_event_id", "provider"], ["home_pl", "home_pl_odds", "away_pl_odds", "total", "over_odds", "under_odds", "home_ml", "away_ml"]),
            ("books", bk, ["espn_event_id", "book", "period", "market", "side"], ["value", "odds", "is_live", "line_status"])):
        by_day = {}
        for r in rows: by_day.setdefault(r["date"], []).append(r)
        n[name] = 0
        for day, rr in by_day.items():
            d = os.path.join(W, "research", "live", day); os.makedirs(d, exist_ok=True)
            n[name] += research._append_changed(os.path.join(d, f"{name}.csv"), rr, key, vals)
    print(f"{NOW:%a %H:%M:%S} ET: {len(live)} games in progress; new rows: {n}; live prices this poll: {sum(1 for r in bk if r.get('is_live'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
