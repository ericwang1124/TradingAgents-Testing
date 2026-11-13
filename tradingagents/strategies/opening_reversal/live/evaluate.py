"""After the fact: what would the signal have done on each journal day (traded or not), and how
did the decisions sort good days from bad ones? Writes evaluation.json per day and SUMMARY.md."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ..backtest import simulate_short
from ..data import load_alpaca_minutes
from ..levels import build_day_contexts
from ..signals import find_signal
from . import journal
from .settings import HISTORY_DAYS, JOURNAL_DIR, LIVE_PARAMS, SHADOW_PARAMS, SYMBOL


def shadow_outcomes(day: date) -> Dict[str, Any]:
    minutes = load_alpaca_minutes(SYMBOL, day - timedelta(days=HISTORY_DAYS), day, verbose=False)
    ctxs = [c for c in build_day_contexts(minutes) if c.day.date() == day]
    if not ctxs:
        return {"available": False}
    ctx = ctxs[0]
    out: Dict[str, Any] = {"available": True, "gap_pct": round(ctx.gap_pct * 100, 3)}
    from .addon import shadow as addon_shadow

    out["addon"] = addon_shadow(day, minutes)
    for name, params in {"live_signal": LIVE_PARAMS, **SHADOW_PARAMS}.items():
        sig = find_signal(ctx, params)
        if sig is None:
            out[name] = None
            continue
        t = simulate_short(ctx, sig, params)
        out[name] = {k: t[k] for k in ("entry_time", "exit_time", "entry", "stop", "r_multiple", "exit_reason")}
    return out


def evaluate_pending(today: date, force: bool = False, include_today: bool = False) -> List[date]:
    """Evaluate journal days before ``today`` (and ``today`` itself if ``include_today``; SIP data
    for the morning window is available ~15 minutes after it ends)."""
    done = []
    for day in journal.journal_days():
        if (day > today if include_today else day >= today) or (journal.read(day, "evaluation") and not force):
            continue
        if not journal.read(day, "briefing"):
            continue
        journal.write(day, "evaluation", shadow_outcomes(day))
        done.append(day)
    write_summary()
    return done


def summary_table() -> pd.DataFrame:
    rows = []
    for day in journal.journal_days():
        b, d = journal.read(day, "briefing") or {}, journal.read(day, "decision") or {}
        e, ev = journal.read(day, "execution") or {}, journal.read(day, "evaluation") or {}
        live = (ev or {}).get("live_signal")
        ad, adr = (ev or {}).get("addon") or {}, journal.read(day, "addon") or {}
        core = journal.read(day, "core") or {}
        rows.append({
            "date": day.isoformat(),
            "decision": d.get("decision", "—"),
            "confidence": d.get("confidence"),
            "regime": (b.get("regime") or {}).get("label"),
            "addon_efficiency": ad.get("efficiency"),
            "addon_signal": ad.get("take"),
            "addon_shadow_ret_%": ad.get("return_pct", np.nan),
            "addon_traded": adr.get("traded", False),
            "addon_pnl_usd": adr.get("pnl_usd", np.nan),
            "core_gross": core.get("gross_exposure"),
            "core_orders": len(core.get("orders", [])),
            "core_unfilled": len(core.get("unfilled", [])),
            "fade_signal": bool(live),
            "fade_shadow_R": live["r_multiple"] if live else np.nan,
            "traded": e.get("traded", False),
            "paper_pnl_usd": e.get("pnl_usd", np.nan),
        })
    return pd.DataFrame(rows)


def _table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False, floatfmt=".2f")
    except ImportError:  # tabulate missing
        return "```\n" + df.to_string(index=False) + "\n```"


def write_summary() -> None:
    df = summary_table()
    if df.empty:
        return
    df.to_csv(JOURNAL_DIR / "summary.csv", index=False)
    sig = df[df["addon_signal"].fillna(False).astype(bool)]
    go, no = sig[sig["decision"] == "GO"], sig[sig["decision"] != "GO"]

    def line(name, frame):
        r = frame["addon_shadow_ret_%"].dropna()
        return f"| {name} | {len(r)} | {r.mean():+.3f}% | {r.sum():+.2f}% |" if len(r) else f"| {name} | 0 | – | – |"

    fade = df[df["fade_signal"]]
    lines = [
        "# Forward test journal — core portfolio, intraday add-on, fade (shadow)",
        "",
        f"Sessions logged: {len(df)}; add-on signal days: {len(sig)}; GO decisions: {(df['decision'] == 'GO').sum()}; "
        f"add-on trades: {int(df['addon_traded'].sum())}, P&L ${df['addon_pnl_usd'].fillna(0).sum():,.0f}; "
        f"fade shadow signals: {len(fade)}, avg {fade['fade_shadow_R'].mean() if len(fade) else float('nan'):+.2f}R",
        "",
        "Does Claude's morning decision separate good add-on days from bad ones? (shadow return 10:00 -> 11:55, traded or not)",
        "",
        "| group | add-on signal days | avg shadow return | total |",
        "|---|---:|---:|---:|",
        line("decided GO", go),
        line("decided NO_GO", no),
        line("all add-on signal days", sig),
        "",
        _table(df),
    ]
    (JOURNAL_DIR / "SUMMARY.md").write_text("\n".join(lines))
