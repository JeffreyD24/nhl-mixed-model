"""
One-time check: which reporters are active on Bluesky? Two sources:
  1. every beat writer / insider in research/media/<league>_media_list.csv, looked up by name;
  2. members of public Bluesky "starter packs" of NFL / NHL reporters (finds people the list doesn't have).
Uses Bluesky's public API (no login). Writes research/media/bluesky_check.csv (the list) and
research/media/bluesky_starterpacks.csv (starter-pack members, with the team their bio points to and recent activity).
  python tools/bluesky_check.py . nfl|nhl
"""
import os, sys, json, time, re, urllib.request, urllib.parse
import pandas as pd

W, LEAGUE = os.path.abspath(sys.argv[1]), sys.argv[2].lower()
API = "https://public.api.bsky.app/xrpc/"
MEDIA = os.path.join(W, "research", "media")
L = pd.read_csv(os.path.join(MEDIA, f"{LEAGUE}_media_list.csv")).fillna("")
P = L[L.category.isin(["Beat writer / team reporter", "National insider / news account"])]

NFL_NAMES = {"ari": ["cardinals", "arizona"], "atl": ["falcons", "atlanta"], "bal": ["ravens", "baltimore"], "buf": ["bills", "buffalo"],
             "car": ["panthers", "carolina"], "chi": ["bears", "chicago"], "cin": ["bengals", "cincinnati"], "cle": ["browns", "cleveland"],
             "dal": ["cowboys", "dallas"], "den": ["broncos", "denver"], "det": ["lions", "detroit"], "gb": ["packers", "green bay"],
             "hou": ["texans", "houston"], "ind": ["colts", "indianapolis", "indy"], "jax": ["jaguars", "jags", "jacksonville"],
             "kc": ["chiefs", "kansas city"], "lv": ["raiders", "las vegas"], "lac": ["chargers", "bolts"], "lar": ["rams"],
             "mia": ["dolphins", "miami"], "min": ["vikings", "minnesota"], "ne": ["patriots", "pats", "new england"],
             "no": ["saints", "new orleans"], "nyg": ["giants"], "nyj": ["jets"], "phi": ["eagles", "philadelphia", "philly"],
             "pit": ["steelers", "pittsburgh"], "sf": ["49ers", "niners", "san francisco"], "sea": ["seahawks", "seattle"],
             "tb": ["buccaneers", "bucs", "tampa bay"], "ten": ["titans", "tennessee"], "wsh": ["commanders", "washington"]}
if LEAGUE == "nhl":
    sys.path.insert(0, W); import nhl_data; NAMES = nhl_data.NAMES
    LEAGUE_RX = re.compile(r"\b(nhl|hockey|puck|goalie)\b", re.I)
    PACK_Q = ["NHL", "NHL reporters", "NHL beat writers", "hockey writers", "hockey media", "NHL insiders", "hockey reporters"]
else:
    NAMES = NFL_NAMES
    LEAGUE_RX = re.compile(r"\b(nfl|football)\b", re.I)
    PACK_Q = ["NFL", "NFL reporters", "NFL beat writers", "NFL media", "NFL insiders", "football writers", "NFL writers"]
JOB_RX = re.compile(r"\b(beat|reporter|writer|insider|covers?|covering|columnist|correspondent|journalist|host|analyst|editor|"
                    r"athletic|espn|sportsnet|tsn|newspaper|times|post|news|herald|tribune|journal)\b", re.I)
WORD = {c: re.compile(r"\b(" + "|".join(re.escape(w) for w in ws) + r")\b", re.I) for c, ws in NAMES.items()}


def get(method, **q):
    url = API + method + "?" + urllib.parse.urlencode(q)
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f"{LEAGUE}-mixed-model research"}), timeout=20) as r:
                return json.loads(r.read())
        except Exception as e:
            if k == 2: return {"error": str(e)[:100]}
            time.sleep(2 * (k + 1))


def norm(s): return re.sub(r"[^a-z]", "", s.lower())


def teams_in(text):
    return ",".join(c for c, rx in WORD.items() if rx.search(text))


def activity(actor):
    feed = get("app.bsky.feed.getAuthorFeed", actor=actor, limit=50, filter="posts_no_replies")
    dates = []
    for i in feed.get("feed", []):
        c = i.get("post", {}).get("record", {}).get("createdAt")
        if c and not i.get("reason"):
            d = pd.Timestamp(c); dates.append(d if d.tzinfo else d.tz_localize("UTC"))
    now = pd.Timestamp.now(tz="UTC")
    return (str(max(dates))[:16] if dates else ""), sum(1 for d in dates if now - d <= pd.Timedelta(days=14))


# ---- 1. names on the list
rows, found = [], set()
for r in P.itertuples():
    name = re.sub(r"\s*\(.*\)", "", r.name).strip()
    res = get("app.bsky.actor.searchActors", q=name, limit=10)
    best = None
    for a in res.get("actors", []) or []:
        dn = a.get("displayName") or ""; desc = a.get("description") or ""; handle = a.get("handle", "")
        score = 0
        if norm(dn) == norm(name): score += 3
        elif norm(name) in norm(dn) or norm(name.split()[-1]) in norm(handle): score += 1
        if LEAGUE_RX.search(desc + " " + dn): score += 2
        if r.team_code and WORD[r.team_code].search(desc + " " + dn): score += 2
        elif JOB_RX.search(desc): score += 1
        if score >= 4 and (best is None or score > best[0]): best = (score, a)
    out = dict(team=r.team, team_code=r.team_code, name=r.name, outlet=r.outlet, category=r.category, bluesky_handle="", did="",
               bluesky_name="", followers="", posts="", last_post_utc="", posts_last_14d="", match_score="", bio_teams="", bio="")
    if best:
        a = best[1]; found.add(a["did"])
        prof = get("app.bsky.actor.getProfile", actor=a["did"])
        last, n14 = activity(a["did"])
        bio = (a.get("description") or "").replace("\n", " ")
        out.update(bluesky_handle=a.get("handle"), did=a["did"], bluesky_name=a.get("displayName"), followers=prof.get("followersCount", ""),
                   posts=prof.get("postsCount", ""), last_post_utc=last, posts_last_14d=n14, match_score=best[0],
                   bio_teams=teams_in(bio + " " + (a.get("displayName") or "")), bio=bio[:200])
    rows.append(out); time.sleep(0.25)
    print(f"{r.team:14s} {r.name:28s} -> {out['bluesky_handle'] or '-'} {out['posts_last_14d']}", flush=True)
D = pd.DataFrame(rows)
D.to_csv(os.path.join(MEDIA, "bluesky_check.csv"), index=False)
f = D[D.bluesky_handle != ""]; act = f[pd.to_numeric(f.posts_last_14d, errors="coerce").fillna(0) >= 3]
print(f"\nList: on Bluesky {len(f)} of {len(D)}; posting regularly (3+ posts in the last 14 days): {len(act)}")

# ---- 2. starter packs of reporters
packs = {}
for q in PACK_Q:
    res = get("app.bsky.graph.searchStarterPacks", q=q, limit=25)
    if "error" in res: print("starter pack search failed:", q, res["error"]); continue
    for sp in res.get("starterPacks", []) or []:
        nm = (sp.get("record") or {}).get("name", "")
        desc = (sp.get("record") or {}).get("description", "")
        if LEAGUE_RX.search(nm + " " + desc) and re.search(r"(report|writ|beat|media|insider|journal|cover|news)", nm + " " + desc, re.I):
            packs[sp["uri"]] = nm
    time.sleep(0.3)
print(f"\nStarter packs found: {len(packs)}")
members = {}
for uri, nm in packs.items():
    sp = get("app.bsky.graph.getStarterPack", starterPack=uri)
    lst = ((sp.get("starterPack") or {}).get("list") or {}).get("uri")
    cursor, n = None, 0
    while lst and n < 6:
        q = dict(list=lst, limit=100) | ({"cursor": cursor} if cursor else {})
        res = get("app.bsky.graph.getList", **q); n += 1
        for it in res.get("items", []) or []:
            s = it.get("subject") or {}
            m = members.setdefault(s.get("did"), dict(did=s.get("did"), handle=s.get("handle"), name=s.get("displayName") or "",
                                                      bio=(s.get("description") or "").replace("\n", " "), packs=set()))
            m["packs"].add(nm)
        cursor = res.get("cursor")
        if not cursor: break
    print(f"  {nm[:60]:60s} members so far {len(members)}", flush=True)
    time.sleep(0.3)
rows = []
for did, m in members.items():
    txt = m["bio"] + " " + m["name"]
    tm = teams_in(txt)
    if not (tm or (LEAGUE_RX.search(txt) and JOB_RX.search(txt))): continue
    last, n14 = activity(did); time.sleep(0.15)
    rows.append(dict(handle=m["handle"], did=did, name=m["name"], bio_teams=tm, on_list=did in found, last_post_utc=last,
                     posts_last_14d=n14, packs="; ".join(sorted(m["packs"]))[:200], bio=m["bio"][:240]))
S = pd.DataFrame(rows).sort_values("posts_last_14d", ascending=False) if rows else pd.DataFrame()
S.to_csv(os.path.join(MEDIA, "bluesky_starterpacks.csv"), index=False)
print(f"Starter-pack members with a team or reporter bio: {len(S)}; posting 3+ in 14 days: "
      f"{int((pd.to_numeric(S.get('posts_last_14d', pd.Series(dtype=float))) >= 3).sum()) if len(S) else 0}")
