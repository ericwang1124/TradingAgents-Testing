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


def test_confirmed_pullback_waits_for_a_move_above_the_pullback_day_high():
    ind, idx, spy, vol, rf = _ind()
    ind["O"].iloc[9] = 59.8                                            # day after the quiet pullback: opens near its high, trades through
    p = jl.JParams(entry="confirm_pullback", start=str(idx[1].date()))
    tr = jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)["trades"]
    trig = 59.4 * 1.005                                                # high of the pullback day (day 8)
    assert len(tr) == 1 and tr["entry_date"].iloc[0] == idx[9]
    assert abs(tr["entry"].iloc[0] - max(59.8, trig) * 1.0005) < 1e-9
    ind2, *_ = _ind()                                                  # unchanged data: day 9 opens more than 2% above the trigger
    ind2["C"].iloc[9:13] = 59.0                                        # and the next days never trade above it
    ind2["H"].iloc[9:13] = 59.3
    ind2["O"].iloc[9:13] = 59.0
    ind2["L"].iloc[9:13] = 58.8
    assert len(jl.simulate(ind2, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)["trades"]) == 0     # no confirmation, no trade
    assert len(jl.simulate(ind2, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, jl.JParams(start=str(idx[1].date())))["trades"]) == 1


def test_close_breakout_buys_the_confirmed_close_only():
    ind, idx, spy, vol, rf = _ind()
    p = jl.JParams(entry="close_breakout", start=str(idx[1].date()))
    tr = jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)["trades"]
    assert len(tr) == 1 and tr["entry_date"].iloc[0] == idx[5] and abs(tr["entry"].iloc[0] - 60.0 * 1.0005) < 1e-9
    ind["V"].iloc[5] = 0.5                                             # same price action on light volume
    assert len(jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)["trades"]) == 0


def test_flex_score_and_bounds():
    from tradingagents.strategies.vcp import jlaw_flex as jf

    F = pd.DataFrame({"t": [100, 100], "j": [0, 1], "has": [True, True], "n": [3, 2], "d_first": [0.25, 0.12],
                      "d_last": [0.06, 0.12], "deepest": [0.25, 0.12], "base": [40, 10], "pivot_age": [5, 5],
                      "low_before": [True, True], "volr": [0.6, 1.2], "rs": [100.0, 80.0], "touches": [2, 0], "catalyst": [1.0, 0.0]})
    s = jf.score(F)
    assert s["total"].tolist() == [7.0, 0.0]
    assert jf.bounded(F).tolist() == [True, False]                     # second base is only 10 sessions long


def test_risk_multiplier_scales_and_blocks_new_trades():
    ind, idx, spy, vol, rf = _ind()
    p = jl.JParams(entry="close_breakout", start=str(idx[1].date()))
    full = jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p)
    half = jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p, risk_mult=np.full(len(idx), 0.5))
    none = jl.simulate(ind, {4: [(0, 58.5, 56.0)]}, spy, vol, rf, p, risk_mult=np.zeros(len(idx)))
    assert abs(half["gross"].loc[idx[5]] / full["gross"].loc[idx[5]] - 0.5) < 0.01
    assert len(none["trades"]) == 0 and none["gross"].max() == 0


def test_leader_news_items_score_reports_guidance_and_analysts(monkeypatch):
    from tradingagents.strategies.vcp import leaders, news

    recs = {"AAA": {"windows": [], "items": [["2024-01-10T21:05:00Z", "AAA Q4 EPS $1.10 Beats $1.00 Estimate, Sales $2.0B Beat $1.9B Estimate"],
                                              ["2024-01-10T21:06:00Z", "AAA Raises FY24 Sales Guidance From $8B To $9B"],
                                              ["2024-01-11T12:00:00Z", "Firm A Maintains Buy on AAA, Raises Price Target to $50"],
                                              ["2024-01-11T12:10:00Z", "Firm B Maintains Buy on AAA, Raises Price Target to $55"],
                                              ["2024-01-11T12:20:00Z", "Firm C Upgrades AAA to Buy"]]},
            "BBB": {"windows": [], "items": [["2024-01-10T21:05:00Z", "BBB Q4 EPS $0.10 Misses $0.20 Estimate, Sales $1.0B Beat $0.9B Estimate"]]},
            "CCC": {"windows": [], "items": []}}
    monkeypatch.setattr(news, "load", lambda col: recs[col])
    ev = pd.DataFrame({"col": ["AAA", "BBB", "CCC", "AAA"], "day": pd.to_datetime(["2024-01-20", "2024-01-20", "2024-01-20", "2024-01-10"])})
    it = leaders.news_items(ev)
    assert it["earnings"].tolist() == [1.0, 0.0, 0.0, 0.0]            # beat both / one beat and one miss / no report / not yet published
    assert it["guidance"].tolist() == [1.0, 0.0, 0.0, 0.0] and it["analysts"].tolist() == [1.0, 0.0, 0.0, 0.0]
