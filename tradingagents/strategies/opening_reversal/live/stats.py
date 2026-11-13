"""Historical reference numbers for the briefing (written to historical_stats.json, committed)."""

from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

from ..backtest import eligible_contexts, run_backtest
from ..data import load_alpaca_minutes
from ..events import tag_sessions
from ..levels import build_day_contexts
from ..regime import attach_vix, load_vix, regime_by_date
from .settings import LIVE_PARAMS, STATS_PATH, SYMBOL


def _s(r: pd.Series) -> dict:
    n = len(r)
    return {"trades": n, "win_pct": round((r > 0).mean() * 100, 1) if n else None,
            "avg_R": round(r.mean(), 3) if n else None, "total_R": round(r.sum(), 1)}


def compute(start: date = date(2019, 1, 1), end: date = None) -> dict:
    end = end or date.today() - timedelta(days=1)
    minutes = load_alpaca_minutes(SYMBOL, start - timedelta(days=120), end, verbose=False)
    ctxs = [c for c in eligible_contexts(build_day_contexts(minutes)) if start <= c.day.date() <= end]
    attach_vix(ctxs, load_vix(start - timedelta(days=120), end))
    regimes = regime_by_date(ctxs)
    tags = tag_sessions([c.day.date() for c in ctxs], minutes, release_threshold=4.0)
    trades = run_backtest(params=LIVE_PARAMS, contexts=ctxs)
    trades["regime"] = trades["date"].map(regimes)
    trades["major_event"] = trades["date"].map(tags["any_major_event"]).fillna(False).astype(bool)
    clean = trades[~trades["major_event"]]
    return {
        "period": f"{start} to {end}",
        "note": "major-event days excluded except in 'major_event_days'",
        "overall": _s(clean["r_multiple"]),
        "major_event_days": _s(trades.loc[trades["major_event"], "r_multiple"]),
        "other_days": _s(clean["r_multiple"]),
        "by_regime": {k: _s(g["r_multiple"]) for k, g in clean.groupby("regime")},
        "by_year": {str(k): _s(g["r_multiple"]) for k, g in clean.groupby(pd.to_datetime(clean["date"]).dt.year)},
    }


def main() -> None:
    stats = compute()
    STATS_PATH.write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))
