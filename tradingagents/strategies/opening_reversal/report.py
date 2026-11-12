"""Summary statistics, variant comparison table, equity curves and a markdown report."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from .config import StrategyParams


def summarize(trades: pd.DataFrame, sessions: int) -> Dict[str, float]:
    if trades.empty:
        return {"trades": 0, "trade_freq_%": 0.0}
    r = trades["r_multiple"]
    wins, losses = r[r > 0], r[r <= 0]
    equity = r.cumsum()
    drawdown = (equity - equity.cummax()).min()
    return {
        "trades": int(len(r)),
        "trade_freq_%": len(r) / sessions * 100,
        "win_rate_%": (r > 0).mean() * 100,
        "avg_R": r.mean(),
        "median_R": r.median(),
        "total_R": r.sum(),
        "profit_factor": wins.sum() / -losses.sum() if losses.sum() < 0 else np.inf,
        "max_dd_R": drawdown,
        "avg_win_R": wins.mean() if len(wins) else 0.0,
        "avg_loss_R": losses.mean() if len(losses) else 0.0,
        "stopped_%": trades["exit_reason"].str.startswith("stop").mean() * 100,
        "avg_risk_%": trades["risk_pct"].mean(),
        "avg_minutes": trades["minutes_held"].mean(),
        # t-stat of mean R; |t| < 2 means "cannot tell from noise"
        "t_stat": r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 2 and r.std() > 0 else np.nan,
    }


def by_year(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    t = trades.assign(year=pd.to_datetime(trades["date"]).dt.year)
    g = t.groupby("year")["r_multiple"]
    return pd.DataFrame({
        "trades": g.size(),
        "win_rate_%": g.apply(lambda s: (s > 0).mean() * 100),
        "avg_R": g.mean(),
        "total_R": g.sum(),
    })


def plot_equity(results: Dict[str, pd.DataFrame], path: Path) -> bool:
    try:
        import matplotlib
    except ImportError:  # optional dependency
        return False

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5), dpi=120)
    for name, trades in results.items():
        if trades.empty:
            continue
        curve = trades.set_index(pd.to_datetime(trades["date"]))["r_multiple"].cumsum()
        ax.plot(curve.index, curve.values, label=f"{name} ({len(trades)})", linewidth=1.6)
    ax.axhline(0, color="#888", linewidth=0.8)
    ax.set_ylabel("Cumulative R")
    ax.set_title("SPY opening reversal short — cumulative R by variant (underlying, not options)")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True


def _fmt(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(floatfmt=".2f")
    except ImportError:  # tabulate not installed
        return "```\n" + df.round(2).to_string() + "\n```"


def write_report(
    results: Dict[str, pd.DataFrame],
    sessions: int,
    out_dir: Path,
    meta: Dict[str, str],
    base_params: StrategyParams,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame({name: summarize(t, sessions) for name, t in results.items()}).T
    table.to_csv(out_dir / "summary.csv")
    for name, trades in results.items():
        safe = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
        trades.to_csv(out_dir / f"trades_{safe}.csv", index=False)
    has_chart = plot_equity(results, out_dir / "equity_curves.png")

    full_name = next((n for n in results if n.startswith("full")), None)
    lines = [
        "# SPY opening-hour gap-down reversal short — phase 1 backtest",
        "",
        *(f"- **{k}**: {v}" for k, v in meta.items()),
        f"- **Sessions evaluated**: {sessions}",
        "",
        "Results are measured on the SPY underlying in R (multiples of the initial stop distance).",
        "They are **not** 0DTE option P&L; option pricing is phase 3.",
        "",
        "## Variant comparison",
        "",
        _fmt(table),
        "",
        "![equity](equity_curves.png)" if has_chart else "_(install matplotlib for the equity chart)_",
        "",
    ]
    if full_name and not results[full_name].empty:
        full = results[full_name]
        lines += [
            f"## Full strategy by year",
            "",
            _fmt(by_year(full)),
            "",
            "## Full strategy by rejection zone",
            "",
            _fmt(full.groupby("zone")["r_multiple"].agg(["size", "mean", "sum"]).rename(
                columns={"size": "trades", "mean": "avg_R", "sum": "total_R"})),
            "",
            "## Exit reasons (full strategy)",
            "",
            _fmt(full["exit_reason"].value_counts().to_frame("trades")),
            "",
        ]
    lines += ["## Parameters (full strategy)", "", "```"]
    lines += [f"{k} = {v}" for k, v in asdict(base_params).items()]
    lines += ["```", ""]
    path = out_dir / "REPORT.md"
    path.write_text("\n".join(lines))
    return path
