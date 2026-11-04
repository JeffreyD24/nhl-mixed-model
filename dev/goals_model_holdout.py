"""NHL GOALS model vs the SHOT model on the 2017-22 holdout, same games, same goalie data, same rules
(pre-registered: backtests/GOALS_MODEL_PREREG.md).
  python dev/goalie_recal_test.py WORKDIR predict GM          (after oos_sbr_build.py and goalie_recal_test.py build; G1 predictions already exist)
  python dev/goals_model_holdout.py WORKDIR score             -> backtests/goals_model_output.txt
  python dev/goals_model_holdout.py WORKDIR pipeline          -> bug check on 2015-16 only, prints, writes nothing"""
import os, sys
import numpy as np, pandas as pd
W = os.path.abspath(sys.argv[1]); MODE = sys.argv[2]
sys.argv = [sys.argv[0], W, "x"]; sys.path.insert(0, W); sys.path.insert(0, os.path.join(W, "dev"))
import goalie_recal_test as g

SEAS = g.HOLDOUT if MODE == "score" else g.PIPELINE
lines = []
def say(*a):
    lines.append(" ".join(str(x) for x in a)); print(*a, flush=True)


def prep(V):
    P = g.load(V); P = P[P.season.isin(SEAS)].copy()
    P["p_blend"] = 0.55 * P.p_home_win_open + 0.45 * P.nv_open
    return P


def main():
    P1, PG = prep("G1"), prep("GM")
    say(f"NHL goals model (GM) vs shot model (G1), same goalie data, {SEAS[0]}-{SEAS[-1]} "
        f"({'HOLDOUT' if MODE == 'score' else 'PIPELINE CHECK, not a result'}). Pre-registered: backtests/GOALS_MODEL_PREREG.md. Trusted rows unless noted.")
    for s in SEAS:
        import json
        m = json.load(open(os.path.join(g.TMP, f"gr_GM_meta_{s}.json")))["summary"]
        say(f"  GM {s}: sd_goalie {m['sd_goalie']:.3f}, sd_offense {m['sd_offense']:.3f}, sd_defense {m['sd_defense']:.3f}, half-life {m['chosen_halflife']}")

    say("\n1. Accuracy on every game (home win): log loss / Brier; lower is better")
    for lab, P, c in (("opener (no-vig)", P1, "nv_open"), ("closer (no-vig)", P1, "nv_close"), ("G1 shot model", P1, "p_home_win_open"),
                      ("GM goals model", PG, "p_home_win_open"), ("G1 shot + 55/45 blend", P1, "p_blend"), ("GM goals + 55/45 blend", PG, "p_blend")):
        Q = P.dropna(subset=["y", c, "nv_open", "nv_close"])
        by = " ".join(f"{str(s)[2:]}:{g.ll(x[c], x.y):.4f}" for s, x in Q.groupby("season"))
        say(f"  {lab:26s} logloss {g.ll(Q[c], Q.y):.4f}  Brier {np.mean((Q[c] - Q.y) ** 2):.4f}  n={len(Q)}  by season {by}")

    say("\n2. Bet rules at the opening price (1 unit). CLV = win-% points the de-vigged line moved toward the bet.")
    B = {}
    spec = [("G1 ML plain EV6", P1, "p_home_win_open", .06, False), ("GM ML plain EV6", PG, "p_home_win_open", .06, False),
            ("G1 ML blend55 EV4 noB2B", P1, "p_blend", .04, True), ("GM ML blend55 EV4 noB2B", PG, "p_blend", .04, True)]
    for name, P, c, thr, sk in spec:
        b = g.bets(P, c, thr, sk, name); b = b[b.trusted == 1]; B[name] = b
        lo, hi = g.boot_days(b, lambda x: x.profit.mean()); clo, chi = g.boot_days(b, lambda x: x.clv.mean())
        ls = b[(b.price >= 150) & (b.price < 250)]
        say(f"  {name:26s} {len(b):5d} bets {np.mean(b.profit > 0):.1%} {b.profit.sum():+7.1f}u ROI {b.profit.mean():+.1%} [{lo:+.1%},{hi:+.1%}]  "
            f"CLV {b.clv.mean():+.2f} [{clo:+.2f},{chi:+.2f}]  +150..+249: n={len(ls)} said {ls.p.mean():.1%} won {ls.win.mean():.1%}")

    say("\n3. Bets only the goals model makes (blend rule), vs bets both make (live finding 2025-26: the goals model's own bets lost -16.6u on 1,026)")
    key = lambda b: set(zip(b.season, b.date, b.home, b.away, b.side))
    kg1 = key(B["G1 ML blend55 EV4 noB2B"]); kgm = key(B["GM ML blend55 EV4 noB2B"])
    bg = B["GM ML blend55 EV4 noB2B"]; b1 = B["G1 ML blend55 EV4 noB2B"]
    tag = lambda b, ks, inside: b[[((k in ks) == inside) for k in zip(b.season, b.date, b.home, b.away, b.side)]]
    for lab, b in (("GM only (shot model did not bet it)", tag(bg, kg1, False)), ("both models bet it", tag(bg, kg1, True)),
                   ("G1 only (goals model did not bet it)", tag(b1, kgm, False))):
        if not len(b): say(f"  {lab}: 0 bets"); continue
        lo, hi = g.boot_days(b, lambda x: x.profit.mean())
        bys = " ".join(f"{str(s)[2:]}:{x.profit.sum():+.0f}" for s, x in b.groupby("season"))
        say(f"  {lab:38s} {len(b):5d} bets {np.mean(b.profit > 0):.1%} {b.profit.sum():+7.1f}u ROI {b.profit.mean():+.1%} [{lo:+.1%},{hi:+.1%}]  CLV {b.clv.mean():+.2f}  by season {bys}")

    say("\n4. Pre-registered decisions (paired CLV difference, 90% interval resampling game days)")
    for lab, a, b in (("Blend rule, GM minus G1", "G1 ML blend55 EV4 noB2B", "GM ML blend55 EV4 noB2B"),
                      ("Plain rule, GM minus G1", "G1 ML plain EV6", "GM ML plain EV6")):
        d, lo, hi = g.paired_clv(B[a], B[b])
        say(f"  {lab}: CLV {d:+.2f} [{lo:+.2f},{hi:+.2f}] -> {'GOALS BETTER' if lo > 0 else ('GOALS WORSE' if hi < 0 else 'NOT SHOWN')}")
    Q = P1.dropna(subset=["y"]).merge(PG[["season", "date", "home", "away", "p_home_win_open"]], on=["season", "date", "home", "away"], suffixes=("", "_gm"))
    a, b = g.ll(Q.p_home_win_open, Q.y), g.ll(Q.p_home_win_open_gm, Q.y)
    say(f"  Log loss shot {a:.4f} vs goals {b:.4f} (n={len(Q)}) -> {'goals more accurate' if b < a else 'shot model more accurate'}")
    own = tag(bg, kg1, False)
    if len(own):
        lo, hi = g.boot_days(own, lambda x: x.profit.mean())
        say(f"  Goals-model-only bets: ROI {own.profit.mean():+.1%} [{lo:+.1%},{hi:+.1%}], CLV {own.clv.mean():+.2f} -> "
            f"{'consistent with the live finding (loses)' if own.profit.mean() < 0 else 'NOT consistent with the live finding'}")

    say("\n5. Overs at the opening total, EV 6%+ (rebuilt over price), trusted rows")
    for lab, P in (("G1 shot", P1), ("GM goals", PG)):
        o = g.overs(P); o = o[o.trusted == 1]
        if not len(o): say(f"  {lab}: 0 bets"); continue
        lo, hi = g.boot_days(o, lambda x: x.profit.mean())
        say(f"  {lab}: {len(o)} bets {np.mean(o.profit > 0):.1%} {o.profit.sum():+.1f}u ROI {o.profit.mean():+.1%} [{lo:+.1%},{hi:+.1%}]  "
            f"total rose {np.mean(o.move > 0):.1%} fell {np.mean(o.move < 0):.1%}")
    if MODE == "score":
        open(os.path.join(W, "backtests", "goals_model_output.txt"), "w").write("\n".join(lines) + "\n")


main()
