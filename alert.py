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

THRESHOLD = 0.06                    # expected value at the current price (6% = +0.06 units per unit risked)
ALERT_MARKETS = ("moneyline", "puck line")   # add "total" to alert on totals too (they lost money in the backtests)
MAX_MOVE = 5.0                      # caution when the home win chance implied by the moneyline moved this many points AGAINST the bet since open
JUMP_WINDOW_MIN = 60                # a "jump" is a move within this many minutes
JUMP_LOG_PROB = 3.0                 # log moneyline moves of at least this many win-probability points (and any change in the total)
JUMP_ALERT_PROB = 5.0               # send a "Line jump" notification at this size (and for totals moving a full goal)
P_MISS = {"Out": 1.0, "Injured Reserve": 1.0, "Long Term Injured Reserve": 1.0, "Suspension": 1.0, "Suspended": 1.0, "Day-To-Day": 0.5}
WINDOW = None                       # None = check all day; or (16, 0, 19, 0) for 4:00-7:00 PM ET
ET = ZoneInfo("America/New_York")
STATE = os.path.join(W, "state")
NOW = pd.Timestamp(dt.datetime.now(ET).replace(tzinfo=None))
TODAY = NOW.normalize()


def in_window():
    if WINDOW is None: return True
    start = TODAY + pd.Timedelta(hours=WINDOW[0], minutes=WINDOW[1]); end = TODAY + pd.Timedelta(hours=WINDOW[2], minutes=WINDOW[3])
    return start <= NOW < end


def fair(a, b):
    if pd.isna(a) or pd.isna(b): return np.nan
    ia, ib = 1 / espn.nd_dec(a), 1 / espn.nd_dec(b); return ia / (ia + ib)


def log_link(date, away, home, market, pick, line, odds):
    repo = os.environ.get("GITHUB_REPOSITORY", "JeffreyD24/nhl-mixed-model")
    desc = f"{pick.upper()} {'ML' if market == 'moneyline' else line}"
    q = dict(template="log-bet.yml", title=f"Bet: {desc} {away.upper()} @ {home.upper()} {date}", game_date=date, away=away.upper(),
             home=home.upper(), market=market, pick=pick.upper() if market != "total" else pick, line=line, odds=odds)
    return f"https://github.com/{repo}/issues/new?" + urllib.parse.urlencode(q)


def notify(title, body, priority="high", tags="ice_hockey", link=None):
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC not set; would have sent:", title, "|", body); return False
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=body.encode("utf-8"), method="POST",
                                 headers={"Title": title.encode("ascii", "ignore").decode(), "Priority": priority, "Tags": tags,
                                          **({"Actions": f"view, Log this bet, {link}"} if link else {})})
    urllib.request.urlopen(req, timeout=20)
    return True


def fmt_price(o): return "" if pd.isna(o) else f"{o:+.0f}"


def main():
    if "--test" in sys.argv:
        topic = os.environ.get("NTFY_TOPIC") or ""
        try:
            ok = notify("Test alert: NHL tracker connected", "If you can read this, phone alerts from your NHL GitHub tracker are working. No bet here.")
            msg = (f"sent OK to a topic {len(topic)} characters long, starting with '{topic[:2]}'" if ok
                   else "NOT sent: the NTFY_TOPIC secret is missing or empty")
        except Exception as e:
            msg = f"NOT sent: ntfy returned an error ({type(e).__name__}: {str(e)[:80]})"
        open(os.path.join(STATE, "test_alert_result.txt"), "w").write(f"{NOW}: test alert {msg}\n")
        print("Test alert", msg); return
    if not FORCE and not in_window():
        print(f"{NOW:%H:%M} ET is outside the alert window; nothing to do."); return
    models = sorted(f for f in os.listdir(STATE) if f.startswith("model_") and f[6:16] >= str(TODAY.date()))
    if not models: print("No model saved for today or tomorrow yet."); return
    try:
        FEED = espn.injury_feed()
    except Exception as e:
        FEED = None; print("Injury feed unavailable:", type(e).__name__)
    NEWS = espn.injury_news(hours=24, feed=FEED) if FEED is not None else None
    status_of = {}
    for team, items in (FEED or {}).items():
        for pid, name, st, _, _ in items:
            if pid: status_of[pid] = st

    apath = os.path.join(STATE, "alerts.csv")
    A = pd.read_csv(apath) if os.path.exists(apath) else pd.DataFrame(columns=["game_id", "market", "skipped"])
    if len(A) and "sent" in A:          # an alert that couldn't be delivered (e.g. no ntfy topic yet) is tried again next check
        A = A[A.sent.astype(str) == "True"].reset_index(drop=True)
    done = set(zip(A[A.skipped.isna()].game_id, A[A.skipped.isna()].market)) if len(A) else set()
    skipped = set(zip(A[A.skipped.notna()].game_id, A[A.skipped.notna()].market)) if len(A) else set()
    graded = A[A.result.isin(["W", "L"]) & A.skipped.isna()] if "result" in A else A.iloc[:0]
    rec = (f"{int((graded.result == 'W').sum())}-{int((graded.result == 'L').sum())}, {graded.profit.sum():+.1f}u" if len(graded) else "no graded alerts yet")
    cg = A[A.result.isin(["W", "L"]) & A.skipped.notna()] if "result" in A else A.iloc[:0]
    crec = f"{int((cg.result == 'W').sum())}-{int((cg.result == 'L').sum())}" if len(cg) else "none graded yet"
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

    for mf in models:
        M = json.load(open(os.path.join(STATE, mf)))
        day = pd.Timestamp(M["date"]); gval = {int(k): v for k, v in M["goalies"].items()}
        gname = {int(k): v for k, v in M.get("goalie_names", {}).items()}
        try:
            SB = {(r["home"], r["away"]): r for r in nd.scoreboard(day)}
        except Exception as e:
            SB = {}; print("Scoreboard unavailable:", type(e).__name__)
        L = espn.lines([day], when=("open", "current"))
        for g in M["games"]:
            info[g["game_id"]] = (g, M)
            line = L[(L.home == g["home"]) & (L.away == g["away"])] if len(L) else L
            if not len(line) or line.iloc[0].get("state") not in (None, "pre"): continue
            n_games += 1
            ln = line.iloc[0]
            pr = SB.get((g["home"], g["away"]), {}).get("probables", {})

            def goalie(def_side):
                """(effect, label, confirmed) for the goalie facing the other team"""
                p = pr.get(def_side)
                if p:
                    pid, name, st = p
                    return gval.get(int(pid), 0.0), f"{name} ({(st or 'listed').lower()})", st == "Confirmed", True
                mix = {int(k): w for k, w in g[f"{def_side}_gmix"].items()}
                top = max(mix.items(), key=lambda x: x[1]) if mix else (None, 0)
                return (sum(w * gval.get(k, 0.0) for k, w in mix.items()),
                        f"{gname.get(top[0], 'unknown')} ({top[1]:.0%} likely, not announced)" if top[0] else "unknown", False, False)

            def missing(side):
                tot, out = 0.0, []
                for pid, (name, val, missed_last) in g[f"{side}_regulars"].items():
                    st = status_of.get(int(pid)) if FEED is not None else None
                    pm = P_MISS.get(st, 0.0) if st else (1.0 if missed_last else 0.0)
                    if pm > 0: tot += pm * val; out.append(name.split()[-1] + ("" if pm == 1 else "?"))
                return tot, out
            gh_v, gh_lab, gh_conf, gh_known = goalie("home"); ga_v, ga_lab, ga_conf, ga_known = goalie("away")
            mh, outs_h = missing("home"); ma, outs_a = missing("away")
            lam_h = g["base_home"] + M["c_miss"] * mh + ga_v
            lam_a = g["base_away"] + M["c_miss"] * ma + gh_v
            cal = M["cal"]["pretip" if (gh_known and ga_known) else "open"]
            mp = nm.market_probs(np.array([lam_h]), np.array([lam_a]), M["h_ot"], cal)
            p_home, p_hby2, p_aby2 = float(mp["home_win"][0]), float(mp["home_by2"][0]), float(mp["away_by2"][0])
            exp_total = float(lam_h + lam_a + nm.raw_probs(np.array([lam_h]), np.array([lam_a]), M["h_ot"])["tie"][0])
            goalies_txt = f"{g['away'].upper()} {ga_lab}; {g['home'].upper()} {gh_lab}"
            model_rows.append(dict(seen_at_et=str(NOW)[:16], game_id=g["game_id"], date=M["date"], away=g["away"], home=g["home"],
                                   model_home_win=round(p_home, 4), lam_home=round(lam_h, 3), lam_away=round(lam_a, 3),
                                   model_total=round(exp_total, 2), away_goalie=ga_lab, home_goalie=gh_lab,
                                   missing=f"{g['away'].upper()}: {', '.join(outs_a) or '-'} | {g['home'].upper()}: {', '.join(outs_h) or '-'}"))
            c, o = {k: ln.get(f"current_{k}") for k in espn.MARKET_COLS}, {k: ln.get(f"open_{k}") for k in espn.MARKET_COLS}
            ph_now, ph_open = fair(c["home_ml"], c["away_ml"]), fair(o["home_ml"], o["away_ml"])
            record_line(g["game_id"], "moneyline", c["home_ml"], f"{g['away'].upper()} {fmt_price(c['away_ml'])} / {g['home'].upper()} {fmt_price(c['home_ml'])}", 100 * ph_now)
            record_line(g["game_id"], "total", c["total"], f"o{fmt_price(c['over_odds'])}/u{fmt_price(c['under_odds'])}", 100 * fair(c["over_odds"], c["under_odds"]))
            tip = pd.Timestamp(g["tip_et"]).strftime("%a %-I:%M %p")
            H, Aw = g["home"].upper(), g["away"].upper()
            # candidate bets at the current prices
            cands = []
            if not pd.isna(c["home_ml"]):
                for side, p, price in (("home", p_home, c["home_ml"]), ("away", 1 - p_home, c["away_ml"])):
                    cands.append(("moneyline", side, np.nan, price, p, o[f"{side}_ml"]))
            if not pd.isna(c["home_pl"]):
                hl = c["home_pl"]; p_hc = p_hby2 if hl < 0 else 1 - p_aby2
                cands += [("puck line", "home", hl, c["home_pl_odds"], p_hc, o["home_pl_odds"] if o["home_pl"] == hl else np.nan),
                          ("puck line", "away", -hl, c["away_pl_odds"], 1 - p_hc, o["away_pl_odds"] if o["home_pl"] == hl else np.nan)]
            if not pd.isna(c["total"]):
                po, pu, pp = nm.over_prob(np.array([lam_h]), np.array([lam_a]), np.array([c["total"]]), M["h_ot"], cal)
                same = o["total"] == c["total"]
                cands += [("total", "over", c["total"], c["over_odds"], float(po[0]), o["over_odds"] if same else np.nan),
                          ("total", "under", c["total"], c["under_odds"], float(pu[0]), o["under_odds"] if same else np.nan)]
            best = {}
            for mk, side, lnum, price, p, oprice in cands:
                if pd.isna(price): continue
                ev = p * espn.nd_dec(price) - 1
                if mk not in best or ev > best[mk][4]: best[mk] = (side, lnum, price, p, ev, oprice)
            for mk in ("moneyline", "puck line", "total"):
                hist_txt = history_text(g["game_id"], "total" if mk == "total" else "moneyline")
                if mk not in best or mk not in ALERT_MARKETS or (g["game_id"], mk) in done: continue
                side, lnum, price, p, ev, oprice = best[mk]
                team = H if side == "home" else (Aw if side == "away" else side.upper())
                what = (f"{team} ML {fmt_price(price)}" if mk == "moneyline" else
                        (f"{team} {lnum:+g} ({fmt_price(price)})" if mk == "puck line" else f"{side.upper()} {lnum:g} ({fmt_price(price)})"))
                title = f"Bet {what}: {Aw} @ {H}, {tip}"
                body = (f"Model: {team if mk != 'total' else side} {p:.1%} to win this bet; DraftKings {fmt_price(price)} needs {1 / espn.nd_dec(price):.1%}. "
                        f"Expected value {ev:+.1%}.")
                if not pd.isna(oprice):
                    ev_o = p * espn.nd_dec(oprice) - 1
                    body += (" (opening price)" if oprice == price else f" Opened {fmt_price(oprice)} (EV then {ev_o:+.1%}).")
                body += f" Model score: {Aw} {lam_a:.2f}, {H} {lam_h:.2f} in regulation; total {exp_total:.2f}."
                # moneyline movement since open, from the home side, in win-probability points
                move = 100 * (ph_now - ph_open) if not (pd.isna(ph_now) or pd.isna(ph_open)) else 0.0
                bet_home = side == "home" or (mk == "total" and False)
                toward = mk != "total" and abs(move) >= MAX_MOVE and ((move > 0) == bet_home)
                against = mk != "total" and abs(move) >= MAX_MOVE and ((move > 0) != bet_home)
                if ev < THRESHOLD:
                    if toward and (g["game_id"], mk) not in moved_done:
                        notify(f"Market agrees: {Aw} @ {H} {mk}, {tip}",
                               f"The moneyline moved {abs(move):.1f} win-% points toward the model's side ({team}) since open. "
                               f"EV left at {what}: {ev:+.1%} (under {THRESHOLD:.0%}, so no bet). Info only." + hist_txt + news_for(g),
                               priority="low", tags="chart_with_upwards_trend")
                        moves_new.append(dict(at_et=str(NOW), game_id=g["game_id"], date=M["date"], home=g["home"], away=g["away"], market=mk,
                                              model_side=side, open_home_prob=round(100 * ph_open, 1), home_prob=round(100 * ph_now, 1),
                                              move=round(move, 1), model_home_prob=round(100 * p_home, 1), ev_left=round(ev, 4)))
                        moved_done.add((g["game_id"], mk))
                    continue
                skip = None
                if not (gh_conf and ga_conf): skip = "starting goalies not both confirmed yet"
                elif against: skip = f"the moneyline moved {abs(move):.1f} win-% points against this side since open"
                odds_s = f"{price:+.0f}"
                link = log_link(M["date"], g["away"], g["home"], mk, team if mk != "total" else side,
                                "" if mk == "moneyline" else f"{lnum:+g}" if mk == "puck line" else f"{lnum:g}", odds_s)
                row = dict(alerted_at_et=str(NOW), game_id=g["game_id"], date=M["date"], home=g["home"], away=g["away"], tip_et=g["tip_et"],
                           market=mk, side=side, line=lnum, price=price, open_price=oprice, model_prob=round(p, 4), ev=round(ev, 4),
                           goalies=goalies_txt, sent=False, skipped=skip)
                tail = f"\nGoalies: {goalies_txt}."
                if outs_a or outs_h: tail += f"\nMissing: {Aw} {', '.join(outs_a) or 'none'}; {H} {', '.join(outs_h) or 'none'}."
                if skip:
                    if (g["game_id"], mk) not in skipped:
                        cbody = body + f"\nCAUTION: {skip}. The model may be missing news here; bet with caution." + tail + \
                                f"\nCaution alerts so far: {crec}." + hist_txt + news_for(g)
                        row["sent"] = notify("CAUTION - " + title, cbody, priority="default", tags="warning,ice_hockey", link=link)
                        new.append(row); skipped.add((g["game_id"], mk)); print("CAUTION ALERT:", title, "|", skip)
                    continue
                if toward:
                    body += f" Market agrees: the moneyline has moved {abs(move):.1f} win-% points toward this side since open."
                    moved_done.add((g["game_id"], mk))
                body += tail + f"\nAlerts so far: {rec}. Tracking test: the model has not yet proven an edge live." + hist_txt + news_for(g)
                row["sent"] = notify(title, body, link=link)
                new.append(row); done.add((g["game_id"], mk)); print("ALERT:", title, "|", body)
    if new:
        pd.concat([A, pd.DataFrame(new)], ignore_index=True).to_csv(apath, index=False)
    # ---- line jumps: fast moves, logged for research and alerted when large
    jpath = os.path.join(STATE, "line_jumps.csv")
    J = pd.read_csv(jpath) if os.path.exists(jpath) else pd.DataFrame(columns=["game_id", "market", "detected_at_et"])
    allh = pd.concat([H_, pd.DataFrame(hist_new)], ignore_index=True)
    jumps_new = []
    if len(allh):
        allh["t"] = pd.to_datetime(allh.seen_at_et)
        for (gid, market), rows in allh.groupby(["game_id", "market"]):
            if gid not in info: continue
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
    if jumps_new: pd.concat([J, pd.DataFrame(jumps_new)], ignore_index=True).to_csv(jpath, index=False)
    if hist_new: pd.concat([H_, pd.DataFrame(hist_new)], ignore_index=True).to_csv(hpath, index=False)
    if moves_new: pd.concat([MV, pd.DataFrame(moves_new)], ignore_index=True).to_csv(mpath, index=False)
    # ---- research database (never allowed to break alerts)
    try:
        import research
        research.init(W)
        n_odds = n_pred = n_spl = n_bk = n_g = 0
        for mf in models:
            M3 = json.load(open(os.path.join(STATE, mf)))
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
