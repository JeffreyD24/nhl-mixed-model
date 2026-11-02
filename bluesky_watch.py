"""
Bluesky watcher (Nov 2, 2026; ported from the NBA tracker): new posts from the NHL reporters in
research/media/bluesky_watch.csv, every minute between the 5-minute checks (alert_loop.sh).

- Saves every new post (time posted, time first seen, reporter, team, text) to research/bluesky/YYYY-MM-DD.csv, flagging
  goalie / lineup / injury posts, the players they name, the starting goalie they report and any clear decision.
- Starting goalies (the biggest single-player effect in the backtests): a post naming a team's goalie with "will start",
  "gets the start", "in goal tonight"... goes to state/goalie_news.json, as "confirmed" (no hedge word) or "expected"
  ("expected to start", "first off the ice"). alert.py uses a confirmed reporter starter until ESPN confirms one, and an
  expected one when ESPN lists nobody.
- Skaters: clear decisions in one sentence with the player's name and no hedge ("out tonight", "will not play", "scratched",
  "will play", "returns tonight", "draws back in") go to state/news_overrides.json for that day's game.
- Goalie news that's confirmed or names someone other than the model's most likely starter, and skater decisions about a
  regular worth 0.25+, run a full check at once (exit code 10): if the news opens an edge, alert.py sends the bet alert.
  The news itself is logged, not pushed (NEWS_PUSH; phone alerts are bets only since Nov 1, 2026).
- Bluesky's public API (no login, free).

  python bluesky_watch.py WORKDIR
"""
import os, sys, json, re, time, urllib.request, urllib.parse
from zoneinfo import ZoneInfo
import pandas as pd

W = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
sys.path.insert(0, W)
STATE, R = os.path.join(W, "state"), os.path.join(W, "research")
API = "https://public.api.bsky.app/xrpc/"
ET = ZoneInfo("America/New_York")
NEWS_PUSH = False          # push goalie news / skater decisions to the phone (off: bets only, as BET_ONLY in alert.py)
SKATER_NEWS = 0.25         # a skater decision about a regular worth this much (model value) runs a full check at once
MAX_AGE_MIN = 120          # ignore posts older than this when first seen (e.g. after the watcher was off)

RELEVANT = re.compile(
    r"\b(goalie|goaltender|netminder|in goal|in net|crease|start\w*|nod|lineup|lines|scratch\w*|out|will play|won'?t play|"
    r"injur\w*|day[- ]to[- ]day|ir|ltir|upper[- ]body|lower[- ]body|illness|returns?|back in|dress\w*|game[- ]time|"
    r"questionable|doubtful|morning skate|off the ice|pregame|warmups?|sidelined|miss\w*|surgery|concussion|recall\w*|call(?:ed)? up)\b", re.I)
START_RX = re.compile(
    r"\b(will start|starts? (?:tonight|today|vs\.?|against|in goal|in net|for)|gets? the (?:start|nod|call)|"
    r"(?:is|will be) (?:in goal|in net|between the pipes|the starter)|in (?:goal|net) (?:tonight|today|for|vs\.?|against)|"
    r"starting (?:in goal|in net|tonight|today|goalie|goaltender|netminder)|confirmed (?:as )?(?:the )?start\w*|"
    r"tonight'?s starter|starter tonight|makes? (?:his|her) (?:\w+ )?(?:nhl )?(?:debut|start)|"
    r"first (?:goalie )?off the ice|led the \w+ (?:off|onto) the ice|lead (?:goalie )?off)\b", re.I)
TELL_RX = re.compile(r"\b(first (?:goalie )?off the ice|led the \w+ (?:off|onto) the ice|lead (?:goalie )?off)\b", re.I)
OUT_RX = re.compile(r"\b(ruled out|will not play|won'?t play|not playing|(?:is|are) out\b(?! of)|will be out\b(?! of)|out tonight|"
                    r"scratch(?:ed)?|healthy scratch|won'?t dress|will not dress|will miss|sidelined|placed on (?:ir|ltir|injured reserve)|"
                    r"out (?:for|vs\.?|against) (?:tonight|today|the game))\b", re.I)
IN_RX = re.compile(r"\b(will play|is playing|will return|returns tonight|will dress|draws? back in|back in the lineup|in the lineup|"
                   r"(?:is|will be) available|good to go|cleared to play|will make (?:his|her) (?:season )?debut|activated)\b", re.I)
HEDGE_RX = re.compile(r"\b(questionable|doubtful|game[- ]time|likely|unlikely|could|might|may|hope|hoping|expected|expects|"
                      r"if he|whether|unclear|uncertain|undecided|probabl\w*|projected|anticipat\w*|should|presumably|"
                      r"looks like|appears|plans? to|trending|tbd|believe\w*)\b", re.I)
SENT = re.compile(r"(?<=[.!?;])\s+|\n")


def api(method, **q):
    url = API + method + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nhl-mixed-model research"}), timeout=15) as r:
        return json.loads(r.read())


def norm(s): return re.sub(r"[^a-z' ]", " ", str(s).lower().replace(".", "")).strip()


def team_code(name):
    import nhl_data as nd
    if not name or name == "League-wide": return ""
    t = name.lower()
    for c, ws in nd.NAMES.items():
        if c == t or any(w == t or w in t for w in ws): return c
    return ""


def index(now):
    """games not started in the saved model files, with each team's goalie candidates and regular skaters:
    {'games': [dict(game, date, side, team, goalies {id: name}, top (id, name, share), skaters {id: (name, value)})]}"""
    models = sorted(f for f in os.listdir(STATE) if f.startswith("model_") and f.endswith(".json") and f[6:16] >= str(now.date()))
    gp = os.path.join(R, "goalies.csv")
    seen_g = pd.read_csv(gp) if os.path.exists(gp) else pd.DataFrame(columns=["team", "goalie_id", "goalie", "date"])
    seen_g = seen_g[pd.to_datetime(seen_g.date, errors="coerce") >= now - pd.Timedelta(days=40)].dropna(subset=["goalie_id"])
    out = []
    for mf in models:
        Mall = json.load(open(os.path.join(STATE, mf)))
        lead = "goals" if "goals" in Mall["models"] else next(iter(Mall["models"]))
        M = Mall["models"][lead]; gname = {int(k): v for k, v in M.get("goalie_names", {}).items()}
        for g in M["games"]:
            if pd.Timestamp(g["tip_et"]) <= now: continue
            for side in ("home", "away"):
                team = g[side]
                mix = {int(k): w for k, w in g[f"{side}_gmix"].items()}
                gl = {k: gname.get(k, "") for k in mix}
                for r in seen_g[seen_g.team == team].itertuples():
                    gl.setdefault(int(r.goalie_id), r.goalie)
                top = max(mix.items(), key=lambda x: x[1]) if mix else (None, 0)
                out.append(dict(game=g, date=Mall["date"], side=side, team=team, goalies={k: v for k, v in gl.items() if v},
                                top=(top[0], gname.get(top[0], ""), top[1]),
                                skaters={int(pid): (name, val) for pid, (name, val, _) in g[f"{side}_regulars"].items()}))
    return out


def who(sent, team, I):
    """[(entry, kind 'G'/'S', player id, name)] named in a sentence: full name anywhere; last name alone for the reporter's team"""
    t = f" {norm(sent)} "; out = []
    for e in I:
        own = bool(team) and e["team"] == team
        for kind, pool in (("G", e["goalies"]), ("S", {k: v[0] for k, v in e["skaters"].items()})):
            for pid, name in pool.items():
                n = norm(name); last = n.split()[-1] if n else ""
                if (n and f" {n} " in t) or (own and len(last) > 3 and f" {last} " in t and
                                               (kind == "G" or abs(e["skaters"][pid][1]) >= SKATER_NEWS)):
                    out.append((e, kind, pid, name))
    first = {}
    for x in out:                      # a player can appear in two upcoming games: keep his next one
        k = (x[1], x[2])
        if k not in first or x[0]["game"]["tip_et"] < first[k][0]["game"]["tip_et"]: first[k] = x
    return list(first.values())


def read_post(text, team, I):
    """(names, goalie starts [(entry, id, name, level)], decisions [(entry, id, name, 'Out'/'Available')])"""
    names, starts, dec = [], [], []
    for sent in SENT.split(text):
        w = who(sent, team, I)
        if not w: continue
        names += [x[3] for x in w if x[3] not in names]
        hedge = bool(HEDGE_RX.search(sent))
        if START_RX.search(sent):
            gs = [x for x in w if x[1] == "G"]
            if len(gs) == 1 or len({x[0]["team"] for x in gs}) == len(gs):     # one goalie per team named as starting
                lvl = "expected" if hedge or TELL_RX.search(sent) else "confirmed"
                starts += [(e, pid, name, lvl) for e, _, pid, name in gs]
        if hedge: continue
        o, i = bool(OUT_RX.search(sent)), bool(IN_RX.search(sent))
        if o != i:
            dec += [(e, pid, name, "Out" if o else "Available") for e, kind, pid, name in w if kind == "S"]
    return names, starts, dec


def process(posts, watch, seen, I, now, gnews=None, overrides=None):
    """posts: [(handle, post dict)]. Returns (rows to log, news worth a full check now); updates seen / gnews / overrides."""
    rows, urgent = [], []
    gnews = {} if gnews is None else gnews; overrides = {} if overrides is None else overrides
    for handle, p in posts:
        rec = p.get("record") or {}; uri = p.get("uri", "")
        if not uri or uri in seen.get(handle, []): continue
        created = pd.Timestamp(rec.get("createdAt")).tz_convert(ET).tz_localize(None) if rec.get("createdAt") else now
        seen.setdefault(handle, []).append(uri)
        if now - created > pd.Timedelta(minutes=MAX_AGE_MIN): continue
        w = watch.get(handle, {}); team = w.get("team_code") or team_code(w.get("team", ""))
        text = (rec.get("text") or "").replace("\n", " ").strip()
        rel = bool(RELEVANT.search(text))
        names, starts, dec = read_post(text, team, I) if rel else ([], [], [])
        url = f"https://bsky.app/profile/{handle}/post/{uri.rsplit('/', 1)[-1]}"
        rows.append(dict(seen_at_et=str(now)[:19], posted_at_et=str(created)[:19], lag_min=round((now - created).total_seconds() / 60, 1),
                         handle=handle, reporter=w.get("name", ""), team=w.get("team", ""), relevant=rel, players="; ".join(names),
                         goalie_starts="; ".join(f"{e['team'].upper()} {n} ({lvl})" for e, _, n, lvl in starts),
                         decisions="; ".join(f"{n} {st}" for _, _, n, st in dec), text=text[:500], url=url))
        src = dict(reporter=w.get("name", handle), posted_at_et=str(created)[:19], seen_at_et=str(now)[:19], url=url, text=text[:300])
        for e, pid, name, lvl in starts:
            gk = f"{e['game']['game_id']}|{e['side']}"; old = gnews.get(gk)
            if old and old["goalie_id"] == pid and (old["level"] == lvl or lvl == "expected"): continue
            if old and old["level"] == "confirmed" and lvl == "expected": continue   # a hedge doesn't undo a confirmation
            surprise = e["top"][0] is not None and pid != e["top"][0]
            gnews[gk] = dict(goalie_id=pid, goalie=name, level=lvl, team=e["team"], date=e["date"], tip_et=e["game"]["tip_et"],
                             model_expected=e["top"][1], model_expected_share=round(e["top"][2], 2), surprise=surprise, **src)
            if lvl == "confirmed" or surprise:
                urgent.append(f"{e['team'].upper()} goalie {name} ({lvl}{', not the model goalie ' + e['top'][1] if surprise else ''}; {src['reporter']})")
        for e, pid, name, st in dec:
            ok = f"{e['date']}|{e['team']}|{pid}"
            if overrides.get(ok, {}).get("status") == st: continue
            val = e["skaters"][pid][1]
            overrides[ok] = dict(status=st, player=name, game_id=e["game"]["game_id"], value=round(val, 3), **src)
            if abs(val) >= SKATER_NEWS: urgent.append(f"{name} {st.upper()} ({src['reporter']})")
    return rows, urgent


def main():
    now = pd.Timestamp.now(tz=ET).tz_localize(None)
    wpath = os.path.join(R, "media", "bluesky_watch.csv")
    if not os.path.exists(wpath): print("No watch list."); return 0
    watch = {r.bluesky_handle: dict(name=r.name, team=r.team, team_code=getattr(r, "team_code", ""))
             for r in pd.read_csv(wpath).fillna("").itertuples()}
    spath = os.path.join(STATE, "bluesky_seen.json")
    seen = json.load(open(spath)) if os.path.exists(spath) else {}
    posts, errors = [], 0
    for h in watch:
        try:
            feed = api("app.bsky.feed.getAuthorFeed", actor=h, limit=15, filter="posts_and_author_threads")
            posts += [(h, i["post"]) for i in feed.get("feed", []) if i.get("post") and not i.get("reason")]    # skip reposts
        except Exception:
            errors += 1
        time.sleep(0.12)
    try:
        I = index(now)
    except Exception as e:
        print("Game index unavailable:", type(e).__name__); I = []
    gpath, opath = os.path.join(STATE, "goalie_news.json"), os.path.join(STATE, "news_overrides.json")
    gnews = json.load(open(gpath)) if os.path.exists(gpath) else {}
    overrides = json.load(open(opath)) if os.path.exists(opath) else {}
    rows, urgent = process(posts, watch, seen, I, now, gnews, overrides)
    keep = str((now - pd.Timedelta(days=2)).date())
    gnews = {k: v for k, v in gnews.items() if v["date"] >= keep}
    overrides = {k: v for k, v in overrides.items() if k.split("|")[0] >= keep}
    json.dump(gnews, open(gpath, "w"), indent=1); json.dump(overrides, open(opath, "w"), indent=1)
    for h in seen: seen[h] = seen[h][-60:]
    json.dump(seen, open(spath, "w"))
    if rows:
        os.makedirs(os.path.join(R, "bluesky"), exist_ok=True)
        p = os.path.join(R, "bluesky", f"{now.date()}.csv")
        D = pd.DataFrame(rows)
        if os.path.exists(p):
            old = pd.read_csv(p)
            if list(old.columns) != list(D.columns): pd.concat([old, D], ignore_index=True).to_csv(p, index=False)
            else: D.to_csv(p, mode="a", header=False, index=False)
        else: D.to_csv(p, index=False)
    print(f"Bluesky: {len(watch)} reporters, {len(rows)} new posts ({sum(r['relevant'] for r in rows)} goalie/lineup/injury), "
          f"{errors} feeds unavailable.")
    for u in urgent: print("NEWS:", u)
    if urgent and NEWS_PUSH and os.environ.get("NTFY_TOPIC"):
        try:
            urllib.request.urlopen(urllib.request.Request(f"https://ntfy.sh/{os.environ['NTFY_TOPIC']}", data="\n".join(urgent).encode(),
                                                          method="POST", headers={"Title": "Reporter news", "Tags": "ice_hockey"}), timeout=15)
        except Exception as e:
            print("Alert not sent:", type(e).__name__)
    return 10 if urgent else 0


if __name__ == "__main__":
    sys.exit(main())
