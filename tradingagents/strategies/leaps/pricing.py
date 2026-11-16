"""Black-Scholes pricing of QQQ LEAP calls with an implied-volatility model calibrated to real quotes.

Historical option prices are only available from 2024 (Alpaca), so earlier prices are modelled:
implied vol = a + b * VXN + c * log(K/S) + d * log(K/S)^2 + e * (T - 1), fitted on 2024-26 daily closes
of QQQ calls 5 to 27 months from expiry, 60% to 130% of spot, that traded at least 5 contracts that day.
VXN is the Nasdaq-100 30-day implied volatility index; LEAP vol moves less than it (b < 1) and the
skew makes in-the-money calls carry more vol than at-the-money ones (c < 0).
"""

from __future__ import annotations

from math import erf, exp, log, sqrt
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from ..opening_reversal.data import default_cache_dir

CACHE = default_cache_dir().parent / "leaps"
DIV_YIELD = 0.006          # QQQ dividend yield, roughly constant over the period


def _ncdf(x: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(erf)(x / sqrt(2.0)))


def bs_call(S, K, T, r, sigma, q: float = DIV_YIELD) -> np.ndarray:
    S, K, T, r, sigma = (np.asarray(x, dtype=float) for x in (S, K, T, r, sigma))
    T = np.maximum(T, 1e-6)
    sig = np.maximum(sigma, 1e-4)
    d1 = (np.log(S / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    d2 = d1 - sig * np.sqrt(T)
    return S * np.exp(-q * T) * _ncdf(d1) - K * np.exp(-r * T) * _ncdf(d2)


def bs_delta(S, K, T, r, sigma, q: float = DIV_YIELD) -> np.ndarray:
    S, K, T, r, sigma = (np.asarray(x, dtype=float) for x in (S, K, T, r, sigma))
    T = np.maximum(T, 1e-6)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return np.exp(-q * T) * _ncdf(d1)


def implied_vol(price, S, K, T, r, q: float = DIV_YIELD) -> np.ndarray:
    """Bisection, vectorised; NaN where the price is outside the no-arbitrage range."""
    price, S, K, T, r = (np.asarray(x, dtype=float) for x in (price, S, K, T, r))
    lo, hi = np.full(price.shape, 0.01), np.full(price.shape, 2.0)
    intrinsic = np.maximum(S * np.exp(-q * T) - K * np.exp(-r * T), 0.0)
    bad = (price <= intrinsic + 1e-6) | (price >= S)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        f = bs_call(S, K, T, r, mid, q) - price
        lo, hi = np.where(f < 0, mid, lo), np.where(f < 0, hi, mid)
    out = 0.5 * (lo + hi)
    out[bad] = np.nan
    return out


def market() -> pd.DataFrame:
    rd = lambda n: pd.read_csv(CACHE / f"{n}.csv", index_col=0, parse_dates=True)["Close"]
    df = pd.DataFrame({"QQQ": rd("QQQ"), "VGT": rd("VGT"), "VXN": rd("_VXN"), "VIX": rd("_VIX"), "IRX": rd("_IRX")})
    df["r"] = df["IRX"].ffill() / 100.0
    df["VXN"] = df["VXN"].ffill()
    return df


def calibration_data() -> pd.DataFrame:
    m = market()
    b = pd.read_csv(CACHE / "qqq_leap_bars.csv.gz", parse_dates=["date", "exp"])
    b = b[b["volume"] >= 5].copy()
    b = b.join(m[["QQQ", "VXN", "r"]], on="date").dropna(subset=["QQQ", "VXN", "r"])
    b["T"] = (b["exp"] - b["date"]).dt.days / 365.0
    b["m"] = np.log(b["K"] / b["QQQ"])
    b = b[(b["T"] >= 150 / 365) & (b["T"] <= 820 / 365) & (b["m"] >= np.log(0.6)) & (b["m"] <= np.log(1.3))]
    b["iv"] = implied_vol(b["close"], b["QQQ"], b["K"], b["T"], b["r"])
    return b.dropna(subset=["iv"])


def fit(b: pd.DataFrame) -> Dict[str, float]:
    X = np.c_[np.ones(len(b)), b["VXN"] / 100.0, b["m"], b["m"] ** 2, b["T"] - 1.0]
    coef, *_ = np.linalg.lstsq(X, b["iv"].to_numpy(), rcond=None)
    return dict(zip(["a", "b", "c", "d", "e"], map(float, coef)))


def model_iv(vxn, S, K, T, coef: Dict[str, float]) -> np.ndarray:
    m = np.log(np.asarray(K, dtype=float) / np.asarray(S, dtype=float))
    iv = coef["a"] + coef["b"] * np.asarray(vxn, dtype=float) / 100.0 + coef["c"] * m + coef["d"] * m ** 2 + coef["e"] * (np.asarray(T, dtype=float) - 1.0)
    return np.clip(iv, 0.08, 1.5)
