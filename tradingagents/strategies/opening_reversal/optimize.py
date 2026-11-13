"""Walk-forward parameter search: choose settings on a training window, judge them on a later,
untouched test window.

    python -m tradingagents.strategies.opening_reversal.optimize --split 2023-01-01

Every grid point is backtested once over the whole period; trades are then split by date.
Ranking uses the *training* t-stat only. The test columns are what you should believe. The
report also shows how well training performance predicts test performance across the grid:
if that rank correlation is ~0, the "best" settings are noise.
"""

from __future__ import annotations

import argparse
import itertools
import multiprocessing as mp
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .backtest import eligible_contexts, run_backtest
from .config import StrategyParams
from .data import load_alpaca_minutes, resample_bars
from .levels import build_day_contexts

CONDITIONS: Dict[str, dict] = {
    "gap_only": dict(require_exhaustion=False, require_zone=False),
    "gap+exhaustion": dict(require_zone=False),
    "gap+zone": dict(require_exhaustion=False),
    "full": {},
}
EXITS: Dict[str, dict] = {
    "1R all": dict(take_profits=((1.0, 1.0),)),
    "1R/2R half": dict(take_profits=((1.0, 0.5), (2.0, 0.5))),
}
GRID: Dict[str, list] = {
    "bar_minutes": [1, 5],
    "min_gap_pct": [0.0015, 0.003, 0.005],
    "regime": ["any", "below_sma20"],
    "conditions": list(CONDITIONS),
    "break_lookback": [1, 3],
    "exit": list(EXITS),
}
ORIGINAL = dict(bar_minutes=1, min_gap_pct=0.0015, regime="any", conditions="full", break_lookback=1, exit="1R/2R half")

_CONTEXTS: Dict[int, list] = {}  # bar_minutes -> contexts; filled before the worker pool forks
_SPLIT: date = date(2023, 1, 1)


def params_for(combo: dict) -> StrategyParams:
    return replace(
        StrategyParams(),
        min_gap_pct=combo["min_gap_pct"],
        regime=combo["regime"],
        break_lookback=combo["break_lookback"],
        **CONDITIONS[combo["conditions"]],
        **EXITS[combo["exit"]],
    )


def _stats(r: pd.Series, prefix: str) -> dict:
    n = len(r)
    out = {f"{prefix}_n": n}
    if n == 0:
        return {**out, f"{prefix}_win%": np.nan, f"{prefix}_avgR": np.nan, f"{prefix}_totR": 0.0,
                f"{prefix}_PF": np.nan, f"{prefix}_t": np.nan}
    losses = -r[r <= 0].sum()
    sd = r.std(ddof=1) if n > 1 else np.nan
    return {
        **out,
        f"{prefix}_win%": (r > 0).mean() * 100,
        f"{prefix}_avgR": r.mean(),
        f"{prefix}_totR": r.sum(),
        f"{prefix}_PF": r[r > 0].sum() / losses if losses > 0 else np.inf,
        f"{prefix}_t": r.mean() / (sd / np.sqrt(n)) if n > 2 and sd > 0 else np.nan,
    }


def evaluate(combo: dict) -> dict:
    trades = run_backtest(params=params_for(combo), contexts=_CONTEXTS[combo["bar_minutes"]])
    if trades.empty:
        r_train = r_test = pd.Series(dtype=float)
    else:
        is_test = pd.to_datetime(trades["date"]) >= pd.Timestamp(_SPLIT)
        r_train = trades.loc[~is_test, "r_multiple"]
        r_test = trades.loc[is_test, "r_multiple"]
    return {**combo, **_stats(r_train, "train"), **_stats(r_test, "test")}


def run_grid(grid: Dict[str, list], processes: int) -> pd.DataFrame:
    combos = [dict(zip(grid, values)) for values in itertools.product(*grid.values())]
    with mp.get_context("fork").Pool(processes) as pool:
        rows = pool.map(evaluate, combos, chunksize=4)
    return pd.DataFrame(rows)


def write_report(table: pd.DataFrame, out_dir: Path, meta: Dict[str, str], min_train: int, top: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "optimization.csv", index=False)
    keys = list(GRID)
    eligible = table[table["train_n"] >= min_train].sort_values("train_t", ascending=False)
    both = table[(table["train_n"] >= 20) & (table["test_n"] >= 20)]
    rho = both["train_avgR"].rank().corr(both["test_avgR"].rank()) if len(both) > 3 else np.nan
    show = keys + ["train_n", "train_win%", "train_avgR", "train_t", "test_n", "test_win%", "test_avgR",
                   "test_totR", "test_PF", "test_t"]
    original = table
    for k, v in ORIGINAL.items():
        original = original[original[k] == v]

    def md(df):
        df = df.copy()
        if "min_gap_pct" in df.columns:  # 0.0015 would otherwise print as 0.002
            df["min_gap_pct"] = df["min_gap_pct"].map(lambda v: f"{v * 100:.2f}%")
        try:
            return df.to_markdown(index=False, floatfmt=".3f")
        except ImportError:
            return "```\n" + df.round(3).to_string(index=False) + "\n```"

    best = eligible.head(1)
    lines = [
        "# Opening reversal short — walk-forward optimisation",
        "",
        *(f"- **{k}**: {v}" for k, v in meta.items()),
        f"- **Grid size**: {len(table)} combinations; ranked by training t-stat among those with "
        f">= {min_train} training trades ({len(eligible)} qualify)",
        "",
        "## Does training performance predict test performance?",
        "",
        f"- Spearman rank correlation of avg R, train vs test (combos with >= 20 trades in both): **{rho:+.2f}**",
        f"- Combos with positive avg R — train: {(table['train_avgR'] > 0).sum()}, "
        f"test: {(table['test_avgR'] > 0).sum()} of {len(table)}",
        f"- Combos positive in **both** periods: {((table['train_avgR'] > 0) & (table['test_avgR'] > 0)).sum()}",
        "",
        "## Selected on training data (top 1) — the honest out-of-sample estimate",
        "",
        md(best[show]),
        "",
        f"## Top {top} by training t-stat",
        "",
        md(eligible.head(top)[show]),
        "",
        "## Original rules for reference",
        "",
        md(original[show]),
        "",
        "## Marginal effect of each knob (mean of test avg R across all other settings)",
        "",
    ]
    for k in keys:
        g = table.groupby(k).agg(train_avgR=("train_avgR", "mean"), test_avgR=("test_avgR", "mean"),
                                 test_n=("test_n", "mean"))
        lines += [f"**{k}**", "", md(g.reset_index()), ""]
    path = out_dir / "OPTIMIZATION.md"
    path.write_text("\n".join(lines))
    return path


def main(argv=None) -> None:
    global _SPLIT
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--symbol", default="SPY")
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--split", type=date.fromisoformat, default=date(2023, 1, 1), help="first day of the test window")
    p.add_argument("--min-train-trades", type=int, default=30)
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--processes", type=int, default=max(1, mp.cpu_count()))
    p.add_argument("--out", type=Path, default=Path("results/opening_reversal"))
    args = p.parse_args(argv)
    _SPLIT = args.split

    # ~4 months of warm-up so the 50-day average and volume baseline exist on day one
    minutes = load_alpaca_minutes(args.symbol, args.start - timedelta(days=120), args.end)
    for n in GRID["bar_minutes"]:
        ctxs = build_day_contexts(resample_bars(minutes, n))
        _CONTEXTS[n] = [c for c in eligible_contexts(ctxs) if args.start <= c.day.date() <= args.end]
    sessions = len(_CONTEXTS[1])
    n_train = sum(c.day.date() < args.split for c in _CONTEXTS[1])
    print(f"{sessions} sessions: train {n_train} (< {args.split}), test {sessions - n_train}")

    table = run_grid(GRID, args.processes)
    meta = {
        "Symbol": args.symbol,
        "Data": "Alpaca SIP 1-minute bars (split+dividend adjusted), optionally aggregated to 5 minutes",
        "Train": f"{args.start} to {args.split - timedelta(days=1)} ({n_train} sessions)",
        "Test": f"{args.split} to {args.end} ({sessions - n_train} sessions)",
        "Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    path = write_report(table, args.out, meta, args.min_train_trades, args.top)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
