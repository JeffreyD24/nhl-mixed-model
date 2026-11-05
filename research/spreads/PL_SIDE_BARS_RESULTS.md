# Results: separate EV bars for -1.5 and +1.5 puck lines (Nov 5, 2026)

Pre-registration: `research/spreads/PL_SIDE_BARS_PREREG.md` (pushed in commit 87f5e0b, before any test ran).
Code: `analysis/pl_side_bars.py`. Full output: `analysis/pl_side_bars_output.txt`.
Older-season predictions: `dev/oos_sbr_build.py` + `dev/goalie_recal_test.py ... predict G1 2015..2021` (shot model with goalies).

## Verdict by the pre-registered rule: NOT SUPPORTED. No live change.

| Criterion | Result | |
|---|---|---|
| 1. T1 leave-one-season-out: per-side bars beat a shared bar in total and in 3+/5 folds | +98.5u vs +66.2u, 4/5 folds | PASS |
| 2. T3 approximate openers 2015-2021: +1.5 at EV 6-9% positive, 4+/7 seasons, ROI above -1.5 at 6-9% | +21.2u on 884 bets (+2.4%), 5/7 seasons, but -1.5 at 6-9% did +4.1% (87 bets) | FAIL |
| 3. T2 SBR closing lines: +1.5 at 6-9% not worse than -1.5 at 6-9% | -0.7% vs -1.8% | PASS |

The failure is on the last clause of criterion 2 only, against a group of just 87 bets. That is what the rule says, so the verdict
stands; it is not re-argued here.

## What each test showed

**T1, DK openers 2021-26, leave-one-season-out.** Choosing each side's bar on the other four seasons picked a **4% bar for +1.5 in
all five folds** and 8-9% for -1.5. Graded on the held-out seasons that made +98.5u vs +66.2u for one shared bar. Same DK seasons
by band: -1.5 loses below 9% (4-6% -10.6%, 6-9% -6.8%), +1.5 is positive at every band (4-6% +5.4%, 6-9% +2.6%, 9%+ +12.2%).

**T2, SBR closing puck lines 2014-15..2020-21.** Everything loses at the close, both sides, every band (-0.0% to -9.0%), as every
closing-price rule has. No side difference worth reading.

**T3, approximate opening puck lines 2014-15..2020-21.** +1.5 at 6-9%: 884 bets +21.2u (+2.4%), 5/7 seasons positive. +1.5 at 9%+:
1,293 bets +71.0u (+5.5%), 6/7 positive. -1.5 bets are rare here (316 in all) and **-1.5 at 9%+ lost: 139 bets -16.9u (-12.2%)**,
the opposite of the DK seasons (+11.8%).

## How much to trust T3
- The opening puck line price is rebuilt from SBR's opening moneyline with a mapping fit on DK openers. Checked against SBR's real
  closing puck lines, the rebuilt price is off by about 3.2 implied-probability points per game (sd), with a home/away bias
  (home side rebuilt 1.5 pts too expensive, away side 1.0 pt too cheap). That noise is about the size of a whole EV band, so bets
  shift between bands, and the bias tilts which side looks best.
- SBR's opener is a consensus-style opener, not DraftKings'.
- So T3 is direction only. It shows the model's +1.5 bets held up on seven seasons it never saw; it cannot settle a 1-point bar.

## Leads this opens (not tested, not acted on)
- [LEAD] -1.5 at EV 9%+ lost on the older seasons (T3, -12.2%) but made money on DK 2021-26 (+11.8%). If real, the live 9%+ -1.5
  bets carry more risk than the DK record says. Before believing it, the T3 price mapping needs its home/away bias removed
  (fit the mapping per home/away side and check it on SBR closes), then re-run T3. Needs its own pre-registration.
- [CORRELATION] +1.5 bets were positive at every EV band from 6% up on the DK seasons and the older seasons; -1.5 bets were
  profitable only at 9%+ on DK and not at all on the older seasons. This is a correlation between side and profit, not a cause.
