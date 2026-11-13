"""Checks for the regime overlay helpers (no network)."""

import numpy as np
import pandas as pd

from tradingagents.strategies import regime_overlays as ro


def test_drawdown_multiplier_hysteresis():
    idx = pd.bdate_range("2020-01-01", periods=6)
    # equity: 1.0 -> 0.88 (12% down, cut) -> 0.92 (still >5% down, stay cut) -> 0.97 (within 5%, restore)
    eq = pd.Series([1.0, 1.0, 0.88, 0.92, 0.97, 0.97], index=idx)
    m = ro.drawdown_multiplier(eq.pct_change().fillna(0.0))
    assert m.tolist() == [1.0, 1.0, 0.5, 0.5, 1.0, 1.0]


def test_renorm_keeps_sum_one_and_cash_when_all_dropped():
    W = pd.DataFrame({"a": [0.5, 0.0], "b": [0.25, 0.0]})
    out = ro.renorm(W)
    assert np.isclose(out.iloc[0].sum(), 1.0) and out.iloc[1].sum() == 0.0


def test_markov_like_matches_signal_share():
    idx = pd.bdate_range("2010-01-01", periods=4000)
    rng = np.random.default_rng(0)
    sig = pd.Series((np.cumsum(rng.random(len(idx)) > 0.98) % 4) == 0, index=idx)
    fakes = ro.markov_like(sig, 20, seed=1)
    assert abs(np.mean([f.mean() for f in fakes]) - sig.mean()) < 0.08
