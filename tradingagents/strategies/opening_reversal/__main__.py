"""CLI: python -m tradingagents.strategies.opening_reversal --source alpaca --start 2019-01-01

Runs every variant in ``VARIANTS`` on the same sessions and writes REPORT.md, summary.csv,
per-variant trade lists and an equity-curve chart to ``--out``.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

from .backtest import eligible_contexts, run_backtest
from .config import VARIANTS, StrategyParams
from .data import load_alpaca_minutes, load_yfinance_bars
from .levels import build_day_contexts
from .report import summarize, write_report


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--symbol", default="SPY")
    p.add_argument("--source", choices=["alpaca", "yfinance"], default="alpaca")
    p.add_argument("--interval", default="5m", help="yfinance only: 1m (~30 days) or 5m (~60 days)")
    p.add_argument("--feed", default="sip", help="alpaca feed: sip (all exchanges) or iex")
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--out", type=Path, default=Path("results/opening_reversal"))
    args = p.parse_args(argv)

    base = StrategyParams()
    if args.source == "alpaca":
        from .data import AlpacaBarsClient

        print(f"Loading {args.symbol} 1-minute bars {args.start}..{args.end} from Alpaca")
        # one month of warm-up for prior-day levels and the relative-volume baseline
        bars = load_alpaca_minutes(args.symbol, args.start - timedelta(days=45), args.end,
                                   client=AlpacaBarsClient(feed=args.feed))
        source = f"Alpaca {args.feed.upper()} 1-minute bars (split+dividend adjusted)"
    else:
        print(f"Loading {args.symbol} {args.interval} bars from yfinance (recent data only)")
        bars = load_yfinance_bars(args.symbol, args.interval)
        source = f"yfinance {args.interval} bars (recent window only — smoke test, not statistically meaningful)"

    contexts = build_day_contexts(bars, base)
    contexts = [c for c in eligible_contexts(contexts) if c.day.date() >= args.start]
    if not contexts:
        raise SystemExit("No eligible sessions (need ~20 sessions of warm-up for the volume baseline).")
    sessions = len(contexts)
    gap_days = sum(1 for c in contexts if -base.max_gap_pct <= c.gap_pct <= -base.min_gap_pct)
    print(f"{sessions} sessions ({contexts[0].day.date()} .. {contexts[-1].day.date()}), {gap_days} gap-down days")

    results = {}
    for name, params in VARIANTS.items():
        trades = run_backtest(params=params, contexts=contexts)
        results[name] = trades
        s = summarize(trades, sessions)
        if s["trades"]:
            print(f"  {name:<28} n={s['trades']:>4}  win={s['win_rate_%']:5.1f}%  avgR={s['avg_R']:+.3f}  "
                  f"totalR={s['total_R']:+7.1f}  PF={s['profit_factor']:.2f}  t={s['t_stat']:+.2f}")
        else:
            print(f"  {name:<28} no trades")

    meta = {
        "Symbol": args.symbol,
        "Data": source,
        "Period": f"{contexts[0].day.date()} to {contexts[-1].day.date()}",
        "Gap-down sessions": f"{gap_days} (open <= -{base.min_gap_pct*100:.2f}% vs prior close)",
        "Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    path = write_report(results, sessions, args.out, meta, base)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
