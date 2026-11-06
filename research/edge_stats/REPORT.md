# Edge statistics (NHL), made 2026-11-06 10:00 ET

## ROI and closing line value with bootstrap ranges

ROI = units won per bet (each bet 1 unit; scorecard NBA/NFL bets at -110). 90% ranges from 10,000 resamples; `by_day` resamples whole days. CLV is in win-prob (fraction) against DraftKings' close (as logged); Pinnacle price CLV is below.

| source | rule | scope | n | W | L | P | units | roi | roi_lo90 | roi_hi90 | roi_lo90_by_day | roi_hi90_by_day | p_roi_above_0 | clv_n | clv_mean | clv_lo90 | clv_hi90 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scorecard | goals open moneyline EV>=6% | all | 118 | 40 | 78 | 0 | -22.9 | -0.194 | -0.366 | -0.020 | -0.302 | -0.075 | 0.033 | 118 | -0.039 | -0.049 | -0.029 |  |
| scorecard | goals open moneyline EV>=6% | live only | 25 | 8 | 17 | 0 | -5.940 | -0.238 | -0.610 | 0.138 | -0.576 | 0.084 | 0.146 | 25 | -0.042 | -0.063 | -0.023 | n<30: too few bets to read |
| scorecard | goals open puck line EV>=6% | all | 83 | 43 | 40 | 0 | -13.0 | -0.157 | -0.310 | -0.007 | -0.274 | -0.045 | 0.042 | 81 | -0.035 | -0.044 | -0.027 |  |
| scorecard | goals open puck line EV>=6% | live only | 14 | 7 | 7 | 0 | -3.080 | -0.220 | -0.565 | 0.121 | -0.584 | -0.013 | 0.154 | 14 | -0.052 | -0.072 | -0.032 | n<30: too few bets to read |
| scorecard | goals open total EV>=6% (not in rule) | all | 41 | 21 | 20 | 0 | 1.100 | 0.027 | -0.233 | 0.283 | -0.168 | 0.215 | 0.568 | 36 | 0.021 | 0.008 | 0.034 |  |
| scorecard | goals open total EV>=6% (not in rule) | live only | 13 | 8 | 5 | 0 | 2.740 | 0.211 | -0.247 | 0.653 | 0.037 | 0.539 | 0.797 | 12 | 0.029 | 0.012 | 0.045 | n<30: too few bets to read |
| scorecard | shot open moneyline EV>=6% | all | 92 | 41 | 51 | 0 | -6.430 | -0.070 | -0.254 | 0.114 | -0.236 | 0.101 | 0.266 | 92 | 0.009 | -0.002 | 0.020 |  |
| scorecard | shot open moneyline EV>=6% | live only | 17 | 9 | 8 | 0 | 1.220 | 0.072 | -0.351 | 0.496 | -0.188 | 0.487 | 0.612 | 17 | 0.003 | -0.020 | 0.024 | n<30: too few bets to read |
| scorecard | shot open puck line EV>=6% | all | 74 | 37 | 37 | 0 | -4.650 | -0.063 | -0.254 | 0.130 | -0.306 | 0.172 | 0.299 | 66 | 0.006 | -0.007 | 0.019 |  |
| scorecard | shot open puck line EV>=6% | live only | 11 | 6 | 5 | 0 | 1.380 | 0.126 | -0.407 | 0.676 | -0.256 | 0.665 | 0.640 | 10 | -0.015 | -0.052 | 0.019 | n<30: too few bets to read |
| scorecard | shot open total EV>=6% (not in rule) | all | 38 | 25 | 13 | 0 | 10.2 | 0.269 | 0.019 | 0.514 | 0.030 | 0.519 | 0.962 | 27 | 0.004 | -0.012 | 0.021 |  |
| scorecard | shot open total EV>=6% (not in rule) | live only | 4 | 3 | 1 | 0 | 1.700 | 0.425 | -0.130 | 0.980 | -0.465 | 0.980 | 0.757 | 2 | 0.026 | -0.018 | 0.070 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET | all | 12 | 5 | 7 | 0 | -0.800 | -0.067 | -0.607 | 0.473 | -0.600 | 0.465 | 0.384 | 12 | -0.032 | -0.050 | -0.010 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET | all | 13 | 6 | 7 | 0 | -3.730 | -0.287 | -0.648 | 0.070 | -0.620 | -0.002 | 0.087 | 12 | -0.028 | -0.040 | -0.015 | n<30: too few bets to read |
| alerts | goals alert moneyline BET | all | 7 | 4 | 3 | 0 | 2.120 | 0.302 | -0.375 | 1.009 | -0.453 | 1.195 | 0.726 | 7 | -0.041 | -0.059 | -0.022 | n<30: too few bets to read |
| alerts | goals alert puck line BET | all | 6 | 3 | 3 | 0 | -1.420 | -0.237 | -0.741 | 0.282 | -0.611 | 0.454 | 0.266 | 6 | -0.034 | -0.040 | -0.026 | n<30: too few bets to read |
| alerts | xg alert moneyline caution / DON'T BET | all | 12 | 5 | 7 | 0 | -2.420 | -0.201 | -0.665 | 0.274 | -0.636 | 0.492 | 0.215 | 12 | 0.004 | -0.016 | 0.025 | n<30: too few bets to read |
| alerts | xg alert puck line caution / DON'T BET | all | 10 | 5 | 5 | 0 | -1.430 | -0.143 | -0.577 | 0.330 | -0.523 | 0.206 | 0.310 | 9 | -0.022 | -0.037 | -0.007 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | all | 4 | 3 | 1 | 0 | 3.330 | 0.833 | -0.262 | 1.595 | -0.262 | 1.595 | 0.949 | 4 | 0.002 | -0.016 | 0.017 | n<30: too few bets to read |
| alerts | goals alert moneyline BET (opening price only) | all | 3 | 1 | 2 | 0 | -0.050 | -0.017 | -1.000 | 0.967 | -1.000 | 0.967 | 0.257 | 3 | -0.020 | -0.037 | -0.003 | n<30: too few bets to read |
| alerts | xg alert puck line BET | all | 8 | 4 | 4 | 0 | 1.130 | 0.141 | -0.502 | 0.893 | -0.257 | 0.673 | 0.620 | 8 | 0.016 | -0.006 | 0.037 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET (opening price only) | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.058 | -0.058 | -0.058 | n<30: too few bets to read |
| alerts | goals alert total BET | all | 3 | 1 | 2 | 0 | -1.050 | -0.349 | -1.000 | 0.302 | -1.000 | 0.952 | 0.264 | 3 | 0.015 | -0.030 | 0.060 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET (opening price only) | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.069 | -0.069 | -0.069 | n<30: too few bets to read |
| alerts | xg alert total BET | all | 5 | 3 | 2 | 0 | 0.540 | 0.108 | -0.636 | 0.826 | -0.410 | 0.886 | 0.686 | 4 | 0.005 | -0.037 | 0.051 | n<30: too few bets to read |
| alerts | xg alert total caution / DON'T BET | all | 1 | 1 | 0 | 0 | 0.770 | 0.769 | 0.769 | 0.769 |  |  | 1.000 | 0 |  |  |  | n<30: too few bets to read |
| my bets | NHL v1 (goals + shot models) | all | 16 | 7 | 9 | 0 | -2.310 | -0.144 | -0.544 | 0.273 | -0.454 | 0.165 | 0.281 | 14 | -0.030 | -0.044 | -0.016 | n<30: too few bets to read |
| my bets | NHL v3 | all | 2 | 1 | 1 | 0 | 0.600 | 0.300 | -1.000 | 1.600 |  |  | 0.754 | 2 | 0.034 | 0.027 | 0.041 | n<30: too few bets to read |
| my bets | NHL overs v1.1 | all | 2 | 1 | 1 | 0 | -0.180 | -0.090 | -1.000 | 0.820 | -1.000 | 0.820 | 0.249 | 1 | -0.058 | -0.058 | -0.058 | n<30: too few bets to read |
| my bets | NHL v3.1 | all | 3 | 3 | 0 | 0 | 4.280 | 1.427 | 1.327 | 1.527 | 1.390 | 1.500 | 1.000 | 3 | 0.009 | -0.019 | 0.036 | n<30: too few bets to read |
| my bets | NHL v4 [ML EV 9%+] | all | 1 | 1 | 0 | 0 | 1.950 | 1.950 | 1.950 | 1.950 |  |  | 1.000 | 1 | 0.010 | 0.010 | 0.010 | n<30: too few bets to read |
| my bets | NHL v4.1 | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | 0.009 | 0.009 | 0.009 | n<30: too few bets to read |
| my bets | ALL logged bets | all | 25 | 13 | 12 | 0 | 3.340 | 0.134 | -0.236 | 0.503 | -0.180 | 0.591 | 0.717 | 22 | -0.017 | -0.029 | -0.003 | n<30: too few bets to read |


## Calibration: predicted chance vs what happened

### games

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: home win chance, all games | (0.35, 0.45] | 29 | 0.416 | 0.414 | -0.002 | -0.020 |  |  |
| goals: home win chance, all games | (0.45, 0.5] | 58 | 0.475 | 0.448 | -0.027 | -0.412 |  |  |
| goals: home win chance, all games | (0.5, 0.55] | 90 | 0.525 | 0.600 | 0.075 | 1.419 |  |  |
| goals: home win chance, all games | (0.55, 0.65] | 82 | 0.584 | 0.646 | 0.063 | 1.152 |  |  |
| goals: home win chance, all games | (0.65, 1.0] | 2 | 0.661 | 1.000 | 0.339 | 1.012 |  |  |
| goals: home win chance, all games | ALL | 261 | 0.521 | 0.563 | 0.042 | 1.353 | 0.239 | 0.671 |
| shot: home win chance, all games | (-0.001, 0.35] | 13 | 0.318 | 0.308 | -0.010 | -0.077 |  |  |
| shot: home win chance, all games | (0.35, 0.45] | 51 | 0.410 | 0.451 | 0.041 | 0.590 |  |  |
| shot: home win chance, all games | (0.45, 0.5] | 44 | 0.476 | 0.591 | 0.115 | 1.532 |  |  |
| shot: home win chance, all games | (0.5, 0.55] | 51 | 0.520 | 0.431 | -0.088 | -1.265 |  |  |
| shot: home win chance, all games | (0.55, 0.65] | 82 | 0.598 | 0.671 | 0.073 | 1.352 |  |  |
| shot: home win chance, all games | (0.65, 1.0] | 20 | 0.685 | 0.850 | 0.165 | 1.584 |  |  |
| shot: home win chance, all games | ALL | 261 | 0.518 | 0.563 | 0.045 | 1.462 | 0.231 | 0.655 |


### bets

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 1 | 0.344 | 0.000 | -0.344 | -0.724 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 77 | 0.415 | 0.312 | -0.103 | -1.842 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 74 | 0.474 | 0.338 | -0.136 | -2.342 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 74 | 0.524 | 0.500 | -0.024 | -0.412 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 34 | 0.581 | 0.500 | -0.081 | -0.962 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 1 | 0.666 | 1.000 | 0.334 | 0.708 |  |  |
| goals: higher-EV side of every game (not only rule bets) | ALL | 261 | 0.485 | 0.398 | -0.086 | -2.795 | 0.239 | 0.671 |
| shot: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 11 | 0.314 | 0.000 | -0.314 | -2.243 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 55 | 0.404 | 0.345 | -0.058 | -0.878 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 48 | 0.479 | 0.479 | 0.000 | 0.003 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 47 | 0.523 | 0.319 | -0.204 | -2.797 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 78 | 0.593 | 0.603 | 0.009 | 0.170 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 22 | 0.683 | 0.682 | -0.002 | -0.015 |  |  |
| shot: higher-EV side of every game (not only rule bets) | ALL | 261 | 0.515 | 0.456 | -0.059 | -1.921 | 0.231 | 0.655 |


### price_bands

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | units |
|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game, by price band | -150 or shorter | 8 | 0.630 | 0.750 | 0.120 | 0.702 | 1.277 |
| goals: higher-EV side of every game, by price band | -149..+99 | 72 | 0.538 | 0.486 | -0.052 | -0.882 | -6.545 |
| goals: higher-EV side of every game, by price band | +100..+149 | 116 | 0.480 | 0.388 | -0.092 | -1.980 | -17.0 |
| goals: higher-EV side of every game, by price band | +150..+249 | 61 | 0.420 | 0.295 | -0.125 | -1.984 | -12.7 |
| goals: higher-EV side of every game, by price band | +250 or longer | 4 | 0.374 | 0.000 | -0.374 | -1.545 | -4.000 |
| shot: higher-EV side of every game, by price band | -150 or shorter | 39 | 0.651 | 0.718 | 0.066 | 0.871 | 4.610 |
| shot: higher-EV side of every game, by price band | -149..+99 | 88 | 0.562 | 0.455 | -0.108 | -2.035 | -15.4 |
| shot: higher-EV side of every game, by price band | +100..+149 | 83 | 0.485 | 0.470 | -0.015 | -0.281 | 1.800 |
| shot: higher-EV side of every game, by price band | +150..+249 | 47 | 0.387 | 0.255 | -0.132 | -1.854 | -14.2 |
| shot: higher-EV side of every game, by price band | +250 or longer | 4 | 0.290 | 0.000 | -0.290 | -1.277 | -4.000 |


## CLV against Pinnacle's closing price (games from Nov 2, 2026; live recorder only)

price_clv_pct = fair Pinnacle close x bet decimal odds - 1 (negative = paid the usual vig at the same line; zero or above = beat the close). winpct_pts = fair close chance - break-even chance. points_clv = points better than Pinnacle's closing line.

| source | rule | market | n | points_clv_n | points_clv_mean | points_clv_lo90 | points_clv_hi90 | price_clv_pct_n | price_clv_pct_mean | price_clv_pct_lo90 | price_clv_pct_hi90 | winpct_pts_n | winpct_pts_mean | winpct_pts_lo90 | winpct_pts_hi90 | share_points_positive | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scorecard | goals open moneyline EV>=6% | moneyline | 12 | 0 |  |  |  | 12 | -0.048 | -0.072 | -0.022 | 12 | -2.083 | -3.177 | -0.899 |  | n<30: too few bets to read |
| scorecard | goals open puck line EV>=6% | puck line | 5 | 5 | 0.000 | 0.000 | 0.000 | 5 | -0.031 | -0.056 | -0.006 | 5 | -1.520 | -2.947 | -0.179 | 0.000 | n<30: too few bets to read |
| scorecard | goals open total EV>=6% (not in rule) | total | 5 | 5 | 0.100 | -0.300 | 0.500 | 1 | 0.066 | 0.066 | 0.066 | 1 | 3.446 | 3.446 | 3.446 | 0.400 | n<30: too few bets to read |
| scorecard | shot open moneyline EV>=6% | moneyline | 8 | 0 |  |  |  | 8 | 0.004 | -0.022 | 0.030 | 8 | 0.249 | -0.874 | 1.394 |  | n<30: too few bets to read |
| scorecard | shot open puck line EV>=6% | puck line | 6 | 6 | 0.000 | 0.000 | 0.000 | 6 | 0.013 | -0.013 | 0.041 | 6 | 0.407 | -0.732 | 1.500 | 0.000 | n<30: too few bets to read |
| scorecard | shot open total EV>=6% (not in rule) | total | 1 | 1 | 1.000 | 1.000 | 1.000 | 0 |  |  |  | 0 |  |  |  | 1.000 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET | moneyline | 3 | 0 |  |  |  | 3 | -0.034 | -0.070 | 0.003 | 3 | -1.476 | -3.088 | 0.136 |  | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET | puck line | 2 | 2 | 0.000 | 0.000 | 0.000 | 2 | -0.024 | -0.046 | -0.002 | 2 | -1.248 | -2.381 | -0.116 | 0.000 | n<30: too few bets to read |
| alerts | xg alert moneyline caution / DON'T BET | moneyline | 5 | 0 |  |  |  | 5 | 0.003 | -0.028 | 0.030 | 5 | 0.445 | -0.846 | 1.529 |  | n<30: too few bets to read |
| alerts | xg alert puck line caution / DON'T BET | puck line | 3 | 3 | 0.000 | 0.000 | 0.000 | 3 | -0.033 | -0.056 | -0.009 | 3 | -1.291 | -2.283 | -0.300 | 0.000 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | moneyline | 2 | 0 |  |  |  | 2 | 0.020 | 0.009 | 0.031 | 2 | 0.898 | 0.431 | 1.364 |  | n<30: too few bets to read |
| alerts | xg alert puck line BET | puck line | 5 | 5 | 0.000 | 0.000 | 0.000 | 5 | 0.025 | 0.002 | 0.051 | 5 | 0.965 | 0.137 | 1.860 | 0.000 | n<30: too few bets to read |
| alerts | goals alert moneyline BET | moneyline | 3 | 0 |  |  |  | 3 | -0.035 | -0.070 | 0.001 | 3 | -1.583 | -3.088 | -0.078 |  | n<30: too few bets to read |
| alerts | goals alert puck line BET | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.002 | -0.002 | -0.002 | 1 | -0.116 | -0.116 | -0.116 | 0.000 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET (opening price only) | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.060 | -0.060 | -0.060 | 1 | -2.085 | -2.085 | -2.085 | 0.000 | n<30: too few bets to read |
| alerts | goals alert total BET | total | 2 | 2 | -0.250 | -0.500 | 0.000 | 1 | 0.066 | 0.066 | 0.066 | 1 | 3.446 | 3.446 | 3.446 | 0.000 | n<30: too few bets to read |
| alerts | xg alert total BET | total | 3 | 3 | 0.000 | -0.333 | 0.333 | 1 | 0.066 | 0.066 | 0.066 | 1 | 3.446 | 3.446 | 3.446 | 0.333 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET (opening price only) | moneyline | 1 | 0 |  |  |  | 1 | -0.072 | -0.072 | -0.072 | 1 | -2.223 | -2.223 | -2.223 |  | n<30: too few bets to read |
| my bets | NHL v1 (goals + shot models) | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| my bets | NHL v3 | puck line | 2 | 2 | 0.000 | 0.000 | 0.000 | 2 | 0.027 | 0.005 | 0.049 | 2 | 1.037 | 0.205 | 1.869 | 0.000 | n<30: too few bets to read |
| my bets | NHL overs v1.1 | total | 1 | 1 | -0.500 | -0.500 | -0.500 | 0 |  |  |  | 0 |  |  |  | 0.000 | n<30: too few bets to read |
| my bets | NHL v3.1 | moneyline | 1 | 0 |  |  |  | 1 | 0.031 | 0.031 | 0.031 | 1 | 1.364 | 1.364 | 1.364 |  | n<30: too few bets to read |
| my bets | NHL v3.1 | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.013 | -0.013 | -0.013 | 1 | -0.521 | -0.521 | -0.521 | 0.000 | n<30: too few bets to read |
| my bets | ALL logged bets | moneyline | 2 | 0 |  |  |  | 2 | 0.020 | 0.009 | 0.031 | 2 | 0.898 | 0.431 | 1.364 |  | n<30: too few bets to read |
| my bets | ALL logged bets | puck line | 3 | 3 | 0.000 | 0.000 | 0.000 | 3 | 0.013 | -0.007 | 0.034 | 3 | 0.518 | -0.279 | 1.314 | 0.000 | n<30: too few bets to read |
| my bets | ALL logged bets | total | 1 | 1 | -0.500 | -0.500 | -0.500 | 0 |  |  |  | 0 |  |  |  | 0.000 | n<30: too few bets to read |


## By sportsbook (bets logged through `Log a bet`)

Book names are normalized (dk / DraftKings are one book). `(not recorded)` means the form's Sportsbook field was blank.

| book | bets | graded | stake_units | units | roi | roi_lo90 | roi_hi90 | clv_mean | clv_n | first_bet | last_bet | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DraftKings | 27 | 24 | 27.0 | 2.410 | 0.100 | -0.280 | 0.491 | -0.018 | 22 | 2026-10-30 | 2026-11-05 | n<30: too few bets to read |
| (not recorded) | 1 | 1 | 1.000 | 0.930 | 0.930 | 0.930 | 0.930 | 0.013 | 1 | 2026-10-31 | 2026-10-31 | n<30: too few bets to read |


### Limit events (`Log a limit` form, state/book_limits.csv)

`bets_logged_at_book_before` counts logged bets at that book up to the end of that day, so a cut can be read against how much was bet and won first.

_no rows yet_

