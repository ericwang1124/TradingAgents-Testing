# Winning vs losing opening-reversal shorts

- **Candidates**: first rally-then-reversal short (09:35-10:30) on every session, 2019-01-01 to 2026-11-12: 1850 trades, 48.8% winners, avg -0.054R
- **Early / late periods** for the comparison: before / from 2023-01-01
- **Walk-forward** test years: 2021-2026 (1473 sessions); every rule is learned from earlier years only
- **Generated**: 2026-11-13 05:00

## Out-of-sample: trade only when the learned pattern says so

|                                            |   trades |   % of sessions |   win_% |   avg_R |   total_R |     t |
|:-------------------------------------------|---------:|----------------:|--------:|--------:|----------:|------:|
| take every candidate                       |  1382.00 |           93.82 |   48.63 |   -0.06 |    -79.92 | -2.03 |
| gap-down candidates only (>= 0.15%)        |   447.00 |           30.35 |   51.01 |   -0.00 |     -1.28 | -0.06 |
| walk-forward tree depth 1 (leaf >= 60)     |   485.00 |           32.93 |   45.36 |   -0.12 |    -55.96 | -2.42 |
| walk-forward tree depth 2 (leaf >= 40)     |   387.00 |           26.27 |   45.99 |   -0.14 |    -52.93 | -2.62 |
| walk-forward tree depth 3 (leaf >= 30)     |   607.00 |           41.21 |   47.45 |   -0.11 |    -63.77 | -2.51 |
| walk-forward stable-feature score, top 30% |   304.00 |           20.64 |   45.39 |   -0.13 |    -38.11 | -2.09 |
| walk-forward stable-feature score, top 15% |   146.00 |            9.91 |   45.21 |   -0.14 |    -19.83 | -1.58 |

Total R by year:

|    y |   every candidate |   tree depth 2 |   tree depth 2 trades |
|-----:|------------------:|---------------:|----------------------:|
| 2021 |            -38.96 |           1.42 |                  5.00 |
| 2022 |              1.01 |          -9.71 |                125.00 |
| 2023 |            -13.51 |          -4.62 |                  7.00 |
| 2024 |             18.26 |          -8.22 |                 65.00 |
| 2025 |            -15.62 |         -10.17 |                 25.00 |
| 2026 |            -31.11 |         -21.64 |                160.00 |

## Winners vs losers — features sorted by how consistently they relate to R

`corr_with_R` is the Spearman rank correlation between the feature and the trade's R. A feature only matters if the sign is the same in both periods and the size is not tiny.

| feature                | meaning                                                     |   corr_with_R_early |   corr_with_R_late |   winners_median_early |   losers_median_early |   winners_median_late |   losers_median_late |
|:-----------------------|:------------------------------------------------------------|--------------------:|-------------------:|-----------------------:|----------------------:|----------------------:|---------------------:|
| dist_sma20_pct         | prior close vs 20-day SMA, %                                |               -0.01 |              -0.01 |                   1.17 |                  1.06 |                  0.84 |                 0.97 |
| exhaustion_ratio       | late / early rally relative volume                          |                0.01 |               0.03 |                   1.11 |                  1.09 |                  1.08 |                 1.08 |
| weekday                | 0 = Monday                                                  |                0.04 |               0.00 |                   2.00 |                  2.00 |                  2.00 |                 2.00 |
| vwap_dist_pct          | entry vs session VWAP, %                                    |                0.00 |               0.03 |                   0.02 |                  0.02 |                  0.02 |                 0.02 |
| above_premarket_high   | rally high above pre-market high (0/1)                      |               -0.05 |              -0.00 |                   0.00 |                  0.00 |                  0.00 |                 0.00 |
| drop_pct               | open -> morning low, %                                      |                0.06 |              -0.03 |                   0.15 |                  0.12 |                  0.10 |                 0.11 |
| gap_atr                | gap in units of 14-day ATR                                  |               -0.06 |               0.03 |                   0.04 |                  0.08 |                  0.08 |                 0.07 |
| entry_minute           | minutes after 09:30 of the entry                            |               -0.02 |               0.02 |                  14.00 |                 15.00 |                 17.00 |                16.00 |
| rally_pct              | morning low -> rally high, %                                |                0.04 |              -0.04 |                   0.27 |                  0.27 |                  0.23 |                 0.23 |
| gap_pct                | open vs prior close, %                                      |               -0.04 |               0.02 |                   0.05 |                  0.09 |                  0.09 |                 0.09 |
| high_vs_prev_close_pct | rally high vs prior close, %                                |               -0.03 |               0.04 |                   0.19 |                  0.20 |                  0.19 |                 0.17 |
| high_vs_open_pct       | rally high vs open, %                                       |               -0.01 |               0.02 |                   0.14 |                  0.15 |                  0.13 |                 0.13 |
| retrace_of_drop        | rally size / opening drop (1 = back to the open)            |               -0.05 |               0.01 |                   1.91 |                  2.16 |                  2.34 |                 2.31 |
| rally_bars             | bars from low to rally high                                 |               -0.03 |               0.03 |                   6.00 |                  7.00 |                  8.00 |                 8.00 |
| signal_body_frac       | reversal bar body / range                                   |               -0.01 |               0.02 |                   0.65 |                  0.67 |                  0.65 |                 0.65 |
| relvol_session         | mean relative volume so far today                           |               -0.02 |               0.02 |                   1.04 |                  1.06 |                  1.09 |                 1.08 |
| relvol_signal          | relative volume of the reversal bar                         |               -0.03 |               0.01 |                   0.99 |                  1.00 |                  1.13 |                 1.10 |
| signal_range_pct       | reversal bar high-low, %                                    |                0.03 |              -0.04 |                   0.08 |                  0.08 |                  0.06 |                 0.07 |
| near_level_pct         | rally high distance to nearest prior-day/premarket level, % |                0.08 |              -0.01 |                   0.09 |                  0.08 |                  0.06 |                 0.07 |
| risk_atr               | stop distance in ATR units                                  |               -0.03 |               0.00 |                   0.10 |                  0.10 |                  0.11 |                 0.11 |
| risk_pct               | stop distance, %                                            |                0.04 |              -0.03 |                   0.14 |                  0.13 |                  0.12 |                 0.12 |
| vix_prev               | prior-day VIX close                                         |                0.03 |              -0.08 |                  21.60 |                 21.32 |                 16.61 |                17.04 |
| dist_sma50_pct         | prior close vs 50-day SMA, %                                |               -0.01 |               0.01 |                   2.33 |                  2.25 |                  2.05 |                 1.85 |
| ret_1d_pct             | prior day return, %                                         |                0.01 |              -0.02 |                   0.10 |                  0.05 |                  0.05 |                 0.08 |
| ret_5d_pct             | prior 5-day return, %                                       |                0.00 |              -0.00 |                   0.54 |                  0.55 |                  0.41 |                 0.36 |
| atr14_pct              | 14-day ATR, % of price                                      |                0.06 |              -0.06 |                   1.43 |                  1.35 |                  1.02 |                 1.09 |

## Features the stable-feature score picked each year (from earlier years only)

- **2021**: +drop_pct, +exhaustion_ratio, -relvol_session, -relvol_signal, +near_level_pct, +ret_1d_pct, +weekday
- **2022**: -gap_atr, +drop_pct, -retrace_of_drop, -relvol_signal, +near_level_pct
- **2023**: -gap_atr, +drop_pct, +near_level_pct
- **2024**: +drop_pct, +rally_pct, +near_level_pct
- **2025**: +near_level_pct
- **2026**: (none)

## Latest tree (trained on 2019..2025) — depth 2

```
|--- retrace_of_drop <= 7.73
|   |--- drop_pct <= 0.32
|   |   |--- value: [0.04]
|   |--- drop_pct >  0.32
|   |   |--- value: [-0.19]
|--- retrace_of_drop >  7.73
|   |--- gap_pct <= -0.06
|   |   |--- value: [0.00]
|   |--- gap_pct >  -0.06
|   |   |--- value: [-0.33]

```
