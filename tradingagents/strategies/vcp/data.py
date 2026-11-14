"""US stock daily bars from Alpaca (SIP, split- and dividend-adjusted), delisted names included.

    python -m tradingagents.strategies.vcp.data

1. Assets: every active and inactive us_equity on NYSE, NASDAQ and AMEX, minus funds, notes,
   warrants, rights, units and preferreds (by name).
2. Monthly bars for all of them; keep a symbol only if in some month it closed >= $10 with average
   daily dollar volume >= $15M (a loose pre-filter: the backtest applies its own daily rule).
3. Daily bars 2016-01 onward for the kept symbols, saved as date x symbol matrices.
A ticker that goes quiet for more than 30 sessions and comes back is usually a different company
reusing the symbol (e.g. BBBY), so each such piece is kept as its own column ("BBBY~1", "BBBY~2").
Requires ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY (or proxy-injected credentials).
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import requests

from ..opening_reversal.data import default_cache_dir

CACHE = default_cache_dir().parent / "vcp"
START = "2016-01-01T00:00:00Z"
END = "2026-11-14T00:00:00Z"
EXCHANGES = {"NYSE", "NASDAQ", "AMEX"}
NOT_STOCK = re.compile(r"\b(ETF|ETN|ETP|FUND|FUNDS|ISHARES|PROSHARES|DIREXION|SPDR|INVESCO|VANGUARD|WISDOMTREE|"
                       r"GRANITESHARES|GLOBAL X|ULTRA|ULTRASHORT|LEVERAGED|INVERSE|2X|3X|-1X|-2X|-3X|BULL|BEAR|"
                       r"NOTES?|WARRANTS?|RIGHTS?|UNITS?|PREFERRED|PFD|DEBENTURES?|BOND|TERM TRUST|INCOME TRUST|"
                       r"MUNICIPAL|ACQUISITION CORP|ACQUISITION CORPORATION|SPAC)\b", re.I)
PRE_PRICE, PRE_DV = 10.0, 15e6
GAP_SESSIONS = 30


def _headers() -> Dict[str, str]:
    k, s = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
    return {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s} if k and s else {}


def _get(url: str, params: dict, tries: int = 5) -> dict:
    for i in range(tries):
        r = requests.get(url, headers=_headers(), params=params, timeout=120)
        if r.status_code == 429:
            time.sleep(2 + 2 * i)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return {}


def stock_assets() -> pd.DataFrame:
    rows = []
    for status in ("active", "inactive"):
        for a in _get("https://paper-api.alpaca.markets/v2/assets", {"status": status, "asset_class": "us_equity"}):
            if a["exchange"] not in EXCHANGES:
                continue
            name, sym = a.get("name") or "", a["symbol"]
            if NOT_STOCK.search(name) or re.search(r"[^A-Z.]", sym) or re.search(r"\.(P|W|U|R)", sym):
                continue
            rows.append({"symbol": sym, "name": name, "exchange": a["exchange"], "status": status})
    return pd.DataFrame(rows).drop_duplicates("symbol")


def bars(symbols: List[str], timeframe: str, batch: int = 200) -> pd.DataFrame:
    out = []
    for i in range(0, len(symbols), batch):
        syms = symbols[i:i + batch]
        tok = None
        while True:
            p = {"symbols": ",".join(syms), "timeframe": timeframe, "start": START, "end": END, "limit": 10000,
                 "feed": "sip", "adjustment": "all"}
            if tok:
                p["page_token"] = tok
            j = _get("https://data.alpaca.markets/v2/stocks/bars", p)
            for s, bs in (j.get("bars") or {}).items():
                for b in bs:
                    out.append((s, b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]))
            tok = j.get("next_page_token")
            if not tok:
                break
        print(f"{timeframe}: {min(i + batch, len(symbols))}/{len(symbols)} symbols, {len(out):,} bars", flush=True)
    df = pd.DataFrame(out, columns=["symbol", "date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def prefilter(monthly: pd.DataFrame) -> List[str]:
    m = monthly.copy()
    m["dv"] = m["close"] * m["volume"] / 21.0
    ok = m[(m["close"] >= PRE_PRICE) & (m["dv"] >= PRE_DV)]
    return sorted(ok["symbol"].unique())


def to_matrices(daily: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    cal = pd.DatetimeIndex(sorted(daily.loc[daily["symbol"] == "SPY", "date"].unique())) if (daily["symbol"] == "SPY").any() \
        else pd.DatetimeIndex(sorted(daily["date"].unique()))
    pos = pd.Series(np.arange(len(cal)), index=cal)
    pieces = []
    for sym, g in daily.groupby("symbol", sort=False):
        g = g[g["date"].isin(cal)].sort_values("date")
        if g.empty:
            continue
        k = pos[g["date"]].to_numpy()
        breaks = np.where(np.diff(k) > GAP_SESSIONS)[0]
        if len(breaks) == 0:
            pieces.append((sym, g))
        else:
            for n, part in enumerate(np.split(g, breaks + 1), start=1):
                pieces.append((f"{sym}~{n}", part))
    out = {}
    for f in ("open", "high", "low", "close", "volume"):
        out[f] = pd.DataFrame({s: g.set_index("date")[f] for s, g in pieces}).reindex(cal).astype("float32")
    return out


def save(mats: Dict[str, pd.DataFrame]) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    cols = mats["close"].columns.to_numpy(dtype=str)
    np.savez_compressed(CACHE / "daily.npz", dates=mats["close"].index.to_numpy(dtype="datetime64[D]"), symbols=cols,
                        **{f: m.to_numpy() for f, m in mats.items()})


def load() -> Dict[str, pd.DataFrame]:
    z = np.load(CACHE / "daily.npz", allow_pickle=False)
    idx, cols = pd.DatetimeIndex(z["dates"]), list(z["symbols"])
    return {f: pd.DataFrame(z[f], index=idx, columns=cols) for f in ("open", "high", "low", "close", "volume")}


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    assets = stock_assets()
    assets.to_csv(CACHE / "assets.csv", index=False)
    print(f"{len(assets)} stock assets ({(assets['status'] == 'inactive').sum()} inactive)")
    monthly = bars(assets["symbol"].tolist(), "1Month")
    monthly.to_csv(CACHE / "monthly.csv.gz", index=False)
    keep = prefilter(monthly)
    print(f"{len(keep)} symbols pass the liquidity pre-filter")
    daily = bars(sorted(set(keep) | {"SPY"}), "1Day")
    mats = to_matrices(daily)
    save(mats)
    print(f"saved {mats['close'].shape[1]} columns x {mats['close'].shape[0]} sessions to {CACHE}")


if __name__ == "__main__":
    main()
