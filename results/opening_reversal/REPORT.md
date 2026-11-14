# SPY opening-hour gap-down reversal short — phase 1 backtest

- **Symbol**: SPY
- **Data**: Alpaca SIP 1-minute bars (split+dividend adjusted)
- **Period**: 2019-01-02 to 2026-11-12
- **Gap-down sessions**: 587 (open <= -0.15% vs prior close)
- **Generated**: 2026-11-13 03:28
- **Sessions evaluated**: 1978

Results are measured on the SPY underlying in R (multiples of the initial stop distance).
They are **not** 0DTE option P&L; option pricing is phase 3.

## Variant comparison

|                            |   trades |   trade_freq_% |   win_rate_% |   avg_R |   median_R |   total_R |   profit_factor |   max_dd_R |   avg_win_R |   avg_loss_R |   stopped_% |   avg_risk_% |   avg_minutes |   t_stat |
|:---------------------------|---------:|---------------:|-------------:|--------:|-----------:|----------:|----------------:|-----------:|------------:|-------------:|------------:|-------------:|--------------:|---------:|
| gap_only                   |   572.00 |          28.92 |        49.65 |   -0.03 |      -1.01 |    -16.24 |            0.95 |     -26.38 |        0.99 |        -1.03 |       50.35 |         0.16 |         13.42 |    -0.63 |
| gap+exhaustion             |   285.00 |          14.41 |        48.77 |   -0.08 |      -1.01 |    -22.39 |            0.85 |     -38.71 |        0.93 |        -1.03 |       51.23 |         0.14 |         12.59 |    -1.27 |
| gap+zone                   |   286.00 |          14.46 |        44.76 |   -0.12 |      -1.01 |    -34.16 |            0.78 |     -36.58 |        0.96 |        -1.00 |       53.15 |         0.21 |         34.80 |    -1.95 |
| full (gap+exhaustion+zone) |    92.00 |           4.65 |        47.83 |   -0.14 |      -1.01 |    -13.14 |            0.73 |     -15.51 |        0.81 |        -1.01 |       51.09 |         0.19 |         35.30 |    -1.41 |
| control: no gap-down       |   123.00 |           6.22 |        39.84 |   -0.22 |      -1.02 |    -26.79 |            0.63 |     -30.37 |        0.94 |        -0.99 |       55.28 |         0.18 |         41.91 |    -2.41 |

![equity](equity_curves.png)

## Full strategy by year

|   year |   trades |   win_rate_% |   avg_R |   total_R |
|-------:|---------:|-------------:|--------:|----------:|
|   2019 |    11.00 |        45.45 |   -0.01 |     -0.11 |
|   2020 |    16.00 |        50.00 |   -0.17 |     -2.79 |
|   2021 |    14.00 |        50.00 |   -0.11 |     -1.54 |
|   2022 |    12.00 |        33.33 |   -0.35 |     -4.22 |
|   2023 |     9.00 |        44.44 |   -0.13 |     -1.21 |
|   2024 |     8.00 |        37.50 |   -0.52 |     -4.14 |
|   2025 |    12.00 |        58.33 |    0.06 |      0.68 |
|   2026 |    10.00 |        60.00 |    0.02 |      0.18 |

## Full strategy by rejection zone

| zone           |   trades |   avg_R |   total_R |
|:---------------|---------:|--------:|----------:|
| premarket_high |    15.00 |   -0.28 |     -4.18 |
| prev_close     |    16.00 |   -0.30 |     -4.82 |
| prev_high      |     1.00 |   -1.02 |     -1.02 |
| prev_low       |    18.00 |    0.19 |      3.43 |
| prev_poc       |    15.00 |   -0.02 |     -0.35 |
| prev_vah       |     6.00 |   -0.59 |     -3.54 |
| prev_val       |    21.00 |   -0.13 |     -2.66 |

## Exit reasons (full strategy)

| exit_reason      |   trades |
|:-----------------|---------:|
| stop             |       47 |
| target/breakeven |       25 |
| target/target    |       14 |
| target/time      |        3 |
| time             |        3 |

## Parameters (full strategy)

```
require_gap_down = True
require_exhaustion = True
require_zone = True
gap_filter = any
min_gap_pct = 0.0015
max_gap_pct = 0.02
regime = any
min_rally_pct = 0.0015
max_bars_since_high = 5
break_lookback = 1
volume_lookback_days = 20
exhaustion_window = 3
max_exhaustion_ratio = 0.8
zone_sources = ('prev_close', 'prev_low', 'prev_val', 'prev_poc', 'prev_vah', 'prev_high', 'premarket_high')
zone_half_width_pct = 0.0005
profile_bin_pct = 0.0005
value_area_share = 0.7
entry_start = 09:35:00
entry_end = 10:30:00
stop_buffer_pct = 0.0003
max_risk_pct = 0.006
min_risk_pct = 0.0005
take_profits = ((1.0, 0.5), (2.0, 0.5))
move_stop_to_breakeven = True
time_exit = 12:00:00
slippage_pct = 2e-05
```
