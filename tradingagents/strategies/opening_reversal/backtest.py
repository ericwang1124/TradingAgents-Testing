"""Trade simulation on the underlying. Results are in R (multiples of initial risk) and in % of the
underlying, *not* option P&L: phase 1 only answers whether the signal has an edge on SPY itself."""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from .config import StrategyParams
from .levels import DayContext, build_day_contexts
from .signals import Signal, find_signal


def simulate_short(ctx: DayContext, sig: Signal, params: StrategyParams) -> Dict:
    bars = ctx.rth
    o = bars["open"].to_numpy()
    h = bars["high"].to_numpy()
    l = bars["low"].to_numpy()
    c = bars["close"].to_numpy()
    times = bars.index.time
    slip = params.slippage_pct

    entry = sig.entry_price * (1.0 - slip)          # selling short: fill slightly lower
    risk = sig.stop - sig.entry_price
    stop = sig.stop
    targets = [[sig.entry_price - r * risk, frac, False] for r, frac in params.take_profits]
    remaining = 1.0
    fills: List[tuple] = []                         # (fraction, price, reason)
    exit_idx = len(bars) - 1
    hit_target = False

    for j in range(sig.entry_idx, len(bars)):
        if times[j] >= params.time_exit:
            fills.append((remaining, o[j] * (1.0 + slip), "time"))
            remaining = 0.0
            exit_idx = j
            break
        # Stop is checked before targets: within one bar we cannot know the order, assume worst.
        # A bar that opens beyond a level fills at its open (gap through).
        if h[j] >= stop:
            px = max(o[j], stop)
            fills.append((remaining, px * (1.0 + slip), "breakeven" if hit_target else "stop"))
            remaining = 0.0
            exit_idx = j
            break
        for tgt in targets:
            if not tgt[2] and l[j] <= tgt[0]:
                px = min(o[j], tgt[0])
                frac = min(tgt[1], remaining)
                fills.append((frac, px * (1.0 + slip), "target"))
                remaining -= frac
                tgt[2] = True
                hit_target = True
                if params.move_stop_to_breakeven:
                    stop = min(stop, sig.entry_price)
        if remaining <= 1e-9:
            exit_idx = j
            break
    if remaining > 1e-9:  # session ended (e.g. half day) before time exit
        fills.append((remaining, c[-1] * (1.0 + slip), "eod"))
        exit_idx = len(bars) - 1

    pnl_per_share = sum(frac * (entry - px) for frac, px, _ in fills)
    exit_px = sum(frac * px for frac, px, _ in fills)
    return {
        "date": ctx.day.date(),
        "gap_pct": ctx.gap_pct * 100,
        "entry_time": bars.index[sig.entry_idx].strftime("%H:%M"),
        "exit_time": bars.index[exit_idx].strftime("%H:%M"),
        "entry": round(sig.entry_price, 4),
        "stop": round(sig.stop, 4),
        "avg_exit": round(exit_px, 4),
        "risk_pct": risk / sig.entry_price * 100,
        "r_multiple": pnl_per_share / risk,
        "return_pct": pnl_per_share / sig.entry_price * 100,
        "max_favorable_r": (sig.entry_price - l[sig.entry_idx : exit_idx + 1].min()) / risk,
        "exit_reason": "/".join(reason for _, _, reason in fills),
        "zone": sig.zone,
        "exhaustion_ratio": sig.exhaustion_ratio,
        "rally_pct": (sig.rally_high / sig.rally_low - 1.0) * 100,
        "minutes_held": (bars.index[exit_idx] - bars.index[sig.entry_idx]).seconds // 60,
    }


def run_backtest(
    bars: Optional[pd.DataFrame] = None,
    params: Optional[StrategyParams] = None,
    contexts: Optional[List[DayContext]] = None,
) -> pd.DataFrame:
    """Run one parameter set. Pass pre-built ``contexts`` to reuse them across variants."""
    params = params or StrategyParams()
    if contexts is None:
        contexts = build_day_contexts(bars, params)
    trades = []
    for ctx in contexts:
        sig = find_signal(ctx, params)
        if sig is not None:
            trades.append(simulate_short(ctx, sig, params))
    return pd.DataFrame(trades)


def eligible_contexts(contexts: List[DayContext]) -> List[DayContext]:
    """Sessions with a full relative-volume baseline, so every variant sees the same sample."""
    out = []
    for ctx in contexts:
        window = ctx.rth.between_time("09:30", "10:30")
        if window["rel_vol"].notna().mean() > 0.9:
            out.append(ctx)
    return out
