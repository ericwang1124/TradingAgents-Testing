"""Pre-market briefing: the facts the daily GO / NO_GO decision is based on."""

from __future__ import annotations

import json
import time as _time
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..data import NY, default_cache_dir, load_alpaca_minutes
from ..events import load_earnings_sessions, load_fomc_days, load_fred_release_days, premarket_release_ratio
from ..levels import RTH_CLOSE, RTH_OPEN, _daily_features, volume_profile
from ..regime import load_vix, vix_bucket
from .alpaca_trading import AlpacaClient
from .settings import HARD_RULES, HISTORY_DAYS, LIVE_PARAMS, STATS_PATH, SYMBOL


def _stale(path: Path, days: float) -> bool:
    return not path.exists() or (_time.time() - path.stat().st_mtime) > days * 86400


def daily_bars(minutes: pd.DataFrame) -> pd.DataFrame:
    t = minutes.index.time
    rth = minutes[(t >= RTH_OPEN) & (t < RTH_CLOSE)]
    g = rth.groupby(rth.index.date)
    return pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                         "close": g["close"].last()})


def build_briefing(day: date, client: Optional[AlpacaClient] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    client = client or AlpacaClient()
    now = now or pd.Timestamp.now(tz=NY).to_pydatetime()
    cal = client.calendar(day, day)
    session = cal[0] if cal and cal[0]["date"] == day.isoformat() else None
    hard: Dict[str, bool] = {k: False for k in HARD_RULES}
    out: Dict[str, Any] = {"date": day.isoformat(), "generated_at": now.isoformat(), "symbol": SYMBOL}
    if session is None:
        hard["market_closed"] = True
        out.update(hard_rules=hard, hard_no_go=True)
        return out
    hard["half_day"] = session["close"] < "16:00"

    history = load_alpaca_minutes(SYMBOL, day - timedelta(days=HISTORY_DAYS), day - timedelta(days=1), verbose=False)
    daily = daily_bars(history)
    prev_day = daily.index[-1]
    prev = daily.iloc[-1]
    t = history.index.time
    prev_rth = history[(history.index.date == prev_day) & (t >= RTH_OPEN) & (t < RTH_CLOSE)]
    profile = volume_profile(prev_rth, LIVE_PARAMS.profile_bin_pct, LIVE_PARAMS.value_area_share)
    hlc = list(daily[["high", "low", "close"]].itertuples(index=False, name=None))
    feats = _daily_features(hlc)
    closes = daily["close"].to_numpy()
    sma20, sma50 = closes[-20:].mean(), closes[-50:].mean() if len(closes) >= 50 else np.nan

    today = client.bars_today(SYMBOL, day)
    pre = today[today.index.time < RTH_OPEN]
    last_price = float(pre["close"].iloc[-1]) if not pre.empty else np.nan
    ratio = premarket_release_ratio(today)
    release_ratio = float(ratio.iloc[-1]) if len(ratio) and now.time() >= time(8, 35) else None

    vix = load_vix(day - timedelta(days=30), day - timedelta(days=1))
    vix_prev = float(vix[vix.index.date < day].iloc[-1])
    trend = "up" if prev["close"] >= sma50 else "down"

    cache = default_cache_dir()
    fomc = set(load_fomc_days(refresh=_stale(cache / "fomc_days.csv", 7)))
    cpi = set(load_fred_release_days("cpi", refresh=_stale(cache / "fred_cpi_days.csv", 7)))
    jobs = set(load_fred_release_days("jobs", refresh=_stale(cache / "fred_jobs_days.csv", 7)))
    earnings = load_earnings_sessions([prev_day, day], refresh=_stale(cache / "megacap_earnings.csv", 3))
    hard.update(fomc_day=day in fomc, fomc_next_day=prev_day in fomc, cpi_day=day in cpi, jobs_day=day in jobs)

    news = client.news("SPY,QQQ", start=pd.Timestamp(datetime.combine(prev_day, time(16, 0)), tz=NY)
                       .tz_convert("UTC").to_pydatetime(), limit=40)
    stats = json.loads(STATS_PATH.read_text()) if STATS_PATH.exists() else {}
    regime = f"{trend}/{vix_bucket(vix_prev)}"

    out.update({
        "session": {"open": session["open"], "close": session["close"], "prev_session": prev_day.isoformat()},
        "levels": {
            "prev_close": round(float(prev["close"]), 2), "prev_high": round(float(prev["high"]), 2),
            "prev_low": round(float(prev["low"]), 2),
            **{f"prev_{k}": round(v, 2) for k, v in profile.items()},
            "premarket_high": round(float(pre["high"].max()), 2) if not pre.empty else None,
            "premarket_low": round(float(pre["low"].min()), 2) if not pre.empty else None,
        },
        "premarket": {
            "last_price": round(last_price, 2) if not np.isnan(last_price) else None,
            "implied_gap_pct": round((last_price / prev["close"] - 1) * 100, 3) if not np.isnan(last_price) else None,
            "gap_down_setup_possible": bool(last_price / prev["close"] - 1 <= -LIVE_PARAMS.min_gap_pct)
            if not np.isnan(last_price) else None,
            "release_830_volume_ratio_iex": round(release_ratio, 2) if release_ratio is not None else None,
        },
        "regime": {
            "label": regime, "vix_prev_close": round(vix_prev, 2),
            "prev_close_vs_sma20_pct": round((prev["close"] / sma20 - 1) * 100, 2),
            "prev_close_vs_sma50_pct": round((prev["close"] / sma50 - 1) * 100, 2) if not np.isnan(sma50) else None,
            "atr14_pct": round(feats["atr14_pct"] * 100, 2), "ret_1d_pct": round(feats["ret_1d"] * 100, 2),
            "ret_5d_pct": round(feats["ret_5d"] * 100, 2),
        },
        "events": {
            "fomc_today": hard["fomc_day"], "fomc_yesterday": hard["fomc_next_day"],
            "cpi_today": hard["cpi_day"], "jobs_report_today": hard["jobs_day"],
            "monthly_opex": day.weekday() == 4 and 15 <= day.day <= 21,
            "megacap_earnings_since_last_close": earnings.get(day, []),
        },
        "hard_rules": hard,
        "hard_no_go": any(hard.values()),
        "historical": {
            "strategy": "gap-down reversal short, 1R target, flat 10:45 (2019-2026 backtest, underlying R)",
            "overall": stats.get("overall"),
            "this_regime": stats.get("by_regime", {}).get(regime),
            "major_event_days": stats.get("major_event_days"),
            "other_days": stats.get("other_days"),
        },
        "news": [{"time": pd.Timestamp(n["created_at"]).tz_convert(NY).strftime("%m-%d %H:%M"),
                  "headline": n["headline"]} for n in news],
    })
    return out


def briefing_markdown(b: Dict[str, Any]) -> str:
    if b.get("hard_rules", {}).get("market_closed"):
        return f"# {b['date']}: market closed — no trading"
    lines = [f"# Pre-market briefing {b['date']} ({b['symbol']})", ""]
    hard = [k for k, v in b["hard_rules"].items() if v]
    lines.append(f"**Hard rules:** {'NO_GO — ' + ', '.join(hard) if hard else 'none triggered'}")
    lines.append("")
    for section in ("premarket", "levels", "regime", "events", "historical"):
        lines.append(f"## {section}")
        for k, v in b[section].items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    lines.append("## news since last close (Alpaca/Benzinga)")
    lines += [f"- {n['time']} {n['headline']}" for n in b["news"][:30]]
    return "\n".join(lines)
