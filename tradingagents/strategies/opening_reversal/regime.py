"""Market-regime labels for each session, using only information known before the open.

Two fixed (not optimised) dimensions:
  * trend      — prior close above / below its 50-day simple moving average
  * volatility — prior-day VIX close: < 15 calm, 15-20 normal, >= 20 stressed
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .data import default_cache_dir
from .levels import DayContext

VIX_BUCKETS = ((15.0, "vix<15"), (20.0, "vix15-20"), (np.inf, "vix>=20"))


def load_vix(start: date, end: date, cache_dir: Optional[Path] = None) -> pd.Series:
    """Daily VIX closes indexed by date (Yahoo ^VIX), cached as csv."""
    cache_dir = Path(cache_dir or default_cache_dir())
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "vix_daily.csv"
    if path.exists():
        cached = pd.read_csv(path, index_col=0, parse_dates=True)["close"]
        if cached.index.min().date() <= start and cached.index.max().date() >= end:
            return cached
    import yfinance as yf

    raw = yf.Ticker("^VIX").history(start=start, end=end + pd.Timedelta(days=1), interval="1d", auto_adjust=False)
    if raw.empty:
        raise RuntimeError("yfinance returned no ^VIX data")
    series = pd.Series(raw["Close"].to_numpy(), index=pd.DatetimeIndex(raw.index.date), name="close")
    series.to_frame().to_csv(path)
    return series


def attach_vix(contexts: Iterable[DayContext], vix: pd.Series) -> None:
    """Set ``features['vix_prev']`` = last VIX close strictly before each session's date."""
    vix = vix.sort_index()
    dates = vix.index.values
    values = vix.to_numpy()
    for ctx in contexts:
        pos = np.searchsorted(dates, np.datetime64(ctx.day.date()), side="left") - 1
        ctx.features["vix_prev"] = float(values[pos]) if pos >= 0 else np.nan


def vix_bucket(v: float) -> Optional[str]:
    if v is None or np.isnan(v):
        return None
    for upper, label in VIX_BUCKETS:
        if v < upper:
            return label
    return None


def classify(ctx: DayContext) -> Optional[str]:
    """e.g. 'down/vix>=20'. None when a feature is missing (warm-up)."""
    sma = ctx.features.get("sma50", np.nan)
    vol = vix_bucket(ctx.features.get("vix_prev", np.nan))
    if np.isnan(sma) or vol is None:
        return None
    trend = "up" if ctx.prev_close >= sma else "down"
    return f"{trend}/{vol}"


def regime_by_date(contexts: List[DayContext]) -> Dict[date, Optional[str]]:
    return {ctx.day.date(): classify(ctx) for ctx in contexts}
