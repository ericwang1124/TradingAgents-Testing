"""Synthetic checks for the published intraday momentum rules."""

from datetime import time

import numpy as np
import pandas as pd
import pytest

from tradingagents.strategies.intraday_momentum.strategies import (
    NoiseAreaParams, half_hour_momentum, noise_area_momentum, session_matrix)

NY = "America/New_York"


def _day(day: str, path: np.ndarray) -> pd.DataFrame:
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=NY)
    close = np.asarray(path, dtype=float)
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({"open": open_, "high": np.maximum(open_, close) + 0.01,
                         "low": np.minimum(open_, close) - 0.01, "close": close, "volume": 1000.0}, index=idx)


def _history(last_path: np.ndarray, n_quiet: int = 20) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    days = pd.bdate_range("2024-01-01", periods=n_quiet + 1)
    frames = []
    for d in days[:-1]:
        wiggle = 100 + np.cumsum(rng.normal(0, 0.01, 390))  # tiny noise area (~0.1% moves)
        frames.append(_day(d.strftime("%Y-%m-%d"), wiggle))
    frames.append(_day(days[-1].strftime("%Y-%m-%d"), last_path))
    return pd.concat(frames)


def test_noise_area_goes_long_on_a_trend_day_and_profits():
    trend = 100 + np.linspace(0, 2.0, 390)  # +2% steady rally from the open
    res = noise_area_momentum(session_matrix(_history(trend)), NoiseAreaParams(vol_target=False))
    last = res.iloc[-1]
    assert last["trades"] == 1
    # entered at 10:00 (~+0.15%), held to the close (+2%) minus costs
    assert last["ret"] == pytest.approx(trend[-1] / trend[29] - 1, abs=2e-4)


def test_noise_area_stays_flat_inside_the_noise_area():
    flat = np.full(390, 100.0)
    res = noise_area_momentum(session_matrix(_history(flat)), NoiseAreaParams(vol_target=False))
    assert res.iloc[-1]["trades"] == 0 and res.iloc[-1]["ret"] == 0.0


def test_morning_variant_exits_at_noon():
    trend = 100 + np.linspace(0, 2.0, 390)
    p = NoiseAreaParams(vol_target=False, last_check=time(10, 30), exit_time=time(12, 0))
    last = noise_area_momentum(session_matrix(_history(trend)), p).iloc[-1]
    noon = 150 - 1  # bar ending at 12:00
    assert last["ret"] == pytest.approx(trend[noon] / trend[29] - 1, abs=2e-4)


def test_half_hour_momentum_sign_and_costs():
    up = 100 + np.linspace(0, 1.0, 390)
    hh = half_hour_momentum(session_matrix(_history(up)))
    last = hh.iloc[-1]
    assert last["signal"] == 1.0
    assert last["ret"] == pytest.approx(up[389] / up[359] - 1 - 2 * 0.0045 / up[359], abs=1e-9)
