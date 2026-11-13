"""Should the opening reversal short avoid (or prefer) scheduled-event days?

    python -m tradingagents.strategies.opening_reversal.event_study

Event tags come from ``events.tag_sessions`` and are all known before the open. For three
signal sets (original rules, gap-down only, every-session candidates) the report compares
average R on event vs non-event days in an early and a late period, and shows what a fixed
"skip event days" rule would have done. No parameters are fitted, so there is nothing to
over-fit beyond the choice of which events to look at — all of them are reported.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import eligible_contexts, run_backtest
from .config import VARIANTS
from .data import load_alpaca_minutes
from .events import tag_sessions
from .levels import build_day_contexts
from .patterns import candidate_params

EVENT_COLUMNS = ["fomc_day", "fomc_next_day", "macro_830", "opex", "quad_witching", "megacap_earnings",
                 "any_major_event"]
SIGNAL_SETS = {
    "original rules": VARIANTS["full (gap+exhaustion+zone)"],
    "gap-down reversal": VARIANTS["gap_only"],
    "every-session candidate": candidate_params(),
}


def _cell(r: pd.Series) -> str:
    if len(r) == 0:
        return "–"
    return f"{r.mean():+.2f} ({len(r)})"


def event_table(trades: pd.DataFrame, tags: pd.DataFrame, split: date) -> pd.DataFrame:
    t = trades.join(tags, on="date")
    early = pd.to_datetime(t["date"]) < pd.Timestamp(split)
    rows = {}
    for ev in EVENT_COLUMNS:
        on = t[ev].fillna(False).astype(bool)
        rows[ev] = {
            "event days, early": _cell(t.loc[on & early, "r_multiple"]),
            "other days, early": _cell(t.loc[~on & early, "r_multiple"]),
            "event days, late": _cell(t.loc[on & ~early, "r_multiple"]),
            "other days, late": _cell(t.loc[~on & ~early, "r_multiple"]),
        }
    return pd.DataFrame(rows).T


def _md(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown()
    except ImportError:
        return "```\n" + df.to_string() + "\n```"


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--symbol", default="SPY")
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--split", type=date.fromisoformat, default=date(2023, 1, 1))
    p.add_argument("--release-threshold", type=float, default=4.0,
                   help="08:30-08:34 / 08:00-08:29 pre-market volume ratio that marks an 8:30 release")
    p.add_argument("--out", type=Path, default=Path("results/opening_reversal"))
    args = p.parse_args(argv)

    minutes = load_alpaca_minutes(args.symbol, args.start - timedelta(days=120), args.end, verbose=False)
    contexts = [c for c in eligible_contexts(build_day_contexts(minutes)) if args.start <= c.day.date() <= args.end]
    sessions = [c.day.date() for c in contexts]
    tags = tag_sessions(sessions, minutes, args.release_threshold)
    freq = tags[EVENT_COLUMNS].mean().mul(100).round(1).to_frame("% of sessions")

    lines = [
        "# Opening reversal short — scheduled-event days",
        "",
        f"- **Period**: {sessions[0]} to {sessions[-1]} ({len(sessions)} sessions); early/late split at {args.split}",
        "- **Cells**: average R (number of trades)",
        f"- **macro_830**: pre-market volume burst at 08:30 >= {args.release_threshold}x the 08:00-08:29 rate "
        "(catches ~88% of 2025-26 CPI/jobs days; about half the flags are other market-moving 8:30 data)",
        "- **any_major_event**: FOMC day, day after FOMC, or macro_830",
        f"- **Generated**: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## How common each event is",
        "",
        _md(freq),
        "",
    ]
    skip_rows = {}
    for name, params in SIGNAL_SETS.items():
        trades = run_backtest(params=params, contexts=contexts)
        lines += [f"## {name}", "", _md(event_table(trades, tags, args.split)), ""]
        t = trades.join(tags, on="date")
        for label, mask in (("all days", pd.Series(True, index=t.index)),
                            ("skip any_major_event", ~t["any_major_event"].astype(bool)),
                            ("only any_major_event", t["any_major_event"].astype(bool))):
            r = t.loc[mask, "r_multiple"]
            sd = r.std(ddof=1)
            skip_rows[(name, label)] = {
                "trades": len(r), "avg_R": r.mean(), "total_R": r.sum(),
                "t": r.mean() / (sd / np.sqrt(len(r))) if len(r) > 2 and sd > 0 else np.nan,
            }
    skip = pd.DataFrame(skip_rows).T
    lines += ["## Fixed rule: skip / only major-event days (whole period)", "", _md(skip.round(3)), ""]
    args.out.mkdir(parents=True, exist_ok=True)
    tags.to_csv(args.out / "event_tags.csv")
    path = args.out / "EVENTS.md"
    path.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
