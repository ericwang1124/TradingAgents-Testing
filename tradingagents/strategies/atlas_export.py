"""Export the strategy x scenario atlas as JSON files for the interactive heatmap.

    python -m tradingagents.strategies.atlas_export --out-dir <dir>

Writes atlas_cells.json ({rows, meta}: one row per strategy x scenario dimension x state, with
the Sharpe ratio over the whole history and over each half, the number of days, the usable /
avoid flag and whether the state is today's) and atlas_strategies.json (one row per strategy).
Sharpe = annualised mean / std of daily excess returns on days in that state; states are known
at the prior close (calendar states in advance). "usable" = Sharpe >= 0.5 in both halves of the
strategy's history, "avoid" = <= -0.3 in both.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .strategy_atlas import _sharpe, build_scenarios, build_strategies, load_cpi, load_ohlc

FAMILIES = [
    ("intraday:", "SPY intraday"),
    ("MR:", "Short-term mean reversion"),
    ("pre-FOMC", "Calendar and events"),
    ("turn of month", "Calendar and events"),
    ("SPY overnight", "Equity timing"),
    ("SPY intraday", "Equity timing"),
    ("SPY trend", "Equity timing"),
    ("SPY 1-month", "Equity timing"),
    ("trend: TSMOM", "Multi-asset"),
    ("risk parity", "Multi-asset"),
    ("dual momentum", "Multi-asset"),
    ("put writing", "Volatility"),
    ("long VIX", "Volatility"),
    ("short VIX", "Volatility"),
    (" - ", "Style and sector spreads"),
    ("sector momentum", "Style and sector spreads"),
    ("long SPY", "Equity beta"), ("long QQQ", "Equity beta"), ("long IWM", "Equity beta"), ("long RSP", "Equity beta"),
    ("long developed", "Equity beta"), ("long emerging", "Equity beta"), ("long REITs", "Equity beta"),
    ("long ", "Bonds, commodities, FX, crypto"),
]


def family(name: str) -> str:
    for key, fam in FAMILIES:
        if name.startswith(key) or (key == " - " and key in name):
            return fam
    return "Other"


def r(x: float, n: int = 3):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


def export(out_dir: Path) -> None:
    d = load_ohlc()
    S = build_strategies(d)
    sc = build_scenarios(d, load_cpi(), S.index)
    today = sc.iloc[-1]
    rows = []
    for dim in sc.columns:
        states = sorted(s for s in sc[dim].dropna().unique() if s not in ("nan", "None"))
        for strat in S.columns:
            x = S[strat]
            valid = x.dropna()
            if valid.empty:
                continue
            mid = valid.index[0] + (valid.index[-1] - valid.index[0]) / 2
            for st in states:
                mask = sc[dim] == st
                full = _sharpe(x[mask])
                h1, h2 = _sharpe(x[mask & (x.index < mid)]), _sharpe(x[mask & (x.index >= mid)])
                verdict = ""
                if not np.isnan(h1) and not np.isnan(h2):
                    verdict = "usable" if (h1 >= 0.5 and h2 >= 0.5) else ("avoid" if (h1 <= -0.3 and h2 <= -0.3) else "")
                rows.append({"dimension": dim, "state": st, "strategy": strat, "family": family(strat),
                             "sharpe": r(full), "half1": r(h1), "half2": r(h2),
                             "days": int(x[mask].notna().sum()), "verdict": verdict,
                             "today": bool(today.get(dim) == st)})
    strategies = [{"strategy": s, "family": family(s), "sharpe": r(_sharpe(S[s])),
                   "start": str(S[s].dropna().index[0].date()), "end": str(S[s].dropna().index[-1].date())}
                  for s in S.columns]
    code = Path(__file__).read_text()
    meta = [{"label": "atlas_export.py", "value": code, "type": "code", "lang": "python"},
            {"label": "Inputs", "value": "Yahoo Finance daily prices (ETFs, futures, FX, VIX), FRED (CPI, Treasury yields, "
                                          "Fed balance sheet, policy uncertainty), Fed FOMC calendars, SPY 1-minute bars (Alpaca) "
                                          "for the intraday streams"},
            {"label": "As of", "value": str(sc.index[-1].date())}]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "atlas_cells.json").write_text(json.dumps({"rows": rows, "meta": meta}, separators=(",", ":")))
    (out_dir / "atlas_strategies.json").write_text(json.dumps({"rows": strategies, "meta": meta[:1] + meta[2:]}, separators=(",", ":")))
    print(f"{len(rows)} cells, {len(strategies)} strategies, {sc.shape[1]} dimensions -> {out_dir}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("results/opening_reversal/atlas_export"))
    export(p.parse_args(argv).out_dir)


if __name__ == "__main__":
    main()
