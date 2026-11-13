"""Daily-return simulations of the two published intraday momentum rules on SPY 1-minute bars.

Bars are labelled by their start minute (09:30 bar = 09:30:00-09:30:59). "Price at HH:MM" is the
close of the bar that ends at HH:MM, i.e. the bar labelled HH:MM minus one minute; the session
close is the close of the 15:59 bar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Dict, List

import numpy as np
import pandas as pd

RTH_MINUTES = 390


def session_matrix(minutes: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Regular-session bars as day x minute-of-session matrices (only full 390-minute days)."""
    t = minutes.index.time
    rth = minutes[(t >= time(9, 30)) & (t < time(16, 0))]
    mins = (rth.index.hour * 60 + rth.index.minute) - 570
    days = rth.index.normalize()
    out = {}
    for col in ("open", "high", "low", "close", "volume"):
        frame = pd.DataFrame({"day": days, "m": mins, "v": rth[col].to_numpy()})
        out[col] = frame.pivot_table(index="day", columns="m", values="v", aggfunc="last")
    full = out["close"].notna().sum(axis=1) == RTH_MINUTES
    # half days (13:00 close) are dropped: both papers trade full sessions
    out = {k: v.loc[full].reindex(columns=range(RTH_MINUTES)).ffill(axis=1) for k, v in out.items()}
    out["open"] = out["open"].bfill(axis=1)
    return out


def _price_at(close: pd.DataFrame, hhmm: time) -> pd.Series:
    """Close of the bar ending at hh:mm."""
    m = (hhmm.hour * 60 + hhmm.minute) - 570 - 1
    return close[m]


def half_hour_momentum(mat: Dict[str, pd.DataFrame], cost_per_share: float = 0.0045) -> pd.DataFrame:
    """Gao et al. (2018): position(15:30-16:00) = sign(log P_10:00 - log P_prevclose)."""
    close = mat["close"]
    prev_close = close[RTH_MINUTES - 1].shift(1)
    p1000, p1530, p1600 = _price_at(close, time(10, 0)), _price_at(close, time(15, 30)), close[RTH_MINUTES - 1]
    signal = np.sign(np.log(p1000 / prev_close))
    gross = signal * (p1600 / p1530 - 1.0)
    cost = np.where(signal != 0, 2 * cost_per_share / p1530, 0.0)
    out = pd.DataFrame({"signal": signal, "ret": gross - cost}).dropna()
    return out


@dataclass(frozen=True)
class NoiseAreaParams:
    lookback: int = 14             # sessions for the noise area and for daily volatility
    first_check: time = time(10, 0)
    last_check: time = time(15, 30)
    step_minutes: int = 30
    target_daily_vol: float = 0.02
    max_leverage: float = 4.0
    cost_per_share: float = 0.0035 + 0.001   # commission + slippage, per share per side (paper)
    vol_target: bool = True
    exit_time: time = time(16, 0)            # flat at this time (paper: the close)


def noise_area_momentum(mat: Dict[str, pd.DataFrame], p: NoiseAreaParams = NoiseAreaParams()) -> pd.DataFrame:
    """Zarattini, Aziz & Barbon (2024). Returns one row per session with the day's return."""
    o, h, l, c, v = (mat[k] for k in ("open", "high", "low", "close", "volume"))
    day_open = o[0]
    prev_close = c[RTH_MINUTES - 1].shift(1)
    move = (c.div(day_open, axis=0) - 1.0).abs()
    sigma = move.rolling(p.lookback, min_periods=p.lookback).mean().shift(1)   # prior 14 sessions only
    upper = sigma.add(1.0).mul(np.maximum(day_open, prev_close), axis=0)
    lower = (1.0 - sigma).mul(np.minimum(day_open, prev_close), axis=0)
    typical = (h + l + c) / 3.0
    vwap = (typical * v).cumsum(axis=1) / v.cumsum(axis=1).replace(0, np.nan)
    daily_ret = c[RTH_MINUTES - 1].pct_change()
    vol14 = daily_ret.rolling(p.lookback, min_periods=p.lookback).std().shift(1)
    lev = (p.target_daily_vol / vol14).clip(upper=p.max_leverage) if p.vol_target else pd.Series(1.0, index=c.index)

    checks = []
    m = (p.first_check.hour * 60 + p.first_check.minute) - 570 - 1
    exit_idx = min((p.exit_time.hour * 60 + p.exit_time.minute) - 570 - 1, RTH_MINUTES - 1)
    last = min((p.last_check.hour * 60 + p.last_check.minute) - 570 - 1, exit_idx - 1)
    while m <= last:
        checks.append(m)
        m += p.step_minutes

    rows = []
    for day in c.index:
        if np.isnan(sigma.loc[day, 0]) or np.isnan(prev_close.loc[day]) or np.isnan(lev.loc[day]):
            continue
        L = float(lev.loc[day])
        cs, ub, lb, vw = c.loc[day].to_numpy(), upper.loc[day].to_numpy(), lower.loc[day].to_numpy(), vwap.loc[day].to_numpy()
        pos, entry, ret, trades = 0, 0.0, 0.0, 0
        for k in checks:
            px = cs[k]
            # exits (trailing stop) first
            if pos == 1 and px < max(ub[k], vw[k]):
                ret += L * (px / entry - 1.0) - L * p.cost_per_share / px
                pos = 0
            elif pos == -1 and px > min(lb[k], vw[k]):
                ret += L * (1.0 - px / entry) - L * p.cost_per_share / px
                pos = 0
            if pos == 0:
                if px > ub[k]:
                    pos, entry = 1, px
                elif px < lb[k]:
                    pos, entry = -1, px
                if pos != 0:
                    ret -= L * p.cost_per_share / px
                    trades += 1
        if pos != 0:
            px = cs[exit_idx]
            ret += L * pos * (px / entry - 1.0) - L * p.cost_per_share / px
        rows.append({"day": day, "ret": ret, "trades": trades, "leverage": L})
    return pd.DataFrame(rows).set_index("day")


def perf(ret: pd.Series) -> Dict[str, float]:
    ret = ret.dropna()
    if ret.empty or ret.std() == 0:
        return {"days": len(ret), "sharpe": np.nan}
    eq = (1 + ret).cumprod()
    years = len(ret) / 252
    return {
        "days": len(ret),
        "sharpe": ret.mean() / ret.std() * np.sqrt(252),
        "ann_return_%": (eq.iloc[-1] ** (1 / years) - 1) * 100,
        "ann_vol_%": ret.std() * np.sqrt(252) * 100,
        "max_dd_%": (eq / eq.cummax() - 1).min() * 100,
        "hit_rate_%": (ret[ret != 0] > 0).mean() * 100,
    }
