"""Point-in-time earnings, guidance and analyst signals from Alpaca's news headlines (Benzinga).

Headlines carry a timestamp, exist for delisted companies too, and follow a few stable formats:

    "Super Micro Computer Q1 EPS $3.43 Beats $3.20 Estimate, Sales $2.12B Beat $2.06B Estimate"
    "Boot Barn Reports Q1 EPS $0.03 vs $0.02 In Same Qtr. Last Year, Sales $139.4M vs $133.4M YoY"      (older)
    "e.l.f Beauty Raises FY23 Adj. EPS Guidance From $0.84-$0.87 To $1.07-$1.10 vs $0.91 Est."
    "JP Morgan Maintains Overweight on e.l.f. Beauty, Raises Price Target to $48"

``signals`` reduces what was published before a cutoff time to three numbers a trader could have
known then: how the latest quarterly report compared with estimates (or with the year before),
whether guidance moved up or down, and the balance of analyst target raises and cuts.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests

from . import data as vdata

NEWS_DIR = vdata.CACHE / "news"
MIN_INTERVAL = 0.32          # seconds between requests (the API allows 200 per minute)
MAX_PAGES = 40               # 2,000 headlines per window; heavily covered names are cut off at the old end
GUIDE = re.compile(r"\b(Guidance|Outlook|Forecast|Sees|Guides|Expects)\b", re.I)
UP = re.compile(r"\b(Raises|Raised|Raising|Boosts|Lifts|Increases|Hikes|Ups)\b", re.I)
DOWN = re.compile(r"\b(Lowers|Lowered|Cuts|Reduces|Slashes|Trims|Withdraws|Suspends)\b", re.I)
NUMBER = re.compile(r"(?P<neg>(?<![\w.])-)?\$(?P<par>\()?(?P<num>-?\d*\.?\d+)\)?\s?(?P<unit>[KMBT])?(?![A-Za-z])")
UNIT = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
_last_call = [0.0]


# ------------------------------------------------------------------ parsing
def _numbers(seg: str) -> List[float]:
    out = []
    for m in NUMBER.finditer(seg):                       # "$1.1B-$1.2B" is a range, "$(0.12)" and "-$0.12" are negative
        x = float(m.group("num")) * UNIT.get((m.group("unit") or "").upper(), 1.0)
        neg = m.group("neg") or m.group("par") or m.group("num").startswith("-")
        out.append(-abs(x) if neg else x)
    return out


def _versus(seg: str) -> Optional[Tuple[str, float]]:
    """('est', +1/0/-1) against estimates, or ('yoy', growth) against the year before."""
    if re.search(r"\bBeats?\b", seg, re.I):
        return "est", 1.0
    if re.search(r"\bMiss(es)?\b", seg, re.I):
        return "est", -1.0
    if re.search(r"In-?Line|Inline|\bMeets\b|\bMatches\b", seg, re.I):
        return "est", 0.0
    n = _numbers(seg)
    if len(n) >= 2:
        if re.search(r"\bEst", seg, re.I):
            return "est", float((n[0] > n[1]) - (n[0] < n[1]))
        if re.search(r"Last Year|YoY|Year Ago|Prior Year|Same Qtr", seg, re.I) and n[1] != 0:
            return "yoy", n[0] / abs(n[1]) - (1.0 if n[1] > 0 else -1.0)
    return None


def parse(headline: str) -> Dict[str, float]:
    """Signals in one headline: eps, sales (+1 beat / 0 in line / -1 miss), guidance (+1 / -1), analyst (+1 / -1)."""
    h = re.sub(r"(?<=\d),(?=\d{3})", "", headline)
    out: Dict[str, float] = {}
    if re.search(r"Price Target|\bPT\b", h, re.I):
        if re.search(r"\bRaises\b", h, re.I):
            out["analyst"] = 1.0
        elif re.search(r"\bLowers\b", h, re.I):
            out["analyst"] = -1.0
        return out
    if re.search(r"\bUpgrades\b", h):
        return {"analyst": 1.0}
    if re.search(r"\bDowngrades\b", h):
        return {"analyst": -1.0}
    segs = re.split(r"[,;]", h)
    if re.search(r"\bQ[1-4]\b", h) and re.search(r"\bEPS\b", h):
        for key, pat in (("eps", r"\bEPS\b"), ("sales", r"\b(Sales|Revenues?|Revs)\b")):
            seg = next((s for s in segs if re.search(pat, s) and not GUIDE.search(s)), None)
            v = _versus(seg) if seg else None
            if v is None:
                continue
            kind, x = v
            if kind == "est":
                out[key] = x
            else:                                    # year-over-year format: sales need 10% growth to count as strong
                out[key] = (1.0 if x >= 0.10 else (-1.0 if x < 0 else 0.0)) if key == "sales" else float((x > 0) - (x < 0))
    g = [s for s in segs if GUIDE.search(s)]
    if g:
        text = " ".join(g)
        up, down = bool(UP.search(text)), bool(DOWN.search(text))
        if up != down:
            out["guidance"] = 1.0 if up else -1.0
        else:
            m = re.search(r"\bFrom\b(.*?)\bTo\b(.*)", text, re.I)
            if m:
                a, b = _numbers(m.group(1)), _numbers(m.group(2))
                if a and b and a[0] != b[0]:
                    out["guidance"] = 1.0 if b[0] > a[0] else -1.0
            elif re.search(r"\bvs\.?\b.*\bEst", text, re.I):
                left, right = re.split(r"\bvs\.?\b", text, maxsplit=1, flags=re.I)
                a, b = _numbers(left), _numbers(right)
                if a and b:
                    mid = sum(a[-2:]) / len(a[-2:]) if "-" in left[-30:] and len(a) >= 2 else a[-1]
                    if abs(mid - b[0]) > 0.005 * abs(b[0]):
                        out["guidance"] = 1.0 if mid > b[0] else -1.0
    return out


def signals(items: Iterable[Tuple[str, str]], cutoff: pd.Timestamp) -> Dict[str, float]:
    """What the headlines published before ``cutoff`` say. ``items``: (ISO time, headline)."""
    cutoff = pd.Timestamp(cutoff).tz_localize("UTC") if pd.Timestamp(cutoff).tzinfo is None else pd.Timestamp(cutoff)
    rows = [(pd.Timestamp(ts), parse(hl)) for ts, hl in items]
    rows = sorted([(ts, p) for ts, p in rows if p and ts < cutoff], key=lambda x: x[0], reverse=True)
    out = {"report": float("nan"), "eps": float("nan"), "sales": float("nan"), "guidance": 0.0, "analyst": 0.0,
           "headlines": float(sum(1 for ts, _ in items if pd.Timestamp(ts) < cutoff))}
    for ts, p in rows:
        age = (cutoff - ts).days
        if age <= 95 and ("eps" in p or "sales" in p) and out["report"] != out["report"]:
            out["report"], out["eps"], out["sales"] = float(age), p.get("eps", float("nan")), p.get("sales", float("nan"))
        if age <= 95 and "guidance" in p:
            out["guidance"] += p["guidance"]
        if age <= 60 and "analyst" in p:
            out["analyst"] += p["analyst"]
    return out


# ------------------------------------------------------------------ download
def _headers() -> Dict[str, str]:
    k, s = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
    return {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s} if k and s else {}


def _page(params: dict) -> dict:
    for i in range(10):
        wait = MIN_INTERVAL - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        try:
            r = requests.get("https://data.alpaca.markets/v1beta1/news", headers=_headers(), params=params, timeout=60)
        except requests.RequestException:
            time.sleep(3 + 2 * i)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 + 3 * i)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("news request failed repeatedly")


def fetch(symbols: List[str], start: pd.Timestamp, end: pd.Timestamp) -> Tuple[List[Tuple[str, str]], bool]:
    """Headlines for any of ``symbols`` in [start, end], newest first; the flag says the page cap was hit."""
    items, tok = [], None
    for _ in range(MAX_PAGES):
        p = {"symbols": ",".join(symbols), "start": start.strftime("%Y-%m-%dT00:00:00Z"), "end": end.strftime("%Y-%m-%dT23:59:59Z"),
             "limit": 50, "sort": "desc", "include_content": "false", "exclude_contentless": "false"}
        if tok:
            p["page_token"] = tok
        j = _page(p)
        items += [(x["created_at"], x["headline"]) for x in j.get("news", [])]
        tok = j.get("next_page_token")
        if not tok:
            return items, False
    return items, True


def aliases() -> Dict[str, List[str]]:
    """Current ticker -> earlier tickers of the same company (news is filed under the ticker of its day)."""
    path = vdata.CACHE / "aliases.json"
    if path.exists():
        return json.loads(path.read_text())
    rd = lambda f: pd.read_csv(vdata.CACHE / f, parse_dates=["date"], keep_default_na=False, na_values=[""])
    both = pd.concat([rd("monthly_raw_listed.csv.gz"), rd("monthly_raw_unlisted.csv.gz")], ignore_index=True)
    keep = set(vdata.prefilter(both))
    out: Dict[str, List[str]] = {}
    for kept, dropped in vdata.duplicate_pairs(both[both["symbol"].isin(keep)]):
        out.setdefault(kept, []).append(dropped)
    path.write_text(json.dumps(out))
    return out


def load(column: str) -> Dict[str, list]:
    path = NEWS_DIR / f"{column}.json"
    return json.loads(path.read_text()) if path.exists() else {"windows": [], "items": []}


def ensure(column: str, start: pd.Timestamp, end: pd.Timestamp, alias: Dict[str, List[str]]) -> Dict[str, list]:
    """Headlines for a data column over [start, end], fetched once and kept on disk."""
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    rec = load(column)
    s, e = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    if any(w[0] <= s and e <= w[1] for w in rec["windows"]):
        return rec
    sym = column.split("~")[0]
    items, cut = fetch([sym] + alias.get(sym, []), start, end)
    seen = {(a, b) for a, b in rec["items"]}
    rec["items"] += [[a, b] for a, b in items if (a, b) not in seen]
    rec["windows"].append([s, e, cut])
    (NEWS_DIR / f"{column}.json").write_text(json.dumps(rec))
    return rec
