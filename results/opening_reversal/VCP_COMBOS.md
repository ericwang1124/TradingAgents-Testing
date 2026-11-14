# Combinations of score items: exhaustive search, two-fold validation

```
Which combination of score items works? Exhaustive search with two-fold validation.

    python -m tradingagents.strategies.vcp.combos

Fifteen ingredients: the twelve score items of vcp.leaders and three market states on the day before
the breakout (environment E >= 3, reversal window, at least half of recent breakouts held). Written
and committed before it was run.

1. Outcome of an event: the R multiple (profit / initial risk) of the trade it produces under the
   two confirmed entries, simulated with tiny positions and no risk reductions so that every eligible
   event trades and no trade depends on another. Events that never trigger a trade have no outcome.
2. A combination is any non-empty subset of the fifteen (32,767 of them). Its score is the sum of its
   items; it picks the events at or above the 75th percentile of the training period's events.
3. Two folds: train 2017-2021 / test 2022-2026, and the reverse. Within a fold, combinations with at
   least 40 traded picks in training are ranked by the t-statistic of their mean R in training.
4. What is reported, per fold:
   - the best combination in training and what it did in the test period;
   - the test-period mean R of the top 1% by training rank, against all combinations - if searching
     for combinations is worth anything, the top 1% must beat the typical combination out of sample;
   - the rank correlation between training and test t-statistics across all combinations;
   - how often each ingredient appears in the top 1%.
5. Consensus: ingredients present in at least half of the top 1% in both folds. It is run through
   the full portfolio simulator, as are the two fold winners on their test periods. The consensus
   uses both periods, so its backtest is in-sample; only the fold winners' test runs are out of sample.

Caveat: both periods have been looked at before (see vcp.jlaw_flex and vcp.leaders). The search itself
is mechanical and each fold's selection uses its training period only.
```

Events: 1085; with a trade outcome: 628 (312 in 2017-21, 316 in 2022-26). Mean R of all traded events: +0.06 / -0.04. Combinations: 32,767.

### Train 2017-21, test 2022-26

- Combinations with at least 40 traded picks in training: 32,767.
- Best in training: **count + first + dry + strength + guidance + mkt: environment** - training 72 trades, +0.76R (t = 2.54); test 58 trades, **+0.08R (t = 0.33)**, better than 36% of all combinations in the test period.
- Top 1% in training (327 combinations, 6.2 ingredients on average): test mean +0.20R, average t 0.94, 90% positive; better than 64% of all combinations.
- All combinations in the test period: median +0.14R (middle half +0.03R to +0.26R).
- Rank correlation between training and test t-statistics: +0.24.

### Train 2022-26, test 2017-21

- Combinations with at least 40 traded picks in training: 32,767.
- Best in training: **count + tight + dry + catalyst + analysts + trendline + mkt: reversal** - training 93 trades, +0.69R (t = 3.23); test 76 trades, **-0.02R (t = -0.09)**, better than 44% of all combinations in the test period.
- Top 1% in training (327 combinations, 7.2 ingredients on average): test mean +0.12R, average t 0.48, 78% positive; better than 70% of all combinations.
- All combinations in the test period: median +0.01R (middle half -0.13R to +0.15R).
- Rank correlation between training and test t-statistics: +0.24.

### How often each ingredient is in the top 1% (share of those combinations)

|                        |   train 2017-21 |   train 2022-26 |
|:-----------------------|----------------:|----------------:|
| count                  |            0.83 |            0.88 |
| tight                  |            0.64 |            0.81 |
| first                  |            0.92 |            0.27 |
| dry                    |            0.54 |            0.83 |
| level                  |            0.46 |            0.6  |
| catalyst               |            0.2  |            0.67 |
| strength               |            0.69 |            0.57 |
| earnings               |            0.12 |            0.34 |
| guidance               |            0.56 |            0.06 |
| analysts               |            0.11 |            0.35 |
| group                  |            0.17 |            0.05 |
| trendline              |            0.07 |            0.72 |
| mkt: environment       |            0.56 |            0.06 |
| mkt: reversal          |            0.21 |            0.6  |
| mkt: breakouts holding |            0.06 |            0.43 |

Consensus (at least half of the top 1% in both folds): **count + tight + dry + strength**

### Each ingredient alone (picks = events at or above its own 75th percentile; in-sample for each period)

|                        |   2017-21 mean R |   2017-21 n |   2022-26 mean R |   2022-26 n |
|:-----------------------|-----------------:|------------:|-----------------:|------------:|
| count                  |             0.06 |         312 |            -0.04 |         316 |
| tight                  |             0.12 |         175 |             0.05 |         175 |
| first                  |             0.41 |          79 |            -0.1  |          92 |
| dry                    |             0.33 |          82 |             0.43 |          86 |
| level                  |             0.04 |         185 |            -0.02 |         179 |
| catalyst               |             0.02 |          84 |             0.21 |          84 |
| strength               |             0.4  |          64 |             0.15 |          61 |
| earnings               |             0.03 |         140 |            -0.03 |         173 |
| guidance               |             0.22 |          89 |            -0.05 |          92 |
| analysts               |            -0.13 |          82 |             0.02 |         125 |
| group                  |            -0.15 |          74 |            -0.25 |          79 |
| trendline              |             0.06 |         312 |            -0.04 |         316 |
| mkt: environment       |             0.06 |         264 |            -0.15 |         216 |
| mkt: reversal          |             0.06 |         312 |             0.03 |          91 |
| mkt: breakouts holding |            -0.1  |         251 |            -0.03 |         234 |

### Reference scores, event level

|                                           |   2017-21: trades |   2017-21: mean R |   2017-21: t |   2022-26: trades (cutoff from 2017-21) |   2022-26: mean R |   2022-26: t |
|:------------------------------------------|------------------:|------------------:|-------------:|----------------------------------------:|------------------:|-------------:|
| 7 pattern items                           |                84 |              0.53 |         2.05 |                                      79 |              0.4  |         1.78 |
| all 12 items                              |                77 |              0.03 |         0.17 |                                      91 |              0.31 |         1.47 |
| consensus: count + tight + dry + strength |                94 |              0.42 |         1.8  |                                      90 |              0.37 |         1.95 |

### Full portfolio simulator (0.35% risk per trade, the usual limits)

|                                                                                                                     |   Sharpe |   ann % |   maxDD % |   invested % |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |   t(avg R) |   alpha t vs SPY |
|:--------------------------------------------------------------------------------------------------------------------|---------:|--------:|----------:|-------------:|---------:|--------:|------------:|-------------:|--------:|-----------:|-----------:|-----------------:|
| fold winner, trained 2017-21, run on 2022-26: count + first + dry + strength + guidance + mkt: environment          |    -0.17 |   -0.25 |     -3.55 |         2.75 |       59 |   35.59 |       10.98 |        -5.37 |    0.08 |      16.68 |       0.32 |            -0.69 |
| fold winner, trained 2022-26, run on 2017-21: count + tight + dry + catalyst + analysts + trendline + mkt: reversal |    -0.17 |   -0.33 |     -4.62 |         4.03 |       79 |   24.05 |       14.87 |        -4.65 |   -0.04 |      16.9  |      -0.16 |            -0.84 |
| consensus, 2017-21 (in-sample)                                                                                      |     0.82 |    2.8  |     -3.48 |         8.31 |       99 |   39.39 |       15.2  |        -4.97 |    0.5  |      20.22 |       2.13 |             1.38 |
| consensus, 2022-26 (in-sample)                                                                                      |     0.61 |    1.42 |     -2.41 |         5.64 |       93 |   47.31 |       10.42 |        -5.36 |    0.37 |      18.56 |       1.98 |             1.08 |
| consensus, whole period (in-sample)                                                                                 |     0.73 |    2.12 |     -4.14 |         6.97 |      192 |   43.23 |       12.66 |        -5.14 |    0.43 |      19.42 |       2.9  |             1.76 |
| 7 pattern items, whole period                                                                                       |     0.63 |    1.68 |     -5.59 |         5.92 |      167 |   42.51 |       13.67 |        -5.33 |    0.44 |      20.05 |       2.63 |             1.49 |

