"""What separates winning opening-reversal shorts from losing ones — and can we trade only the
winners' pattern out of sample?

    python -m tradingagents.strategies.opening_reversal.patterns

Candidates are deliberately broad: on *every* session, the first rally-then-reversal short in the
first hour (gap, volume exhaustion and supply zone are recorded as features instead of being
required). For each candidate ~25 features known at the entry bar's open are recorded.

1. Winners vs losers: per feature, Spearman correlation with the trade's R and winner/loser
   medians, separately for an early and a late period. Only differences present in both periods
   are worth anything.
2. Walk-forward filter: each year, a shallow regression tree is fitted on earlier years only;
   that year's candidates are traded only when they land in a leaf whose historical mean R is
   positive. Out-of-sample results are compared with taking every candidate.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .backtest import eligible_contexts, simulate_short
from .config import StrategyParams
from .data import load_alpaca_minutes
from .levels import DayContext, build_day_contexts
from .regime import attach_vix, load_vix
from .signals import Signal, find_signal

# Features fed to the model (all known at the entry bar's open). Descriptions are for the report.
FEATURES: Dict[str, str] = {
    "gap_pct": "open vs prior close, %",
    "gap_atr": "gap in units of 14-day ATR",
    "entry_minute": "minutes after 09:30 of the entry",
    "drop_pct": "open -> morning low, %",
    "rally_pct": "morning low -> rally high, %",
    "rally_bars": "bars from low to rally high",
    "retrace_of_drop": "rally size / opening drop (1 = back to the open)",
    "high_vs_open_pct": "rally high vs open, %",
    "high_vs_prev_close_pct": "rally high vs prior close, %",
    "vwap_dist_pct": "entry vs session VWAP, %",
    "exhaustion_ratio": "late / early rally relative volume",
    "relvol_session": "mean relative volume so far today",
    "relvol_signal": "relative volume of the reversal bar",
    "signal_range_pct": "reversal bar high-low, %",
    "signal_body_frac": "reversal bar body / range",
    "risk_pct": "stop distance, %",
    "risk_atr": "stop distance in ATR units",
    "near_level_pct": "rally high distance to nearest prior-day/premarket level, %",
    "above_premarket_high": "rally high above pre-market high (0/1)",
    "vix_prev": "prior-day VIX close",
    "dist_sma20_pct": "prior close vs 20-day SMA, %",
    "dist_sma50_pct": "prior close vs 50-day SMA, %",
    "ret_1d_pct": "prior day return, %",
    "ret_5d_pct": "prior 5-day return, %",
    "atr14_pct": "14-day ATR, % of price",
    "weekday": "0 = Monday",
}


def candidate_params() -> StrategyParams:
    return replace(StrategyParams(), require_gap_down=False, gap_filter="any",
                   require_exhaustion=False, require_zone=False)


def extract_features(ctx: DayContext, sig: Signal) -> Dict[str, float]:
    bars = ctx.rth
    o, h, l, c = (bars[k].to_numpy() for k in ("open", "high", "low", "close"))
    v = bars["volume"].to_numpy()
    rv = bars["rel_vol"].to_numpy(dtype=float)
    i = sig.signal_idx
    low_idx = int(np.argmin(l[: i + 1]))
    high_idx = low_idx + int(np.argmax(h[low_idx : i + 1]))
    lo, hi, op = sig.rally_low, sig.rally_high, ctx.open
    typical = (h[: i + 1] + l[: i + 1] + c[: i + 1]) / 3.0
    vwap = float((typical * v[: i + 1]).sum() / max(v[: i + 1].sum(), 1.0))
    f = ctx.features
    atr = f.get("atr14_pct", np.nan)
    risk = (sig.stop - sig.entry_price) / sig.entry_price
    levels = [x for x in ctx.levels.values() if x]
    pm_high = ctx.levels.get("premarket_high", np.nan)
    entry_ts = bars.index[sig.entry_idx]
    return {
        "gap_pct": ctx.gap_pct * 100,
        "gap_atr": ctx.gap_pct / atr if atr and not np.isnan(atr) else np.nan,
        "entry_minute": (entry_ts.hour * 60 + entry_ts.minute) - 570,
        "drop_pct": (op - lo) / op * 100,
        "rally_pct": (hi / lo - 1) * 100,
        "rally_bars": high_idx - low_idx,
        "retrace_of_drop": (hi - lo) / (op - lo) if op - lo > 1e-9 else np.nan,
        "high_vs_open_pct": (hi / op - 1) * 100,
        "high_vs_prev_close_pct": (hi / ctx.prev_close - 1) * 100,
        "vwap_dist_pct": (sig.entry_price / vwap - 1) * 100,
        "exhaustion_ratio": sig.exhaustion_ratio if sig.exhaustion_ratio is not None else np.nan,
        "relvol_session": float(np.nanmean(rv[: i + 1])),
        "relvol_signal": rv[i],
        "signal_range_pct": (h[i] - l[i]) / c[i] * 100,
        "signal_body_frac": (o[i] - c[i]) / (h[i] - l[i]) if h[i] > l[i] else 0.0,
        "risk_pct": risk * 100,
        "risk_atr": risk / atr if atr and not np.isnan(atr) else np.nan,
        "near_level_pct": min(abs(hi / x - 1) for x in levels) * 100 if levels else np.nan,
        "above_premarket_high": float(hi >= pm_high) if not np.isnan(pm_high) else np.nan,
        "vix_prev": f.get("vix_prev", np.nan),
        "dist_sma20_pct": (ctx.prev_close / f["sma20"] - 1) * 100 if not np.isnan(f.get("sma20", np.nan)) else np.nan,
        "dist_sma50_pct": (ctx.prev_close / f["sma50"] - 1) * 100 if not np.isnan(f.get("sma50", np.nan)) else np.nan,
        "ret_1d_pct": f.get("ret_1d", np.nan) * 100,
        "ret_5d_pct": f.get("ret_5d", np.nan) * 100,
        "atr14_pct": atr * 100,
        "weekday": float(ctx.day.weekday()),
    }


def candidate_table(contexts: List[DayContext], params: StrategyParams) -> pd.DataFrame:
    rows = []
    for ctx in contexts:
        sig = find_signal(ctx, params)
        if sig is None:
            continue
        trade = simulate_short(ctx, sig, params)
        rows.append({"date": trade["date"], "r": trade["r_multiple"], **extract_features(ctx, sig)})
    df = pd.DataFrame(rows)
    df["win"] = (df["r"] > 0).astype(int)
    # Outcome with the fixed per-fill slippage removed (-1 / 0 / +0.5 / +1 / +1.5 ...). Ranking raw R
    # would reward wide stops spuriously: the same 1-cent slippage is a larger fraction of a tight
    # stop, so among equal outcomes raw R sorts by stop width.
    df["r_bucket"] = (df["r"] * 2).round() / 2
    return df


def _spearman(x: pd.Series, y: pd.Series) -> float:
    ok = x.notna() & y.notna()
    return x[ok].rank().corr(y[ok].rank()) if ok.sum() > 10 else np.nan


def feature_stability(df: pd.DataFrame, split: date) -> pd.DataFrame:
    early = df[pd.to_datetime(df["date"]) < pd.Timestamp(split)]
    late = df[pd.to_datetime(df["date"]) >= pd.Timestamp(split)]
    rows = []
    for feat, desc in FEATURES.items():
        r_early, r_late = _spearman(early[feat], early["r_bucket"]), _spearman(late[feat], late["r_bucket"])
        rows.append({
            "feature": feat,
            "meaning": desc,
            "corr_with_R_early": r_early,
            "corr_with_R_late": r_late,
            "same_sign": bool(np.sign(r_early) == np.sign(r_late)),
            "winners_median_early": early.loc[early.win == 1, feat].median(),
            "losers_median_early": early.loc[early.win == 0, feat].median(),
            "winners_median_late": late.loc[late.win == 1, feat].median(),
            "losers_median_late": late.loc[late.win == 0, feat].median(),
        })
    out = pd.DataFrame(rows)
    out["min_abs_corr"] = np.where(out["same_sign"],
                                   np.minimum(out["corr_with_R_early"].abs(), out["corr_with_R_late"].abs()), 0.0)
    return out.sort_values("min_abs_corr", ascending=False)


def walk_forward_tree(df: pd.DataFrame, years: List[int], max_depth: int = 2, min_leaf: int = 40,
                      min_edge: float = 0.0) -> Tuple[pd.DataFrame, Dict[int, str]]:
    """Each year: fit a regression tree on R using earlier years only; trade the year's candidates
    whose leaf has a training mean R > ``min_edge``. Returns (traded rows, tree text per year)."""
    from sklearn.tree import DecisionTreeRegressor, export_text

    feats = list(FEATURES)
    df = df.assign(year=pd.to_datetime(df["date"]).dt.year)
    traded, trees = [], {}
    for year in years:
        train, test = df[df["year"] < year], df[df["year"] == year]
        if train.empty or test.empty:
            continue
        fill = train[feats].median()
        model = DecisionTreeRegressor(max_depth=max_depth, min_samples_leaf=min_leaf, random_state=0)
        model.fit(train[feats].fillna(fill), train["r"])
        pred = model.predict(test[feats].fillna(fill))
        traded.append(test[pred > min_edge])
        trees[year] = export_text(model, feature_names=feats, decimals=2)
    return (pd.concat(traded) if traded else df.iloc[0:0]), trees


def walk_forward_score(df: pd.DataFrame, years: List[int], top_frac: float = 0.3, min_abs_corr: float = 0.05,
                       sign_agreement: float = 0.75) -> Tuple[pd.DataFrame, Dict[int, List[str]]]:
    """Each year, using earlier years only: keep features whose rank correlation with the outcome
    has the same sign in >= ``sign_agreement`` of past years and |overall corr| >= ``min_abs_corr``;
    score = sum(sign * z-score); trade the year's candidates scoring in the past top ``top_frac``."""
    feats = list(FEATURES)
    df = df.assign(year=pd.to_datetime(df["date"]).dt.year)
    traded, chosen = [], {}
    for year in years:
        train, test = df[df["year"] < year], df[df["year"] == year]
        if train["year"].nunique() < 2 or test.empty:
            continue
        signs = {}
        for f in feats:
            overall = _spearman(train[f], train["r_bucket"])
            if np.isnan(overall) or abs(overall) < min_abs_corr:
                continue
            per_year = [_spearman(g[f], g["r_bucket"]) for _, g in train.groupby("year")]
            per_year = [x for x in per_year if not np.isnan(x)]
            if per_year and np.mean(np.sign(per_year) == np.sign(overall)) >= sign_agreement:
                signs[f] = np.sign(overall)
        chosen[year] = [f"{'+' if s > 0 else '-'}{f}" for f, s in signs.items()]
        if not signs:
            continue
        mu, sd = train[list(signs)].mean(), train[list(signs)].std().replace(0, np.nan)

        def score(frame):
            z = ((frame[list(signs)] - mu) / sd).fillna(0.0)
            return (z * pd.Series(signs)).sum(axis=1)

        cut = score(train).quantile(1 - top_frac)
        traded.append(test[score(test) >= cut])
    return (pd.concat(traded) if traded else df.iloc[0:0]), chosen


def _summary(r: pd.Series, days: int) -> dict:
    n = len(r)
    sd = r.std(ddof=1) if n > 1 else np.nan
    return {
        "trades": n,
        "% of sessions": n / days * 100 if days else np.nan,
        "win_%": (r > 0).mean() * 100 if n else np.nan,
        "avg_R": r.mean() if n else np.nan,
        "total_R": r.sum(),
        "t": r.mean() / (sd / np.sqrt(n)) if n > 2 and sd > 0 else np.nan,
    }


def _md(df: pd.DataFrame, index: bool = True, fmt: str = ".2f") -> str:
    try:
        return df.to_markdown(index=index, floatfmt=fmt)
    except ImportError:
        return "```\n" + df.round(2).to_string(index=index) + "\n```"


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--symbol", default="SPY")
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    p.add_argument("--split", type=date.fromisoformat, default=date(2023, 1, 1))
    p.add_argument("--first-test-year", type=int, default=2021)
    p.add_argument("--out", type=Path, default=Path("results/opening_reversal"))
    args = p.parse_args(argv)

    minutes = load_alpaca_minutes(args.symbol, args.start - timedelta(days=120), args.end, verbose=False)
    contexts = [c for c in eligible_contexts(build_day_contexts(minutes)) if args.start <= c.day.date() <= args.end]
    attach_vix(contexts, load_vix(args.start - timedelta(days=120), args.end))
    df = candidate_table(contexts, candidate_params())
    df.to_csv(args.out / "pattern_candidates.csv", index=False)
    years = list(range(args.first_test_year, args.end.year + 1))
    days_per_year = pd.Series([c.day.year for c in contexts]).value_counts()
    oos_days = int(days_per_year.reindex(years).fillna(0).sum())
    print(f"{len(contexts)} sessions, {len(df)} candidates, {df['win'].mean() * 100:.1f}% winners")

    stability = feature_stability(df, args.split)
    oos_all = df[pd.to_datetime(df["date"]).dt.year.isin(years)]
    rows = {"take every candidate": _summary(oos_all["r"], oos_days)}
    gap_down = oos_all[oos_all["gap_pct"] <= -0.15]
    rows["gap-down candidates only (>= 0.15%)"] = _summary(gap_down["r"], oos_days)
    trees = {}
    for depth, leaf in ((1, 60), (2, 40), (3, 30)):
        traded, t = walk_forward_tree(df, years, max_depth=depth, min_leaf=leaf)
        rows[f"walk-forward tree depth {depth} (leaf >= {leaf})"] = _summary(traded["r"], oos_days)
        trees[depth] = t
    chosen_features = {}
    for frac in (0.3, 0.15):
        traded, chosen = walk_forward_score(df, years, top_frac=frac)
        rows[f"walk-forward stable-feature score, top {frac:.0%}"] = _summary(traded["r"], oos_days)
        chosen_features = chosen if frac == 0.3 else chosen_features
    comp = pd.DataFrame(rows).T
    print(comp.round(3).to_string())

    traded2, _ = walk_forward_tree(df, years, max_depth=2, min_leaf=40)
    yearly = pd.DataFrame({
        "every candidate": oos_all.assign(y=pd.to_datetime(oos_all["date"]).dt.year).groupby("y")["r"].sum(),
        "tree depth 2": traded2.assign(y=pd.to_datetime(traded2["date"]).dt.year).groupby("y")["r"].sum(),
        "tree depth 2 trades": traded2.assign(y=pd.to_datetime(traded2["date"]).dt.year).groupby("y").size(),
    }).reindex(years).fillna(0)

    cols = ["feature", "meaning", "corr_with_R_early", "corr_with_R_late", "winners_median_early",
            "losers_median_early", "winners_median_late", "losers_median_late"]
    lines = [
        "# Winning vs losing opening-reversal shorts",
        "",
        f"- **Candidates**: first rally-then-reversal short (09:35-10:30) on every session, "
        f"{args.start} to {args.end}: {len(df)} trades, {df['win'].mean() * 100:.1f}% winners, "
        f"avg {df['r'].mean():+.3f}R",
        f"- **Early / late periods** for the comparison: before / from {args.split}",
        f"- **Walk-forward** test years: {years[0]}-{years[-1]} ({oos_days} sessions); every rule is learned "
        "from earlier years only",
        f"- **Generated**: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## Out-of-sample: trade only when the learned pattern says so",
        "",
        _md(comp),
        "",
        "Total R by year:",
        "",
        _md(yearly),
        "",
        "## Winners vs losers — features sorted by how consistently they relate to R",
        "",
        "`corr_with_R` is the Spearman rank correlation between the feature and the trade's R. "
        "A feature only matters if the sign is the same in both periods and the size is not tiny.",
        "",
        _md(stability[cols], index=False),
        "",
        "## Features the stable-feature score picked each year (from earlier years only)",
        "",
        *(f"- **{y}**: {', '.join(f) if f else '(none)'}" for y, f in chosen_features.items()),
        "",
        f"## Latest tree (trained on {args.start.year}..{years[-1] - 1}) — depth 2",
        "",
        "```",
        trees[2].get(years[-1], ""),
        "```",
        "",
    ]
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / "PATTERNS.md"
    path.write_text("\n".join(lines))
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
