"""Live tag: NHL games whose expected or alerted starting goalie is NEW (no regular-season start in the three previous seasons).
Changes no bet rule; it only labels bets that the existing rules already made, so a record builds up over the season.
Why: on SBR 2017-22 the shot model beat the opener in games with a new expected starter (591 games); on DraftKings 2023-26 the
direction matched but only 153 games existed (betting-goals models/tests/NHL_NEW_STARTER_DK_RESULTS.md). Approved by Jeffrey Nov 4, 2026.
  python tools/new_starter_tag.py WORKDIR   -> state/new_starter_tags.csv, research/new_starter/REPORT.md"""
import os, sys, re
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
ST = os.path.join(W, "state"); OUT = os.path.join(W, "research", "new_starter"); os.makedirs(OUT, exist_ok=True)
SEASON = 2027                                   # END year of the current season (2026-27)


def veterans():
    T = pd.read_csv(os.path.join(W, "data", "training_games.csv"))
    T = T[T.season.between(SEASON - 3, SEASON - 1)]
    ids = set(T.home_goalie.dropna().astype(int)) | set(T.away_goalie.dropna().astype(int))
    names = {}
    for f in (os.path.join(W, "data", "box_2025_26.csv"), os.path.join(ST, f"box_{SEASON - 1}_{SEASON % 100:02d}.csv")):
        if os.path.exists(f):
            B = pd.read_csv(f); B = B[B.pos == "G"]
            names.update(dict(zip(B.playerid.astype(int), B.player)))
    vet = {names[i] for i in ids if i in names}
    return vet, len(ids), sum(i in names for i in ids)


def clean(n):
    n = re.sub(r"\s*\(.*?\)\s*$", "", str(n or "")).strip()
    return n


def alert_goalies(txt):
    """'WPG Nico Daws (expected); FLA Akira Schmid (confirmed)' -> ['Nico Daws', 'Akira Schmid']"""
    out = []
    for part in str(txt or "").split(";"):
        part = clean(part)
        if not part: continue
        bits = part.split(" ", 1)
        out.append(bits[1].strip() if len(bits) == 2 and bits[0].isupper() and len(bits[0]) <= 3 else part)
    return out


def summary(df, unit, clv, label):
    d = df.dropna(subset=[unit])
    if not len(d): return f"| {label} | 0 | | | | |"
    w, l = int((d[unit] > 0).sum()), int((d[unit] < 0).sum())
    c = d[clv].dropna()
    return f"| {label} | {len(d)} | {w}-{l} | {d[unit].sum():+.2f} | {d[unit].mean():+.1%} | {c.mean() * 100:+.2f} ({len(c)}) |"


def main():
    vet, n_ids, n_named = veterans()
    is_new = lambda n: bool(n) and n not in vet
    rows = []
    P = pd.read_csv(os.path.join(ST, "picks_log_xg.csv"))
    P = P[P.date >= "2026-10-06"]                          # regular season
    for r in P.itertuples():
        hg, ag = clean(r.home_goalie_exp), clean(r.away_goalie_exp)
        rows.append(dict(source="shot model side at the open, every game", game_id=r.game_id, date=r.date, home=r.home, away=r.away,
                         home_goalie=hg, away_goalie=ag, new_starter=is_new(hg) or is_new(ag), pick_type=r.pick_type,
                         bet=getattr(r, "open_moneyline_bet"), profit=getattr(r, "open_moneyline_profit"), clv=getattr(r, "open_moneyline_clv")))
    A = pd.read_csv(os.path.join(ST, "alerts.csv"))
    A = A[(A.sent == True) | (A.sent.astype(str) == "True")]
    for r in A.itertuples():
        gs = alert_goalies(r.goalies)
        rows.append(dict(source=f"sent alert ({r.model}, {r.market})", game_id=r.game_id, date=r.date, home=r.home, away=r.away,
                         home_goalie="; ".join(gs), away_goalie="", new_starter=any(is_new(g) for g in gs), pick_type="alert",
                         bet=r.side, profit=r.profit, clv=r.clv))
    R = pd.DataFrame(rows)
    bf = os.path.join(ST, f"box_{SEASON - 1}_{SEASON % 100:02d}.csv")
    if os.path.exists(bf):                               # after the game: was the ACTUAL starter new? (grading only, never for a bet)
        B = pd.read_csv(bf); B = B[(B.pos == "G") & (B.starter == 1)]
        act = B.groupby("game_id").player.apply(lambda x: any(is_new(n) for n in x))
        R["actual_new_starter"] = R.game_id.map(act)
    R.to_csv(os.path.join(ST, "new_starter_tags.csv"), index=False)
    L = ["# NHL new-starter tag (live record; no rule changed)", "",
         "A game is tagged when an expected or alerted starting goalie has no regular-season start in the three previous seasons.",
         "Background and backtests: betting-goals models/tests/NHL_NEW_STARTER_DK_RESULTS.md. Judge it by CLV first, then units, after a",
         "few dozen tagged bets; it is a side record only.", "",
         f"Goalies with a start in {SEASON - 3}-{SEASON - 1} (END years): {n_ids}; matched to a name: {n_named}. An expected goalie not "
         "matched counts as new, so unmatched veterans could be mis-tagged; check the names in state/new_starter_tags.csv.", "",
         "| Bets | n | W-L | Units | ROI | CLV, win-% pts (n) |", "|---|---|---|---|---|---|"]
    for src, g in R.groupby("source"):
        bets = g[g.bet.notna() & (g.bet.astype(str) != "")]
        L.append(summary(bets[bets.new_starter], "profit", "clv", f"{src}: NEW starter"))
        L.append(summary(bets[~bets.new_starter], "profit", "clv", f"{src}: other"))
    if "actual_new_starter" in R:
        L.append(summary(R[(R.source == "shot model side at the open, every game") & (R.actual_new_starter == True)], "profit", "clv",
                         "shot model side at the open, every game: ACTUAL starter new (after the fact, descriptive)"))
    L += ["", "The 'every game' rows are the model's side in every game, not the alert rule; they show direction, not a bettable record."]
    newg = R[(R.source == "shot model side at the open, every game") & R.new_starter]
    L += ["", f"Tagged games so far (shot-model picks log): {len(newg)} of {int((R.source == 'shot model side at the open, every game').sum())}.", ""]
    if len(newg):
        L += ["| Date | Game | Home goalie | Away goalie |", "|---|---|---|---|"]
        for r in newg.sort_values("date").itertuples():
            L.append(f"| {r.date} | {r.away} @ {r.home} | {r.home_goalie}{' (new)' if is_new(r.home_goalie) else ''} | {r.away_goalie}{' (new)' if is_new(r.away_goalie) else ''} |")
    open(os.path.join(OUT, "REPORT.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
