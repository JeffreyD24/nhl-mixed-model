# Ideas from the Nov 3, 2026 web sweep, and the implementation checklist

Why this file exists: we searched GitHub, Reddit summaries, forums, pick-seller sites and papers for how other people beat (or fail to beat)
sports betting markets. This is the keeper: what we learned, what we already had, what we added, and what is left. Update the checkboxes
as work lands. Raw sources are listed at the bottom.

## What the evidence says (short version)
1. Settled lines are almost impossible to beat. The pro VSiN/Circa contest composite went 50.3% in 2024 (break-even is 52.4%).
   Edges live at openers and in soft markets (props, early lines), not late-week numbers.
2. The scoreboard is closing line value (CLV), not wins. Winning too early is luck; beating the close over 1,000+ bets is skill.
3. Winning gets you limited (about 10% of a fresh account's limit once flagged). Connecticut has only three books (DraftKings, FanDuel, Fanatics).
   The ceiling on profit is account limits, not model quality.
4. Every "verified" pick seller and Discord found was marketed through affiliate review sites; none had an independently checkable record. Do not pay for picks.
5. Claims that look too good (e.g. an NFL repo showing 91.9% spread wins) are leakage or bugs.

## Checklist (status as of Nov 3, 2026)
Legend: [x] already in place  [~] partly  [ ] open  (O) = good job for Opus

### A. Measure edge the right way
- [x] CLV in points on every logged bet, summarized in the NBA, NHL and NFL workbooks (average CLV, share of bets that beat the close)
- [x] Pinnacle and 9 other books recorded live (pinnacle_watch.py) and used as a sharp-book check in alerts
- [ ] CLV in PRICE terms against Pinnacle's de-vigged close (points hide price moves, e.g. -110 to -125 with no point change)
- [ ] Bootstrap (resample bets within each walk-forward season, ~1,000 draws) to put a confidence interval on ROI and CLV for every rule, and the share of draws that lose (idea from r/algobetting, see community_notes)
- [ ] Calibration table: group our predicted edges/probabilities into buckets and compare with realized results (the Reddit props author claimed 70%+ confidence and got 60%); choose any cutoff on one season and test it on the next
- [ ] Report CLV per model version and per bet rule next to the win/loss record, and set a decision rule up front
      (suggestion: judge a rule only after 300+ bets with average CLV; do not drop or promote one on win/loss alone)

### B. Shrink toward the market
- [x] NFL: late-season shrink toward the line already tested (analysis/nfl_fixes.py)
- [x] NBA: tested Nov 3, 2026 (analysis/market_shrink_test.py, results in analysis/FINDINGS.md). Against OPENING lines the model deserves about
      0.25 weight on its disagreement for spreads (+/-0.09) and 0.39 for totals (+/-0.10); against CLOSING lines about 0 (-0.06 and -0.13).
- [x] (Nov 3, 2026: shrunk_record.py, w = 0.147 / 0.318 with the one-day lag; research/SHRINK_WEIGHTS_2026-11-03.md) Add "Model 1 shrunk" as a side-by-side record (do NOT change Model 1; new version = new record, per your rule): shrunk number =
      line + w x (model - line) with w = 0.25 spreads / 0.39 totals, thresholds re-derived by backtest
- [ ] Same test as a regularized logistic/linear stack that takes model number AND market number as inputs, fitted on earlier seasons and scored on a later one (idea from the r/algobetting LLM thread; see community_notes)
- [x] (Nov 3, 2026: NHL 0.29 ML / 0.40 overs; NFL totals 0.55, spreads 0.06) Repeat the weight test for NHL and NFL (needs their walk-forward prediction files lined up with openers) (O: choosing thresholds without overfitting)

### C. Keep models simple
- [x] Three NBA models run side by side; none beat closing lines (research/model_comparison)
- [ ] Rule for adding factors: a new factor must improve out-of-sample CLV, not just in-sample fit. Log each test in analysis/FINDINGS.md

### D. Price vs consensus (Kaunitz et al.: bet prices that beat the de-vigged consensus)
- [~] Multi-book prices are already recorded (research/books, data/odds_history)
- [ ] Test whether best available price vs consensus at the opener predicts CLV in NBA/NHL/NFL. Needs a few months of snapshots; limits will cap it. (O)

### E. Free data
- [x] SportsbookReview 2011-2021 openers and closers, all four sports, cleaned and flagged (data/external/sbr, see its README)
- [ ] Out-of-sample test of the "bet at the opener" rules on 2011-2021 using the SBR openers (old_seasons.py currently grades closes only) (O)
- [ ] MLB: the SBR MLB file is stored for when the MLB model starts
- [x] hockeyR xG: code, fitted objects and a 2010-23 team-game xG table stored (data/external/hockeyr). Next: test it against SBR NHL openers (O)
- [x] NHL out-of-sample test vs SBR openers, 2016-17..2021-22 (Nov 3, 2026, nhl-mixed-model backtests/OOS_SBR_RESULTS.md): moneylines +1%/bet with
      negative CLV (not confirmed); overs at the opener +16.5%/bet and the total rose on 33.5% of picks vs 10.9% of all games (real signal)
- [~] BeatTheBookie: code stored; odds data is on Dropbox/Google Drive and needs your browser (data/external/beatthebookie/DOWNLOAD_LINKS.md)

### F. Audit for the classic failure modes
- [x] (Nov 3, 2026: research/LEAKAGE_AUDIT_2026-11-03.md) Independent leakage audit: timestamps of injury reports vs when openers were seen, any feature using information from after the bet time,
      training on closing lines, tuning thresholds on the test season (O: best done by Opus or a fresh pair of eyes)
- [x] (Nov 3, 2026: config/thresholds.csv + tools/check_thresholds.py) Place every threshold in one config file with the date and the data it was chosen on, so changes are visible

### G. Execution and limits
- [ ] Track which book each bet is placed at and the limit you were offered; log limit cuts the day they happen
- [ ] Plan for limits: decide what you do when DraftKings/FanDuel/Fanatics cap you (prediction markets once outside Connecticut)

### H. Communities (needs your browser)
- [x] Four r/algobetting threads read from your pastes ("Has anyone done it", NBA props season review, LLM bots, comments from a deleted post); notes in research/community_notes. Only new ideas: bootstrap intervals, calibration table, stack with the market; live-line overreaction parked
- [~] X public search done (research/community_notes). Reddit/4chan still open: re-do the sweep with the Claude desktop app browser or the Chrome extension (my shell cannot reach those sites)

## From the statistics catalog (Nov 4, 2026; research/stats_catalog/README.md)
- [x] Tie-inflated score matrix (Nov 4): fixes the tie rate but no market improves after the existing recalibration; without it, puck lines
      get worse (real games also have extra empty-net 2-goal wins). Not adopted. backtests/TIE_INFLATION_RESULTS.md
- [x] Rested team vs a back-to-back team (Nov 5): PASSED the pre-registered 2011-16 test (+2.7 pts vs the no-vig close, p = 0.017, 4 of 5 seasons).
      backtests/REST_B2B_PREREG.md, REST_B2B_RESULTS.md
- [x] Follow-up 1 (Nov 5): backup-goalie split. NOT SHOWN without backups: starter games +1.75 pts (p = 0.10), backup games +2.95 (p = 0.006), difference
      not distinguishable. Inconclusive, power about 57%. backtests/REST_B2B_FOLLOWUPS_PREREG.md, REST_B2B_FOLLOWUPS_RESULTS.md
- [x] Follow-up 2 (Nov 5): does the shot model already price it? Prices about 70% of it (model leans +2.1 pts toward the rested team); rest still adds
      beyond opener + model (p = 0.025), but not vs the close + model (p = 0.087) and the leftover win - model is only +0.9 pts (SE 1.1)
- [ ] [IDEA, untested] Split the rest effect by rest days (b2b vs 1 day vs 2+ days) and by whether the b2b team is on the road the second night; same
      data (derived/oos_games_g.csv.gz), pre-register first
- [ ] [IDEA, untested] Add rest as an explicit term in the model and test leave-one-season-out on 2012-22 whether the leftover ~1 pt is real (RULE 2: past seasons)
- [ ] (Original idea, now partly answered) as a standalone rule or a filter for model bets: the model already captures most of it, so only the filter version is open
- [ ] Re-measure the model's logistic weight vs the opener each season (82% with goalies 2024-26, 28% team-only 2016-22; live blend 55%)

## Leads and ideas from Nov 5, 2026 (details in nba-mixed-model analysis/FINDINGS.md)
- [x] [LEAD, TESTED Nov 5] Separate puck line EV bars for -1.5 and +1.5: NOT SUPPORTED by the pre-registered rule
      (research/spreads/PL_SIDE_BARS_RESULTS.md). Leave-one-season-out favored a 4% +1.5 bar (+98.5u vs +66.2u, 4/5 folds), but the
      approximate older-season openers failed one clause. Do not re-suggest without a new reason.
- [x] [LEAD, TESTED Nov 5] -1.5 at EV 9%+ on 2014-21 with the price rebuild fixed (research/spreads/PL_FAV_9PLUS_RESULTS.md):
      CONFIRMED by the written rule, 654 bets -1.0% (interval -9.8% to +7.9%) vs DK +11.8%. Pooled 12 seasons +5.0%.
- [ ] [LEAD] Does puck line EV predict profit at all? EV bands don't repeat their order across 2014-21 and 2021-26. Pre-register a
      pooled 12-season test (profit vs EV slope, leave-one-season-out) before touching the puck line bar again.
- [ ] [IDEA] Goalie-fragile bets: split backtest opener bets by whether the bet still clears the bar under every likely starter;
      if fragile bets do worse, wait for confirmation on those or grade them as their own group.

## When to switch to Opus
Switch for: (1) the independent leakage audit, (2) choosing shrink thresholds and bet rules without overfitting, (3) any redesign of how
the three models are combined. Stay on Sonnet for: data downloads, cleaning, running backtests, logging, wiring alerts, reports.

## Sources
- VSiN/Circa contest write-up: figureitoutsportsbetting.substack.com/p/vsincirca-contest-showed-toughness
- r/algobetting summary: sportbotai.com/blog/sports-betting-model-reddit
- Simple-model backtest on SBR data: samesolutions-equipment-service.pages.dev/bets/learn/backtest-results.html
- Limits: howgamblingworks.substack.com/p/sportsbook-limits-get-a-closer-look; vixio.com (Connecticut operators)
- Consensus-price strategy: Kaunitz, Zhong, Kreiner, arXiv 1710.02824; github.com/Lisandro79/BeatTheBookie
- nfelo market regression: nfeloapp.com
- Data: github.com/FinnedAI/sportsbookreview-scraper

## NHL player props (Nov 7, 2026)
- [x] BettingPros prop history Apr 2022 on (props_bettingpros_nhl.py) - backfill running
- [x] ESPN BET own opener + close Feb 2024-Nov 2025 (props_espn_nhl.py) - backfill running
- [ ] Wayback snapshot counts of NHL prop pages (tools/probe_props_wayback.py on a runner) - read the output
- [ ] Kalshi NHL player markets history (runner -> JeffreyD24/private)
- [ ] The Odds API historical NHL props May 2023 on (paid credits: ask Jeffrey)
- [ ] Snapshot PrizePicks/Underdog NHL boards going forward
- [ ] Projection models (shots first) + pre-registration, walk-forward at the opener
