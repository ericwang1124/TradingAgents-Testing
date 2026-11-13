"""Do more (and less correlated) equity indices improve the live core portfolio?

    python -m tradingagents.strategies.equity_indices

Candidates are US-listed country / region / US-size ETFs (all tradable on the paper account).
Rules, fixed before running:

  A. long each index (excess over T-bills)
  B. trend: long each index while it is above its 200-day average, else cash
  C. three country composites, long-only:
     - country momentum: on the first session of each month hold the 5 countries with the best
       12-1 month return, equal weight (needs >= 10 countries with history)
     - country TSMOM: every country with a positive 12-month return, risk-weighted (10% vol / N)
     - country risk parity: inverse 60-day-vol weights across all countries
  D. A + B + C together

Each block is added to the core portfolio's strategy list and the whole book is rerun exactly as
live (weights refit each January on earlier years only, 2x leverage, gross <= 2, long-only, 2 bp per
unit of turnover). A block is adopted only if the book's Sharpe improves in every period:
2011-26, 2011-18, 2019-26 and 2024-05 onward.

Also reported: each candidate's own Sharpe and its weekly correlation with the core book, and the
high-efficiency open continuation add-on run on QQQ and IWM besides SPY (long side, 2021+).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np
import pandas as pd

from . import core_portfolio as cp
from . import regime_overlays as ro
from .opening_reversal.data import default_cache_dir
from .strategy_atlas import load_ohlc

COUNTRIES = {"EWJ": "Japan", "EWG": "Germany", "EWU": "UK", "EWQ": "France", "EWL": "Switzerland",
             "EWP": "Spain", "EWI": "Italy", "EWN": "Netherlands", "EWD": "Sweden", "EWA": "Australia",
             "EWC": "Canada", "EWH": "Hong Kong", "EWS": "Singapore", "EWT": "Taiwan", "EWY": "South Korea",
             "EWZ": "Brazil", "EWW": "Mexico", "FXI": "China large caps", "MCHI": "China", "INDA": "India",
             "EIDO": "Indonesia", "THD": "Thailand", "EZA": "South Africa", "TUR": "Turkey", "ECH": "Chile",
             "EPOL": "Poland", "EWM": "Malaysia", "ARGT": "Argentina", "VNM": "Vietnam", "EPHE": "Philippines"}
REGIONS = {"VGK": "Europe", "SCZ": "developed ex-US small caps", "MDY": "US mid caps",
           "IJR": "US small caps (S&P 600)", "DIA": "Dow 30"}
ALL = {**COUNTRIES, **REGIONS}
PERIODS = [("2011-26", "2011-01-01", "2026-12-31"), ("2011-18", "2011-01-01", "2018-12-31"),
           ("2019-26", "2019-01-01", "2026-12-31"), ("2024-05+", "2024-05-01", "2026-12-31")]
OUT = Path("results/opening_reversal/EQUITY_INDICES.md")
FEATURES = {"SPY": "results/opening_reversal/DAY_TYPE_features.csv",
            "QQQ": "results/opening_reversal/DAY_TYPE_features_QQQ.csv",
            "IWM": "results/opening_reversal/DAY_TYPE_features_IWM.csv"}


def load_indices(cal: pd.DatetimeIndex) -> pd.DataFrame:
    cache = default_cache_dir() / "equity_indices"
    return pd.DataFrame({t: pd.read_csv(cache / f"{t}.csv", index_col=0, parse_dates=True)["Close"] for t in ALL}).reindex(cal)


def _one(idx, t, amount) -> pd.DataFrame:
    return pd.DataFrame({t: amount}, index=idx)


def block_long(X: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    return {f"long {ALL[t]} {t}": _one(X.index, t, X[t].notna().astype(float)) for t in X}


def block_trend(X: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    return {f"trend {ALL[t]} {t}": _one(X.index, t, (X[t] > X[t].rolling(200).mean()).astype(float)) for t in X}


def block_composites(X: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    cty = X[list(COUNTRIES)]
    idx = cty.index
    ms = ro.month_starts(idx)
    mom = cty.shift(21) / cty.shift(252) - 1
    enough = mom.notna().sum(axis=1) >= 10
    top = mom.rank(axis=1, ascending=False).le(5) & enough.to_numpy()[:, None]
    P = {"country momentum: top 5 of 12-1m": (top.astype(float) / 5).where(ms, np.nan).ffill().fillna(0.0)}
    r = cty.pct_change()
    vol = r.ewm(span=60).std() * np.sqrt(252)
    n = cty.notna().sum(axis=1).replace(0, np.nan)
    P["country TSMOM (long-only)"] = ((cty.pct_change(252) > 0).astype(float) * (0.10 / vol).clip(upper=2)).div(n, axis=0).fillna(0.0)
    inv = (1 / vol).where(cty.notna())
    P["country risk parity"] = inv.div(inv.sum(axis=1), axis=0).fillna(0.0)
    return P


def make_ctx(base: ro.Ctx, extra: Dict[str, pd.DataFrame], X: pd.DataFrame) -> ro.Ctx:
    C = pd.concat([base.C, X], axis=1)
    P = {**base.P, **extra}
    R = cp.strategy_returns(P, C)
    scale = cp.strategy_scale(R)
    Rs = R * scale.shift(1)
    W0 = pd.DataFrame(0.0, index=C.index, columns=R.columns)
    for y in range(2011, C.index[-1].year + 1):
        W0.loc[W0.index.year == y] = cp.fit_weights(Rs[Rs.index.year < y]).to_numpy()
    r = C.pct_change()
    ex = r.sub(r["BIL"].fillna(0.0), axis=0)
    return ro.Ctx(C, P, Rs, scale, W0, ex, r, base.cpi_up)


def period_stats(r: pd.Series) -> Dict[str, float]:
    out = {name: ro.sharpe(r[(r.index >= a) & (r.index <= b)]) for name, a, b in PERIODS}
    out["2022"] = ro.sharpe(r[r.index.year == 2022])
    eq = (1 + r).cumprod()
    out["ann %"] = (eq.iloc[-1] ** (252 / len(r)) - 1) * 100
    out["maxDD %"] = (eq / eq.cummax() - 1).min() * 100
    return out


def weekly(x: pd.Series) -> pd.Series:
    return x.fillna(0.0).resample("W-FRI").sum()


def addon_long(path: str, years: List[int]) -> pd.Series:
    f = pd.read_csv(path, index_col=0, parse_dates=True)
    out = pd.Series(0.0, index=f.index)
    for y in years:
        thr = f.loc[f.index.year < y, "efficiency"].quantile(2 / 3)
        m = (f.index.year == y) & (f["efficiency"] >= thr) & (f["direction"] == 1)
        out[m] = f.loc[m, "cont_to_noon"]
    return out[out.index >= f"{years[0]}-01-01"]


def run() -> Dict[str, object]:
    base = ro.setup()
    X = load_indices(base.C.index)
    core = ro.book(base, base.W0)
    blocks: Dict[str, Callable[[pd.DataFrame], Dict[str, pd.DataFrame]]] = {
        "A. long each index": block_long, "B. trend (above SMA200)": block_trend,
        "C. country composites": block_composites,
        "D. A + B + C": lambda X: {**block_long(X), **block_trend(X), **block_composites(X)}}
    rows = {"baseline (live core)": period_stats(core)}
    shares, ctxs = {}, {}
    for name, fn in blocks.items():
        extra = fn(X)
        ctx = make_ctx(base, extra, X)
        ctxs[name] = ctx
        rows[name] = period_stats(ro.book(ctx, ctx.W0))
        w = ctx.W0.iloc[-1]
        shares[name] = {"risk budget to new strategies, 2026": float(w[list(extra)].sum()),
                        "new strategies with weight > 0, 2026": int((w[list(extra)] > 0).sum()),
                        "of": len(extra)}
    table = pd.DataFrame(rows).T
    b = table.loc["baseline (live core)"]
    verdict = {k: ("ADOPT" if all(table.loc[k, p] > b[p] for p, _, _ in PERIODS) else "reject") for k in blocks}

    # candidate-level: own Sharpe and weekly correlation with the core book
    allctx = ctxs["D. A + B + C"]
    R_new = cp.strategy_returns({k: v for k, v in allctx.P.items() if k not in base.P}, allctx.C)
    cw = weekly(core)
    cand = []
    for k in R_new:
        x = R_new[k][R_new[k].index >= "2011-01-01"].dropna()
        if len(x) < 500:
            continue
        cand.append({"strategy": k, "start": str(R_new[k].dropna().index[0].date()), "Sharpe 2011-26": ro.sharpe(x),
                     "weekly corr with core": float(weekly(x).corr(cw.reindex(weekly(x).index))),
                     "weekly corr with SPY": float(weekly(x).corr(weekly(base.ex["SPY"]).reindex(weekly(x).index))),
                     "weight 2026": float(allctx.W0.iloc[-1].get(k, 0.0))})
    cand = pd.DataFrame(cand).set_index("strategy").sort_values("Sharpe 2011-26", ascending=False)

    # intraday add-on on other indices
    years = list(range(2021, 2027))
    adds = {t: addon_long(p, years) for t, p in FEATURES.items() if Path(p).exists()}
    A = pd.DataFrame(adds).fillna(0.0)
    intr = {f"{t} only, 1x": ro.sharpe(A[t]) for t in A}
    intr["SPY + QQQ + IWM, 1/3x each"] = ro.sharpe(A.mean(axis=1))
    corr = A.where(A != 0).corr().round(2)
    c21 = core[core.index >= "2021-01-01"]
    comb = {"core + SPY add-on 1x": ro.sharpe(c21 + A["SPY"].reindex(c21.index).fillna(0.0)),
            "core + 3-index add-on 1/3x each": ro.sharpe(c21 + A.mean(axis=1).reindex(c21.index).fillna(0.0))}
    return {"table": table, "verdict": verdict, "shares": pd.DataFrame(shares).T, "cand": cand,
            "intraday": intr, "intraday_corr": corr, "intraday_comb": comb,
            "trade_days": {t: int((A[t] != 0).sum()) for t in A}}


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    res = run()
    md = lambda df: df.round(2).to_markdown()
    lines = ["# More equity indices in the core portfolio", "", "```", __doc__.strip(), "```", "",
             "## Core book with each block added", "", md(res["table"]), "", md(res["shares"]), "",
             "## Verdict", ""] + [f"- {k}: **{v}**" for k, v in res["verdict"].items()] + [
             "", "## Candidates: own Sharpe and correlation (2011-26, weekly)", "", md(res["cand"]), "",
             "## Intraday high-efficiency continuation on other indices (long side, 2021+)", "",
             "\n".join(f"- {k}: Sharpe {v:.2f}" for k, v in {**res["intraday"], **res["intraday_comb"]}.items()),
             "", "Trade days: " + ", ".join(f"{k} {v}" for k, v in res["trade_days"].items()), "",
             "Correlation of add-on returns on days both trade:", "", res["intraday_corr"].to_markdown()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
