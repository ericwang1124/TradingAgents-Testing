"""Live signal detection and 0DTE put execution on Alpaca paper.

The signal logic is exactly ``signals.find_signal``: each minute the completed bars of today
(IEX real-time feed) are joined to the SIP history, a placeholder bar priced at the last trade is
appended for the minute in progress, and a signal counts only if its entry bar is that
placeholder — i.e. the reversal bar just closed. Exits follow the underlying, like the backtest:
stop above the rally high, target at 1R, flat at 10:45.
"""

from __future__ import annotations

import math
import time as _time
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..config import StrategyParams
from ..data import NY, load_alpaca_minutes
from ..levels import DayContext, build_day_contexts
from ..signals import Signal, find_signal
from . import journal
from .alpaca_trading import AlpacaClient
from .settings import (ENTRY_LIMIT_SLIPPAGE, EST_PUT_DELTA, HISTORY_DAYS, LIVE_PARAMS, MAX_CONTRACTS,
                       MAX_PREMIUM_FRACTION, POLL_SECONDS, RISK_PER_TRADE, SYMBOL)

ORDER_PREFIX = "orv"


def now_ny() -> pd.Timestamp:
    return pd.Timestamp.now(tz=NY)


def today_context(history: pd.DataFrame, today_bars: pd.DataFrame, day: date,
                  params: StrategyParams = LIVE_PARAMS) -> Optional[DayContext]:
    combined = pd.concat([history, today_bars]).sort_index()
    combined = combined[~combined.index.duplicated(keep="last")]
    ctxs = build_day_contexts(combined, params, min_session_minutes=-1)
    return ctxs[-1] if ctxs and ctxs[-1].day.date() == day else None


def detect_now(ctx: DayContext, price: float, minute_start: pd.Timestamp,
               params: StrategyParams = LIVE_PARAMS) -> Optional[Signal]:
    """Signal whose entry is the minute now starting (reversal bar = last completed bar)."""
    placeholder = pd.DataFrame({"open": price, "high": price, "low": price, "close": price,
                                "volume": 0.0, "rel_vol": np.nan}, index=pd.DatetimeIndex([minute_start]))
    live = replace(ctx, rth=pd.concat([ctx.rth, placeholder]))
    sig = find_signal(live, params)
    return sig if sig is not None and sig.entry_idx == len(live.rth) - 1 else None


def size_contracts(equity: float, risk_points: float, bid: float, ask: float, size_multiplier: float) -> int:
    per_contract_loss = EST_PUT_DELTA * risk_points * 100 + max(ask - bid, 0.0) * 100
    by_risk = equity * RISK_PER_TRADE * size_multiplier / max(per_contract_loss, 1e-9)
    by_premium = equity * MAX_PREMIUM_FRACTION / max(ask * 100, 1e-9)
    return int(max(0, min(math.floor(by_risk), math.floor(by_premium), MAX_CONTRACTS)))


def pick_put(client: AlpacaClient, day: date, price: float) -> Optional[dict]:
    contracts = client.put_contracts(SYMBOL, day, price - 5, price + 1)
    if not contracts:
        return None
    at_or_below = [c for c in contracts if float(c["strike_price"]) <= price]
    pool = at_or_below or contracts
    return max(pool, key=lambda c: float(c["strike_price"])) if at_or_below else \
        min(pool, key=lambda c: abs(float(c["strike_price"]) - price))


def _sleep_until(ts: pd.Timestamp) -> None:
    while True:
        remaining = (ts - now_ny()).total_seconds()
        if remaining <= 0:
            return
        _time.sleep(min(remaining, 30))


def run(day: date, client: Optional[AlpacaClient] = None, dry_run: bool = False) -> Dict[str, Any]:
    client = client or AlpacaClient()
    briefing, decision = journal.read(day, "briefing"), journal.read(day, "decision")
    record: Dict[str, Any] = {"date": day.isoformat(), "dry_run": dry_run, "traded": False, "events": []}

    def log(msg: str, **extra) -> None:
        entry = {"time": now_ny().strftime("%H:%M:%S"), "msg": msg, **extra}
        record["events"].append(entry)
        print(f"[{entry['time']}] {msg} {extra if extra else ''}", flush=True)
        journal.write(day, "execution", record)

    if not briefing or not decision:
        log("missing briefing or decision; not trading")
        return record
    if briefing.get("hard_no_go") or decision.get("decision") != "GO":
        log("decision is not GO; nothing to do", decision=decision.get("decision"))
        return record

    p = LIVE_PARAMS
    history = load_alpaca_minutes(SYMBOL, day - timedelta(days=HISTORY_DAYS), day - timedelta(days=1), verbose=False)
    first_check = pd.Timestamp(datetime.combine(day, p.entry_start), tz=NY) + pd.Timedelta(minutes=1, seconds=3)
    log("waiting for the entry window", first_check=first_check.strftime("%H:%M:%S"))
    _sleep_until(first_check)

    sig = None
    while True:
        minute_start = now_ny().floor("min")
        if minute_start.time() > p.entry_end:
            log("entry window closed without a signal")
            return record
        bars = client.bars_today(SYMBOL, day)
        bars = bars[bars.index < minute_start]
        ctx = today_context(history, bars, day)
        price = client.latest_trade_price(SYMBOL)
        if ctx is not None:
            sig = detect_now(ctx, price, minute_start)
            if sig is not None:
                break
        _sleep_until(minute_start + pd.Timedelta(minutes=1, seconds=3))

    risk_pts = sig.stop - price
    target = price - risk_pts * p.take_profits[0][0]
    record["signal"] = {"signal_bar": ctx.rth.index[sig.signal_idx].strftime("%H:%M"), "ref_price": price,
                        "stop": round(sig.stop, 2), "target": round(target, 2), "risk_points": round(risk_pts, 3),
                        "rally_low": sig.rally_low, "rally_high": sig.rally_high, "gap_pct": round(ctx.gap_pct * 100, 3)}
    log("signal", **record["signal"])

    contract = pick_put(client, day, price)
    if contract is None:
        log("no 0DTE put contract found")
        return record
    quote = client.option_quote(contract["symbol"])
    equity = float(client.account()["equity"])
    qty = size_contracts(equity, risk_pts, quote["bid"], quote["ask"], float(decision.get("size", 1.0)))
    record["order_plan"] = {"contract": contract["symbol"], "strike": contract["strike_price"], "qty": qty, **quote}
    log("order plan", **record["order_plan"])
    if qty == 0 or quote["ask"] <= 0:
        log("size is zero or no ask; not trading")
        return record
    if dry_run:
        log("dry run: no order sent")
        return record

    entry = client.submit_order(contract["symbol"], qty, "buy", "limit", limit_price=quote["ask"] + ENTRY_LIMIT_SLIPPAGE,
                                client_order_id=f"{ORDER_PREFIX}-{day:%Y%m%d}-entry")
    entry = client.wait_filled(entry["id"], timeout_s=30)
    if entry["status"] != "filled":
        client.cancel_order(entry["id"])
        log("entry not filled within 30s; cancelled", status=entry["status"])
        return record
    record["traded"] = True
    record["entry_fill"] = {"price": float(entry["filled_avg_price"]), "qty": int(float(entry["filled_qty"])),
                            "time": entry["filled_at"], "underlying": price}
    log("entry filled", **record["entry_fill"])

    exit_at = pd.Timestamp(datetime.combine(day, p.time_exit), tz=NY)
    reason, under = None, price
    lo, hi = price, price
    while reason is None:
        _time.sleep(POLL_SECONDS)
        under = client.latest_trade_price(SYMBOL)
        lo, hi = min(lo, under), max(hi, under)
        if under >= sig.stop:
            reason = "stop"
        elif under <= target:
            reason = "target"
        elif now_ny() >= exit_at:
            reason = "time"
    exit_order = client.submit_order(contract["symbol"], record["entry_fill"]["qty"], "sell", "market",
                                     client_order_id=f"{ORDER_PREFIX}-{day:%Y%m%d}-exit")
    exit_order = client.wait_filled(exit_order["id"], timeout_s=60)
    fill = float(exit_order.get("filled_avg_price") or 0.0)
    record["exit_fill"] = {"reason": reason, "price": fill, "time": exit_order.get("filled_at"),
                           "status": exit_order["status"], "underlying": under,
                           "underlying_low": lo, "underlying_high": hi}
    record["pnl_usd"] = round((fill - record["entry_fill"]["price"]) * record["entry_fill"]["qty"] * 100, 2)
    record["underlying_R"] = round((price - under) / risk_pts, 3)
    log("exit", **record["exit_fill"], pnl_usd=record["pnl_usd"], underlying_R=record["underlying_R"])
    return record


def flatten_strategy_positions(day: date, client: Optional[AlpacaClient] = None) -> Dict[str, Any]:
    """Safety net: close this strategy's 0DTE SPY puts for ``day`` and cancel its open orders only."""
    client = client or AlpacaClient()
    tag = f"{SYMBOL}{day:%y%m%d}P"
    closed = [pos["symbol"] for pos in client.positions() if pos["symbol"].startswith(tag)]
    for sym in closed:
        client.close_position(sym)
    for o in client.orders(after=datetime.combine(day, time(0, 0)), status="open"):
        if (o.get("client_order_id") or "").startswith(ORDER_PREFIX):
            client.cancel_order(o["id"])
    return {"closed": closed}
