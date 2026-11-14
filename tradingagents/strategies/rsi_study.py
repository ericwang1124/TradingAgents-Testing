"""RSI(30) < 35 buy / > 65 sell, long-only, across many underlyings.

    python -m tradingagents.strategies.rsi_study

Rule: Wilder RSI over 30 daily closes. Buy at the close when RSI < 35, hold until the close on which
RSI > 65, then sell; out of the market the money earns T-bills (BIL). 2 bp per side.
Sharpe = annualised mean / std of daily excess returns over T-bills (0 while out).
Compared with buy-and-hold of the same underlying over the same days.

Robustness: the same rule over each half of the sample, and a grid of nearby settings
(RSI period 14/20/30/40/50 x buy level 30/35/40 x sell level 60/65/70) to see whether 30/35/65 is
a lucky spot or a broad plateau.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from .core_portfolio import _hold_until, _rsi
from .opening_reversal.data import default_cache_dir
from .strategy_atlas import load_ohlc

START = "2007-06-01"
COST_BP = 2.0
GROUPS = {
    "US equity": ["SPY", "QQQ", "IWM", "DIA", "RSP", "MDY", "IJR", "IWD", "IWF", "USMV"],
    "US sectors": ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "VNQ"],
    "Developed ex-US": ["EFA", "VGK", "SCZ", "EWJ", "EWG", "EWU", "EWQ", "EWL", "EWP", "EWI", "EWN", "EWD",
                        "EWA", "EWC", "EWH", "EWS"],
    "Emerging": ["EEM", "EWT", "EWY", "EWZ", "EWW", "FXI", "MCHI", "INDA", "EIDO", "THD", "EZA", "TUR", "ECH",
                 "EPOL", "EWM", "ARGT", "VNM", "EPHE"],
    "Bonds": ["TLT", "IEF", "TIP", "LQD", "HYG"],
    "Commodities, FX, crypto, vol": ["GLD", "DBC", "USO", "UUP", "FXE", "FXY", "BTC-USD", "VIXY", "SVXY"],
}
GRID_N, GRID_LO, GRID_HI = (14, 20, 30, 40, 50), (30, 35, 40), (60, 65, 70)
OUT = Path("results/opening_reversal/RSI_STUDY.md")


def load_closes() -> pd.DataFrame:
    d = load_ohlc()
    closes = {t: d[t]["Close"] for t in d}
    cache = default_cache_dir() / "equity_indices"
    for f in cache.glob("*.csv"):
        closes.setdefault(f.stem, pd.read_csv(f, index_col=0, parse_dates=True)["Close"])
    return pd.DataFrame(closes)


def rsi_position(c: pd.Series, n: int = 30, lo: float = 35, hi: float = 65) -> pd.Series:
    rs = _rsi(c, n)
    rs[: 3 * n] = np.nan                                  # let Wilder smoothing settle
    return _hold_until(rs < lo, rs > hi)


def run_one(c: pd.Series, rf: pd.Series, n: int = 30, lo: float = 35, hi: float = 65,
            start: str = START) -> Dict[str, object]:
    c = c.dropna()
    pos = rsi_position(c, n, lo, hi)
    r = c.pct_change()
    rfr = rf.reindex(c.index).fillna(0.0)
    ex = r - rfr
    turn = pos.diff().abs().fillna(0.0)
    strat = pos.shift(1) * ex - turn * COST_BP / 1e4          # signal at close t, held from close t
    keep = c.index >= max(pd.Timestamp(start), c.index[0] + pd.Timedelta(days=200))
    return {"strat": strat[keep].fillna(0.0), "bh": ex[keep].fillna(0.0), "pos": pos[keep], "r": r[keep]}


def sharpe(x: pd.Series) -> float:
    return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else float("nan")


def max_dd(x: pd.Series) -> float:
    eq = (1 + x).cumprod()
    return float((eq / eq.cummax() - 1).min() * 100)


def trades(pos: pd.Series, r: pd.Series) -> pd.DataFrame:
    """One row per round trip (an open trade at the end is closed at the last price)."""
    p = pos.to_numpy()
    out, entry = [], None
    idx = pos.index
    for i in range(len(p)):
        if entry is None and p[i] == 1:
            entry = i
        elif entry is not None and p[i] == 0:
            out.append((idx[entry], idx[i], i - entry, float(np.prod(1 + r.iloc[entry + 1:i + 1]) - 1)))
            entry = None
    if entry is not None:
        out.append((idx[entry], idx[-1], len(p) - 1 - entry, float(np.prod(1 + r.iloc[entry + 1:]) - 1)))
    return pd.DataFrame(out, columns=["entry", "exit", "days", "ret"])


def summary(res: Dict[str, object]) -> Dict[str, float]:
    s, b, pos, r = res["strat"], res["bh"], res["pos"], res["r"]
    t = trades(pos, r)
    mid = s.index[0] + (s.index[-1] - s.index[0]) / 2
    return {"start": str(s.index[0].date()), "Sharpe": sharpe(s), "B&H Sharpe": sharpe(b),
            "1st half": sharpe(s[s.index < mid]), "2nd half": sharpe(s[s.index >= mid]),
            "maxDD %": max_dd(s), "B&H maxDD %": max_dd(b),
            "ann % (excess)": float(((1 + s).prod() ** (252 / len(s)) - 1) * 100),
            "time in market %": float(pos.mean() * 100), "trades": len(t),
            "win %": float((t["ret"] > 0).mean() * 100) if len(t) else np.nan,
            "avg trade %": float(t["ret"].mean() * 100) if len(t) else np.nan,
            "avg days held": float(t["days"].mean()) if len(t) else np.nan}


def grid(c: pd.Series, rf: pd.Series) -> pd.Series:
    vals = {}
    for n in GRID_N:
        for lo in GRID_LO:
            for hi in GRID_HI:
                vals[(n, lo, hi)] = sharpe(run_one(c, rf, n, lo, hi)["strat"])
    return pd.Series(vals)


def run() -> Dict[str, pd.DataFrame]:
    C = load_closes()
    rf = C["BIL"].pct_change()
    rows, grids = [], {}
    for g, tickers in GROUPS.items():
        for t in tickers:
            if t not in C or C[t].dropna().index[-1] < pd.Timestamp("2026-01-01"):
                continue
            res = run_one(C[t], rf)
            row = {"group": g, "ticker": t, **summary(res)}
            gr = grid(C[t], rf)
            grids[t] = gr
            row["grid median Sharpe"] = float(gr.median())
            row["rank of 30/35/65 in grid %"] = float((gr < gr[(30, 35, 65)]).mean() * 100)
            rows.append(row)
    table = pd.DataFrame(rows).set_index("ticker")
    # long history for SPY
    spy_long = summary(run_one(C["SPY"], rf, start="1993-01-01"))
    return {"table": table, "grids": pd.DataFrame(grids), "spy_long": spy_long,
            "spy_trades": trades(run_one(C["SPY"], rf, start="1993-01-01")["pos"], run_one(C["SPY"], rf, start="1993-01-01")["r"])}


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    res = run()
    t = res["table"]
    cols = ["group", "start", "Sharpe", "B&H Sharpe", "1st half", "2nd half", "maxDD %", "B&H maxDD %",
            "time in market %", "trades", "win %", "avg trade %", "avg days held", "grid median Sharpe",
            "rank of 30/35/65 in grid %"]
    by_group = t.groupby("group", sort=False).agg(
        n=("Sharpe", "size"), median_Sharpe=("Sharpe", "median"), median_BH_Sharpe=("B&H Sharpe", "median"),
        beats_BH=("Sharpe", lambda s: int((s > t.loc[s.index, "B&H Sharpe"]).sum())),
        median_time_in=("time in market %", "median"), median_trades=("trades", "median"))
    st = res["spy_trades"].copy()
    st["entry"], st["exit"] = st["entry"].dt.date, st["exit"].dt.date
    st["ret %"] = (st.pop("ret") * 100).round(1)
    lines = ["# RSI(30) < 35 buy / > 65 sell across underlyings", "", "```", __doc__.strip(), "```", "",
             "## By group", "", by_group.round(2).to_markdown(), "",
             "## Every underlying (from 2007-06 or first date)", "", t[cols].round(2).to_markdown(), "",
             "## SPY since 1993", "", pd.Series(res["spy_long"]).to_frame("SPY").T.round(2).to_markdown(), "",
             "SPY round trips since 1993:", "", st.to_markdown(index=False), "",
             "## Parameter grid Sharpe, median across underlyings", "",
             res["grids"].median(axis=1).unstack([1, 2]).round(2).to_markdown()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
