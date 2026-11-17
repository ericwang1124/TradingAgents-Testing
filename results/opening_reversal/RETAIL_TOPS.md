# Retail TOPS: traders' methods weighted by their own record

```
Retail TOPS: well-known traders' methods as contributors, weighted by their own track record.

    python -m tradingagents.strategies.vcp.retail_tops

Marshall Wace's TOPS collects trade ideas from sell-side contributors, scores every contributor on
how their ideas did, and sizes ideas by that score. Here the contributors are seven published trading
methods, each turned into daily-bar rules on the same point-in-time US stock universe (unadjusted
price >= $12, 50-day dollar volume >= $20M, delisted names included). Written and committed before
any run; the rules follow the public descriptions cited in reports/散户TOPS_交易员方法加权.md.

Contributors (entry at the close of the signal day unless stated; 5 bp per side):
  1 Minervini VCP      scored setups of vcp.jlaw_flex (seven items, top quarter by the 2017-21 cutoff),
                       close-confirmed breakout entry, stop below the last contraction, SMA20 trail
  2 J Law pullback     the same setups, buy-stop above a quiet pullback to the pivot (jlaw_flex)
  3 Qullamaggie BO     a 30%+ move within the prior 63 sessions, then 15 sessions within a 15% range
                       with SMA10 above SMA20 and the close above SMA20; a close above the range high on
                       volume >= 1.5x the 50-day average. Stop: the day's low (skipped if farther than one
                       ATR14). Trail: close below SMA10 if the 20-day average range is >= 4%, else SMA20.
  4 Qullamaggie EP     open >= 10% above the prior close on volume >= 3x the 50-day average, close at or
                       above the open, prior 63-session return <= +30% (not already extended). Stop: the
                       day's low (skipped if farther than 1.5 ATR14). Trail as 3.
  5 Kell crossback     EMA10 > EMA21 > SMA50, SMA50 rising, at least 10 of the prior 15 closes above EMA21;
                       yesterday's low touched EMA21 and today closes above yesterday's high and EMA10.
                       Stop 0.5% below the lowest low of the past 4 sessions (skipped beyond 8%).
                       Exit: close below EMA21.
  6 Darvas box         box top = 20-session high set at least 3 sessions ago and within 5% of the 52-week
                       high; box bottom = lowest low since the top. Close above the top on volume >= 1.5x
                       the 50-day average. Stop: box bottom (skipped beyond 10%). Trail: lowest low of the
                       prior 10 sessions.
  7 Weinstein stage 2  Fridays: weekly close crosses above the 30-week average, which is flat or rising
                       over 4 weeks; weekly volume >= 2x its 10-week average; relative strength vs SPY above
                       its 52-week average. Stop: lowest low of the prior 8 weeks (skipped beyond 15%).
                       Exit: a weekly close below the 30-week average.
  All: stop moves to entry after 5 sessions if the close is above entry (3, 4) or after a close 10% above
  entry (1, 2, 5, 6, 7); at most 252 sessions; a stock whose data ends is sold at its last close.
  When trailing starts: for 3 and 4 only once the stop has moved to entry (Qullamaggie's low-of-day stop
  first, the moving average after the first days); for 5, 6 and 7 from the day after entry; 1 and 2 keep
  the jlaw_flex rule (SMA20 trail after a close 10% above entry).

Each contributor's ideas are first played out one by one (no capital limits) to give its track record.
The portfolio then takes them with 0.35% of equity at risk per idea (size = risk / stop distance),
at most 15% per stock, gross at most 100%, cash in T-bills, ideas of the day ranked by weight.
Weighting, three variants:
  A equal         every contributor x1
  B skill (PRIMARY)  each month-end, mean R of the contributor's ideas closed in the past 24 months,
                  shrunk by n / (n + 30); weight = shrunk mean / average of the positive ones; zero or
                  negative = paused (its ideas still recorded); fewer than 10 closed ideas = x1
  C skill + consensus  B, and x1.5 when at least two contributors had an idea on the stock in the past
                  10 sessions
Reported: each contributor's record and stand-alone portfolio, A/B/C for 2017-26, 2017-21 and 2022-26,
SPY, and B added to the live core. B is adopted only if it raises the core's Sharpe in 2019-26, 2021-26
and 2024-05 onward. Weights are always computed from the past, so the whole period is out of sample for
the weighting; the rule definitions come from public descriptions, not from this data.
```

## Each contributor's ideas, played one by one

2017-2021:

| who               |   ideas |   per year |   win % |   avg R |   t(avg R) |   avg win % |   avg loss % |   avg days |
|:------------------|--------:|-----------:|--------:|--------:|-----------:|------------:|-------------:|-----------:|
| Minervini VCP     |      59 |      11.82 |   45.76 |    0.65 |       2.39 |       14.85 |        -4.88 |      24    |
| J Law pullback    |      77 |      15.43 |   33.77 |    0.44 |       1.45 |       16.48 |        -4.94 |      18.12 |
| Qullamaggie BO    |    1161 |     232.61 |   14.04 |   -0.22 |      -2.72 |        8.06 |        -1.71 |       6.39 |
| Qullamaggie EP    |     333 |      66.72 |   26.73 |    0.08 |       0.87 |       10.35 |        -3.78 |       8.5  |
| Kell crossback    |   33831 |    6778.26 |   30.25 |    0.07 |       8.13 |        6.65 |        -2.48 |      11.89 |
| Darvas box        |    2883 |     577.63 |   36.73 |    0.03 |       0.87 |        7.39 |        -4.1  |      24.96 |
| Weinstein stage 2 |      97 |      19.43 |   21.65 |    0.18 |       0.63 |       24.5  |        -5.53 |      46.96 |

2022-2026:

| who               |   ideas |   per year |   win % |   avg R |   t(avg R) |   avg win % |   avg loss % |   avg days |
|:------------------|--------:|-----------:|--------:|--------:|-----------:|------------:|-------------:|-----------:|
| Minervini VCP     |      57 |      11.74 |   45.61 |    0.34 |       1.37 |       11.08 |        -5.96 |      19.53 |
| J Law pullback    |      76 |      15.66 |   40.79 |    0.55 |       1.81 |       13.56 |        -4.79 |      18.26 |
| Qullamaggie BO    |    1290 |     265.75 |   14.65 |   -0.09 |      -1    |       10    |        -1.96 |       6.35 |
| Qullamaggie EP    |     467 |      96.21 |   24.84 |   -0    |      -0.03 |       11.71 |        -4    |       8.24 |
| Kell crossback    |   30776 |    6340.06 |   26.57 |   -0.02 |      -2.32 |        7.45 |        -2.8  |      10.4  |
| Darvas box        |    2284 |     470.52 |   35.38 |   -0.04 |      -0.77 |        7.92 |        -4.54 |      22.34 |
| Weinstein stage 2 |      89 |      18.33 |   21.35 |    0.3  |       1.15 |       23.22 |        -4.96 |      45.74 |

## Weights (yearly average of the monthly weights; 0 = paused)

|      |   Minervini VCP |   J Law pullback |   Qullamaggie BO |   Qullamaggie EP |   Kell crossback |   Darvas box |   Weinstein stage 2 |
|-----:|----------------:|-----------------:|-----------------:|-----------------:|-----------------:|-------------:|--------------------:|
| 2016 |            1    |             1    |             1    |             1    |             1    |         1    |                1    |
| 2017 |            1.22 |             1.07 |             0    |             0.62 |             0.41 |         0.42 |                0.92 |
| 2018 |            1.6  |             0.93 |             0    |             0.08 |             0.43 |         0.56 |                2.07 |
| 2019 |            1.39 |             1.3  |             0    |             0.63 |             0.3  |         0.33 |                1.8  |
| 2020 |            1.57 |             1.56 |             0    |             0.26 |             0.02 |         0    |                0.09 |
| 2021 |            1.78 |             1.4  |             0    |             0.16 |             0.91 |         0.09 |                0    |
| 2022 |            0.08 |             0.13 |             0.27 |             0.59 |             1.13 |         0.05 |                0    |
| 2023 |            0.64 |             0.39 |             0    |             0.3  |             0    |         0    |                0    |
| 2024 |            1.06 |             1.59 |             0    |             0.47 |             0.02 |         0.08 |                0.78 |
| 2025 |            0.91 |             1.65 |             0.13 |             0.24 |             0.3  |         0.46 |                2.57 |
| 2026 |            0.28 |             1.41 |             0.67 |             0    |             0.4  |         0.24 |                2.37 |

## Portfolios (excess over T-bills)

|                                      |   Sharpe |   ann % |   vol % |   maxDD % |   invested % |   trades |   win % |   avg R |   alpha t vs SPY |
|:-------------------------------------|---------:|--------:|--------:|----------:|-------------:|---------:|--------:|--------:|-----------------:|
| 2017-26 | A equal weights            |     0.14 |    1.01 |   15.04 |    -35.29 |        98.25 |     3265 |   25.57 |    0    |            -0.98 |
| 2017-26 | B skill-weighted (PRIMARY) |    -0.03 |   -1    |   11.83 |    -30.45 |        74.34 |     3921 |   29.94 |    0.06 |            -1.56 |
| 2017-26 | C skill + consensus        |     0.02 |   -0.48 |   12.13 |    -31.61 |        75.23 |     3606 |   29.98 |    0.06 |            -1.35 |
| 2017-26 | alone: Minervini VCP       |     0.75 |    1.88 |    2.54 |     -5.2  |         6.09 |      116 |   45.69 |    0.5  |             1.94 |
| 2017-26 | alone: J Law pullback      |     0.63 |    2.38 |    3.88 |     -6.72 |         8.5  |      153 |   37.25 |    0.49 |             1.46 |
| 2017-26 | alone: Qullamaggie BO      |    -0.22 |   -3.39 |   12.12 |    -38.62 |        56.24 |     1542 |   15.11 |   -0.12 |            -1.58 |
| 2017-26 | alone: Qullamaggie EP      |     0.16 |    1.05 |    8.68 |    -19.04 |        25.26 |      794 |   26.45 |    0.07 |            -0.26 |
| 2017-26 | alone: Kell crossback      |     0.11 |    0.58 |   13.92 |    -33.43 |        96.88 |     3282 |   28.18 |    0.04 |            -1.1  |
| 2017-26 | alone: Darvas box          |    -0.27 |   -3.72 |   11.44 |    -45.62 |        84.29 |     1763 |   36.87 |   -0.01 |            -2.07 |
| 2017-26 | alone: Weinstein stage 2   |     0.24 |    0.88 |    4    |    -14.95 |        16.3  |      188 |   21.81 |    0.24 |            -0.49 |
| 2017-26 | SPY                        |     0.73 |   12.23 |   18.13 |    -33.89 |       nan    |      nan |  nan    |  nan    |           nan    |
| 2017-21 | A equal weights            |     0.51 |    6.19 |   13.69 |    -16.73 |        98.02 |     1483 |   27.51 |    0.05 |            -0.17 |
| 2017-21 | B skill-weighted (PRIMARY) |     0.24 |    2.11 |   11.06 |    -15.72 |        79.5  |     2148 |   32.12 |    0.12 |            -0.73 |
| 2017-21 | C skill + consensus        |     0.38 |    3.74 |   11.3  |    -17.7  |        80.2  |     2016 |   32.24 |    0.13 |            -0.36 |
| 2017-21 | alone: Minervini VCP       |     0.98 |    2.6  |    2.67 |     -4.7  |         6.72 |       59 |   45.76 |    0.65 |             1.82 |
| 2017-21 | alone: J Law pullback      |     0.58 |    2.2  |    3.91 |     -5.85 |         8.21 |       77 |   33.77 |    0.44 |             0.84 |
| 2017-21 | alone: Qullamaggie BO      |    -0.19 |   -2.63 |   10.73 |    -29.91 |        53.13 |      714 |   15.83 |   -0.1  |            -1.16 |
| 2017-21 | alone: Qullamaggie EP      |     0.31 |    1.89 |    6.73 |     -9.83 |        21.62 |      321 |   26.79 |    0.09 |            -0.12 |
| 2017-21 | alone: Kell crossback      |     0.59 |    6.92 |   12.74 |    -18.04 |        95.96 |     1498 |   30.57 |    0.09 |             0.17 |
| 2017-21 | alone: Darvas box          |     0.38 |    3.44 |   10.32 |    -19.32 |        85.95 |      835 |   39.4  |    0.14 |            -0.24 |
| 2017-21 | alone: Weinstein stage 2   |     0.27 |    1.02 |    4.13 |    -12.03 |        15.91 |       97 |   21.65 |    0.18 |            -0.7  |
| 2017-21 | SPY                        |     0.94 |   17.25 |   18.86 |    -33.89 |       nan    |      nan |  nan    |  nan    |           nan    |
| 2022-26 | A equal weights            |    -0.07 |   -2.49 |   16.31 |    -33.95 |        98.48 |     1762 |   24.29 |   -0.03 |            -0.83 |
| 2022-26 | B skill-weighted (PRIMARY) |    -0.23 |   -3.62 |   12.59 |    -28.61 |        69.01 |     1773 |   27.35 |   -0.01 |            -1.27 |
| 2022-26 | C skill + consensus        |    -0.27 |   -4.15 |   12.81 |    -26.89 |        70.09 |     1590 |   26.92 |   -0.03 |            -1.37 |
| 2022-26 | alone: Minervini VCP       |     0.49 |    1.15 |    2.41 |     -3.24 |         5.43 |       57 |   45.61 |    0.34 |             0.87 |
| 2022-26 | alone: J Law pullback      |     0.68 |    2.56 |    3.84 |     -4.73 |         8.8  |       76 |   40.79 |    0.55 |             1.25 |
| 2022-26 | alone: Qullamaggie BO      |    -0.22 |   -3.83 |   13.4  |    -29.38 |        59.38 |      828 |   14.49 |   -0.13 |            -0.96 |
| 2022-26 | alone: Qullamaggie EP      |     0.09 |    0.43 |   10.31 |    -19.04 |        28.99 |      473 |   26.22 |    0.05 |            -0.14 |
| 2022-26 | alone: Kell crossback      |    -0.23 |   -4.47 |   15.05 |    -28.53 |        97.77 |     1785 |   26.22 |   -0    |            -1.32 |
| 2022-26 | alone: Darvas box          |    -0.79 |  -10.11 |   12.46 |    -41.81 |        82.12 |      932 |   34.44 |   -0.15 |            -2.34 |
| 2022-26 | alone: Weinstein stage 2   |     0.27 |    0.95 |    3.81 |     -6.3  |        16.34 |       91 |   21.98 |    0.31 |             0.12 |
| 2022-26 | SPY                        |     0.49 |    7.29 |   17.36 |    -24.95 |       nan    |      nan |  nan    |  nan    |           nan    |

## Monthly correlation of contributors' average R

|                   |   Minervini VCP |   J Law pullback |   Qullamaggie BO |   Qullamaggie EP |   Kell crossback |   Darvas box |   Weinstein stage 2 |
|:------------------|----------------:|-----------------:|-----------------:|-----------------:|-----------------:|-------------:|--------------------:|
| Minervini VCP     |            1    |             0.59 |            -0.03 |            -0.03 |             0.13 |         0.28 |               -0.03 |
| J Law pullback    |            0.59 |             1    |            -0.06 |             0.02 |             0.05 |         0.23 |                0.01 |
| Qullamaggie BO    |           -0.03 |            -0.06 |             1    |             0.11 |             0.35 |         0.19 |                0.02 |
| Qullamaggie EP    |           -0.03 |             0.02 |             0.11 |             1    |             0.16 |         0.07 |               -0.02 |
| Kell crossback    |            0.13 |             0.05 |             0.35 |             0.16 |             1    |         0.37 |                0.17 |
| Darvas box        |            0.28 |             0.23 |             0.19 |             0.07 |             0.37 |         1    |                0.09 |
| Weinstein stage 2 |           -0.03 |             0.01 |             0.02 |            -0.02 |             0.17 |         0.09 |                1    |

## B added to the live core (walk-forward weights)

|                 |   2019-26 |   2021-26 |   2024-05+ |
|:----------------|----------:|----------:|-----------:|
| core (live)     |     1.019 |     0.835 |      1.054 |
| core + VCP      |     1.008 |     0.825 |      1.038 |
| VCP weight 2026 |     0.012 |   nan     |    nan     |

Verdict: **reject** (raises the core's Sharpe in all three periods: False)
