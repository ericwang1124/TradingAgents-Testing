"""End-of-day rebalance of the core diversified portfolio on Alpaca paper (market-on-close orders).

Weights are refit once a year (``core-weights``) on the full history and saved next to this file;
the daily run only needs ~2 years of daily bars to compute today's positions and strategy scales.
Today's close is approximated by the latest trade at run time (the run is scheduled ~15:12 ET and
orders are market-on-close, so they fill at the actual close).
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ... import core_portfolio as cp
from ..data import NY
from . import journal
from .alpaca_trading import AlpacaClient

WEIGHTS_PATH = Path(__file__).with_name("core_weights.json")
MIN_TRADE_USD = 250.0
MOC_CUTOFF = time(15, 49)
CORE_FRACTION = 1.0          # share of account equity run by the core book (before its leverage)
ORDER_PREFIX = "core"


def _history_yahoo(years: str = "2y") -> Dict[str, pd.DataFrame]:
    import yfinance as yf

    out = {}
    for t in cp.UNIVERSE:
        h = yf.Ticker(t).history(period=years, auto_adjust=True)[["Open", "High", "Low", "Close"]]
        h.index = pd.DatetimeIndex(h.index.date)
        out[t] = h
    return out


def compute_weights(year: int) -> Dict[str, float]:
    """Walk-forward weights for ``year`` from all history before it (atlas cache, Yahoo)."""
    from ...strategy_atlas import load_ohlc

    d = load_ohlc()
    cal = d["SPY"].index[d["SPY"].index >= "2007-06-01"]
    C = pd.DataFrame({t: d[t]["Close"] for t in cp.UNIVERSE}).reindex(cal)
    P = cp.strategy_positions(C, d["SPY"]["High"].reindex(cal), d["SPY"]["Low"].reindex(cal), cal)
    R = cp.strategy_returns(P, C)
    Rs = R * cp.strategy_scale(R).shift(1)
    w = cp.fit_weights(Rs[Rs.index.year < year])
    return {k: float(v) for k, v in w.items() if v > 0}


def save_weights(year: int) -> Dict[str, float]:
    w = compute_weights(year)
    WEIGHTS_PATH.write_text(json.dumps({"year": year, "weights": w}, indent=2))
    return w


def load_weights() -> Dict[str, float]:
    return json.loads(WEIGHTS_PATH.read_text())["weights"]


def target_exposures(hist: Dict[str, pd.DataFrame], today: date, today_prices: Dict[str, float],
                     next_sessions: List[date], weights: Dict[str, float]) -> pd.Series:
    """Net ETF exposure (fraction of core capital) to hold from today's close."""
    cal = hist["SPY"].index
    C = pd.DataFrame({t: hist[t]["Close"] for t in cp.UNIVERSE}).reindex(cal)
    H, L = hist["SPY"]["High"].reindex(cal), hist["SPY"]["Low"].reindex(cal)
    ts = pd.Timestamp(today)
    if ts not in C.index:  # add today's row from live prices
        C.loc[ts] = np.nan
        H.loc[ts], L.loc[ts] = np.nan, np.nan
        C = C.sort_index(); H = H.sort_index(); L = L.sort_index()
    for t, p in today_prices.items():
        if t in C.columns:
            C.loc[ts, t] = p
    C = C.ffill()
    spy_today = today_prices.get("SPY", C.loc[ts, "SPY"])
    H.loc[ts] = np.nanmax([H.loc[ts], spy_today]) if not np.isnan(H.loc[ts]) else spy_today
    L.loc[ts] = np.nanmin([L.loc[ts], spy_today]) if not np.isnan(L.loc[ts]) else spy_today
    sessions = C.index.union(pd.DatetimeIndex(next_sessions))
    P = cp.strategy_positions(C, H, L, sessions)
    R = cp.strategy_returns(P, C)
    scale = cp.strategy_scale(R)
    W = pd.DataFrame({k: weights.get(k, 0.0) for k in R.columns}, index=C.index)
    E = cp.combine(P, W, scale).loc[ts]
    gross = E.abs().sum()
    lev = min(cp.LEVERAGE, cp.MAX_GROSS / gross) if gross > 0 else 0.0
    return (E * lev).clip(lower=0.0)


def plan_orders(targets_usd: Dict[str, float], current_qty: Dict[str, float], prices: Dict[str, float]) -> List[dict]:
    """Whole-share deltas (sells first); ignores trades below MIN_TRADE_USD."""
    orders = []
    for sym in sorted(set(targets_usd) | set(current_qty)):
        px = prices.get(sym)
        if not px:
            continue
        want = max(targets_usd.get(sym, 0.0), 0.0) / px   # long-only
        have = max(current_qty.get(sym, 0.0), 0.0)
        delta = want - have
        qty = math.floor(have) if want == 0 else math.floor(abs(delta))  # MOC orders take whole shares
        if qty == 0 or qty * px < MIN_TRADE_USD:
            continue
        orders.append({"symbol": sym, "side": "buy" if delta > 0 else "sell", "qty": qty, "est_usd": round(qty * px, 2)})
    return sorted(orders, key=lambda o: o["side"] != "sell")


def rebalance(day: date, client: Optional[AlpacaClient] = None, dry_run: bool = False) -> dict:
    client = client or AlpacaClient()
    now = pd.Timestamp.now(tz=NY)
    cal = client.calendar(day, day + timedelta(days=10))
    if not cal or cal[0]["date"] != day.isoformat():
        rec = {"date": day.isoformat(), "skipped": "market closed"}
        journal.write(day, "core", rec)
        return rec
    next_sessions = [date.fromisoformat(c["date"]) for c in cal[1:]]
    weights = load_weights()
    hist = _history_yahoo()
    live_syms = sorted({cp.LIVE_TICKER.get(t, t) for t in cp.UNIVERSE if t not in ("BIL",)})
    prices = client.latest_prices(live_syms)
    today_prices = {t: prices[cp.LIVE_TICKER.get(t, t)] for t in cp.UNIVERSE if cp.LIVE_TICKER.get(t, t) in prices
                    and t not in cp.LIVE_TICKER}
    E = target_exposures(hist, day, today_prices, next_sessions, weights)
    acct = client.account()
    equity = float(acct["equity"]) * CORE_FRACTION
    targets = {cp.LIVE_TICKER.get(t, t): float(v * equity) for t, v in E.items() if v > 1e-4}
    positions = {p["symbol"]: float(p["qty"]) for p in client.positions() if p.get("asset_class") == "us_equity"}
    orders = plan_orders(targets, positions, prices)
    tif = "cls" if now.time() <= MOC_CUTOFF else "day"
    rec = {"date": day.isoformat(), "run_at": now.isoformat(), "equity": equity, "time_in_force": tif,
           "exposures": {k: round(float(v), 4) for k, v in E.items() if v > 1e-4},
           "targets_usd": {k: round(v, 2) for k, v in targets.items()},
           "gross_exposure": round(float(E.sum()), 3), "orders": orders, "submitted": [], "dry_run": dry_run}
    if not dry_run:
        for o in orders:
            try:
                res = client.submit_order(o["symbol"], o["qty"], o["side"], time_in_force=tif,
                                          client_order_id=f"{ORDER_PREFIX}-{day:%Y%m%d}-{o['symbol']}-{o['side']}")
                rec["submitted"].append({"symbol": o["symbol"], "id": res.get("id"), "status": res.get("status")})
            except Exception as e:  # keep going; log the failure
                rec["submitted"].append({"symbol": o["symbol"], "error": str(e)[:300]})
    journal.write(day, "core", rec)
    return rec
