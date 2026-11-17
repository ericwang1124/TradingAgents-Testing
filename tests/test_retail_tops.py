"""Retail TOPS mechanics on synthetic data (no network)."""

import numpy as np
import pandas as pd

from tradingagents.strategies.vcp import retail_tops as rt


def _x(close, low=None, opn=None):
    c = np.asarray(close, float).reshape(-1, 1)
    l = c * 0.99 if low is None else np.asarray(low, float).reshape(-1, 1)
    o = c if opn is None else np.asarray(opn, float).reshape(-1, 1)
    s = pd.DataFrame(c)
    return {"Cn": c, "On": o, "Ln": l, "adr": np.full_like(c, 2.0), "sma10n": s.rolling(10).mean().to_numpy(),
            "sma20n": s.rolling(20).mean().to_numpy(), "ema21n": s.ewm(span=21, adjust=False).mean().to_numpy(),
            "low10": pd.DataFrame(l).rolling(10).min().to_numpy(), "w30n": np.full_like(c, np.nan), "week_end": np.zeros(len(c), bool)}


def test_play_stop_breakeven_and_trail():
    up = np.r_[np.full(30, 100.0), np.linspace(100, 130, 30), np.linspace(130, 110, 20)]
    res = rt.play(rt.Idea("t", 29, 0, 100.0, 95.0, "sma20", "10pct"), _x(up))
    assert res["reason"] == "below sma20" and res["exit"] > 115                 # rode the run, left when it rolled over
    down = np.r_[np.full(30, 100.0), np.linspace(99, 80, 20)]
    res2 = rt.play(rt.Idea("t", 29, 0, 100.0, 95.0, "sma20", "10pct"), _x(down))
    assert res2["reason"] == "below sma20" and res2["exit_t"] == 30          # trails from the first day: out on the first close below
    res2b = rt.play(rt.Idea("t", 29, 0, 100.0, 95.0, "sma20", "5d"), _x(down))
    assert res2b["reason"] == "stop" and abs(res2b["exit"] / (100 * (1 + rt.COST)) - 1 + 0.05) < 0.01   # Qullamaggie: day-low stop first
    flat = np.r_[np.full(30, 100.0), np.full(10, 101.0), np.full(5, 99.0)]
    opn = flat.copy()
    opn[40] = 100.5                                                               # opens above the moved stop, trades through it
    res3 = rt.play(rt.Idea("t", 29, 0, 100.0, 95.0, "low10", "5d"), _x(flat, low=np.r_[np.full(30, 99.0), np.full(10, 100.5), np.full(5, 98.0)], opn=opn))
    assert res3["reason"] == "stop" and res3["exit"] >= 100 * (1 + rt.COST) * (1 - rt.COST) - 1e-9   # stop moved to entry after 5 days


def test_monthly_weights_shrink_and_pause():
    dates = pd.bdate_range("2019-01-01", "2021-12-31")
    rows = [{"who": "Kell crossback", "exit_date": d, "R": 0.6, "reason": "x"} for d in dates[::10][:60]]
    rows += [{"who": "Darvas box", "exit_date": d, "R": -0.2, "reason": "x"} for d in dates[::10][:60]]
    rows += [{"who": "Qullamaggie EP", "exit_date": d, "R": 0.3, "reason": "x"} for d in dates[::10][:60]]
    rows += [{"who": "Weinstein stage 2", "exit_date": dates[5], "R": 5.0, "reason": "x"}]           # too few ideas
    W = rt.monthly_weights(pd.DataFrame(rows), dates)
    last = W.iloc[-1]
    assert last["Darvas box"] == 0.0 and last["Weinstein stage 2"] == 1.0
    assert abs(last["Kell crossback"] / last["Qullamaggie EP"] - 2.0) < 1e-9 and abs((last["Kell crossback"] + last["Qullamaggie EP"]) / 2 - 1.0) < 1e-9


def test_portfolio_sizes_by_risk_and_closes_same_day_stops():
    dates = pd.bdate_range("2020-01-01", periods=40)
    x = {"Cn": np.full((40, 2), 100.0)}
    x["Cn"][20:, 0] = 110.0
    tr = pd.DataFrame([{"who": "Kell crossback", "j": 0, "entry_t": 10, "exit_t": 30, "entry": 100.0, "exit": 110.0, "r": 0.05, "R": 2.0, "entry_date": dates[10]},
                       {"who": "Darvas box", "j": 1, "entry_t": 10, "exit_t": 10, "entry": 100.0, "exit": 95.0, "r": 0.05, "R": -1.0, "entry_date": dates[10]}])
    rf = pd.Series(0.0, index=dates)
    p = rt.portfolio(tr, x, dates, rf, "equal", start=str(dates[1].date()))
    eq = (1 + p["excess"]).cumprod()
    assert abs(p["gross"].iloc[12] - 0.07 / (1 - 0.07 * 0.05)) < 1e-6           # 0.35% risk / 5% stop = 7% of equity (after the other loss)
    assert abs(eq.iloc[-1] - (1 + 0.07 * 0.10 - 0.07 * 0.05)) < 1e-6           # +10% on one, -5% on the other
