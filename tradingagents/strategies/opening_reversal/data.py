"""Intraday bar loaders (Alpaca market data with a yfinance fallback) and a monthly disk cache.

All loaders return a DataFrame indexed by tz-aware America/New_York timestamps (bar open time)
with float columns ``open, high, low, close, volume``. Extended-hours bars are kept so that the
pre-market high can be used as a supply level.
"""

from __future__ import annotations

import os
import time as _time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

NY = "America/New_York"
ALPACA_DATA_URL = "https://data.alpaca.markets/v2/stocks/{symbol}/bars"
COLUMNS = ["open", "high", "low", "close", "volume"]


def default_cache_dir() -> Path:
    here = Path(__file__).resolve().parents[2]  # tradingagents/
    return here / "dataflows" / "data_cache" / "intraday"


class AlpacaError(RuntimeError):
    pass


class AlpacaBarsClient:
    """Minimal client for ``GET /v2/stocks/{symbol}/bars``.

    Credentials: if ``ALPACA_API_KEY_ID`` / ``ALPACA_API_SECRET_KEY`` are set they are sent as
    headers. Otherwise no auth header is sent, which works when an HTTPS proxy injects the
    credential (as in the hosted dev environment).
    """

    def __init__(self, feed: str = "sip", adjustment: str = "all", session: Optional[requests.Session] = None):
        self.feed = feed
        # "all" = split + dividend adjusted. Raw prices would show a fake ~0.3-0.4% gap down on
        # every SPY ex-dividend date.
        self.adjustment = adjustment
        self.session = session or requests.Session()
        key_id = os.getenv("ALPACA_API_KEY_ID")
        secret = os.getenv("ALPACA_API_SECRET_KEY")
        if key_id and secret:
            self.session.headers.update({"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret})

    def fetch(self, symbol: str, start: datetime, end: datetime, timeframe: str = "1Min") -> pd.DataFrame:
        params = {
            "timeframe": timeframe,
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": 10000,
            "adjustment": self.adjustment,
            "feed": self.feed,
            "sort": "asc",
        }
        rows = []
        url = ALPACA_DATA_URL.format(symbol=symbol.upper())
        while True:
            resp = self._get(url, params)
            payload = resp.json()
            rows.extend(payload.get("bars") or [])
            token = payload.get("next_page_token")
            if not token:
                break
            params["page_token"] = token
        return _alpaca_rows_to_frame(rows)

    def _get(self, url: str, params: dict) -> requests.Response:
        for attempt in range(6):
            resp = self.session.get(url, params=params, timeout=60)
            if resp.status_code == 429 or resp.status_code >= 500:
                _time.sleep(2 ** attempt)
                continue
            if resp.status_code != 200:
                raise AlpacaError(f"Alpaca {resp.status_code}: {resp.text[:300]}")
            return resp
        raise AlpacaError(f"Alpaca request kept failing: {resp.status_code} {resp.text[:300]}")


def _alpaca_rows_to_frame(rows: list) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=COLUMNS, index=pd.DatetimeIndex([], tz=NY))
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["t"], utc=True).dt.tz_convert(NY)
    df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
    df = df[COLUMNS].astype(float)
    df.index.name = "timestamp"
    return df[~df.index.duplicated(keep="last")].sort_index()


def _month_starts(start: date, end: date):
    cur = date(start.year, start.month, 1)
    while cur <= end:
        nxt = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
        yield cur, nxt
        cur = nxt


def load_alpaca_minutes(
    symbol: str,
    start: date,
    end: date,
    cache_dir: Optional[Path] = None,
    client: Optional[AlpacaBarsClient] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Load 1-minute bars [start, end] month by month, caching completed months as csv.gz."""
    client = client or AlpacaBarsClient()
    cache_dir = Path(cache_dir or default_cache_dir())
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Free plans may not query SIP data from the last 15 minutes.
    latest_allowed = datetime.utcnow() - timedelta(minutes=20)
    frames = []
    for m_start, m_next in _month_starts(start, end):
        tag = f"alpaca_{symbol.upper()}_1Min_{client.feed}_{client.adjustment}_{m_start:%Y-%m}.csv.gz"
        path = cache_dir / tag
        month_complete = datetime.combine(m_next, datetime.min.time()) + timedelta(days=1) < latest_allowed
        if path.exists():
            df = pd.read_csv(path, index_col=0)
            df.index = pd.to_datetime(df.index, utc=True).tz_convert(NY)
        else:
            fetch_end = min(datetime.combine(m_next, datetime.min.time()) + timedelta(hours=5), latest_allowed)
            fetch_start = datetime.combine(m_start, datetime.min.time())
            if fetch_start >= fetch_end:
                continue
            if verbose:
                print(f"  fetching {symbol} {m_start:%Y-%m} from Alpaca ({client.feed})...", flush=True)
            df = client.fetch(symbol, fetch_start, fetch_end)
            df = df[(df.index >= pd.Timestamp(m_start, tz=NY)) & (df.index < pd.Timestamp(m_next, tz=NY))]
            if month_complete and not df.empty:
                df.to_csv(path, compression="gzip")
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    out = pd.concat(frames).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    lo = pd.Timestamp(start, tz=NY)
    hi = pd.Timestamp(end + timedelta(days=1), tz=NY)
    return out[(out.index >= lo) & (out.index < hi)]


def resample_bars(bars: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Aggregate 1-minute bars to N-minute bars (bins anchored on the clock, so 9:30 starts a bar)."""
    if minutes == 1:
        return bars
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    out = bars.resample(f"{minutes}min", label="left", closed="left").agg(agg)
    return out.dropna(subset=["open"])


def load_yfinance_bars(symbol: str, interval: str = "5m") -> pd.DataFrame:
    """Recent intraday bars from Yahoo (5m: ~60 days, 1m: ~30 days). For smoke tests only."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    if interval == "1m":
        frames = []
        end = datetime.utcnow()
        for _ in range(4):  # Yahoo serves 1m data in <=7-day windows, last ~30 days only
            start = end - timedelta(days=7)
            frames.append(ticker.history(start=start, end=end, interval="1m", prepost=True, auto_adjust=False))
            end = start
        raw = pd.concat(frames)
    else:
        raw = ticker.history(period="60d", interval=interval, prepost=True, auto_adjust=False)
    if raw.empty:
        raise RuntimeError(f"yfinance returned no {interval} data for {symbol}")
    df = raw.rename(columns=str.lower)[COLUMNS].astype(float)
    df.index = df.index.tz_convert(NY)
    df.index.name = "timestamp"
    return df[~df.index.duplicated(keep="last")].sort_index()
