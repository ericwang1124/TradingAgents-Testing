# Scenario-based exposure sizing: robustness

Out of sample 2011-2026 (walk-forward, yearly refit). ΔSharpe = sized portfolio minus the unsized base. Placebo: 50 random two-state regimes with the atlas' median day-to-day persistence (0.932).

## Summary by base portfolio and setting

|                                                                     |   base Sharpe 2011-26 |   median ΔSharpe (35+2 dims) |   share of dims improving |   best dim Δ |   worst dim Δ |   placebo median Δ |   placebo 95th pct Δ |   dims beating placebo 95th |   vol-target Δ |   dims beating vol-target |   median Δ 2024-05+ |
|:--------------------------------------------------------------------|----------------------:|-----------------------------:|--------------------------:|-------------:|--------------:|-------------------:|---------------------:|----------------------------:|---------------:|--------------------------:|--------------------:|
| ('core basket (positive-edge strategies)', 'k=250, clip 0.25-2.0')  |                  0.88 |                        -0.10 |                     18.92 |         0.32 |         -0.43 |              -0.07 |                 0.05 |                        2.00 |           0.01 |                      6.00 |               -0.04 |
| ('core basket (positive-edge strategies)', 'k=1000, clip 0.25-2.0') |                  0.88 |                        -0.05 |                     24.32 |         0.22 |         -0.25 |              -0.05 |                 0.04 |                        2.00 |           0.01 |                      7.00 |               -0.02 |
| ('core basket (positive-edge strategies)', 'k=250, clip 0.5-1.5')   |                  0.88 |                        -0.08 |                     24.32 |         0.25 |         -0.33 |              -0.07 |                 0.07 |                        2.00 |           0.00 |                      9.00 |               -0.03 |
| ('core basket (positive-edge strategies)', 'k=1000, clip 0.5-1.5')  |                  0.88 |                        -0.05 |                     27.03 |         0.18 |         -0.24 |              -0.05 |                 0.04 |                        2.00 |           0.00 |                     10.00 |               -0.02 |
| ('8-strategy equal risk', 'k=250, clip 0.25-2.0')                   |                  0.74 |                        -0.06 |                     21.62 |         0.39 |         -0.35 |              -0.06 |                 0.04 |                        6.00 |          -0.09 |                     23.00 |               -0.07 |
| ('8-strategy equal risk', 'k=1000, clip 0.25-2.0')                  |                  0.74 |                        -0.03 |                     21.62 |         0.20 |         -0.20 |              -0.05 |                 0.03 |                        6.00 |          -0.09 |                     30.00 |               -0.04 |
| ('8-strategy equal risk', 'k=250, clip 0.5-1.5')                    |                  0.74 |                        -0.06 |                     29.73 |         0.31 |         -0.29 |              -0.05 |                 0.05 |                        6.00 |          -0.08 |                     23.00 |               -0.06 |
| ('8-strategy equal risk', 'k=1000, clip 0.5-1.5')                   |                  0.74 |                        -0.03 |                     24.32 |         0.20 |         -0.20 |              -0.05 |                 0.04 |                        6.00 |          -0.08 |                     31.00 |               -0.04 |
| ('SPY alone', 'k=250, clip 0.25-2.0')                               |                  0.74 |                        -0.10 |                     13.51 |         0.24 |         -0.38 |              -0.09 |                 0.06 |                        3.00 |          -0.04 |                     13.00 |               -0.02 |
| ('SPY alone', 'k=1000, clip 0.25-2.0')                              |                  0.74 |                        -0.06 |                     16.22 |         0.20 |         -0.26 |              -0.07 |                 0.09 |                        1.00 |          -0.04 |                     16.00 |               -0.02 |
| ('SPY alone', 'k=250, clip 0.5-1.5')                                |                  0.74 |                        -0.08 |                     18.92 |         0.20 |         -0.30 |              -0.06 |                 0.09 |                        2.00 |          -0.03 |                     12.00 |               -0.02 |
| ('SPY alone', 'k=1000, clip 0.5-1.5')                               |                  0.74 |                        -0.06 |                     21.62 |         0.16 |         -0.23 |              -0.06 |                 0.11 |                        1.00 |          -0.03 |                     14.00 |               -0.02 |
| ('QQQ alone', 'k=250, clip 0.25-2.0')                               |                  0.85 |                        -0.08 |                     10.81 |         0.19 |         -0.26 |              -0.06 |                 0.02 |                        4.00 |           0.07 |                      2.00 |               -0.03 |
| ('QQQ alone', 'k=1000, clip 0.25-2.0')                              |                  0.85 |                        -0.05 |                     16.22 |         0.14 |         -0.17 |              -0.04 |                 0.04 |                        4.00 |           0.07 |                      2.00 |               -0.02 |
| ('QQQ alone', 'k=250, clip 0.5-1.5')                                |                  0.85 |                        -0.06 |                     13.51 |         0.15 |         -0.22 |              -0.05 |                 0.02 |                        4.00 |           0.05 |                      3.00 |               -0.02 |
| ('QQQ alone', 'k=1000, clip 0.5-1.5')                               |                  0.85 |                        -0.05 |                     16.22 |         0.13 |         -0.15 |              -0.04 |                 0.05 |                        3.00 |           0.05 |                      3.00 |               -0.02 |
| ('IWM alone', 'k=250, clip 0.25-2.0')                               |                  0.30 |                        -0.09 |                     24.32 |         0.27 |         -0.43 |              -0.08 |                 0.17 |                        5.00 |          -0.05 |                     15.00 |               -0.06 |
| ('IWM alone', 'k=1000, clip 0.25-2.0')                              |                  0.30 |                        -0.05 |                     24.32 |         0.22 |         -0.30 |              -0.06 |                 0.12 |                        6.00 |          -0.05 |                     15.00 |               -0.04 |
| ('IWM alone', 'k=250, clip 0.5-1.5')                                |                  0.30 |                        -0.05 |                     21.62 |         0.22 |         -0.34 |              -0.05 |                 0.15 |                        4.00 |          -0.07 |                     20.00 |               -0.04 |
| ('IWM alone', 'k=1000, clip 0.5-1.5')                               |                  0.30 |                        -0.05 |                     24.32 |         0.21 |         -0.27 |              -0.05 |                 0.11 |                        5.00 |          -0.07 |                     26.00 |               -0.03 |

## Each scenario dimension, median over bases and settings

| dimension                                         |   Δ 2011-26 |   Δ 2019-26 |   Δ 2024-05+ |   share of (base,setting) improving |
|:--------------------------------------------------|------------:|------------:|-------------:|------------------------------------:|
| bitcoin 1-month move                              |        0.20 |        0.25 |        -0.11 |                              100.00 |
| inflation direction (CPI y/y vs 6m ago)           |        0.09 |        0.13 |         0.17 |                              100.00 |
| combo B: trend x inflation                        |        0.08 |        0.10 |         0.14 |                              100.00 |
| yield curve 3-month change                        |        0.07 |        0.17 |         0.18 |                               85.00 |
| combo A: trend x VIX>=20                          |        0.02 |        0.07 |         0.22 |                               60.00 |
| yield curve 10y-2y level                          |        0.01 |        0.04 |         0.23 |                               65.00 |
| trend vs SMA200                                   |        0.01 |       -0.02 |        -0.02 |                               55.00 |
| net liquidity (Fed assets - TGA - RRP) 13w change |       -0.00 |        0.02 |        -0.07 |                               50.00 |
| last FOMC decision                                |       -0.01 |        0.01 |        -0.11 |                               35.00 |
| EUR/USD 1-month move                              |       -0.02 |        0.05 |         0.14 |                               40.00 |
| FOMC calendar                                     |       -0.03 |       -0.07 |        -0.28 |                                5.00 |
| credit (HYG/LQD vs SMA50)                         |       -0.04 |       -0.03 |        -0.26 |                                0.00 |
| oil (WTI) 1-month move                            |       -0.04 |       -0.09 |        -0.23 |                                0.00 |
| gold 1-month move                                 |       -0.04 |       -0.07 |         0.04 |                                5.00 |
| VIX term structure                                |       -0.05 |       -0.06 |        -0.04 |                                0.00 |
| drawdown from 52w high                            |       -0.05 |       -0.06 |         0.00 |                                0.00 |
| Fed policy cycle (fed funds 6m change)            |       -0.05 |        0.07 |         0.07 |                               25.00 |
| 10y breakeven inflation 3-month change            |       -0.05 |       -0.10 |        -0.15 |                                0.00 |
| implied - realized vol (VIX - RV20)               |       -0.06 |       -0.04 |        -0.08 |                                0.00 |
| dollar index DXY 1-month move                     |       -0.06 |       -0.01 |         0.04 |                               20.00 |
| trend vs SMA50                                    |       -0.07 |       -0.09 |         0.10 |                                0.00 |
| 2y yield 3-month change                           |       -0.07 |       -0.03 |        -0.11 |                                0.00 |
| VIX level                                         |       -0.07 |        0.00 |         0.10 |                               15.00 |
| copper/gold ratio vs SMA50                        |       -0.08 |       -0.08 |        -0.10 |                                0.00 |
| SPY 20d volume vs 1y median                       |       -0.08 |        0.03 |         0.08 |                                5.00 |
| 1-month SPY return                                |       -0.08 |       -0.14 |        -0.02 |                                0.00 |
| 10y real yield 3-month change                     |       -0.09 |       -0.09 |        -0.28 |                                0.00 |
| US dollar (UUP vs SMA50)                          |       -0.09 |       -0.05 |        -0.02 |                                0.00 |
| bond volatility MOVE vs 1y median                 |       -0.09 |       -0.03 |         0.03 |                                0.00 |
| Fed balance sheet 13w change                      |       -0.09 |       -0.02 |        -0.08 |                                0.00 |
| 10y yield 3-month change                          |       -0.10 |       -0.07 |        -0.03 |                                0.00 |
| policy uncertainty EPU (5d avg vs 1y median)      |       -0.11 |       -0.20 |        -0.15 |                                0.00 |
| trade policy uncertainty vs 3y median             |       -0.14 |       -0.05 |        -0.05 |                                0.00 |
| up/down volume balance (10d)                      |       -0.16 |       -0.13 |        -0.10 |                                0.00 |
| USD/JPY 1-month move                              |       -0.17 |       -0.18 |        -0.11 |                                0.00 |
| price-volume (last day)                           |       -0.22 |       -0.29 |        -0.08 |                                0.00 |
| SPY volume vs 20d median                          |       -0.26 |       -0.27 |        -0.09 |                                0.00 |
