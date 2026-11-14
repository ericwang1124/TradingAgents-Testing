"""Synthetic checks for the J Law VCP rules (no network)."""

import numpy as np
import pandas as pd

from tradingagents.strategies.vcp import jlaw as jl


def _seg(a, b, n):
    return np.linspace(a, b, n, endpoint=False)


def _base():
    # high 100 (idx 50) -> 75 (25%) -> 98 -> 88 (10.2%) -> 97 -> 92 (5.2%) -> back up to 96
    return np.r_[_seg(50, 100, 50), _seg(100, 75, 10), _seg(75, 98, 10), _seg(98, 88, 6), _seg(88, 97, 6),
                 _seg(97, 92, 4), _seg(92, 96, 5), [96.0]]


def test_contractions_measures_each_pullback_from_its_prior_high():
    c = _base()
    seq = jl.contractions(c, c, len(c) - 1, 250, 0.03)
    assert [(a, b) for a, b, _ in seq] == [(50, 60), (70, 76), (82, 86)]
    assert np.allclose([d for _, _, d in seq], [0.25, 10 / 98, 5 / 97], atol=1e-6)
    assert jl.contractions(c, c, 60, 250, 0.03)[-1][1] == 60        # low is "today": no rebound yet


def test_scan_and_select_apply_the_pattern_rules():
    c = _base()
    t = len(c) - 1
    H = c.reshape(-1, 1)
    V = np.ones_like(H)
    V[83:87] = 0.5                                                     # quiet final decline
    screen = np.zeros_like(H, dtype=bool)
    screen[t] = True
    S = jl.scan(H, H, V, np.ones_like(H), np.full_like(H, 95.0), screen, 0, 250, 0.03)
    assert len(S["t"]) == 1 and S["pivot"][0] == 97.0 and S["low"][0] == 92.0
    assert jl.select(S, jl.JParams()) == {t: [(0, 97.0, 92.0)]}
    assert jl.select(S, jl.JParams(min_contractions=3)) != {}
    assert jl.select(S, jl.JParams(last_max=0.04)) == {}             # final contraction too wide
    assert jl.select(S, jl.JParams(rs_min=99.0)) == {}
    V[83:87] = 2.0                                                     # heavy selling in the final decline
    S2 = jl.scan(H, H, V, np.ones_like(H), np.full_like(H, 95.0), screen, 0, 250, 0.03)
    assert jl.select(S2, jl.JParams()) == {}


def _ind(T=40):
    idx = pd.bdate_range("2021-01-04", periods=T)
    c = np.full(T, 57.5)
    c[5:8] = [60.0, 61.0, 60.5]
    c[8] = 59.4
    c[9:21] = np.linspace(61, 70, 12)
    c[21:] = np.linspace(69, 60, T - 21)
    o, h, l = c * 0.999, c * 1.005, c * 0.995
    o[5], h[5], l[5] = 58.2, 60.5, 58.0
    l[8] = 59.0
    v = np.full(T, 0.8)
    v[5] = 2.0
    v[8] = 0.6
    s20 = np.r_[np.full(15, 58.0), np.linspace(58.5, 66, T - 15)]
    f = lambda x: pd.DataFrame({"XYZ": np.asarray(x, dtype=float)}, index=idx)
    ind = {"C": f(c), "O": f(o), "H": f(h), "L": f(l), "V": f(v), "v50": f(np.ones(T)), "s10": f(np.full(T, 58.9)),
           "s20": f(s20), "s50": f(np.full(T, 50.0)), "rs": f(np.full(T, 95.0))}
    spy = pd.Series(np.linspace(100, 110, T + 300), index=pd.bdate_range(end=idx[-1], periods=T + 300))
    return ind, idx, spy, pd.Series(1.0, index=spy.index), pd.Series(0.0, index=spy.index)


def test_pullback_entry_after_volume_breakout_then_trails_sma20():
    ind, idx, spy, vol, rf = _ind()
    p = jl.JParams(start=str(idx[1].date()))
    sim = jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)
    tr = sim["trades"]
    assert len(tr) == 1 and tr["kind"].iloc[0] == "pullback"
    assert tr["entry_date"].iloc[0] == idx[8]                         # first quiet return to the pivot
    assert abs(tr["r"].iloc[0] - (59.4 * 1.0005 - 58.0 * 0.99) / (59.4 * 1.0005)) < 1e-9   # stop 1% under the lowest support
    assert tr["reason"].iloc[0] == "close below SMA20" and tr["ret"].iloc[0] > 0.05
    assert abs(sim["gross"].loc[idx[8]] - 0.0035 / tr["r"].iloc[0]) < 0.005              # 0.35% of equity at risk


def test_breakout_entry_is_sold_the_same_day_without_volume():
    ind, idx, spy, vol, rf = _ind()
    ind["V"].iloc[5] = 0.5                                             # crosses the pivot on light volume
    p = jl.JParams(entry="breakout", start=str(idx[1].date()))
    tr = jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)["trades"]
    assert len(tr) == 1 and tr["reason"].iloc[0] == "breakout not confirmed" and tr["days"].iloc[0] == 0
    ind2, *_ = _ind()
    tr2 = jl.simulate(ind2, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)["trades"]
    assert tr2["kind"].iloc[0] == "breakout" and abs(tr2["entry"].iloc[0] - 58.5 * 1.0005) < 1e-9 and tr2["days"].iloc[0] > 5
