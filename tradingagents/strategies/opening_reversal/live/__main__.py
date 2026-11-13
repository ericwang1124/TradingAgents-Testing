"""python -m tradingagents.strategies.opening_reversal.live <command>

  briefing   pre-market briefing -> journal/opening_reversal/<date>/briefing.{json,md}
  decide     record the GO / NO_GO decision (hard rules always win)
  run        watch 09:35-10:30 and trade the signal on Alpaca paper if the decision is GO
  flatten    close this strategy's 0DTE puts for the day (safety net)
  evaluate   shadow outcomes for past journal days + SUMMARY.md
  stats      recompute historical_stats.json used by the briefing
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
    for name in ("briefing", "run", "flatten", "evaluate"):
        s = sub.add_parser(name)
        s.add_argument("--date", type=date.fromisoformat, default=None)
        if name == "run":
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
        decision = args.decision
        notes = []
        if b.get("hard_no_go") and decision == "GO":
            decision = "NO_GO"
            notes.append("overridden: hard rule(s) " + ", ".join(k for k, v in b["hard_rules"].items() if v))
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


if __name__ == "__main__":
    main()
