# Edge statistics (NHL), made 2026-11-03 10:03 ET

## ROI and closing line value with bootstrap ranges

ROI = units won per bet (each bet 1 unit; scorecard NBA/NFL bets at -110). 90% ranges from 10,000 resamples; `by_day` resamples whole days. CLV is in win-prob (fraction) against DraftKings' close (as logged); Pinnacle price CLV is below.

| source | rule | scope | n | W | L | P | units | roi | roi_lo90 | roi_hi90 | roi_lo90_by_day | roi_hi90_by_day | p_roi_above_0 | clv_n | clv_mean | clv_lo90 | clv_hi90 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scorecard | goals open moneyline EV>=6% | all | 103 | 37 | 66 | 0 | -15.8 | -0.153 | -0.334 | 0.030 | -0.259 | -0.032 | 0.084 | 103 | -0.038 | -0.049 | -0.027 |  |
| scorecard | goals open moneyline EV>=6% | live only | 10 | 5 | 5 | 0 | 1.230 | 0.123 | -0.510 | 0.718 | -0.271 | 0.461 | 0.622 | 10 | -0.035 | -0.056 | -0.010 | n<30: too few bets to read |
| scorecard | goals open puck line EV>=6% | all | 73 | 38 | 35 | 0 | -10.9 | -0.149 | -0.312 | 0.010 | -0.272 | -0.029 | 0.062 | 71 | -0.033 | -0.042 | -0.023 |  |
| scorecard | goals open puck line EV>=6% | live only | 4 | 2 | 2 | 0 | -0.950 | -0.239 | -1.000 | 0.483 | -0.600 | 0.122 | 0.315 | 4 | -0.044 | -0.076 | -0.017 | n<30: too few bets to read |
| scorecard | goals open total EV>=6% (not in rule) | all | 33 | 17 | 16 | 0 | 1.230 | 0.037 | -0.259 | 0.330 | -0.196 | 0.271 | 0.577 | 28 | 0.019 | 0.004 | 0.035 |  |
| scorecard | goals open total EV>=6% (not in rule) | live only | 5 | 4 | 1 | 0 | 2.870 | 0.575 | -0.152 | 1.044 | 0.460 | 0.842 | 0.944 | 4 | 0.036 | 0.016 | 0.057 | n<30: too few bets to read |
| scorecard | shot open moneyline EV>=6% | all | 81 | 36 | 45 | 0 | -5.610 | -0.069 | -0.265 | 0.126 | -0.256 | 0.121 | 0.280 | 81 | 0.011 | -0.001 | 0.024 |  |
| scorecard | shot open moneyline EV>=6% | live only | 6 | 4 | 2 | 0 | 2.040 | 0.340 | -0.340 | 1.000 | -0.174 | 1.090 | 0.811 | 6 | 0.026 | 0.007 | 0.046 | n<30: too few bets to read |
| scorecard | shot open puck line EV>=6% | all | 66 | 33 | 33 | 0 | -6.120 | -0.093 | -0.291 | 0.106 | -0.368 | 0.160 | 0.220 | 58 | 0.008 | -0.006 | 0.022 |  |
| scorecard | shot open puck line EV>=6% | live only | 3 | 2 | 1 | 0 | -0.090 | -0.031 | -0.527 | 0.465 | -0.527 | 0.465 | 0.300 | 2 | -0.049 | -0.103 | 0.004 | n<30: too few bets to read |
| scorecard | shot open total EV>=6% (not in rule) | all | 37 | 24 | 13 | 0 | 9.400 | 0.254 | -0.012 | 0.507 | 0.011 | 0.505 | 0.941 | 27 | 0.004 | -0.012 | 0.021 |  |
| scorecard | shot open total EV>=6% (not in rule) | live only | 3 | 2 | 1 | 0 | 0.880 | 0.294 | -0.420 | 1.007 | -0.420 | 1.007 | 0.734 | 2 | 0.026 | -0.018 | 0.070 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET | all | 11 | 5 | 6 | 0 | 0.200 | 0.018 | -0.571 | 0.604 | -0.511 | 0.641 | 0.542 | 11 | -0.035 | -0.055 | -0.013 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET | all | 10 | 5 | 5 | 0 | -2.570 | -0.257 | -0.684 | 0.165 | -0.645 | 0.134 | 0.170 | 9 | -0.026 | -0.040 | -0.012 | n<30: too few bets to read |
| alerts | goals alert moneyline BET | all | 6 | 3 | 3 | 0 | 0.880 | 0.146 | -0.592 | 0.963 | -0.583 | 0.875 | 0.644 | 6 | -0.052 | -0.063 | -0.042 | n<30: too few bets to read |
| alerts | goals alert puck line BET | all | 6 | 3 | 3 | 0 | -1.420 | -0.237 | -0.741 | 0.289 | -0.599 | 0.454 | 0.268 | 6 | -0.034 | -0.040 | -0.026 | n<30: too few bets to read |
| alerts | xg alert moneyline caution / DON'T BET | all | 7 | 3 | 4 | 0 | -0.830 | -0.119 | -0.725 | 0.492 | -0.694 | 0.661 | 0.346 | 7 | 0.006 | -0.019 | 0.035 | n<30: too few bets to read |
| alerts | xg alert puck line caution / DON'T BET | all | 4 | 3 | 1 | 0 | 0.340 | 0.085 | -0.628 | 0.466 | -0.141 | 0.461 | 0.736 | 3 | -0.012 | -0.027 | 0.003 | n<30: too few bets to read |
| alerts | xg alert puck line BET | all | 2 | 1 | 1 | 0 | -0.510 | -0.256 | -1.000 | 0.488 | -1.000 | 0.488 | 0.243 | 2 | -0.017 | -0.039 | 0.004 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | all | 2 | 1 | 1 | 0 | 0.140 | 0.070 | -1.000 | 1.140 | -1.000 | 1.140 | 0.742 | 2 | -0.014 | -0.029 | 0.001 | n<30: too few bets to read |
| alerts | goals alert moneyline BET (opening price only) | all | 2 | 0 | 2 | 0 | -2.000 | -1.000 | -1.000 | -1.000 | -1.000 | -1.000 | 0.000 | 2 | -0.035 | -0.041 | -0.029 | n<30: too few bets to read |
| my bets | NHL v1 (goals + shot models) | all | 16 | 7 | 9 | 0 | -2.310 | -0.144 | -0.542 | 0.270 | -0.454 | 0.165 | 0.276 | 14 | -0.030 | -0.044 | -0.015 | n<30: too few bets to read |
| my bets | ALL logged bets | all | 16 | 7 | 9 | 0 | -2.310 | -0.144 | -0.548 | 0.284 | -0.454 | 0.165 | 0.286 | 14 | -0.030 | -0.044 | -0.015 | n<30: too few bets to read |


## Calibration: predicted chance vs what happened

### games

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: home win chance, all games | (0.35, 0.45] | 24 | 0.416 | 0.417 | 0.001 | 0.009 |  |  |
| goals: home win chance, all games | (0.45, 0.5] | 52 | 0.476 | 0.442 | -0.034 | -0.485 |  |  |
| goals: home win chance, all games | (0.5, 0.55] | 82 | 0.525 | 0.598 | 0.072 | 1.315 |  |  |
| goals: home win chance, all games | (0.55, 0.65] | 75 | 0.582 | 0.653 | 0.071 | 1.245 |  |  |
| goals: home win chance, all games | (0.65, 1.0] | 2 | 0.661 | 1.000 | 0.339 | 1.012 |  |  |
| goals: home win chance, all games | ALL | 235 | 0.522 | 0.566 | 0.043 | 1.334 | 0.239 | 0.670 |
| shot: home win chance, all games | (-0.001, 0.35] | 10 | 0.317 | 0.300 | -0.017 | -0.113 |  |  |
| shot: home win chance, all games | (0.35, 0.45] | 46 | 0.410 | 0.435 | 0.025 | 0.347 |  |  |
| shot: home win chance, all games | (0.45, 0.5] | 41 | 0.475 | 0.610 | 0.134 | 1.722 |  |  |
| shot: home win chance, all games | (0.5, 0.55] | 47 | 0.520 | 0.447 | -0.073 | -1.007 |  |  |
| shot: home win chance, all games | (0.55, 0.65] | 74 | 0.598 | 0.676 | 0.078 | 1.371 |  |  |
| shot: home win chance, all games | (0.65, 1.0] | 17 | 0.685 | 0.824 | 0.138 | 1.227 |  |  |
| shot: home win chance, all games | ALL | 235 | 0.518 | 0.566 | 0.048 | 1.460 | 0.232 | 0.655 |


### bets

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 1 | 0.344 | 0.000 | -0.344 | -0.724 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 66 | 0.416 | 0.303 | -0.113 | -1.866 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 68 | 0.474 | 0.353 | -0.121 | -2.001 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 66 | 0.523 | 0.515 | -0.008 | -0.135 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 33 | 0.581 | 0.515 | -0.066 | -0.769 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 1 | 0.666 | 1.000 | 0.334 | 0.708 |  |  |
| goals: higher-EV side of every game (not only rule bets) | ALL | 235 | 0.487 | 0.409 | -0.079 | -2.408 | 0.239 | 0.670 |
| shot: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 10 | 0.318 | 0.000 | -0.318 | -2.157 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 47 | 0.404 | 0.340 | -0.063 | -0.884 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 44 | 0.479 | 0.477 | -0.002 | -0.023 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 44 | 0.523 | 0.318 | -0.205 | -2.726 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 73 | 0.594 | 0.616 | 0.023 | 0.394 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 17 | 0.686 | 0.647 | -0.039 | -0.345 |  |  |
| shot: higher-EV side of every game (not only rule bets) | ALL | 235 | 0.516 | 0.455 | -0.061 | -1.862 | 0.232 | 0.655 |


### price_bands

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | units |
|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game, by price band | -150 or shorter | 8 | 0.630 | 0.750 | 0.120 | 0.702 | 1.277 |
| goals: higher-EV side of every game, by price band | -149..+99 | 66 | 0.538 | 0.485 | -0.053 | -0.862 | -6.323 |
| goals: higher-EV side of every game, by price band | +100..+149 | 104 | 0.481 | 0.413 | -0.068 | -1.388 | -9.590 |
| goals: higher-EV side of every game, by price band | +150..+249 | 54 | 0.420 | 0.278 | -0.143 | -2.124 | -13.7 |
| goals: higher-EV side of every game, by price band | +250 or longer | 3 | 0.380 | 0.000 | -0.380 | -1.355 | -3.000 |
| shot: higher-EV side of every game, by price band | -150 or shorter | 34 | 0.648 | 0.706 | 0.058 | 0.706 | 3.418 |
| shot: higher-EV side of every game, by price band | -149..+99 | 80 | 0.563 | 0.450 | -0.113 | -2.034 | -14.7 |
| shot: higher-EV side of every game, by price band | +100..+149 | 76 | 0.488 | 0.487 | -0.001 | -0.015 | 4.160 |
| shot: higher-EV side of every game, by price band | +150..+249 | 42 | 0.387 | 0.238 | -0.149 | -1.982 | -14.8 |
| shot: higher-EV side of every game, by price band | +250 or longer | 3 | 0.294 | 0.000 | -0.294 | -1.116 | -3.000 |


## CLV against Pinnacle's closing price (games from Nov 2, 2026; live recorder only)

price_clv_pct = fair Pinnacle close x bet decimal odds - 1 (negative = paid the usual vig at the same line; zero or above = beat the close). winpct_pts = fair close chance - break-even chance. points_clv = points better than Pinnacle's closing line.

| source | rule | market | n | points_clv_n | points_clv_mean | points_clv_lo90 | points_clv_hi90 | price_clv_pct_n | price_clv_pct_mean | price_clv_pct_lo90 | price_clv_pct_hi90 | winpct_pts_n | winpct_pts_mean | winpct_pts_lo90 | winpct_pts_hi90 | share_points_positive | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scorecard | goals open moneyline EV>=6% | moneyline | 3 | 0 |  |  |  | 3 | -0.063 | -0.070 | -0.057 | 3 | -2.684 | -3.088 | -2.280 |  | n<30: too few bets to read |
| scorecard | goals open puck line EV>=6% | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | 0.015 | 0.015 | 0.015 | 1 | 1.068 | 1.068 | 1.068 | 0.000 | n<30: too few bets to read |
| scorecard | goals open total EV>=6% (not in rule) | total | 1 | 1 | 1.000 | 1.000 | 1.000 | 0 |  |  |  | 0 |  |  |  | 1.000 | n<30: too few bets to read |
| scorecard | shot open moneyline EV>=6% | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| scorecard | shot open puck line EV>=6% | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.592 | 0.592 | 0.592 | 0.000 | n<30: too few bets to read |
| scorecard | shot open total EV>=6% (not in rule) | total | 1 | 1 | 1.000 | 1.000 | 1.000 | 0 |  |  |  | 0 |  |  |  | 1.000 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET | moneyline | 2 | 0 |  |  |  | 2 | -0.067 | -0.077 | -0.057 | 2 | -3.057 | -3.151 | -2.962 |  | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.002 | -0.002 | -0.002 | 1 | -0.116 | -0.116 | -0.116 | 0.000 | n<30: too few bets to read |
| alerts | xg alert moneyline caution / DON'T BET | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| alerts | xg alert puck line caution / DON'T BET | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.592 | 0.592 | 0.592 | 0.000 | n<30: too few bets to read |
| alerts | xg alert puck line BET | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.592 | 0.592 | 0.592 | 0.000 | n<30: too few bets to read |
| alerts | goals alert moneyline BET | moneyline | 2 | 0 |  |  |  | 2 | -0.067 | -0.077 | -0.057 | 2 | -3.057 | -3.151 | -2.962 |  | n<30: too few bets to read |
| alerts | goals alert puck line BET | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.002 | -0.002 | -0.002 | 1 | -0.116 | -0.116 | -0.116 | 0.000 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| my bets | NHL v1 (goals + shot models) | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| my bets | ALL logged bets | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |


## By sportsbook (bets logged through `Log a bet`)

Book names are normalized (dk / DraftKings are one book). `(not recorded)` means the form's Sportsbook field was blank.

| book | bets | graded | stake_units | units | roi | roi_lo90 | roi_hi90 | clv_mean | clv_n | first_bet | last_bet | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DraftKings | 17 | 15 | 17.0 | -3.240 | -0.216 | -0.629 | 0.219 | -0.032 | 14 | 2026-10-30 | 2026-11-02 | n<30: too few bets to read |
| (not recorded) | 1 | 1 | 1.000 | 0.930 | 0.930 | 0.930 | 0.930 | 0.013 | 1 | 2026-10-31 | 2026-10-31 | n<30: too few bets to read |


### Limit events (`Log a limit` form, state/book_limits.csv)

`bets_logged_at_book_before` counts logged bets at that book up to the end of that day, so a cut can be read against how much was bet and won first.

_no rows yet_

