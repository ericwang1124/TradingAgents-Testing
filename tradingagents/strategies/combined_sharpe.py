"""Raise the combined (core + intraday add-on) Sharpe: pre-registered candidates.

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
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from . import core_portfolio as cp
from . import equity_indices as ei
from . import regime_overlays as ro
from .opening_reversal.data import default_cache_dir
from .strategy_atlas import load_ohlc

SH_EXTRA_COST = 3.0 / 1e4
OUT = Path("results/opening_reversal/COMBINED_SHARPE.md")
PERIODS_FULL = [("2011-26", "2011-01-01"), ("2011-18", "2011-01-01", "2018-12-31"), ("2019-26", "2019-01-01"),
                ("2021-26", "2021-01-01"), ("2024-05+", "2024-05-01")]


def addon_streams(path: str = "results/opening_reversal/DAY_TYPE_features.csv", years=range(2021, 2027)):
    f = pd.read_csv(path, index_col=0, parse_dates=True)
    L = pd.Series(0.0, index=f.index)
    S = pd.Series(0.0, index=f.index)
    for y in years:
        thr = f.loc[f.index.year < y, "efficiency"].quantile(2 / 3)
        m = (f.index.year == y) & (f["efficiency"] >= thr)
        up, dn = m & (f["direction"] == 1), m & (f["direction"] == -1)
        L[up] = f.loc[up, "cont_to_noon"]
        S[dn] = f.loc[dn, "cont_to_noon"] - SH_EXTRA_COST
    start = f"{min(years)}-01-01"
    return L[L.index >= start], S[S.index >= start]


def pstats(r: pd.Series) -> Dict[str, float]:
    out = {}
    for p in PERIODS_FULL:
        name, a = p[0], p[1]
        b = p[2] if len(p) > 2 else "2100-01-01"
        x = r[(r.index >= a) & (r.index <= b)]
        out[name] = ro.sharpe(x) if len(x) > 200 else np.nan
    eq = (1 + r).cumprod()
    out["maxDD %"] = (eq / eq.cummax() - 1).min() * 100
    return out


def _mr_positions(c: pd.Series, h: pd.Series, l: pd.Series, t: str) -> Dict[str, pd.DataFrame]:
    idx = c.index
    r = c.pct_change()
    ibs = (c - l) / (h - l).replace(0, np.nan)
    rs = cp._rsi(c, 2)
    down3 = (r < 0) & (r.shift(1) < 0) & (r.shift(2) < 0)
    return {f"MR {t}: IBS<0.2 1 day": pd.DataFrame({t: (ibs < 0.2).astype(float)}, index=idx),
            f"MR {t}: RSI(2)<10 until >70": pd.DataFrame({t: cp._hold_until(rs < 10, rs > 70)}, index=idx),
            f"MR {t}: 3 down closes until up close": pd.DataFrame({t: cp._hold_until(down3, r > 0)}, index=idx)}


def _rsi30_positions(c: pd.Series, t: str) -> Dict[str, pd.DataFrame]:
    rs = cp._rsi(c, 30)
    rs[:90] = np.nan
    above = c > c.rolling(200).mean()
    return {f"RSI30 {t}: <35 buy, >65 sell": pd.DataFrame({t: cp._hold_until(rs < 35, rs > 65)}, index=c.index),
            f"RSI30 {t}: same, no entry below SMA200": pd.DataFrame({t: cp._hold_until((rs < 35) & above, rs > 65)}, index=c.index)}


def candidate_blocks(cal: pd.DatetimeIndex):
    d = load_ohlc()
    eq = default_cache_dir() / "equity_indices"
    alt = default_cache_dir() / "alt_etfs"
    ohlc = {t: d[t] for t in ("SPY", "QQQ", "IWM", "RSP")}
    ohlc["DIA"] = pd.read_csv(eq / "DIA.csv", index_col=0, parse_dates=True)
    for t in ("DBMF", "KMLM"):
        ohlc[t] = pd.read_csv(alt / f"{t}.csv", index_col=0, parse_dates=True)
    ohlc = {t: v.reindex(cal) for t, v in ohlc.items()}
    X = pd.DataFrame({t: ohlc[t]["Close"] for t in ("DIA", "DBMF", "KMLM")})
    B1, B2 = {}, {}
    for t in ("QQQ", "IWM", "DIA", "RSP"):
        B1.update(_mr_positions(ohlc[t]["Close"], ohlc[t]["High"], ohlc[t]["Low"], t))
    for t in ("SPY", "QQQ", "IWM"):
        B2.update(_rsi30_positions(ohlc[t]["Close"], t))
    B3 = {f"long {t} (managed futures)": pd.DataFrame({t: ohlc[t]["Close"].notna().astype(float)}, index=cal)
          for t in ("DBMF", "KMLM")}
    return {"B1. MR on QQQ/IWM/DIA/RSP": B1, "B2. RSI(30) on SPY/QQQ/IWM": B2, "B3. managed futures ETFs": B3}, X


def pre_change_base() -> ro.Ctx:
    """The core as it was before this study (without the RSI(30) strategies it led to adding)."""
    ctx = ro.setup()
    keep = [c for c in ctx.Rs.columns if not c.startswith("RSI(30)")]
    W = pd.DataFrame(0.0, index=ctx.W0.index, columns=keep)
    for y in range(2011, W.index[-1].year + 1):
        W.loc[W.index.year == y] = cp.fit_weights(ctx.Rs[keep][ctx.Rs.index.year < y]).to_numpy()
    return ro.Ctx(ctx.C, {k: v for k, v in ctx.P.items() if k in keep}, ctx.Rs[keep], ctx.scale[keep], W,
                  ctx.ex, ctx.r, ctx.cpi_up)


def run() -> Dict[str, object]:
    base = pre_change_base()
    core = ro.book(base, base.W0)
    L, S = addon_streams()

    # part 1: add-on side and size, on top of the current core
    rows1 = {}
    for k in (1.0, 1.5, 2.0):
        for name, a in (("long only", L), ("long + SH short", L + S)):
            c = core[core.index >= "2021-01-01"]
            comb = c + k * a.reindex(c.index).fillna(0.0)
            rows1[f"core + add-on {name}, {k:g}x"] = {k2: v for k2, v in pstats(comb).items() if k2 in ("2021-26", "2024-05+", "maxDD %")}
    rows1 = pd.DataFrame(rows1).T
    t_short = S[S != 0]
    short_stats = {"trades": len(t_short), "mean bp (after SH cost)": t_short.mean() * 1e4,
                   "t": t_short.mean() / t_short.std() * np.sqrt(len(t_short)),
                   "corr with core": core.reindex(S.index).corr(S)}

    # part 2: candidate blocks in the core
    blocks, X = candidate_blocks(base.C.index)
    rows2 = {"baseline core": pstats(core)}
    standalone, ctxs = {}, {}
    for name, extra in blocks.items():
        ctx = ei.make_ctx(base, extra, X)
        ctxs[name] = ctx
        rows2[name] = pstats(ro.book(ctx, ctx.W0))
        R = cp.strategy_returns(extra, ctx.C)
        for k in extra:
            x = R[k][R[k].index >= "2011-01-01"].dropna()
            standalone[k] = {"block": name, "Sharpe": ro.sharpe(x), "time in %": float((extra[k].reindex(x.index).abs().sum(axis=1) > 0).mean() * 100),
                             "corr with core": float(x.corr(core.reindex(x.index))),
                             "weight 2026": float(ctx.W0.iloc[-1].get(k, 0.0))}
    rows2 = pd.DataFrame(rows2).T
    b = rows2.loc["baseline core"]
    verdict = {}
    for name in blocks:
        ps = ["2021-26", "2024-05+"] if name.startswith("B3") else ["2011-26", "2011-18", "2019-26", "2024-05+"]
        verdict[name] = "ADOPT" if all(rows2.loc[name, p] > b[p] for p in ps) else "reject"
    return {"addon": rows1, "short_stats": short_stats, "core": rows2, "verdict": verdict,
            "standalone": pd.DataFrame(standalone).T, "ctxs": ctxs, "base": base, "L": L, "S": S}


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    res = run()
    md = lambda df: df.astype(float, errors="ignore").round(2).to_markdown() if isinstance(df, pd.DataFrame) else str(df)
    lines = ["# Raising the combined Sharpe", "", "```", __doc__.strip(), "```", "",
             "## Part 1: add-on short side via SH and size (core unchanged)", "", md(res["addon"]), "",
             "Short side: " + ", ".join(f"{k} {v:.2f}" for k, v in res["short_stats"].items()), "",
             "## Part 2: candidate blocks in the core", "", md(res["core"]), "", "## Verdict", ""]
    lines += [f"- {k}: **{v}**" for k, v in res["verdict"].items()]
    sa = res["standalone"].copy()
    for c in ("Sharpe", "time in %", "corr with core", "weight 2026"):
        sa[c] = sa[c].astype(float).round(2)
    lines += ["", "## Candidates on their own (2011+ or first date)", "", sa.to_markdown()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
