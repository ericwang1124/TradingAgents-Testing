# Raising the combined Sharpe

```
Raise the combined (core + intraday add-on) Sharpe: pre-registered candidates.

    python -m tradingagents.strategies.combined_sharpe

Part 1, add-on (2021+, thresholds walk-forward as live):
  * short side through the inverse ETF SH: on high-efficiency down opens, buy SH at 10:00 and sell
    at the noon exit. SH tracks -1x SPY intraday (beta 1.003 over the past year of 1-minute bars);
    each short trade is charged 3 bp more than the SPY trade for SH's wider spread.
  * size: 1x, 1.5x, 2x of account equity.

Part 2, blocks added to the core book's strategy list, rerun walk-forward exactly as live:
  B1. short-term mean reversion on QQQ, IWM, DIA and RSP, the three rules the core already runs on
      SPY: IBS < 0.2 hold 1 day; RSI(2) < 10 until RSI(2) > 70; after 3 down closes until an up close
  B2. RSI(30) < 35 buy / > 65 sell on SPY, QQQ, IWM, raw and with a trend filter (no new entry while
      the close is below its 200-day average)
  B3. managed-futures ETFs DBMF (2019-05) and KMLM (2020-12), held long; their funds go short inside
Adoption: B1 and B2 must improve the core Sharpe in 2011-26, 2011-18, 2019-26 and 2024-05 onward;
B3, whose ETFs only get weights from 2021, in 2021-26 and 2024-05 onward.
```

## Part 1: add-on short side via SH and size (core unchanged)

|                                     |   2021-26 |   2024-05+ |   maxDD % |
|:------------------------------------|----------:|-----------:|----------:|
| core + add-on long only, 1x         |      0.95 |       1.12 |    -18.28 |
| core + add-on long + SH short, 1x   |      0.94 |       1.11 |    -21.13 |
| core + add-on long only, 1.5x       |      1.01 |       1.16 |    -18.18 |
| core + add-on long + SH short, 1.5x |      0.97 |       1.13 |    -22.63 |
| core + add-on long only, 2x         |      1.05 |       1.18 |    -18.2  |
| core + add-on long + SH short, 2x   |      0.99 |       1.13 |    -24.16 |

Short side: trades 213.00, mean bp (after SH cost) -0.59, t -0.17, corr with core -0.13

## Part 2: candidate blocks in the core

|                            |   2011-26 |   2011-18 |   2019-26 |   2021-26 |   2024-05+ |   maxDD % |
|:---------------------------|----------:|----------:|----------:|----------:|-----------:|----------:|
| baseline core              |      0.8  |      0.63 |      0.96 |      0.8  |       1.02 |    -25.36 |
| B1. MR on QQQ/IWM/DIA/RSP  |      0.73 |      0.59 |      0.85 |      0.76 |       1    |    -24.64 |
| B2. RSI(30) on SPY/QQQ/IWM |      0.84 |      0.64 |      1.02 |      0.83 |       1.05 |    -25.07 |
| B3. managed futures ETFs   |      0.8  |      0.63 |      0.96 |      0.78 |       0.99 |    -25.36 |

## Verdict

- B1. MR on QQQ/IWM/DIA/RSP: **reject**
- B2. RSI(30) on SPY/QQQ/IWM: **ADOPT**
- B3. managed futures ETFs: **reject**

## Candidates on their own (2011+ or first date)

|                                        | block                      |   Sharpe |   time in % |   corr with core |   weight 2026 |
|:---------------------------------------|:---------------------------|---------:|------------:|-----------------:|--------------:|
| MR QQQ: IBS<0.2 1 day                  | B1. MR on QQQ/IWM/DIA/RSP  |     0.96 |       17.49 |             0.46 |          0.06 |
| MR QQQ: RSI(2)<10 until >70            | B1. MR on QQQ/IWM/DIA/RSP  |     0.64 |       19.97 |             0.54 |          0.04 |
| MR QQQ: 3 down closes until up close   | B1. MR on QQQ/IWM/DIA/RSP  |     0.9  |        8.02 |             0.35 |          0.06 |
| MR IWM: IBS<0.2 1 day                  | B1. MR on QQQ/IWM/DIA/RSP  |     0.59 |       19.54 |             0.43 |          0.04 |
| MR IWM: RSI(2)<10 until >70            | B1. MR on QQQ/IWM/DIA/RSP  |     0.51 |       22.17 |             0.5  |          0.02 |
| MR IWM: 3 down closes until up close   | B1. MR on QQQ/IWM/DIA/RSP  |     0.67 |        9.27 |             0.41 |          0.01 |
| MR DIA: IBS<0.2 1 day                  | B1. MR on QQQ/IWM/DIA/RSP  |     0.59 |       18.12 |             0.44 |          0.03 |
| MR DIA: RSI(2)<10 until >70            | B1. MR on QQQ/IWM/DIA/RSP  |     0.43 |       20.7  |             0.5  |          0.01 |
| MR DIA: 3 down closes until up close   | B1. MR on QQQ/IWM/DIA/RSP  |     0.5  |        9.15 |             0.41 |          0.03 |
| MR RSP: IBS<0.2 1 day                  | B1. MR on QQQ/IWM/DIA/RSP  |     0.38 |       18.32 |             0.45 |          0.02 |
| MR RSP: RSI(2)<10 until >70            | B1. MR on QQQ/IWM/DIA/RSP  |     0.52 |       20.67 |             0.49 |          0.03 |
| MR RSP: 3 down closes until up close   | B1. MR on QQQ/IWM/DIA/RSP  |     0.38 |        8.67 |             0.45 |          0.02 |
| RSI30 SPY: <35 buy, >65 sell           | B2. RSI(30) on SPY/QQQ/IWM |     0.52 |       20.3  |             0.31 |          0.03 |
| RSI30 SPY: same, no entry below SMA200 | B2. RSI(30) on SPY/QQQ/IWM |   nan    |        0    |           nan    |          0    |
| RSI30 QQQ: <35 buy, >65 sell           | B2. RSI(30) on SPY/QQQ/IWM |     0.68 |       23.05 |             0.35 |          0.07 |
| RSI30 QQQ: same, no entry below SMA200 | B2. RSI(30) on SPY/QQQ/IWM |   nan    |        0    |           nan    |          0    |
| RSI30 IWM: <35 buy, >65 sell           | B2. RSI(30) on SPY/QQQ/IWM |     0.37 |       42.37 |             0.43 |          0    |
| RSI30 IWM: same, no entry below SMA200 | B2. RSI(30) on SPY/QQQ/IWM |   nan    |        0    |           nan    |          0    |
| long DBMF (managed futures)            | B3. managed futures ETFs   |     0.59 |      100    |             0.29 |          0.04 |
| long KMLM (managed futures)            | B3. managed futures ETFs   |     0.29 |      100    |            -0.11 |          0    |
