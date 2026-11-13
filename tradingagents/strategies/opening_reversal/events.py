"""Scheduled-event calendar for each session — everything here is known before the open.

Sources
  * FOMC statement days: federalreserve.gov (current calendar page + 2019/2020 historical pages)
  * CPI / jobs-report days: FRED release calendar (FRED only lists 2025 onward)
  * 8:30 ET macro releases (all years): detected from SPY pre-market volume — the 08:30-08:34
    volume burst relative to 08:00-08:29 on the same morning; validated against FRED dates
  * Monthly options expiration: third Friday (previous session if it is a holiday)
  * Mega-cap earnings: Yahoo earnings dates; an after-close report tags the *next* session
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

import numpy as np
import pandas as pd
import requests

from .data import NY, default_cache_dir

FED_PAGES = {
    "current": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
    2019: "https://www.federalreserve.gov/monetarypolicy/fomchistorical2019.htm",
    2020: "https://www.federalreserve.gov/monetarypolicy/fomchistorical2020.htm",
}
# FRED's calendar ignores older ranges and serves roughly the previous year onward; without an
# explicit range it renders a different (weekly) layout, so always pass one.
HISTORICAL_PAGE = "https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"
FRED_CALENDAR ="https://fred.stlouisfed.org/releases/calendar?rid={rid}&vs=2025-01-01&ve={end}-12-31&y=2025"
FRED_RELEASES = {"cpi": 10, "jobs": 50}
MEGACAPS = ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _get(url: str) -> str:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.text


def _month(name: str) -> int:
    return MONTHS[name.strip().lower()[:3]]


def parse_fomc_current(html: str) -> List[date]:
    """Statement day (last day) of each meeting on the current calendar page, all year panels."""
    out = []
    panels = [(m.start(), int(m.group(1))) for m in re.finditer(r"(\d{4}) FOMC Meetings", html)]
    for k, (start, year) in enumerate(panels):
        end = panels[k + 1][0] if k + 1 < len(panels) else len(html)
        block = html[start:end]
        for months, days in re.findall(
                r'fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>.*?fomc-meeting__date[^>]*>([^<]+)<', block, re.S):
            if "notation" in days.lower() or "cancel" in days.lower():
                continue
            nums = [int(x) for x in re.findall(r"\d+", days)]
            if not nums:
                continue
            month_names = months.split("/")
            # "Apr/May 30-1": the statement comes on the second month's day
            m = _month(month_names[-1] if len(month_names) > 1 and nums[-1] < nums[0] else month_names[0])
            out.append(date(year, m, nums[-1]))
    return out


def parse_fomc_historical(html: str) -> List[date]:
    """Meetings from a historical year page, e.g. 'April/May 30-1 Meeting - 2019'."""
    out = []
    for title in re.findall(r"<h5[^>]*>([^<]*Meeting - \d{4})</h5>", html):
        if "cancel" in title.lower():
            continue
        # "January 29-30", "April/May 30-1", "July 31-August 1", "March 15 (unscheduled)"
        m = re.match(r"\s*([A-Za-z]+)(?:/([A-Za-z]+))?\s+(\d+)(?:-(?:([A-Za-z]+)\s+)?(\d+))?\s*(\(unscheduled\))?"
                     r"\s*Meeting - (\d{4})", title)
        if not m:
            continue
        m1, m_slash, d1, m2, d2, unscheduled, year = m.groups()
        year, first = int(year), int(d1)
        last = int(d2) if d2 else first
        if m2:
            mon = _month(m2)
        elif m_slash and last < first:
            mon = _month(m_slash)
        else:
            mon = _month(m1)
        day = date(year, mon, last)
        if unscheduled:
            # The 2 Mar 2020 call was announced on 3 Mar; the Sunday 15 Mar 2020 cut hit Monday's open.
            day = day + timedelta(days=1)
        out.append(day)
    return out


def load_fomc_days(cache_dir: Optional[Path] = None, refresh: bool = False) -> List[date]:
    path = Path(cache_dir or default_cache_dir()) / "fomc_days.csv"
    if path.exists() and not refresh:
        return [d.date() for d in pd.to_datetime(pd.read_csv(path)["date"])]
    days = set(parse_fomc_current(_get(FED_PAGES["current"])))
    for year in range(2007, 2021):  # historical pages; the current page covers the last ~5 years
        days |= set(parse_fomc_historical(_get(FED_PAGES.get(year, HISTORICAL_PAGE.format(year=year)))))
    out = sorted(days)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"date": out}).to_csv(path, index=False)
    return out


def parse_fred_calendar(html: str) -> List[date]:
    found = re.findall(r"font-weight: bold;\">\w+day (\w+ \d+, \d{4})</span>", html)
    return sorted({datetime.strptime(s, "%B %d, %Y").date() for s in found})


def load_fred_release_days(name: str, cache_dir: Optional[Path] = None, refresh: bool = False) -> List[date]:
    path = Path(cache_dir or default_cache_dir()) / f"fred_{name}_days.csv"
    if path.exists() and not refresh:
        return [d.date() for d in pd.to_datetime(pd.read_csv(path)["date"])]
    out = parse_fred_calendar(_get(FRED_CALENDAR.format(rid=FRED_RELEASES[name], end=date.today().year + 1)))
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"date": out}).to_csv(path, index=False)
    return out


def opex_days(sessions: Sequence[date]) -> Set[date]:
    """Third Friday of each month, or the previous session when that Friday is a holiday."""
    sess = sorted(sessions)
    out = set()
    for y, m in sorted({(d.year, d.month) for d in sess}):
        first = date(y, m, 1)
        third_friday = first + timedelta(days=(4 - first.weekday()) % 7 + 14)
        prior = [d for d in sess if d <= third_friday and d.month == m]
        if prior:
            out.add(prior[-1])
    return out


def load_earnings_sessions(sessions: Sequence[date], tickers: Iterable[str] = MEGACAPS,
                           cache_dir: Optional[Path] = None, refresh: bool = False) -> Dict[date, List[str]]:
    """Session whose open first reflects each mega-cap earnings report."""
    path = Path(cache_dir or default_cache_dir()) / "megacap_earnings.csv"
    if path.exists() and not refresh:
        raw = pd.read_csv(path)
    else:
        import yfinance as yf

        rows = []
        for t in tickers:
            e = yf.Ticker(t).get_earnings_dates(limit=60)
            for ts in e.index:
                ts = pd.Timestamp(ts).tz_convert(NY)
                rows.append({"ticker": t, "timestamp": ts.isoformat()})
        raw = pd.DataFrame(rows)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(path, index=False)
    sess = np.array(sorted(sessions), dtype="datetime64[D]")
    out: Dict[date, List[str]] = {}
    for _, row in raw.iterrows():
        ts = pd.Timestamp(row["timestamp"])
        day = np.datetime64(ts.date())
        after_open = ts.time() >= time(9, 30)
        pos = np.searchsorted(sess, day, side="right" if after_open else "left")
        if pos < len(sess):
            d = pd.Timestamp(sess[pos]).date()
            out.setdefault(d, []).append(row["ticker"])
    return out


def premarket_release_ratio(minutes: pd.DataFrame) -> pd.Series:
    """Per session: mean volume 08:30-08:34 / mean volume 08:00-08:29 (pre-market, 1-minute bars)."""
    t = minutes.index.time
    burst = minutes[(t >= time(8, 30)) & (t < time(8, 35))]["volume"]
    base = minutes[(t >= time(8, 0)) & (t < time(8, 30))]["volume"]
    b = burst.groupby(burst.index.date).mean()
    a = base.groupby(base.index.date).mean()
    return (b / a.replace(0, np.nan)).rename("release_ratio")


def tag_sessions(sessions: Sequence[date], minutes: pd.DataFrame, release_threshold: float,
                 cache_dir: Optional[Path] = None) -> pd.DataFrame:
    """One row per session with boolean event columns."""
    sess = sorted(sessions)
    fomc = set(load_fomc_days(cache_dir))
    sess_arr = np.array(sess, dtype="datetime64[D]")
    fomc_next = set()
    for d in fomc:
        pos = np.searchsorted(sess_arr, np.datetime64(d), side="right")
        if pos < len(sess):
            fomc_next.add(pd.Timestamp(sess_arr[pos]).date())
    cpi = set(load_fred_release_days("cpi", cache_dir))
    jobs = set(load_fred_release_days("jobs", cache_dir))
    earn = load_earnings_sessions(sess, cache_dir=cache_dir)
    opex = opex_days(sess)
    ratio = premarket_release_ratio(minutes)
    df = pd.DataFrame(index=pd.Index(sess, name="date"))
    df["fomc_day"] = [d in fomc for d in sess]
    df["fomc_next_day"] = [d in fomc_next for d in sess]
    df["cpi_day_fred"] = [d in cpi for d in sess]
    df["jobs_day_fred"] = [d in jobs for d in sess]
    df["release_ratio"] = ratio.reindex(sess).to_numpy()
    df["macro_830"] = df["release_ratio"] >= release_threshold
    df["opex"] = [d in opex for d in sess]
    df["quad_witching"] = df["opex"] & np.array([d.month in (3, 6, 9, 12) for d in sess])
    df["megacap_earnings"] = [d in earn for d in sess]
    df["earnings_tickers"] = [",".join(earn.get(d, [])) for d in sess]
    df["any_major_event"] = df[["fomc_day", "fomc_next_day", "macro_830"]].any(axis=1)
    return df
