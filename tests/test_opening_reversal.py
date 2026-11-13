"""Synthetic-data tests for the opening reversal strategy (no network needed)."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from tradingagents.strategies.opening_reversal.backtest import run_backtest
from tradingagents.strategies.opening_reversal.config import VARIANTS, StrategyParams
from tradingagents.strategies.opening_reversal.levels import build_day_contexts, volume_profile
from tradingagents.strategies.opening_reversal.signals import find_signal

NY = "America/New_York"
BASE_VOL = 1000.0


def _flat_day(day: str, price: float) -> pd.DataFrame:
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=NY)
    return pd.DataFrame(
        {"open": price, "high": price + 0.02, "low": price - 0.02, "close": price, "volume": BASE_VOL},
        index=idx,
    )


def _setup_day(day: str, rally_volume: str = "fading", after_entry: str = "down") -> pd.DataFrame:
    """Gap down to 99.60, dip to 99.50, rally to 99.99 into the ~100 supply cluster, fail, then move."""
    path = []  # (open, high, low, close, volume multiple)
    closes = [99.58, 99.56, 99.54, 99.52, 99.51]
    prev = 99.60
    for cl in closes:  # bars 0-4: drift to the low
        path.append((prev, prev + 0.01, cl - 0.01, cl, 2.0))
        prev = cl
    rally = np.linspace(99.56, 99.96, 10)  # bars 5-14
    vols = np.linspace(3.0, 1.0, 10) if rally_volume == "fading" else np.linspace(1.0, 3.0, 10)
    for k, (cl, v) in enumerate(zip(rally, vols)):
        hi = 99.99 if k == 9 else cl + 0.01
        path.append((prev, hi, prev - 0.01, cl, v))
        prev = cl
    path.append((99.95, 99.96, 99.84, 99.85, 1.5))  # bar 15: bearish, closes below bar 14's low
    path.append((99.84, 99.85, 99.80, 99.81, 1.0))  # bar 16: entry bar (fills at 99.84)
    if after_entry == "down":
        drift = np.linspace(99.78, 99.10, 30)
    else:
        drift = np.linspace(99.90, 100.40, 30)
    prev = 99.81
    for cl in drift:
        path.append((prev, max(prev, cl) + 0.01, min(prev, cl) - 0.01, cl, 1.0))
        prev = cl
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=NY)
    rest = len(idx) - len(path)
    path += [(prev, prev + 0.01, prev - 0.01, prev, 1.0)] * rest
    df = pd.DataFrame(path, columns=["open", "high", "low", "close", "volume"], index=idx)
    df["volume"] *= BASE_VOL
    return df


def _history(test_day: pd.DataFrame, prior_price: float = 100.0, trend: float = 0.0) -> pd.DataFrame:
    """25 flat sessions before the test day. ``trend`` shifts earlier sessions up (+) or down (-)
    so the last prior close ends at ``prior_price``."""
    days = pd.bdate_range("2024-01-01", periods=25)
    frames = [
        _flat_day(d.strftime("%Y-%m-%d"), prior_price + trend * (len(days) - 1 - k))
        for k, d in enumerate(days)
    ]
    return pd.concat(frames + [test_day])


TEST_DAY = pd.bdate_range("2024-01-01", periods=26)[-1].strftime("%Y-%m-%d")


def _last_ctx(bars):
    return build_day_contexts(bars)[-1]


def test_full_strategy_detects_textbook_setup_and_scales_out():
    bars = _history(_setup_day(TEST_DAY))
    ctx = _last_ctx(bars)
    assert ctx.gap_pct == pytest.approx(-0.004, abs=1e-6)

    params = VARIANTS["full (gap+exhaustion+zone)"]
    sig = find_signal(ctx, params)
    assert sig is not None
    assert sig.signal_idx == 15 and sig.entry_idx == 16
    assert sig.entry_price == pytest.approx(99.84)
    assert sig.zone is not None and sig.exhaustion_ratio < params.max_exhaustion_ratio
    assert sig.stop > sig.rally_high  # stop sits above the rally high / zone

    trades = run_backtest(bars, params)
    assert len(trades) == 1
    t = trades.iloc[0]
    assert t["exit_reason"] == "target/target"
    assert t["r_multiple"] == pytest.approx(1.5, abs=0.02)  # 0.5 @ 1R + 0.5 @ 2R, minus slippage


def test_rising_volume_rally_is_filtered_by_exhaustion_only():
    bars = _history(_setup_day(TEST_DAY, rally_volume="rising"))
    ctx = _last_ctx(bars)
    assert find_signal(ctx, VARIANTS["full (gap+exhaustion+zone)"]) is None
    assert find_signal(ctx, VARIANTS["gap+zone"]) is not None


def test_no_gap_down_means_no_trade_for_gap_variants():
    day = _setup_day(TEST_DAY)
    bars = _history(day, prior_price=99.60)  # prior close == today's open
    ctx = _last_ctx(bars)
    assert abs(ctx.gap_pct) < 1e-9
    for name in ("gap_only", "gap+exhaustion", "gap+zone", "full (gap+exhaustion+zone)"):
        assert find_signal(ctx, VARIANTS[name]) is None


def test_failed_setup_is_stopped_for_about_minus_one_r():
    bars = _history(_setup_day(TEST_DAY, after_entry="up"))
    trades = run_backtest(bars, VARIANTS["full (gap+exhaustion+zone)"])
    assert len(trades) == 1
    t = trades.iloc[0]
    assert t["exit_reason"] == "stop"
    assert t["r_multiple"] == pytest.approx(-1.0, abs=0.02)


def test_entry_window_is_enforced():
    bars = _history(_setup_day(TEST_DAY))
    ctx = _last_ctx(bars)
    late = replace(VARIANTS["full (gap+exhaustion+zone)"], entry_start=pd.Timestamp("10:00").time())
    assert find_signal(ctx, late) is None


def test_regime_filter_uses_prior_closes_only():
    full = VARIANTS["full (gap+exhaustion+zone)"]
    # Downtrend: earlier closes above the last one -> prior close is below its 20-day average.
    down = _last_ctx(_history(_setup_day(TEST_DAY), trend=0.02))
    assert down.prev_close < down.features["sma20"]
    assert find_signal(down, replace(full, regime="below_sma20")) is not None
    assert find_signal(down, replace(full, regime="above_sma20")) is None
    # Not enough history for a 50-day average -> the filter refuses to trade.
    assert find_signal(down, replace(full, regime="below_sma50")) is None


def test_break_lookback_waits_for_structure_break():
    ctx = _last_ctx(_history(_setup_day(TEST_DAY)))
    full = VARIANTS["full (gap+exhaustion+zone)"]
    assert find_signal(ctx, full).signal_idx == 15
    # Bar 15 closes at 99.85, above the low of bars 12-14 (99.817): with N=3 the trigger
    # moves to bar 16, which closes below the low of bars 13-15.
    sig = find_signal(ctx, replace(full, break_lookback=3))
    assert sig is not None and sig.signal_idx == 16 and sig.entry_idx == 17


def test_resample_bars_aggregates_ohlcv():
    from tradingagents.strategies.opening_reversal.data import resample_bars

    idx = pd.date_range("2024-01-02 09:30", periods=10, freq="1min", tz=NY)
    bars = pd.DataFrame(
        {"open": np.arange(10.0), "high": np.arange(10.0) + 1, "low": np.arange(10.0) - 1,
         "close": np.arange(10.0) + 0.5, "volume": 1.0},
        index=idx,
    )
    out = resample_bars(bars, 5)
    assert list(out.index.strftime("%H:%M")) == ["09:30", "09:35"]
    first = out.iloc[0]
    assert (first["open"], first["high"], first["low"], first["close"], first["volume"]) == (0, 5, -1, 4.5, 5)


def test_volume_profile_poc_and_value_area():
    idx = pd.date_range("2024-01-02 09:30", periods=4, freq="1min", tz=NY)
    bars = pd.DataFrame(
        {"open": [100, 101, 102, 101], "high": [100, 101, 102, 101], "low": [100, 101, 102, 101],
         "close": [100, 101, 102, 101], "volume": [10, 1000, 10, 1000]},
        index=idx, dtype=float,
    )
    prof = volume_profile(bars, bin_pct=0.001, value_area_share=0.7)
    assert prof["poc"] == pytest.approx(101, abs=0.11)
    assert prof["val"] <= 101 <= prof["vah"]
