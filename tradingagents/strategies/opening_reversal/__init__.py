"""Opening-hour gap-down reversal short (SPY), phase 1: OHLCV-only backtest.

Rules (all must hold for the full variant):
  1. Gap down: the regular-session open is below the prior close by at least ``min_gap_pct``.
  2. Exhaustion: the rally off the morning low rises on fading, time-of-day-normalised volume.
  3. Rejection: the rally tags a pre-computed supply zone and a bar closes back below it.
Stop goes above the rally high / zone, profits are scaled out in R multiples, and entries are
only taken inside the first trading hour.
"""

from .config import StrategyParams, VARIANTS
from .backtest import run_backtest

__all__ = ["StrategyParams", "VARIANTS", "run_backtest"]
