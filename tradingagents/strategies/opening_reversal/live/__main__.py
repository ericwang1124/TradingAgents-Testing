"""python -m tradingagents.strategies.opening_reversal.live <command>

Current framework (paper):
  briefing     pre-market briefing -> journal/opening_reversal/<date>/briefing.{json,md}
  decide       record Claude's GO / NO_GO for the intraday add-on (add-on hard rules always win)
  wait-until   sleep until HH:MM ET (to chain runs inside the 2-hour background limit)
  addon        10:00 high-efficiency open continuation, long SPY, out at 11:55 (only on GO)
  core         end-of-day rebalance of the core ETF portfolio with market-on-close orders
  core-weights yearly refit of the core strategy weights (saved to core_weights.json)
  evaluate     shadow outcomes (add-on and fade) for journal days + SUMMARY.md
Legacy (fade strategy, kept for shadow logging only):
  run, flatten, stats
"""

from __future__ import annotations

import argparse
import json
from datetime import date

import pandas as pd

from ..data import NY
from . import journal


def _today() -> date:
    return pd.Timestamp.now(tz=NY).date()


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("briefing", "run", "flatten", "evaluate", "addon", "core"):
        s = sub.add_parser(name)
        s.add_argument("--date", type=date.fromisoformat, default=None)
        if name in ("run", "addon", "core"):
            s.add_argument("--dry-run", action="store_true", help="detect and plan, but send no orders")
        if name == "evaluate":
            s.add_argument("--force", action="store_true")
            s.add_argument("--include-today", action="store_true", help="also evaluate today (after ~11:00 ET)")
    d = sub.add_parser("decide")
    d.add_argument("--date", type=date.fromisoformat, default=None)
    d.add_argument("--decision", choices=["GO", "NO_GO"], required=True)
    d.add_argument("--size", type=float, default=1.0, help="0-1 multiplier on the normal risk")
    d.add_argument("--confidence", type=float, required=True, help="0-1")
    d.add_argument("--reason", action="append", required=True, help="repeat for each reason")
    d.add_argument("--sources", action="append", default=[], help="URLs / sources consulted")
    sub.add_parser("stats")
    cw = sub.add_parser("core-weights")
    cw.add_argument("--year", type=int, default=None)
    wu = sub.add_parser("wait-until")
    wu.add_argument("hhmm", help="e.g. 09:57 (America/New_York)")
    args = p.parse_args(argv)
    day = getattr(args, "date", None) or _today()

    if args.cmd == "briefing":
        from .briefing import briefing_markdown, build_briefing

        b = build_briefing(day)
        journal.write(day, "briefing", b)
        md = briefing_markdown(b)
        (journal.day_dir(day) / "briefing.md").write_text(md)
        print(md)
    elif args.cmd == "decide":
        b = journal.read(day, "briefing")
        if b is None:
            raise SystemExit("Run `briefing` first.")
        from .addon import HARD_RULES as ADDON_RULES

        decision = args.decision
        notes = []
        hit = [k for k in ADDON_RULES if (b.get("hard_rules") or {}).get(k)]
        if hit and decision == "GO":
            decision = "NO_GO"
            notes.append("overridden: hard rule(s) " + ", ".join(hit))
        payload = {"date": day.isoformat(), "decision": decision, "size": max(0.0, min(args.size, 1.0)),
                   "confidence": args.confidence, "reasons": args.reason + notes, "sources": args.sources,
                   "decided_at": pd.Timestamp.now(tz=NY).isoformat()}
        journal.write(day, "decision", payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.cmd == "run":
        from .executor import run

        run(day, dry_run=args.dry_run)
    elif args.cmd == "flatten":
        from .executor import flatten_strategy_positions

        print(flatten_strategy_positions(day))
    elif args.cmd == "evaluate":
        from .evaluate import evaluate_pending

        print("evaluated:", evaluate_pending(day, force=args.force, include_today=args.include_today))
    elif args.cmd == "stats":
        from .stats import main as stats_main

        stats_main()
    elif args.cmd == "addon":
        from .addon import run as addon_run

        addon_run(day, dry_run=args.dry_run)
    elif args.cmd == "core":
        from .core_rebalance import rebalance

        rec = rebalance(day, dry_run=args.dry_run)
        print(json.dumps({k: rec.get(k) for k in ("gross_exposure", "order_type", "orders", "submitted", "unfilled", "skipped")},
                         indent=2, default=str))
    elif args.cmd == "core-weights":
        from .core_rebalance import save_weights

        print(json.dumps(save_weights(args.year or day.year), indent=2))
    elif args.cmd == "wait-until":
        import time as _t

        hh, mm = (int(x) for x in args.hhmm.split(":"))
        target = pd.Timestamp.now(tz=NY).normalize() + pd.Timedelta(hours=hh, minutes=mm)
        while (rem := (target - pd.Timestamp.now(tz=NY)).total_seconds()) > 0:
            _t.sleep(min(rem, 30))
        print("reached", args.hhmm)


if __name__ == "__main__":
    main()
