# Leader breakouts

```
Leader breakouts: the scored VCP setups plus earnings news, peer strength and a market overlay.

    python -m tradingagents.strategies.vcp.leaders             # development period only
    python -m tradingagents.strategies.vcp.leaders --holdout   # once the development choice is frozen

Starting point: vcp.jlaw_flex (seven pattern items, confirmed entries). J Law's method is used as an
idea, not a target. Added here, each for a reason that does not depend on him. Written and committed
before any of it was run.

A. Five more score items, one point each (twelve in total with the seven of jlaw_flex):
   earnings   the latest quarterly report within 95 days, from timestamped news headlines: 1 if both
              EPS and sales beat estimates (older headlines give year-over-year numbers instead: EPS
              up and sales up 10% or more), 0.5 if one did and the other did not miss, else 0.
              Post-earnings drift is among the best-documented regularities.
   guidance   1 if guidance was raised (or set above estimates) on balance in those 95 days.
   analysts   price-target raises and upgrades minus cuts and downgrades in the past 60 days:
              3 or more = 1, 1 or 2 = 0.5.
   group      average 1-year-return percentile of the 20 stocks whose daily returns, net of the
              market, were most correlated with this one over the past 126 sessions (peers found
              from prices each month-end, since no industry codes are at hand): 0 at 50, 1 at 80.
   trendline  the base's highs descend (the earlier high more than 3% above the pivot) and the close
              is already above the line through the last two of them.
   Only what was published before 19:00 UTC on the breakout day counts.
B. Events and cutoff. An event is a bounded setup followed the next day by a close above the pivot on
   volume above the prior day's and the 50-day average. Traded: events whose 12-item score is at or above
   the 75th percentile of development-period events.
C. Entries: both confirmed ones of jlaw_flex (the close of the breakout day if within 5% of the
   pivot; else or later, a buy-stop above a quiet pullback day's high). The development period showed
   the choice between them to be noise, so both are taken.
D. Market overlay, three candidates:
   M0  none beyond the two reductions already in vcp.jlaw.
   M1  environment E = SPY above its 50-day average + at least half the stock universe above its
       50-day average + VIX below 3-month VIX + high-yield vs investment-grade bonds (HYG/LQD) above
       its 50-day average. New-trade risk x1 at E >= 3, x0.5 at E = 2, none at E <= 1; halved again
       while fewer than 30% of the market's breakouts of the past 30 sessions held their pivot five
       sessions later (needs at least five such breakouts).
   M2  M1, and in a reversal window - SPY was 8% or more below its 52-week high within the past 40
       sessions, is now above its 20-day average and above its close 10 sessions ago - new-trade
       risk is x1.5 whatever E says. Breakouts as a correction ends are the classic best case.
E. Unchanged: screen, 3-8% stops, 0.35% of equity at risk per trade, exits, 5 bp costs.

Protocol. Development 2017-01 to 2021-12: M0, M1, M2 compared; the highest Sharpe with at least 50
trades is frozen. Holdout 2022-01 to 2026-11: the frozen one is run once. Reported next to it: the
seven-item score on the same events (what the new information adds) and each item's own record.

Caveats. The holdout was already used once for jlaw_flex, so it is clean only for what is new here:
the five items, the event cutoff and the overlay. Renamed companies are looked up under old and new
tickers, but news coverage is thinner for small companies and for the earliest years.
```

Events: 1085 (538 in the development period). Score cutoffs from development events: 12 items 5.59, 7 items 3.43.

Share of events with a parsed quarterly report, and average new items, by year:

|   day |   has_report |   earnings |   guidance |   analysts |   group |   trendline |   events |
|------:|-------------:|-----------:|-----------:|-----------:|--------:|------------:|---------:|
|  2017 |         0.83 |       0.4  |       0.23 |       0.18 |    0.5  |        0.17 |       88 |
|  2018 |         0.9  |       0.48 |       0.34 |       0.42 |    0.56 |        0.24 |      105 |
|  2019 |         0.9  |       0.45 |       0.34 |       0.34 |    0.58 |        0.18 |      104 |
|  2020 |         0.84 |       0.51 |       0.2  |       0.59 |    0.65 |        0.13 |      118 |
|  2021 |         0.87 |       0.63 |       0.31 |       0.47 |    0.57 |        0.12 |      123 |
|  2022 |         0.79 |       0.5  |       0.33 |       0.45 |    0.61 |        0.12 |       75 |
|  2023 |         0.86 |       0.57 |       0.2  |       0.54 |    0.46 |        0.12 |      116 |
|  2024 |         0.87 |       0.6  |       0.26 |       0.6  |    0.47 |        0.16 |      117 |
|  2025 |         0.86 |       0.6  |       0.34 |       0.55 |    0.51 |        0.14 |      128 |
|  2026 |         0.89 |       0.65 |       0.52 |       0.57 |    0.59 |        0.16 |      111 |

Market overlay in development: M1 blocks new trades on 15% of days and halves or quarters them on 10%; reversal windows cover 19% of days.

## Development 2017-2021

|                               |   Sharpe |   ann % |   maxDD % |   invested % |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |   t(avg R) |   alpha t vs SPY |
|:------------------------------|---------:|--------:|----------:|-------------:|---------:|--------:|------------:|-------------:|--------:|-----------:|-----------:|-----------------:|
| 12 items, M0                  |     0.02 |    0.02 |     -4.9  |         3.94 |       79 |   32.91 |       11.29 |        -5.14 |    0.02 |      17.54 |       0.11 |            -0.44 |
| 12 items, M1                  |     0.02 |    0.01 |     -4.82 |         3.87 |       76 |   32.89 |       10.71 |        -5.1  |   -0.01 |      17.53 |      -0.07 |            -0.44 |
| 12 items, M2                  |    -0    |   -0.03 |     -5.06 |         4.3  |       77 |   33.77 |       11.21 |        -5.1  |    0.04 |      17.79 |       0.22 |            -0.5  |
| 7 items (jlaw_flex score), M0 |     0.72 |    2.3  |     -4.91 |         7.29 |       87 |   40.23 |       15.21 |        -5.15 |    0.49 |      20.57 |       1.95 |             1.14 |
| SPY buy and hold              |     0.94 |   17.25 |    -33.89 |       100    |      nan |  nan    |      nan    |       nan    |  nan    |     nan    |     nan    |           nan    |

Frozen for the holdout: **12 items, M0**

Each item's own record, development (all events bought at the confirmed close, no score filter):

|                                            |   n high |   avg R high |   n low |   avg R low |   difference t |
|:-------------------------------------------|---------:|-------------:|--------:|------------:|---------------:|
| count                                      |       42 |         0.49 |     127 |       -0.06 |           1.85 |
| tight                                      |      169 |         0.07 |       0 |      nan    |         nan    |
| first                                      |       31 |         0.88 |     138 |       -0.11 |           2.6  |
| dry                                        |       77 |         0.34 |      92 |       -0.15 |           1.95 |
| level                                      |      110 |         0.03 |      59 |        0.16 |          -0.45 |
| catalyst                                   |       42 |         0.06 |     127 |        0.08 |          -0.08 |
| strength                                   |       68 |         0.39 |     101 |       -0.14 |           1.95 |
| earnings                                   |       87 |        -0.07 |      82 |        0.23 |          -1.22 |
| guidance                                   |       55 |         0.21 |     114 |        0.01 |           0.8  |
| analysts                                   |       88 |        -0.08 |      81 |        0.24 |          -1.25 |
| group                                      |      101 |         0.24 |      68 |       -0.17 |           1.63 |
| trendline                                  |       23 |        -0.02 |     146 |        0.09 |          -0.37 |
| score7                                     |       43 |         0.61 |     126 |       -0.11 |           2.15 |
| score12                                    |       43 |         0.26 |     126 |        0.01 |           0.85 |
| market: environment E >= 3                 |      148 |         0.09 |      21 |       -0.03 |           0.41 |
| market: reversal window                    |       26 |        -0.42 |     143 |        0.16 |          -1.5  |
| market: half or more recent breakouts held |      138 |        -0.04 |      31 |        0.58 |          -1.83 |

