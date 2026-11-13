"""Walk-forward day-type selection: continuation vs reversal vs no trade, decided at 10:00.

    python -m tradingagents.strategies.day_type
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Callable, Dict, List

import numpy as np
import pandas as pd

from ..intraday_momentum.strategies import perf
from ..opening_reversal.data import load_alpaca_minutes
from ..opening_reversal.regime import load_vix
from .features import FEATURES, build_features

HORIZONS = ("noon", "close")


def dalton_rule(f: pd.DataFrame) -> pd.Series:
    """Fixed, no learning. Open drive (one-way first 30 min ending near the extreme) -> continue;
    rotational open (little net progress) -> fade; otherwise stand aside."""
    at_extreme = np.where(f["direction"] > 0, f["pos_in_or"] >= 0.8, f["pos_in_or"] <= 0.2)
    drive = (f["efficiency"] >= 0.5) & at_extreme
    rotation = f["efficiency"] < 0.2
    return pd.Series(np.where(drive, 1, np.where(rotation, -1, 0)), index=f.index)


def _sharpe(r: pd.Series) -> float:
    return r.mean() / r.std() * np.sqrt(252) if len(r) > 5 and r.std() > 0 else np.nan


def cells_model(train: pd.DataFrame, test: pd.DataFrame, horizon: str, min_n: int = 40,
                min_sharpe: float = 0.3) -> pd.Series:
    """Efficiency tercile x opening-range-width tercile (cut points from the training years);
    each cell gets continuation / reversal / nothing by its past Sharpe."""
    e_cut = train["efficiency"].quantile([1 / 3, 2 / 3]).to_numpy()
    w_cut = train["or_range_atr"].quantile([1 / 3, 2 / 3]).to_numpy()

    def cell(frame):
        return (np.digitize(frame["efficiency"], e_cut) * 3 + np.digitize(frame["or_range_atr"], w_cut))

    tr_cell, te_cell = cell(train), cell(test)
    action = {}
    for k in range(9):
        r = train.loc[tr_cell == k, f"cont_to_{horizon}"]
        s = _sharpe(r)
        if len(r) < min_n or np.isnan(s) or abs(s) < min_sharpe:
            action[k] = 0
        else:
            action[k] = 1 if s > 0 else -1
    return pd.Series([action[k] for k in te_cell], index=test.index)


def tree_model(train: pd.DataFrame, test: pd.DataFrame, horizon: str, depth: int = 2, leaf: int = 80) -> pd.Series:
    from sklearn.tree import DecisionTreeRegressor

    feats = list(FEATURES)
    fill = train[feats].median()
    m = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=leaf, random_state=0)
    m.fit(train[feats].fillna(fill), train[f"cont_to_{horizon}"])
    pred = m.predict(test[feats].fillna(fill))
    return pd.Series(np.sign(pred), index=test.index)


def linear_model(train: pd.DataFrame, test: pd.DataFrame, horizon: str) -> pd.Series:
    """Ridge on standardised features; trade only predictions stronger than the training median."""
    feats = list(FEATURES)
    mu, sd = train[feats].mean(), train[feats].std().replace(0, 1)
    X = ((train[feats] - mu) / sd).fillna(0).to_numpy()
    y = train[f"cont_to_{horizon}"].to_numpy()
    lam = 10.0
    beta = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ (y - y.mean()))
    pred_tr = X @ beta + y.mean()
    Xt = ((test[feats] - mu) / sd).fillna(0).to_numpy()
    pred = Xt @ beta + y.mean()
    cut = np.median(np.abs(pred_tr))
    return pd.Series(np.where(np.abs(pred) > cut, np.sign(pred), 0), index=test.index)


def walk_forward(f: pd.DataFrame, years: List[int], horizon: str,
                 model: Callable[[pd.DataFrame, pd.DataFrame, str], pd.Series]) -> pd.Series:
    year = pd.Series([d.year for d in f.index], index=f.index)
    actions = []
    for y in years:
        train, test = f[year < y], f[year == y]
        if len(train) < 200 or test.empty:
            continue
        actions.append(model(train, test, horizon))
    return pd.concat(actions)


def returns_from_actions(f: pd.DataFrame, actions: pd.Series, horizon: str) -> pd.Series:
    cont, rev = f.loc[actions.index, f"cont_to_{horizon}"], f.loc[actions.index, f"rev_to_{horizon}"]
    return pd.Series(np.where(actions > 0, cont, np.where(actions < 0, rev, 0.0)), index=actions.index)


def summarize(r: pd.Series) -> Dict[str, float]:
    idx = pd.to_datetime(pd.Index(r.index).astype(str))
    r = pd.Series(r.to_numpy(), index=idx)
    out = {}
    for name, (a, b) in {"OOS 2021-26": ("2021-01-01", "2100-01-01"), "2021-23": ("2021-01-01", "2023-12-31"),
                         "2024-26": ("2024-01-01", "2100-01-01"), "2024-05+": ("2024-05-01", "2100-01-01")}.items():
        out[f"Sharpe {name}"] = perf(r[(r.index >= a) & (r.index <= b)])["sharpe"]
    full = perf(r[r.index >= "2021-01-01"])
    out["ann_ret_% (1x)"] = full["ann_return_%"]
    out["max_dd_%"] = full["max_dd_%"]
    out["days traded %"] = (r[r.index >= "2021-01-01"] != 0).mean() * 100
    return out


def run(f: pd.DataFrame, years: List[int]) -> Dict[str, pd.DataFrame]:
    tables = {}
    oos = f[[d.year in years for d in f.index]]
    for h in HORIZONS:
        rows = {
            "always continuation": summarize(oos[f"cont_to_{h}"]),
            "always reversal": summarize(oos[f"rev_to_{h}"]),
            "Dalton rule (fixed)": summarize(returns_from_actions(oos, dalton_rule(oos), h)),
        }
        for name, model in {"cells: efficiency x OR width": cells_model, "tree depth 2": tree_model,
                            "ridge, top-half confidence": linear_model}.items():
            acts = walk_forward(f, years, h, model)
            rows[f"walk-forward {name}"] = summarize(returns_from_actions(f, acts, h))
        tables[h] = pd.DataFrame(rows).T
    return tables


def descriptive(f: pd.DataFrame) -> pd.DataFrame:
    """Continuation Sharpe (to noon) by efficiency tercile x OR-width tercile, early vs late."""
    g = f.copy()
    g["eff_t"] = pd.qcut(g["efficiency"], 3, labels=["low eff", "mid eff", "high eff"])
    g["w_t"] = pd.qcut(g["or_range_atr"], 3, labels=["narrow OR", "mid OR", "wide OR"])
    g["period"] = ["2019-22" if d.year <= 2022 else "2023-26" for d in g.index]
    return g.groupby(["eff_t", "w_t", "period"], observed=True)["cont_to_noon"].agg(_sharpe).unstack("period")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--first-test-year", type=int, default=2021)
    p.add_argument("--out", default="results/opening_reversal/DAY_TYPE.md")
    args = p.parse_args(argv)
    minutes = load_alpaca_minutes("SPY", args.start - timedelta(days=120), args.end, verbose=False)
    f = build_features(minutes, load_vix(args.start - timedelta(days=200), args.end))
    f = f[[d >= args.start for d in f.index]]
    years = list(range(args.first_test_year, args.end.year + 1))
    tables = run(f, years)

    def md(df):
        try:
            return df.to_markdown(floatfmt=".2f")
        except ImportError:
            return "```\n" + df.round(2).to_string() + "\n```"

    lines = ["# Day-type regimes decided at 10:00 (pre-market + first 30 minutes)", "",
             f"Sessions: {len(f)} ({f.index[0]} to {f.index[-1]}). Returns are 1x SPY, costs included; "
             "continuation = trade the 09:30-10:00 direction at 10:00.", ""]
    for h, t in tables.items():
        lines += [f"## Hold from 10:00 to {h}", "", md(t), ""]
    lines += ["## Descriptive: continuation-to-noon Sharpe by efficiency x opening-range width", "",
              md(descriptive(f)), ""]
    text = "\n".join(lines)
    with open(args.out, "w") as fh:
        fh.write(text)
    f.to_csv(args.out.replace(".md", "_features.csv"))
    print(text)


if __name__ == "__main__":
    main()
