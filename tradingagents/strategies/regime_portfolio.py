"""Different strategies for different regimes — daily, multi-asset, 2007-2026.

    python -m tradingagents.strategies.regime_portfolio

Strategies (daily excess returns over T-bills, positions set at the prior close):
  EQ        long SPY
  TREND_EQ  long SPY when it closed above its 200-day SMA, else T-bills
  TSMOM     time-series momentum on SPY, TLT, GLD, DBC: sign of the 12-month return, each leg
            scaled to 10% vol (Moskowitz-Ooi-Pedersen style), equal-weighted
  MR_EQ     short-term mean reversion: long SPY from RSI(2) < 10 until RSI(2) > 70
  BONDS     long TLT;  GOLD  long GLD;  COMMOD  long DBC
  PUTWRITE  Cboe S&P 500 PutWrite index (systematic put selling)

Regimes (known at the prior close):
  A  trend (SPY vs 200-day SMA) x volatility (VIX < 20 / >= 20)
  B  trend x inflation direction (CPI y/y now vs 6 months earlier, with a publication lag)

Allocation methods, each strategy first scaled to 10% annualised volatility (trailing 60 days):
  static        equal risk in all strategies, every day
  ex-ante map   a regime -> strategy-set map written from the literature BEFORE testing
  learned       walk-forward (yearly): per regime, shrunk mean / variance weights, long-only
  learned, no regime   the same estimator without regimes (isolates the value of regimes)
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .opening_reversal.data import default_cache_dir

TICKERS = ["SPY", "TLT", "GLD", "DBC", "BIL", "^VIX", "^PUT"]
STRATS = ["EQ", "TREND_EQ", "TSMOM", "MR_EQ", "BONDS", "GOLD", "COMMOD", "PUTWRITE"]
TARGET_VOL = 0.10

# Written from the literature before looking at results (see the research notes):
#   trend following holds up in drawdowns and inflation (Hurst-Ooi-Pedersen; Neville et al. 2021),
#   short-term reversal pays more when VIX is high (Nagel 2012), put selling earns more at higher
#   VIX in calm uptrends (Bondarenko), bonds hedge equity sell-offs when inflation is falling,
#   commodities / gold / trend are the inflation hedges, equities and bonds suffer when inflation rises.
EX_ANTE: Dict[str, Dict[str, List[str]]] = {
    "A": {
        "up/vix<20": ["EQ", "TREND_EQ", "MR_EQ", "PUTWRITE", "TSMOM"],
        "up/vix>=20": ["EQ", "MR_EQ", "PUTWRITE", "TSMOM"],
        "down/vix<20": ["TSMOM", "BONDS", "GOLD"],
        "down/vix>=20": ["TSMOM", "MR_EQ", "BONDS", "GOLD"],
    },
    "B": {
        "up/infl falling": ["EQ", "TREND_EQ", "MR_EQ", "PUTWRITE", "BONDS"],
        "up/infl rising": ["EQ", "TSMOM", "COMMOD", "GOLD", "MR_EQ"],
        "down/infl falling": ["TSMOM", "BONDS", "GOLD", "MR_EQ"],
        "down/infl rising": ["TSMOM", "COMMOD", "GOLD"],
    },
}


def load_daily(refresh: bool = False) -> pd.DataFrame:
    path = default_cache_dir() / "regime_portfolio_daily.csv"
    if path.exists() and not refresh:
        return pd.read_csv(path, index_col=0, parse_dates=True)
    import yfinance as yf

    cols = {}
    for t in TICKERS:
        h = yf.Ticker(t).history(period="max", auto_adjust=True)
        cols[t] = pd.Series(h["Close"].to_numpy(), index=pd.DatetimeIndex(h.index.date))
    px = pd.DataFrame(cols).sort_index()
    path.parent.mkdir(parents=True, exist_ok=True)
    px.to_csv(path)
    return px


def load_cpi() -> pd.Series:
    cpi = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL", parse_dates=["observation_date"])
    return cpi.set_index("observation_date")["CPIAUCSL"]


def rsi(close: pd.Series, n: int = 2) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def build_strategies(px: pd.DataFrame) -> pd.DataFrame:
    px = px.dropna(subset=["SPY", "TLT", "GLD", "DBC", "BIL", "^VIX", "^PUT"])
    r = px.pct_change()
    rf = r["BIL"].fillna(0.0)
    ex = r[["SPY", "TLT", "GLD", "DBC", "^PUT"]].sub(rf, axis=0)
    spy = px["SPY"]
    above = (spy > spy.rolling(200).mean()).shift(1)
    out = pd.DataFrame(index=px.index)
    out["EQ"] = ex["SPY"]
    out["TREND_EQ"] = ex["SPY"].where(above.fillna(False).astype(bool), 0.0)
    legs = []
    for a in ("SPY", "TLT", "GLD", "DBC"):
        sig = np.sign(px[a] / px[a].shift(252) - 1).shift(1)
        vol = r[a].ewm(span=60).std().shift(1) * np.sqrt(252)
        legs.append(sig * (TARGET_VOL / vol).clip(upper=2.0) * ex[a])
    out["TSMOM"] = pd.concat(legs, axis=1).mean(axis=1)
    rs = rsi(spy, 2)
    pos, state = [], 0
    for v in rs.to_numpy():
        if state == 0 and v < 10:
            state = 1
        elif state == 1 and v > 70:
            state = 0
        pos.append(state)
    out["MR_EQ"] = ex["SPY"] * pd.Series(pos, index=px.index).shift(1).fillna(0)
    out["BONDS"], out["GOLD"], out["COMMOD"], out["PUTWRITE"] = ex["TLT"], ex["GLD"], ex["DBC"], ex["^PUT"]
    return out.dropna()


def build_regimes(px: pd.DataFrame, cpi: pd.Series, index: pd.DatetimeIndex) -> pd.DataFrame:
    spy = px["SPY"]
    trend = np.where(spy > spy.rolling(200).mean(), "up", "down")
    trend = pd.Series(trend, index=px.index).shift(1)
    vix = px["^VIX"].shift(1)
    yoy = cpi.pct_change(12)
    infl_up = (yoy - yoy.shift(6)) > 0
    # CPI for month M is published mid-month M+1: on day d use the latest month <= d - 45 days
    avail = pd.Series(infl_up.to_numpy(), index=infl_up.index + pd.DateOffset(days=45)).sort_index()
    infl = avail.reindex(index, method="ffill")
    reg = pd.DataFrame(index=index)
    reg["A"] = trend.reindex(index) + "/" + np.where(vix.reindex(index) >= 20, "vix>=20", "vix<20")
    reg["B"] = trend.reindex(index) + "/" + np.where(infl.fillna(False).astype(bool), "infl rising", "infl falling")
    return reg


def scale_to_vol(strats: pd.DataFrame) -> pd.DataFrame:
    vol = strats.rolling(60, min_periods=40).std().shift(1) * np.sqrt(252)
    return (strats * (TARGET_VOL / vol).clip(upper=5.0)).dropna()


def portfolio(scaled: pd.DataFrame, weights: pd.DataFrame) -> pd.Series:
    return (scaled * weights.reindex(scaled.index).fillna(0.0)).sum(axis=1)


def ex_ante_weights(regime: pd.Series, mapping: Dict[str, List[str]]) -> pd.DataFrame:
    w = pd.DataFrame(0.0, index=regime.index, columns=STRATS)
    for reg, names in mapping.items():
        w.loc[regime == reg, names] = 1.0 / len(names)
    return w


def learned_weights(scaled: pd.DataFrame, regime: pd.Series, years: List[int], shrink_days: float = 500.0,
                    use_regime: bool = True) -> pd.DataFrame:
    """Each January: per regime, mu = shrink(regime mean -> overall mean, n/(n+k)); w ~ max(mu,0)/var."""
    w = pd.DataFrame(0.0, index=scaled.index, columns=STRATS)
    yr = scaled.index.year
    for y in years:
        past = scaled[yr < y]
        reg_p = regime.reindex(past.index)
        mu_all, var = past.mean(), past.var()
        for reg in regime.dropna().unique():
            if use_regime:
                sub = past[reg_p == reg]
                n = len(sub)
                mu = (n / (n + shrink_days)) * sub.mean().fillna(0) + (shrink_days / (n + shrink_days)) * mu_all
            else:
                mu = mu_all
            raw = (mu.clip(lower=0) / var).fillna(0)
            wt = raw / raw.sum() if raw.sum() > 0 else raw
            mask = (yr == y) & (regime.reindex(scaled.index) == reg).to_numpy()
            w.loc[mask, :] = wt.to_numpy()
    return w


def stats(r: pd.Series) -> Dict[str, float]:
    r = r.dropna()
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    return {"Sharpe": r.mean() / r.std() * np.sqrt(252), "ann_ret_%": (eq.iloc[-1] ** (1 / yrs) - 1) * 100,
            "ann_vol_%": r.std() * np.sqrt(252) * 100, "max_dd_%": (eq / eq.cummax() - 1).min() * 100}


PERIODS = {"OOS 2011-26": ("2011-01-01", "2100-01-01"), "2011-18": ("2011-01-01", "2018-12-31"),
           "2019-26": ("2019-01-01", "2100-01-01"), "2020": ("2020-01-01", "2020-12-31"),
           "2022": ("2022-01-01", "2022-12-31"), "2024-05+": ("2024-05-01", "2100-01-01")}


def table(series: Dict[str, pd.Series]) -> pd.DataFrame:
    rows = {}
    for name, r in series.items():
        row = {}
        for p, (a, b) in PERIODS.items():
            s = r[(r.index >= a) & (r.index <= b)]
            row[f"Sharpe {p}"] = stats(s)["Sharpe"] if len(s) > 20 else np.nan
        full = stats(r[r.index >= "2011-01-01"])
        row["ann_ret_% 11-26"], row["max_dd_% 11-26"] = full["ann_ret_%"], full["max_dd_%"]
        rows[name] = row
    return pd.DataFrame(rows).T


def run() -> Dict[str, pd.DataFrame]:
    # Keep only dates where every series printed: a gap in SPY would otherwise blank the 200-day
    # SMA for 200 sessions and silently label them "down".
    px = load_daily().dropna(subset=TICKERS)
    strats = build_strategies(px)
    scaled = scale_to_vol(strats)
    reg = build_regimes(px, load_cpi(), scaled.index)
    years = list(range(2011, scaled.index[-1].year + 1))
    out: Dict[str, pd.DataFrame] = {}
    out["strategies"] = table({s: scaled[s] for s in STRATS})
    series = {"static equal-risk (all 8)": portfolio(scaled, pd.DataFrame(1 / len(STRATS), index=scaled.index, columns=STRATS)),
              "learned, no regime": portfolio(scaled, learned_weights(scaled, reg["A"], years, use_regime=False))}
    for scheme in ("A", "B"):
        series[f"ex-ante map, regime {scheme}"] = portfolio(scaled, ex_ante_weights(reg[scheme], EX_ANTE[scheme]))
        series[f"learned walk-forward, regime {scheme}"] = portfolio(scaled, learned_weights(scaled, reg[scheme], years))
    series["SPY (EQ, 10% vol)"] = scaled["EQ"]
    out["portfolios"] = table(series)
    for scheme in ("A", "B"):
        g = scaled[scaled.index >= "2007-06-01"].join(reg[scheme].rename("regime"))
        g["half"] = np.where(g.index.year <= 2016, "07-16", "17-26")
        sh = g.groupby(["regime", "half"])[STRATS].agg(lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan).round(2)
        out[f"by_regime_{scheme}"] = sh
        out[f"days_{scheme}"] = g.groupby(["regime", "half"]).size().unstack()
    out["today"] = reg.tail(1)
    return out


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="results/opening_reversal/REGIME_PORTFOLIO.md")
    args = p.parse_args(argv)
    res = run()

    def md(df):
        try:
            return df.to_markdown(floatfmt=".2f")
        except ImportError:
            return "```\n" + df.round(2).to_string() + "\n```"

    lines = ["# Different strategies for different regimes (daily, 2007-2026)", "",
             "All series are daily excess returns over T-bills, each strategy scaled to 10% vol on trailing data.", ""]
    for k in ("strategies", "portfolios"):
        lines += [f"## {k}", "", md(res[k]), ""]
    for scheme in ("A", "B"):
        lines += [f"## Sharpe by regime {scheme} (descriptive, two halves)", "", md(res[f"by_regime_{scheme}"]), "",
                  md(res[f"days_{scheme}"]), ""]
    lines += ["## Regime today", "", md(res["today"]), ""]
    text = "\n".join(lines)
    Path(args.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
