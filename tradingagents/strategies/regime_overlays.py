"""Three pre-registered regime overlays on the live core portfolio.

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
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from . import core_portfolio as cp
from .strategy_atlas import load_cpi, load_ohlc

PERIODS = [("2011-26", "2011-01-01"), ("2021-26", "2021-01-01"), ("2024-05+", "2024-05-01")]
BONDS = ["long bonds TLT", "long bonds IEF"]
RECIPIENTS = ["long gold", "long commodities DBC", "trend: TSMOM SPY/TLT/GLD/DBC"]
OUT = Path("results/opening_reversal/REGIME_OVERLAYS.md")


@dataclass
class Ctx:
    C: pd.DataFrame
    P: Dict[str, pd.DataFrame]
    Rs: pd.DataFrame
    scale: pd.DataFrame
    W0: pd.DataFrame
    ex: pd.DataFrame
    r: pd.DataFrame
    cpi_up: pd.Series


def setup() -> Ctx:
    d = load_ohlc()
    cal = d["SPY"].index[d["SPY"].index >= "2007-06-01"]
    C = pd.DataFrame({t: d[t]["Close"] for t in cp.UNIVERSE}).reindex(cal)
    P = cp.strategy_positions(C, d["SPY"]["High"].reindex(cal), d["SPY"]["Low"].reindex(cal), cal)
    R = cp.strategy_returns(P, C)
    scale = cp.strategy_scale(R)
    Rs = R * scale.shift(1)
    W0 = pd.DataFrame(0.0, index=cal, columns=R.columns)
    for y in range(2011, cal[-1].year + 1):
        W0.loc[W0.index.year == y] = cp.fit_weights(Rs[Rs.index.year < y]).to_numpy()
    r = C.pct_change()
    ex = r.sub(r["BIL"].fillna(0.0), axis=0)
    cpi = load_cpi()
    yoy = cpi.pct_change(12)
    up = pd.Series(((yoy - yoy.shift(6)) > 0).to_numpy(), index=cpi.index + pd.DateOffset(days=45))
    cpi_up = up.sort_index().reindex(cal, method="ffill").fillna(False).astype(bool)
    return Ctx(C, P, Rs, scale, W0, ex, r, cpi_up)


def book(ctx: Ctx, W: pd.DataFrame, multiplier: Optional[pd.Series] = None) -> pd.Series:
    """Same arithmetic as ``core_portfolio.backtest`` for a given daily weight frame."""
    E = cp.combine(ctx.P, W, ctx.scale)
    gross = E.abs().sum(axis=1)
    cap = cp.MAX_GROSS / gross.replace(0, np.nan)
    lev = pd.Series(cp.LEVERAGE, index=E.index).clip(upper=cap).fillna(0.0)
    if multiplier is not None:
        lev = (lev * multiplier.reindex(lev.index).fillna(1.0)).clip(upper=cap).fillna(0.0)
    Ef = E.mul(lev, axis=0).clip(lower=0.0)
    ret = (Ef.shift(1) * ctx.ex[Ef.columns]).sum(axis=1)
    ret = ret - Ef.diff().abs().sum(axis=1).fillna(0.0) * 2.0 / 1e4
    return ret[ret.index >= "2011-01-01"]


def sharpe(r: pd.Series) -> float:
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else float("nan")


def stats(r: pd.Series) -> Dict[str, float]:
    out = {}
    for name, start in PERIODS:
        out[name] = sharpe(r[r.index >= start])
    out["2022"] = sharpe(r[r.index.year == 2022])
    eq = (1 + r).cumprod()
    out["ann %"] = (eq.iloc[-1] ** (252 / len(r)) - 1) * 100
    out["maxDD %"] = (eq / eq.cummax() - 1).min() * 100
    return out


# ------------------------------------------------------------------ overlay 1: strategy momentum
def month_starts(index: pd.DatetimeIndex) -> pd.Series:
    m = pd.Series(index.month, index=index)
    return m != m.shift(1)


def momentum_mask(ctx: Ctx, lookback: int, halve: bool) -> pd.DataFrame:
    trail = ctx.Rs.rolling(lookback, min_periods=int(lookback * 0.8)).sum()
    keep = (trail > 0) | trail.isna()                         # no history yet -> keep
    k = keep.astype(float) if not halve else keep.astype(float).replace(0.0, 0.5)
    return k.where(month_starts(ctx.Rs.index), np.nan).ffill().fillna(1.0)


def renorm(W: pd.DataFrame) -> pd.DataFrame:
    s = W.sum(axis=1)
    return W.div(s.replace(0, np.nan), axis=0).fillna(0.0)


def momentum_weights(ctx: Ctx, lookback: int = 252, halve: bool = False) -> pd.DataFrame:
    return renorm(ctx.W0 * momentum_mask(ctx, lookback, halve))


def momentum_placebo(ctx: Ctx, seed: int) -> pd.DataFrame:
    """Each month, drop as many positive-weight strategies as the real rule drops, at random."""
    rng = np.random.default_rng(seed)
    mask = momentum_mask(ctx, 252, False)
    starts = ctx.W0.index[month_starts(ctx.W0.index).to_numpy()]
    fake = pd.DataFrame(np.nan, index=ctx.W0.index, columns=ctx.W0.columns)
    for t in starts:
        live = ctx.W0.columns[ctx.W0.loc[t] > 0]
        n_drop = int(((mask.loc[t, live]) == 0).sum())
        row = pd.Series(1.0, index=ctx.W0.columns)
        if n_drop:
            row[rng.choice(live, size=n_drop, replace=False)] = 0.0
        fake.loc[t] = row.to_numpy()
    return renorm(ctx.W0 * fake.ffill().fillna(1.0))


# ------------------------------------------------------------------ overlay 2: stock-bond correlation
def sb_corr_signal(ctx: Ctx) -> pd.Series:
    return (ctx.r["SPY"].rolling(252, min_periods=200).corr(ctx.r["TLT"]) > 0).fillna(False)


def bond_tilt_weights(ctx: Ctx, on: pd.Series) -> pd.DataFrame:
    W = ctx.W0.copy()
    on = on.reindex(W.index).fillna(False).astype(bool)
    freed = 0.5 * W[BONDS].sum(axis=1)
    W.loc[on, BONDS] = W.loc[on, BONDS] * 0.5
    base = W[RECIPIENTS]
    share = base.div(base.sum(axis=1).replace(0, np.nan), axis=0).fillna(1.0 / len(RECIPIENTS))
    W.loc[on, RECIPIENTS] = W.loc[on, RECIPIENTS] + share.loc[on].mul(freed[on], axis=0)
    return W


# ------------------------------------------------------------------ overlay 3: drawdown control
def drawdown_multiplier(base: pd.Series, enter: float = 0.10, exit_: float = 0.05, cut: float = 0.5) -> pd.Series:
    eq = (1 + base.fillna(0.0)).cumprod()
    dd = eq / eq.rolling(252, min_periods=1).max() - 1
    state, out = False, []
    for v in dd.to_numpy():
        if not state and v < -enter:
            state = True
        elif state and v > -exit_:
            state = False
        out.append(cut if state else 1.0)
    return pd.Series(out, index=base.index)


# ------------------------------------------------------------------ placebo regimes
def markov_like(signal: pd.Series, n: int, seed: int) -> List[pd.Series]:
    """Random on/off series with the signal's own P(stay on) and P(stay off)."""
    s = signal.astype(bool).to_numpy()
    prev, cur = s[:-1], s[1:]
    p_on = (cur & prev).sum() / max(prev.sum(), 1)
    p_off = (~cur & ~prev).sum() / max((~prev).sum(), 1)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        u = rng.random(len(s))
        st = np.empty(len(s), dtype=bool)
        st[0] = u[0] < s.mean()
        for i in range(1, len(s)):
            st[i] = (u[i] < p_on) if st[i - 1] else (u[i] >= p_off)
        out.append(pd.Series(st, index=signal.index))
    return out


def run(n_placebo: int = 50) -> Dict[str, object]:
    ctx = setup()
    base = book(ctx, ctx.W0)
    rows: Dict[str, Dict[str, float]] = {"baseline (live core)": stats(base)}

    rows["1. momentum 12m drop [PRIMARY]"] = stats(book(ctx, momentum_weights(ctx, 252, False)))
    rows["1. momentum 6m drop"] = stats(book(ctx, momentum_weights(ctx, 126, False)))
    rows["1. momentum 12m halve"] = stats(book(ctx, momentum_weights(ctx, 252, True)))

    sb = sb_corr_signal(ctx)
    rows["2. stock-bond corr > 0 [PRIMARY]"] = stats(book(ctx, bond_tilt_weights(ctx, sb)))
    rows["2. CPI direction rising"] = stats(book(ctx, bond_tilt_weights(ctx, ctx.cpi_up)))
    rows["2. either signal"] = stats(book(ctx, bond_tilt_weights(ctx, sb | ctx.cpi_up)))

    dd_mult = drawdown_multiplier(base.reindex(ctx.W0.index).fillna(0.0))
    rows["3. drawdown 10%/5% x0.5 [PRIMARY]"] = stats(book(ctx, ctx.W0, dd_mult))
    rows["3. drawdown 15%/7.5% x0.5"] = stats(book(ctx, ctx.W0, drawdown_multiplier(base.reindex(ctx.W0.index).fillna(0.0), 0.15, 0.075)))
    rows["3. drawdown 10%/5% x0 (flat)"] = stats(book(ctx, ctx.W0, drawdown_multiplier(base.reindex(ctx.W0.index).fillna(0.0), cut=0.0)))

    table = pd.DataFrame(rows).T
    b = table.loc["baseline (live core)"]

    placebo = {}
    p1 = [sharpe(book(ctx, momentum_placebo(ctx, s))) for s in range(n_placebo)]
    p2 = [sharpe(book(ctx, bond_tilt_weights(ctx, f))) for f in markov_like(sb[sb.index >= "2010-01-01"], n_placebo, 1)]
    dd_on = (dd_mult < 1).reindex(ctx.W0.index).fillna(False)
    p3 = [sharpe(book(ctx, ctx.W0, f.map({True: 0.5, False: 1.0})))
          for f in markov_like(dd_on[dd_on.index >= "2011-01-01"], n_placebo, 2)]
    for key, vals in (("1. momentum 12m drop [PRIMARY]", p1), ("2. stock-bond corr > 0 [PRIMARY]", p2),
                      ("3. drawdown 10%/5% x0.5 [PRIMARY]", p3)):
        d = np.asarray(vals) - b["2011-26"]
        placebo[key] = {"placebo median Δ": float(np.median(d)), "placebo 95th Δ": float(np.percentile(d, 95)),
                        "real Δ": float(table.loc[key, "2011-26"] - b["2011-26"])}
    pl = pd.DataFrame(placebo).T
    verdict = {}
    for key in pl.index:
        better = all(table.loc[key, p] > b[p] for p, _ in PERIODS)
        verdict[key] = "ADOPT" if (better and pl.loc[key, "real Δ"] > pl.loc[key, "placebo 95th Δ"]) else "reject"
    signal_share = {"stock-bond corr > 0": float(sb[sb.index >= "2011-01-01"].mean()),
                    "CPI rising": float(ctx.cpi_up[ctx.cpi_up.index >= "2011-01-01"].mean()),
                    "drawdown control on": float(dd_on[dd_on.index >= "2011-01-01"].mean())}
    return {"table": table, "placebo": pl, "verdict": verdict, "signal_share": signal_share, "base": base}


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--placebos", type=int, default=50)
    args = p.parse_args(argv)
    res = run(args.placebos)
    t, pl = res["table"].round(2), res["placebo"].round(3)
    lines = ["# Regime overlays on the live core portfolio", "", "```", __doc__.strip(), "```", "",
             "## Sharpe by period, 2022, annual return, max drawdown", "", t.to_markdown(), "",
             f"## Placebos (2011-26 Sharpe change vs baseline, {args.placebos} draws)", "", pl.to_markdown(), "",
             "## Verdict", ""] + [f"- {k}: **{v}**" for k, v in res["verdict"].items()] + [
             "", "Share of days each signal is on (2011+): " + ", ".join(f"{k} {v:.0%}" for k, v in res["signal_share"].items())]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
