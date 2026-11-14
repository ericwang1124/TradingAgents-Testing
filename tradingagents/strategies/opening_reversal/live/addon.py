"""Intraday add-on: high-efficiency open continuation, long side only, SPY shares on Alpaca paper.

At 10:00 ET: efficiency = |P(10:00) - open| / (path length of 1-minute closes 09:30-09:59). If it is at
or above this year's threshold (2/3 quantile of past sessions, see addon_params.json) and the
first 30 minutes were up, buy SPY for ADDON_NOTIONAL x equity (capped by day-trading buying power)
and sell the same quantity at EXIT_TIME. Runs only when the morning decision is GO. (Backtest: SPY
2021-26 long side 5.9 bp/trade, t = 2.3. Size raised from 1x to 1.5x on 2026-11-14: the add-on is
nearly uncorrelated with the core, so the combined Sharpe rises with its size; see
reports/综合夏普_提升检验.md. The short side through SH was tested and dropped: after SH's wider spread
it averaged -0.6 bp/trade.)
"""

from __future__ import annotations

import json
import time as _time
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..data import NY
from . import journal
from .alpaca_trading import AlpacaClient

PARAMS_PATH = Path(__file__).with_name("addon_params.json")
ADDON_NOTIONAL = 1.5           # x account equity
BP_USE = 0.9                   # never use more than this share of day-trading buying power
ENTRY_TIME = time(10, 0, 5)
EXIT_TIME = time(11, 55)       # backtest exits at 12:00; 11:55 keeps the run inside a 2-hour window
SYMBOL = "SPY"
ORDER_PREFIX = "addon"
HARD_RULES = ("market_closed", "half_day")


def efficiency(bars: pd.DataFrame) -> Dict[str, float]:
    """bars: 1-minute bars of the first 30 minutes (09:30..09:59), oldest first."""
    o = float(bars["open"].iloc[0])
    c = bars["close"].to_numpy(dtype=float)
    path = float(np.abs(np.diff(c)).sum() + abs(c[0] - o))
    net = c[-1] - o
    return {"open": o, "p10": float(c[-1]), "direction": float(np.sign(net)),
            "efficiency": abs(net) / path if path > 0 else 0.0, "bars": int(len(bars))}


def load_threshold() -> float:
    return float(json.loads(PARAMS_PATH.read_text())["efficiency_threshold"])


def addon_qty(equity: float, acct: Dict[str, Any], price: float, size: float = 1.0) -> int:
    """Whole SPY shares for ADDON_NOTIONAL x equity x size, capped by day-trading buying power."""
    want = ADDON_NOTIONAL * equity * size
    bp = float(acct.get("daytrading_buying_power") or 0.0) or float(acct.get("buying_power") or 0.0)
    if bp > 0:
        want = min(want, BP_USE * bp)
    return max(int(want // price), 0)


def _sleep_until(ts: pd.Timestamp) -> None:
    while True:
        rem = (ts - pd.Timestamp.now(tz=NY)).total_seconds()
        if rem <= 0:
            return
        _time.sleep(min(rem, 30))


def run(day: date, client: Optional[AlpacaClient] = None, dry_run: bool = False) -> Dict[str, Any]:
    client = client or AlpacaClient()
    rec: Dict[str, Any] = {"date": day.isoformat(), "dry_run": dry_run, "traded": False, "events": []}

    def log(msg, **kw):
        rec["events"].append({"time": pd.Timestamp.now(tz=NY).strftime("%H:%M:%S"), "msg": msg, **kw})
        print(rec["events"][-1], flush=True)
        journal.write(day, "addon", rec)

    decision = journal.read(day, "decision") or {}
    if decision.get("decision") != "GO":
        log("decision is not GO; add-on not run", decision=decision.get("decision"))
        return rec
    _sleep_until(pd.Timestamp(datetime.combine(day, ENTRY_TIME), tz=NY))
    bars = client.bars_today(SYMBOL, day)
    t = bars.index.time
    first30 = bars[(t >= time(9, 30)) & (t < time(10, 0))]
    if len(first30) < 20:
        log("not enough opening bars", bars=len(first30))
        return rec
    sig = efficiency(first30)
    thr = load_threshold()
    sig.update(threshold=thr, take=bool(sig["efficiency"] >= thr and sig["direction"] > 0))
    rec["signal"] = sig
    log("signal", **sig)
    if not sig["take"]:
        log("no entry (efficiency below threshold or first 30 minutes not up)")
        return rec
    acct = client.account()
    equity = float(acct["equity"])
    price = client.latest_trade_price(SYMBOL)
    qty = addon_qty(equity, acct, price, float(decision.get("size", 1.0)))
    rec["plan"] = {"qty": qty, "ref_price": price, "notional": round(qty * price, 2)}
    if dry_run or qty <= 0:
        log("dry run or zero size; no order", **rec["plan"])
        return rec
    buy = client.wait_filled(client.submit_order(SYMBOL, qty, "buy", client_order_id=f"{ORDER_PREFIX}-{day:%Y%m%d}-entry")["id"], 60)
    if buy["status"] != "filled":
        try:
            client.cancel_order(buy["id"])
        except Exception:
            pass
        buy = client.get_order(buy["id"])
    filled = int(float(buy.get("filled_qty") or 0))
    if filled <= 0:
        log("entry not filled", status=buy["status"])
        return rec
    rec["traded"] = True
    rec["entry_fill"] = {"price": float(buy["filled_avg_price"]), "qty": filled, "time": buy.get("filled_at"),
                         "status": buy["status"]}
    log("entry filled", **rec["entry_fill"])
    _sleep_until(pd.Timestamp(datetime.combine(day, EXIT_TIME), tz=NY))
    sell = client.wait_filled(client.submit_order(SYMBOL, rec["entry_fill"]["qty"], "sell",
                                                  client_order_id=f"{ORDER_PREFIX}-{day:%Y%m%d}-exit")["id"], 60)
    rec["exit_fill"] = {"price": float(sell.get("filled_avg_price") or 0), "time": sell.get("filled_at"), "status": sell["status"]}
    rec["pnl_usd"] = round((rec["exit_fill"]["price"] - rec["entry_fill"]["price"]) * rec["entry_fill"]["qty"], 2)
    rec["return_pct"] = round((rec["exit_fill"]["price"] / rec["entry_fill"]["price"] - 1) * 100, 3)
    log("exit", **rec["exit_fill"], pnl_usd=rec["pnl_usd"])
    return rec


def shadow(day: date, minutes: pd.DataFrame) -> Dict[str, Any]:
    """What the add-on would have done (SIP bars, after the fact), traded or not."""
    b = minutes[minutes.index.date == day]
    t = b.index.time
    first30 = b[(t >= time(9, 30)) & (t < time(10, 0))]
    if len(first30) < 20:
        return {"available": False}
    sig = efficiency(first30)
    thr = load_threshold()
    take = sig["efficiency"] >= thr and sig["direction"] > 0
    out = {"available": True, **sig, "threshold": thr, "take": bool(take)}
    exit_bar = b[t < EXIT_TIME]
    if take and len(exit_bar):
        out["return_pct"] = round((float(exit_bar["close"].iloc[-1]) / sig["p10"] - 1) * 100, 3)
    return out
