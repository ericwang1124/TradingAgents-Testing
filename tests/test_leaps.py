"""LEAP pricing and trade mechanics (no network)."""

import numpy as np
import pandas as pd

from tradingagents.strategies.leaps import backtest as lb
from tradingagents.strategies.leaps import pricing as pr


def test_black_scholes_and_implied_vol_round_trip():
    p = pr.bs_call(100.0, 100.0, 1.0, 0.04, 0.25, q=0.0)
    assert abs(float(p) - 11.837) < 0.01                                  # d1 = 0.285, d2 = 0.035
    iv = pr.implied_vol(np.array([float(p)]), 100.0, 100.0, 1.0, 0.04, q=0.0)
    assert abs(iv[0] - 0.25) < 1e-4
    assert np.isnan(pr.implied_vol(np.array([1.0]), 100.0, 50.0, 1.0, 0.04)[0])   # below intrinsic
    assert 0.8 < float(pr.bs_delta(100.0, 80.0, 1.0, 0.04, 0.3)) < 0.9


def _market(path, vxn=20.0):
    idx = pd.bdate_range("2010-01-04", periods=len(path))
    return pd.DataFrame({"QQQ": path, "VXN": vxn, "r": 0.03}, index=idx)


COEF = {"a": 0.17, "b": 0.33, "c": -0.28, "d": 0.2, "e": 0.0}


def test_signal_cooldown_and_trend_filter():
    px = np.r_[np.linspace(50, 100, 250), np.full(150, 100.0)]             # uptrend, then flat
    px[250:255] = 97.0                                                      # -3% (signal)
    px[255:290] = 94.0                                                      # another -3% five days later (inside the cooldown)
    px[290:] = 60.0                                                         # a crash 40 days later: a signal, but below the 200-day average
    s = pd.Series(px, index=pd.bdate_range("2010-01-04", periods=400))
    lb.START = "2010-01-01"
    assert lb.signal_days(s, trend=False) == [250, 290]
    assert lb.signal_days(s, trend=True) == [250]                          # by day 290 the price is below its 200-day average


def test_trade_take_profit_and_costs():
    path = np.r_[np.full(5, 100.0), np.linspace(100, 130, 60), np.full(200, 130.0)]
    m = _market(path)
    t = lb.trade(m, COEF, 4, lb.Spec("QQQ", 1.0, 189, 0.20))
    assert t["ret"] >= 0.20 and t["days"] < 60                             # sold at the first close 20% above cost
    t2 = lb.trade(m, COEF, 4, lb.Spec("QQQ", 1.0, 189, None))
    assert t2["days"] == 189 and t2["ret"] > t["ret"]
    flat = lb.trade(_market(np.full(300, 100.0)), COEF, 4, lb.Spec("QQQ", 1.0, 189, None))
    assert flat["ret"] < -0.3                                               # time decay of an at-the-money call over 9 months
