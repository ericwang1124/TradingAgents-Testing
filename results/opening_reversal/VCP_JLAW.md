# J Law's VCP method as fixed rules

```
J Law's VCP method as fixed daily-bar rules, US stocks 2017-2026 (delisted names included).

    python -m tradingagents.strategies.vcp.jlaw

Translated from the user's notes on J Law's method. Written and committed before the first run on
real data. PRIMARY decides; the other rows are reported for information, not to pick a winner.

1. Screen at each close: unadjusted price >= $12; 50-day average dollar volume >= $20M; >= 240 closes in the
   past year; close > SMA50 > SMA200, both averages above their value 21 sessions earlier; close within
   15% of the 52-week high; 1-year return in the top 20% of the day's universe.
2. Pattern at the close of t, over the past 250 sessions: start at the highest high, take the lowest
   low after it (contraction 1 = high -> low), then the highest high after that low and the lowest
   low after it (contraction 2), and so on; moves smaller than 3% are ignored. The VCP is the run of
   contractions starting with the first one <= 35% deep. Needed: at least 2 contractions, the first
   10%..35%, each shallower than the one before, the last <= 10%, average volume during the last
   decline below the 50-day average, the last high (the pivot) at least 3 sessions old, the last low
   before t, the base at least 15 sessions long, nothing in the window deeper than 60%.
3. Entries.
   pullback (PRIMARY): a breakout day is a close above the pivot on volume above both the prior
     day's and the 50-day average. Within the next 15 sessions, on the first day whose low is within
     2% above the pivot (or below it), whose close is no more than 3% below the pivot and above SMA50,
     whose volume is below the 50-day average, and with SMA10 or SMA20 within 3% of the pivot: buy at
     that close. The watch ends if a close falls more than 3% below the pivot.
   breakout: buy when price crosses the pivot intraday (at the pivot, or the open if it gaps above;
     skipped if the open is more than 2% above). If by the close the price is back below the pivot
     or the volume condition fails, sell at that close.
4. Stops and size. Pullback: 1% below the lowest of the pivot, the day's low and the supporting
   average(s). Breakout: 1% below the last contraction's low. A stop farther than 8% skips the trade;
   closer than 3% is set to 3%. Each trade risks 0.35% of equity; a position is at most 15% of
   equity; no leverage (gross <= 100%); cash earns T-bills. New trades risk half as much while fewer
   than 3 of the last 10 closed trades were winners, and half as much while SPY has had 4 or more
   distribution days (down >= 0.2% on higher volume than the day before) in the past 20 sessions.
   Candidates on the same day are taken in order of 1-year relative strength.
5. Exits. Initial stop (a gap below fills at the open). After a close 10% above entry the stop moves
   to 0.5% above entry and from then on a close below SMA20 sells. A close below SMA50 always sells.
   A stock whose data ends is sold at its last close. Costs 5 bp per side.

Reported alongside: breakout entry; both entries; SMA10 trail; sell into strength at 4x the risk;
at least 3 contractions; first contraction up to 50%; relative strength top 10%; no reduction after
losing streaks; no trades while SPY is below its 200-day average; 1% risk per trade (25% cap).
References: the fixed-window Minervini version (vcp.backtest), a screen-only momentum book (each Friday
the 20 highest relative-strength stocks that pass the screen, 5% each), SPY and 60/40 buy and hold.

Not testable here: revenue acceleration, earnings surprises and guidance, sector moves, hand-drawn
trend lines, the leverage of the competition account, and discretion.
```

Data: 4649 stock columns (delisted included). Median day: 1435 stocks in the universe, 168 pass the screen; 80,237 stock-days with at least two contractions.

## Results 2017-2026 (excess over T-bills)

|                                         |   Sharpe |   1st half |   2nd half |   ann % (excess) |   vol % |   maxDD % |   avg gross % |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |
|:----------------------------------------|---------:|-----------:|-----------:|-----------------:|--------:|----------:|--------------:|---------:|--------:|------------:|-------------:|--------:|-----------:|
| PRIMARY: pullback entry, SMA20 trail    |     0.17 |       0.13 |       0.22 |             0.59 |    3.92 |     -9.67 |         10.11 |      341 |   30.5  |       11.51 |        -4.13 |    0.16 |      15.08 |
| breakout entry                          |    -0.15 |       0.21 |      -0.7  |            -0.58 |    3.51 |    -15.95 |          9.3  |     1605 |   35.45 |        3.2  |        -1.88 |   -0.01 |       3.66 |
| both entries                            |    -0.04 |       0.15 |      -0.3  |            -0.29 |    4.39 |    -13.97 |         12.74 |     1715 |   35.22 |        3.76 |        -2.07 |    0    |       4.42 |
| pullback, SMA10 trail                   |     0.21 |      -0.08 |       0.5  |             0.61 |    3.13 |     -6.63 |          8.55 |      341 |   30.5  |       12.37 |        -4.13 |    0.23 |      13.47 |
| pullback, sell at 4R                    |     0.1  |      -0.08 |       0.32 |             0.25 |    3.09 |     -7.15 |          7.91 |      341 |   30.5  |       11.32 |        -4.13 |    0.12 |      12.33 |
| pullback, >= 3 contractions             |     0.76 |       0.83 |       0.69 |             1.43 |    1.89 |     -2.76 |          3.56 |       74 |   39.19 |       12.91 |        -3.73 |    0.73 |      17.5  |
| pullback, first contraction up to 50%   |     0.15 |       0.1  |       0.23 |             0.53 |    3.96 |    -10.67 |         10.29 |      352 |   30.4  |       11.38 |        -4.13 |    0.15 |      14.87 |
| pullback, RS top 10%                    |     0.13 |       0.16 |       0.1  |             0.27 |    2.16 |     -4.4  |          4.31 |      153 |   30.07 |       13.55 |        -4.4  |    0.28 |      14.43 |
| pullback, no losing-streak reduction    |     0.28 |       0.16 |       0.42 |             1.22 |    4.73 |     -9.82 |         13.55 |      341 |   30.5  |       11.51 |        -4.13 |    0.16 |      15.08 |
| pullback, no trades while SPY < SMA200  |     0.19 |       0.19 |       0.19 |             0.64 |    3.84 |     -9.22 |          9.27 |      302 |   30.46 |       11.7  |        -4.1  |    0.17 |      15.05 |
| pullback, 1% risk per trade             |     0.01 |      -0.04 |       0.06 |            -0.25 |    8.27 |    -17.69 |         24.69 |      332 |   30.12 |       11.63 |        -4.14 |    0.16 |      14.99 |
| reference: Minervini fixed-window VCP   |    -0.12 |       0.07 |      -0.33 |            -1.75 |   10.36 |    -33.84 |         49.46 |      589 |   30.39 |       11.17 |        -5.22 |   -0.01 |      29.05 |
| reference: screen only, top-20 momentum |     0.39 |       0.5  |       0.29 |             7.6  |   35.1  |    -60.99 |        nan    |      nan |  nan    |      nan    |       nan    |  nan    |     nan    |
| SPY buy and hold                        |     0.73 |       0.93 |       0.51 |            12.23 |   18.13 |    -33.89 |        nan    |      nan |  nan    |      nan    |       nan    |  nan    |     nan    |
| 60/40 SPY/IEF                           |     0.68 |       1.09 |       0.28 |             7.04 |   10.92 |    -21.51 |        nan    |      nan |  nan    |      nan    |       nan    |  nan    |     nan    |

## Against SPY (daily regression)

|                              |   beta |   alpha %/yr |   alpha t |
|:-----------------------------|-------:|-------------:|----------:|
| PRIMARY                      |   0.06 |        -0.12 |     -0.1  |
| breakout entry               |   0.05 |        -1.19 |     -1.1  |
| both entries                 |   0.07 |        -1.11 |     -0.83 |
| screen only, top-20 momentum |   1.04 |        -0.21 |     -0.02 |
| Minervini fixed-window       |   0.21 |        -4.01 |     -1.3  |

## By year (primary)

|      |   J Law % |   SPY % |   avg invested % |   trades |
|-----:|----------:|--------:|-----------------:|---------:|
| 2017 |       2.4 |    20.9 |             14.5 |       31 |
| 2018 |      -4   |    -6.2 |              5.5 |       29 |
| 2019 |      -0.8 |    28.6 |              6.3 |       31 |
| 2020 |       7.5 |    17.9 |             18.4 |       40 |
| 2021 |      -2.6 |    28.9 |              7.2 |       37 |
| 2022 |      -1.5 |   -19.3 |              4.5 |       27 |
| 2023 |       2.2 |    20.2 |              7.9 |       29 |
| 2024 |       5.1 |    18.7 |             21.7 |       49 |
| 2025 |      -1   |    13   |              8   |       40 |
| 2026 |      -1.1 |     8.1 |              6.5 |       28 |

## Breakout vs pullback entries (from the run that takes both)

|          |   trades |   win % |   avg win % |   avg loss % |   avg R |   avg days |
|:---------|---------:|--------:|------------:|-------------:|--------:|-----------:|
| breakout |     1593 |   35.59 |        3.21 |        -1.87 |   -0    |       3.68 |
| pullback |      122 |   30.33 |       12.33 |        -4.41 |    0.11 |      14.11 |

## Exits (primary)

| reason            |   n |   avg_ret_pct |   avg_R |
|:------------------|----:|--------------:|--------:|
| breakeven stop    |   8 |          0.45 |    0.09 |
| close below SMA20 |  90 |         13.19 |    3.16 |
| close below SMA50 |  44 |         -2.12 |   -0.43 |
| delisted          |   1 |          0.04 |    0.01 |
| stop              | 198 |         -4.44 |   -1.06 |

## Ten best and five worst trades (primary)

| symbol   | entry_date          | exit_date           |   ret |   R_mult |   days | reason            |
|:---------|:--------------------|:--------------------|------:|---------:|-------:|:------------------|
| GH       | 2025-10-22 00:00:00 | 2025-12-10 00:00:00 | 0.507 |   11.285 |     34 | close below SMA20 |
| ELF      | 2022-10-19 00:00:00 | 2022-12-09 00:00:00 | 0.338 |   11.282 |     36 | close below SMA20 |
| BOOT     | 2021-10-04 00:00:00 | 2021-12-01 00:00:00 | 0.337 |    7.668 |     41 | close below SMA20 |
| RNG      | 2020-01-03 00:00:00 | 2020-03-03 00:00:00 | 0.324 |   10.405 |     40 | close below SMA20 |
| VERX     | 2024-10-10 00:00:00 | 2024-12-13 00:00:00 | 0.32  |    8.082 |     45 | close below SMA20 |
| BTU      | 2017-10-27 00:00:00 | 2018-02-02 00:00:00 | 0.304 |    7.863 |     66 | close below SMA20 |
| MTH      | 2020-07-09 00:00:00 | 2020-08-26 00:00:00 | 0.291 |    5.417 |     34 | close below SMA20 |
| ABVX     | 2025-10-07 00:00:00 | 2025-12-03 00:00:00 | 0.274 |    5.758 |     40 | close below SMA20 |
| NVMI     | 2024-05-06 00:00:00 | 2024-07-11 00:00:00 | 0.271 |    4.366 |     45 | close below SMA20 |
| LGND     | 2026-05-26 00:00:00 | 2026-07-15 00:00:00 | 0.258 |    3.356 |     34 | close below SMA20 |

| symbol   | entry_date          | exit_date           |    ret |   R_mult |   days | reason   |
|:---------|:--------------------|:--------------------|-------:|---------:|-------:|:---------|
| MRVL     | 2025-01-24 00:00:00 | 2025-01-27 00:00:00 | -0.13  |   -3.174 |      1 | stop     |
| KEYS     | 2026-10-09 00:00:00 | 2026-10-15 00:00:00 | -0.102 |   -1.308 |      4 | stop     |
| MEDP     | 2019-02-12 00:00:00 | 2019-02-26 00:00:00 | -0.101 |   -2.025 |      9 | stop     |
| ORLY     | 2022-04-12 00:00:00 | 2022-04-28 00:00:00 | -0.089 |   -2.46  |     11 | stop     |
| ARW      | 2026-08-05 00:00:00 | 2026-08-07 00:00:00 | -0.077 |   -1.308 |      2 | stop     |

## Added to the live core (walk-forward weights)

|                 |   2019-26 |   2021-26 |   2024-05+ |
|:----------------|----------:|----------:|-----------:|
| core (live)     |     1.019 |     0.835 |      1.054 |
| core + VCP      |     1.012 |     0.825 |      1.045 |
| VCP weight 2026 |     0.012 |   nan     |    nan     |
