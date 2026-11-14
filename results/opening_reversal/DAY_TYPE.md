# Day-type regimes decided at 10:00 (pre-market + first 30 minutes)

Sessions: 1956 (2019-01-02 to 2026-11-12). Returns are 1x SPY, costs included; continuation = trade the 09:30-10:00 direction at 10:00.

## Hold from 10:00 to noon

|                                           |   Sharpe OOS 2021-26 |   Sharpe 2021-23 |   Sharpe 2024-26 |   Sharpe 2024-05+ |   ann_ret_% (1x) |   max_dd_% |   days traded % |
|:------------------------------------------|---------------------:|-----------------:|-----------------:|------------------:|-----------------:|-----------:|----------------:|
| always continuation                       |                 0.22 |             0.33 |             0.09 |              0.01 |             1.40 |     -14.91 |          100.00 |
| always reversal                           |                -0.35 |            -0.47 |            -0.21 |             -0.11 |            -2.86 |     -22.43 |          100.00 |
| Dalton rule (fixed)                       |                 0.21 |             0.05 |             0.39 |              0.58 |             1.01 |     -13.85 |           61.19 |
| walk-forward cells: efficiency x OR width |                -0.31 |            -0.45 |            -0.14 |             -0.10 |            -2.22 |     -19.30 |           73.65 |
| walk-forward tree depth 2                 |                -0.15 |             0.01 |            -0.36 |             -0.45 |            -1.40 |     -18.95 |          100.00 |
| walk-forward ridge, top-half confidence   |                 0.33 |             0.84 |            -0.32 |             -0.39 |             1.70 |     -10.26 |           47.09 |

## Hold from 10:00 to close

|                                           |   Sharpe OOS 2021-26 |   Sharpe 2021-23 |   Sharpe 2024-26 |   Sharpe 2024-05+ |   ann_ret_% (1x) |   max_dd_% |   days traded % |
|:------------------------------------------|---------------------:|-----------------:|-----------------:|------------------:|-----------------:|-----------:|----------------:|
| always continuation                       |                 0.23 |             0.01 |             0.51 |              0.49 |             2.18 |     -28.72 |          100.00 |
| always reversal                           |                -0.31 |            -0.09 |            -0.58 |             -0.56 |            -4.59 |     -35.24 |          100.00 |
| Dalton rule (fixed)                       |                 0.18 |             0.05 |             0.36 |              0.50 |             1.25 |     -19.79 |           61.19 |
| walk-forward cells: efficiency x OR width |                -0.25 |            -0.10 |            -0.43 |             -0.33 |            -3.62 |     -52.38 |           84.05 |
| walk-forward tree depth 2                 |                -0.33 |            -0.46 |            -0.17 |             -0.11 |            -4.85 |     -32.30 |          100.00 |
| walk-forward ridge, top-half confidence   |                 0.13 |             0.15 |             0.11 |             -0.08 |             0.78 |     -25.55 |           49.69 |

## Descriptive: continuation-to-noon Sharpe by efficiency x opening-range width

|                           |   2019-22 |   2023-26 |
|:--------------------------|----------:|----------:|
| ('low eff', 'narrow OR')  |      0.02 |      0.44 |
| ('low eff', 'mid OR')     |      0.42 |     -0.08 |
| ('low eff', 'wide OR')    |      1.87 |     -1.74 |
| ('mid eff', 'narrow OR')  |     -1.01 |     -0.43 |
| ('mid eff', 'mid OR')     |      1.67 |     -0.72 |
| ('mid eff', 'wide OR')    |     -0.48 |      0.42 |
| ('high eff', 'narrow OR') |      1.72 |      1.91 |
| ('high eff', 'mid OR')    |      1.32 |      0.93 |
| ('high eff', 'wide OR')   |      0.63 |      0.59 |
