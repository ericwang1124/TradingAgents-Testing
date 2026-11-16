"""QQQ LEAP call sleeve on Alpaca paper: buy one-year at-the-money calls on 2% down days in an uptrend.

Run once a day near the close (after the core rebalance):
  1. exits: sell a position whose bid is 20% above its cost, or that has been held 189 sessions
     (about 9 months), or that has 90 days or less to expiry;
  2. entry: if QQQ is 2% or more below the previous close and above its 200-day average, no entry in
     the past 20 sessions and fewer than 2 positions open, buy the listed call with expiry closest
     to one year out (300-450 days) and strike closest to spot: as many contracts as 6.5% of equity
     pays for, and one contract if that is zero but one costs no more than 10% of equity (at $100k of
     equity one at-the-money QQQ LEAP costs $7-9k depending on volatility, so the unit is one contract).
Orders are limit orders at the mid price, re-sent at the far side of the quote if not filled.

Backtest 2001-2026 (reports/LEAP_call_跌2%买入.md, modelled prices before 2024): 88 trades, win rate
93%, average +17%, average loss -73%. Added to the core + add-on at this size (6.5% per entry, at most
2 open) the 2011-26 Sharpe went from 0.93 to 1.01 and the annual return from 11.4% to 16.5%, while the
2021-26 Sharpe went from 1.05 to 0.99 and the 2024-05+ Sharpe from 1.20 to 1.16: extra QQQ exposure
with a high hit rate, added at the user's request.
State (entry dates, last entry) lives in journal/opening_reversal/leaps_state.json.
"""

from __future__ import annotations

import json
import math
import time as _time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from . import journal
from .alpaca_trading import AlpacaClient
from .settings import JOURNAL_DIR

SYMBOL = "QQQ"
DROP = -0.02
SMA_DAYS = 200
COOLDOWN = 20
PREMIUM_FRAC = 0.065
MAX_ONE_CONTRACT_FRAC = 0.10
MAX_OPEN = 2
TARGET_DTE, DTE_MIN, DTE_MAX = 365, 300, 450
TAKE_PROFIT = 0.20
MAX_HOLD = 189
MIN_DTE = 90
STATE_PATH = JOURNAL_DIR / "leaps_state.json"
ORDER_PREFIX = "leaps"


# ------------------------------------------------------------------ pure decisions
def entry_signal(closes: pd.Series, price: float) -> Dict[str, Any]:
    """``closes``: daily closes up to yesterday; ``price``: today's price near the close."""
    prev = float(closes.iloc[-1])
    sma = float(pd.concat([closes.iloc[-(SMA_DAYS - 1):], pd.Series([price])]).mean())
    ret = price / prev - 1
    return {"price": price, "prev_close": prev, "return": ret, "sma200": sma, "drop": bool(ret <= DROP),
            "uptrend": bool(price > sma), "signal": bool(ret <= DROP and price > sma)}


def sessions_between(sessions: pd.DatetimeIndex, a: date, b: date) -> int:
    s = pd.DatetimeIndex(sessions)
    return int(((s > pd.Timestamp(a)) & (s <= pd.Timestamp(b))).sum())


def pick_contract(contracts: List[Dict[str, Any]], spot: float, today: date) -> Optional[Dict[str, Any]]:
    rows = []
    for c in contracts:
        exp = date.fromisoformat(c["expiration_date"])
        dte = (exp - today).days
        if DTE_MIN <= dte <= DTE_MAX and c.get("tradable", True):
            rows.append((abs(dte - TARGET_DTE), abs(float(c["strike_price"]) - spot), c))
    if not rows:
        return None
    best_dte = min(r[0] for r in rows)
    return min((r for r in rows if r[0] == best_dte), key=lambda r: r[1])[2]


def exit_reason(pos: Dict[str, Any], bid: float, today: date, held_sessions: int) -> Optional[str]:
    if bid > 0 and bid >= pos["cost"] * (1 + TAKE_PROFIT) - 1e-9:          # exactly +20% counts (no float shortfall)
        return "take profit"
    if held_sessions >= MAX_HOLD:
        return "held 9 months"
    if (date.fromisoformat(pos["expiry"]) - today).days <= MIN_DTE:
        return "90 days to expiry"
    return None


def contracts_to_buy(equity: float, ask: float) -> int:
    if ask <= 0:
        return 0
    n = int(PREMIUM_FRAC * equity // (ask * 100))
    return n if n > 0 else int(ask * 100 <= MAX_ONE_CONTRACT_FRAC * equity)


# ------------------------------------------------------------------ state and execution
def load_state() -> Dict[str, Any]:
    return json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {"last_entry": None, "positions": {}}


def save_state(state: Dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _history(days: int = 420) -> pd.Series:
    import yfinance as yf

    h = yf.Ticker(SYMBOL).history(period="2y", auto_adjust=True)["Close"]
    h.index = pd.DatetimeIndex(h.index.date)
    return h.iloc[-days:]


def trade_option(client: AlpacaClient, symbol: str, qty: int, side: str, day: date, tag: str, wait_s: float = 90.0) -> Dict[str, Any]:
    """Limit at the mid, then at the far side of the quote; returns filled quantity and average price."""
    out = {"symbol": symbol, "side": side, "qty": qty, "filled": 0, "avg_price": None, "attempts": []}
    remaining = qty
    for n, where in enumerate(("mid", "far")):
        q = client.option_quote(symbol)
        bid, ask = q["bid"], q["ask"]
        if ask <= 0 or bid <= 0 or remaining <= 0:
            out["attempts"].append({"note": "no two-sided quote", "bid": bid, "ask": ask})
            break
        px = round((bid + ask) / 2, 2) if where == "mid" else (ask if side == "buy" else bid)
        try:
            res = client.submit_order(symbol, remaining, side, order_type="limit", limit_price=px,
                                      client_order_id=f"{ORDER_PREFIX}-{day:%Y%m%d}-{tag}-{n}")
            fin = client.wait_filled(res["id"], timeout_s=wait_s)
            if fin.get("status") not in ("filled", "canceled", "expired", "rejected"):
                try:
                    client.cancel_order(res["id"])
                except Exception:
                    pass
                fin = client.get_order(res["id"])
            filled = int(float(fin.get("filled_qty") or 0))
            out["attempts"].append({"limit": px, "bid": bid, "ask": ask, "status": fin.get("status"), "filled": filled,
                                    "avg_price": fin.get("filled_avg_price")})
            if filled:
                prev_cost = (out["avg_price"] or 0.0) * out["filled"]
                out["filled"] += filled
                out["avg_price"] = (prev_cost + filled * float(fin["filled_avg_price"])) / out["filled"]
                remaining -= filled
        except Exception as e:
            out["attempts"].append({"error": str(e)[:300]})
        if remaining <= 0:
            break
    return out


def run(day: date, client: Optional[AlpacaClient] = None, dry_run: bool = False, history: Optional[pd.Series] = None) -> Dict[str, Any]:
    client = client or AlpacaClient()
    rec: Dict[str, Any] = {"date": day.isoformat(), "dry_run": dry_run, "exits": [], "entry": None}
    cal = client.calendar(day, day)
    if not cal or cal[0]["date"] != day.isoformat():
        rec["skipped"] = "market closed"
        journal.write(day, "leaps", rec)
        return rec
    state = load_state()
    held = {p["symbol"]: p for p in client.positions() if p.get("asset_class") == "us_option" and p["symbol"].startswith(SYMBOL)}
    for s in list(state["positions"]):                      # closed outside this run (expired, assigned, by hand)
        if s not in held:
            rec["exits"].append({"symbol": s, "reason": "no longer held"})
            del state["positions"][s]
    for s, p in held.items():                               # held but unknown here: adopt with today's date
        if s not in state["positions"]:
            state["positions"][s] = {"entry_date": day.isoformat(), "qty": int(float(p["qty"])), "cost": float(p["avg_entry_price"]),
                                     "expiry": f"20{s[3:5]}-{s[5:7]}-{s[7:9]}", "strike": int(s[-8:]) / 1000, "adopted": True}
    hist = history if history is not None else _history()
    sessions = pd.DatetimeIndex(list(hist.index) + [pd.Timestamp(day)])
    # ---- exits
    for s, pos in list(state["positions"].items()):
        q = client.option_quote(s)
        n_held = sessions_between(sessions, date.fromisoformat(pos["entry_date"]), day)
        why = exit_reason(pos, q["bid"], day, n_held)
        row = {"symbol": s, "bid": q["bid"], "ask": q["ask"], "cost": pos["cost"], "held_sessions": n_held, "reason": why}
        if why and not dry_run:
            row["order"] = trade_option(client, s, pos["qty"], "sell", day, f"exit-{s}")
            sold = row["order"]["filled"]
            if sold:
                row["return"] = row["order"]["avg_price"] / pos["cost"] - 1
                pos["qty"] -= sold
            if pos["qty"] <= 0:
                del state["positions"][s]
        if why:
            rec["exits"].append(row)
    # ---- entry
    price = client.latest_trade_price(SYMBOL)
    hist_before = hist[hist.index < pd.Timestamp(day)]
    sig = entry_signal(hist_before, price)
    last = state.get("last_entry")
    since = sessions_between(sessions, date.fromisoformat(last), day) if last else 10 ** 6
    sig.update(sessions_since_last_entry=since if last else None, open_positions=len(state["positions"]))
    rec["signal"] = sig
    if sig["signal"] and since >= COOLDOWN and len(state["positions"]) < MAX_OPEN:
        lo, hi = price * 0.9, price * 1.1
        contracts = client.call_contracts(SYMBOL, day + timedelta(days=DTE_MIN), day + timedelta(days=DTE_MAX), lo, hi)
        c = pick_contract(contracts, price, day)
        if c is None:
            rec["entry"] = {"note": "no contract 300-450 days out near the money"}
        else:
            q = client.option_quote(c["symbol"])
            equity = float(client.account()["equity"])
            n = contracts_to_buy(equity, q["ask"])
            rec["entry"] = {"contract": c["symbol"], "expiry": c["expiration_date"], "strike": float(c["strike_price"]),
                            "bid": q["bid"], "ask": q["ask"], "contracts": n, "premium_usd": round(n * q["ask"] * 100, 2)}
            if n <= 0:
                rec["entry"]["note"] = "one contract costs more than 10% of equity"
            elif not dry_run:
                o = trade_option(client, c["symbol"], n, "buy", day, "entry")
                rec["entry"]["order"] = o
                if o["filled"]:
                    state["positions"][c["symbol"]] = {"entry_date": day.isoformat(), "qty": o["filled"], "cost": o["avg_price"],
                                                       "expiry": c["expiration_date"], "strike": float(c["strike_price"])}
                    state["last_entry"] = day.isoformat()
    rec["open_after"] = {s: {k: v for k, v in p.items()} for s, p in state["positions"].items()}
    if not dry_run:
        save_state(state)
    journal.write(day, "leaps", rec)
    return rec
