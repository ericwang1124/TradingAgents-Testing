"""US stock daily bars from Alpaca (SIP), delisted names included, with unadjusted prices for filters.

    python -m tradingagents.strategies.vcp.data            # everything (resumable)
    python -m tradingagents.strategies.vcp.data --discover # only steps 1-3, then list the unlisted finds

1. Listed: every active and inactive us_equity on NYSE, NASDAQ and AMEX in Alpaca's asset list, minus
   funds, notes, warrants, rights, units and preferreds (by name).
2. Unlisted: Alpaca's asset list lacks most stocks delisted before 2018 or after 2022 (SIVB, TWTR, ATVI,
   VMW ... are absent although their bars exist), so every 1-4 letter ticker that is not in the list
   is queried too. SIP bars only exist for exchange-listed securities; the finds have no name or
   exchange, so known funds and notes among them are dropped by hand (UNLISTED_NOT_STOCK).
3. Monthly bars with unadjusted prices for all of them; keep a symbol if in some month it closed
   >= $10 with average daily dollar volume >= $15M (a loose pre-filter; backtests apply daily rules).
4. Daily split- and dividend-adjusted bars 2016-01 onward for the kept symbols, as date x symbol
   matrices, plus "rawclose": the price actually traded (adjusted close x that month's raw/adjusted
   ratio). Price filters must use rawclose: adjusted prices of later split winners are far too low
   (NVDA below $6 before 2020) and those of reverse-split penny stocks far too high.
A ticker that goes quiet for more than 30 sessions and comes back is usually a different company
reusing the symbol (e.g. BBBY), so each such piece is kept as its own column ("BBBY~1", "BBBY~2").
Requires ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY (or proxy-injected credentials).
"""

from __future__ import annotations

import argparse
import itertools
import os
import re
import string
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Set

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
THREADS = 4
# Unlisted finds that are not operating companies, picked out by hand from the --discover list
# (1,135 tickers after de-duplication). Tickers I could not place were left in.
UNLISTED_NOT_STOCK: Set[str] = set("""
TVIX DGAZ UGAZ UWTI XIV VXXB DWTI FNGA FNGB AMJ MJX FBGX ZIV VIIX DSLV XXXX FIHD
SPLG RSX IBTE IBTD IBTF IBDP IBDQ IBDO BSCO BSCP BSCN BSCM BSJP CSJ CIU CLY SCPB TLO ITE ITR SLY JKE HEWG
RYT RYE RHS POTX PHB PIN PLW IPE GBF GWL CN NUSI MOON BIGZ CETH ETQ GLOV OKLS PLDR PCRB IGTR IEQ ISDX CLTL CRED
ZBZX ZVV ZZK CBX IGZ
BDXB AQNU PCGU DTP DCUB DCUC TSNU EXCU SWT BKHU
IPOF IPOD GHVI GGPI TPGY ACTC AACQ PDAC FMCI GMHI DPHC SSPK SNPR RMG TRNE GRSH AONE RAAC FCAC NBAC PCPL FTCV
TBA ACAM HZON DCRB ACTT ZING GRAF HCVI VCVC FPAC APGB CND TSIA IVAN
""".split())   # ETNs and leveraged notes; ETFs and funds; exchange test symbols; equity units and preferreds; SPAC shells


def _headers() -> Dict[str, str]:
    k, s = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
    return {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s} if k and s else {}


def _get(url: str, params: dict, tries: int = 12) -> dict:
    r = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=_headers(), params=params, timeout=120)
        except requests.RequestException:
            time.sleep(3 + 2 * i)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 + 2 * i)
            continue
        r.raise_for_status()
        return r.json()
    if r is not None:
        r.raise_for_status()
    raise RuntimeError(f"no response from {url}")


def all_asset_symbols() -> Set[str]:
    out = set()
    for status in ("active", "inactive"):
        out |= {a["symbol"] for a in _get("https://paper-api.alpaca.markets/v2/assets", {"status": status, "asset_class": "us_equity"})}
    return out


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


def _bars_batch(syms: List[str], timeframe: str, adjustment: str) -> list:
    out, tok = [], None
    while True:
        p = {"symbols": ",".join(syms), "timeframe": timeframe, "start": START, "end": END, "limit": 10000,
             "feed": "sip", "adjustment": adjustment}
        if tok:
            p["page_token"] = tok
        j = _get("https://data.alpaca.markets/v2/stocks/bars", p)
        for s, bs in (j.get("bars") or {}).items():
            out.extend((s, b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bs)
        tok = j.get("next_page_token")
        if not tok:
            return out


def bars(symbols: List[str], timeframe: str, batch: int = 200, adjustment: str = "all", log_every: int = 1) -> pd.DataFrame:
    batches = [symbols[i:i + batch] for i in range(0, len(symbols), batch)]
    out, done = [], 0
    with ThreadPoolExecutor(THREADS) as ex:
        for rows in ex.map(lambda s: _bars_batch(s, timeframe, adjustment), batches):
            out.extend(rows)
            done += 1
            if done % log_every == 0 or done == len(batches):
                print(f"{timeframe}/{adjustment}: {min(done * batch, len(symbols))}/{len(symbols)} symbols, {len(out):,} bars", flush=True)
    df = pd.DataFrame(out, columns=["symbol", "date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def _cached(path: Path, make) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"], keep_default_na=False, na_values=[""])
    df = make()
    df.to_csv(path, index=False)
    return df


def prefilter(monthly_raw: pd.DataFrame) -> List[str]:
    """Symbols with some month closing >= $10 (unadjusted) on >= $15M average daily dollar volume."""
    dv = monthly_raw["close"] * monthly_raw["volume"] / 21.0
    return sorted(monthly_raw.loc[(monthly_raw["close"] >= PRE_PRICE) & (dv >= PRE_DV), "symbol"].unique())


def duplicate_symbols(monthly: pd.DataFrame, min_months: int = 3) -> Set[str]:
    """Alpaca serves a renamed company's whole history under its current ticker and the old-ticker
    years again under the old one (XYZ holds SQ's years, ELV holds ANTM's). Two symbols with the same
    unadjusted close and volume in at least ``min_months`` months are one security: the shorter history goes."""
    n = monthly.groupby("symbol").size()
    m = monthly.merge(monthly, on=["date", "close", "volume"], suffixes=("_a", "_b"))
    m = m[m["symbol_a"] < m["symbol_b"]]
    pairs = m.groupby(["symbol_a", "symbol_b"]).size()
    return {a if (n[a], a) < (n[b], b) else b for (a, b), k in pairs.items() if k >= min_months}


def brute_force_symbols(known: Set[str], max_len: int = 4) -> List[str]:
    out = []
    for n in range(1, max_len + 1):
        out += ["".join(c) for c in itertools.product(string.ascii_uppercase, repeat=n)]
    return [s for s in out if s not in known]


def monthly_raw_all() -> Dict[str, pd.DataFrame]:
    CACHE.mkdir(parents=True, exist_ok=True)
    if (CACHE / "assets.csv").exists():
        assets = pd.read_csv(CACHE / "assets.csv", keep_default_na=False)
    else:
        assets = stock_assets()
        assets.to_csv(CACHE / "assets.csv", index=False)
    listed = _cached(CACHE / "monthly_raw_listed.csv.gz",
                     lambda: bars(assets["symbol"].tolist(), "1Month", adjustment="raw", log_every=5))
    unlisted = _cached(CACHE / "monthly_raw_unlisted.csv.gz",
                       lambda: bars(brute_force_symbols(all_asset_symbols()), "1Month", batch=1000, adjustment="raw", log_every=25))
    return {"listed": listed, "unlisted": unlisted}


def daily_bars_checkpointed(symbols: List[str], batch: int = 200) -> pd.DataFrame:
    """Daily adjusted bars in part files; a rerun only fetches symbols that no part holds yet."""
    parts = CACHE / "daily_parts"
    parts.mkdir(parents=True, exist_ok=True)
    asked_path = parts / "asked.txt"
    frames = [pd.read_csv(f, parse_dates=["date"], keep_default_na=False, na_values=[""]) for f in sorted(parts.glob("*.csv.gz"))]
    have = set().union(*(set(f["symbol"].unique()) for f in frames)) if frames else set()
    if asked_path.exists():
        have |= set(asked_path.read_text().split())
    todo = [s for s in symbols if s not in have]
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        df = bars(chunk, "1Day", batch=max(len(chunk) // THREADS, 1) + 1)
        df.to_csv(parts / f"more_{int(time.time())}_{i:05d}.csv.gz", index=False)
        with asked_path.open("a") as fh:
            fh.write("\n".join(chunk) + "\n")
        frames.append(df)
        print(f"1Day parts: {min(i + batch, len(todo))}/{len(todo)} new symbols on disk", flush=True)
    daily = pd.concat(frames, ignore_index=True)
    return daily[daily["symbol"].isin(set(symbols))]


def to_matrices(daily: pd.DataFrame, monthly_raw: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
    """Date x column matrices. SPY (if present) only supplies the session calendar and is dropped.
    With ``monthly_raw`` a "rawclose" matrix (unadjusted price) is added."""
    has_spy = (daily["symbol"] == "SPY").any()
    cal = pd.DatetimeIndex(sorted(daily.loc[daily["symbol"] == "SPY", "date"].unique())) if has_spy \
        else pd.DatetimeIndex(sorted(daily["date"].unique()))
    pos = pd.Series(np.arange(len(cal)), index=cal)
    d = daily[daily["date"].isin(cal) & (daily["symbol"] != "SPY")].sort_values(["symbol", "date"]).reset_index(drop=True)
    k = pos.reindex(d["date"]).to_numpy()
    same_sym = d["symbol"].eq(d["symbol"].shift()).to_numpy()
    gap = (np.diff(k, prepend=k[0]) > GAP_SESSIONS) & same_sym
    piece_no = pd.Series(gap.astype(int)).groupby(d["symbol"]).cumsum() + 1
    n_pieces = piece_no.groupby(d["symbol"]).transform("max")
    d["col"] = np.where(n_pieces > 1, d["symbol"] + "~" + piece_no.astype(str), d["symbol"])
    out = {f: d.pivot(index="date", columns="col", values=f).reindex(cal).astype("float32")
           for f in ("open", "high", "low", "close", "volume")}
    if monthly_raw is not None:
        C = out["close"].astype("float64")
        month = cal.to_period("M")
        adj_last = C.groupby(month).last()                                  # month x column, adjusted month-end close
        raw = monthly_raw.assign(month=monthly_raw["date"].dt.to_period("M")).pivot_table(
            index="month", columns="symbol", values="close", aggfunc="last")
        sym_of = pd.Index([c.split("~")[0] for c in C.columns])
        raw_cols = raw.reindex(index=adj_last.index, columns=sym_of)
        raw_cols.columns = C.columns
        ratio = (raw_cols / adj_last).replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(1.0)
        scale = ratio.reindex(month).set_axis(cal)
        out["rawclose"] = (C * scale).astype("float32")
    return out


def save(mats: Dict[str, pd.DataFrame]) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / "daily.npz", dates=mats["close"].index.to_numpy(dtype="datetime64[D]"),
                        symbols=mats["close"].columns.to_numpy(dtype=str), **{f: m.to_numpy() for f, m in mats.items()})


def load() -> Dict[str, pd.DataFrame]:
    z = np.load(CACHE / "daily.npz", allow_pickle=False)
    idx, cols = pd.DatetimeIndex(z["dates"]), list(z["symbols"])
    return {f: pd.DataFrame(z[f], index=idx, columns=cols) for f in z.files if f not in ("dates", "symbols")}


def unlisted_candidates(unlisted: pd.DataFrame) -> pd.DataFrame:
    keep = prefilter(unlisted)
    m = unlisted[unlisted["symbol"].isin(keep)].copy()
    m["dv"] = m["close"] * m["volume"] / 21.0
    g = m.groupby("symbol")
    return pd.DataFrame({"first": g["date"].min().dt.strftime("%Y-%m"), "last": g["date"].max().dt.strftime("%Y-%m"),
                         "last_close": g["close"].last(), "max_dv_musd": (g["dv"].max() / 1e6).round(0)}).sort_values("max_dv_musd", ascending=False)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--discover", action="store_true")
    args = ap.parse_args(argv)
    m = monthly_raw_all()
    cand = unlisted_candidates(m["unlisted"])
    print(f"listed: {m['listed']['symbol'].nunique()} symbols with bars; unlisted finds: {m['unlisted']['symbol'].nunique()} "
          f"({len(cand)} pass the liquidity pre-filter)")
    if args.discover:
        cand.to_csv(CACHE / "unlisted_candidates.csv")
        with pd.option_context("display.max_rows", 2000, "display.width", 200):
            print(cand)
        return
    keep = set(prefilter(m["listed"])) | set(cand.index)
    both = pd.concat([m["listed"], m["unlisted"]], ignore_index=True)
    dups = duplicate_symbols(both[both["symbol"].isin(keep)])
    keep = sorted(keep - dups - UNLISTED_NOT_STOCK)
    print(f"{len(dups)} duplicate histories and {len(UNLISTED_NOT_STOCK & set(cand.index))} non-stocks dropped; {len(keep)} symbols kept "
          f"({len(set(keep) & set(cand.index))} of them missing from Alpaca's asset list)")
    daily = daily_bars_checkpointed(sorted(set(keep) | {"SPY"}))
    mats = to_matrices(daily, both)
    save(mats)
    print(f"saved {mats['close'].shape[1]} columns x {mats['close'].shape[0]} sessions to {CACHE}")


if __name__ == "__main__":
    main()
