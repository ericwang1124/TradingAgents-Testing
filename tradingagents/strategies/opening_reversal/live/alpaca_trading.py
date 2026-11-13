"""Small Alpaca client for the *paper* trading API plus the live market-data calls the executor needs.

Credentials: ``ALPACA_API_KEY_ID`` / ``ALPACA_API_SECRET_KEY`` if set, otherwise none (the hosted
environment's proxy injects them). Refuses any non-paper trading URL unless ``allow_live=True``.
"""

from __future__ import annotations

import os
import time as _time
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd
import requests

from ..data import NY, _alpaca_rows_to_frame

PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"


class AlpacaAPIError(RuntimeError):
    pass


class AlpacaClient:
    def __init__(self, trading_url: str = PAPER_URL, allow_live: bool = False):
        if "paper-api" not in trading_url and not allow_live:
            raise ValueError("Refusing to use a live trading endpoint; pass allow_live=True explicitly.")
        self.trading_url = trading_url.rstrip("/")
        self.session = requests.Session()
        key_id, secret = os.getenv("ALPACA_API_KEY_ID"), os.getenv("ALPACA_API_SECRET_KEY")
        if key_id and secret:
            self.session.headers.update({"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret})

    # --- plumbing ----------------------------------------------------------------------------
    def _request(self, method: str, url: str, **kwargs):
        for attempt in range(5):
            resp = self.session.request(method, url, timeout=30, **kwargs)
            if resp.status_code == 429 or resp.status_code >= 500:
                _time.sleep(1.5 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                raise AlpacaAPIError(f"{method} {url} -> {resp.status_code}: {resp.text[:400]}")
            return resp.json() if resp.content else None
        raise AlpacaAPIError(f"{method} {url} kept failing ({resp.status_code})")

    def _trade(self, method: str, path: str, **kwargs):
        return self._request(method, f"{self.trading_url}{path}", **kwargs)

    def _data(self, path: str, **params):
        return self._request("GET", f"{DATA_URL}{path}", params=params)

    # --- account / clock -----------------------------------------------------------------------
    def account(self) -> dict:
        return self._trade("GET", "/v2/account")

    def clock(self) -> dict:
        return self._trade("GET", "/v2/clock")

    def calendar(self, start: date, end: date) -> List[dict]:
        return self._trade("GET", "/v2/calendar", params={"start": start.isoformat(), "end": end.isoformat()})

    # --- market data -----------------------------------------------------------------------------
    def bars_today(self, symbol: str, day: date, feed: str = "iex") -> pd.DataFrame:
        """1-minute bars from 04:00 ET of ``day`` until now (IEX is the real-time free feed)."""
        start = pd.Timestamp(datetime.combine(day, datetime.min.time()), tz=NY) + pd.Timedelta(hours=4)
        if pd.Timestamp.now(tz=NY) <= start:  # pre-market has not started yet
            return _alpaca_rows_to_frame([])
        rows, token = [], None
        while True:
            params = {"timeframe": "1Min", "start": start.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "limit": 10000, "feed": feed, "adjustment": "raw", "sort": "asc"}
            if token:
                params["page_token"] = token
            payload = self._data(f"/v2/stocks/{symbol}/bars", **params)
            rows.extend(payload.get("bars") or [])
            token = payload.get("next_page_token")
            if not token:
                break
        return _alpaca_rows_to_frame(rows)

    def latest_trade_price(self, symbol: str, feed: str = "iex") -> float:
        return float(self._data(f"/v2/stocks/{symbol}/trades/latest", feed=feed)["trade"]["p"])

    def news(self, symbols: str, start: datetime, limit: int = 50) -> List[dict]:
        payload = self._data("/v1beta1/news", symbols=symbols, start=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                             limit=limit, sort="desc")
        return payload.get("news") or []

    # --- options -----------------------------------------------------------------------------
    def put_contracts(self, underlying: str, expiration: date, strike_lo: float, strike_hi: float) -> List[dict]:
        payload = self._trade("GET", "/v2/options/contracts", params={
            "underlying_symbols": underlying, "expiration_date": expiration.isoformat(), "type": "put",
            "strike_price_gte": f"{strike_lo:.2f}", "strike_price_lte": f"{strike_hi:.2f}", "limit": 100})
        return [c for c in payload.get("option_contracts", []) if c.get("tradable")]

    def option_quote(self, symbol: str) -> Dict[str, float]:
        snap = self._data("/v1beta1/options/snapshots", symbols=symbol, feed="indicative")
        q = (snap.get("snapshots") or {}).get(symbol, {}).get("latestQuote") or {}
        return {"bid": float(q.get("bp") or 0.0), "ask": float(q.get("ap") or 0.0)}

    # --- orders / positions --------------------------------------------------------------------
    def submit_order(self, symbol: str, qty: int, side: str, order_type: str = "market",
                     limit_price: Optional[float] = None, client_order_id: Optional[str] = None) -> dict:
        body = {"symbol": symbol, "qty": str(qty), "side": side, "type": order_type, "time_in_force": "day"}
        if limit_price is not None:
            body["limit_price"] = f"{limit_price:.2f}"
        if client_order_id:
            body["client_order_id"] = client_order_id
        return self._trade("POST", "/v2/orders", json=body)

    def get_order(self, order_id: str) -> dict:
        return self._trade("GET", f"/v2/orders/{order_id}")

    def wait_filled(self, order_id: str, timeout_s: float = 60.0) -> dict:
        deadline = _time.time() + timeout_s
        order = self.get_order(order_id)
        while order["status"] not in ("filled", "canceled", "expired", "rejected") and _time.time() < deadline:
            _time.sleep(1.0)
            order = self.get_order(order_id)
        return order

    def cancel_order(self, order_id: str) -> None:
        self._trade("DELETE", f"/v2/orders/{order_id}")

    def positions(self) -> List[dict]:
        return self._trade("GET", "/v2/positions") or []

    def close_position(self, symbol: str) -> Optional[dict]:
        return self._trade("DELETE", f"/v2/positions/{symbol}")

    def close_all(self) -> None:
        self._trade("DELETE", "/v2/orders")
        self._trade("DELETE", "/v2/positions", params={"cancel_orders": "true"})

    def orders(self, after: datetime, status: str = "all") -> List[dict]:
        return self._trade("GET", "/v2/orders", params={
            "status": status, "after": after.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 500, "direction": "asc"}) or []
