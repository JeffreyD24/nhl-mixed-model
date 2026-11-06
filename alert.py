"""
Intraday line check. Runs every 5 minutes (see alert_loop.sh).

  python alert.py WORKDIR [--force] [--test]

Uses state/model_YYYY-MM-DD.json from the last tracker run (no refitting). Each check: pulls ESPN's probable/confirmed
starting goalies and injury list, re-predicts today's and tomorrow's games, pulls the current DraftKings prices from ESPN,
and sends one ntfy push per game and market when the model's expected value at the current price is >= THRESHOLD.
Every alert is logged to state/alerts.csv and graded by the next morning run.
"""
import os, sys, json, urllib.request, urllib.parse, datetime as dt
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

W = os.path.abspath(sys.argv[1]); FORCE = "--force" in sys.argv
sys.path.insert(0, W)
import nhl_data as nd                                    # noqa: E402
import nhl_mixed_model as nm                             # noqa: E402
import espn                                              # noqa: E402
import nhl_travel                                        # noqa: E402
import fanduel                                           # noqa: E402

REMIND_EVERY_MIN = 30               # Nov 2, 2026: an alerted bet still not logged and still a bet -> REMINDER every 30 min,
REMIND_HOURS = (6, 20)              #   reminders 6 AM - 8 PM ET only (Jeffrey, Nov 5, 2026 18:16); first-time BET alerts, bail-outs and DON'T BETs go out 24 hours a day
REMIND_GAPS = ((24, 240), (6, 120), (2, 60))   # Nov 4, 2026: reminders spaced by time to start: 24h+ every 4 h, 6-24 h every 2 h,
                                              #   2-6 h hourly, under 2 h every REMIND_EVERY_MIN (an opener alerted the day before
                                              #   no longer sends ~25 reminders)

def ntfy_open(req, tries=4):
    """urlopen for ntfy pushes with retries (Nov 6, 2026): ntfy.sh answers HTTP 429 to bursts, and a refused push used to be lost.
    Retries after 5, 15, 30 s on 429 / 5xx / network errors; the last error is raised as before."""
    import time, urllib.error
    for i in range(tries):
        try:
            return urllib.request.urlopen(req, timeout=20)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500 or i == tries - 1: raise
            print(f"ntfy refused (HTTP {e.code}); retrying")
        except OSError:
            if i == tries - 1: raise
            print("ntfy unreachable; retrying")
        time.sleep((5, 15, 30)[min(i, 2)])

def remind_gap_min(tip, now):
    try: h = (pd.Timestamp(tip) - now).total_seconds() / 3600
    except Exception: return REMIND_EVERY_MIN
    return next((m for hh, m in REMIND_GAPS if h > hh), REMIND_EVERY_MIN)
ML_BLEND = 0.55                     # moneyline win chance = 55% shot model + 45% DraftKings' no-vig opener (approved Nov 2, 2026;
ML_THRESHOLD = 0.04                 #   backtests/IDEA_TESTS.md: +158.1u on 1,221 bets 2021-26, every season +19u or better), EV 4%+ near the opener
THRESHOLD = 0.06                    # expected value needed while the price is at (or within 1.5 win-% points of) its opening price
ML_EV_SPLIT = 0.09                  # Nov 4, 2026 (user decision after spreads step 1): moneyline bets are recorded and graded in two
                                    #   buckets, EV 4-9% and EV 9%+ (2021-26 at honest timing: 4-9% CLV -0.42%, 9%+ CLV +2.22%). Both are
                                    #   still BET alerts; bet_record.py splits the record. research/spreads/STEP1_NHL_RESULTS.md

                                    #   (overs; second-chance moneylines). Puck line: THRESHOLD_PL.
THRESHOLD_PL = 0.09                 # Nov 4, 2026 (approved; analysis/rule_audit_nhl_output.txt section 5): puck line bar 6% -> 9%.
                                    #   2021-26 at DK openers, b2b removed: EV 6-9% 514 bets -11.1u (4 of 5 seasons negative);
                                    #   EV 9%+ 754 bets +90.2u. Chosen on the same seasons: re-test after 2026-27. Puck lines at
                                    #   EV 6-9% near the opener are still logged as TEST rows (not pushed) for that re-test.
THRESHOLD_MOVED = 0.09              # needed once the price has moved more than that: in the backtests the edge mostly disappears
BET_ONLY = True                     # phone alerts only for bets and the DON'T BET follow-up (Nov 1, 2026); everything
                                    # else (cautions, info-only, market agrees, line jumps) is still logged, just not pushed
MOVED_SKIP = "price moved off the opening number (info only)"
NEAR_OPEN = 0.015                   #   as prices move toward the close (shot model +9% ROI at open, +2% halfway, -2% at close)
OPEN_ONLY_LONGSHOTS = {"goals": 150}  # model -> bets priced at this or longer (+150) are alerted ONLY at/near the opening price
                                     #   (within NEAR_OPEN), labeled "OPENING PRICE ONLY" with the shortest price still worth taking.
                                     #   The goals model's underdog win chances run ~5 points high: its +150-and-longer bets made
                                     #   +13.5u on 641 bets at the open but lost once the price moved (backtests/IDEA_TESTS.md).
                                     #   The shot model's long shots are calibrated, so they get normal alerts. Scorecard unchanged.
ALERT_MARKETS = ("moneyline", "puck line", "total")   # totals: OVERS ONLY (approved Nov 2, 2026; backtests/IDEA_TESTS.md "NHL totals rework":
TOTAL_SIDES = ("over",)                               #   overs at the opener EV 6%+ +57.6u on 515, all five seasons positive; unders lose)
MAX_MOVE = 5.0                      # caution when the home win chance implied by the moneyline moved this many points AGAINST the bet since open
JUMP_WINDOW_MIN = 60                # a "jump" is a move within this many minutes
JUMP_LOG_PROB = 3.0                 # log moneyline moves of at least this many win-probability points (and any change in the total)
JUMP_ALERT_PROB = 5.0               # send a "Line jump" notification at this size (and for totals moving a full goal)
P_MISS = {"Out": 1.0, "Injured Reserve": 1.0, "Long Term Injured Reserve": 1.0, "Suspension": 1.0, "Suspended": 1.0, "Day-To-Day": 0.5}
SHORT = {"xg": "Shot model", "goals": "Goals model"}
ALERT_MODELS = ("xg",)   # Nov 1, 2026: only the shot model alerts. Backtest 2025-26 at opening prices: the goals model's own
                         # bets (ones the shot model didn't make) lost -16.6u on 1,026 bets, in both seasons; its profit came
                         # only from bets the shot model also made. The goals model still runs and is logged (research/model).
WINDOW = None                       # None = check all day; or (16, 0, 19, 0) for 4:00-7:00 PM ET
ET = ZoneInfo("America/New_York")
STATE = os.path.join(W, "state")
NOW = pd.Timestamp(dt.datetime.now(ET).replace(tzinfo=None))
TODAY = NOW.normalize()


def in_window():
    if WINDOW is None: return True
    start = TODAY + pd.Timedelta(hours=WINDOW[0], minutes=WINDOW[1]); end = TODAY + pd.Timedelta(hours=WINDOW[2], minutes=WINDOW[3])
    return start <= NOW < end


PIN_URL = "https://raw.githubusercontent.com/JeffreyD24/nba-mixed-model/main/state/pinnacle_now.json"   # live Pinnacle recorder (nba repo)
PIN_NAME = {"Anaheim Ducks": "ana", "Arizona Coyotes": "uta", "Utah Hockey Club": "uta", "Utah Mammoth": "uta", "Boston Bruins": "bos",
            "Buffalo Sabres": "buf", "Carolina Hurricanes": "car", "Columbus Blue Jackets": "cbj", "Calgary Flames": "cgy",
            "Chicago Blackhawks": "chi", "Colorado Avalanche": "col", "Dallas Stars": "dal", "Detroit Red Wings": "det",
            "Edmonton Oilers": "edm", "Florida Panthers": "fla", "Los Angeles Kings": "la", "Minnesota Wild": "min",
            "Montréal Canadiens": "mtl", "Montreal Canadiens": "mtl", "New Jersey Devils": "nj", "Nashville Predators": "nsh",
            "New York Islanders": "nyi", "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
            "Pittsburgh Penguins": "pit", "Seattle Kraken": "sea", "San Jose Sharks": "sj", "St Louis Blues": "stl", "St. Louis Blues": "stl",
            "Tampa Bay Lightning": "tb", "Toronto Maple Leafs": "tor", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk",
            "Winnipeg Jets": "wpg", "Washington Capitals": "wsh"}
USE_PINNACLE_RULE = True    # approved Nov 2, 2026: no bet when Pinnacle has ALREADY posted at alert time and disagrees
PIN_DISAGREE = 0.005     # Pinnacle's first moneyline gives our side 0.5+ win-% points less than DraftKings' opener -> no bet.
                         #   Rule audit Nov 4 (live blend, bettable timing): Pinnacle up at DK's open and disagreeing 27 bets -8.8u
                         #   (small sample). The old "405 bets -42u" was the raw model graded at DK's opener with Pinnacle's
                         #   LATER price (look-ahead); under the live blend that group made +5.4u.
SKIP_B2B = True          # no bet on a team playing the second night of a back-to-back, PUCK LINE ONLY since Nov 4, 2026
SKIP_B2B_MARKETS = ("puck line",)   # (rule audit, 2021-26 at DK openers: puck line bets on b2b teams 137 bets, won 35%, -37.3u,
                         #   4 of 5 seasons negative; moneyline under the live blend + travel adjustment 77 bets +0.9u, i.e. the
                         #   travel adjustment already prices the b2b, so the moneyline is no longer skipped)
PREFER_ML = True         # Nov 4, 2026: one bet per game -> the MONEYLINE when it qualifies. The old rule compared blended ML EV with
                         #   raw puck line EV and picked the puck line 79% of the time; in those 597 games 2021-26 always-ML made
                         #   +69.7u vs +54.2u as picked (dropped ML legs +57.3u on 470). The puck line leg is logged as a TEST row.
PIN_FOLLOWUP = False     # Nov 4, 2026: no DON'T BET when Pinnacle posts after the alert and disagrees. At the price still available
                         #   when Pinnacle posts, those bets made +9.1u on 187 (2021-26, live blend): the follow-up saved nothing.
                         #   The at-alert-time Pinnacle rule (USE_PINNACLE_RULE) stays.
GOALIE_OVER_TEST = True  # Nov 4, 2026 (TEST only, never pushed): once both starters are confirmed, an over with EV 6%+ at DK's current
GOALIE_OVER_EV = 0.06    #   price (shot model re-run with the confirmed starters) on a game with no over alerted at the opener is
                         #   logged once per game to state/ovr_goalie_test.csv. Backtest (analysis/nhl_totals_research.py s.2a, DK price
                         #   1 h before puck drop 2021-26): 162 bets +31.1u, 0 of 5 seasons negative; no out-of-sample check possible.
GOALIE_RECHECK_TEST = True   # Nov 4, 2026 (user approved; TEST only, never pushed): spreads step 3 (research/spreads/STEP3_NHL_GOALIE_RESULTS.md).
GR_ML_EV, GR_PL_EV = 0.04, 0.09   # The first check after BOTH starters are confirmed logs one row per game for the moneyline and one for the
                             #   puck line to state/goalie_recheck_test.csv: shot model with the confirmed starters and the live skater
                             #   picture (injury feed + reporters, nothing from the box score), at DraftKings' price that minute. Moneyline
                             #   chance = 0.55 x model + 0.45 x DK no-vig NOW (as tested); puck line raw, +/-1.5 only. Every game is logged;
                             #   `qualifies` marks ML EV 4%+ / PL EV 9%+ (PL: not on a b2b team). Graded by tracker.py with CLV to the close.
                             #   Purpose: history can't show when starters became public; this measures it live.
REST_TEST = True         # Nov 4, 2026 (TEST only, never pushed): games where exactly one team is on the 2nd night of a back-to-back.
                         #   The RESTED team's moneyline at DK's opening price is logged once per game to state/rest_b2b_test.csv and graded
                         #   by tracker.py (market-only rule, no model). Statistics catalog X02: 2016-22 holdout 1,520 bets +2.2%,
                         #   2024-26 538 bets +7.8%; the closing price moved toward the rested team in every season.
ML_HOLD_NEAR_ALERT = True   # Nov 4, 2026: no moneyline DON'T BET just because EV dipped under the bar while DK's price is still
                         #   within NEAR_OPEN (1.5 win-% pts) of the alerted price (those bets halfway to puck drop: 113 bets
                         #   +26.0u, 4 of 5 seasons positive). Bigger moneyline moves and overs keep the DON'T BET.


PIN_SEEN = {}            # (home, away) -> when the recorder first saw Pinnacle's price (UTC)
SECOND_CHANCE = True     # Nov 2, 2026 (approved): moneyline bets the model missed at the opener (EV under 6% there) that are 6%+ at
SC_WINDOW_MIN = 60       #   DraftKings' price when Pinnacle first posts (within this many minutes) and Pinnacle agrees or matches.
                         #   Shot model 2021-26: 172 bets, +17.2u (+10.0%), positive all five seasons (tracker analysis/sharp_nhl.py G)


def pinnacle_first():
    """{(home, away): Pinnacle's first no-vig home win chance} from the live recorder; {} if unavailable"""
    try:
        with urllib.request.urlopen(PIN_URL, timeout=20) as r: js = json.loads(r.read())
    except Exception as e:
        print("Pinnacle prices unavailable:", type(e).__name__); return {}
    out = {}
    for ev in js.get("nhl", {}).values():
        h, a = PIN_NAME.get(ev.get("home")), PIN_NAME.get(ev.get("away")); f = ev.get("first", {})
        ph, pa = f.get(f"h2h|{ev.get('home')}", [None])[0], f.get(f"h2h|{ev.get('away')}", [None])[0]
        if h and a and ph is not None and pa is not None:
            out[(h, a)] = fair(ph, pa); PIN_SEEN[(h, a)] = ev.get("first_seen_utc")
    return out


def fair(a, b):
    if pd.isna(a) or pd.isna(b): return np.nan
    ia, ib = 1 / espn.nd_dec(a), 1 / espn.nd_dec(b); return ia / (ia + ib)


def log_link(date, away, home, market, pick, line, odds):
    repo = os.environ.get("GITHUB_REPOSITORY", "JeffreyD24/nhl-mixed-model")
    desc = f"{pick.upper()} {'ML' if market == 'moneyline' else line}"
    q = dict(template="log-bet.yml", title=f"Bet: {desc} {away.upper()} @ {home.upper()} {date}", game_date=date, away=away.upper(),
             home=home.upper(), market=market, pick=pick.upper() if market != "total" else pick, line=line, odds=odds)
    return f"https://github.com/{repo}/issues/new?" + urllib.parse.urlencode(q)


DK_NHL = "https://sportsbook.draftkings.com/leagues/hockey/nhl"


def notify(title, body, priority="high", tags="ice_hockey", link=None, dk=None, kind="info", fd=None, best=None):
    """kind: 'bet', 'stop' (DON'T BET follow-up), 'test', or 'info' (not pushed while BET_ONLY).
    dk / fd: DraftKings / FanDuel links (better book first, from fanduel.compare). link: unused since Nov 4, 2026 (Log button removed)."""
    if BET_ONLY and kind not in ("bet", "stop", "test"):
        print("Logged only (not pushed):", title); return "quiet"     # kept in alerts.csv, not retried
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC not set; would have sent:", title, "|", body, "| DK:", dk or "-", "| FD:", fd or "-"); return False
    actions = fanduel.actions(dk, fd, best)
    if best == "FanDuel" and "BEST AT FANDUEL" not in title: title += " | BEST AT FANDUEL"     # every alert type (Fable review)
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=body.encode("utf-8"), method="POST",
                                 headers={"Title": title.encode("ascii", "ignore").decode(), "Priority": priority, "Tags": tags,
                                          **({"Actions": actions} if actions else {})})
    with ntfy_open(req) as resp:
        try: mid = json.loads(resp.read()).get("id")
        except Exception: mid = None
        print(f"ntfy accepted (HTTP {resp.status}, id {mid}, {len(body.encode('utf-8'))} bytes): {title[:70]}")
    return True


def load_models(path):
    """model file for one day; older single-model files are wrapped as the goals model"""
    M = json.load(open(path))
    if "models" not in M:
        M = dict(date=M["date"], made_at_et=M.get("made_at_et", ""), active="goals", models={"goals": M})
    return M


def fill_from_action_network(L, day):
    """ESPN can trail DraftKings by a few minutes when a line first posts. For games where ESPN has no DraftKings price
    yet, use DraftKings' price from Action Network (as both the current and the opening price: it has just opened)."""
    try:
        A = pd.DataFrame(nd.an_lines(day, books=(68,)))
    except Exception:
        return L
    if not len(A) or not len(L): return L
    A = A[A.book_id == 68].set_index(["home", "away"])
    L = L.copy()
    for i, r in L.iterrows():
        if not pd.isna(r.get("current_home_ml", np.nan)) or (r.home, r.away) not in A.index: continue
        a = A.loc[(r.home, r.away)]
        a = a.iloc[0] if isinstance(a, pd.DataFrame) else a
        if pd.isna(a.home_ml): continue
        for k in espn.MARKET_COLS:
            L.at[i, f"current_{k}"] = a[k]; L.at[i, f"open_{k}"] = a[k]
        L.at[i, "book"] = "DraftKings (via Action Network)"
        print(f"Using Action Network's new DraftKings line for {r.away} @ {r.home} (not on ESPN yet).")
    return L


def threshold_for(price, oprice):
    """EV bar for a bet: THRESHOLD near the opening price, THRESHOLD_MOVED once it has moved (or the line number changed)"""
    if pd.isna(oprice) or pd.isna(price): return THRESHOLD_MOVED
    return THRESHOLD if abs(1 / espn.nd_dec(price) - 1 / espn.nd_dec(oprice)) <= NEAR_OPEN else THRESHOLD_MOVED


def fmt_price(o): return "" if pd.isna(o) else f"{o:+.0f}"


def near_open(price, oprice):
    return not (pd.isna(oprice) or pd.isna(price)) and abs(1 / espn.nd_dec(price) - 1 / espn.nd_dec(oprice)) <= NEAR_OPEN


def american(d):
    return (d - 1) * 100 if d >= 2 else -100 / (d - 1)


def thr_for(mk, price, oprice):
    """EV bar by market near the opener: moneyline (blended chance) ML_THRESHOLD, puck line THRESHOLD_PL, overs THRESHOLD;
    THRESHOLD_MOVED once the price moved"""
    t = threshold_for(price, oprice)
    if t != THRESHOLD: return t
    return ML_THRESHOLD if mk == "moneyline" else (THRESHOLD_PL if mk == "puck line" else THRESHOLD)


def scan_bar(mk, price, oprice):
    """lowest EV that gets a row at all: puck lines near the opener from THRESHOLD (6-9% = TEST rows, logged not pushed)"""
    t = thr_for(mk, price, oprice)
    return THRESHOLD if (mk == "puck line" and t == THRESHOLD_PL) else t


def open_only_floor(p, oprice, thr=None):
    """shortest price still worth taking on an opening-price-only bet: still near the opening price AND still EV >= the bar"""
    d_near = 1 / (1 / espn.nd_dec(oprice) + NEAR_OPEN)
    d_ev = (1 + (THRESHOLD if thr is None else thr)) / p
    return american(max(d_near, d_ev))


def is_open_only(name, price):
    return name in OPEN_ONLY_LONGSHOTS and not pd.isna(price) and price >= OPEN_ONLY_LONGSHOTS[name]


def main():
    if "--test" in sys.argv:
        topic = os.environ.get("NTFY_TOPIC") or ""
        try:
            ok = notify("Test alert: NHL tracker connected", "If you can read this, phone alerts from your NHL GitHub tracker are working. No bet here.", kind="test")
            msg = (f"sent OK to a topic {len(topic)} characters long, starting with '{topic[:2]}'" if ok
                   else "NOT sent: the NTFY_TOPIC secret is missing or empty")
        except Exception as e:
            msg = f"NOT sent: ntfy returned an error ({type(e).__name__}: {str(e)[:80]})"
        open(os.path.join(STATE, "test_alert_result.txt"), "w").write(f"{NOW}: test alert {msg}\n")
        print("Test alert", msg); return
    if not FORCE and not in_window():
        print(f"{NOW:%H:%M} ET is outside the alert window; nothing to do."); return
    models = sorted(f for f in os.listdir(STATE) if f.startswith("model_") and f.endswith(".json") and f[6:16] >= str(TODAY.date()))
    if not models: print("No model saved for today or tomorrow yet."); return
    try:
        FEED = espn.injury_feed()
    except Exception as e:
        FEED = None; print("Injury feed unavailable:", type(e).__name__)
    NEWS = espn.injury_news(hours=24, feed=FEED) if FEED is not None else None
    # reporter news on Bluesky (bluesky_watch.py, since Nov 2, 2026): starting goalies and clear skater decisions
    try: GNEWS = json.load(open(os.path.join(STATE, "goalie_news.json")))
    except Exception: GNEWS = {}
    try: SKNEWS = json.load(open(os.path.join(STATE, "news_overrides.json")))
    except Exception: SKNEWS = {}
    status_of = {}
    for team, items in (FEED or {}).items():
        for pid, name, st, _, _ in items:
            if pid: status_of[pid] = st

    apath = os.path.join(STATE, "alerts.csv")
    A = pd.read_csv(apath) if os.path.exists(apath) else pd.DataFrame(columns=["game_id", "market", "skipped", "model"])
    if "model" not in A: A["model"] = "goals"                 # alerts from before both models ran
    A["model"] = A.model.fillna("goals")
    if len(A) and "sent" in A:          # an alert that couldn't be delivered (e.g. no ntfy topic yet) is tried again next check
        A = A[A.sent.astype(str).isin(["True", "quiet"])].reset_index(drop=True)
    done = set(zip(A[A.skipped.isna()].game_id, A[A.skipped.isna()].market, A[A.skipped.isna()].model)) if len(A) else set()
    skipped = set(zip(A[A.skipped.notna()].game_id, A[A.skipped.notna()].market, A[A.skipped.notna()].model)) if len(A) else set()
    bpath = os.path.join(STATE, "my_bets.csv")
    try:
        MYB = pd.read_csv(bpath) if os.path.exists(bpath) else pd.DataFrame(columns=["date", "home", "away", "market"])
    except Exception:
        MYB = pd.DataFrame(columns=["date", "home", "away", "market"])

    def bets_note(date, home, away, market, want=None):
        """('same market' text, 'other markets' text) for bets already logged on this game (ported from the NBA tracker)"""
        if not len(MYB): return "", ""
        x = MYB[(MYB.date.astype(str) == str(date)) & (MYB.home.astype(str).str.lower() == home) & (MYB.away.astype(str).str.lower() == away)]
        def desc(r):
            try:
                pick = str(r.pick).upper(); mk_ = str(r.market)
                ln_ = "" if mk_ == "moneyline" or pd.isna(r.line) else (f" {float(r.line):+g}" if mk_ == "puck line" else f" {float(r.line):g}")
                st = float(r.stake); stake = f"{st:g}u"
                when = pd.Timestamp(r.logged_at_et).strftime("%-I:%M %p") if isinstance(r.logged_at_et, str) else "earlier"
                book = f", {r.book}" if isinstance(r.book, str) and r.book else ""
                return f"{pick}{' ML' if mk_ == 'moneyline' else ''}{ln_} ({float(r.odds):+g}, {stake}{book}, logged {when})"
            except Exception:
                return "a bet (see My Bets)"
        sm = x[x.market == market]
        if want is not None:            # bets on the same market but the OTHER side are reported separately
            opp = sm[sm.pick.astype(str).str.lower() != str(want).lower()]
            sm = sm[sm.pick.astype(str).str.lower() == str(want).lower()]
        else:
            opp = sm.iloc[:0]
        return ("; ".join(desc(r) for r in sm.itertuples()),
                "; ".join(desc(r) for r in x[x.market != market].itertuples()) +
                (("; " if (x.market != market).any() else "") + "OTHER SIDE: " + "; ".join(desc(r) for r in opp.itertuples()) if len(opp) else ""))

    def caution_before(gid, market, names):
        """the latest caution alert sent earlier for this game, market and any of these models"""
        c = A[(A.game_id == gid) & (A.market == market) & A.skipped.notna() & (A.skipped != MOVED_SKIP) & A.model.isin(names)] if len(A) else A.iloc[:0]
        return c.iloc[-1] if len(c) else None

    def record(name, caution):
        g = A[(A.model == name) & (A.skipped.notna() if caution else A.skipped.isna())]
        g = g[g.result.isin(["W", "L"])] if "result" in g else g.iloc[:0]
        return (f"{int((g.result == 'W').sum())}-{int((g.result == 'L').sum())}, {g.profit.sum():+.1f}u" if len(g) else "none graded yet")
    new, n_games, model_rows = [], 0, []
    hpath = os.path.join(STATE, "line_history.csv")
    H_ = pd.read_csv(hpath) if os.path.exists(hpath) else pd.DataFrame(columns=["game_id", "market", "seen_at_et", "line", "prices", "prob"])
    hist_new = []

    def record_line(gid, market, line, prices, prob):
        """log the line whenever it or its prices change (or the first time it is seen), with the time we saw it"""
        if pd.isna(prob): return
        prev = [r for r in hist_new if r["game_id"] == gid and r["market"] == market]
        old = H_[(H_.game_id == gid) & (H_.market == market)]
        last = (prev[-1]["line"], prev[-1]["prices"]) if prev else ((old.line.iloc[-1], old.prices.iloc[-1]) if len(old) else None)
        if last is None or str(last[0]) != str(line) or str(last[1]) != str(prices):
            hist_new.append(dict(game_id=gid, market=market, seen_at_et=str(NOW)[:16], line=line, prices=prices, prob=round(prob, 1)))

    def history_text(gid, market):
        rows = pd.concat([H_[(H_.game_id == gid) & (H_.market == market)],
                          pd.DataFrame([r for r in hist_new if r["game_id"] == gid and r["market"] == market])], ignore_index=True)
        if not len(rows): return ""
        lab = (lambda r: f"{r.prices}") if market == "moneyline" else (lambda r: f"{r.line:g} {r.prices}")
        steps = [f"{lab(r)} ({'first seen ' if i == 0 else ''}{pd.Timestamp(r.seen_at_et):%a %-I:%M %p})" for i, r in enumerate(rows.itertuples())]
        if len(steps) > 5: steps = steps[:1] + ["…"] + steps[-3:]
        return f"\n{'Moneyline' if market == 'moneyline' else 'Total'} history: " + " -> ".join(steps)

    news_for = lambda g: ("\n" + espn.news_text(NEWS, [g["away"], g["home"]])) if NEWS is not None else ""
    mpath = os.path.join(STATE, "market_moves.csv")
    MV = pd.read_csv(mpath) if os.path.exists(mpath) else pd.DataFrame(columns=["game_id", "market"])
    moved_done = set(zip(MV.game_id, MV.market)); moves_new = []
    info = {}
    gpath = os.path.join(STATE, "ovr_goalie_test.csv")
    GT = pd.read_csv(gpath) if os.path.exists(gpath) else pd.DataFrame(columns=["game_id"])
    gtest_done, gtest_new = set(GT.game_id), []
    grpath = os.path.join(STATE, "goalie_recheck_test.csv")
    GR = pd.read_csv(grpath) if os.path.exists(grpath) else pd.DataFrame(columns=["game_id", "market"])
    grtest_done, grtest_new = set(zip(GR.game_id, GR.market)), []
    rpath = os.path.join(STATE, "rest_b2b_test.csv")
    RT = pd.read_csv(rpath) if os.path.exists(rpath) else pd.DataFrame(columns=["game_id"])
    rtest_done, rtest_new = set(RT.game_id), []
    NOWC, GINFO = {}, {}   # this check's price and EV for every (game, market, side, model), and game details, for reminders
    DKC = {}               # (game, market, side) -> DraftKings bet-slip link, so reminders carry the same button as the first alert

    for mf in models:
        Mall = load_models(os.path.join(STATE, mf))
        order = [k for k in ("xg", "goals") if k in Mall["models"]] + [k for k in Mall["models"] if k not in ("xg", "goals")]
        lead = order[0]
        M = dict(Mall["models"][lead], date=Mall["date"], made_at_et=Mall["made_at_et"])
        day = pd.Timestamp(M["date"])
        gname = {int(k): v for k, v in M.get("goalie_names", {}).items()}
        try:
            SB = {(r["home"], r["away"]): r for r in nd.scoreboard(day)}
        except Exception as e:
            SB = {}; print("Scoreboard unavailable:", type(e).__name__)
        B2B = set()
        try:
            for r in nd.scoreboard(day - pd.Timedelta(days=1)): B2B |= {r["home"], r["away"]}
        except Exception as e:
            print("Yesterday's scoreboard unavailable:", type(e).__name__)
        PIN = pinnacle_first()
        LAST = nhl_travel.last_games(nd, day, os.path.join(STATE, "_travel_cache.json"))   # each team's previous game (back-to-backs, travel)
        L = espn.lines([day], when=("open", "current"))
        L = fill_from_action_network(L, day)
        for g in M["games"]:
            info[g["game_id"]] = (g, M)
            line = L[(L.home == g["home"]) & (L.away == g["away"])] if len(L) else L
            if not len(line) or line.iloc[0].get("state") not in (None, "pre"): continue
            n_games += 1
            ln = line.iloc[0]
            pr = SB.get((g["home"], g["away"]), {}).get("probables", {})

            def goalie(def_side, gv):
                """(effect, label, confirmed, known) for the goalie facing the other team, using one model's goalie effects"""
                p = pr.get(def_side)
                rn = GNEWS.get(f"{g['game_id']}|{def_side}")
                if rn and not (p and p[2] == "Confirmed") and (rn["level"] == "confirmed" or not p):
                    # a reporter's starter: used until ESPN confirms one; an 'expected' one only when ESPN lists nobody
                    conf = rn["level"] == "confirmed"
                    return (gv.get(int(rn["goalie_id"]), 0.0), f"{rn['goalie']} ({'confirmed' if conf else 'expected'} by "
                            f"{rn['reporter']} {pd.Timestamp(rn['posted_at_et']):%-I:%M %p})", conf, True)
                if p:
                    pid, name, st = p
                    return gv.get(int(pid), 0.0), f"{name} ({(st or 'listed').lower()})", st == "Confirmed", True
                mix = {int(k): w for k, w in g[f"{def_side}_gmix"].items()}
                top = max(mix.items(), key=lambda x: x[1]) if mix else (None, 0)
                return (sum(w * gv.get(k, 0.0) for k, w in mix.items()),
                        f"{gname.get(top[0], 'unknown')} ({top[1]:.0%} likely, not announced)" if top[0] else "unknown", False, False)

            def missing(side):
                tot, out = 0.0, []
                for pid, (name, val, missed_last) in g[f"{side}_regulars"].items():
                    st = status_of.get(int(pid)) if FEED is not None else None
                    pm = P_MISS.get(st, 0.0) if st else (1.0 if missed_last else 0.0)
                    rv = SKNEWS.get(f"{M['date']}|{g[side]}|{pid}")       # a reporter's clear 'out' / 'will play' for this game
                    if rv: pm = 1.0 if rv["status"] == "Out" else 0.0
                    if pm > 0: tot += pm * val; out.append(name.split()[-1] + ("" if pm == 1 else "?"))
                return tot, out
            _, gh_lab, gh_conf, gh_known = goalie("home", {}); _, ga_lab, ga_conf, ga_known = goalie("away", {})
            mh, outs_h = missing("home"); ma, outs_a = missing("away")
            goalies_txt = f"{g['away'].upper()} {ga_lab}; {g['home'].upper()} {gh_lab}"
            missing_txt = f"{g['away'].upper()}: {', '.join(outs_a) or '-'} | {g['home'].upper()}: {', '.join(outs_h) or '-'}"
            c, o = {k: ln.get(f"current_{k}") for k in espn.MARKET_COLS}, {k: ln.get(f"open_{k}") for k in espn.MARKET_COLS}
            ph_now, ph_open = fair(c["home_ml"], c["away_ml"]), fair(o["home_ml"], o["away_ml"])
            record_line(g["game_id"], "moneyline", c["home_ml"], f"{g['away'].upper()} {fmt_price(c['away_ml'])} / {g['home'].upper()} {fmt_price(c['home_ml'])}", 100 * ph_now)
            record_line(g["game_id"], "puck line", c["home_pl"], f"{g['home'].upper()} {c['home_pl']:+g} {fmt_price(c['home_pl_odds'])} / {g['away'].upper()} {fmt_price(c['away_pl_odds'])}" if not pd.isna(c["home_pl"]) else "",
                        100 * fair(c["home_pl_odds"], c["away_pl_odds"]))
            record_line(g["game_id"], "total", c["total"], f"o{fmt_price(c['over_odds'])}/u{fmt_price(c['under_odds'])}", 100 * fair(c["over_odds"], c["under_odds"]))
            tip = pd.Timestamp(g["tip_et"]).strftime("%a %-I:%M %p")
            H, Aw = g["home"].upper(), g["away"].upper()
            move = 100 * (ph_now - ph_open) if not (pd.isna(ph_now) or pd.isna(ph_open)) else 0.0
            # ---- every model's numbers and best bet per market at the current prices
            TADJ, TWHY = nhl_travel.adjustment(g["home"], g["away"], day, LAST)
            best, est = {}, {}
            for name in order:
                OM = Mall["models"][name]
                og = next((x for x in OM["games"] if x["game_id"] == g["game_id"]), None)
                if og is None: continue
                gv = {int(k): v for k, v in OM["goalies"].items()}
                lam_h = og["base_home"] + OM["c_miss"] * mh + goalie("away", gv)[0]
                lam_a = og["base_away"] + OM["c_miss"] * ma + goalie("home", gv)[0]
                cal = OM["cal"]["pretip" if (gh_known and ga_known) else "open"]
                mp = nm.market_probs(np.array([lam_h]), np.array([lam_a]), OM["h_ot"], cal)
                p_home, p_hby2, p_aby2 = float(mp["home_win"][0]), float(mp["home_by2"][0]), float(mp["away_by2"][0])
                if name in ALERT_MODELS and TADJ: p_home = min(max(p_home + TADJ, 0.02), 0.98)   # schedule/travel (moneyline)
                exp_total = float(lam_h + lam_a + nm.raw_probs(np.array([lam_h]), np.array([lam_a]), OM["h_ot"])["tie"][0])
                est[name] = (lam_h, lam_a, exp_total, p_home)
                model_rows.append(dict(seen_at_et=str(NOW)[:16], model=name, game_id=g["game_id"], date=M["date"], away=g["away"], home=g["home"],
                                       model_home_win=round(p_home, 4), lam_home=round(lam_h, 3), lam_away=round(lam_a, 3),
                                       model_total=round(exp_total, 2), away_goalie=ga_lab, home_goalie=gh_lab, missing=missing_txt))
                cands = []
                p_ml = (ML_BLEND * p_home + (1 - ML_BLEND) * ph_open) if (name in ALERT_MODELS and not pd.isna(ph_open)) else p_home
                if not pd.isna(c["home_ml"]):
                    for side, p, price in (("home", p_ml, c["home_ml"]), ("away", 1 - p_ml, c["away_ml"])):
                        cands.append(("moneyline", side, np.nan, price, p, o[f"{side}_ml"]))
                # Nov 4, 2026 (spreads step 1 review): only +/-1.5 puck lines. p_hby2 / p_aby2 are "win by 2+" chances, so a -2.5
                # line (DK opened 22 games 2021-26 at -2.5) was priced and alerted as if it were -1.5 (fake EV 15-47%).
                if not pd.isna(c["home_pl"]) and abs(float(c["home_pl"])) == 1.5:
                    hl = c["home_pl"]; p_hc = p_hby2 if hl < 0 else 1 - p_aby2
                    cands += [("puck line", "home", hl, c["home_pl_odds"], p_hc, o["home_pl_odds"] if o["home_pl"] == hl else np.nan),
                              ("puck line", "away", -hl, c["away_pl_odds"], 1 - p_hc, o["away_pl_odds"] if o["home_pl"] == hl else np.nan)]
                if not pd.isna(c["total"]):
                    po, pu, pp = nm.over_prob(np.array([lam_h]), np.array([lam_a]), np.array([c["total"]]), OM["h_ot"], cal)
                    same = o["total"] == c["total"]
                    cands += [("total", "over", c["total"], c["over_odds"], float(po[0]), o["over_odds"] if same else np.nan),
                              ("total", "under", c["total"], c["under_odds"], float(pu[0]), o["under_odds"] if same else np.nan)]
                for mk, side, lnum, price, p, oprice in cands:
                    if pd.isna(price): continue
                    ev = p * espn.nd_dec(price) - 1
                    NOWC[(g["game_id"], mk, side, name)] = (lnum, price, p, ev, oprice)
                    if (name, mk) not in best or ev > best[(name, mk)][4]: best[(name, mk)] = (side, lnum, price, p, ev, oprice)
            # ---- TEST: rested team vs a back-to-back team, at DK's opening moneyline (logged only, never pushed)
            if REST_TEST and g["game_id"] not in rtest_done and ((g["home"] in B2B) != (g["away"] in B2B)):
                rs = "away" if g["home"] in B2B else "home"
                if not pd.isna(o[f"{rs}_ml"]) and not pd.isna(o[f"{'home' if rs == 'away' else 'away'}_ml"]):
                    p_open = ph_open if rs == "home" else 1 - ph_open
                    rtest_new.append(dict(logged_at_et=str(NOW)[:16], game_id=g["game_id"], date=M["date"], home=g["home"], away=g["away"],
                                          tip_et=g["tip_et"], side=rs, team=g[rs], b2b_team=g["away" if rs == "home" else "home"],
                                          price=o[f"{rs}_ml"], open_fair=round(p_open, 4), current_price=c[f"{rs}_ml"],
                                          verdict="TEST: rested team vs back-to-back (not a bet)"))
                    rtest_done.add(g["game_id"]); print(f"TEST (not pushed): rested {g[rs].upper()} {fmt_price(o[rs + '_ml'])} vs b2b, {Aw} @ {H}")
            # ---- TEST: goalie-confirmed over (logged only, never pushed)
            if GOALIE_OVER_TEST and gh_conf and ga_conf and g["game_id"] not in gtest_done:
                v = NOWC.get((g["game_id"], "total", "over", "xg"))
                over_alerted = len(A) and ((A.game_id == g["game_id"]) & (A.market == "total") & (A.side == "over") & A.skipped.isna()).any()
                if v is not None and v[3] >= GOALIE_OVER_EV and not over_alerted and "xg" in est:
                    gtest_new.append(dict(logged_at_et=str(NOW)[:16], game_id=g["game_id"], date=M["date"], home=g["home"], away=g["away"],
                                          tip_et=g["tip_et"], side="over", line=v[0], price=v[1], open_total=o["total"], open_over_odds=o["over_odds"],
                                          model_prob=round(v[2], 4), ev=round(v[3], 4), model_total=round(est["xg"][2], 2), goalies=goalies_txt,
                                          sent=False, verdict="TEST: goalie-confirmed over (not a bet)"))
                    gtest_done.add(g["game_id"]); print(f"TEST (not pushed): goalie-confirmed OVER {v[0]:g} ({fmt_price(v[1])}) {Aw} @ {H}, EV {v[3]:+.1%}")
            # ---- TEST: game-day re-check once both starters are confirmed (logged only, never pushed)
            if GOALIE_RECHECK_TEST and gh_conf and ga_conf and "xg" in est:
                try:
                    exp_ = {sd: (lambda mx: gname.get(max(mx, key=mx.get), "?") if mx else "?")({int(k): w for k, w in g[f"{sd}_gmix"].items()})
                            for sd in ("home", "away")}
                    bet_before = {mk_: bool(len(A) and ((A.game_id == g["game_id"]) & (A.market == mk_) & A.skipped.isna()).any())
                                  for mk_ in ("moneyline", "puck line")}
                    base = dict(logged_at_et=str(NOW)[:16], game_id=g["game_id"], date=M["date"], home=g["home"], away=g["away"], tip_et=g["tip_et"],
                                goalies=goalies_txt, expected_home=exp_["home"], expected_away=exp_["away"], missing=missing_txt)
                    if (g["game_id"], "moneyline") not in grtest_done and not pd.isna(c["home_ml"]) and not pd.isna(ph_now):
                        pm_ = ML_BLEND * est["xg"][3] + (1 - ML_BLEND) * ph_now
                        evs = {"home": pm_ * espn.nd_dec(c["home_ml"]) - 1, "away": (1 - pm_) * espn.nd_dec(c["away_ml"]) - 1}
                        sd = max(evs, key=evs.get)
                        grtest_new.append(dict(base, market="moneyline", side=sd, team=g[sd], line=np.nan, price=c[f"{sd}_ml"],
                                               open_price=o[f"{sd}_ml"], model_prob=round(pm_ if sd == "home" else 1 - pm_, 4),
                                               raw_model_home=round(est["xg"][3], 4), dk_fair_home_now=round(ph_now, 4), ev=round(evs[sd], 4),
                                               qualifies=bool(evs[sd] >= GR_ML_EV), bet_alerted_before=bet_before["moneyline"],
                                               verdict="TEST: goalie re-check (not a bet)"))
                        grtest_done.add((g["game_id"], "moneyline"))
                    vh, va = NOWC.get((g["game_id"], "puck line", "home", "xg")), NOWC.get((g["game_id"], "puck line", "away", "xg"))
                    if (g["game_id"], "puck line") not in grtest_done and vh is not None and va is not None:
                        sd, v = ("home", vh) if vh[3] >= va[3] else ("away", va)
                        grtest_new.append(dict(base, market="puck line", side=sd, team=g[sd], line=v[0], price=v[1], open_price=v[4],
                                               model_prob=round(v[2], 4), raw_model_home=round(est["xg"][3], 4), dk_fair_home_now=round(ph_now, 4)
                                               if not pd.isna(ph_now) else np.nan, ev=round(v[3], 4),
                                               qualifies=bool(v[3] >= GR_PL_EV and g[sd] not in B2B), bet_alerted_before=bet_before["puck line"],
                                               verdict="TEST: goalie re-check (not a bet)"))
                        grtest_done.add((g["game_id"], "puck line"))
                except Exception as e:                       # a TEST logger must never stop the real alerts
                    print(f"goalie re-check TEST skipped for {Aw} @ {H}: {e}")
            GINFO[g["game_id"]] = dict(H=H, Aw=Aw, tip=tip, tip_et=g["tip_et"], goalies=goalies_txt, conf=gh_conf and ga_conf,
                                      ph_open=ph_open, pin=PIN.get((g["home"], g["away"])))
            for _mk, _sides in (("moneyline", ("home", "away")), ("puck line", ("home", "away")), ("total", ("over", "under"))):
                for _sd in _sides:
                    _col = {"moneyline": f"dk_link_{_sd}_ml", "puck line": f"dk_link_{_sd}_pl", "total": f"dk_link_{_sd}"}[_mk]
                    DKC[(g["game_id"], _mk, _sd)] = ln.get(_col) if isinstance(ln.get(_col), str) else DK_NHL
            # ---- goalie what-ifs (Nov 5, 2026): the bet's EV under each likely starter for every goalie not yet confirmed,
            # so an alert shows whether a goalie announcement could push it out of range (UTA -1.5 on Nov 5: alerted at
            # +10.2% with Vejmelka expected, Cossa was confirmed 13 minutes later and it fell to +8.9%, under the 9% bar)
            def goalie_whatifs(name, mk, side, lnum, price, oprice):
                OM = Mall["models"][name]
                og = next((x for x in OM["games"] if x["game_id"] == g["game_id"]), None)
                if og is None: return []
                gv = {int(k): v for k, v in OM["goalies"].items()}
                cal = OM["cal"]["pretip" if (gh_known and ga_known) else "open"]   # same calibration as the headline EV
                eff = {d: goalie(d, gv)[0] for d in ("home", "away")}
                out = []
                for d, conf in (("home", gh_conf), ("away", ga_conf)):
                    if conf: continue
                    mix = {int(k): w for k, w in g[f"{d}_gmix"].items()}
                    cands = [k for k, w in sorted(mix.items(), key=lambda x: -x[1]) if w >= 0.10][:3]
                    p_ = pr.get(d); rn = GNEWS.get(f"{g['game_id']}|{d}")
                    cur = int(rn["goalie_id"]) if rn else (int(p_[0]) if p_ else None)
                    if cur is not None and cur not in cands: cands = [cur] + cands
                    if len(cands) < 2: continue
                    opts = []
                    for gid in cands:
                        e = dict(eff); e[d] = gv.get(gid, 0.0)
                        lh = og["base_home"] + OM["c_miss"] * mh + e["away"]; la = og["base_away"] + OM["c_miss"] * ma + e["home"]
                        if mk == "total":
                            po, pu, _ = nm.over_prob(np.array([lh]), np.array([la]), np.array([lnum]), OM["h_ot"], cal)
                            p = float(po[0]) if side == "over" else float(pu[0])
                        else:
                            mp = nm.market_probs(np.array([lh]), np.array([la]), OM["h_ot"], cal)
                            if mk == "moneyline":
                                ph = float(mp["home_win"][0])
                                if name in ALERT_MODELS and TADJ: ph = min(max(ph + TADJ, 0.02), 0.98)
                                if name in ALERT_MODELS and not pd.isna(ph_open): ph = ML_BLEND * ph + (1 - ML_BLEND) * ph_open
                                p = ph if side == "home" else 1 - ph
                            else:
                                hl = c["home_pl"]; phc = float(mp["home_by2"][0]) if hl < 0 else 1 - float(mp["away_by2"][0])
                                p = phc if side == "home" else 1 - phc
                        ev = p * espn.nd_dec(price) - 1
                        ok = ev >= thr_for(mk, price, oprice)
                        nm_ = gname.get(gid, "?").split()[-1]
                        opts.append(f"{nm_} {ev:+.1%} {'✅' if ok else '❌'}" + ("" if gid != cur else " (listed)"))
                    out.append(f"If {g[d].upper()} starts: " + " | ".join(opts))
                return out

            # ---- alerts: one per side; both models in one alert when they agree
            def second_chance(name, bt, mk):
                """moneyline only: no value at the opener, 6%+ now, Pinnacle posted in the last hour and agrees or matches"""
                if not SECOND_CHANCE or mk != "moneyline" or name not in ALERT_MODELS: return False
                key = (g["home"], g["away"]); seen = PIN_SEEN.get(key)
                if key not in PIN or not seen or pd.isna(bt[5]) or pd.isna(ph_now): return False
                if NOW - pd.Timestamp(seen).tz_convert(ET).tz_localize(None) > pd.Timedelta(minutes=SC_WINDOW_MIN): return False
                p_raw = est[name][3] if bt[0] == "home" else 1 - est[name][3]        # tested with the plain shot model's chance
                if p_raw * espn.nd_dec(bt[2]) - 1 < THRESHOLD or p_raw * espn.nd_dec(bt[5]) - 1 >= THRESHOLD: return False
                diff = (PIN[key] - ph_now) if bt[0] == "home" else (ph_now - PIN[key])
                return diff >= -PIN_DISAGREE
            for mk in ALERT_MARKETS:
                hist_txt = history_text(g["game_id"], "total" if mk == "total" else "moneyline")
                groups = {}
                for name in order:
                    bt = best.get((name, mk))
                    if bt is None: continue
                    if mk == "total" and bt[0] not in TOTAL_SIDES: continue        # unders are logged by the model, never alerted
                    if name in OPEN_ONLY_LONGSHOTS and bt[2] >= OPEN_ONLY_LONGSHOTS[name] and not near_open(bt[2], bt[5]): continue
                    thr = scan_bar(mk, bt[2], bt[5])
                    if bt[4] < thr and not second_chance(name, bt, mk):
                        side = bt[0]
                        toward = mk != "total" and abs(move) >= MAX_MOVE and ((move > 0) == (side == "home"))
                        if name == lead and toward and (g["game_id"], mk) not in moved_done:
                            team = H if side == "home" else Aw
                            notify(f"Market agrees: {Aw} @ {H} {mk}, {tip}",
                                   f"The moneyline moved {abs(move):.1f} win-% points toward the {SHORT.get(name, name)}'s side ({team}) since open. "
                                   f"EV left: {bt[4]:+.1%} (under {thr:.0%}, so no bet). Info only." + hist_txt + news_for(g),
                                   priority="low", tags="chart_with_upwards_trend")
                            moves_new.append(dict(at_et=str(NOW), game_id=g["game_id"], date=M["date"], home=g["home"], away=g["away"], market=mk,
                                                  model=name, model_side=side, open_home_prob=round(100 * ph_open, 1), home_prob=round(100 * ph_now, 1),
                                                  move=round(move, 1), model_home_prob=round(100 * est[name][3], 1), ev_left=round(bt[4], 4)))
                            moved_done.add((g["game_id"], mk))
                        continue
                    groups.setdefault((bt[0], bt[1], bt[2]), []).append((name, bt))
                for (side, lnum, price), members in groups.items():
                    if not any(n in ALERT_MODELS for n, _ in members): continue      # research-only model's bet: not alerted
                    oprice = members[0][1][5]
                    team = H if side == "home" else (Aw if side == "away" else side.upper())
                    against = mk != "total" and abs(move) >= MAX_MOVE and ((move > 0) != (side == "home"))
                    toward = mk != "total" and abs(move) >= MAX_MOVE and ((move > 0) == (side == "home"))
                    # Since Nov 1, 2026: only opening-price bets are real bets (the backtests made money only there). The goalie
                    # caution no longer applies to them (backtest openers: +3.7% when the expected goalie started, +3.2% when not).
                    at_open = near_open(price, oprice)
                    skip = None
                    is_sc = (not at_open) and any(second_chance(n, bt_, mk) for n, bt_ in members)
                    if not at_open and not is_sc: skip = MOVED_SKIP
                    elif against: skip = f"the moneyline moved {abs(move):.1f} win-% points against this side since open"
                    pending = [(n, bt) for n, bt in members if (g["game_id"], mk, n) not in (skipped if skip else done)]
                    if not pending: continue
                    # never both sides: the two models backing different teams in this game (moneyline or puck line), or
                    # a logged bet on the other team, means no bet (Nov 1, 2026: UTA ML and PHI ML were both alerted)
                    conflict = None
                    TEAM_MK = ("moneyline", "puck line")
                    if mk in TEAM_MK:
                        opp = "away" if side == "home" else "home"; mine = {n for n, _ in pending}
                        for (gid2, mk2, s2, n2), v in NOWC.items():
                            if gid2 == g["game_id"] and mk2 in TEAM_MK and s2 == opp and n2 in ALERT_MODELS and v[3] >= thr_for(mk2, v[1], v[4]):
                                conflict = (f"the models disagree: the {SHORT.get(n2, n2)} likes {g[opp].upper()} "
                                            f"({mk2}, EV {v[3]:+.1%}){' too' if n2 in mine else ''}")
                                break
                        if len(MYB):
                            mb = MYB[(MYB.date.astype(str) == str(M["date"])) & (MYB.home.astype(str).str.lower() == g["home"]) &
                                     (MYB.away.astype(str).str.lower() == g["away"]) & MYB.market.isin(TEAM_MK) &
                                     (MYB.pick.astype(str).str.lower() == g[opp])]
                            if len(mb): conflict = f"you already bet {g[opp].upper()} on this game ({mb.market.iloc[-1]})"
                    if mk in TEAM_MK and not conflict:
                        if SKIP_B2B and mk in SKIP_B2B_MARKETS and g[side] in B2B:
                            conflict = (f"{g[side].upper()} also plays the night before this game (second night of a back-to-back); puck line "
                                        f"bets on back-to-back teams 2021-26: 137 bets, won 35%, -37.3u, 4 of 5 seasons negative")
                        elif USE_PINNACLE_RULE and mk == "moneyline" and (g["home"], g["away"]) in PIN and not pd.isna(ph_open):
                            pin = PIN[(g["home"], g["away"])]
                            diff = (pin - ph_open) if side == "home" else (ph_open - pin)
                            if diff < -PIN_DISAGREE:
                                ours_pin = pin if side == "home" else 1 - pin; ours_dk = ph_open if side == "home" else 1 - ph_open
                                conflict = (f"Pinnacle (the sharp book) opened {g[side].upper()} at {ours_pin:.1%} vs DraftKings' "
                                            f"{ours_dk:.1%}; when Pinnacle was already up and disagreed, 2021-26: 27 bets -8.8u (small sample)")
                    if mk in TEAM_MK and not conflict and not skip:
                        # one bet per game (Nov 2, 2026): moneyline and puck line on the same team are the same prediction. Since Nov 4
                        # (PREFER_ML) the moneyline is the bet when it qualifies; the puck line leg is logged as a TEST row (not pushed).
                        # Rule audit 2021-26, 597 games where both qualified: always the moneyline +69.7u, the old higher-EV pick +54.2u.
                        other = "puck line" if mk == "moneyline" else "moneyline"
                        mine_ev = max(bt_[4] for _, bt_ in pending)
                        if any((g["game_id"], other, n) in done for n in ALERT_MODELS):
                            conflict = (f"TEST: one bet per game, the moneyline on this game is the bet (puck line leg recorded for testing)"
                                        if mk == "puck line" and PREFER_ML else f"one bet per game: the {other} on this game was already alerted")
                        elif not PREFER_ML:
                            for n2 in ALERT_MODELS:
                                ob = best.get((n2, other))
                                if ob and ob[0] == side and near_open(ob[2], ob[5]) and ob[4] >= thr_for(other, ob[2], ob[5]) and ob[4] > mine_ev:
                                    conflict = f"one bet per game: the {other} has more value (EV {ob[4]:+.1%} vs {mine_ev:+.1%})"
                                    break
                    if mk == "puck line" and not conflict and not skip and max(bt_[4] for _, bt_ in pending) < thr_for(mk, price, oprice):
                        conflict = (f"TEST: puck line EV {max(bt_[4] for _, bt_ in pending):+.1%} is under the {THRESHOLD_PL:.0%} bar "
                                    f"(6-9% bucket recorded for the re-test after 2026-27; not a bet)")
                    if conflict and not skip and all((g["game_id"], mk, n) in skipped for n, _ in pending): continue   # logged already
                    tag = "Both models" if len(pending) > 1 else SHORT.get(pending[0][0], pending[0][0])
                    what = (f"{team} ML {fmt_price(price)}" if mk == "moneyline" else
                            (f"{team} {lnum:+g} ({fmt_price(price)})" if mk == "puck line" else f"{side.upper()} {lnum:g} ({fmt_price(price)})"))
                    title = f"[{tag}] Bet {what}: {Aw} @ {H}, {tip}"
                    oo = [(n, bt) for n, bt in pending if is_open_only(n, price)]
                    if oo and len(oo) == len(pending):
                        title = "OPENING PRICE ONLY - " + title
                    lines_ = []
                    for n, bt in pending:
                        p, ev = bt[3], bt[4]
                        s_ = f"{SHORT.get(n, n)}: {p:.1%} to win (needs {1 / espn.nd_dec(price):.1%}), EV {ev:+.1%}"
                        lines_.append(s_ + ".")
                    body = ("DraftKings " + fmt_price(price) + (" (opening price)." if oprice == price else
                            (f" (opened {fmt_price(oprice)})." if not pd.isna(oprice) else ".")) + "\n" + "\n".join(lines_))
                    if oo:
                        floor = min(open_only_floor(bt[3], oprice) for _, bt in oo)
                        who = SHORT.get(oo[0][0], oo[0][0])
                        body = (f"OPENING PRICE ONLY ({who}): bet this only at {fmt_price(floor)} or longer. If DraftKings now shows a shorter "
                                f"price than {fmt_price(floor)}, skip it. In the backtests the {who}'s +150-and-longer bets made money at "
                                f"the opening price (+13.5u on 641 bets) but lost once the price moved.\n" + body)
                        if len(oo) < len(pending):
                            body += f"\nThe shot model's number on this bet holds at any price; only the {who}'s needs the opening price."
                    if is_sc:
                        title = "SECOND CHANCE - " + title
                        pin_ours = PIN[(g["home"], g["away"])] if side == "home" else 1 - PIN[(g["home"], g["away"])]
                        body = (f"SECOND CHANCE: no bet at the opening price, but Pinnacle (the sharp book) just posted {team} at {pin_ours:.1%} "
                                f"and DraftKings' price now has {max(bt[4] for _, bt in pending):+.1%} EV. These bets made +17.2u on 172 "
                                f"(+10%) 2021-26, every season positive. Bet at {fmt_price(price)} or better, now.\n" + body)
                    elif threshold_for(price, oprice) > THRESHOLD:
                        body += f"\nThe price has moved since it opened, so this needed {THRESHOLD_MOVED:.0%}+ EV (vs {THRESHOLD:.0%} at the opening price)."
                    # Nov 5, 2026: alerts trimmed to what decides the bet. Goalies plus the EV under each possible starter stay;
                    # schedule, missing skaters, line history, news and the running record are left out (still in the model).
                    tail = f"\nGoalies: {goalies_txt}."
                    try:
                        wi = []
                        n_wi = next((n_ for n_, _ in pending if n_ in ALERT_MODELS), pending[0][0])   # the model the bet is graded on
                        wi = goalie_whatifs(n_wi, mk, side, lnum, price, oprice)
                        if wi: tail += "\nEV by starter (✅ still a bet at this price):\n" + "\n".join(wi)
                    except Exception as e:
                        print("goalie what-ifs skipped:", e)
                    link = log_link(M["date"], g["away"], g["home"], mk, team if mk != "total" else side,
                                    "" if mk == "moneyline" else f"{lnum:+g}" if mk == "puck line" else f"{lnum:g}", f"{price:+.0f}")
                    dkcol = {"moneyline": f"dk_link_{side}_ml", "puck line": f"dk_link_{side}_pl", "total": f"dk_link_{side}"}[mk]
                    dk = ln.get(dkcol) if isinstance(ln.get(dkcol), str) else None
                    if not dk:   # brand-new line (taken from Action Network before ESPN has it): no bet-slip link yet,
                        dk = DK_NHL  # so the button opens DraftKings' NHL page instead and the body says to find the bet
                        body += "\nNo one-tap DraftKings link yet (line is brand new); the button opens DraftKings' NHL page."
                    recs = "; ".join(f"{SHORT.get(n, n)} {record(n, bool(skip))}" for n, _ in pending)
                    best_book = None
                    def fd_cmp():
                        """FanDuel next to DraftKings (Nov 4, 2026): both books' lines, the better one first and marked"""
                        return fanduel.compare("nhl", M["date"], g["home"], g["away"], mk, side,
                                               None if mk == "moneyline" else lnum, price, label=(team if mk != "total" else side))
                    if at_open and not pd.isna(oprice):
                        floor = min(open_only_floor(bt[3], oprice, thr_for(mk, price, oprice)) for _, bt in pending)
                        body = f"Bet only at {fmt_price(floor)} or better. If DraftKings shows a shorter price, skip it.\n" + body
                    if skip == MOVED_SKIP:
                        body = ("INFO ONLY, DON'T BET: the price has moved off its opening number "
                                f"({fmt_price(oprice)} at open). In the backtests the model loses at moved prices.\n" + body + tail)
                        sent = notify("INFO ONLY - " + title.replace("] Bet ", "] "), body, priority="low", tags="information_source,ice_hockey")
                    elif skip:
                        body += f"\nCAUTION: {skip}. The model may be missing news here; bet with caution." + tail + \
                                ""
                        same, other = bets_note(M["date"], g["home"], g["away"], mk, (team if mk != "total" else side))
                        ctitle = "CAUTION " + title
                        if same: body = f"ALREADY BET: you logged {same}.\n" + body; ctitle = "ALREADY BET - " + ctitle
                        if other: body += f"\nYour other bets on this game: {other}."
                        if "OTHER SIDE" in other: ctitle = "YOU BET THE OTHER SIDE - " + ctitle
                        fd_txt, fd_link, best_book = fd_cmp()
                        if fd_txt: body = fd_txt + "\n" + body
                        sent = notify(ctitle, body, priority="default", tags="warning,ice_hockey", link=link, dk=dk, fd=fd_link, best=best_book)
                    else:
                        body += tail
                        prio = "high"; why = ""
                        cb = caution_before(g["game_id"], mk, [n for n, _ in pending])
                        if cb is not None:      # a caution went out earlier: say why this one follows it
                            reason = str(cb.skipped)
                            cleared = ("goalie cautions no longer apply to opening-price bets" if "goalies" in reason and not (gh_conf and ga_conf) else
                                       "both starting goalies are now confirmed" if "goalies" in reason else
                                       "the moneyline is no longer moving against this side" if "against" in reason else
                                       "the caution no longer applies")
                            why = f"UPDATE to the {pd.Timestamp(cb.alerted_at_et):%-I:%M %p} caution: {cleared}.\n"
                            title = "UPDATE - " + title
                        same, other = bets_note(M["date"], g["home"], g["away"], mk, (team if mk != "total" else side))
                        if same:
                            why = f"ALREADY BET: you logged {same}. Only add to it if you mean to.\n" + why
                            title = "ALREADY BET - " + title; prio = "default"
                        if other: body += f"\nYour other bets on this game: {other}."
                        if "OTHER SIDE" in other: title = "YOU BET THE OTHER SIDE - " + title
                        if conflict:      # logged, not pushed: betting both teams pays the vig twice
                            title = ("TEST (not a bet) - " if conflict.startswith("TEST") else
                                     "NO BET (both sides) - " if ("disagree" in conflict and "Pinnacle" not in conflict) or "already bet" in conflict else "NO BET - ") + title
                            body = f"NO BET: {conflict}.\n" + why + body
                            sent = notify(title, body, priority="low", link=link, dk=dk, kind="info")
                        else:
                            fd_txt, fd_link, best_book = fd_cmp()
                            sent = notify(title + (" | BEST AT FANDUEL" if best_book == "FanDuel" else ""), (fd_txt + "\n" if fd_txt else "") + why + body, priority=prio, link=link, dk=dk, kind="bet",
                                          fd=fd_link, best=best_book)
                    for n, bt in pending:
                        new.append(dict(alerted_at_et=str(NOW), model=n, both_models=len(pending) > 1, game_id=g["game_id"], date=M["date"],
                                        home=g["home"], away=g["away"], tip_et=g["tip_et"], market=mk, side=side, line=lnum, price=price,
                                        open_price=oprice, model_prob=round(bt[3], 4), ev=round(bt[4], 4), goalies=goalies_txt, sent=sent,
                                        skipped=skip or (conflict if not skip else None),
                                        open_only=is_open_only(n, price), remind_ok=skip != MOVED_SKIP and not conflict, second_chance=bool(is_sc),
                                        best_book=best_book))
                        (skipped if (skip or conflict) else done).add((g["game_id"], mk, n))
                    print(("CAUTION " if skip else "") + "ALERT:", title, "|", skip or "")
    # ---- DON'T BET follow-up: a pushed bet alert, still not logged, that no longer meets the bar before puck drop
    A2 = pd.concat([A, pd.DataFrame(new)], ignore_index=True) if new else A.copy()
    n_rem = 0
    if len(A2) and "remind_ok" in A2:
        if "reminded_at_et" not in A2: A2["reminded_at_et"] = np.nan
        A2["reminded_at_et"] = A2["reminded_at_et"].astype(object)
        if "resumed_at_et" not in A2: A2["resumed_at_et"] = np.nan
        A2["resumed_at_et"] = A2["resumed_at_et"].astype(object)
        if "last_reminder_at_et" not in A2: A2["last_reminder_at_et"] = np.nan
        A2["last_reminder_at_et"] = A2["last_reminder_at_et"].astype(object)
        ok_ = (A2.remind_ok.astype(str).isin(["True", "1", "1.0"]) & A2.sent.astype(str).isin(["True", "1", "1.0"])
               & A2.skipped.isna())
        for (gid, mk), grp in A2[ok_].groupby(["game_id", "market"]):
            allr = A2[(A2.game_id == gid) & (A2.market == mk)]
            stopped = allr.reminded_at_et.astype(str).str.len().gt(3).any()
            resumed = stopped and allr.resumed_at_et.astype(str).str.len().gt(3).any()      # one DON'T BET and one BACK IN RANGE max
            t_last = grp.alerted_at_et.max(); rows = grp[grp.alerted_at_et == t_last]; r = rows.iloc[0]
            gi = GINFO.get(gid)
            if gi is None or pd.Timestamp(gi["tip_et"]) <= NOW: continue
            logged = len(MYB) and ((MYB.date.astype(str) == str(r.date)) & (MYB.home.astype(str).str.lower() == r.home) &
                                   (MYB.away.astype(str).str.lower() == r.away) & (MYB.market == mk)).any()
            if logged: continue
            nowv = [(m, NOWC.get((gid, mk, r.side, m))) for m in rows.model]
            nowv = [(m, v) for m, v in nowv if v is not None]
            if not nowv: continue
            m_best, (lnum, price, p, ev, oprice) = max(nowv, key=lambda x: x[1][3])
            thr = THRESHOLD if str(r.get("second_chance", "")) in ("True", "1", "1.0") else thr_for(mk, price, oprice)
            longshot_gone = m_best in OPEN_ONLY_LONGSHOTS and price >= OPEN_ONLY_LONGSHOTS[m_best] and not near_open(price, oprice)
            ok_now = ev >= thr and not longshot_gone
            # Nov 4, 2026: a moneyline still within NEAR_OPEN of the alerted price stays a bet even if EV dipped under the bar
            ml_hold = (ML_HOLD_NEAR_ALERT and mk == "moneyline" and not ok_now and not pd.isna(r.price) and not pd.isna(price)
                       and abs(1 / espn.nd_dec(price) - 1 / espn.nd_dec(float(r.price))) <= NEAR_OPEN
                       # Fable review (Nov 4): only a PRICE-driven dip is held; if the model itself moved (goalie news, side flip),
                       # EV going negative or the win chance falling 2+ pts still gets the DON'T BET
                       and ev >= 0 and (pd.isna(pd.to_numeric(r.get("model_prob"), errors="coerce"))
                                        or float(p) >= float(r.get("model_prob")) - 0.02))
            if ml_hold: ok_now = True
            pin_txt = None
            if PIN_FOLLOWUP and USE_PINNACLE_RULE and ok_now and mk == "moneyline" and gi.get("pin") is not None and not pd.isna(gi.get("ph_open")):
                d_ = (gi["pin"] - gi["ph_open"]) if r.side == "home" else (gi["ph_open"] - gi["pin"])
                if d_ < -PIN_DISAGREE:
                    pin_txt = (f"Pinnacle (the sharp book) has now opened and gives this side {abs(d_) * 100:.1f} win-% points less than "
                               f"DraftKings' opener; bets Pinnacle disagrees with lost every season 2021-26")
            def remind():
                """REMINDER push every REMIND_EVERY_MIN minutes, REMIND_HOURS only, while still a bet and not logged"""
                if not (REMIND_HOURS[0] <= NOW.hour < REMIND_HOURS[1]): return 0
                refs = [x for x in list(allr.last_reminder_at_et) + list(allr.resumed_at_et) + [t_last] if isinstance(x, str) and len(x) > 3]
                ref = max(pd.Timestamp(x) for x in refs)
                if NOW - ref < pd.Timedelta(minutes=remind_gap_min(gi["tip_et"], NOW)): return 0
                team = gi["H"] if r.side == "home" else (gi["Aw"] if r.side == "away" else str(r.side).upper())
                what = (f"{team} ML {fmt_price(price)}" if mk == "moneyline" else
                        (f"{team} {lnum:+g} ({fmt_price(price)})" if mk == "puck line" else f"{str(r.side).upper()} {lnum:g} ({fmt_price(price)})"))
                try:
                    if ml_hold: floor_txt = (f"Bet only at {fmt_price(american(1 / (1 / espn.nd_dec(float(r.price)) + NEAR_OPEN)))} or better "
                                             f"(within 1.5 win-% points of the alerted {fmt_price(r.price)}).\n")
                    else: floor_txt = f"Bet only at {fmt_price(open_only_floor(p, oprice, thr))} or better (stop if DraftKings shows a shorter price).\n"
                except Exception: floor_txt = f"Bet only at {fmt_price(price)} or better.\n"
                body = floor_txt + (f"REMINDER: still a bet and not logged yet (alerted {pd.Timestamp(t_last):%a %-I:%M %p}). EV {ev:+.1%} at {fmt_price(price)}; "
                                    f"[{SHORT.get(m_best, m_best)}] win chance {p:.1%}. Goalies: {gi['goalies']}. If you already bet it, log it to stop these.")
                rlink = log_link(str(r.date), r.away, r.home, mk, team if mk != "total" else r.side,
                                 "" if mk == "moneyline" else f"{lnum:+g}" if mk == "puck line" else f"{lnum:g}", f"{price:+.0f}")
                fdt, fdl, bb = fanduel.compare("nhl", str(r.date), r.home, r.away, mk, r.side, None if mk == "moneyline" else lnum, price,
                                               label=(team if mk != "total" else str(r.side)))
                if fdt: body = fdt + "\n" + body
                notify(f"REMINDER - BET {what}: {gi['Aw']} @ {gi['H']}, {gi['tip']}", body, priority="default", tags="alarm_clock",
                       link=rlink, dk=DKC.get((gid, mk, r.side), DK_NHL), kind="bet", fd=fdl, best=bb)
                A2.loc[rows.index, "last_reminder_at_et"] = str(NOW)[:16]; print("REMINDER:", what); return 1
            if resumed:
                same_line = mk == "moneyline" or (not pd.isna(lnum) and float(lnum) == float(r.line))
                if ok_now and not pin_txt and same_line and espn.nd_dec(price) >= espn.nd_dec(float(r.price)): n_rem += remind()
                continue
            if stopped:
                # BACK IN RANGE (Nov 2, 2026): after a DON'T BET, it qualifies again at a price no worse than the original alert
                same_line = mk == "moneyline" or (not pd.isna(lnum) and float(lnum) == float(r.line))
                if not (ok_now and not pin_txt and same_line and espn.nd_dec(price) >= espn.nd_dec(float(r.price))): continue
                team = gi["H"] if r.side == "home" else (gi["Aw"] if r.side == "away" else str(r.side).upper())
                what = (f"{team} ML {fmt_price(price)}" if mk == "moneyline" else
                        (f"{team} {lnum:+g} ({fmt_price(price)})" if mk == "puck line" else f"{str(r.side).upper()} {lnum:g} ({fmt_price(price)})"))
                try: floor_txt = f"Bet only at {fmt_price(open_only_floor(p, oprice, thr))} or better (stop if DraftKings shows a shorter price).\n"
                except Exception: floor_txt = f"Bet only at {fmt_price(price)} or better.\n"
                body = floor_txt + (f"BET: back in range. The DON'T BET earlier no longer applies: EV {ev:+.1%} at {fmt_price(price)}, no worse than the "
                        f"original alert ({fmt_price(r.price)}). [{SHORT.get(m_best, m_best)}] win chance {p:.1%}. Goalies: {gi['goalies']}."
                        + " Bet it now if you still want it; log it after.")
                fdt, fdl, bb = fanduel.compare("nhl", str(r.date), r.home, r.away, mk, r.side, None if mk == "moneyline" else lnum, price,
                                               label=(team if mk != "total" else str(r.side)))
                if fdt: body = fdt + "\n" + body
                notify(f"BACK IN RANGE - BET {what}: {gi['Aw']} @ {gi['H']}, {gi['tip']}", body, priority="high", tags="white_check_mark", kind="bet",
                       dk=DKC.get((gid, mk, r.side), DK_NHL), fd=fdl, best=bb)
                A2.loc[rows.index, "resumed_at_et"] = str(NOW)[:16]; n_rem += 1
                print("BACK IN RANGE:", what); continue
            if ok_now and not pin_txt:
                n_rem += remind(); continue
            team = gi["H"] if r.side == "home" else (gi["Aw"] if r.side == "away" else str(r.side).upper())
            what = (f"{team} ML {fmt_price(price)}" if mk == "moneyline" else
                    (f"{team} {lnum:+g} ({fmt_price(price)})" if mk == "puck line" else f"{str(r.side).upper()} {lnum:g} ({fmt_price(price)})"))
            why = pin_txt or (f"EV now {ev:+.1%} at {fmt_price(price)}, below the {thr:.0%} bar"
                   + (" (opening-price-only long shot and the price has moved)" if longshot_gone else ""))
            body = (f"DON'T BET: {why}.\nThe bet alert at {pd.Timestamp(t_last):%-I:%M %p} was at {fmt_price(r.price)} "
                    f"(EV {float(r.ev):+.1%}); no bet is logged for it. [{SHORT.get(m_best, m_best)}] win chance now {p:.1%}.\n"
                    f"Goalies: {gi['goalies']}." + (" Both confirmed." if gi["conf"] else " Not both confirmed yet.")
                    + " If you did bet it, log it and ignore this.")
            notify(f"DON'T BET - {what}: {gi['Aw']} @ {gi['H']}, {gi['tip']}", body, priority="high", tags="no_entry", kind="stop")
            A2.loc[rows.index, "reminded_at_et"] = str(NOW)[:16]; n_rem += 1
            print("DON'T BET:", what, why)
    if new or n_rem:
        A2.to_csv(apath, index=False)
    # ---- line jumps: fast moves, logged for research and alerted when large
    jpath = os.path.join(STATE, "line_jumps.csv")
    J = pd.read_csv(jpath) if os.path.exists(jpath) else pd.DataFrame(columns=["game_id", "market", "detected_at_et"])
    allh = pd.concat([H_, pd.DataFrame(hist_new)], ignore_index=True)
    jumps_new = []
    if len(allh):
        allh["t"] = pd.to_datetime(allh.seen_at_et)
        for (gid, market), rows in allh.groupby(["game_id", "market"]):
            if gid not in info or market == "puck line": continue      # puck line moves follow the moneyline
            rows = rows.sort_values("t"); t_cur = rows.t.iloc[-1]
            val = (lambda r: float(r.prob)) if market == "moneyline" else (lambda r: float(r.line))
            cur = val(rows.iloc[-1]); start = NOW - pd.Timedelta(minutes=JUMP_WINDOW_MIN)
            before = rows[rows.t <= start]; ref_row = before.iloc[-1] if len(before) else rows.iloc[0]
            ref, t_ref = val(ref_row), ref_row.t
            move = cur - ref
            big = abs(move) >= (JUMP_LOG_PROB if market == "moneyline" else 0.5)
            if not big or t_cur < start: continue
            recent = J[(J.game_id == gid) & (J.market == market)]
            if len(recent) and pd.to_datetime(recent.detected_at_et).max() >= start: continue
            moving = rows[rows.t > start]; t_move = moving.t.iloc[0] if len(moving) else t_cur
            g, M2 = info[gid]
            mod = 100 * float(nm.market_probs(np.array([g["morning_lam_home"]]), np.array([g["morning_lam_away"]]), M2["h_ot"], M2["cal"]["open"])["home_win"][0]) \
                if market == "moneyline" else g["morning_lam_home"] + g["morning_lam_away"]
            toward = (move > 0) == (mod > ref)
            win_news = []
            if NEWS is not None:
                for team in (g["away"], g["home"]):
                    for when, text in NEWS.get(team, []):
                        if when.replace(tzinfo=None) >= t_ref - pd.Timedelta(minutes=30):
                            win_news.append(f"{team.upper()} {when:%-I:%M %p}: {text}")
            tipd = pd.Timestamp(g["tip_et"])
            alert_it = abs(move) >= (JUMP_ALERT_PROB if market == "moneyline" else 1.0)
            row = dict(detected_at_et=str(NOW)[:16], game_id=gid, date=M2["date"], away=g["away"], home=g["home"], market=market,
                       from_line=round(ref, 1), to_line=round(cur, 1), move=round(move, 1), steady_since=str(t_ref)[:16], move_started=str(t_move)[:16],
                       move_seen=str(t_cur)[:16], minutes=int((t_cur - t_move).total_seconds() // 60),
                       hours_to_tip=round((tipd - t_cur).total_seconds() / 3600, 1), model=round(mod, 1),
                       direction="toward model" if toward else "away from model", news_in_window=" | ".join(win_news),
                       news_count=len(win_news), alerted=alert_it)
            jumps_new.append(row)
            if alert_it:
                H2, A2 = g["home"].upper(), g["away"].upper()
                what = f"{H2} win chance {ref:.0f}% -> {cur:.0f}%" if market == "moneyline" else f"total {ref:g} -> {cur:g}"
                speed = (f"within one check (seen {t_cur:%-I:%M %p})" if row["minutes"] < 5
                         else f"over about {row['minutes']} min ({t_move:%-I:%M} to {t_cur:%-I:%M %p})")
                body = (f"Moved {speed}; steady since {t_ref:%a %-I:%M %p}. {row['hours_to_tip']:.1f} h before puck drop. "
                        f"Model: {mod:.0f}% home" if market == "moneyline" else
                        f"Moved {speed}; steady since {t_ref:%a %-I:%M %p}. {row['hours_to_tip']:.1f} h before puck drop. Model total {mod:.2f}")
                body += f" ({'toward' if toward else 'away from'} the model)." + history_text(gid, market)
                body += ("\nNews around the move:\n- " + "\n- ".join(win_news[:6])) if win_news else \
                        "\nNo injury news reported around the move yet: possibly a goalie announcement, breaking news or big bets."
                notify(f"Line jump: {A2} @ {H2} {what}", body, priority="default", tags="zap")
                print("LINE JUMP:", what, "|", body)
    if gtest_new: pd.concat([GT, pd.DataFrame(gtest_new)], ignore_index=True).to_csv(gpath, index=False)
    if grtest_new: pd.concat([GR, pd.DataFrame(grtest_new)], ignore_index=True).to_csv(grpath, index=False)
    if rtest_new: pd.concat([RT, pd.DataFrame(rtest_new)], ignore_index=True).to_csv(rpath, index=False)
    if jumps_new: pd.concat([J, pd.DataFrame(jumps_new)], ignore_index=True).to_csv(jpath, index=False)
    if hist_new: pd.concat([H_, pd.DataFrame(hist_new)], ignore_index=True).to_csv(hpath, index=False)
    if moves_new: pd.concat([MV, pd.DataFrame(moves_new)], ignore_index=True).to_csv(mpath, index=False)
    # ---- research database (never allowed to break alerts)
    try:
        import research
        research.init(W)
        n_odds = n_pred = n_spl = n_bk = n_g = 0
        for mf in models:
            M3 = load_models(os.path.join(STATE, mf)); M3 = dict(date=M3["date"], games=next(iter(M3["models"].values()))["games"])
            try:
                k, rows = research.odds_snapshot(NOW, M3["date"], M3["games"]); n_odds += k
                n_pred += research.predictor_snapshot(NOW, M3["date"], rows)
            except Exception as e:
                print("ESPN research logging skipped:", type(e).__name__, str(e)[:120])
            try:
                a, b = research.splits_snapshot(NOW, M3["date"], M3["games"]); n_spl += a; n_bk += b
            except Exception as e:
                print("Betting splits logging skipped:", type(e).__name__, str(e)[:120])
            try:
                n_g += research.goalie_snapshot(NOW, M3["date"], M3["games"])
            except Exception as e:
                print("Goalie logging skipped:", type(e).__name__, str(e)[:120])
        n_news = research.news_log(NOW, NEWS) if NEWS is not None else 0
        n_mod = research.model_snapshot(NOW, model_rows)
        print(f"Research log: {n_odds} odds changes, {n_pred} predictor snapshots, {n_spl} betting-split changes, "
              f"{n_bk} book line changes, {n_g} goalie changes, {n_news} new news notes, {n_mod} model changes.")
    except Exception as e:
        print("Research logging skipped:", type(e).__name__, str(e)[:120])
    n_clean = sum(1 for x in new if not x.get("skipped"))
    print(f"{NOW:%H:%M} ET: checked {n_games} upcoming games, {n_clean} alerts and {len(new) - n_clean} caution alerts sent.")


if __name__ == "__main__":
    main()
