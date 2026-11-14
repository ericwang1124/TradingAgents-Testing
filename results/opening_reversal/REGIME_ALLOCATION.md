# Regime-based strategy selection (walk-forward)

Out-of-sample years: 2021-2026. Static rows are the raw streams over the same days.

|                                    |   Sharpe |   ann_ret_% |   max_dd_% |   Sharpe 2024-05+ |   days_in_market_% |
|:-----------------------------------|---------:|------------:|-----------:|------------------:|-------------------:|
| static: morning_momentum           |     0.53 |        2.11 |      -5.93 |              0.41 |              36.76 |
| static: morning_momentum_voltarget |     0.53 |        4.48 |     -12.66 |              0.43 |              36.76 |
| static: fullday_momentum           |     1.12 |        7.27 |      -9.86 |              0.04 |              61.74 |
| static: fade                       |     0.22 |        0.76 |      -8.43 |             -0.67 |              23.41 |
| regime A: all three                |     0.20 |        1.82 |     -34.72 |             -0.80 |              44.90 |
| regime A: momentum only            |     0.46 |        5.62 |     -19.84 |             -0.22 |              48.19 |
| regime A: morning momentum gated   |     0.34 |        3.69 |     -19.57 |              0.24 |              29.98 |
| regime A: fade gated               |    -0.04 |       -1.08 |     -21.86 |             -0.64 |              11.36 |
| regime B: all three                |     0.73 |        9.26 |     -22.29 |             -0.10 |              56.74 |
| regime B: momentum only            |     0.73 |        9.26 |     -22.29 |             -0.10 |              56.74 |
| regime B: morning momentum gated   |     0.40 |        4.63 |     -22.61 |              0.38 |              35.46 |
| regime B: fade gated               |    -0.09 |       -1.59 |     -30.42 |             -0.78 |              11.23 |

## Sharpe of each stream by regime A (whole sample, descriptive)

| regime        |   ('morning_momentum', '2019-22') |   ('morning_momentum', '2023-26') |   ('fullday_momentum', '2019-22') |   ('fullday_momentum', '2023-26') |   ('fade', '2019-22') |   ('fade', '2023-26') |
|:--------------|----------------------------------:|----------------------------------:|----------------------------------:|----------------------------------:|----------------------:|----------------------:|
| down/vix15-20 |                              2.34 |                              0.59 |                              2.32 |                              0.01 |                 -2.99 |                 -2.25 |
| down/vix<15   |                            nan    |                              6.95 |                            nan    |                              8.68 |                nan    |                  5.02 |
| down/vix>=20  |                              0.87 |                             -0.37 |                              0.90 |                              0.42 |                  0.22 |                  0.28 |
| up/vix15-20   |                              1.73 |                              0.74 |                              0.81 |                              0.64 |                  1.17 |                 -0.58 |
| up/vix<15     |                              0.37 |                              0.63 |                             -0.15 |                              1.66 |                 -2.10 |                  1.14 |
| up/vix>=20    |                              0.29 |                             -0.37 |                              1.71 |                             -0.41 |                 -0.22 |                 -1.44 |

Sessions per regime:

| regime        |   2019-22 |   2023-26 |
|:--------------|----------:|----------:|
| down/vix15-20 |        43 |        98 |
| down/vix<15   |         2 |        10 |
| down/vix>=20  |       242 |       119 |
| up/vix15-20   |       255 |       421 |
| up/vix<15     |       149 |       259 |
| up/vix>=20    |       304 |        54 |

## Sharpe of each stream by regime B (whole sample, descriptive)

| regime             |   ('morning_momentum', '2019-22') |   ('morning_momentum', '2023-26') |   ('fullday_momentum', '2019-22') |   ('fullday_momentum', '2023-26') |   ('fade', '2019-22') |   ('fade', '2023-26') |
|:-------------------|----------------------------------:|----------------------------------:|----------------------------------:|----------------------------------:|----------------------:|----------------------:|
| down/backwardation |                              1.14 |                              0.77 |                             -0.33 |                              1.81 |                  0.47 |                 -0.14 |
| down/contango      |                              0.84 |                             -0.28 |                              1.91 |                             -0.26 |                 -0.50 |                 -0.56 |
| up/backwardation   |                              6.67 |                              5.62 |                             -8.88 |                             -2.88 |                 -5.53 |                 -0.17 |
| up/contango        |                              0.56 |                              0.59 |                              1.29 |                              0.85 |                  0.03 |                 -0.06 |

Sessions per regime:

| regime             |   2019-22 |   2023-26 |
|:-------------------|----------:|----------:|
| down/backwardation |        71 |        45 |
| down/contango      |       216 |       182 |
| up/backwardation   |         9 |         6 |
| up/contango        |       699 |       728 |

## Assignments, regime A: all three

|                         | choice           |   past_sharpe |   days_this_year |
|:------------------------|:-----------------|--------------:|-----------------:|
| (2021, 'down/vix15-20') | cash             |       -inf    |                4 |
| (2021, 'down/vix<15')   | cash             |       -inf    |                0 |
| (2021, 'down/vix>=20')  | morning_momentum |          1.42 |               15 |
| (2021, 'up/vix15-20')   | morning_momentum |          3.80 |              153 |
| (2021, 'up/vix<15')     | morning_momentum |          0.37 |                0 |
| (2021, 'up/vix>=20')    | fullday_momentum |          0.92 |               78 |
| (2022, 'down/vix15-20') | cash             |       -inf    |                2 |
| (2022, 'down/vix<15')   | cash             |       -inf    |                0 |
| (2022, 'down/vix>=20')  | morning_momentum |          2.13 |              158 |
| (2022, 'up/vix15-20')   | morning_momentum |          1.88 |               22 |
| (2022, 'up/vix<15')     | morning_momentum |          0.37 |                0 |
| (2022, 'up/vix>=20')    | fullday_momentum |          1.35 |               68 |
| (2023, 'down/vix15-20') | cash             |       -inf    |               38 |
| (2023, 'down/vix<15')   | cash             |       -inf    |                8 |
| (2023, 'down/vix>=20')  | fullday_momentum |          0.90 |               29 |
| (2023, 'up/vix15-20')   | morning_momentum |          1.73 |               77 |
| (2023, 'up/vix<15')     | morning_momentum |          0.37 |               81 |
| (2023, 'up/vix>=20')    | fullday_momentum |          1.71 |               14 |
| (2024, 'down/vix15-20') | fullday_momentum |          2.66 |               18 |
| (2024, 'down/vix<15')   | cash             |       -inf    |                2 |
| (2024, 'down/vix>=20')  | fullday_momentum |          0.92 |               10 |
| (2024, 'up/vix15-20')   | morning_momentum |          1.66 |               66 |
| (2024, 'up/vix<15')     | fullday_momentum |          0.73 |              138 |
| (2024, 'up/vix>=20')    | fullday_momentum |          1.71 |               15 |
| (2025, 'down/vix15-20') | morning_momentum |          1.63 |               21 |
| (2025, 'down/vix<15')   | cash             |       -inf    |                0 |
| (2025, 'down/vix>=20')  | morning_momentum |          0.95 |               42 |
| (2025, 'up/vix15-20')   | fade             |          1.14 |              142 |
| (2025, 'up/vix<15')     | fullday_momentum |          1.20 |               21 |
| (2025, 'up/vix>=20')    | fullday_momentum |          1.67 |               21 |
| (2026, 'down/vix15-20') | morning_momentum |          1.26 |               21 |
| (2026, 'down/vix<15')   | cash             |       -inf    |                0 |
| (2026, 'down/vix>=20')  | fullday_momentum |          0.88 |               38 |
| (2026, 'up/vix15-20')   | fullday_momentum |          0.91 |              136 |
| (2026, 'up/vix<15')     | fullday_momentum |          1.27 |               19 |
| (2026, 'up/vix>=20')    | fullday_momentum |          1.42 |                4 |

## Assignments, regime B: all three

|                              | choice           |   past_sharpe |   days_this_year |
|:-----------------------------|:-----------------|--------------:|-----------------:|
| (2021, 'down/backwardation') | cash             |       -inf    |                1 |
| (2021, 'down/contango')      | cash             |       -inf    |               18 |
| (2021, 'up/backwardation')   | cash             |       -inf    |                1 |
| (2021, 'up/contango')        | fullday_momentum |          0.69 |              230 |
| (2022, 'down/backwardation') | cash             |       -inf    |               15 |
| (2022, 'down/contango')      | morning_momentum |          4.28 |              145 |
| (2022, 'up/backwardation')   | cash             |       -inf    |                0 |
| (2022, 'up/contango')        | fullday_momentum |          1.03 |               90 |
| (2023, 'down/backwardation') | morning_momentum |          1.14 |                0 |
| (2023, 'down/contango')      | fullday_momentum |          1.91 |               75 |
| (2023, 'up/backwardation')   | cash             |       -inf    |                0 |
| (2023, 'up/contango')        | fullday_momentum |          1.29 |              172 |
| (2024, 'down/backwardation') | morning_momentum |          1.14 |                5 |
| (2024, 'down/contango')      | fullday_momentum |          2.02 |               25 |
| (2024, 'up/backwardation')   | cash             |       -inf    |                4 |
| (2024, 'up/contango')        | fullday_momentum |          1.43 |              215 |
| (2025, 'down/backwardation') | morning_momentum |          1.19 |               28 |
| (2025, 'down/contango')      | fullday_momentum |          1.74 |               35 |
| (2025, 'up/backwardation')   | cash             |       -inf    |                1 |
| (2025, 'up/contango')        | fullday_momentum |          1.41 |              183 |
| (2026, 'down/backwardation') | morning_momentum |          1.14 |               12 |
| (2026, 'down/contango')      | fullday_momentum |          1.48 |               47 |
| (2026, 'up/backwardation')   | cash             |       -inf    |                1 |
| (2026, 'up/contango')        | fullday_momentum |          1.23 |              158 |
