"""Per-session features known at 10:00 ET and the continuation returns that follow."""

from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from ..intraday_momentum.strategies import RTH_MINUTES, session_matrix

COST_PER_SHARE = 0.0045   # per side, as in the momentum re-tests
OR_BARS = 30              # 09:30-09:59
NOON_IDX = 149            # bar ending 12:00

FEATURES = {
    "gap_atr": "open vs prior close, in 14-day ATRs",
    "pre_ret_atr": "09:00 -> 09:29 pre-market move, in ATRs",
    "pre_relvol": "09:00-09:29 pre-market volume / 20-day median",
    "or_ret_atr": "09:30 -> 10:00 move, in ATRs (signed)",
    "or_range_atr": "opening range (09:30-09:59 high-low), in ATRs",
    "efficiency": "|net 30-min move| / sum of |1-min moves| (1 = one-way drive, 0 = rotation)",
    "pos_in_or": "10:00 price within the opening range (0 = low, 1 = high)",
    "vwap_dist_atr": "10:00 price vs session VWAP, in ATRs",
    "or_relvol": "09:30-09:59 volume / 20-day median",
    "open_inside_prev_range": "open inside the prior day's high-low (0/1)",
    "or_broke_prev_extreme": "opening range took out the prior day's high or low (0/1)",
    "vix_prev": "prior-day VIX close",
    "trend_sma50": "prior close vs 50-day SMA, %",
}


def build_features(minutes: pd.DataFrame, vix: pd.Series) -> pd.DataFrame:
    mat = session_matrix(minutes)
    o, h, l, c, v = (mat[k] for k in ("open", "high", "low", "close", "volume"))
    day_open, p10, p12, p16 = o[0], c[OR_BARS - 1], c[NOON_IDX], c[RTH_MINUTES - 1]
    prev_close = p16.shift(1)
    dh, dl = h.max(axis=1), l.min(axis=1)
    tr = pd.concat([dh, prev_close], axis=1).max(axis=1) - pd.concat([dl, prev_close], axis=1).min(axis=1)
    atr = tr.rolling(14, min_periods=14).mean().shift(1)
    or_hi, or_lo = h.iloc[:, :OR_BARS].max(axis=1), l.iloc[:, :OR_BARS].min(axis=1)
    path = c.iloc[:, :OR_BARS].diff(axis=1).abs().sum(axis=1) + (c[0] - day_open).abs()
    typical = (h + l + c).iloc[:, :OR_BARS] / 3.0
    vwap10 = (typical * v.iloc[:, :OR_BARS]).sum(axis=1) / v.iloc[:, :OR_BARS].sum(axis=1)
    or_vol = v.iloc[:, :OR_BARS].sum(axis=1)

    t = minutes.index.time
    pre = minutes[(t >= time(9, 0)) & (t < time(9, 30))]
    pg = pre.groupby(pre.index.normalize())
    pre_first, pre_last, pre_vol = pg["open"].first(), pg["close"].last(), pg["volume"].sum()
    pre_first, pre_last, pre_vol = (s.reindex(c.index) for s in (pre_first, pre_last, pre_vol))

    vix_s = pd.Series(vix.to_numpy(), index=pd.to_datetime(vix.index)).sort_index()
    vix_prev = vix_s.reindex(c.index.tz_localize(None).normalize(), method="ffill").shift(1)
    sma50 = p16.rolling(50, min_periods=50).mean().shift(1)

    direction = np.sign(p10 - day_open)
    cost10 = 2 * COST_PER_SHARE / p10
    f = pd.DataFrame({
        "gap_atr": (day_open - prev_close) / atr,
        "pre_ret_atr": (pre_last - pre_first) / atr,
        "pre_relvol": pre_vol / pre_vol.rolling(20, min_periods=10).median().shift(1),
        "or_ret_atr": (p10 - day_open) / atr,
        "or_range_atr": (or_hi - or_lo) / atr,
        "efficiency": (p10 - day_open).abs() / path.replace(0, np.nan),
        "pos_in_or": (p10 - or_lo) / (or_hi - or_lo).replace(0, np.nan),
        "vwap_dist_atr": (p10 - vwap10) / atr,
        "or_relvol": or_vol / or_vol.rolling(20, min_periods=10).median().shift(1),
        "open_inside_prev_range": ((day_open <= dh.shift(1)) & (day_open >= dl.shift(1))).astype(float),
        "or_broke_prev_extreme": ((or_hi > dh.shift(1)) | (or_lo < dl.shift(1))).astype(float),
        "vix_prev": vix_prev.to_numpy(),
        "trend_sma50": (prev_close / sma50 - 1) * 100,
        "direction": direction,
        # continuation returns from 10:00 (positive = the first-30-minute direction kept going)
        "cont_to_noon": direction * (p12 / p10 - 1) - cost10,
        "rev_to_noon": -direction * (p12 / p10 - 1) - cost10,
        "cont_to_close": direction * (p16 / p10 - 1) - cost10,
        "rev_to_close": -direction * (p16 / p10 - 1) - cost10,
    }, index=c.index)
    f.index = pd.Index([d.date() for d in f.index], name="date")
    return f.dropna(subset=["gap_atr", "or_ret_atr", "vix_prev"])
