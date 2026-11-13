"""Split minute bars into sessions and pre-compute everything known before the open:
prior-day OHLC, prior-day volume profile (POC / value area), pre-market high, and the
time-of-day volume baseline used to normalise volume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import StrategyParams

RTH_OPEN = time(9, 30)
RTH_CLOSE = time(16, 0)
PREMARKET_OPEN = time(4, 0)


@dataclass
class DayContext:
    day: pd.Timestamp
    rth: pd.DataFrame              # regular-session bars, with a ``rel_vol`` column
    open: float
    prev_close: float
    levels: Dict[str, float] = field(default_factory=dict)
    features: Dict[str, float] = field(default_factory=dict)  # e.g. sma20 / sma50 of prior closes

    @property
    def gap_pct(self) -> float:
        return self.open / self.prev_close - 1.0


def volume_profile(bars: pd.DataFrame, bin_pct: float, value_area_share: float = 0.70) -> Dict[str, float]:
    """POC / VAH / VAL of a session. Each bar's volume is spread evenly over its high-low range."""
    if bars.empty or bars["volume"].sum() <= 0:
        return {}
    width = float(bars["close"].mean()) * bin_pct
    lo_bin = np.floor(bars["low"].to_numpy() / width).astype(np.int64)
    hi_bin = np.floor(bars["high"].to_numpy() / width).astype(np.int64)
    counts = hi_bin - lo_bin + 1
    base = lo_bin.min()
    starts = np.repeat(lo_bin - base, counts)
    offsets = np.arange(counts.sum()) - np.repeat(np.cumsum(counts) - counts, counts)
    weights = np.repeat(bars["volume"].to_numpy() / counts, counts)
    hist = np.bincount(starts + offsets, weights=weights)

    poc = int(np.argmax(hist))
    target = hist.sum() * value_area_share
    lo = hi = poc
    acc = hist[poc]
    while acc < target and (lo > 0 or hi < len(hist) - 1):
        down = hist[lo - 1] if lo > 0 else -1.0
        up = hist[hi + 1] if hi < len(hist) - 1 else -1.0
        if up >= down:
            hi += 1
            acc += hist[hi]
        else:
            lo -= 1
            acc += hist[lo]
    to_price = lambda b: (b + base) * width
    return {
        "poc": to_price(poc) + width / 2,
        "vah": to_price(hi) + width,
        "val": to_price(lo),
    }


def _relative_volume(rth_by_day: Dict[pd.Timestamp, pd.DataFrame], lookback: int) -> Dict[pd.Timestamp, pd.Series]:
    """volume / median volume of the same minute-of-day over the previous ``lookback`` sessions."""
    rows = {}
    for day, bars in rth_by_day.items():
        minute = (bars.index.hour * 60 + bars.index.minute) - (9 * 60 + 30)
        rows[day] = pd.Series(bars["volume"].to_numpy(), index=minute)
    table = pd.DataFrame(rows).T.sort_index()  # rows: day, cols: minute-of-session
    baseline = table.rolling(lookback, min_periods=max(5, lookback // 2)).median().shift(1)
    rel = (table / baseline.replace(0, np.nan))
    out = {}
    for day, bars in rth_by_day.items():
        minute = (bars.index.hour * 60 + bars.index.minute) - (9 * 60 + 30)
        out[day] = pd.Series(rel.loc[day, minute].to_numpy(), index=bars.index)
    return out


def _session_minutes(bars: pd.DataFrame) -> float:
    """Minutes spanned by a session's bars (bar-size independent)."""
    if len(bars) < 2:
        return 0.0
    return (bars.index[-1] - bars.index[0]).total_seconds() / 60.0


def build_day_contexts(bars: pd.DataFrame, params: Optional[StrategyParams] = None) -> List[DayContext]:
    """Turn a continuous minute-bar frame into per-session contexts (first session is warm-up)."""
    params = params or StrategyParams()
    if bars.empty:
        return []
    t = bars.index.time
    dates = bars.index.normalize()
    rth_mask = (t >= RTH_OPEN) & (t < RTH_CLOSE)
    pre_mask = (t >= PREMARKET_OPEN) & (t < RTH_OPEN)

    rth_by_day = {d: g for d, g in bars[rth_mask].groupby(dates[rth_mask])}
    pre_by_day = {d: g for d, g in bars[pre_mask].groupby(dates[pre_mask])}
    rel_vol = _relative_volume(rth_by_day, params.volume_lookback_days)

    contexts: List[DayContext] = []
    prev: Optional[pd.DataFrame] = None
    daily_closes: List[float] = []  # RTH closes of completed sessions, oldest first
    for day in sorted(rth_by_day):
        rth = rth_by_day[day]
        if prev is not None and _session_minutes(rth) > 30 and rth.index[0].time() == RTH_OPEN:
            profile = volume_profile(prev, params.profile_bin_pct, params.value_area_share)
            levels = {
                "prev_close": float(prev["close"].iloc[-1]),
                "prev_high": float(prev["high"].max()),
                "prev_low": float(prev["low"].min()),
            }
            if profile:
                levels.update({"prev_poc": profile["poc"], "prev_vah": profile["vah"], "prev_val": profile["val"]})
            pre = pre_by_day.get(day)
            if pre is not None and not pre.empty:
                levels["premarket_high"] = float(pre["high"].max())
            frame = rth.copy()
            frame["rel_vol"] = rel_vol[day]
            features = {
                f"sma{n}": float(np.mean(daily_closes[-n:])) if len(daily_closes) >= n else np.nan
                for n in (20, 50)
            }
            contexts.append(
                DayContext(
                    day=day,
                    rth=frame,
                    open=float(rth["open"].iloc[0]),
                    prev_close=levels["prev_close"],
                    levels=levels,
                    features=features,
                )
            )
        if _session_minutes(rth) > 30:
            prev = rth
            daily_closes.append(float(rth["close"].iloc[-1]))
    return contexts
