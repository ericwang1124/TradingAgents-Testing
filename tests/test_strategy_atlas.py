"""Checks for the strategy x scenario atlas helpers."""

import numpy as np
import pandas as pd

from tradingagents.strategies.strategy_atlas import _hold_until, _sharpe, atlas


def test_hold_until_enters_and_exits_on_signals():
    idx = pd.RangeIndex(8)
    enter = pd.Series([0, 1, 0, 0, 0, 1, 0, 0], index=idx).astype(bool)
    exit_ = pd.Series([0, 0, 0, 1, 0, 0, 0, 1], index=idx).astype(bool)
    assert _hold_until(enter, exit_).tolist() == [0, 1, 1, 0, 0, 1, 1, 0]


def test_atlas_flags_consistent_cells_only():
    days = pd.bdate_range("2010-01-01", periods=2000)
    rng = np.random.default_rng(0)
    state = pd.Series(np.where(np.arange(2000) % 2 == 0, "calm", "storm"), index=days)
    # strategy earns in "calm" in both halves and loses in "storm" in both halves
    x = np.where(state == "calm", 0.002, -0.002) + rng.normal(0, 0.01, 2000)
    S = pd.DataFrame({"strat": x}, index=days)
    sc = pd.DataFrame({"dim": state})
    tables, flags = atlas(S, sc)
    verdicts = dict(zip(flags["state"], flags["verdict"]))
    assert verdicts == {"calm": "usable", "storm": "avoid"}
    assert tables["dim"].loc["strat", "calm"].endswith("✓")
    assert _sharpe(pd.Series([0.0] * 30)) != _sharpe(pd.Series([0.0] * 30))  # zero-vol -> NaN
