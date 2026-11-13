"""Regime-based strategy selection, walk-forward.

    python -m tradingagents.strategies.regime_allocation

Daily return streams (all on SPY, out of our own backtests):
  * morning_momentum — noise-area breakout, checks 10:00/10:30, flat 12:00 (Zarattini et al. rules)
  * fullday_momentum — the paper's full-day noise-area strategy, 1x
  * fade             — gap-down reversal short, 1R target, flat 10:45, major-event days skipped
Regimes, fixed thresholds known before the open:
  * A: trend (prior close vs 50-day SMA) x prior-day VIX (<15 / 15-20 / >=20)
  * B: trend x VIX term structure (prior-day VIX / VIX3M < 1 contango, >= 1 backwardation)
Each January, using earlier years only, every regime is assigned the stream with the best past
Sharpe on that regime's days (>= ``min_days`` days, Sharpe > ``min_sharpe``), else cash; streams
are scaled to equal past volatility. The year is then traded with those assignments.
"""

from __future__ import annotations

import argparse
from datetime import date, time, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .intraday_momentum.strategies import NoiseAreaParams, noise_area_momentum, perf, session_matrix
from .opening_reversal.backtest import eligible_contexts, run_backtest
from .opening_reversal.data import load_alpaca_minutes
from .opening_reversal.events import tag_sessions
from .opening_reversal.levels import build_day_contexts
from .opening_reversal.live.settings import LIVE_PARAMS
from .opening_reversal.regime import attach_vix, load_vix, vix_bucket

FADE_RISK = 0.005


def _dates(idx) -> pd.Index:
    return pd.Index([pd.Timestamp(d).date() for d in idx])


def build_streams(start: date, end: date) -> Tuple[pd.DataFrame, pd.DataFrame]:
    minutes = load_alpaca_minutes("SPY", start - timedelta(days=120), end, verbose=False)
    mat = session_matrix(minutes)
    streams = {}
    for name, params in {
        "morning_momentum": NoiseAreaParams(vol_target=False, last_check=time(10, 30), exit_time=time(12, 0)),
        "morning_momentum_voltarget": NoiseAreaParams(vol_target=True, last_check=time(10, 30), exit_time=time(12, 0)),
        "fullday_momentum": NoiseAreaParams(vol_target=False),
    }.items():
        r = noise_area_momentum(mat, params)["ret"]
        streams[name] = pd.Series(r.to_numpy(), index=_dates(r.index))
    ctxs = [c for c in eligible_contexts(build_day_contexts(minutes)) if start <= c.day.date() <= end]
    vix = load_vix(start - timedelta(days=120), end)
    attach_vix(ctxs, vix)
    sessions = [c.day.date() for c in ctxs]
    tags = tag_sessions(sessions, minutes, release_threshold=4.0)
    fade = run_backtest(params=LIVE_PARAMS, contexts=ctxs)
    fade = fade[~fade["date"].map(tags["any_major_event"]).fillna(False).astype(bool)]
    days = pd.Index(sorted(set(streams["morning_momentum"].index) & set(sessions)))
    df = pd.DataFrame({k: v.reindex(days) for k, v in streams.items()}).fillna(0.0)
    df["fade"] = fade.set_index("date")["r_multiple"].reindex(days).fillna(0.0) * FADE_RISK

    import yfinance as yf

    v3 = yf.Ticker("^VIX3M").history(start=start - timedelta(days=30), end=end + timedelta(days=1), auto_adjust=False)
    v3 = pd.Series(v3["Close"].to_numpy(), index=_dates(v3.index))
    vx = pd.Series(vix.to_numpy(), index=_dates(vix.index))
    ratio = (vx / v3).dropna().sort_index()
    rows = []
    for c in ctxs:
        if c.day.date() not in days:
            continue
        sma = c.features.get("sma50", np.nan)
        trend = None if np.isnan(sma) else ("up" if c.prev_close >= sma else "down")
        prior = ratio[ratio.index < c.day.date()]
        ts = None if prior.empty else ("backwardation" if prior.iloc[-1] >= 1 else "contango")
        vb = vix_bucket(c.features.get("vix_prev", np.nan))
        rows.append({"date": c.day.date(),
                     "A": f"{trend}/{vb}" if trend and vb else None,
                     "B": f"{trend}/{ts}" if trend and ts else None})
    regimes = pd.DataFrame(rows).set_index("date").reindex(days)
    return df, regimes


def _sharpe(r: pd.Series) -> float:
    return r.mean() / r.std() * np.sqrt(252) if len(r) > 2 and r.std() > 0 else np.nan


def walk_forward_allocation(streams: pd.DataFrame, regime: pd.Series, years: List[int], candidates: List[str],
                            min_days: int = 60, min_sharpe: float = 0.0) -> Tuple[pd.Series, pd.DataFrame]:
    """Out-of-sample daily returns of the regime -> stream assignment, and the assignments."""
    year = pd.Series([d.year for d in streams.index], index=streams.index)
    out = pd.Series(0.0, index=streams.index[year.isin(years)])
    picks = []
    for y in years:
        past, cur = streams[year < y], streams[year == y]
        scale = {s: 0.01 / past[s].std() if past[s].std() > 0 else 0.0 for s in candidates}
        for reg in sorted(regime.dropna().unique()):
            mask_p = regime.reindex(past.index) == reg
            choice, best = None, -np.inf
            for s in candidates:
                r = past.loc[mask_p, s]
                sh = _sharpe(r)
                if len(r) >= min_days and not np.isnan(sh) and sh > best:
                    choice, best = s, sh
            if choice is None or best <= min_sharpe:
                choice = "cash"
            mask_c = regime.reindex(cur.index) == reg
            if choice != "cash":
                out.loc[cur.index[mask_c.to_numpy()]] = cur.loc[mask_c, choice] * scale[choice]
            picks.append({"year": y, "regime": reg, "choice": choice, "past_sharpe": round(best, 2),
                          "days_this_year": int(mask_c.sum())})
    return out, pd.DataFrame(picks)


def report(streams: pd.DataFrame, regimes: pd.DataFrame, years: List[int]) -> str:
    def row(r: pd.Series) -> Dict[str, float]:
        r = r.dropna()
        late = r[[d >= date(2024, 5, 1) for d in r.index]]
        p = perf(r)
        return {"Sharpe": p["sharpe"], "ann_ret_%": p["ann_return_%"], "max_dd_%": p["max_dd_%"],
                "Sharpe 2024-05+": perf(late)["sharpe"], "days_in_market_%": (r != 0).mean() * 100}

    oos = {}
    oos_idx = streams.index[[d.year in years for d in streams.index]]
    for s in streams.columns:
        oos[f"static: {s}"] = streams.loc[oos_idx, s]
    sets = {
        "all three": ["morning_momentum", "fullday_momentum", "fade"],
        "momentum only": ["morning_momentum", "fullday_momentum"],
        "morning momentum gated": ["morning_momentum"],
        "fade gated": ["fade"],
    }
    picks_out = {}
    for scheme in ("A", "B"):
        for label, cands in sets.items():
            r, picks = walk_forward_allocation(streams, regimes[scheme], years, cands)
            oos[f"regime {scheme}: {label}"] = r
            picks_out[(scheme, label)] = picks
    table = pd.DataFrame({k: row(v) for k, v in oos.items()}).T

    desc = []
    for scheme in ("A", "B"):
        g = streams.join(regimes[scheme].rename("regime")).dropna(subset=["regime"])
        g["period"] = ["2019-22" if d.year <= 2022 else "2023-26" for d in g.index]
        s = g.groupby(["regime", "period"])[["morning_momentum", "fullday_momentum", "fade"]].agg(_sharpe).unstack("period")
        n = g.groupby(["regime", "period"]).size().unstack("period")
        desc.append((scheme, s, n))

    def md(df, fmt=".2f"):
        try:
            return df.to_markdown(floatfmt=fmt)
        except ImportError:
            return "```\n" + df.round(2).to_string() + "\n```"

    lines = ["# Regime-based strategy selection (walk-forward)", "",
             f"Out-of-sample years: {years[0]}-{years[-1]}. Static rows are the raw streams over the same days.", "",
             md(table), ""]
    for scheme, s, n in desc:
        lines += [f"## Sharpe of each stream by regime {scheme} (whole sample, descriptive)", "", md(s), "",
                  "Sessions per regime:", "", md(n, ".0f"), ""]
    for (scheme, label), picks in picks_out.items():
        if label in ("all three",):
            lines += [f"## Assignments, regime {scheme}: {label}", "", md(picks.set_index(["year", "regime"])), ""]
    return "\n".join(lines)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--first-test-year", type=int, default=2021)
    p.add_argument("--out", default="results/opening_reversal/REGIME_ALLOCATION.md")
    args = p.parse_args(argv)
    streams, regimes = build_streams(args.start, args.end)
    text = report(streams, regimes, list(range(args.first_test_year, args.end.year + 1)))
    with open(args.out, "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
