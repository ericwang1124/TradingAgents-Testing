# Which strategies to apply when — walk-forward selector

Each January a model is fitted on earlier years only; each day it goes long the strategies with a positive expected next-day return given today's scenario states (cash if none), 2 bp per unit of weight traded. Every strategy is scaled to 10% vol. Baselines: equal risk in all strategies, and the same weighting without scenario information.

## Daily strategies only (2011-2026 out of sample)

|                                            |   Sharpe 2011-26 |   Sharpe 2011-18 |   Sharpe 2019-26 |   Sharpe 2022 |   Sharpe 2024-05+ |   ann_ret_% |   max_dd_% |   avg # strategies |   daily turnover |
|:-------------------------------------------|-----------------:|-----------------:|-----------------:|--------------:|------------------:|------------:|-----------:|-------------------:|-----------------:|
| static: equal risk, all strategies         |             0.69 |             0.61 |             0.78 |         -0.71 |              1.01 |        2.80 |      -8.83 |              35.63 |             0.00 |
| selector: no-scenario baseline (past mean) |             0.88 |             0.76 |             1.00 |         -1.25 |              1.07 |        5.52 |     -14.11 |              25.25 |             0.00 |
| selector: ridge lambda=1e3                 |             0.48 |             0.47 |             0.49 |         -0.57 |              0.55 |        3.02 |     -19.93 |              20.19 |             0.53 |
| selector: ridge lambda=1e4                 |             0.75 |             0.67 |             0.82 |         -1.50 |              0.96 |        4.81 |     -14.94 |              24.97 |             0.17 |
| selector: shrunk k=250                     |             0.85 |             0.73 |             0.95 |         -1.30 |              1.04 |        5.43 |     -14.42 |              25.03 |             0.05 |
| selector: shrunk k=1000                    |             0.86 |             0.74 |             0.97 |         -1.29 |              1.05 |        5.47 |     -14.32 |              25.07 |             0.03 |

## All strategies incl. SPY intraday (2021-2026 out of sample)

|                                            |   Sharpe 2021-26 |   Sharpe 2021-23 |   Sharpe 2024-26 |   Sharpe 2022 |   Sharpe 2024-05+ |   ann_ret_% |   max_dd_% |   avg # strategies |   daily turnover |
|:-------------------------------------------|-----------------:|-----------------:|-----------------:|--------------:|------------------:|------------:|-----------:|-------------------:|-----------------:|
| static: equal risk, all strategies         |             0.89 |             0.69 |             1.09 |         -0.56 |              1.09 |        3.29 |      -4.92 |              40.93 |             0.00 |
| selector: no-scenario baseline (past mean) |             1.06 |             0.87 |             1.23 |         -1.14 |              1.18 |        6.01 |      -8.61 |              28.79 |             0.01 |
| selector: ridge lambda=1e3                 |             0.88 |             0.83 |             0.93 |         -0.07 |              0.76 |        5.12 |      -8.63 |              23.42 |             0.54 |
| selector: ridge lambda=1e4                 |             1.00 |             0.77 |             1.21 |         -1.20 |              1.13 |        5.83 |      -9.43 |              29.23 |             0.20 |
| selector: shrunk k=250                     |             1.05 |             0.86 |             1.23 |         -1.14 |              1.17 |        6.08 |      -8.85 |              28.97 |             0.05 |
| selector: shrunk k=1000                    |             1.05 |             0.86 |             1.23 |         -1.15 |              1.17 |        6.04 |      -8.80 |              28.84 |             0.03 |

## Today's view (shrunk model, trained on all history before today)

| strategy                                    |   unconditional Sharpe |   scenario-adjusted Sharpe (approx.) | main drivers                                                                                                                                                      |
|:--------------------------------------------|-----------------------:|-------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| intraday: full-day noise-area momentum      |                   0.92 |                                 0.99 | yield curve 3-month change=flattening (+0.54); copper/gold ratio vs SMA50=rising (growth) (+0.49); bitcoin 1-month move=normal (+0.45)                            |
| long bitcoin                                |                   0.97 |                                 0.87 | yield curve 10y-2y level=flat 0-0.5 (-0.74); VIX level=15-20 (-0.67); oil (WTI) 1-month move=normal (+0.61)                                                       |
| intraday: morning noise-area momentum       |                   0.71 |                                 0.86 | SPY 20d volume vs 1y median=quiet (+0.68); up/down volume balance (10d)=distribution (+0.49); policy uncertainty EPU (5d avg vs 1y median)=low (+0.48)            |
| SPY overnight only                          |                   0.84 |                                 0.84 | 10y breakeven inflation 3-month change=falling (-0.46); up/down volume balance (10d)=distribution (+0.40); inflation direction (CPI y/y vs 6m ago)=rising (-0.35) |
| intraday: high-efficiency open continuation |                   0.69 |                                 0.84 | policy uncertainty EPU (5d avg vs 1y median)=low (+0.83); bond volatility MOVE vs 1y median=high (+0.54); SPY 20d volume vs 1y median=quiet (+0.53)               |
| long QQQ                                    |                   0.77 |                                 0.73 | trend vs SMA50=below (+0.45); net liquidity (Fed assets - TGA - RRP) 13w change=falling (-0.44); inflation direction (CPI y/y vs 6m ago)=rising (-0.44)           |
| MR: after 3 down days, exit on up close     |                   0.72 |                                 0.73 | up/down volume balance (10d)=distribution (+1.11); implied - realized vol (VIX - RV20)=VIX < realized (-0.79); trend vs SMA50=below (+0.75)                       |
| risk parity SPY/TLT/GLD/DBC                 |                   0.67 |                                 0.63 | SPY 20d volume vs 1y median=quiet (-0.67); inflation direction (CPI y/y vs 6m ago)=rising (-0.48); yield curve 10y-2y level=flat 0-0.5 (-0.40)                    |
| long SPY                                    |                   0.64 |                                 0.62 | trend vs SMA50=below (+0.57); yield curve 10y-2y level=flat 0-0.5 (-0.49); credit (HYG/LQD vs SMA50)=risk-off (+0.44)                                             |
| MR: IBS<0.2, hold 1 day                     |                   0.60 |                                 0.58 | 1-month SPY return=down (+0.83); trend vs SMA50=below (+0.79); credit (HYG/LQD vs SMA50)=risk-off (+0.57)                                                         |
| long gold                                   |                   0.59 |                                 0.56 | trend vs SMA50=below (+0.54); inflation direction (CPI y/y vs 6m ago)=rising (-0.43); 10y yield 3-month change=rising (-0.40)                                     |
| tech - market (XLK-SPY)                     |                   0.60 |                                 0.55 | yield curve 3-month change=flattening (+0.32); 10y yield 3-month change=rising (-0.28); trade policy uncertainty vs 3y median=normal (-0.27)                      |
| dual momentum: best of SPY/TLT/GLD/DBC      |                   0.57 |                                 0.54 | implied - realized vol (VIX - RV20)=VIX < realized (+0.60); yield curve 10y-2y level=flat 0-0.5 (-0.60); SPY 20d volume vs 1y median=quiet (-0.57)                |
| MR: RSI(2)<10 until RSI(2)>70               |                   0.51 |                                 0.51 | up/down volume balance (10d)=distribution (+0.77); 1-month SPY return=down (+0.62); implied - realized vol (VIX - RV20)=VIX < realized (-0.62)                    |
| long RSP                                    |                   0.51 |                                 0.50 | yield curve 10y-2y level=flat 0-0.5 (-0.66); bitcoin 1-month move=normal (-0.48); credit (HYG/LQD vs SMA50)=risk-off (+0.45)                                      |

Bottom 8:

| strategy                              |   unconditional Sharpe |   scenario-adjusted Sharpe (approx.) | main drivers                                                                                                                                                |
|:--------------------------------------|-----------------------:|-------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------|
| intraday: fade gap-down rally (short) |                  -0.18 |                                -0.18 | implied - realized vol (VIX - RV20)=VIX < realized (-1.08); yield curve 10y-2y level=flat 0-0.5 (-1.00); yield curve 3-month change=flattening (+0.43)      |
| sector momentum: top-3 minus SPY      |                  -0.25 |                                -0.18 | implied - realized vol (VIX - RV20)=VIX < realized (+0.81); 1-month SPY return=down (+0.74); trend vs SMA50=below (+0.57)                                   |
| small - large (IWM-SPY)               |                  -0.21 |                                -0.22 | yield curve 10y-2y level=flat 0-0.5 (-0.85); SPY 20d volume vs 1y median=quiet (-0.55); up/down volume balance (10d)=distribution (-0.51)                   |
| energy - market (XLE-SPY)             |                  -0.31 |                                -0.30 | credit (HYG/LQD vs SMA50)=risk-off (-0.58); yield curve 10y-2y level=flat 0-0.5 (-0.50); price-volume (last day)=down on light volume (+0.43)               |
| long yen FXY                          |                  -0.40 |                                -0.42 | Fed balance sheet 13w change=flat (+0.45); policy uncertainty EPU (5d avg vs 1y median)=low (-0.41); 10y breakeven inflation 3-month change=falling (+0.37) |
| value - growth (IWD-IWF)              |                  -0.53 |                                -0.45 | price-volume (last day)=down on light volume (+0.69); copper/gold ratio vs SMA50=rising (growth) (+0.61); SPY 20d volume vs 1y median=quiet (+0.52)         |
| long euro FXE                         |                  -0.39 |                                -0.49 | inflation direction (CPI y/y vs 6m ago)=rising (-0.55); yield curve 10y-2y level=flat 0-0.5 (-0.50); VIX level=15-20 (-0.43)                                |
| long VIX futures (VIXY)               |                  -0.50 |                                -0.51 | trend vs SMA50=below (-0.74); SPY 20d volume vs 1y median=quiet (+0.71); yield curve 10y-2y level=flat 0-0.5 (+0.61)                                        |
