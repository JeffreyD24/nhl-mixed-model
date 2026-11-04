import os, json, re
os.chdir(os.path.dirname(os.path.abspath(__file__)))
NBA = os.environ.get("NBA_CAT", ".")   # folder holding papers_A.md, papers_B.md and nba_make_catalog.py (copied from nba-mixed-model)
src = open(os.path.join(NBA, "nba_make_catalog.py")).read()
ns = {}; exec(src[src.index("FORM = {"):src.index("ST = {")], ns); FORM = ns["FORM"]
FORM["X01"] = "Overs-only totals rule: EV = P(over) x decimal odds + P(push) - 1 >= 6% at the opening total."
J = json.load(open("results_nhl.json")); R = J["results"]; PV = J["pvalues"]; O = json.load(open("oos_nhl.json"))
NT = len(PV); NR = sum(p < 0.05 for p in PV.values()); NB = sum(p < 0.05 / NT for p in PV.values())
P = {}
for f in ("papers_A.md", "papers_B.md"):
    for line in open(os.path.join(NBA, f)):
        if re.match(r"^\| [AB]\d\d ", line):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            P[c[0]] = dict(name=c[1], cite=c[2], url=c[3], how=c[4], ver=c[6])
P["X01"] = dict(name="Overs (the NHL totals rule)", cite="", url="", how="", ver="yes")
P["X02"] = dict(name="Rested team vs a back-to-back team (market-only rule)", cite="", url="", how="", ver="yes")
FORM["X02"] = "Bet the team NOT on a back-to-back when the other team is, at the opening moneyline. Uses no model, only the schedule."
ST = {k: "Tool" for k in R}
for k in "A07 A38 A47 B51 B53 B54 B69 B78".split(): ST[k] = "Confirmed (in-sample)"
for k in "A03 A04 A39 B73 B75 A02 A32 X01 X02 A27 B76 A33 A12".split(): ST[k] = "Confirmed out of sample"
for k in "B98 B95 B57 A08 B55 A31 A10 A14".split(): ST[k] = "Warning"
for k in "B59 B62 B66 B67 B68 A25 A17 B81 B86".split(): ST[k] = "Suggestive (does not replicate)" if k in ("B59", "B62", "B66", "B67", "B68", "A25") else "Suggestive"
for k in "A09 A11 A28 B56 B58 B60 B71 B72 B74 B90 B92 B93 B94 A34 A05 B87 B84 B61".split(): ST[k] = "No trend"
CARRY = {"A03": "A known, scheduled handicap (fatigue) that the opening price under-weights and the closing price fixes: same pattern as slow-to-price scheduled events in markets.",
         "A04": "Hot streaks regress (same as NBA, and fund-manager persistence).", "A07": "Permutation test of a signal vs random sides.",
         "B73": "Outcomes that bunch at a 'tie' point more than an independence model says (pinning near round numbers / option strikes is the market cousin).",
         "B75": "Price moving toward your position after entry marks skill, in both sports now.", "B76": "Regress outcome on your edge; slope = how much to trust it vs the market.",
         "B98": "The weight a forecast deserves against the market depends on what private information it has (goalies here): measure it, don't assume it.",
         "A36": "A skeptical prior pulls a short good record halfway back to zero.", "B52": "Small edges need thousands of trials, any market."}
def section(k):
    if k[0] == "X": return "NHL-specific rules (overs, rest)"
    i = int(k[1:])
    if k[0] == "A": return "Study design and data collection" if i <= 12 else ("Describing data" if i <= 28 else "Probability and sampling distributions")
    return ("Estimation and tests for one or two populations" if i <= 58 else "ANOVA and multiple comparisons" if i <= 68 else "Categorical data" if i <= 75 else "Regression, diagnostics and model choice")
L = [f"""# Statistics concept catalog: NHL shot model

*Nov 4, 2026. Same 98 concepts, same IDs and papers as the NBA catalog (`nba-mixed-model/research/stats_catalog/`), applied to the NHL
shot model. Living document: add new concepts here and in the NBA file with the same ID.*

**Model tested:** the live shot model (expected-goals mixed model + goalie effects, one-day lag), moneyline bets at EV 6%+ against
DraftKings opening prices, 2024-25 and 2025-26: **2,425 games, 693 bets, 372-321, +79.3u (+11.4%)**. Totals: the overs-only rule.
**Out of sample:** the pre-registered holdout (team-only shot model, no goalies) on 2016-17 to 2021-22 SBR openers, trusted rows:
6,994 games, 2,853 moneyline bets (+29.9u, +1.0%), 293 overs.

Why moneyline: it's the NHL market the model bets most, and the one with a real out-of-sample record. The 2024-26 seasons were used to
choose the 6% rule, so in-sample tests are descriptive; "Confirmed out of sample" means the 2016-22 holdout shows it too.

Status key: same as the NBA catalog (Confirmed out of sample / Confirmed in-sample / Suggestive / No trend / Warning / Tool; ⇄ = carries
over to other markets).

## What came out of it

**1. Regulation ties happen far more often than the model's Poisson math says (B73, A39). New, confirmed in both eras.** Goals per team
are almost exactly Poisson (variance/mean 1.01, and 1.02 in 2016-22). But the two teams' scores aren't independent near the end of games:
regulation ties are **22.8% (2024-26) and 22.5% (2016-22) vs 16.2% / 17.0% predicted by independent Poisson**. The score matrix in
`nhl_mixed_model.score_matrix` multiplies two independent Poissons, so it under-counts ties by about 6 points every season. The calibration
layer may absorb part of this for moneylines (not checked here), but it matters most for puck lines (every tie is a puck-line loss for the favorite at -1.5)
and totals (every tie adds a goal, which is why finals are odd 68% of the time). **Next test:** a tie-inflated score matrix (the Dixon-Coles
idea: inflate the diagonal), checked on 2016-22 puck lines and totals before anything changes live.

**2. The opener under-prices back-to-backs (A03). Confirmed out of sample.** Per back-to-back, the home team wins 6.4 pts less than the
opening price says in 2024-26 and 3.6 pts less in 2016-22 (p = 0.005). The model already has it (residual vs model n.s. in both eras).
A market-only check (X02): backing the rested team against a back-to-back team at the opener made +2.2% on 1,520 holdout bets in 2016-22
(positive in 4 of 6 seasons) and +7.8% on 538 in 2024-26, and **the price moved toward the rested team by the close in every season** (6 of 6 holdout, 2 of 2 recent). It's thin, but it's the cleanest
market-wide lead in either catalog. Worth a pre-registered test as a filter or a standalone rule.

**3. Line movement marks winners in hockey too (B75, A02, A32).** 2024-26: bets whose price moved our way won 55.4% vs a 47.0% market price
(+14.9% ROI); moved against, 43.8% vs 46.1% (-11.3%). 2016-22: the same split (+4.9% vs -8.8%), and the no-vig price moved toward the
team-only model's picks 55% of the time vs 29% against. **Correction to the Nov 3 read:** its negative CLV (-1.7%) measured value
including the vig; the price *did* move toward the picks more often than not, just not by enough to cover the vig.

**4. How much to trust the model depends on the goalie information (B76, B98, B95).** Fitting home win on the opener and the model:
2024-26 (live model, with goalies) gives the model **82%** of the weight; 2016-22 (team-only, no goalies) gives it **28%**. The live blend
uses 55%, in between. Two seasons are too few to raise it, but this is the measurement to repeat each season.

**5. The edge isn't luck (A07, A38) but it's not proven either (A36, B52).** Coin-flip sides at the same prices: -2.6% ROI; the model beat
all but 1 in 5,000. With a skeptical prior (most bettors have no edge), the two-season +11.4% shrinks to about +4% (P(ROI > 0) = 0.95).
80% power to detect a true +4% ROI takes ~4,600 bets (dog prices are noisy, SD 1.09u per bet).

**6. Overs: the totals lead holds (X01).** 2024-26: +3.1% on 198 bets, and the total rose after 36% of bets vs fell 8% (all games: 17% /
16%). 2016-22: +18.4% on 293, rose 33% vs fell 3%.

**7. What didn't hold up:**
- Underdogs made most of the 2024-26 profit (+16.8% vs +3.7% for favorites), but in 2016-22 dogs made +0.6% vs +2.5%. Don't tilt toward dogs.
- Bigger EV didn't win more in 2016-22 (12%+ EV: about -1%), same as the NBA. Bet flat.
- The month pattern in totals (p = 0.04 in-sample) is gone in 2016-22 (p = 0.29).
- The team-only model is *less* accurate than the opener in 2016-22 (log loss p = 0.015); the live model is roughly tied with the opener
  (p = 0.17) and worse than the close (p = 0.049). As in the NBA, the profit is in timing at the open, not a better number.

**8. NBA findings that do NOT carry over:** noise growing with the line (B84/B87): NHL totals sit at 5.5-6.5 and the spread of misses is
flat (2.30 / 2.36 / 2.32). Right-skew in the NBA came from overtime; in the NHL, OT shows up as the odd-total effect instead.

**9. Multiple testing (B64, B65):** {NT} tests, {NR} with p < 0.05, {NB} pass Bonferroni. Several test the same win rate (A38, B51, B54, B69).

### Out-of-sample checks (2016-17 to 2021-22 holdout)
| Concept | 2016-22 result |
|---|---|"""]
for k, v in O.items(): L.append(f"| {k} | {v} |")
L.append("\n## How to read each entry\n**Formula**, **Paper** (same as the NBA catalog; see its file for the NBA-specific lesson), **Applied to the NHL model**, and the 2016-22 check where one was run.\n"
         "Scripts: `research/stats_catalog/build_nhl.py` (per-game data), `run_nhl.py` (all tests), `make_catalog_nhl.py` (this file).\n")
cur = None
for k in R:
    if section(k) != cur: cur = section(k); L.append(f"\n## {cur}\n")
    p = P.get(k, {})
    L.append(f"### {k}. {p.get('name', k)}  ·  *{ST[k]}*{'  ⇄' if k in CARRY else ''}")
    L.append(f"- **Formula / idea:** {FORM.get(k, '')}")
    if p.get("cite"):
        L.append(f"- **Paper:** {p['cite']} {p['url']}{'' if p['ver'].lower().startswith('yes') else ' *(citation details partly unverified)*'}")
        L.append(f"  - *How they used it:* {p['how']}")
    L.append(f"- **Applied to the NHL model:** {R[k]}")
    if k in O: L.append(f"- **2016-22 check:** {O[k]}")
    if k in CARRY: L.append(f"- **Carries over:** {CARRY[k]}")
    L.append("")
L.append("""## Adding a new concept
Same procedure as the NBA catalog: give it the next ID in both files, add a block to `run_nhl.py` (and `run_all.py` for the NBA), rerun so
the multiple-testing bar updates, and check anything that passes on the 2016-22 holdout before calling it real.
""")
open("README.md", "w").write("\n".join(L).replace("{NT}", str(NT)).replace("{NR}", str(NR)).replace("{NB}", str(NB)))
print(NT, NR, NB)
