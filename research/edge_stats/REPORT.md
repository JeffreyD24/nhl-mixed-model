# Edge statistics (NHL), made 2026-11-04 10:02 ET

## ROI and closing line value with bootstrap ranges

ROI = units won per bet (each bet 1 unit; scorecard NBA/NFL bets at -110). 90% ranges from 10,000 resamples; `by_day` resamples whole days. CLV is in win-prob (fraction) against DraftKings' close (as logged); Pinnacle price CLV is below.

| source | rule | scope | n | W | L | P | units | roi | roi_lo90 | roi_hi90 | roi_lo90_by_day | roi_hi90_by_day | p_roi_above_0 | clv_n | clv_mean | clv_lo90 | clv_hi90 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scorecard | goals open moneyline EV>=6% | all | 108 | 37 | 71 | 0 | -20.8 | -0.192 | -0.373 | -0.012 | -0.309 | -0.061 | 0.041 | 108 | -0.039 | -0.050 | -0.029 |  |
| scorecard | goals open moneyline EV>=6% | live only | 15 | 5 | 10 | 0 | -3.770 | -0.252 | -0.697 | 0.215 | -0.767 | 0.333 | 0.190 | 15 | -0.045 | -0.064 | -0.025 | n<30: too few bets to read |
| scorecard | goals open puck line EV>=6% | all | 76 | 39 | 37 | 0 | -12.4 | -0.163 | -0.321 | -0.007 | -0.282 | -0.043 | 0.043 | 74 | -0.034 | -0.043 | -0.025 |  |
| scorecard | goals open puck line EV>=6% | live only | 7 | 3 | 4 | 0 | -2.470 | -0.352 | -0.794 | 0.099 | -0.639 | 0.015 | 0.130 | 7 | -0.051 | -0.070 | -0.032 | n<30: too few bets to read |
| scorecard | goals open total EV>=6% (not in rule) | all | 37 | 19 | 18 | 0 | 1.220 | 0.033 | -0.239 | 0.309 | -0.177 | 0.239 | 0.570 | 32 | 0.019 | 0.005 | 0.033 |  |
| scorecard | goals open total EV>=6% (not in rule) | live only | 9 | 6 | 3 | 0 | 2.860 | 0.318 | -0.170 | 0.800 | 0.146 | 0.779 | 0.851 | 8 | 0.025 | 0.002 | 0.047 | n<30: too few bets to read |
| scorecard | shot open moneyline EV>=6% | all | 86 | 38 | 48 | 0 | -7.220 | -0.084 | -0.270 | 0.104 | -0.259 | 0.103 | 0.232 | 86 | 0.010 | -0.002 | 0.021 |  |
| scorecard | shot open moneyline EV>=6% | live only | 11 | 6 | 5 | 0 | 0.430 | 0.039 | -0.455 | 0.541 | -0.334 | 1.054 | 0.577 | 11 | 0.006 | -0.013 | 0.024 | n<30: too few bets to read |
| scorecard | shot open puck line EV>=6% | all | 70 | 34 | 36 | 0 | -7.520 | -0.107 | -0.300 | 0.088 | -0.363 | 0.139 | 0.184 | 62 | 0.009 | -0.004 | 0.022 |  |
| scorecard | shot open puck line EV>=6% | live only | 7 | 3 | 4 | 0 | -1.490 | -0.213 | -0.797 | 0.381 | -0.628 | 0.437 | 0.236 | 6 | -0.001 | -0.041 | 0.036 | n<30: too few bets to read |
| scorecard | shot open total EV>=6% (not in rule) | all | 37 | 24 | 13 | 0 | 9.400 | 0.254 | -0.001 | 0.500 | 0.013 | 0.506 | 0.949 | 27 | 0.004 | -0.012 | 0.021 |  |
| scorecard | shot open total EV>=6% (not in rule) | live only | 3 | 2 | 1 | 0 | 0.880 | 0.294 | -0.420 | 1.007 | -0.420 | 1.007 | 0.738 | 2 | 0.026 | -0.018 | 0.070 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET | all | 12 | 5 | 7 | 0 | -0.800 | -0.067 | -0.607 | 0.489 | -0.600 | 0.465 | 0.383 | 12 | -0.032 | -0.051 | -0.011 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET | all | 11 | 5 | 6 | 0 | -3.570 | -0.324 | -0.724 | 0.065 | -0.716 | 0.053 | 0.061 | 10 | -0.028 | -0.040 | -0.015 | n<30: too few bets to read |
| alerts | goals alert moneyline BET | all | 6 | 3 | 3 | 0 | 0.880 | 0.146 | -0.592 | 0.963 | -0.583 | 0.875 | 0.648 | 6 | -0.052 | -0.063 | -0.042 | n<30: too few bets to read |
| alerts | goals alert puck line BET | all | 6 | 3 | 3 | 0 | -1.420 | -0.237 | -0.741 | 0.289 | -0.599 | 0.454 | 0.272 | 6 | -0.034 | -0.040 | -0.026 | n<30: too few bets to read |
| alerts | xg alert moneyline caution / DON'T BET | all | 11 | 4 | 7 | 0 | -3.030 | -0.276 | -0.673 | 0.246 | -0.743 | 0.422 | 0.170 | 11 | 0.001 | -0.020 | 0.023 | n<30: too few bets to read |
| alerts | xg alert puck line caution / DON'T BET | all | 6 | 3 | 3 | 0 | -1.660 | -0.277 | -0.759 | 0.212 | -0.787 | 0.428 | 0.107 | 5 | -0.028 | -0.047 | -0.007 | n<30: too few bets to read |
| alerts | xg alert puck line BET | all | 5 | 2 | 3 | 0 | -0.910 | -0.182 | -1.000 | 0.635 | -0.504 | 0.115 | 0.375 | 5 | 0.021 | -0.009 | 0.047 | n<30: too few bets to read |
| alerts | goals alert moneyline BET (opening price only) | all | 2 | 0 | 2 | 0 | -2.000 | -1.000 | -1.000 | -1.000 | -1.000 | -1.000 | 0.000 | 2 | -0.035 | -0.041 | -0.029 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | all | 2 | 1 | 1 | 0 | 0.140 | 0.070 | -1.000 | 1.140 | -1.000 | 1.140 | 0.751 | 2 | -0.014 | -0.029 | 0.001 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET (opening price only) | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.058 | -0.058 | -0.058 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET (opening price only) | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.069 | -0.069 | -0.069 | n<30: too few bets to read |
| alerts | goals alert total BET | all | 2 | 0 | 2 | 0 | -2.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 2 | 0.009 | -0.058 | 0.076 | n<30: too few bets to read |
| alerts | xg alert total BET | all | 3 | 1 | 2 | 0 | -1.230 | -0.410 | -1.000 | 0.179 |  |  | 0.258 | 3 | -0.002 | -0.047 | 0.042 | n<30: too few bets to read |
| my bets | NHL v1 (goals + shot models) | all | 16 | 7 | 9 | 0 | -2.310 | -0.144 | -0.551 | 0.269 | -0.454 | 0.165 | 0.274 | 14 | -0.030 | -0.044 | -0.016 | n<30: too few bets to read |
| my bets | NHL v3 | all | 2 | 1 | 1 | 0 | 0.600 | 0.300 | -1.000 | 1.600 |  |  | 0.756 | 2 | 0.034 | 0.027 | 0.041 | n<30: too few bets to read |
| my bets | NHL overs v1.1 | all | 1 | 0 | 1 | 0 | -1.000 | -1.000 | -1.000 | -1.000 |  |  | 0.000 | 1 | -0.058 | -0.058 | -0.058 | n<30: too few bets to read |
| my bets | ALL logged bets | all | 19 | 8 | 11 | 0 | -2.710 | -0.143 | -0.526 | 0.263 | -0.362 | 0.111 | 0.269 | 17 | -0.024 | -0.039 | -0.009 | n<30: too few bets to read |


## Calibration: predicted chance vs what happened

### games

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: home win chance, all games | (0.35, 0.45] | 28 | 0.416 | 0.429 | 0.013 | 0.139 |  |  |
| goals: home win chance, all games | (0.45, 0.5] | 55 | 0.476 | 0.455 | -0.021 | -0.318 |  |  |
| goals: home win chance, all games | (0.5, 0.55] | 84 | 0.525 | 0.583 | 0.059 | 1.074 |  |  |
| goals: home win chance, all games | (0.55, 0.65] | 77 | 0.583 | 0.649 | 0.067 | 1.188 |  |  |
| goals: home win chance, all games | (0.65, 1.0] | 2 | 0.661 | 1.000 | 0.339 | 1.012 |  |  |
| goals: home win chance, all games | ALL | 246 | 0.521 | 0.561 | 0.040 | 1.266 | 0.240 | 0.673 |
| shot: home win chance, all games | (-0.001, 0.35] | 12 | 0.317 | 0.333 | 0.016 | 0.123 |  |  |
| shot: home win chance, all games | (0.35, 0.45] | 49 | 0.409 | 0.429 | 0.019 | 0.277 |  |  |
| shot: home win chance, all games | (0.45, 0.5] | 43 | 0.476 | 0.605 | 0.129 | 1.690 |  |  |
| shot: home win chance, all games | (0.5, 0.55] | 48 | 0.520 | 0.438 | -0.083 | -1.145 |  |  |
| shot: home win chance, all games | (0.55, 0.65] | 77 | 0.597 | 0.675 | 0.078 | 1.398 |  |  |
| shot: home win chance, all games | (0.65, 1.0] | 17 | 0.685 | 0.824 | 0.138 | 1.227 |  |  |
| shot: home win chance, all games | ALL | 246 | 0.516 | 0.561 | 0.045 | 1.414 | 0.233 | 0.657 |


### bets

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | brier | logloss |
|---|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 1 | 0.344 | 0.000 | -0.344 | -0.724 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 71 | 0.416 | 0.310 | -0.106 | -1.817 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 68 | 0.474 | 0.353 | -0.121 | -2.001 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 71 | 0.523 | 0.493 | -0.030 | -0.509 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 34 | 0.581 | 0.500 | -0.081 | -0.962 |  |  |
| goals: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 1 | 0.666 | 1.000 | 0.334 | 0.708 |  |  |
| goals: higher-EV side of every game (not only rule bets) | ALL | 246 | 0.487 | 0.402 | -0.084 | -2.641 | 0.240 | 0.673 |
| shot: higher-EV side of every game (not only rule bets) | (-0.001, 0.35] | 10 | 0.318 | 0.000 | -0.318 | -2.157 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.35, 0.45] | 50 | 0.404 | 0.340 | -0.064 | -0.924 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.45, 0.5] | 44 | 0.479 | 0.477 | -0.002 | -0.023 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.5, 0.55] | 47 | 0.523 | 0.319 | -0.204 | -2.797 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.55, 0.65] | 76 | 0.594 | 0.618 | 0.024 | 0.434 |  |  |
| shot: higher-EV side of every game (not only rule bets) | (0.65, 1.0] | 19 | 0.685 | 0.632 | -0.054 | -0.506 |  |  |
| shot: higher-EV side of every game (not only rule bets) | ALL | 246 | 0.517 | 0.455 | -0.062 | -1.939 | 0.233 | 0.657 |


### price_bands

`z` is (actual - predicted) in standard errors; |z| above 2 is worth a look, and below 30 bets per bin it is mostly noise.

| set | bin | n | predicted | actual | diff | z | units |
|---|---|---|---|---|---|---|---|
| goals: higher-EV side of every game, by price band | -150 or shorter | 8 | 0.630 | 0.750 | 0.120 | 0.702 | 1.277 |
| goals: higher-EV side of every game, by price band | -149..+99 | 69 | 0.538 | 0.478 | -0.059 | -0.990 | -7.397 |
| goals: higher-EV side of every game, by price band | +100..+149 | 110 | 0.481 | 0.400 | -0.081 | -1.696 | -13.2 |
| goals: higher-EV side of every game, by price band | +150..+249 | 56 | 0.420 | 0.286 | -0.135 | -2.039 | -13.2 |
| goals: higher-EV side of every game, by price band | +250 or longer | 3 | 0.380 | 0.000 | -0.380 | -1.355 | -3.000 |
| shot: higher-EV side of every game, by price band | -150 or shorter | 36 | 0.650 | 0.694 | 0.044 | 0.560 | 3.006 |
| shot: higher-EV side of every game, by price band | -149..+99 | 85 | 0.563 | 0.459 | -0.104 | -1.936 | -14.3 |
| shot: higher-EV side of every game, by price band | +100..+149 | 79 | 0.486 | 0.481 | -0.005 | -0.096 | 3.560 |
| shot: higher-EV side of every game, by price band | +150..+249 | 43 | 0.387 | 0.233 | -0.154 | -2.080 | -15.8 |
| shot: higher-EV side of every game, by price band | +250 or longer | 3 | 0.294 | 0.000 | -0.294 | -1.116 | -3.000 |


## CLV against Pinnacle's closing price (games from Nov 2, 2026; live recorder only)

price_clv_pct = fair Pinnacle close x bet decimal odds - 1 (negative = paid the usual vig at the same line; zero or above = beat the close). winpct_pts = fair close chance - break-even chance. points_clv = points better than Pinnacle's closing line.

| source | rule | market | n | points_clv_n | points_clv_mean | points_clv_lo90 | points_clv_hi90 | price_clv_pct_n | price_clv_pct_mean | price_clv_pct_lo90 | price_clv_pct_hi90 | winpct_pts_n | winpct_pts_mean | winpct_pts_lo90 | winpct_pts_hi90 | share_points_positive | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scorecard | goals open moneyline EV>=6% | moneyline | 8 | 0 |  |  |  | 8 | -0.071 | -0.089 | -0.054 | 8 | -3.114 | -4.073 | -2.331 |  | n<30: too few bets to read |
| scorecard | goals open puck line EV>=6% | puck line | 4 | 4 | 0.000 | 0.000 | 0.000 | 4 | -0.039 | -0.061 | -0.015 | 4 | -1.910 | -3.311 | -0.259 | 0.000 | n<30: too few bets to read |
| scorecard | goals open total EV>=6% (not in rule) | total | 5 | 5 | 0.100 | -0.300 | 0.500 | 1 | 0.066 | 0.066 | 0.066 | 1 | 3.446 | 3.446 | 3.446 | 0.400 | n<30: too few bets to read |
| scorecard | shot open moneyline EV>=6% | moneyline | 6 | 0 |  |  |  | 6 | -0.013 | -0.037 | 0.011 | 6 | -0.450 | -1.501 | 0.699 |  | n<30: too few bets to read |
| scorecard | shot open puck line EV>=6% | puck line | 5 | 5 | 0.000 | 0.000 | 0.000 | 5 | 0.019 | -0.014 | 0.050 | 5 | 0.593 | -0.752 | 1.776 | 0.000 | n<30: too few bets to read |
| scorecard | shot open total EV>=6% (not in rule) | total | 1 | 1 | 1.000 | 1.000 | 1.000 | 0 |  |  |  | 0 |  |  |  | 1.000 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET | moneyline | 3 | 0 |  |  |  | 3 | -0.034 | -0.070 | 0.003 | 3 | -1.476 | -3.088 | 0.136 |  | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET | puck line | 2 | 2 | 0.000 | 0.000 | 0.000 | 2 | -0.024 | -0.046 | -0.002 | 2 | -1.248 | -2.381 | -0.116 | 0.000 | n<30: too few bets to read |
| alerts | xg alert moneyline caution / DON'T BET | moneyline | 5 | 0 |  |  |  | 5 | 0.003 | -0.030 | 0.030 | 5 | 0.445 | -0.760 | 1.629 |  | n<30: too few bets to read |
| alerts | xg alert puck line caution / DON'T BET | puck line | 3 | 3 | 0.000 | 0.000 | 0.000 | 3 | -0.033 | -0.056 | -0.009 | 3 | -1.291 | -2.283 | -0.300 | 0.000 | n<30: too few bets to read |
| alerts | xg alert puck line BET | puck line | 4 | 4 | 0.000 | 0.000 | 0.000 | 4 | 0.035 | 0.008 | 0.060 | 4 | 1.336 | 0.495 | 2.157 | 0.000 | n<30: too few bets to read |
| alerts | xg alert moneyline BET | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| alerts | goals alert moneyline BET | moneyline | 2 | 0 |  |  |  | 2 | -0.067 | -0.077 | -0.057 | 2 | -3.057 | -3.151 | -2.962 |  | n<30: too few bets to read |
| alerts | goals alert puck line BET | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.002 | -0.002 | -0.002 | 1 | -0.116 | -0.116 | -0.116 | 0.000 | n<30: too few bets to read |
| alerts | goals alert puck line caution / DON'T BET (opening price only) | puck line | 1 | 1 | 0.000 | 0.000 | 0.000 | 1 | -0.060 | -0.060 | -0.060 | 1 | -2.085 | -2.085 | -2.085 | 0.000 | n<30: too few bets to read |
| alerts | xg alert total BET | total | 3 | 3 | 0.000 | -0.333 | 0.333 | 1 | 0.066 | 0.066 | 0.066 | 1 | 3.446 | 3.446 | 3.446 | 0.333 | n<30: too few bets to read |
| alerts | goals alert moneyline caution / DON'T BET (opening price only) | moneyline | 1 | 0 |  |  |  | 1 | -0.072 | -0.072 | -0.072 | 1 | -2.223 | -2.223 | -2.223 |  | n<30: too few bets to read |
| alerts | goals alert total BET | total | 2 | 2 | -0.250 | -0.500 | 0.000 | 1 | 0.066 | 0.066 | 0.066 | 1 | 3.446 | 3.446 | 3.446 | 0.000 | n<30: too few bets to read |
| my bets | NHL v1 (goals + shot models) | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| my bets | NHL v3 | puck line | 2 | 2 | 0.000 | 0.000 | 0.000 | 2 | 0.027 | 0.005 | 0.049 | 2 | 1.037 | 0.205 | 1.869 | 0.000 | n<30: too few bets to read |
| my bets | NHL overs v1.1 | total | 1 | 1 | -0.500 | -0.500 | -0.500 | 0 |  |  |  | 0 |  |  |  | 0.000 | n<30: too few bets to read |
| my bets | ALL logged bets | moneyline | 1 | 0 |  |  |  | 1 | 0.009 | 0.009 | 0.009 | 1 | 0.431 | 0.431 | 0.431 |  | n<30: too few bets to read |
| my bets | ALL logged bets | puck line | 2 | 2 | 0.000 | 0.000 | 0.000 | 2 | 0.027 | 0.005 | 0.049 | 2 | 1.037 | 0.205 | 1.869 | 0.000 | n<30: too few bets to read |
| my bets | ALL logged bets | total | 1 | 1 | -0.500 | -0.500 | -0.500 | 0 |  |  |  | 0 |  |  |  | 0.000 | n<30: too few bets to read |


## By sportsbook (bets logged through `Log a bet`)

Book names are normalized (dk / DraftKings are one book). `(not recorded)` means the form's Sportsbook field was blank.

| book | bets | graded | stake_units | units | roi | roi_lo90 | roi_hi90 | clv_mean | clv_n | first_bet | last_bet | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DraftKings | 20 | 18 | 20.0 | -3.640 | -0.202 | -0.589 | 0.214 | -0.026 | 17 | 2026-10-30 | 2026-11-03 | n<30: too few bets to read |
| (not recorded) | 1 | 1 | 1.000 | 0.930 | 0.930 | 0.930 | 0.930 | 0.013 | 1 | 2026-10-31 | 2026-10-31 | n<30: too few bets to read |


### Limit events (`Log a limit` form, state/book_limits.csv)

`bets_logged_at_book_before` counts logged bets at that book up to the end of that day, so a cut can be read against how much was bet and won first.

_no rows yet_

