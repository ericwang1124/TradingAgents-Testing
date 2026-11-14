# More equity indices in the core portfolio

```
Do more (and less correlated) equity indices improve the live core portfolio?

    python -m tradingagents.strategies.equity_indices

Candidates are US-listed country / region / US-size ETFs (all tradable on the paper account).
Rules, fixed before running:

  A. long each index (excess over T-bills)
  B. trend: long each index while it is above its 200-day average, else cash
  C. three country composites, long-only:
     - country momentum: on the first session of each month hold the 5 countries with the best
       12-1 month return, equal weight (needs >= 10 countries with history)
     - country TSMOM: every country with a positive 12-month return, risk-weighted (10% vol / N)
     - country risk parity: inverse 60-day-vol weights across all countries
  D. A + B + C together

Each block is added to the core portfolio's strategy list and the whole book is rerun exactly as
live (weights refit each January on earlier years only, 2x leverage, gross <= 2, long-only, 2 bp per
unit of turnover). A block is adopted only if the book's Sharpe improves in every period:
2011-26, 2011-18, 2019-26 and 2024-05 onward.

Also reported: each candidate's own Sharpe and its weekly correlation with the core book, and the
high-efficiency open continuation add-on run on QQQ and IWM besides SPY (long side, 2021+).
```

## Core book with each block added

|                         |   2011-26 |   2011-18 |   2019-26 |   2024-05+ |   2022 |   ann % |   maxDD % |
|:------------------------|----------:|----------:|----------:|-----------:|-------:|--------:|----------:|
| baseline (live core)    |      0.8  |      0.63 |      0.96 |       1.01 |  -1.26 |    9.3  |    -25.36 |
| A. long each index      |      0.57 |      0.43 |      0.7  |       0.89 |  -1.22 |    6.79 |    -28.19 |
| B. trend (above SMA200) |      0.56 |      0.42 |      0.69 |       0.87 |  -1.85 |    6.04 |    -25.45 |
| C. country composites   |      0.78 |      0.6  |      0.94 |       1    |  -1.26 |    9.06 |    -25.89 |
| D. A + B + C            |      0.46 |      0.34 |      0.56 |       0.79 |  -1.62 |    5.07 |    -30.84 |

|                         |   risk budget to new strategies, 2026 |   new strategies with weight > 0, 2026 |   of |
|:------------------------|--------------------------------------:|---------------------------------------:|-----:|
| A. long each index      |                                  0.36 |                                     31 |   35 |
| B. trend (above SMA200) |                                  0.41 |                                     25 |   35 |
| C. country composites   |                                  0.04 |                                      3 |    3 |
| D. A + B + C            |                                  0.56 |                                     59 |   73 |

## Verdict

- A. long each index: **reject**
- B. trend (above SMA200): **reject**
- C. country composites: **reject**
- D. A + B + C: **reject**

## Candidates: own Sharpe and correlation (2011-26, weekly)

| strategy                             | start      |   Sharpe 2011-26 |   weekly corr with core |   weekly corr with SPY |   weight 2026 |
|:-------------------------------------|:-----------|-----------------:|------------------------:|-----------------------:|--------------:|
| long Dow 30 DIA                      | 2007-06-04 |             0.7  |                    0.67 |                   0.95 |          0.02 |
| long Taiwan EWT                      | 2007-06-04 |             0.55 |                    0.58 |                   0.67 |          0.02 |
| long US mid caps MDY                 | 2007-06-04 |             0.53 |                    0.67 |                   0.91 |          0.01 |
| trend Dow 30 DIA                     | 2007-06-04 |             0.52 |                    0.59 |                   0.69 |          0.02 |
| long US small caps (S&P 600) IJR     | 2007-06-04 |             0.52 |                    0.63 |                   0.85 |          0.01 |
| long Switzerland EWL                 | 2007-06-04 |             0.48 |                    0.61 |                   0.75 |          0.01 |
| long Netherlands EWN                 | 2007-06-04 |             0.47 |                    0.62 |                   0.81 |          0.01 |
| trend US small caps (S&P 600) IJR    | 2007-06-04 |             0.44 |                    0.52 |                   0.52 |          0    |
| trend Taiwan EWT                     | 2007-06-04 |             0.44 |                    0.47 |                   0.41 |          0.02 |
| trend Netherlands EWN                | 2007-06-04 |             0.42 |                    0.51 |                   0.48 |          0.01 |
| long developed ex-US small caps SCZ  | 2007-12-13 |             0.4  |                    0.65 |                   0.84 |          0.01 |
| trend developed ex-US small caps SCZ | 2007-12-13 |             0.39 |                    0.53 |                   0.51 |          0.02 |
| trend Poland EPOL                    | 2010-05-27 |             0.39 |                    0.32 |                   0.3  |          0    |
| long Europe VGK                      | 2007-06-04 |             0.38 |                    0.61 |                   0.82 |          0.01 |
| trend US mid caps MDY                | 2007-06-04 |             0.38 |                    0.57 |                   0.58 |          0.01 |
| trend South Korea EWY                | 2007-06-04 |             0.37 |                    0.38 |                   0.34 |          0.02 |
| long Japan EWJ                       | 2007-06-04 |             0.37 |                    0.56 |                   0.71 |          0.01 |
| trend Switzerland EWL                | 2007-06-04 |             0.37 |                    0.53 |                   0.47 |          0.01 |
| trend Spain EWP                      | 2007-06-04 |             0.36 |                    0.33 |                   0.34 |          0    |
| long Canada EWC                      | 2007-06-04 |             0.35 |                    0.65 |                   0.81 |          0.01 |
| long Spain EWP                       | 2007-06-04 |             0.34 |                    0.45 |                   0.66 |          0    |
| trend Germany EWG                    | 2007-06-04 |             0.34 |                    0.44 |                   0.46 |          0.01 |
| long Sweden EWD                      | 2007-06-04 |             0.34 |                    0.59 |                   0.79 |          0.01 |
| long South Korea EWY                 | 2007-06-04 |             0.34 |                    0.54 |                   0.64 |          0    |
| long France EWQ                      | 2007-06-04 |             0.34 |                    0.54 |                   0.77 |          0.01 |
| long Italy EWI                       | 2007-06-04 |             0.33 |                    0.47 |                   0.69 |          0    |
| trend Italy EWI                      | 2007-06-04 |             0.33 |                    0.41 |                   0.41 |          0    |
| long UK EWU                          | 2007-06-04 |             0.33 |                    0.59 |                   0.79 |          0.01 |
| long Argentina ARGT                  | 2011-03-04 |             0.33 |                    0.49 |                   0.58 |          0.01 |
| long Germany EWG                     | 2007-06-04 |             0.32 |                    0.56 |                   0.78 |          0.01 |
| trend Argentina ARGT                 | 2011-03-04 |             0.31 |                    0.37 |                   0.33 |          0.01 |
| country momentum: top 5 of 12-1m     | 2007-06-04 |             0.31 |                    0.62 |                   0.74 |          0.01 |
| long India INDA                      | 2012-02-06 |             0.29 |                    0.43 |                   0.56 |          0.01 |
| country risk parity                  | 2007-06-04 |             0.29 |                    0.65 |                   0.82 |          0.01 |
| long Australia EWA                   | 2007-06-04 |             0.28 |                    0.62 |                   0.78 |          0    |
| long Singapore EWS                   | 2007-06-04 |             0.26 |                    0.52 |                   0.69 |          0.01 |
| trend Canada EWC                     | 2007-06-04 |             0.25 |                    0.53 |                   0.48 |          0.01 |
| long Hong Kong EWH                   | 2007-06-04 |             0.25 |                    0.41 |                   0.53 |          0.01 |
| long Poland EPOL                     | 2010-05-27 |             0.25 |                    0.49 |                   0.6  |          0    |
| long Mexico EWW                      | 2007-06-04 |             0.21 |                    0.49 |                   0.61 |          0    |
| long South Africa EZA                | 2007-06-04 |             0.21 |                    0.53 |                   0.61 |          0.01 |
| trend Singapore EWS                  | 2007-06-04 |             0.21 |                    0.38 |                   0.36 |          0.02 |
| trend Hong Kong EWH                  | 2007-06-04 |             0.19 |                    0.27 |                   0.29 |          0.01 |
| long Thailand THD                    | 2008-04-02 |             0.18 |                    0.49 |                   0.53 |          0.01 |
| trend France EWQ                     | 2007-06-04 |             0.18 |                    0.42 |                   0.44 |          0    |
| trend Europe VGK                     | 2007-06-04 |             0.18 |                    0.49 |                   0.49 |          0    |
| trend Thailand THD                   | 2008-04-02 |             0.15 |                    0.24 |                   0.24 |          0.02 |
| country TSMOM (long-only)            | 2007-06-04 |             0.15 |                    0.61 |                   0.55 |          0.01 |
| long China MCHI                      | 2011-04-01 |             0.14 |                    0.42 |                   0.52 |          0.01 |
| trend Sweden EWD                     | 2007-06-04 |             0.14 |                    0.47 |                   0.46 |          0.01 |
| trend UK EWU                         | 2007-06-04 |             0.13 |                    0.44 |                   0.43 |          0.01 |
| trend India INDA                     | 2012-02-06 |             0.12 |                    0.34 |                   0.29 |          0    |
| long China large caps FXI            | 2007-06-04 |             0.11 |                    0.4  |                   0.51 |          0.01 |
| trend China MCHI                     | 2011-04-01 |             0.1  |                    0.32 |                   0.33 |          0.01 |
| trend Japan EWJ                      | 2007-06-04 |             0.1  |                    0.43 |                   0.41 |          0    |
| trend Australia EWA                  | 2007-06-04 |             0.1  |                    0.46 |                   0.43 |          0    |
| long Brazil EWZ                      | 2007-06-04 |             0.09 |                    0.39 |                   0.5  |          0    |
| long Philippines EPHE                | 2010-09-30 |             0.07 |                    0.42 |                   0.52 |          0    |
| long Turkey TUR                      | 2008-03-31 |             0.06 |                    0.29 |                   0.36 |          0    |
| trend Mexico EWW                     | 2007-06-04 |             0.03 |                    0.36 |                   0.35 |          0.01 |
| long Malaysia EWM                    | 2007-06-04 |             0.03 |                    0.45 |                   0.56 |          0    |
| long Vietnam VNM                     | 2009-08-17 |             0.02 |                    0.42 |                   0.47 |          0    |
| trend China large caps FXI           | 2007-06-04 |             0.01 |                    0.28 |                   0.3  |          0.01 |
| long Chile ECH                       | 2007-11-21 |            -0.03 |                    0.44 |                   0.52 |          0    |
| trend Vietnam VNM                    | 2009-08-17 |            -0.04 |                    0.28 |                   0.24 |          0.02 |
| long Indonesia EIDO                  | 2010-05-10 |            -0.08 |                    0.41 |                   0.53 |          0    |
| trend Chile ECH                      | 2007-11-21 |            -0.1  |                    0.28 |                   0.26 |          0.01 |
| trend Brazil EWZ                     | 2007-06-04 |            -0.12 |                    0.28 |                   0.23 |          0.02 |
| trend Turkey TUR                     | 2008-03-31 |            -0.18 |                    0.17 |                   0.16 |          0    |
| trend Malaysia EWM                   | 2007-06-04 |            -0.2  |                    0.26 |                   0.28 |          0    |
| trend Philippines EPHE               | 2010-09-30 |            -0.2  |                    0.26 |                   0.27 |          0.01 |
| trend Indonesia EIDO                 | 2010-05-10 |            -0.36 |                    0.26 |                   0.27 |          0    |
| trend South Africa EZA               | 2007-06-04 |            -0.37 |                    0.36 |                   0.31 |          0    |

## Intraday high-efficiency continuation on other indices (long side, 2021+)

- SPY only, 1x: Sharpe 0.96
- QQQ only, 1x: Sharpe 0.54
- IWM only, 1x: Sharpe 0.17
- SPY + QQQ + IWM, 1/3x each: Sharpe 0.66
- core + SPY add-on 1x: Sharpe 0.94
- core + 3-index add-on 1/3x each: Sharpe 0.88

Trade days: SPY 265, QQQ 269, IWM 233

Correlation of add-on returns on days both trade:

|     |   SPY |   QQQ |   IWM |
|:----|------:|------:|------:|
| SPY |  1    |  0.93 |  0.81 |
| QQQ |  0.93 |  1    |  0.77 |
| IWM |  0.81 |  0.77 |  1    |
