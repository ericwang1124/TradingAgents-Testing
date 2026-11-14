# Opening reversal short — market-regime study

- **Symbol**: SPY
- **Data**: Alpaca SIP 1-minute bars (adjusted), VIX daily closes from Yahoo
- **Period**: 2019-01-01 to 2026-11-12
- **Settings searched**: 192 (optimize.GRID)
- **Generated**: 2026-11-13 03:44
- **Regimes** (fixed, not optimised): trend = prior close vs 50-day SMA; volatility = prior-day VIX close < 15 / 15-20 / >= 20

## Walk-forward results (all out of sample)

Each year 2021-2026 is traded with settings chosen only from earlier years (best t-stat, >= 15 trades, t >= 1.0; otherwise stand aside).

|                                                                   |   trades |   win_% |   avg_R |   total_R |     t |
|:------------------------------------------------------------------|---------:|--------:|--------:|----------:|------:|
| regime-adaptive (pick setting per regime)                         |    80.00 |   48.75 |   -0.03 |     -2.47 | -0.26 |
| non-adaptive (pick one setting for all days)                      |    67.00 |   52.24 |    0.01 |      0.90 |  0.11 |
| original rules, regime gate (trade regime only if past avg R > 0) |    10.00 |   50.00 |   -0.13 |     -1.33 | -0.46 |
| original rules, always                                            |    65.00 |   47.69 |   -0.16 |    -10.24 | -1.33 |

Total R by year:

|   year |   regime-adaptive (pick setting per regime) |   non-adaptive (pick one setting for all days) |   original rules, regime gate (trade regime only if past avg R > 0) |   original rules, always |
|-------:|--------------------------------------------:|-----------------------------------------------:|--------------------------------------------------------------------:|-------------------------:|
|   2021 |                                        3.20 |                                           0.33 |                                                                0.00 |                    -1.54 |
|   2022 |                                        7.85 |                                           8.52 |                                                                0.00 |                    -4.22 |
|   2023 |                                       -5.35 |                                           0.68 |                                                                0.00 |                    -1.21 |
|   2024 |                                        2.47 |                                           0.91 |                                                               -1.02 |                    -4.14 |
|   2025 |                                       -3.25 |                                          -2.26 |                                                                0.00 |                     0.68 |
|   2026 |                                       -7.39 |                                          -7.28 |                                                               -0.31 |                     0.18 |

## Sessions per regime

| regime        |   2019-22 |   2023-26 |
|:--------------|----------:|----------:|
| down/vix15-20 |        44 |        98 |
| down/vix<15   |         2 |        10 |
| down/vix>=20  |       246 |       119 |
| up/vix15-20   |       257 |       424 |
| up/vix<15     |       152 |       265 |
| up/vix>=20    |       307 |        54 |

## Original rules by regime

| regime        |   ('trades', 'test') |   ('trades', 'train') |   ('avg_R', 'test') |   ('avg_R', 'train') |   ('total_R', 'test') |   ('total_R', 'train') |
|:--------------|---------------------:|----------------------:|--------------------:|---------------------:|----------------------:|-----------------------:|
| down/vix15-20 |                 3.00 |                  4.00 |               -0.02 |                -0.40 |                 -0.05 |                  -1.59 |
| down/vix>=20  |                 8.00 |                 12.00 |               -0.33 |                -0.23 |                 -2.62 |                  -2.71 |
| up/vix15-20   |                18.00 |                  8.00 |                0.05 |                 0.01 |                  0.90 |                   0.11 |
| up/vix<15     |                 9.00 |                 12.00 |               -0.47 |                -0.26 |                 -4.19 |                  -3.16 |
| up/vix>=20    |                 1.00 |                 17.00 |                1.48 |                -0.08 |                  1.48 |                  -1.30 |

## Within a regime, do good early settings stay good?

| regime        |   settings with >=8 trades in both |   rank corr train vs test |   positive in both |
|:--------------|-----------------------------------:|--------------------------:|-------------------:|
| down/vix15-20 |                              24.00 |                     -0.65 |               0.00 |
| down/vix<15   |                               0.00 |                    nan    |               0.00 |
| down/vix>=20  |                             102.00 |                     -0.28 |               8.00 |
| up/vix15-20   |                              74.00 |                     -0.79 |              12.00 |
| up/vix<15     |                              36.00 |                      0.54 |               6.00 |
| up/vix>=20    |                              16.00 |                     -0.58 |               0.00 |

## Regime-adaptive choices

|   year | regime        | choice                                                               |   train_n |   train_t |   oos_n |   oos_total_R |
|-------:|:--------------|:---------------------------------------------------------------------|----------:|----------:|--------:|--------------:|
|   2021 | down/vix15-20 | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2021 | down/vix<15   | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2021 | down/vix>=20  | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2021 | up/vix15-20   | 1m | gap>=0.15% | any | gap+exhaustion | break1 | 1R all             |        15 |      3.85 |      20 |          3.20 |
|   2021 | up/vix<15     | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2021 | up/vix>=20    | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2022 | down/vix15-20 | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2022 | down/vix<15   | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2022 | down/vix>=20  | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2022 | up/vix15-20   | 1m | gap>=0.50% | any | gap_only | break3 | 1R all                   |        23 |      3.86 |       6 |          3.87 |
|   2022 | up/vix<15     | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2022 | up/vix>=20    | 5m | gap>=0.50% | any | gap_only | break1 | 1R/2R half               |        23 |      1.49 |      11 |          3.98 |
|   2023 | down/vix15-20 | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2023 | down/vix<15   | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2023 | down/vix>=20  | 1m | gap>=0.15% | below_sma20 | gap+exhaustion | break1 | 1R all     |        27 |      1.70 |       3 |         -1.06 |
|   2023 | up/vix15-20   | 1m | gap>=0.50% | any | gap_only | break3 | 1R all                   |        29 |      4.39 |      10 |         -2.26 |
|   2023 | up/vix<15     | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2023 | up/vix>=20    | 5m | gap>=0.50% | any | gap_only | break1 | 1R/2R half               |        34 |      1.85 |       2 |         -2.03 |
|   2024 | down/vix15-20 | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2024 | down/vix<15   | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2024 | down/vix>=20  | 1m | gap>=0.50% | below_sma20 | gap+exhaustion | break1 | 1R all     |        22 |      1.70 |       0 |          0.00 |
|   2024 | up/vix15-20   | 1m | gap>=0.30% | below_sma20 | gap_only | break3 | 1R all           |        17 |      3.26 |       1 |          0.99 |
|   2024 | up/vix<15     | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2024 | up/vix>=20    | 5m | gap>=0.50% | any | gap_only | break1 | 1R/2R half               |        36 |      1.46 |       1 |          1.48 |
|   2025 | down/vix15-20 | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2025 | down/vix<15   | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2025 | down/vix>=20  | 1m | gap>=0.50% | below_sma20 | gap+exhaustion | break1 | 1R all     |        22 |      1.70 |       6 |         -0.13 |
|   2025 | up/vix15-20   | 1m | gap>=0.30% | below_sma20 | gap_only | break3 | 1R all           |        18 |      3.55 |       3 |         -1.07 |
|   2025 | up/vix<15     | 1m | gap>=0.30% | any | gap+exhaustion | break3 | 1R all             |        23 |      2.36 |       1 |         -1.03 |
|   2025 | up/vix>=20    | 5m | gap>=0.50% | any | gap_only | break1 | 1R/2R half               |        37 |      1.66 |       1 |         -1.02 |
|   2026 | down/vix15-20 | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2026 | down/vix<15   | (stand aside)                                                        |         0 |    nan    |       0 |          0.00 |
|   2026 | down/vix>=20  | 1m | gap>=0.50% | below_sma20 | gap+exhaustion | break1 | 1R/2R half |        28 |      1.57 |       6 |         -1.15 |
|   2026 | up/vix15-20   | 1m | gap>=0.30% | below_sma20 | gap_only | break3 | 1R/2R half       |        21 |      2.82 |       8 |         -5.20 |
|   2026 | up/vix<15     | 1m | gap>=0.30% | any | gap+exhaustion | break3 | 1R all             |        24 |      2.01 |       1 |         -1.03 |
|   2026 | up/vix>=20    | 5m | gap>=0.50% | any | gap_only | break1 | 1R/2R half               |        38 |      1.48 |       0 |          0.00 |
