# Edge statistics (NHL), made 2026-11-05 10:05 ET

## ROI and closing line value with bootstrap ranges

ROI = units won per bet (each bet 1 unit; scorecard NBA/NFL bets at -110). 90% ranges from 10,000 resamples; `by_day` resamples whole days. CLV is in win-prob (fraction) against DraftKings' close (as logged); Pinnacle price CLV is below.

| source | rule | scope | n | W | L | P | units | roi | roi_lo90 | roi_hi90 | roi_lo90_by_day | roi_hi90_by_day | p_roi_above_0 | clv_n | clv_mean | clv_lo90 | clv_hi90 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scorecard | goals open moneyline EV>=6% | all | 112 | 38 | 74 | 0 | -22.5 | -0.201 | -0.378 | -0.022 | -0.313 | -0.075 | 0.031 | 112 | -0.038 | -0.048 | -0.027 |  |
| scorecard | goals open moneyline EV>=6% | live only | 19 | 6 | 13 | 0 | -5.530 | -0.291 | -0.660 | 0.113 | -0.685 | 0.164 | 0.111 | 19 | -0.036 | -0.054 | -0.016 | n<30: too few bets to read |
| scorecard | goals open puck line EV>=6% | all | 77 | 39 | 38 | 0 | -13.4 | -0.174 | -0.330 | -0.017 | -0.293 | -0.056 | 0.034 | 75 | -0.034 | -0.042 | -0.025 |  |
| scorecard | goals open puck line EV>=6% | live only | 8 | 3 | 5 | 0 | -3.470 | -0.433 | -0.820 | -0.033 | -0.733 | -0.130 | 0.036 | 8 | -0.046 | -0.065 | -0.029 | n<30: too few bets to read |
| scorecard | goals open total EV>=6% (not in rule) | all | 37 | 19 | 18 | 0 | 1.220 | 0.033 | -0.240 | 0.305 | -0.179 | 0.238 | 0.569 | 32 | 0.019 | 0.005 | 0.033 |  |
| scorecard | goals open total EV>=6% (not in rule) | live only | 9 | 6 | 3 | 0 | 2.860 | 0.318 | -0.176 | 0.800 | 0.146 | 0.779 | 0.853 | 8 | 0.025 | 0.002 | 0.047 | n<30: too few bets to read |
| scorecard | shot open moneyline EV>=6% | all | 88 | 39 | 49 | 0 | -6.980 | -0.079 | -0.262 | 0.110 | -0.250 | 0.108 | 0.241 | 88 | 0.011 | -0.001 | 0.022 |  |
| scorecard | shot open moneyline EV>=6% | live only | 13 | 7 | 6 | 0 | 0.670 | 0.051 | -0.401 | 0.516 | -0.261 | 0.620 | 0.586 | 13 | 0.013 | -0.005 | 0.030 | n<30: too few bets to read |
| scorecard | shot open puck line EV>=6% | all | 71 | 35 | 36 | 0 | -5.980 | -0.084 | -0.272 | 0.111 | -0.346 | 0.163 | 0.232 | 63 | 0.008 | -0.005 | 0.021 |  |
| scorecard | shot open puck line EV>=6% | live only | 8 | 4 | 4 | 0 | 0.050 | 0.006 | -0.637 | 0.656 | -0.392 | 0.808 | 0.515 | 7 | -0.007 | -0.042 | 0.026 | n<30: too few bets to read |
| scorecard | shot open total EV>=6% (not in rule) | all | 37 | 24 | 13 | 0 | 9.400 | 0.254 | -0.003 | 0.503 | 0.010 | 0.503 | 0.948 | 27 | 0.004 | -0.012 | 0.021 |  |
| scorecard | shot open total EV>=6% (not in rule) | live only | 3 | 2 | 1 | 0 | 0.880 | 0.294 | -0.420 | 1.007 | -0.420 | 1.007 | 0.740 | 2 | 0.026 | -0.018 | 0.070 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET | all | 12 | 5 | 7 | 0 | -0.800 | -0.067 | -0.621 | 0.492 | -0.597 | 0.465 | 0.387 | 12 | -0.032 | -0.051 | -0.011 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET | all | 11 | 5 | 6 | 0 | -3.570 | -0.324 | -0.726 | 0.073 | -0.716 | 0.053 | 0.067 | 10 | -0.028 | -0.040 | -0.015 | n<30: too few bets to read |
| alerts | goals alert moneyline BET | all | 7 | 4 | 3 | 0 | 2.120 | 0.302 | -0.375 | 1.002 | -0.375 | 1.195 | 0.725 | 7 | -0.041 | -0.059 | -0.022 | n<30: too few bets to read |
| alerts | goals alert puck line BET | all | 6 | 3 | 3 | 0 | -1.420 | -0.237 | -0.741 | 0.282 | -0.611 | 0.454 | 0.264 | 6 | -0.034 | -0.040 | -0.026 | n<30: too few bets to read |
| alerts | xg alert moneyline caution / DON'T BET | all | 11 | 4 | 7 | 0 | -3.030 | -0.276 | -0.673 | 0.242 | -0.743 | 0.422 | 0.171 | 11 | 0.001 | -0.020 | 0.022 | n<30: too few bets to read |
| alerts | xg alert puck line caution / DON'T BET | all | 6 | 3 | 3 | 0 | -1.660 | -0.277 | -0.759 | 0.212 | -0.787 | 0.428 | 0.110 | 5 | -0.028 | -0.047 | -0.007 | n<30: too few bets to read |
| alerts | xg alert puck line BET | all | 6 | 3 | 3 | 0 | 0.630 | 0.105 | -0.577 | 0.951 | -0.365 | 0.905 | 0.575 | 6 | 0.010 | -0.017 | 0.037 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | all | 3 | 2 | 1 | 0 | 1.380 | 0.460 | -0.287 | 1.207 | -0.287 | 1.207 | 0.740 | 3 | -0.001 | -0.019 | 0.016 | n<30: too few bets to read |
| alerts | goals alert moneyline BET (opening price only) | all | 2 | 0 | 2 | 0 | -2.000 | -1.000 | -1.000 | -1.000 | -1.000 | -1.000 | 0.000 | 2 | -0.035 | -0.041 | -0.029 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET (opening price only) | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.058 | -0.058 | -0.058 | n<30: too few bets to read |
| alerts | xg alert total BET | all | 3 | 1 | 2 | 0 | -1.230 | -0.410 | -1.000 | 0.179 |  |  | 0.262 | 3 | -0.002 | -0.047 | 0.042 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET (opening price only) | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.069 | -0.069 | -0.069 | n<30: too few bets to read |
| alerts | goals alert total BET | all | 2 | 0 | 2 | 0 | -2.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 2 | 0.009 | -0.058 | 0.076 | n<30: too few bets to read |
| my bets | NHL v1 (goals + shot models) | all | 16 | 7 | 9 | 0 | -2.310 | -0.144 | -0.548 | 0.273 | -0.454 | 0.165 | 0.284 | 14 | -0.030 | -0.044 | -0.016 | n<30: too few bets to read |
| my bets | NHL v3 | all | 2 | 1 | 1 | 0 | 0.600 | 0.300 | -1.000 | 1.600 |  |  | 0.747 | 2 | 0.034 | 0.027 | 0.041 | n<30: too few bets to read |
| my bets | NHL overs v1.1 | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.058 | -0.058 | -0.058 | n<30: too few bets to read |
| my bets | NHL v3.1 | all | 2 | 2 | 0 | 0 | 2.780 | 1.390 | 1.240 | 1.540 |  |  | 1.000 | 2 | -0.008 | -0.041 | 0.024 | n<30: too few bets to read |
| my bets | ALL logged bets | all | 21 | 10 | 11 | 0 | 0.070 | 0.003 | -0.389 | 0.390 | -0.275 | 0.476 | 0.497 | 19 | -0.023 | -0.036 | -0.008 | n<30: too few bets to read |


## Calibration: predicted chance vs what happened

### games

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: home win chance, all games | (0.35, 0.45] | 28 | 0.416 | 0.429 | 0.013 | 0.139 |  |  |
| goals: home win chance, all games | (0.45, 0.5] | 55 | 0.476 | 0.455 | -0.021 | -0.318 |  |  |
| goals: home win chance, all games | (0.5, 0.55] | 87 | 0.525 | 0.586 | 0.061 | 1.141 |  |  |
| goals: home win chance, all games | (0.55, 0.65] | 78 | 0.583 | 0.654 | 0.071 | 1.272 |  |  |
| goals: home win chance, all games | (0.65, 1.0] | 2 | 0.661 | 1.000 | 0.339 | 1.012 |  |  |
| goals: home win chance, all games | ALL | 250 | 0.521 | 0.564 | 0.043 | 1.357 | 0.239 | 0.672 |
| shot: home win chance, all games | (-0.001, 0.35] | 12 | 0.317 | 0.333 | 0.016 | 0.123 |  |  |
| shot: home win chance, all games | (0.35, 0.45] | 49 | 0.409 | 0.429 | 0.019 | 0.277 |  |  |
| shot: home win chance, all games | (0.45, 0.5] | 43 | 0.476 | 0.605 | 0.129 | 1.690 |  |  |
| shot: home win chance, all games | (0.5, 0.55] | 50 | 0.520 | 0.440 | -0.080 | -1.135 |  |  |
| shot: home win chance, all games | (0.55, 0.65] | 77 | 0.597 | 0.675 | 0.078 | 1.398 |  |  |
| shot: home win chance, all games | (0.65, 1.0] | 19 | 0.684 | 0.842 | 0.159 | 1.486 |  |  |
| shot: home win chance, all games | ALL | 250 | 0.517 | 0.564 | 0.047 | 1.482 | 0.232 | 0.655 |


### bets

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 1 | 0.344 | 0.000 | -0.344 | -0.724 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 72 | 0.416 | 0.306 | -0.110 | -1.899 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 71 | 0.474 | 0.352 | -0.122 | -2.053 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 71 | 0.523 | 0.493 | -0.030 | -0.509 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 34 | 0.581 | 0.500 | -0.081 | -0.962 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 1 | 0.666 | 1.000 | 0.334 | 0.708 |  |  |
| goals: higher-EV side of every game (not only rule bets) | ALL | 250 | 0.486 | 0.400 | -0.086 | -2.721 | 0.239 | 0.672 |
| shot: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 10 | 0.318 | 0.000 | -0.318 | -2.157 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 50 | 0.404 | 0.340 | -0.064 | -0.924 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 46 | 0.479 | 0.478 | -0.001 | -0.010 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 47 | 0.523 | 0.319 | -0.204 | -2.797 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 76 | 0.594 | 0.618 | 0.024 | 0.434 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 21 | 0.684 | 0.667 | -0.017 | -0.169 |  |  |
| shot: higher-EV side of every game (not only rule bets) | ALL | 250 | 0.518 | 0.460 | -0.058 | -1.834 | 0.232 | 0.655 |


### price_bands

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | units |
|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game, by price band | -150 or shorter | 8 | 0.630 | 0.750 | 0.120 | 0.702 | 1.277 |
| goals: higher-EV side of every game, by price band | -149..+99 | 69 | 0.538 | 0.478 | -0.059 | -0.990 | -7.397 |
| goals: higher-EV side of every game, by price band | +100..+149 | 113 | 0.480 | 0.398 | -0.082 | -1.749 | -14.0 |
| goals: higher-EV side of every game, by price band | +150..+249 | 57 | 0.420 | 0.281 | -0.139 | -2.128 | -14.2 |
| goals: higher-EV side of every game, by price band | +250 or longer | 3 | 0.380 | 0.000 | -0.380 | -1.355 | -3.000 |
| shot: higher-EV side of every game, by price band | -150 or shorter | 38 | 0.651 | 0.711 | 0.060 | 0.771 | 4.008 |
| shot: higher-EV side of every game, by price band | -149..+99 | 85 | 0.563 | 0.459 | -0.104 | -1.936 | -14.3 |
| shot: higher-EV side of every game, by price band | +100..+149 | 81 | 0.486 | 0.481 | -0.005 | -0.085 | 3.800 |
| shot: higher-EV side of every game, by price band | +150..+249 | 43 | 0.387 | 0.233 | -0.154 | -2.080 | -15.8 |
| shot: higher-EV side of every game, by price band | +250 or longer | 3 | 0.294 | 0.000 | -0.294 | -1.116 | -3.000 |


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
| alerts | goals alert moneyline BET | moneyline | 3 | 0 |  |  |  | 3 | -0.035 | -0.070 | 0.001 | 3 | -1.583 | -3.088 | -0.078 |  | n<30: too few bets to read |
| alerts | goals alert puck line BET | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.002 | -0.002 | -0.002 | 1 | -0.116 | -0.116 | -0.116 | 0.000 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | moneyline | 2 | 0 |  |  |  | 2 | 0.020 | 0.009 | 0.031 | 2 | 0.898 | 0.431 | 1.364 |  | n<30: too few bets to read |
| alerts | xg alert puck line BET | puck line | 5 | 5 | 0.000 | 0.000 | 0.000 | 5 | 0.025 | 0.002 | 0.051 | 5 | 0.965 | 0.119 | 1.860 | 0.000 | n<30: too few bets to read |
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
| DraftKings | 23 | 20 | 23.0 | -0.860 | -0.043 | -0.445 | 0.362 | -0.024 | 19 | 2026-10-30 | 2026-11-04 | n<30: too few bets to read |
| (not recorded) | 1 | 1 | 1.000 | 0.930 | 0.930 | 0.930 | 0.930 | 0.013 | 1 | 2026-10-31 | 2026-10-31 | n<30: too few bets to read |


### Limit events (`Log a limit` form, state/book_limits.csv)

`bets_logged_at_book_before` counts logged bets at that book up to the end of that day, so a cut can be read against how much was bet and won first.

_no rows yet_

