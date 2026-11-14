# J Law's VCP, flexible version

```
J Law's VCP, flexible version: scored setups and confirmed entries, tuned on 2017-21, tested once on 2022-26.

    python -m tradingagents.strategies.vcp.jlaw_flex             # development period only
    python -m tradingagents.strategies.vcp.jlaw_flex --holdout   # once the development choice is frozen

Why. The fixed-rule version (vcp.jlaw) has the average win and loss J Law reports (+11.5% / -4.1%) but a
30% win rate against his 45-50%. Three places where those rules were more rigid than his description:
they accept any two contractions (he speaks of three or four), they buy the first touch of the pivot
zone without waiting for the price to turn, and they treat every rule as pass/fail although he weighs
them. This version changes those three things and nothing else. Written and committed before any run.

1. Pattern. The hard limits become sanity bounds and a quality score ranks what is left.
   Bounds: at least 2 contractions, counted from the first one no deeper than 50%; that first one at
   least 8%; the last one at most 15%; base at least 15 sessions; pivot at least 3 sessions old; last
   low before today; nothing in the 250-session window deeper than 60%.
   Score, one point each, 0 to 7:
     count     3 or 4 contractions
     tight     last contraction: 1 at 6% or less, 0 at 12% or more, linear in between
     first     first contraction between 20% and 35%
     dry       volume during the last decline / 50-day average: 1 at 0.6 or less, 0 at 1.0 or more, linear
     level     earlier highs of the base within 3% above the pivot (a flat top, i.e. horizontal
               resistance): two or more = 1, one = 0.5
     catalyst  in the past 60 sessions, a day up 8% or more on at least twice its average volume
               (a price-and-volume stand-in for an earnings beat or raised guidance)
     strength  1-year return percentile: 0 at 80, 1 at 100, linear
   Traded: setups whose score is at or above the 75th percentile of all bounded setup-days of the
   development period. The cutoff comes from the score distribution, not from returns.
2. Entries, both confirmed.
   close breakout: bought at the close of a day that closes above the pivot, no more than 5% above
     it, on volume above both the prior day's and the 50-day average. Stop 1% below the last contraction low.
   confirmed pullback: after such a breakout, a quiet day back in the pivot zone with SMA10 or SMA20
     nearby (the original pullback conditions) only arms a buy-stop at that day's high. Bought when
     one of the next 3 sessions trades above it (not when it opens more than 2% above). Stop 1% below
     the lowest of the pivot, that day's low and the supporting averages.
3. Everything else is unchanged from vcp.jlaw: screen, 3-8% stops, 0.35% of equity at risk per trade,
   the two risk reductions, breakeven after +10%, SMA20 trail, SMA50 backstop, 5 bp costs.

Protocol.
  Development, 2017-01 to 2021-12. Four candidates on the scored setups:
    A touch pullback (the original entry)      B confirmed pullback
    C close breakout                           D close breakout + confirmed pullback
  The one with the highest development Sharpe among those with at least 50 trades is frozen.
  Holdout, 2022-01 to 2026-11. The frozen candidate is run once and that is the result. The other
  candidates' holdout numbers are printed for information only.

Caveat. The fixed version's whole-period results were seen before this was written, including that
three-contraction setups beat two-contraction ones in both halves. The "count" item is therefore not
a clean test on the holdout. The other six items, both entries and the cutoff rule had not been run.
```

Bounded setup-days in the development period: 10,331; score cutoff (75th percentile): 3.27; setup-days at or above it: 2,583.

Average score items of bounded setups (development):

|      |   count |   tight |   first |   dry |   level |   catalyst |   strength |   total |
|:-----|--------:|--------:|--------:|------:|--------:|-----------:|-----------:|--------:|
| mean |    0.12 |     0.7 |    0.28 |  0.43 |    0.29 |        0.3 |       0.47 |    2.59 |

## Development 2017-2021

|                                       |   Sharpe |   ann % |   maxDD % |   invested % |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |   t(avg R) |   alpha t vs SPY |
|:--------------------------------------|---------:|--------:|----------:|-------------:|---------:|--------:|------------:|-------------:|--------:|-----------:|-----------:|-----------------:|
| A touch pullback                      |     0.56 |    2.08 |     -7.43 |         8.65 |      100 |   31    |       13.09 |        -4.3  |    0.46 |      14.99 |       1.47 |             0.79 |
| B confirmed pullback                  |     0.43 |    1.28 |     -4.8  |         6.51 |       77 |   33.77 |       16.48 |        -4.94 |    0.44 |      18.12 |       1.45 |             0.47 |
| C close breakout                      |     0.98 |    2.35 |     -3.82 |         5.91 |       59 |   45.76 |       14.85 |        -4.88 |    0.65 |      24    |       2.39 |             1.84 |
| D close breakout + confirmed pullback |     0.74 |    2.44 |     -5.32 |         7.95 |       98 |   40.82 |       14.89 |        -5.15 |    0.48 |      20.56 |       2.04 |             1.16 |
| fixed rules (vcp.jlaw primary)        |     0.12 |    0.43 |     -8.06 |        10.39 |      167 |   25.75 |       11.76 |        -3.99 |    0.06 |      14.61 |       0.37 |            -0.29 |
| SPY buy and hold                      |     0.94 |   17.25 |    -33.89 |       100    |      nan |  nan    |      nan    |       nan    |  nan    |     nan    |     nan    |           nan    |

Frozen for the holdout: **C close breakout**

Does the score rank setups? (development only, close-breakout entry)

|                    |   Sharpe |   ann % |   maxDD % |   invested % |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |   t(avg R) |   alpha t vs SPY |
|:-------------------|---------:|--------:|----------:|-------------:|---------:|--------:|------------:|-------------:|--------:|-----------:|-----------:|-----------------:|
| score: bottom half |    -0.54 |   -0.74 |     -4.49 |         4.63 |       73 |   28.77 |        6.29 |        -5.43 |   -0.29 |      19.63 |      -2.01 |            -1.75 |
| score: 50-75%      |    -0.6  |   -0.46 |     -2.5  |         1.56 |       39 |   28.21 |        7.99 |        -4.27 |   -0.13 |      17.26 |      -0.74 |            -1.69 |
| score: top quarter |     0.98 |    2.35 |     -3.82 |         5.91 |       59 |   45.76 |       14.85 |        -4.88 |    0.65 |      24    |       2.39 |             1.84 |

## Holdout 2022-2026 (run once)

The result is the row **C close breakout**; the others are for information.

|                                       |   Sharpe |   ann % |   maxDD % |   invested % |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |   t(avg R) |   alpha t vs SPY |
|:--------------------------------------|---------:|--------:|----------:|-------------:|---------:|--------:|------------:|-------------:|--------:|-----------:|-----------:|-----------------:|
| A touch pullback                      |     0.41 |    1.14 |     -4.87 |         6.26 |       96 |   37.5  |       12.54 |        -4.19 |    0.48 |      15.77 |       1.67 |             0.65 |
| B confirmed pullback                  |     0.88 |    2.13 |     -2.38 |         5.7  |       76 |   40.79 |       13.56 |        -4.79 |    0.55 |      18.26 |       1.81 |             1.71 |
| C close breakout                      |     0.21 |    0.28 |     -2.37 |         2.85 |       57 |   45.61 |       11.08 |        -5.96 |    0.34 |      19.53 |       1.37 |             0.27 |
| D close breakout + confirmed pullback |     0.45 |    1.05 |     -3.28 |         5.62 |       98 |   43.88 |       11.85 |        -5.69 |    0.33 |      18.59 |       1.68 |             0.74 |
| fixed rules (vcp.jlaw primary)        |     0.24 |    0.8  |     -4.33 |         9.83 |      172 |   35.47 |       11.34 |        -4.3  |    0.27 |      15.63 |       1.55 |             0.23 |
| SPY buy and hold                      |     0.49 |    7.29 |    -24.95 |       100    |      nan |  nan    |      nan    |       nan    |  nan    |     nan    |     nan    |           nan    |

## Whole period 2017-2026, for reference

|                                |   Sharpe |   ann % |   maxDD % |   invested % |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |   t(avg R) |   alpha t vs SPY |
|:-------------------------------|---------:|--------:|----------:|-------------:|---------:|--------:|------------:|-------------:|--------:|-----------:|-----------:|-----------------:|
| C close breakout               |     0.68 |    1.33 |     -4.07 |         4.4  |      116 |   45.69 |       13    |        -5.41 |    0.5  |      21.8  |       2.7  |             1.76 |
| fixed rules (vcp.jlaw primary) |     0.17 |    0.59 |     -9.67 |        10.11 |      341 |   30.5  |       11.51 |        -4.13 |    0.16 |      15.08 |       1.35 |            -0.1  |
| SPY buy and hold               |     0.73 |   12.23 |    -33.89 |       100    |      nan |  nan    |      nan    |       nan    |  nan    |     nan    |     nan    |           nan    |

Holdout trades of the frozen candidate by entry year:

|   entry_date |   trades |   win_pct |   avg_R |
|-------------:|---------:|----------:|--------:|
|         2022 |        7 |     57.14 |    0.19 |
|         2023 |       17 |     58.82 |    0.83 |
|         2024 |       13 |     23.08 |    0.1  |
|         2025 |       13 |     30.77 |    0.23 |
|         2026 |        7 |     71.43 |   -0.04 |

## Added to the live core (whole-period stream, walk-forward weights)

|                 |   2019-26 |   2021-26 |   2024-05+ |
|:----------------|----------:|----------:|-----------:|
| core (live)     |     1.019 |     0.835 |      1.054 |
| core + VCP      |     1.024 |     0.82  |      1.036 |
| VCP weight 2026 |     0.032 |   nan     |    nan     |

