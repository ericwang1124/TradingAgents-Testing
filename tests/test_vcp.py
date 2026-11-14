"""Synthetic checks for the VCP rules (no network)."""

import numpy as np
import pandas as pd

from tradingagents.strategies.vcp import backtest as vb


def _path():
    up = np.linspace(20, 60, 300)
    w1 = np.r_[np.linspace(60, 48, 8), np.linspace(48, 58, 7)]        # ~20% pullback
    w2 = np.r_[np.linspace(59, 53, 8), np.linspace(53, 58, 7)]        # ~11%
    w3 = np.r_[np.linspace(59, 56, 8), np.linspace(56, 58.5, 7)]      # ~6%
    after = np.r_[60.0, np.linspace(61, 75, 40)]                       # breakout, then a run
    return np.r_[up, w1, w2, w3, after]


def _matrices(c, vol_break=2.5e6):
    idx = pd.bdate_range("2018-01-01", periods=len(c))
    n_pre = 300 + 45
    v = np.r_[np.full(300, 1.2e6), np.full(15, 1.0e6), np.full(15, 0.8e6), np.full(15, 0.6e6),
              [vol_break], np.full(len(c) - n_pre - 1, 1.0e6)]
    C = pd.DataFrame({"XYZ": c}, index=idx)
    return {"open": C * 0.999, "high": C * 1.005, "low": C * 0.995, "close": C,
            "volume": pd.DataFrame({"XYZ": v}, index=idx)}, idx


def test_vcp_setup_and_breakout_entry():
    c = _path()
    M, idx = _matrices(c)
    p = vb.Params(start=str(idx[250].date()))
    ind = vb.indicators(M, p)
    t_setup = idx[300 + 45 - 1]
    assert bool(ind["setup"].loc[t_setup, "XYZ"])                      # contraction recognised at the last base day
    spy = pd.Series(np.linspace(100, 200, len(idx)), index=idx)
    rf = pd.Series(0.0, index=idx)
    sim = vb.simulate(ind, spy, rf, p)
    tr = sim["trades"]
    assert sim["open"] == 1 or len(tr) >= 1
    first_entry = idx[300 + 45]
    assert sim["gross"].loc[first_entry] > 0                          # bought at the breakout close


def test_no_entry_without_volume_or_in_a_falling_market():
    c = _path()
    M, idx = _matrices(c, vol_break=0.9e6)
    p = vb.Params(start=str(idx[250].date()))
    ind = vb.indicators(M, p)
    spy_up = pd.Series(np.linspace(100, 200, len(idx)), index=idx)
    rf = pd.Series(0.0, index=idx)
    assert vb.simulate(ind, spy_up, rf, p)["gross"].loc[idx[300 + 45]] == 0          # weak breakout volume
    M2, _ = _matrices(c)
    ind2 = vb.indicators(M2, p)
    spy_down = pd.Series(np.linspace(200, 100, len(idx)), index=idx)
    assert vb.simulate(ind2, spy_down, rf, p)["gross"].loc[idx[300 + 45]] == 0       # SPY below its 200-day


def test_stop_exit_caps_the_loss_near_r():
    c = _path()
    c[300 + 46:] = np.linspace(58, 40, len(c) - 300 - 46)              # breakout fails
    M, idx = _matrices(c)
    p = vb.Params(start=str(idx[250].date()))
    sim = vb.simulate(vb.indicators(M, p), pd.Series(np.linspace(100, 200, len(idx)), index=idx),
                      pd.Series(0.0, index=idx), p)
    tr = sim["trades"]
    assert len(tr) == 1 and tr["reason"].iloc[0] == "stop"
    assert -0.09 < tr["ret"].iloc[0] < 0                                 # about -R (R capped at 8%) plus costs


def test_to_matrices_splits_reused_tickers_and_drops_spy():
    from tradingagents.strategies.vcp import data as vd

    cal = pd.bdate_range("2020-01-01", periods=120)
    rows = [("SPY", d, 1.0, 1.0, 1.0, 1.0, 10.0) for d in cal]
    rows += [("AAA", d, 5.0, 5.5, 4.5, 5.0, 100.0) for d in cal]                       # continuous
    rows += [("BBB", d, 9.0, 9.5, 8.5, 9.0, 50.0) for d in cal[:20]]                    # old company
    rows += [("BBB", d, 2.0, 2.5, 1.5, 2.0, 70.0) for d in cal[80:]]                    # ticker reused 60 sessions later
    daily = pd.DataFrame(rows, columns=["symbol", "date", "open", "high", "low", "close", "volume"])
    m = vd.to_matrices(daily.sample(frac=1.0, random_state=0))
    assert list(m["close"].columns) == ["AAA", "BBB~1", "BBB~2"] and len(m["close"]) == 120
    assert m["close"]["BBB~1"].notna().sum() == 20 and m["close"]["BBB~2"].notna().sum() == 40
    assert m["close"]["BBB~1"].iloc[25:].isna().all() and float(m["close"]["BBB~2"].iloc[-1]) == 2.0
