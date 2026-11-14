# Regime overlays on the live core portfolio

```
Three pre-registered regime overlays on the live core portfolio.

    python -m tradingagents.strategies.regime_overlays [--placebos 50]

The core book (``core_portfolio``: ETF positions, constant 2x leverage, gross <= 2, long-only,
2 bp per unit of turnover, weights refit each January) is the baseline. Each overlay below was
written down before it was run; only the PRIMARY variant decides adoption, the others are
robustness checks reported alongside.

1. Strategy momentum. On the first session of each month a strategy keeps its baseline weight
   only if its trailing 12-month vol-scaled return is positive; weights are renormalised to sum 1.
   Robustness: 6-month lookback; halve instead of drop.
   Placebo: each month drop the same number of strategies, chosen at random.
2. Stock-bond correlation. While the trailing 252-day correlation of SPY and TLT daily returns is
   above 0, the weights of "long bonds TLT" and "long bonds IEF" are halved and the freed weight goes
   to "long gold", "long commodities DBC" and the TSMOM trend strategy in proportion to their
   baseline weights. Robustness: CPI y/y rising vs 6 months earlier (45-day release lag) as the
   signal; either signal.
   Placebo: random on/off regimes with the signal's own transition probabilities.
3. Drawdown control. Leverage x0.5 once the baseline book is more than 10% below its trailing
   252-day high, back to full once it is within 5%. Robustness: 15% / 7.5%; x0 (flat) instead of x0.5.
   Placebo: random on/off periods with the same transition probabilities.

Adoption: the primary variant must beat the baseline Sharpe in all three periods (2011-26, 2021-26,
2024-05 onward) and beat the placebos' 95th percentile over 2011-26.
```

## Sharpe by period, 2022, annual return, max drawdown

|                                   |   2011-26 |   2021-26 |   2024-05+ |   2022 |   ann % |   maxDD % |
|:----------------------------------|----------:|----------:|-----------:|-------:|--------:|----------:|
| baseline (live core)              |      0.8  |      0.79 |       1.01 |  -1.26 |    9.3  |    -25.36 |
| 1. momentum 12m drop [PRIMARY]    |      0.82 |      0.79 |       1.03 |  -1.19 |   10.38 |    -31.22 |
| 1. momentum 6m drop               |      0.65 |      0.58 |       0.85 |  -1.82 |    8.35 |    -30.01 |
| 1. momentum 12m halve             |      0.81 |      0.8  |       1.02 |  -1.26 |    9.61 |    -27.53 |
| 2. stock-bond corr > 0 [PRIMARY]  |      0.81 |      0.82 |       1.04 |  -1.28 |    9.49 |    -25.36 |
| 2. CPI direction rising           |      0.77 |      0.83 |       1.02 |  -1.13 |    9.04 |    -26.65 |
| 2. either signal                  |      0.78 |      0.85 |       1.04 |  -1.14 |    9.18 |    -26.65 |
| 3. drawdown 10%/5% x0.5 [PRIMARY] |      0.79 |      0.77 |       0.97 |  -1.34 |    8.29 |    -18.87 |
| 3. drawdown 15%/7.5% x0.5         |      0.78 |      0.78 |       1.01 |  -1.48 |    8.71 |    -20.54 |
| 3. drawdown 10%/5% x0 (flat)      |      0.72 |      0.69 |       0.89 |  -1.16 |    7.2  |    -14.51 |

## Placebos (2011-26 Sharpe change vs baseline, 50 draws)

|                                   |   placebo median Δ |   placebo 95th Δ |   real Δ |
|:----------------------------------|-------------------:|-----------------:|---------:|
| 1. momentum 12m drop [PRIMARY]    |             -0.046 |            0.063 |    0.02  |
| 2. stock-bond corr > 0 [PRIMARY]  |              0.002 |            0.021 |    0.012 |
| 3. drawdown 10%/5% x0.5 [PRIMARY] |             -0.024 |            0.025 |   -0.012 |

## Verdict

- 1. momentum 12m drop [PRIMARY]: **reject**
- 2. stock-bond corr > 0 [PRIMARY]: **reject**
- 3. drawdown 10%/5% x0.5 [PRIMARY]: **reject**

Share of days each signal is on (2011+): stock-bond corr > 0 25%, CPI rising 53%, drawdown control on 23%
