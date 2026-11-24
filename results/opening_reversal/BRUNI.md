# Gianluca Bruni's rules, as posted: SPY / QQQ / IWM intraday

```
Gianluca Bruni's rules as posted (value-area pullback + engulfing candle, ATR-percentile filter),
on SPY / QQQ / IWM intraday bars, 2018-10 to 2026-10.

    python -m tradingagents.strategies.bruni

Pre-registered: the rules, parameters, samples and adoption test below were written and committed
before the first run on market data. Every variant is reported; none is picked after the fact.

The post (user's summary): 1 market filter: ATR percentile 51-75%, volatility regime no older than
30 bars; 2 direction from the value area, structure highs/lows as boundaries; 3 entry: pullback to
the value area, engulfing candle of sufficient size, volume requirement; 4 enter at the signal
bar's close, stop at that bar's low, fixed 1:2, flat at the structure high; 5 skip the signal after
a losing trade, five-question score -> Kelly size; 6 test on two samples, drop the rule if the
expectancy falls by more than half.

Our reading, one number per vague term, fixed in advance:
Bars       15-minute regular-session bars (main test); 5-minute bars reported as a second test.
ATR        14 bars; true range within the session (a day's first bar uses high - low).
Filter     ATR percentile among the previous 20 sessions of bars in [51%, 75%], and the run of
           consecutive bars with percentile above 50% is 30 bars or shorter (a fresh expansion).
Value area prior session's 70% volume profile (VAH / VAL) from 1-minute bars.
Direction  long when at least 2 of the 4 previous bars of the session closed above VAH;
           short when at least 2 of them closed below VAL.
Pullback   long: bar low at or below VAH + 0.25 ATR and close above VAH (short mirrored on VAL).
Engulfing  bullish bar after a bearish bar, its body covering the previous body, body >= 0.5 ATR.
Volume     bar volume >= 1.2x the median of the same time slot over the previous 20 sessions.
Structure  swing high = a bar's high above the 2 bars on each side, known 2 bars later. The nearest
           swing high above entry (this or the previous session) must be >= 2R away, or none
           exists (short mirrored with swing lows).
Trade      enter at the signal bar's close; stop at its low (long) / high (short); target 2R; a
           bar touching both counts as a stop; flat at the session's last bar. Signal bars from
           the second bar of the session to the bar ending 15:00. One position per symbol.
           Slippage 0.002% of price per fill (about 1 cent on SPY); stress test 0.01%.
Skip       after a losing trade in a symbol, that symbol's next signal is not taken.
Score      five yes/no questions: body >= 1 ATR; volume >= 2x; prior close on the trade side of its
           20-day average; the session opened outside value on the trade side; entry before 12:00.
Kelly      win rate and payoff by score bucket (0-2, 3, 4-5) measured in sample A; half Kelly,
           capped at 1% of equity at risk per trade, applied unchanged in sample B. Compared with a
           fixed 0.5% risk per trade.
Samples    A 2018-10..2022-09, B 2022-10..2026-10.
Adopt      only if the average R after costs is > 0 in both samples, B is at least half of A, the
           pooled t-stat is >= 2, and each sample has >= 30 trades; only then is it tested in the
           live book (core + add-on).
Controls   each ingredient removed one at a time; direction + pullback with no candle or volume
           condition; the same exits from every bar that has a direction (the base rate).
```

## 15-minute bars

### Every variant: taken trades, R after costs, by sample

|                                                                    |   trades |   per year |   win % |   avg R |       t |   total R |
|:-------------------------------------------------------------------|---------:|-----------:|--------:|--------:|--------:|----------:|
| ('rules as posted', 'A 2018-10..2022-09')                          |        7 |      1.751 |  28.571 |  -0.429 |  -0.992 |    -3.003 |
| ('rules as posted', 'B 2022-10..2026-10')                          |        5 |      1.225 |  60     |   0.63  |   0.918 |     3.151 |
| ('no ATR band', 'A 2018-10..2022-09')                              |       18 |      4.503 |  22.222 |  -0.596 |  -4.413 |   -10.722 |
| ('no ATR band', 'B 2022-10..2026-10')                              |       11 |      2.695 |  36.364 |  -0.024 |  -0.062 |    -0.265 |
| ('no freshness (30 bars)', 'A 2018-10..2022-09')                   |        7 |      1.751 |  28.571 |  -0.429 |  -0.992 |    -3.003 |
| ('no freshness (30 bars)', 'B 2022-10..2026-10')                   |        6 |      1.47  |  66.667 |   0.76  |   1.321 |     4.56  |
| ('no ATR filter at all', 'A 2018-10..2022-09')                     |       24 |      6.004 |  12.5   |  -0.631 |  -3.851 |   -15.142 |
| ('no ATR filter at all', 'B 2022-10..2026-10')                     |       20 |      4.899 |  55     |   0.278 |   0.996 |     5.56  |
| ('any engulfing size', 'A 2018-10..2022-09')                       |        9 |      2.252 |  33.333 |  -0.307 |  -0.786 |    -2.761 |
| ('any engulfing size', 'B 2022-10..2026-10')                       |        4 |      0.98  |  50     |   0.29  |   0.376 |     1.158 |
| ('no volume rule', 'A 2018-10..2022-09')                           |       14 |      3.502 |  28.571 |  -0.295 |  -0.867 |    -4.125 |
| ('no volume rule', 'B 2022-10..2026-10')                           |       14 |      3.43  |  50     |   0.27  |   0.729 |     3.782 |
| ('no structure room', 'A 2018-10..2022-09')                        |       18 |      4.503 |  44.444 |  -0.077 |  -0.271 |    -1.39  |
| ('no structure room', 'B 2022-10..2026-10')                        |       14 |      3.43  |  42.857 |   0.175 |   0.483 |     2.453 |
| ('no skip after loss', 'A 2018-10..2022-09')                       |       10 |      2.502 |  30     |  -0.376 |  -1.057 |    -3.762 |
| ('no skip after loss', 'B 2022-10..2026-10')                       |        8 |      1.96  |  62.5   |   0.539 |   1.206 |     4.315 |
| ('slippage 0.01% per fill', 'A 2018-10..2022-09')                  |        7 |      1.751 |  28.571 |  -0.492 |  -1.13  |    -3.446 |
| ('slippage 0.01% per fill', 'B 2022-10..2026-10')                  |        5 |      1.225 |  60     |   0.569 |   0.829 |     2.847 |
| ('direction + pullback, no candle / volume', 'A 2018-10..2022-09') |      221 |     55.288 |  23.982 |  -0.414 |  -4.723 |   -91.406 |
| ('direction + pullback, no candle / volume', 'B 2022-10..2026-10') |      216 |     52.913 |  29.63  |  -0.268 |  -2.904 |   -57.896 |
| ('base rate: every bar with a direction', 'A 2018-10..2022-09')    |    12990 |   3249.72  |  30.077 |  -0.218 | -18.128 | -2826.29  |
| ('base rate: every bar with a direction', 'B 2022-10..2026-10')    |    12613 |   3089.8   |  29.668 |  -0.264 | -17.674 | -3326.32  |

### Adoption test per variant

|                                          |    A avg R |    B avg R |   B / A |    pooled t |   passes |
|:-----------------------------------------|-----------:|-----------:|--------:|------------:|---------:|
| rules as posted                          | -0.428949  |  0.6302    |     nan |   0.0313377 |        0 |
| no ATR band                              | -0.595642  | -0.0240879 |     nan |  -2.18103   |        0 |
| no freshness (30 bars)                   | -0.428949  |  0.760062  |     nan |   0.316602  |        0 |
| no ATR filter at all                     | -0.630908  |  0.278021  |     nan |  -1.2958    |        0 |
| any engulfing size                       | -0.30683   |  0.289609  |     nan |  -0.352772  |        0 |
| no volume rule                           | -0.294617  |  0.270178  |     nan |  -0.0483689 |        0 |
| no structure room                        | -0.0772405 |  0.175204  |     nan |   0.148937  |        0 |
| no skip after loss                       | -0.376242  |  0.539322  |     nan |   0.104562  |        0 |
| slippage 0.01% per fill                  | -0.492333  |  0.569438  |     nan |  -0.126042  |        0 |
| direction + pullback, no candle / volume | -0.413601  | -0.268036  |     nan |  -5.37133   |        0 |
| base rate: every bar with a direction    | -0.217574  | -0.263721  |     nan | -25.1721    |        0 |

### Skip-after-loss: the skipped signals

|                    |   trades |   per year |   win % |   avg R |      t |   total R |
|:-------------------|---------:|-----------:|--------:|--------:|-------:|----------:|
| A 2018-10..2022-09 |        3 |      0.751 |  33.333 |  -0.253 | -0.332 |    -0.76  |
| B 2022-10..2026-10 |        3 |      0.735 |  66.667 |   0.388 |  0.735 |     1.164 |

### By symbol and side (taken, both samples)

|           |   trades |   per year |   win % |   avg R |         t |   total R |
|:----------|---------:|-----------:|--------:|--------:|----------:|----------:|
| IWM short |        1 |      0.125 |     100 |   1.978 |   nan     |     1.978 |
| IWM long  |        2 |      0.25  |       0 |  -1.023 |  -338.866 |    -2.046 |
| QQQ short |        2 |      0.25  |       0 |  -1.006 | -1240.82  |    -2.011 |
| QQQ long  |        4 |      0.5   |      75 |   1.038 |     1.449 |     4.15  |
| SPY short |        2 |      0.25  |      50 |  -0.453 |    -0.817 |    -0.907 |
| SPY long  |        1 |      0.125 |       0 |  -1.016 |   nan     |    -1.016 |

### By score bucket (taken)

|                               |   trades |   per year |   win % |   avg R |       t |   total R |
|:------------------------------|---------:|-----------:|--------:|--------:|--------:|----------:|
| ('0-2', 'A 2018-10..2022-09') |        6 |      1.501 |  16.667 |  -0.831 |  -4.455 |    -4.988 |
| ('3', 'A 2018-10..2022-09')   |        1 |      0.25  | 100     |   1.986 | nan     |     1.986 |
| ('4-5', 'A 2018-10..2022-09') |        0 |    nan     | nan     | nan     | nan     |   nan     |
| ('0-2', 'B 2022-10..2026-10') |        3 |      0.735 |  33.333 |  -0.018 |  -0.018 |    -0.053 |
| ('3', 'B 2022-10..2026-10')   |        2 |      0.49  | 100     |   1.602 |   4.101 |     3.204 |
| ('4-5', 'B 2022-10..2026-10') |        0 |    nan     | nan     | nan     | nan     |   nan     |

### Exit reasons (taken)

| why    |   count |
|:-------|--------:|
| stop   |       7 |
| target |       3 |
| close  |       2 |

### Sizing in sample B: fixed 0.5% risk vs five-question half Kelly (fitted on A)

Kelly risk per bucket from A: {'0-2': 0.0, '3': 0.0}

|                     |   Sharpe |   ann % |   trades |   trades sized > 0 |
|:--------------------|---------:|--------:|---------:|-------------------:|
| fixed 0.5% risk     |    0.454 |   0.373 |        5 |                nan |
| half Kelly by score |  nan     |   0     |      nan |                  0 |

## 5-minute bars

### Every variant: taken trades, R after costs, by sample

|                                                                    |   trades |   per year |   win % |   avg R |        t |    total R |
|:-------------------------------------------------------------------|---------:|-----------:|--------:|--------:|---------:|-----------:|
| ('rules as posted', 'A 2018-10..2022-09')                          |        4 |      1.001 |   0     |  -1.037 |  -69.667 |     -4.15  |
| ('rules as posted', 'B 2022-10..2026-10')                          |        4 |      0.98  |   0     |  -1.025 | -105.882 |     -4.098 |
| ('no ATR band', 'A 2018-10..2022-09')                              |       14 |      3.502 |  28.571 |  -0.159 |   -0.423 |     -2.225 |
| ('no ATR band', 'B 2022-10..2026-10')                              |       13 |      3.185 |   0     |  -0.956 |  -14.633 |    -12.432 |
| ('no freshness (30 bars)', 'A 2018-10..2022-09')                   |        5 |      1.251 |  20     |  -0.433 |   -0.717 |     -2.166 |
| ('no freshness (30 bars)', 'B 2022-10..2026-10')                   |        6 |      1.47  |   0     |  -1.026 | -147.728 |     -6.159 |
| ('no ATR filter at all', 'A 2018-10..2022-09')                     |       30 |      7.505 |  26.667 |  -0.306 |   -1.338 |     -9.194 |
| ('no ATR filter at all', 'B 2022-10..2026-10')                     |       27 |      6.614 |  11.111 |  -0.69  |   -3.728 |    -18.617 |
| ('any engulfing size', 'A 2018-10..2022-09')                       |        5 |      1.251 |   0     |  -1.035 |  -82.81  |     -5.174 |
| ('any engulfing size', 'B 2022-10..2026-10')                       |        6 |      1.47  |   0     |  -1.024 | -159.957 |     -6.144 |
| ('no volume rule', 'A 2018-10..2022-09')                           |       13 |      3.252 |  15.385 |  -0.567 |   -1.818 |     -7.376 |
| ('no volume rule', 'B 2022-10..2026-10')                           |       16 |      3.92  |  12.5   |  -0.65  |   -2.536 |    -10.397 |
| ('no structure room', 'A 2018-10..2022-09')                        |       27 |      6.755 |  22.222 |  -0.434 |   -1.896 |    -11.71  |
| ('no structure room', 'B 2022-10..2026-10')                        |       29 |      7.104 |  31.034 |  -0.217 |   -0.906 |     -6.302 |
| ('no skip after loss', 'A 2018-10..2022-09')                       |        5 |      1.251 |   0     |  -1.032 |  -81.913 |     -5.162 |
| ('no skip after loss', 'B 2022-10..2026-10')                       |       10 |      2.45  |  20     |  -0.422 |   -1.058 |     -4.221 |
| ('slippage 0.01% per fill', 'A 2018-10..2022-09')                  |        4 |      1.001 |   0     |  -1.187 |  -15.946 |     -4.749 |
| ('slippage 0.01% per fill', 'B 2022-10..2026-10')                  |        4 |      0.98  |   0     |  -1.123 |  -23.204 |     -4.49  |
| ('direction + pullback, no candle / volume', 'A 2018-10..2022-09') |      290 |     72.55  |  26.207 |  -0.389 |   -4.769 |   -112.729 |
| ('direction + pullback, no candle / volume', 'B 2022-10..2026-10') |      250 |     61.242 |  26     |  -0.432 |   -4.923 |   -107.997 |
| ('base rate: every bar with a direction', 'A 2018-10..2022-09')    |    37150 |   9293.86  |  28.961 |  -0.277 |  -38.1   | -10301.9   |
| ('base rate: every bar with a direction', 'B 2022-10..2026-10')    |    37024 |   9069.76  |  29.108 |  -0.299 |  -40.324 | -11076.4   |

### Adoption test per variant

|                                          |   A avg R |   B avg R |   B / A |   pooled t |   passes |
|:-----------------------------------------|----------:|----------:|--------:|-----------:|---------:|
| rules as posted                          | -1.03746  | -1.02452  |     nan | -120.21    |        0 |
| no ATR band                              | -0.158953 | -0.95633  |     nan |   -2.59911 |        0 |
| no freshness (30 bars)                   | -0.433219 | -1.02648  |     nan |   -2.76081 |        0 |
| no ATR filter at all                     | -0.306458 | -0.689509 |     nan |   -3.2545  |        0 |
| any engulfing size                       | -1.03472  | -1.02405  |     nan | -158.035   |        0 |
| no volume rule                           | -0.567366 | -0.649812 |     nan |   -3.13658 |        0 |
| no structure room                        | -0.433719 | -0.217327 |     nan |   -1.94665 |        0 |
| no skip after loss                       | -1.03238  | -0.422134 |     nan |   -2.29663 |        0 |
| slippage 0.01% per fill                  | -1.18729  | -1.12262  |     nan |  -26.9327  |        0 |
| direction + pullback, no candle / volume | -0.388719 | -0.431988 |     nan |   -6.85012 |        0 |
| base rate: every bar with a direction    | -0.277306 | -0.299168 |     nan |  -55.4633  |        0 |

### Skip-after-loss: the skipped signals

|                    |   trades |   per year |   win % |   avg R |       t |   total R |
|:-------------------|---------:|-----------:|--------:|--------:|--------:|----------:|
| A 2018-10..2022-09 |        1 |       0.25 |   0     |  -1.012 | nan     |    -1.012 |
| B 2022-10..2026-10 |        6 |       1.47 |  33.333 |  -0.021 |  -0.033 |    -0.123 |

### By symbol and side (taken, both samples)

|           |   trades |   per year |   win % |   avg R |        t |   total R |
|:----------|---------:|-----------:|--------:|--------:|---------:|----------:|
| IWM short |        1 |      0.125 |       0 |  -1.025 |  nan     |    -1.025 |
| IWM long  |        1 |      0.125 |       0 |  -1.018 |  nan     |    -1.018 |
| QQQ short |        2 |      0.25  |       0 |  -1.045 |  -28.779 |    -2.091 |
| QQQ long  |        2 |      0.25  |       0 |  -1.019 | -158.75  |    -2.038 |
| SPY short |        1 |      0.125 |       0 |  -1.025 |  nan     |    -1.025 |
| SPY long  |        1 |      0.125 |       0 |  -1.052 |  nan     |    -1.052 |

### By score bucket (taken)

|                               |   trades |   per year |   win % |   avg R |       t |   total R |
|:------------------------------|---------:|-----------:|--------:|--------:|--------:|----------:|
| ('0-2', 'A 2018-10..2022-09') |        4 |      1.001 |       0 |  -1.037 | -69.667 |    -4.15  |
| ('3', 'A 2018-10..2022-09')   |        0 |    nan     |     nan | nan     | nan     |   nan     |
| ('4-5', 'A 2018-10..2022-09') |        0 |    nan     |     nan | nan     | nan     |   nan     |
| ('0-2', 'B 2022-10..2026-10') |        2 |      0.49  |       0 |  -1.032 | -52.581 |    -2.064 |
| ('3', 'B 2022-10..2026-10')   |        1 |      0.245 |       0 |  -1.009 | nan     |    -1.009 |
| ('4-5', 'B 2022-10..2026-10') |        1 |      0.245 |       0 |  -1.025 | nan     |    -1.025 |

### Exit reasons (taken)

| why   |   count |
|:------|--------:|
| stop  |       8 |

### Sizing in sample B: fixed 0.5% risk vs five-question half Kelly (fitted on A)

Kelly risk per bucket from A: {'0-2': 0.0}

|                     |   Sharpe |   ann % |   trades |   trades sized > 0 |
|:--------------------|---------:|--------:|---------:|-------------------:|
| fixed 0.5% risk     |   -0.974 |  -0.485 |        4 |                nan |
| half Kelly by score |  nan     |   0     |      nan |                  0 |


## Post-hoc diagnostics (written after seeing the results above; not used for adoption)

The rules as posted produce 12 trades in 8 years on 15-minute bars (8 on 5-minute), too few to test.
These loosen the rules to see whether the core idea (pullback to yesterday's value area in the
direction of acceptance, entered on an engulfing candle) has any edge with enough trades. The
pre-registered controls without a candle are distorted: a bar that closes near its low gives a
stop of a few cents, so slippage and gaps dominate R. C1/C2 put the stop at least 0.5 ATR away.

|                                                                              |   trades |   per year |   win % |   avg R |      t |   total R |
|:-----------------------------------------------------------------------------|---------:|-----------:|--------:|--------:|-------:|----------:|
| ('15m', 'D1 direction + pullback + any engulfing (nothing else)', 'A')       |      584 |    146.1   |  40.582 |   0.073 |  1.308 |    42.432 |
| ('15m', 'D1 direction + pullback + any engulfing (nothing else)', 'B')       |      556 |    136.203 |  36.151 |  -0.042 | -0.77  |   -23.59  |
| ('15m', 'D2 D1 + volume >= 1.2x', 'A')                                       |      200 |     50.034 |  39     |   0.017 |  0.191 |     3.47  |
| ('15m', 'D2 D1 + volume >= 1.2x', 'B')                                       |      134 |     32.826 |  45.522 |   0.143 |  1.325 |    19.21  |
| ('15m', 'D3 D1 + body >= 0.5 ATR', 'A')                                      |      382 |     95.565 |  41.623 |   0.058 |  0.884 |    22.284 |
| ('15m', 'D3 D1 + body >= 0.5 ATR', 'B')                                      |      335 |     82.065 |  37.91  |  -0.047 | -0.693 |   -15.616 |
| ('15m', 'D4 D1 but stop >= 0.5 ATR away', 'A')                               |      582 |    145.6   |  40.722 |   0.078 |  1.396 |    45.173 |
| ('15m', 'D4 D1 but stop >= 0.5 ATR away', 'B')                               |      555 |    135.958 |  36.757 |  -0.025 | -0.451 |   -13.868 |
| ('15m', 'C1 control: direction + pullback, no candle, stop >= 0.5 ATR', 'A') |     2515 |    629.181 |  35.507 |  -0.008 | -0.294 |   -20.322 |
| ('15m', 'C1 control: direction + pullback, no candle, stop >= 0.5 ATR', 'B') |     2607 |    638.636 |  34.1   |  -0.083 | -3.211 |  -217.278 |
| ('15m', 'C2 control: every bar with a direction, stop >= 0.5 ATR', 'A')      |    11202 |   2802.42  |  35.012 |  -0.012 | -0.95  |  -139.682 |
| ('15m', 'C2 control: every bar with a direction, stop >= 0.5 ATR', 'B')      |    10997 |   2693.93  |  35.119 |  -0.025 | -1.936 |  -278.809 |
| ('5m', 'D1 direction + pullback + any engulfing (nothing else)', 'A')        |     1161 |    290.449 |  31.352 |  -0.118 | -2.944 |  -137.362 |
| ('5m', 'D1 direction + pullback + any engulfing (nothing else)', 'B')        |     1223 |    299.598 |  31.398 |  -0.126 | -3.246 |  -154.001 |
| ('5m', 'D2 D1 + volume >= 1.2x', 'A')                                        |      417 |    104.321 |  31.655 |  -0.119 | -1.811 |   -49.653 |
| ('5m', 'D2 D1 + volume >= 1.2x', 'B')                                        |      404 |     98.968 |  32.673 |  -0.087 | -1.29  |   -35.056 |
| ('5m', 'D3 D1 + body >= 0.5 ATR', 'A')                                       |      803 |    200.888 |  30.76  |  -0.136 | -2.846 |  -108.947 |
| ('5m', 'D3 D1 + body >= 0.5 ATR', 'B')                                       |      860 |    210.674 |  32.791 |  -0.087 | -1.885 |   -75.186 |
| ('5m', 'D4 D1 but stop >= 0.5 ATR away', 'A')                                |     1157 |    289.448 |  31.634 |  -0.108 | -2.669 |  -124.572 |
| ('5m', 'D4 D1 but stop >= 0.5 ATR away', 'B')                                |     1217 |    298.128 |  31.553 |  -0.119 | -3.061 |  -145.065 |
| ('5m', 'C1 control: direction + pullback, no candle, stop >= 0.5 ATR', 'A')  |     4830 |   1208.33  |  33.126 |  -0.064 | -3.201 |  -311.314 |
| ('5m', 'C1 control: direction + pullback, no candle, stop >= 0.5 ATR', 'B')  |     5085 |   1245.67  |  33.333 |  -0.063 | -3.193 |  -318.612 |
| ('5m', 'C2 control: every bar with a direction, stop >= 0.5 ATR', 'A')       |    33880 |   8475.8   |  34.109 |  -0.037 | -4.741 | -1237.28  |
| ('5m', 'C2 control: every bar with a direction, stop >= 0.5 ATR', 'B')       |    33397 |   8181.26  |  33.994 |  -0.046 | -5.887 | -1521.23  |
