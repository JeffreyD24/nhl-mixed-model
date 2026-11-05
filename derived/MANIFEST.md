# Saved build products (check here BEFORE building anything)

Started Nov 5, 2026, after the 2021-26 DK predictions and the 2015-2021 goalie-model predictions were rebuilt from scratch because
they had only ever lived in the gitignored `_tmp/` folder. Rule (CLAUDE.md RULE 4): anything that takes more than a minute to
build is saved here, gzipped, with a row in this table, in the same session it is built.

Restore everything into `_tmp/` (where the scripts read from): `python derived.py .`
Save new build products from `_tmp/`: `python derived.py . --save`, then add rows below.

| File(s) | What it is | Built by | Inputs | Built (commit) | Used by |
|---|---|---|---|---|---|
| `dk_holdout_{2022..2026}.csv.gz` | Shot model walk-forward predictions at DK's opener, one-day info lag, joined to DK opening/closing prices (`data/nhl_prices.csv.gz`). One row per game, 2021-22..2025-26. Training (END-year labels): 2022 uses [2020, 2021] ... 2026 uses [2022-2025]. | `analysis/rule_audit_nhl.py --build` (same function in `analysis/pl_ev_bands.py --build`) | `data/training_games.csv`, `data/games_hist.csv`, `data/box_hist.csv.gz`, `data/shots_hist.csv.gz`, `data/nhl_prices.csv.gz` | Nov 5, 2026 (fd394cd) | rule_audit_nhl.py, pl_ev_bands.py, pl_side_bars.py |
| `oos_games.csv.gz` | 2011-2023 game table: hockeyR team-game xG joined with SportsbookReview opening/closing lines (moneyline, total, closing puck line), regulation scores, trusted-row flags | `dev/oos_sbr_build.py` | `data/external/hockeyr/team_game_xg_2010_2023.csv.gz`, `data/external/sbr/sbr_nhl_2011_2021_clean.csv.gz` | Nov 5, 2026 (fd394cd) | oos_sbr_backtest.py, goalie_recal_test.py |
| `oos_games_g.csv.gz` | `oos_games` + actual starting goalie and expected-starter mix at the open (one-day lag) | `dev/goalie_recal_test.py build` | `oos_games.csv`, `data/external/nhl_box/goalies_hockeyr_2010_2023.csv.gz` | Nov 5, 2026 (fd394cd) | goalie_recal_test.py, pl_side_bars.py |
| `gr_G1_pred_{2015..2021}.csv.gz`, `gr_G1_meta_*.json` | Goalie-aware shot model (variant G1) walk-forward predictions for 2014-15..2020-21 (END-year labels), with win / by-2 probabilities and SBR lines; meta = calibration and OT share per season | `dev/goalie_recal_test.py predict G1 2015 ... 2021` | `oos_games_g.csv` | Nov 5, 2026 (fd394cd) | goalie_recal_test.py score, pl_side_bars.py |

Not saved yet (rebuild needed if used; save them the next time they are built):
- `_tmp/oos_pred_<season>.csv` (team-only shot model, no goalies, `dev/oos_sbr_backtest.py predict`), G0 and GM variants of
  `gr_*_pred_*`, `_tmp/autopsy_*`, and `_tmp/rule_audit_snaps.pkl` (hourly DK/Pinnacle snapshots; needs the NBA repo's odds history).
