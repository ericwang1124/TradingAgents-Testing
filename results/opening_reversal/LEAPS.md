# One-year calls after a 2% down day

```
Buy a one-year call on QQQ (or VGT) after a 2% down day: per-trade record and a small portfolio.

    python -m tradingagents.strategies.leaps.backtest

Written and committed before the first run. Every variant below is reported; none is picked.

Signal: the underlying closes 2% or more below the previous close. At most one new entry per 20
sessions per underlying (low frequency, and repeated signals in one selloff do not stack up).
Entry at that day's close. Variant: only while the underlying is above its 200-day average.
Option: expiry one year after entry; strike 100% of spot (at the money) or 80% (deep in the money,
delta about 0.85). Priced with Black-Scholes, implied vol from the model in leaps.pricing (VXN,
moneyness, time; fitted to 2024-26 QQQ quotes), T-bill rate, 0.6% dividend yield, every day of the
holding period, so exits use the vol of that day.
Exits:  E1 sell after 6 months
        E2 sell after 9 months (3 months before expiry)
        E3 sell at the first close 50% above cost, else after 9 months
        E4 sell at the first close 20% above cost, else after 9 months
Costs: 1% of the option price per side for QQQ; 4% for VGT, whose options trade thinly.
Controls, same exits: the same option bought on every session (the base rate the signal must beat);
QQQ shares bought on the same signal days and held as long; buy-and-hold.
Portfolio: each entry spends 5% of equity on premium, at most 6 positions open, the rest in T-bills.
Data: QQQ and VGT daily closes (Yahoo), VXN from 2001-01, 13-week T-bill yield.

Limits: modelled prices, not quotes, before 2024; the vol model was fitted in 2024-26 and is applied
back to VXN levels of up to 80 (2008); intraday paths and early assignment are ignored.
```

IV model: {"a": 0.1703, "b": 0.3316, "c": -0.2799, "d": 0.1978, "e": 0.0015}. Signals (after the 20-session cooldown): {'QQQ': 151, 'QQQ above SMA200': 88, 'VGT': 131, 'VGT above SMA200': 83}.

## Every variant, per trade (option return after costs)

|                                                         |   trades |   win % |   avg % |   median % |   avg win % |   avg loss % |   worst % |   lost > 50% (share) |   avg days |
|:--------------------------------------------------------|---------:|--------:|--------:|-----------:|------------:|-------------:|----------:|---------------------:|-----------:|
| QQQ | ATM | E1 6 months                                 |      148 |    60.8 |    27.4 |       27.2 |        83.4 |        -59.6 |    -100   |                 23   |      126   |
| QQQ | ATM | E1 6 months | above SMA200 only             |       88 |    67   |    36.4 |       33.6 |        77.7 |        -47.6 |     -99.7 |                 13.6 |      126   |
| QQQ | ATM | E2 9 months                                 |      147 |    61.2 |    45.9 |       44.5 |       118.5 |        -68.7 |    -100   |                 26.5 |      189   |
| QQQ | ATM | E2 9 months | above SMA200 only             |       88 |    68.2 |    56.6 |       48.3 |       108.5 |        -54.6 |    -100   |                 17   |      189   |
| QQQ | ATM | E3 +50% or 9 months                         |      149 |    75.2 |    21.8 |       51.8 |        53.2 |        -73.4 |    -100   |                 18.1 |       96   |
| QQQ | ATM | E3 +50% or 9 months | above SMA200 only     |       88 |    80.7 |    31.5 |       51.9 |        52.8 |        -57.8 |    -100   |                 10.2 |      100.4 |
| QQQ | ATM | E4 +20% or 9 months                         |      150 |    88   |    12   |       22.7 |        24.4 |        -79.6 |    -100   |                  9.3 |       49.8 |
| QQQ | ATM | E4 +20% or 9 months | above SMA200 only     |       88 |    93.2 |    17.2 |       22.4 |        23.8 |        -73.3 |    -100   |                  4.5 |       47   |
| QQQ | ITM 80% | E1 6 months                             |      148 |    64.9 |    15   |       21.6 |        48.3 |        -46.4 |     -98.4 |                 14.9 |      126   |
| QQQ | ITM 80% | E1 6 months | above SMA200 only         |       88 |    72.7 |    21.9 |       24   |        43.5 |        -35.7 |     -97.2 |                  8   |      126   |
| QQQ | ITM 80% | E2 9 months                             |      147 |    68.7 |    25.9 |       38.1 |        65.4 |        -60.9 |    -100   |                 19   |      189   |
| QQQ | ITM 80% | E2 9 months | above SMA200 only         |       88 |    77.3 |    35.5 |       39.6 |        58.8 |        -43.4 |     -99.9 |                  8   |      189   |
| QQQ | ITM 80% | E3 +50% or 9 months                     |      148 |    72.3 |    15.9 |       50.3 |        45.7 |        -61.8 |    -100   |                 16.9 |      137   |
| QQQ | ITM 80% | E3 +50% or 9 months | above SMA200 only |       88 |    78.4 |    25   |       50.3 |        44.4 |        -45.6 |     -99.9 |                  8   |      139.6 |
| QQQ | ITM 80% | E4 +20% or 9 months                     |      149 |    84.6 |     7   |       21.2 |        22.1 |        -75.4 |    -100   |                 12.1 |       70.7 |
| QQQ | ITM 80% | E4 +20% or 9 months | above SMA200 only |       88 |    90.9 |    12.7 |       21.1 |        21   |        -71.3 |     -99.9 |                  6.8 |       70.9 |
| VGT | ATM | E1 6 months                                 |      127 |    61.4 |    34.9 |       35.4 |        90   |        -52.9 |    -100   |                 20.5 |      126   |
| VGT | ATM | E1 6 months | above SMA200 only             |       83 |    63.9 |    34.8 |       34.5 |        80.7 |        -46.3 |     -99.9 |                 15.7 |      126   |
| VGT | ATM | E2 9 months                                 |      126 |    66.7 |    60.4 |       54.5 |       121.6 |        -61.9 |    -100   |                 19   |      189   |
| VGT | ATM | E2 9 months | above SMA200 only             |       83 |    72.3 |    63.1 |       56.7 |       109.1 |        -56.8 |    -100   |                 12   |      189   |
| VGT | ATM | E3 +50% or 9 months                         |      128 |    77.3 |    26.3 |       52.1 |        53.2 |        -65.7 |    -100   |                 14.1 |      101   |
| VGT | ATM | E3 +50% or 9 months | above SMA200 only     |       83 |    81.9 |    32   |       52.5 |        52.8 |        -62.2 |    -100   |                  8.4 |      101.4 |
| VGT | ATM | E4 +20% or 9 months                         |      130 |    86.9 |    11.8 |       22.3 |        24.2 |        -70.2 |    -100   |                  8.5 |       62.8 |
| VGT | ATM | E4 +20% or 9 months | above SMA200 only     |       83 |    90.4 |    14.4 |       22.3 |        23.6 |        -71.4 |    -100   |                  4.8 |       59.5 |
| VGT | ITM 80% | E1 6 months                             |      127 |    64.6 |    17.3 |       23.5 |        47.7 |        -38.2 |     -99   |                 11.8 |      126   |
| VGT | ITM 80% | E1 6 months | above SMA200 only         |       83 |    68.7 |    17.7 |       21   |        41.1 |        -33.6 |     -99   |                  8.4 |      126   |
| VGT | ITM 80% | E2 9 months                             |      126 |    72.2 |    32.5 |       36.8 |        63.5 |        -48   |    -100   |                 11.9 |      189   |
| VGT | ITM 80% | E2 9 months | above SMA200 only         |       83 |    77.1 |    34.6 |       39.5 |        57.4 |        -42   |    -100   |                  8.4 |      189   |
| VGT | ITM 80% | E3 +50% or 9 months                     |      127 |    73.2 |    19.2 |       50.2 |        44.1 |        -49   |    -100   |                 11.8 |      143.3 |
| VGT | ITM 80% | E3 +50% or 9 months | above SMA200 only |       83 |    78.3 |    24.5 |       50.2 |        43.3 |        -43.5 |    -100   |                  8.4 |      144.7 |
| VGT | ITM 80% | E4 +20% or 9 months                     |      129 |    80.6 |     7.5 |       20.8 |        21.3 |        -49.9 |    -100   |                  8.5 |       88.4 |
| VGT | ITM 80% | E4 +20% or 9 months | above SMA200 only |       83 |    84.3 |    10.4 |       20.9 |        21.1 |        -46.9 |    -100   |                  7.2 |       89.3 |

## Does the 2% drop help? Same QQQ option bought on any day (every 5th session) vs on signal days

|                               |   signal: win % |   any day: win % |   signal: avg % |   any day: avg % |   signal: worst % |   any day: worst % |
|:------------------------------|----------------:|-----------------:|----------------:|-----------------:|------------------:|-------------------:|
| ATM | E1 6 months             |            60.8 |             65   |            27.4 |             30.7 |            -100   |             -100   |
| ATM | E2 9 months             |            61.2 |             63.7 |            45.9 |             50.4 |            -100   |             -100   |
| ATM | E3 +50% or 9 months     |            75.2 |             76.4 |            21.8 |             25   |            -100   |             -100   |
| ATM | E4 +20% or 9 months     |            88   |             87.4 |            12   |             11.9 |            -100   |             -100   |
| ITM 80% | E1 6 months         |            64.9 |             69.1 |            15   |             17   |             -98.4 |              -98.8 |
| ITM 80% | E2 9 months         |            68.7 |             69.5 |            25.9 |             29   |            -100   |             -100   |
| ITM 80% | E3 +50% or 9 months |            72.3 |             73.1 |            15.9 |             20.8 |            -100   |             -100   |
| ITM 80% | E4 +20% or 9 months |            84.6 |             85.2 |             7   |             10.9 |            -100   |             -100   |

## QQQ shares on the same days

|                                   |   trades |   win % |   avg % |   median % |   avg win % |   avg loss % |   worst % |   lost > 50% (share) |   avg days |
|:----------------------------------|---------:|--------:|--------:|-----------:|------------:|-------------:|----------:|---------------------:|-----------:|
| QQQ shares, 6 months, signal days |      148 |    69.6 |     6.7 |        9.6 |        16   |        -14.5 |     -41.1 |                  0   |        126 |
| QQQ shares, 6 months, any day     |     1273 |    75.8 |     7   |        9.2 |        13.3 |        -12.7 |     -44.4 |                  0   |        126 |
| QQQ shares, 9 months, signal days |      147 |    74.1 |    10.5 |       14.2 |        21   |        -19.6 |     -45.8 |                  0   |        189 |
| QQQ shares, 9 months, any day     |     1260 |    78.5 |    11   |       14   |        18.3 |        -15.6 |     -51.1 |                  0.1 |        189 |

## By entry year, QQQ, 9-month hold

ATM, 9 months:

|        |   2001 |   2002 |   2003 |   2004 |   2005 |   2006 |   2007 |   2008 |   2009 |   2010 |   2011 |   2012 |   2013 |   2014 |   2015 |   2016 |   2017 |   2018 |   2019 |   2020 |   2021 |   2022 |   2023 |   2024 |   2025 |   2026 |
|:-------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| trades |   11   |   11   |    8   |    6   |    2   |    5   |    5   |    9   |    8   |    4   |    7   |    3   |    2   |    4   |    6   |    3   |    2   |    7   |    4   |   10   |    5   |   10   |    4   |    5   |    5   |    5   |
| win %  |    0   |   45.5 |   75   |   50   |   50   |   60   |   20   |   22.2 |   87.5 |  100   |   71.4 |   66.7 |  100   |  100   |   33.3 |  100   |  100   |   42.9 |  100   |  100   |   60   |   40   |  100   |   80   |  100   |   40   |
| avg    |  -89.6 |   -9.2 |   99.3 |  -12.3 |   36.1 |   25.4 |  -49.4 |  -39.5 |  157.3 |  123.8 |   45.7 |   26.4 |  178.1 |   96.2 |  -12.8 |  129.1 |  140.8 |   -0.1 |  115.5 |  208.7 |    5.7 |   17.5 |  103.5 |   42.2 |  117.7 |   14.1 |

ITM 80%, 9 months:

|        |   2001 |   2002 |   2003 |   2004 |   2005 |   2006 |   2007 |   2008 |   2009 |   2010 |   2011 |   2012 |   2013 |   2014 |   2015 |   2016 |   2017 |   2018 |   2019 |   2020 |   2021 |   2022 |   2023 |   2024 |   2025 |   2026 |
|:-------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| trades |   11   |   11   |    8   |    6   |    2   |    5   |    5   |    9   |    8   |    4   |    7   |    3   |    2   |    4   |    6   |    3   |    2   |    7   |    4   |   10   |    5   |   10   |    4   |      5 |    5   |    5   |
| win %  |    9.1 |   45.5 |   75   |   50   |   50   |   80   |   40   |   22.2 |  100   |  100   |   85.7 |  100   |  100   |  100   |   66.7 |  100   |  100   |   71.4 |  100   |  100   |   60   |   50   |  100   |     80 |  100   |   60   |
| avg    |  -75.7 |  -11.4 |   64.2 |    5.4 |   25.1 |   23.4 |  -27.9 |  -43   |   93.5 |   73.4 |   37.6 |   27.4 |   90.2 |   56.7 |    7   |   72.7 |   74.2 |   11.6 |   68.2 |  118.9 |   -3.3 |    5.4 |   62.6 |     30 |   69.7 |   11.1 |

## Portfolios 2001-2026 (excess over T-bills)

|                                                        |   Sharpe |   ann % (excess) |   vol % |   maxDD % |
|:-------------------------------------------------------|---------:|-----------------:|--------:|----------:|
| QQQ ATM, E2 9 months, 5% premium per entry             |     0.46 |             8.36 |   23.92 |    -59.28 |
| QQQ ATM, E4 +20% or 9 months, 5% premium per entry     |     0.44 |             3.17 |    7.71 |    -23.07 |
| QQQ ITM 80%, E2 9 months, 5% premium per entry         |     0.38 |             4.94 |   16.26 |    -51.2  |
| QQQ ITM 80%, E4 +20% or 9 months, 5% premium per entry |     0.2  |             1.39 |    8.66 |    -36.77 |
| QQQ buy and hold                                       |     0.45 |             8.32 |   24.39 |    -70.48 |
