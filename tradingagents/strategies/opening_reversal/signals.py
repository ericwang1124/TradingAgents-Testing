"""Per-session entry detection. Uses only information available at the close of the signal bar;
the entry itself is filled at the *next* bar's open."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from .config import StrategyParams
from .levels import DayContext


@dataclass
class Signal:
    signal_idx: int           # index (into ctx.rth) of the bar that confirmed the reversal
    entry_idx: int            # index of the entry bar (filled at its open)
    entry_price: float
    stop: float
    rally_low: float
    rally_high: float
    zone: Optional[str]
    zone_level: Optional[float]
    exhaustion_ratio: Optional[float]


def supply_zones(ctx: DayContext, params: StrategyParams) -> List[Tuple[str, float, float, float]]:
    """(name, level, zone_low, zone_high) for every configured level at/above the open, low to high."""
    zones = []
    for name in params.zone_sources:
        level = ctx.levels.get(name)
        if level is None or level < ctx.open:
            continue
        half = level * params.zone_half_width_pct
        zones.append((name, level, level - half, level + half))
    return sorted(zones, key=lambda z: z[1])


def gap_ok(ctx: DayContext, params: StrategyParams) -> bool:
    gap = ctx.gap_pct
    is_gap_down = -params.max_gap_pct <= gap <= -params.min_gap_pct
    if params.require_gap_down:
        return is_gap_down
    if params.gap_filter == "not_gap_down":
        return gap > -params.min_gap_pct
    return True


def regime_ok(ctx: DayContext, params: StrategyParams) -> bool:
    """Trend filter on the prior close vs its moving average (no same-day information)."""
    if params.regime == "any":
        return True
    side, _, length = params.regime.partition("_sma")
    sma = ctx.features.get(f"sma{length}", np.nan)
    if np.isnan(sma):
        return False
    if side == "below":
        return ctx.prev_close < sma
    if side == "above":
        return ctx.prev_close > sma
    raise ValueError(f"unknown regime {params.regime!r}")


def exhaustion_ratio(rel_vol: np.ndarray, low_idx: int, high_idx: int, window: int) -> Optional[float]:
    """Mean relative volume of the last ``window`` rally bars over that of the first ``window``.

    The rally leg is the bars *after* the low up to and including the high, so a high-volume
    capitulation bar at the low does not inflate the "early" side.
    """
    leg = high_idx - low_idx
    if leg < 2:
        return None
    w = max(1, min(window, leg // 2))
    early = rel_vol[low_idx + 1 : low_idx + 1 + w]
    late = rel_vol[high_idx - w + 1 : high_idx + 1]
    if np.isnan(early).any() or np.isnan(late).any() or early.mean() <= 0:
        return None
    return float(late.mean() / early.mean())


def find_signal(ctx: DayContext, params: StrategyParams) -> Optional[Signal]:
    if not gap_ok(ctx, params) or not regime_ok(ctx, params):
        return None
    bars = ctx.rth
    o = bars["open"].to_numpy()
    h = bars["high"].to_numpy()
    l = bars["low"].to_numpy()
    c = bars["close"].to_numpy()
    rv = bars["rel_vol"].to_numpy(dtype=float)
    times = bars.index.time
    zones = supply_zones(ctx, params) if params.require_zone else []
    if params.require_zone and not zones:
        return None

    for i in range(1, len(bars) - 1):
        if times[i] < params.entry_start:
            continue
        if times[i + 1] > params.entry_end:
            break

        low_idx = int(np.argmin(l[: i + 1]))
        if low_idx >= i:
            continue
        seg = h[low_idx : i + 1]
        high_idx = low_idx + int(np.argmax(seg))
        rally_low, rally_high = l[low_idx], h[high_idx]
        if high_idx >= i or i - high_idx > params.max_bars_since_high:
            continue
        if rally_high / rally_low - 1.0 < params.min_rally_pct:
            continue
        # bearish bar that closes below the lowest low of the prior N bars = the push has failed
        if not (c[i] < o[i] and c[i] < l[max(0, i - params.break_lookback) : i].min()):
            continue

        zone = None
        if params.require_zone:
            closes_in_rally = c[low_idx:i]
            for name, level, z_lo, z_hi in reversed(zones):  # highest touched, unbroken zone
                touched = rally_high >= z_lo
                accepted_above = (closes_in_rally > z_hi).any()
                if touched and not accepted_above:
                    zone = (name, level, z_lo, z_hi)
                    break
            if zone is None or c[i] >= zone[2]:
                continue

        ratio = exhaustion_ratio(rv, low_idx, high_idx, params.exhaustion_window)
        if params.require_exhaustion and (ratio is None or ratio > params.max_exhaustion_ratio):
            continue

        stop_anchor = max(rally_high, zone[3]) if zone else rally_high
        stop = stop_anchor * (1.0 + params.stop_buffer_pct)
        entry = o[i + 1]
        risk_pct = (stop - entry) / entry
        if not (params.min_risk_pct <= risk_pct <= params.max_risk_pct):
            continue

        return Signal(
            signal_idx=i,
            entry_idx=i + 1,
            entry_price=float(entry),
            stop=float(stop),
            rally_low=float(rally_low),
            rally_high=float(rally_high),
            zone=zone[0] if zone else None,
            zone_level=float(zone[1]) if zone else None,
            exhaustion_ratio=ratio,
        )
    return None
