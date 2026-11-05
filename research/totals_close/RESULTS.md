# NHL shot model vs DraftKings' closing total price: results (Nov 5, 2026)

Pre-registration: `PREREG.md` (commit e5ced1f, pushed before any result). Code `close_weight.py`, output `output.txt`.

## Verdict: NO PASS. Bet NHL totals at the opener, as now; the close leaves too little of the model's edge.
Weight of the model's disagreement with DK's price (1 = trust the model fully, 0 = it adds nothing), over at DK's line,
decided games, walk-forward shot model with opener-time inputs only:

| | At DK's open | At DK's close |
|---|---|---|
| All five seasons (2021-26) | **+0.48** (se 0.13) | +0.15 (se 0.15) |
| Train 2021-22..2023-24 | +0.56 (se 0.19) | +0.23 (se 0.20) |
| **Test 2024-25 + 2025-26 (pre-registered)** | +0.43 (se 0.20) | **+0.10 (se 0.22), 90% [-0.26, +0.46]** |
| Seasons positive | 5 of 5 | 3 of 5 |

- The open weight reproduces yesterday's 0.48, so the setup matches the earlier study.
- DK's close keeps only about a third of the model's opener information (0.15 / 0.48 = 0.32); about two thirds is absorbed.
  The old SBR test (points only, no prices) said ~45% absorbed. With prices included, the close absorbs more.
- Only 2023-24 shows a clear weight at the close (+0.95); the other four seasons are within noise of zero.

## What it means
- **Matches yesterday's timing result**: the overs edge held about 3 h after the opener (+54u), then decayed to +5.3u at the
  close (3/5 seasons negative). Today's test explains why: by the close DK has priced in most of what the model knows.
- **Closes daily/2026-11-04.md explore #1.** No late or closing-line totals rule from the shot model. No rule changes.
- **Still open, and different:** the goalie-confirmed overs TEST (state/ovr_goalie_test.csv) re-runs the model with
  confirmed starters, i.e. new information, not the opener model at a later price. This test does not judge it.
