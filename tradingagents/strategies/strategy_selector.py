"""Decide which strategies to apply each day from the current scenario states — walk-forward.

    python -m tradingagents.strategies.strategy_selector

Inputs come from ``strategy_atlas``: daily strategy streams and scenario states known at the prior
close. Every stream is scaled to 10% annualised volatility on trailing data. Each January, using
earlier years only, a model maps "today's scenario states" to an expected next-day return per
strategy; that year each day goes long the strategies with positive expected return, weighted by
it (cash if none). Switching costs: 2 bp per unit of weight traded.

Models
  ridge     per strategy, ridge regression of the scaled return on one-hot scenario states
  shrunk    per strategy, average over dimensions of the shrunk deviation of the conditional mean
            (state) from the unconditional mean
  no-scenario baseline  the same weighting using each strategy's unconditional past mean only
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .strategy_atlas import build_scenarios, build_strategies, load_cpi, load_ohlc

TARGET_VOL = 0.10
COST_BP = 2.0
INTRADAY_PREFIX = "intraday:"


def scale(S: pd.DataFrame) -> pd.DataFrame:
    vol = S.rolling(60, min_periods=40).std().shift(1) * np.sqrt(252)
    return S * (TARGET_VOL / vol).clip(upper=5.0)


def one_hot(sc: pd.DataFrame) -> pd.DataFrame:
    parts = [pd.get_dummies(sc[c].where(sc[c].notna() & ~sc[c].isin(["nan", "None"])), prefix=c, prefix_sep="=", dtype=float)
             for c in sc.columns]
    return pd.concat(parts, axis=1).fillna(0.0)


def ridge_mu(X: np.ndarray, y: np.ndarray, Xt: np.ndarray, lam: float) -> np.ndarray:
    ok = ~np.isnan(y)
    X, y = X[ok], y[ok]
    if len(y) < 250:
        return np.full(len(Xt), np.nan)
    mu = y.mean()
    Xc = X - X.mean(axis=0)
    beta = np.linalg.solve(Xc.T @ Xc + lam * np.eye(X.shape[1]), Xc.T @ (y - mu))
    return mu + (Xt - X.mean(axis=0)) @ beta


def shrunk_mu(sc_past: pd.DataFrame, y: pd.Series, sc_now: pd.DataFrame, k: float) -> np.ndarray:
    ok = y.notna()
    y, sc_past = y[ok], sc_past[ok]
    if len(y) < 250:
        return np.full(len(sc_now), np.nan)
    mu = y.mean()
    dev = np.zeros(len(sc_now))
    used = np.zeros(len(sc_now))
    for c in sc_past.columns:
        g = y.groupby(sc_past[c])
        n, m = g.size(), g.mean()
        shr = (n / (n + k)) * (m - mu)  # shrink the state's deviation toward 0
        d = sc_now[c].map(shr).to_numpy(dtype=float)
        has = ~np.isnan(d)
        dev[has] += d[has]
        used[has] += 1
    return mu + dev / np.maximum(used, 1)


def walk_forward(Sx: pd.DataFrame, sc: pd.DataFrame, years: List[int], model: str, param: float) -> pd.DataFrame:
    """Expected next-day return per strategy, each year fitted on earlier years only."""
    X_all = one_hot(sc)
    mu = pd.DataFrame(np.nan, index=Sx.index, columns=Sx.columns)
    yr = Sx.index.year
    for y in years:
        tr, te = yr < y, yr == y
        if not te.any():
            continue
        for s in Sx.columns:
            ytr = Sx.loc[tr, s]
            if model == "ridge":
                mu.loc[te, s] = ridge_mu(X_all.loc[tr].to_numpy(), ytr.to_numpy(), X_all.loc[te].to_numpy(), param)
            elif model == "shrunk":
                mu.loc[te, s] = shrunk_mu(sc.loc[tr], ytr, sc.loc[te], param)
            elif model == "none":
                mu.loc[te, s] = ytr.mean() if ytr.notna().sum() >= 250 else np.nan
    return mu


def vote_scores(Sx: pd.DataFrame, sc: pd.DataFrame, years: List[int]) -> pd.DataFrame:
    """Each January rebuild the atlas on earlier years only; a strategy's score on a day is
    (# of today's states flagged 'usable') - (# flagged 'avoid')."""
    from .strategy_atlas import atlas

    votes = pd.DataFrame(np.nan, index=Sx.index, columns=Sx.columns)
    yr = Sx.index.year
    for y in years:
        tr, te = yr < y, yr == y
        if not te.any():
            continue
        _, flags = atlas(Sx.loc[tr], sc.loc[tr])
        score = pd.DataFrame(0.0, index=Sx.index[te], columns=Sx.columns)
        if not flags.empty:
            for (dim, st, strat), v in flags.set_index(["scenario", "state", "strategy"])["verdict"].items():
                hit = (sc.loc[te, dim] == st).to_numpy()
                score.loc[hit, strat] += 1.0 if v == "usable" else -1.0
        votes.loc[te] = score.where(Sx.loc[te].notna()).to_numpy()
    return votes


def to_weights(mu: pd.DataFrame, available: pd.DataFrame) -> pd.DataFrame:
    m = mu.where(available).clip(lower=0).fillna(0.0)
    tot = m.sum(axis=1)
    return m.div(tot.replace(0, np.nan), axis=0).fillna(0.0)


def run_portfolio(Sx: pd.DataFrame, w: pd.DataFrame) -> pd.Series:
    gross = (Sx.fillna(0.0) * w).sum(axis=1)
    turnover = w.diff().abs().sum(axis=1).fillna(0.0)
    return gross - turnover * COST_BP / 1e4


def perf(r: pd.Series) -> Dict[str, float]:
    r = r.dropna()
    eq = (1 + r).cumprod()
    return {"Sharpe": r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan,
            "ann_ret_%": (eq.iloc[-1] ** (252 / len(r)) - 1) * 100,
            "max_dd_%": (eq / eq.cummax() - 1).min() * 100}


def evaluate(series: Dict[str, pd.Series], weights: Dict[str, pd.DataFrame], periods: Dict[str, Tuple[str, str]]) -> pd.DataFrame:
    rows = {}
    for name, r in series.items():
        row = {}
        for p, (a, b) in periods.items():
            row[f"Sharpe {p}"] = perf(r[(r.index >= a) & (r.index <= b)])["Sharpe"]
        first = list(periods.values())[0]
        full = perf(r[(r.index >= first[0]) & (r.index <= first[1])])
        row["ann_ret_%"], row["max_dd_%"] = full["ann_ret_%"], full["max_dd_%"]
        if name in weights:
            w = weights[name].loc[r.index[r.index >= first[0]]]
            row["avg # strategies"] = (w > 0).sum(axis=1).mean()
            row["daily turnover"] = w.diff().abs().sum(axis=1).mean()
        rows[name] = row
    return pd.DataFrame(rows).T


def explain_today(Sx: pd.DataFrame, sc: pd.DataFrame, k: float, top: int = 3) -> pd.DataFrame:
    """Shrunk-model view for the latest session, trained on everything before it."""
    hist, now = sc.iloc[:-1], sc.iloc[-1:]
    rows = []
    for s in Sx.columns:
        y = Sx[s].iloc[:-1]
        ok = y.notna()
        if ok.sum() < 250:
            continue
        mu, sd = y[ok].mean(), y[ok].std()
        to_sharpe = np.sqrt(252) / sd  # daily mean -> annualised Sharpe units
        contrib = []
        for c in sc.columns:
            g = y[ok].groupby(hist.loc[ok, c])
            n, m = g.size(), g.mean()
            st = now[c].iloc[0]
            if st in n.index:
                contrib.append((c, st, float(n[st] / (n[st] + k) * (m[st] - mu)) * to_sharpe))
        dev = np.mean([x[2] for x in contrib]) if contrib else 0.0
        contrib.sort(key=lambda x: -abs(x[2]))
        rows.append({"strategy": s, "unconditional Sharpe": mu * to_sharpe,
                     "scenario-adjusted Sharpe (approx.)": mu * to_sharpe + dev,
                     "main drivers": "; ".join(f"{c}={st} ({v:+.2f})" for c, st, v in contrib[:top])})
    return pd.DataFrame(rows).sort_values("scenario-adjusted Sharpe (approx.)", ascending=False)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="results/opening_reversal/STRATEGY_SELECTOR.md")
    args = p.parse_args(argv)
    d = load_ohlc()
    S = build_strategies(d)
    sc = build_scenarios(d, load_cpi(), S.index)
    Sx = scale(S)
    daily_cols = [c for c in Sx.columns if not c.startswith(INTRADAY_PREFIX)]
    available = Sx.notna()

    out_lines = ["# Which strategies to apply when — walk-forward selector", "",
                 "Each January a model is fitted on earlier years only; each day it goes long the strategies with a "
                 f"positive expected next-day return given today's scenario states (cash if none), {COST_BP:.0f} bp per unit of weight traded. "
                 "Every strategy is scaled to 10% vol. Baselines: equal risk in all strategies, and the same weighting without scenario information.", ""]

    def md(df):
        try:
            return df.to_markdown(floatfmt=".2f")
        except ImportError:
            return "```\n" + df.round(2).to_string() + "\n```"

    for label, cols, years, periods in (
        ("Daily strategies only (2011-2026 out of sample)", daily_cols, list(range(2011, 2027)),
         {"2011-26": ("2011-01-01", "2100-01-01"), "2011-18": ("2011-01-01", "2018-12-31"),
          "2019-26": ("2019-01-01", "2100-01-01"), "2022": ("2022-01-01", "2022-12-31"), "2024-05+": ("2024-05-01", "2100-01-01")}),
        ("All strategies incl. SPY intraday (2021-2026 out of sample)", list(Sx.columns), list(range(2021, 2027)),
         {"2021-26": ("2021-01-01", "2100-01-01"), "2021-23": ("2021-01-01", "2023-12-31"),
          "2024-26": ("2024-01-01", "2100-01-01"), "2022": ("2022-01-01", "2022-12-31"), "2024-05+": ("2024-05-01", "2100-01-01")}),
    ):
        X = Sx[cols]
        av = available[cols]
        series, weights = {}, {}
        w_eq = av.astype(float).div(av.sum(axis=1), axis=0)
        series["static: equal risk, all strategies"], weights["static: equal risk, all strategies"] = run_portfolio(X, w_eq), w_eq
        for name, model, param in (("no-scenario baseline (past mean)", "none", 0),
                                   ("ridge lambda=1e3", "ridge", 1e3), ("ridge lambda=1e4", "ridge", 1e4),
                                   ("shrunk k=250", "shrunk", 250), ("shrunk k=1000", "shrunk", 1000)):
            mu = walk_forward(X, sc, years, model, param)
            w = to_weights(mu, av)
            series[f"selector: {name}"], weights[f"selector: {name}"] = run_portfolio(X, w), w
        start = list(periods.values())[0][0]
        series = {k: v[v.index >= start] for k, v in series.items()}
        out_lines += [f"## {label}", "", md(evaluate(series, weights, periods)), ""]
        if label.startswith("All"):
            today = explain_today(X, sc, k=250)
            out_lines += ["## Today's view (shrunk model, trained on all history before today)", "",
                          md(today.head(15).set_index("strategy")), "", "Bottom 8:", "",
                          md(today.tail(8).set_index("strategy")), ""]
    text = "\n".join(out_lines)
    Path(args.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
