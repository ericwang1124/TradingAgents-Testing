"""Does adapting the strategy to the market regime help out of sample?

    python -m tradingagents.strategies.opening_reversal.regime_study

1. Every grid point from ``optimize.GRID`` is backtested over the whole period and each trade is
   tagged with its session's regime (trend vs 50-day SMA x prior-day VIX bucket, see regime.py).
2. Descriptive: how each regime behaved in 2019-2022 vs 2023-2026, and whether, *within* a
   regime, settings that did well early also did well later.
3. Walk-forward: at the start of every year, using only earlier trades, pick for each regime the
   setting with the best t-stat (min trades / min t, otherwise stand aside), then trade that year.
   Compared against the same procedure without regimes and against the fixed original rules.
"""

from __future__ import annotations

import argparse
import itertools
import multiprocessing as mp
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from . import optimize
from .backtest import eligible_contexts, run_backtest
from .data import load_alpaca_minutes, resample_bars
from .levels import build_day_contexts
from .regime import attach_vix, load_vix, regime_by_date

_CONTEXTS: Dict[int, list] = {}


def combo_key(combo: dict) -> str:
    return (f"{combo['bar_minutes']}m | gap>={combo['min_gap_pct'] * 100:.2f}% | {combo['regime']} | "
            f"{combo['conditions']} | break{combo['break_lookback']} | {combo['exit']}")


ORIGINAL_KEY = combo_key(optimize.ORIGINAL)


def _trades_for(combo: dict) -> pd.DataFrame:
    trades = run_backtest(params=optimize.params_for(combo), contexts=_CONTEXTS[combo["bar_minutes"]])
    if trades.empty:
        return pd.DataFrame(columns=["combo", "date", "r"])
    return pd.DataFrame({"combo": combo_key(combo), "date": trades["date"], "r": trades["r_multiple"]})


def collect_trades(grid: Dict[str, list], processes: int) -> pd.DataFrame:
    combos = [dict(zip(grid, values)) for values in itertools.product(*grid.values())]
    with mp.get_context("fork").Pool(processes) as pool:
        frames = pool.map(_trades_for, combos, chunksize=4)
    return pd.concat(frames, ignore_index=True)


def summarize_r(r: pd.Series) -> dict:
    n = len(r)
    if n == 0:
        return {"trades": 0, "win_%": np.nan, "avg_R": np.nan, "total_R": 0.0, "t": np.nan}
    sd = r.std(ddof=1) if n > 1 else np.nan
    return {
        "trades": n,
        "win_%": (r > 0).mean() * 100,
        "avg_R": r.mean(),
        "total_R": r.sum(),
        "t": r.mean() / (sd / np.sqrt(n)) if n > 2 and sd > 0 else np.nan,
    }


def walk_forward(
    trades: pd.DataFrame,
    years: List[int],
    min_n: int = 15,
    min_t: float = 1.0,
    by_regime: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Expanding-window selection. ``trades`` needs columns combo, date, r, regime.

    For each test year and regime, only trades dated before 1 January of that year are used to
    choose a combo (highest t-stat with at least ``min_n`` trades and t >= ``min_t``); if none
    qualifies the regime is skipped for the year. Returns (out-of-sample trades, choices).
    """
    t = trades.copy()
    t["year"] = pd.to_datetime(t["date"]).dt.year
    if not by_regime:
        t["regime"] = "all"
    t = t[t["regime"].notna()]
    regimes = sorted(t["regime"].unique())
    oos, choices = [], []
    for year in years:
        past, current = t[t["year"] < year], t[t["year"] == year]
        g = past.groupby(["regime", "combo"])["r"]
        stats = pd.DataFrame({"n": g.size(), "mean": g.mean(), "sd": g.std(ddof=1)})
        stats["t"] = stats["mean"] / (stats["sd"] / np.sqrt(stats["n"]))
        stats = stats[(stats["n"] >= min_n) & np.isfinite(stats["t"])]
        for regime in regimes:
            choice, train_t, train_n = None, np.nan, 0
            if regime in stats.index.get_level_values(0):
                s = stats.loc[regime]
                best = s["t"].idxmax()
                if s.loc[best, "t"] >= min_t:
                    choice, train_t, train_n = best, s.loc[best, "t"], int(s.loc[best, "n"])
            picked = current[(current["regime"] == regime) & (current["combo"] == choice)] if choice else current.iloc[0:0]
            choices.append({"year": year, "regime": regime, "choice": choice or "(stand aside)",
                            "train_n": train_n, "train_t": train_t, "oos_n": len(picked),
                            "oos_total_R": picked["r"].sum()})
            oos.append(picked)
    return pd.concat(oos, ignore_index=True), pd.DataFrame(choices)


def _md(df: pd.DataFrame, index: bool = True) -> str:
    try:
        return df.to_markdown(index=index, floatfmt=".2f")
    except ImportError:
        return "```\n" + df.round(2).to_string(index=index) + "\n```"


def build_report(trades: pd.DataFrame, regimes: Dict[date, Optional[str]], split: date,
                 years: List[int], meta: Dict[str, str], min_n: int, min_t: float) -> str:
    trades = trades.copy()
    trades["regime"] = trades["date"].map(regimes)
    trades["period"] = np.where(pd.to_datetime(trades["date"]) < pd.Timestamp(split), "train", "test")

    day_regimes = pd.Series(regimes).dropna()
    day_period = np.where(pd.to_datetime(day_regimes.index) < pd.Timestamp(split), "2019-22", "2023-26")
    freq = pd.crosstab(day_regimes.values, day_period).rename_axis("regime")

    orig = trades[trades["combo"] == ORIGINAL_KEY]
    by_regime = orig.groupby(["regime", "period"])["r"].apply(lambda r: pd.Series(summarize_r(r))).unstack()
    by_regime = by_regime[["trades", "avg_R", "total_R"]].unstack("period")

    # Within each regime: does early performance of a setting predict its later performance?
    stab_rows = []
    for regime, grp in trades.dropna(subset=["regime"]).groupby("regime"):
        pivot = grp.groupby(["combo", "period"])["r"].agg(["size", "mean"]).unstack("period")
        ok = pivot[(pivot[("size", "train")] >= 8) & (pivot[("size", "test")] >= 8)]
        rho = ok[("mean", "train")].rank().corr(ok[("mean", "test")].rank()) if len(ok) > 5 else np.nan
        both = ((ok[("mean", "train")] > 0) & (ok[("mean", "test")] > 0)).sum()
        stab_rows.append({"regime": regime, "settings with >=8 trades in both": len(ok),
                          "rank corr train vs test": rho, "positive in both": both})
    stability = pd.DataFrame(stab_rows).set_index("regime")

    oos_regime, choices = walk_forward(trades, years, min_n, min_t, by_regime=True)
    oos_plain, _ = walk_forward(trades, years, min_n, min_t, by_regime=False)
    oos_gate, gate_choices = walk_forward(orig, years, min_n=10, min_t=0.0, by_regime=True)
    static = orig[pd.to_datetime(orig["date"]).dt.year.isin(years)]
    methods = {
        "regime-adaptive (pick setting per regime)": oos_regime,
        "non-adaptive (pick one setting for all days)": oos_plain,
        "original rules, regime gate (trade regime only if past avg R > 0)": oos_gate,
        "original rules, always": static,
    }
    comp = pd.DataFrame({k: summarize_r(v["r"]) for k, v in methods.items()}).T
    yearly = pd.DataFrame({
        k: v.assign(year=pd.to_datetime(v["date"]).dt.year).groupby("year")["r"].sum() for k, v in methods.items()
    }).reindex(years).fillna(0.0)

    lines = [
        "# Opening reversal short — market-regime study",
        "",
        *(f"- **{k}**: {v}" for k, v in meta.items()),
        "- **Regimes** (fixed, not optimised): trend = prior close vs 50-day SMA; volatility = prior-day VIX close"
        " < 15 / 15-20 / >= 20",
        "",
        "## Walk-forward results (all out of sample)",
        "",
        f"Each year {years[0]}-{years[-1]} is traded with settings chosen only from earlier years "
        f"(best t-stat, >= {min_n} trades, t >= {min_t}; otherwise stand aside).",
        "",
        _md(comp),
        "",
        "Total R by year:",
        "",
        _md(yearly),
        "",
        "## Sessions per regime",
        "",
        _md(freq),
        "",
        "## Original rules by regime",
        "",
        _md(by_regime),
        "",
        "## Within a regime, do good early settings stay good?",
        "",
        _md(stability),
        "",
        "## Regime-adaptive choices",
        "",
        _md(choices, index=False),
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--symbol", default="SPY")
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--split", type=date.fromisoformat, default=date(2023, 1, 1))
    p.add_argument("--first-test-year", type=int, default=2021)
    p.add_argument("--min-trades", type=int, default=15)
    p.add_argument("--min-t", type=float, default=1.0)
    p.add_argument("--processes", type=int, default=max(1, mp.cpu_count()))
    p.add_argument("--out", type=Path, default=Path("results/opening_reversal"))
    args = p.parse_args(argv)

    minutes = load_alpaca_minutes(args.symbol, args.start - timedelta(days=120), args.end)
    vix = load_vix(args.start - timedelta(days=120), args.end)
    for n in optimize.GRID["bar_minutes"]:
        ctxs = [c for c in eligible_contexts(build_day_contexts(resample_bars(minutes, n)))
                if args.start <= c.day.date() <= args.end]
        attach_vix(ctxs, vix)
        _CONTEXTS[n] = ctxs
    regimes = regime_by_date(_CONTEXTS[1])
    print(f"{len(regimes)} sessions; collecting trades for {np.prod([len(v) for v in optimize.GRID.values()])} settings")

    trades = collect_trades(optimize.GRID, args.processes)
    years = list(range(args.first_test_year, args.end.year + 1))
    meta = {
        "Symbol": args.symbol,
        "Data": "Alpaca SIP 1-minute bars (adjusted), VIX daily closes from Yahoo",
        "Period": f"{args.start} to {args.end}",
        "Settings searched": f"{trades['combo'].nunique()} (optimize.GRID)",
        "Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    report = build_report(trades, regimes, args.split, years, meta, args.min_trades, args.min_t)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / "REGIME.md"
    path.write_text(report)
    trades.assign(regime=trades["date"].map(regimes)).to_csv(args.out / "regime_trades.csv", index=False)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
