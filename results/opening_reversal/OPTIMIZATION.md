# Opening reversal short — walk-forward optimisation

- **Symbol**: SPY
- **Data**: Alpaca SIP 1-minute bars (split+dividend adjusted), optionally aggregated to 5 minutes
- **Train**: 2019-01-01 to 2022-12-31 (1008 sessions)
- **Test**: 2023-01-01 to 2026-11-12 (970 sessions)
- **Generated**: 2026-11-13 03:28
- **Grid size**: 192 combinations; ranked by training t-stat among those with >= 30 training trades (100 qualify)

## Does training performance predict test performance?

- Spearman rank correlation of avg R, train vs test (combos with >= 20 trades in both): **-0.42**
- Combos with positive avg R — train: 109, test: 66 of 192
- Combos positive in **both** periods: 22

## Selected on training data (top 1) — the honest out-of-sample estimate

|   bar_minutes | min_gap_pct   | regime      | conditions     |   break_lookback | exit   |   train_n |   train_win% |   train_avgR |   train_t |   test_n |   test_win% |   test_avgR |   test_totR |   test_PF |   test_t |
|--------------:|:--------------|:------------|:---------------|-----------------:|:-------|----------:|-------------:|-------------:|----------:|---------:|------------:|------------:|------------:|----------:|---------:|
|             1 | 0.30%         | below_sma20 | gap+exhaustion |                1 | 1R all |        39 |       79.487 |        0.567 |     4.334 |       42 |      35.714 |      -0.314 |     -13.171 |     0.525 |   -2.096 |

## Top 10 by training t-stat

|   bar_minutes | min_gap_pct   | regime      | conditions     |   break_lookback | exit       |   train_n |   train_win% |   train_avgR |   train_t |   test_n |   test_win% |   test_avgR |   test_totR |   test_PF |   test_t |
|--------------:|:--------------|:------------|:---------------|-----------------:|:-----------|----------:|-------------:|-------------:|----------:|---------:|------------:|------------:|------------:|----------:|---------:|
|             1 | 0.30%         | below_sma20 | gap+exhaustion |                1 | 1R all     |        39 |       79.487 |        0.567 |     4.334 |       42 |      35.714 |      -0.314 |     -13.171 |     0.525 |   -2.096 |
|             1 | 0.15%         | below_sma20 | gap+exhaustion |                1 | 1R all     |        48 |       77.083 |        0.518 |     4.225 |       51 |      33.333 |      -0.361 |     -18.424 |     0.473 |   -2.711 |
|             1 | 0.30%         | below_sma20 | gap+exhaustion |                1 | 1R/2R half |        39 |       79.487 |        0.620 |     4.060 |       42 |      35.714 |      -0.230 |      -9.671 |     0.651 |   -1.339 |
|             1 | 0.15%         | below_sma20 | gap+exhaustion |                1 | 1R/2R half |        48 |       77.083 |        0.540 |     3.869 |       51 |      33.333 |      -0.293 |     -14.928 |     0.573 |   -1.932 |
|             1 | 0.50%         | below_sma20 | gap+exhaustion |                1 | 1R all     |        33 |       78.788 |        0.553 |     3.834 |       32 |      40.625 |      -0.215 |      -6.887 |     0.647 |   -1.219 |
|             1 | 0.50%         | below_sma20 | gap+exhaustion |                1 | 1R/2R half |        33 |       78.788 |        0.601 |     3.587 |       32 |      40.625 |      -0.137 |      -4.387 |     0.775 |   -0.684 |
|             1 | 0.30%         | below_sma20 | gap+exhaustion |                3 | 1R all     |        30 |       76.667 |        0.514 |     3.279 |       32 |      50.000 |      -0.023 |      -0.729 |     0.955 |   -0.127 |
|             1 | 0.30%         | below_sma20 | gap+exhaustion |                3 | 1R/2R half |        30 |       76.667 |        0.484 |     2.802 |       32 |      50.000 |      -0.054 |      -1.729 |     0.894 |   -0.292 |
|             1 | 0.15%         | below_sma20 | gap+exhaustion |                3 | 1R all     |        37 |       67.568 |        0.333 |     2.137 |       38 |      44.737 |      -0.128 |      -4.879 |     0.773 |   -0.786 |
|             1 | 0.15%         | below_sma20 | gap+exhaustion |                3 | 1R/2R half |        37 |       67.568 |        0.308 |     1.848 |       38 |      44.737 |      -0.142 |      -5.379 |     0.749 |   -0.833 |

## Original rules for reference

|   bar_minutes | min_gap_pct   | regime   | conditions   |   break_lookback | exit       |   train_n |   train_win% |   train_avgR |   train_t |   test_n |   test_win% |   test_avgR |   test_totR |   test_PF |   test_t |
|--------------:|:--------------|:---------|:-------------|-----------------:|:-----------|----------:|-------------:|-------------:|----------:|---------:|------------:|------------:|------------:|----------:|---------:|
|             1 | 0.15%         | any      | full         |                1 | 1R/2R half |        53 |       45.283 |       -0.163 |    -1.175 |       39 |      51.282 |      -0.115 |      -4.493 |     0.763 |   -0.769 |

## Marginal effect of each knob (mean of test avg R across all other settings)

**bar_minutes**

|   bar_minutes |   train_avgR |   test_avgR |   test_n |
|--------------:|-------------:|------------:|---------:|
|         1.000 |       -0.002 |      -0.044 |   63.583 |
|         5.000 |        0.172 |       0.004 |   21.958 |

**min_gap_pct**

| min_gap_pct   |   train_avgR |   test_avgR |   test_n |
|:--------------|-------------:|------------:|---------:|
| 0.15%         |        0.050 |      -0.093 |   59.375 |
| 0.30%         |        0.088 |      -0.025 |   42.938 |
| 0.50%         |        0.117 |       0.056 |   26.000 |

**regime**

| regime      |   train_avgR |   test_avgR |   test_n |
|:------------|-------------:|------------:|---------:|
| any         |        0.030 |      -0.081 |   61.417 |
| below_sma20 |        0.140 |       0.041 |   24.125 |

**conditions**

| conditions     |   train_avgR |   test_avgR |   test_n |
|:---------------|-------------:|------------:|---------:|
| full           |        0.144 |       0.283 |    9.083 |
| gap+exhaustion |        0.350 |      -0.297 |   34.000 |
| gap+zone       |       -0.270 |       0.054 |   41.500 |
| gap_only       |        0.116 |      -0.074 |   86.500 |

**break_lookback**

|   break_lookback |   train_avgR |   test_avgR |   test_n |
|-----------------:|-------------:|------------:|---------:|
|            1.000 |       -0.017 |       0.035 |   50.083 |
|            3.000 |        0.188 |      -0.083 |   35.458 |

**exit**

| exit       |   train_avgR |   test_avgR |   test_n |
|:-----------|-------------:|------------:|---------:|
| 1R all     |        0.092 |      -0.013 |   42.771 |
| 1R/2R half |        0.078 |      -0.030 |   42.771 |
