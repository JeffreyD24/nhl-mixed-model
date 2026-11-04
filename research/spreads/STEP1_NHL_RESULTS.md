# Spreads step 1 (NHL): moneyline and puck line re-graded with opener-time information — results (Nov 4, 2026)

Pre-registration: `research/spreads/STEP1_NHL_PREREG.md` (pushed first, commit 1ab00db). Data rebuilt in GitHub Actions
(`step1-nhl-build.yml`, run 41902732435: 8,510 games, 0 fetch errors, 990k shot attempts; gzipped `box_hist` / `shots_hist` now on the
`data-rebuild` branch so later audits don't need to refetch). Grading `research/spreads/step1_nhl.py`, output
`research/spreads/step1_nhl_output.txt`, per-bet rows `research/spreads/step1_nhl_bets.csv`. DK openers 2021-22..2025-26, units at the
actual DK opener price. **CLV = expected return at DK's no-vig close; break-even is 0.**

## Is the live timing honest?
Yes. DK's opener posted the day before, before 7 PM ET, for 91.7% of games (8.0% two or more days before, 0.3% on game day); median 31 h
before puck drop. The model's one-day lag (results through two days before) matches. **One more night of results (lag 0) is worth nothing**
(v4 combined CLV +0.31% at both lags; lag-0 units lower), so unlike the NBA and NFL, the NHL record had no timing leak.

## Main table (lag 1 = opener-time information)
| Row | Bets | Win % | Units | Per 100 [90%] | CLV [90%] | Units by season 22 / 23 / 24 / 25 / 26 | CLV by season |
|---|---|---|---|---|---|---|---|
| **v4 moneyline (PRIMARY)** | 1,267 | 56.0% | **+147.1** | +11.6 [+7.0, +16.7] | **+0.23%** [-0.07, +0.52] | +22 / +52 / +22 / +25 / +26 | +1.3 / -0.1 / -0.5 / +0.7 / -0.8 |
| **v4 puck line (PRIMARY)** | 321 | 43.9% | **+35.6** | +11.1 [-1.2, +23.1] | **+0.65%** [+0.11, +1.19] | +8 / +12 / -10 / +17 / +7 | +2.1 / +0.9 / -0.6 / +1.3 / +0.2 |
| v4 combined | 1,588 | 53.5% | +182.7 | +11.5 [+6.9, +16.3] | +0.31% [+0.05, +0.57] | 0 of 5 negative | |
| v3.1 moneyline | 722 | 54.2% | +90.1 | +12.5 | +0.22% | | |
| v3.1 puck line | 1,123 | 47.7% | +69.6 | +6.2 | +0.17% | | |
| v3.1 combined | 1,845 | 50.2% | +159.7 | +8.7 | +0.19% | | |

Accuracy (6,560 games, home-win log loss): raw shot model 0.6612, + travel 0.6605, **live blend 0.6586**, DK no-vig opener 0.6610,
DK no-vig close 0.6579. The blend beats the opener and gets most of the way to the close.

## Verdict (pre-registered rule)
- **v4 moneyline: CLV > 0 and units > 0 → keep live** (not disproved). But the evidence is weak: the CLV interval includes 0, CLV is
  negative in 3 of 5 seasons, and +11.6 units per 100 is far more than +0.23% CLV can explain. Most of the units are not backed by the
  close; on these seasons (where ML_BLEND and the 4% bar were chosen), plan on roughly break-even to a few % per bet, not +11.6.
- **v4 puck line: keep live; the strongest result in this test.** CLV +0.65% with the whole 90% interval above 0, units positive in 4/5.
  The 9% bar was chosen on units; CLV independently backs it: the 6-9% band (now TEST rows) had **CLV -1.26% [-1.65, -0.85]**, -10.6u.
- v4 beats v3.1 on units and CLV. No timing leak to flag.

## Breakdowns (v4, lag 1; exploratory — chosen after looking)
| Group | Bets | Units | CLV [90%] |
|---|---|---|---|
| ML EV 4-6% | 539 | +44.4 | **-0.58%** [-1.00, -0.16] |
| ML EV 6-9% | 416 | +37.3 | -0.23% [-0.68, +0.24] |
| ML EV 9-15% | 255 | +41.5 | **+1.54%** [+0.81, +2.26] |
| ML EV 15%+ | 57 | +23.9 | **+5.28%** [+3.36, +7.24] |
| ML EV 4-9% (combined) | 955 | +81.7 | -0.42%, negative or zero in **5 of 5** seasons |
| ML EV 9%+ (combined) | 312 | +65.4 | +2.22%, positive in 3 of 5 |
| ML away / home | 793 / 474 | +118.0 / +29.1 | +0.42% [+0.03, +0.79] / -0.09% |
| ML favorites / +100..+149 / +150+ | 614 / 395 / 258 | +53.0 / +33.6 / +60.6 | +0.06% / +0.24% / +0.61% |
| ML on a b2b team (allowed since v4) | 77 | +0.9 | +0.11% |
| PL favorite -1.5 / underdog +1.5 | 284 / 37 | +37.7 / -2.2 | +0.85% [+0.25, +1.45] / -0.92% |

Live 2026-27 so far: moneyline 10 graded bets -1.0u, puck line 11 bets -2.3u (too few to read).

## Takeaways
1. **The NHL models are the only spread-type market that beats the close at honest timing**, and the timing was already honest (unlike
   the NBA's 8 PM report and the NFL's previous-week results). Keep v4 as is.
2. **The moneyline's CLV lives entirely in the bigger edges.** EV 4-9% bets lose to the close every season (-0.42%) even though they made
   +81.7u; EV 9%+ bets beat it by +2.2%. That pattern matches the puck line (6-9% negative CLV, 9%+ positive) and the rule audit's
   "moved moneylines at 9%+". **Proposal (not applied; needs your OK and a Fable check, and it was found after looking):** raise the
   moneyline bar to 9% at the opener and log 4-9% as TEST rows, exactly like the puck line. Cost on these seasons: -81.7u of units that the
   close doesn't back. Caution: the SBR 2016-22 holdout (team-only model, no goalies) did not show bigger edges doing better, so this needs
   the 2026-27 TEST rows to confirm before it's treated as proven. A middle option is PROVISIONAL: keep 4-9% as bets for now and review
   their CLV monthly under the Nov 4 standing rule.
3. **Expect much less than the backtest units.** v4 combined CLV +0.31% means the close only backs a small edge; +186u on these seasons is
   mostly the seasons the rules were chosen on. Size bets on CLV, not units.
4. **Long shots are not the weak spot at honest timing** (+150 and longer: CLV +0.61%, +60.6u, 0/5 negative seasons); away moneylines carry
   the CLV, home moneylines don't (-0.09%).
5. Puck line: the edge is the favorite -1.5 (CLV +0.85%, interval above 0). Underdog +1.5 picks are rare (37) and negative on CLV.

## Independent review (Fable, Nov 4) and fixes
- Timing, rule replication (matches `alert.py` and the rule audit: ML EV 4%+ = 1,267 bets +147.1u vs the audit's 1,269 / +147.0u; PL 9%+
  no-b2b 754 / +90.2u identical), CLV side mapping and the write-up were checked. A shuffled-model test (same 0.45 market weight, no skill)
  gives flat CLV of about -4.4% to -5.1% in every EV band, so **CLV rising with EV is not an artifact of the blend**; it is post hoc and the
  9%+ bands are longer-priced and smaller, so it still needs confirming.
- **Bug found and fixed:** DK opened 22 games at home **-2.5**; the code priced and graded them as -1.5 (model "win by 2+" chance, cover =
  margin >= 2), giving fake EVs of 15-47%. The tables above are re-run with only +/-1.5 puck lines (v4 PL +38.9u -> +35.6u; verdict unchanged).
  **The same bug was in live `alert.py`** (could push a -2.5 puck line as a big-EV bet). Fixed Nov 4: puck lines other than +/-1.5 are no
  longer priced; new version row NHL v4.1 (puck line). Same bug remains in `analysis/rule_audit_nhl.py` (analysis only; ~4u).
- Footnote: 8% of openers posted two or more days early (522 games, mostly Oct-Dec; 114 v4 ML bets, +4.6u); for those lag 1 still has one
  night of look-ahead. Immaterial (lag 0 vs lag 1 shows a night of results is worth nothing).
