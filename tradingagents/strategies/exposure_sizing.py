"""Robustness of scenario-based exposure sizing (scale total size by regime, don't switch strategies).

    python -m tradingagents.strategies.exposure_sizing

For a base portfolio's daily returns, each January (earlier years only) every regime state gets an
exposure multiplier m = clip(shrunk mean_state / overall mean, lo, hi), renormalised so the past
average multiplier is 1; that year's daily returns are multiplied by the state's m (2 bp per unit
of exposure change). Run for every atlas dimension, two shrinkage strengths and two clip ranges,
on five base portfolios, against two controls:
  * volatility targeting (exposure ~ 1 / trailing 20-day realised vol, same clip and renormalisation)
  * placebo: random two-state "regimes" with realistic persistence, same procedure
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .strategy_atlas import build_scenarios, build_strategies, load_cpi, load_ohlc
from .strategy_selector import INTRADAY_PREFIX, run_portfolio, scale, to_weights, walk_forward

YEARS = list(range(2011, 2027))
COST_BP = 2.0
PERIODS = {"2011-26": ("2011-01-01", "2100-01-01"), "2019-26": ("2019-01-01", "2100-01-01"),
           "2024-05+": ("2024-05-01", "2100-01-01")}


def sharpe(r: pd.Series) -> float:
    r = r.dropna()
    return r.mean() / r.std() * np.sqrt(252) if len(r) > 20 and r.std() > 0 else np.nan


def regime_multiplier(base: pd.Series, regime: pd.Series, k: float, lo: float, hi: float) -> pd.Series:
    m = pd.Series(1.0, index=base.index)
    yr = base.index.year
    reg = regime.reindex(base.index)
    for y in YEARS:
        past = base[yr < y].dropna()
        if len(past) < 500:
            continue
        rp = reg.reindex(past.index)
        mu = past.mean()
        if mu <= 0:
            continue
        mult = {}
        for st, g in past.groupby(rp):
            n = len(g)
            mult[st] = float(np.clip(((n / (n + k)) * g.mean() + (k / (n + k)) * mu) / mu, lo, hi))
        avg = sum(mult[s] * (rp == s).sum() for s in mult) / max(rp.notna().sum(), 1)
        cur = yr == y
        m[cur] = reg[cur].map({s: v / avg for s, v in mult.items()}).fillna(1.0).astype(float).to_numpy()
    return m


def vol_target_multiplier(base: pd.Series, lo: float, hi: float) -> pd.Series:
    rv = base.rolling(20, min_periods=15).std().shift(1)
    raw = (1.0 / rv).replace([np.inf, -np.inf], np.nan)
    m = pd.Series(1.0, index=base.index)
    yr = base.index.year
    for y in YEARS:
        past = raw[yr < y].dropna()
        if len(past) < 500:
            continue
        norm = past.median()
        cur = yr == y
        m[cur] = (raw[cur] / norm).clip(lo, hi).fillna(1.0).to_numpy()
    return m


def apply(base: pd.Series, m: pd.Series) -> pd.Series:
    return base * m - m.diff().abs().fillna(0.0) * COST_BP / 1e4


def placebo_regimes(index: pd.DatetimeIndex, n: int, p_stay: float, seed: int = 0) -> List[pd.Series]:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        flips = rng.random(len(index)) > p_stay
        state = np.cumsum(flips) % 2
        out.append(pd.Series(np.where(state == 0, "x", "y"), index=index))
    return out


def persistence(sc: pd.DataFrame) -> float:
    stays = [(sc[c] == sc[c].shift(1)).mean() for c in sc.columns]
    return float(np.median(stays))


def bases(S: pd.DataFrame) -> Dict[str, pd.Series]:
    Sx = scale(S)
    daily = [c for c in Sx.columns if not c.startswith(INTRADAY_PREFIX)]
    X = Sx[daily]
    mu = walk_forward(X, pd.DataFrame(index=X.index), YEARS, "none", 0)
    w = to_weights(mu, X.notna())
    out = {"core basket (positive-edge strategies)": run_portfolio(X, w)}
    core8 = ["long SPY", "SPY trend: above SMA200", "trend: TSMOM SPY/TLT/GLD/DBC", "MR: RSI(2)<10 until RSI(2)>70",
             "long bonds TLT", "long gold", "long commodities DBC", "put writing (Cboe PUT index)"]
    eq = X[core8].notna().astype(float)
    out["8-strategy equal risk"] = run_portfolio(X[core8], eq.div(eq.sum(axis=1), axis=0))
    for t in ("SPY", "QQQ", "IWM"):
        out[f"{t} alone"] = X[f"long {t}"]
    return {k: v[v.index >= "2008-01-01"] for k, v in out.items()}


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="results/opening_reversal/EXPOSURE_SIZING.md")
    p.add_argument("--placebos", type=int, default=50)
    args = p.parse_args(argv)
    d = load_ohlc()
    S = build_strategies(d)
    sc = build_scenarios(d, load_cpi(), S.index)
    trend = sc["trend vs SMA200"]
    sc = sc.assign(**{"combo A: trend x VIX>=20": trend + "/" + np.where(sc["VIX level"].isin(["20-30", ">=30"]), "vix>=20", "vix<20"),
                      "combo B: trend x inflation": trend + "/" + sc["inflation direction (CPI y/y vs 6m ago)"].astype(str)})
    sc = sc.where(sc.notna() & ~sc.isin(["nan", "None", "nan/nan"]))
    base_series = bases(S)
    p_stay = persistence(sc)
    settings = [(250, 0.25, 2.0), (1000, 0.25, 2.0), (250, 0.5, 1.5), (1000, 0.5, 1.5)]

    summary, details = [], []
    for bname, base in base_series.items():
        s0 = {pn: sharpe(base[(base.index >= a) & (base.index <= b)]) for pn, (a, b) in PERIODS.items()}
        for k, lo, hi in settings:
            tag = f"k={k}, clip {lo}-{hi}"
            real = {}
            for dim in sc.columns:
                r = apply(base, regime_multiplier(base, sc[dim], k, lo, hi))
                real[dim] = {pn: sharpe(r[(r.index >= a) & (r.index <= b)]) - s0[pn] for pn, (a, b) in PERIODS.items()}
            rv = apply(base, vol_target_multiplier(base, lo, hi))
            vt = {pn: sharpe(rv[(rv.index >= a) & (rv.index <= b)]) - s0[pn] for pn, (a, b) in PERIODS.items()}
            plac = []
            for i, fake in enumerate(placebo_regimes(base.index, args.placebos, p_stay, seed=k)):
                r = apply(base, regime_multiplier(base, fake, k, lo, hi))
                plac.append(sharpe(r[r.index >= "2011-01-01"]) - s0["2011-26"])
            real_df = pd.DataFrame(real).T
            d11 = real_df["2011-26"]
            summary.append({
                "base": bname, "setting": tag, "base Sharpe 2011-26": s0["2011-26"],
                "median ΔSharpe (35+2 dims)": d11.median(), "share of dims improving": (d11 > 0).mean() * 100,
                "best dim Δ": d11.max(), "worst dim Δ": d11.min(),
                "placebo median Δ": np.median(plac), "placebo 95th pct Δ": np.percentile(plac, 95),
                "dims beating placebo 95th": int((d11 > np.percentile(plac, 95)).sum()),
                "vol-target Δ": vt["2011-26"], "dims beating vol-target": int((d11 > vt["2011-26"]).sum()),
                "median Δ 2024-05+": real_df["2024-05+"].median(),
            })
            for dim, row in real.items():
                details.append({"base": bname, "setting": tag, "dimension": dim, **{f"Δ {pn}": v for pn, v in row.items()}})
        print(f"done: {bname}", flush=True)

    summ = pd.DataFrame(summary)
    det = pd.DataFrame(details)
    # dimensions that help consistently: across all bases and settings
    agg = det.groupby("dimension")[["Δ 2011-26", "Δ 2019-26", "Δ 2024-05+"]].median()
    agg["share of (base,setting) improving"] = det.groupby("dimension")["Δ 2011-26"].apply(lambda s: (s > 0).mean() * 100)
    agg = agg.sort_values("Δ 2011-26", ascending=False)

    def md(df, index=True):
        try:
            return df.to_markdown(index=index, floatfmt=".2f")
        except ImportError:
            return "```\n" + df.round(2).to_string(index=index) + "\n```"

    lines = ["# Scenario-based exposure sizing: robustness", "",
             f"Out of sample 2011-2026 (walk-forward, yearly refit). ΔSharpe = sized portfolio minus the unsized base. "
             f"Placebo: {args.placebos} random two-state regimes with the atlas' median day-to-day persistence ({p_stay:.3f}).", "",
             "## Summary by base portfolio and setting", "", md(summ.set_index(["base", "setting"])), "",
             "## Each scenario dimension, median over bases and settings", "", md(agg), ""]
    Path(args.out).write_text("\n".join(lines))
    det.to_csv(args.out.replace(".md", "_details.csv"), index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
