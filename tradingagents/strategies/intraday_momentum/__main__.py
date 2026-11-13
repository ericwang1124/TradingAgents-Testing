"""python -m tradingagents.strategies.intraday_momentum [--dix path/to/DIX.csv]

Re-tests the published rules on SPY 1-minute Alpaca data and prints Sharpe tables by period,
including the post-publication window (May 2024 onward). With ``--dix`` (SqueezeMetrics' free
daily file: date, price, dix, gex) it also splits results by the prior day's dealer-gamma
percentile within the trailing year.
"""

from __future__ import annotations

import argparse
from datetime import date, time, timedelta
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from ..opening_reversal.data import load_alpaca_minutes
from .strategies import NoiseAreaParams, half_hour_momentum, noise_area_momentum, perf, session_matrix

PERIODS: Dict[str, Tuple[str, str]] = {
    "2019-26": ("2019-01-01", "2100-01-01"),
    "2019-22": ("2019-01-01", "2022-12-31"),
    "2023-26": ("2023-01-01", "2100-01-01"),
    "2024-05+ (after publication)": ("2024-05-01", "2100-01-01"),
}
VARIANTS = {
    "noise area, vol-targeted (paper)": NoiseAreaParams(),
    "noise area, 1x": NoiseAreaParams(vol_target=False),
    "noise area morning: checks 10:00/10:30, flat 12:00, 1x": NoiseAreaParams(
        vol_target=False, last_check=time(10, 30), exit_time=time(12, 0)),
}


def by_period(ret: pd.Series) -> pd.DataFrame:
    idx = pd.to_datetime(pd.Index(ret.index).astype(str).str[:10])
    ret = pd.Series(ret.to_numpy(), index=idx)
    return pd.DataFrame({k: perf(ret[(ret.index >= a) & (ret.index <= b)]) for k, (a, b) in PERIODS.items()}).T


def gamma_split(ret: pd.Series, dix_path: Path) -> pd.DataFrame:
    dix = pd.read_csv(dix_path, parse_dates=["date"]).set_index("date").sort_index()
    pct = dix["gex"].rolling(252, min_periods=126).apply(lambda w: (w[:-1] < w[-1]).mean(), raw=True).shift(1)
    idx = pd.to_datetime(pd.Index(ret.index).astype(str).str[:10])
    r = pd.DataFrame({"ret": ret.to_numpy(), "pct": pct.reindex(idx).to_numpy()}, index=idx)
    rows = {}
    for name, (a, b) in PERIODS.items():
        g = r[(r.index >= a) & (r.index <= b)]
        lo, hi = g[g["pct"] < 0.5]["ret"], g[g["pct"] >= 0.5]["ret"]
        rows[name] = {"sharpe low-gamma days": perf(lo)["sharpe"], "sharpe high-gamma days": perf(hi)["sharpe"],
                      "n low": len(lo), "n high": len(hi)}
    return pd.DataFrame(rows).T


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--dix", type=Path, default=None, help="SqueezeMetrics DIX.csv for the gamma split")
    args = p.parse_args(argv)

    minutes = load_alpaca_minutes("SPY", args.start - timedelta(days=60), args.end, verbose=False)
    mat = session_matrix(minutes)
    pd.set_option("display.width", 200)
    for name, params in VARIANTS.items():
        ret = noise_area_momentum(mat, params)["ret"]
        ret = ret[ret.index >= pd.Timestamp(args.start, tz=ret.index.tz)]
        print(f"\n=== {name} ===\n{by_period(ret).round(2).to_string()}")
        if args.dix:
            print(gamma_split(ret, args.dix).round(2).to_string())
    hh = half_hour_momentum(mat)["ret"]
    hh = hh[hh.index >= pd.Timestamp(args.start, tz=hh.index.tz)]
    print(f"\n=== half-hour momentum (Gao et al. 2018), 1x ===\n{by_period(hh).round(2).to_string()}")
    spy = mat["close"].iloc[:, -1].pct_change()
    spy = spy[spy.index >= pd.Timestamp(args.start, tz=spy.index.tz)]
    print(f"\n=== SPY buy & hold ===\n{by_period(spy).round(2).to_string()}")


if __name__ == "__main__":
    main()
