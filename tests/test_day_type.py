"""Checks for the 10:00 day-type features and walk-forward selection."""

import numpy as np
import pandas as pd
import pytest

from tradingagents.strategies.day_type.features import build_features
from tradingagents.strategies.day_type.study import returns_from_actions, walk_forward

NY = "America/New_York"


def _session(day: str, rth_path: np.ndarray) -> pd.DataFrame:
    pre_idx = pd.date_range(f"{day} 09:00", periods=30, freq="1min", tz=NY)
    rth_idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=NY)
    pre = pd.DataFrame({"open": rth_path[0], "high": rth_path[0], "low": rth_path[0], "close": rth_path[0],
                        "volume": 100.0}, index=pre_idx)
    close = np.asarray(rth_path, float)
    open_ = np.r_[close[0], close[:-1]]
    rth = pd.DataFrame({"open": open_, "high": np.maximum(open_, close), "low": np.minimum(open_, close),
                        "close": close, "volume": 1000.0}, index=rth_idx)
    return pd.concat([pre, rth])


def _features(last_path: np.ndarray):
    rng = np.random.default_rng(3)
    days = pd.bdate_range("2024-01-01", periods=25)
    frames = [_session(d.strftime("%Y-%m-%d"), 100 + np.cumsum(rng.normal(0, 0.02, 390))) for d in days[:-1]]
    frames.append(_session(days[-1].strftime("%Y-%m-%d"), last_path))
    vix = pd.Series(18.0, index=pd.DatetimeIndex(days.date))
    return build_features(pd.concat(frames), vix).iloc[-1]


def test_one_way_drive_has_efficiency_near_one_and_continuation_pays():
    path = np.r_[np.linspace(100, 101, 30), np.linspace(101, 102, 360)]  # up all day
    f = _features(path)
    assert f["efficiency"] == pytest.approx(1.0, abs=1e-6)
    assert f["direction"] == 1 and f["pos_in_or"] == pytest.approx(1.0)
    assert f["cont_to_noon"] > 0 and f["rev_to_noon"] < 0


def test_rotational_open_has_low_efficiency():
    zigzag = 100 + 0.2 * np.sin(np.arange(390) / 2.0)
    f = _features(zigzag)
    assert f["efficiency"] < 0.2  # the Dalton rule's "rotation" threshold


def test_walk_forward_trains_on_earlier_years_only():
    idx = [pd.Timestamp(f"{y}-03-01").date() + pd.Timedelta(days=k) for y in (2019, 2020, 2021) for k in range(150)]
    f = pd.DataFrame({"efficiency": np.tile(np.linspace(0, 1, 150), 3),
                      "cont_to_noon": 0.001, "rev_to_noon": -0.001}, index=pd.Index(idx))
    seen = {}

    def model(train, test, horizon):
        seen[test.index[0].year] = max(d.year for d in train.index)
        return pd.Series(1, index=test.index)

    acts = walk_forward(f, [2021], "noon", model)
    assert seen == {2021: 2020}
    assert returns_from_actions(f, acts, "noon").sum() == pytest.approx(150 * 0.001)
