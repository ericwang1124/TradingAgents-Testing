"""Which combination of score items works? Exhaustive search with two-fold validation.

    python -m tradingagents.strategies.vcp.combos

Fifteen ingredients: the twelve score items of vcp.leaders and three market states on the day before
the breakout (environment E >= 3, reversal window, at least half of recent breakouts held). Written
and committed before it was run.

1. Outcome of an event: the R multiple (profit / initial risk) of the trade it produces under the
   two confirmed entries, simulated with tiny positions and no risk reductions so that every eligible
   event trades and no trade depends on another. Events that never trigger a trade have no outcome.
2. A combination is any non-empty subset of the fifteen (32,767 of them). Its score is the sum of its
   items; it picks the events at or above the 75th percentile of the training period's events.
3. Two folds: train 2017-2021 / test 2022-2026, and the reverse. Within a fold, combinations with at
   least 40 traded picks in training are ranked by the t-statistic of their mean R in training.
4. What is reported, per fold:
   - the best combination in training and what it did in the test period;
   - the test-period mean R of the top 1% by training rank, against all combinations - if searching
     for combinations is worth anything, the top 1% must beat the typical combination out of sample;
   - the rank correlation between training and test t-statistics across all combinations;
   - how often each ingredient appears in the top 1%.
5. Consensus: ingredients present in at least half of the top 1% in both folds. It is run through
   the full portfolio simulator, as are the two fold winners on their test periods. The consensus
   uses both periods, so its backtest is in-sample; only the fold winners' test runs are out of sample.

Caveat: both periods have been looked at before (see vcp.jlaw_flex and vcp.leaders). The search itself
is mechanical and each fold's selection uses its training period only.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from . import jlaw as jl
from . import jlaw_flex as jf
from . import leaders as ld

OUT = Path("results/opening_reversal/VCP_COMBOS.md")
MARKET = ["mkt: environment", "mkt: reversal", "mkt: breakouts holding"]
INGREDIENTS = ld.ALL_ITEMS + MARKET
MIN_PICKS = 40
TOP_SHARE = 0.01


def event_outcomes(ctx, ev: pd.DataFrame) -> pd.DataFrame:
    """One trade per eligible event, sized so small that capital never binds."""
    spy, spy_vol, rf = ctx["mkt"]
    p = replace(ctx["base"], entry="flex", risk=0.01, max_pos=0.012, throttle=False, dist_days=False, start=jf.DEV[0], end=None)
    mask = ld.mask_from(ctx, ev, np.ones(len(ev), dtype=bool))
    tr = jl.simulate(ctx["ind"], jf.to_by_day(ctx["S"], mask), spy, spy_vol, rf, p)["trades"]
    dates = ctx["ind"]["C"].index
    pos = pd.Series(np.arange(len(dates)), index=dates)
    out = pd.DataFrame({"R": np.nan, "kind": None}, index=ev.index)
    by_col: Dict[str, pd.DataFrame] = {c: g.sort_values("b") for c, g in ev.groupby("col")}
    window = ctx["base"].pb_window + ctx["base"].arm_days
    for sym, day, kind, R in zip(tr["symbol"], tr["entry_date"], tr["kind"], tr["R_mult"]):
        g = by_col.get(sym)
        if g is None:
            continue
        i = int(pos[day])
        cand = g[g["b"] == i] if kind == "breakout" else g[(g["b"] < i) & (g["b"] >= i - window)]
        if len(cand):
            e = cand.index[-1]
            if np.isnan(out.at[e, "R"]):
                out.at[e, "R"], out.at[e, "kind"] = R, kind
    return out


def ingredient_matrix(items: pd.DataFrame, ev: pd.DataFrame, mk: pd.DataFrame) -> pd.DataFrame:
    prev = ev["b"].to_numpy() - 1
    X = items[ld.ALL_ITEMS].copy()
    X[MARKET[0]] = (mk["E"].to_numpy()[prev] >= 3).astype(float)
    X[MARKET[1]] = mk["reversal"].to_numpy()[prev].astype(float)
    X[MARKET[2]] = (np.nan_to_num(mk["follow"].to_numpy()[prev], nan=0.0) >= 0.5).astype(float)
    return X


def all_subsets(k: int) -> np.ndarray:
    n = np.arange(1, 2 ** k, dtype=np.uint32)
    return ((n[:, None] >> np.arange(k)) & 1).astype(np.float32)          # (2^k - 1, k)


def evaluate(X: np.ndarray, R: np.ndarray, train: np.ndarray, test: np.ndarray, B: np.ndarray, chunk: int = 4096) -> pd.DataFrame:
    """For every subset: picks by its training cutoff, then n / mean R / t in training and test."""
    has = ~np.isnan(R)
    R0 = np.where(has, R, 0.0)
    cols = {k: [] for k in ("n_tr", "mean_tr", "t_tr", "n_te", "mean_te", "t_te")}
    for s in range(0, len(B), chunk):
        sc = X @ B[s:s + chunk].T                                          # events x subsets
        cut = np.quantile(sc[train], 0.75, axis=0)
        pick = sc >= cut[None, :] - 1e-9
        for tag, rows in (("tr", train), ("te", test)):
            m = pick & (rows & has)[:, None]
            n = m.sum(axis=0)
            sm = (m * R0[:, None]).sum(axis=0)
            sq = (m * (R0 ** 2)[:, None]).sum(axis=0)
            mean = np.divide(sm, n, out=np.full(len(n), np.nan), where=n > 0)
            var = np.divide(sq - n * mean ** 2, n - 1, out=np.full(len(n), np.nan), where=n > 1)
            with np.errstate(invalid="ignore", divide="ignore"):
                t = mean / np.sqrt(var / n)
            cols[f"n_{tag}"].append(n); cols[f"mean_{tag}"].append(mean); cols[f"t_{tag}"].append(t)
    return pd.DataFrame({k: np.concatenate(v) for k, v in cols.items()})


def name_of(b: np.ndarray, names: List[str]) -> str:
    return " + ".join(n for n, x in zip(names, b) if x > 0)


def fold_report(res: pd.DataFrame, B: np.ndarray, names: List[str]) -> Dict[str, object]:
    ok = res["n_tr"] >= MIN_PICKS
    r = res[ok]
    order = r["t_tr"].sort_values(ascending=False)
    top = order.index[:max(int(len(r) * TOP_SHARE), 1)]
    best = order.index[0]
    rank = r[["t_tr", "t_te"]].rank()
    return {"eligible": int(ok.sum()), "best": int(best), "best_name": name_of(B[best], names), "best_row": res.loc[best],
            "top_mean_te": float(res.loc[top, "mean_te"].mean()), "top_pos_share": float((res.loc[top, "mean_te"] > 0).mean()),
            "top_t_te": float(res.loc[top, "t_te"].mean()),
            "all_mean_te": float(r["mean_te"].median()), "all_q25": float(r["mean_te"].quantile(0.25)), "all_q75": float(r["mean_te"].quantile(0.75)),
            "best_pctile_te": float((r["mean_te"] < res.loc[best, "mean_te"]).mean() * 100),
            "top_pctile_te": float((r["mean_te"] < res.loc[top, "mean_te"].mean()).mean() * 100),
            "spearman": float(rank["t_tr"].corr(rank["t_te"])),
            "freq": pd.Series(B[top].mean(axis=0), index=names), "top": top,
            "size_top": float(B[top].sum(axis=1).mean())}


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    ctx, ev, items, mk, in_dev = ld.build()
    out = event_outcomes(ctx, ev)
    X = ingredient_matrix(items, ev, mk)
    B = all_subsets(X.shape[1])
    names = list(X.columns)
    R = out["R"].to_numpy(dtype=float)
    dev, hold = in_dev.to_numpy(), ~in_dev.to_numpy() & (ev["day"] >= jf.HOLD[0]).to_numpy()
    A = evaluate(X.to_numpy(dtype=np.float32), R, dev, hold, B)           # train dev, test holdout
    Bk = evaluate(X.to_numpy(dtype=np.float32), R, hold, dev, B)          # train holdout, test dev
    fa, fb = fold_report(A, B, names), fold_report(Bk, B, names)
    base = {"all events (no selection)": (np.nanmean(R[dev]), np.nanmean(R[hold]), int((~np.isnan(R[dev])).sum()), int((~np.isnan(R[hold])).sum()))}
    seven = (B[:, :7].sum(axis=1) == 7) & (B[:, 7:].sum(axis=1) == 0)
    twelve = (B[:, :12].sum(axis=1) == 12) & (B[:, 12:].sum(axis=1) == 0)
    freq = pd.DataFrame({"train 2017-21": fa["freq"], "train 2022-26": fb["freq"]})
    consensus = [n for n in names if freq.loc[n].min() >= 0.5]
    cons_b = np.array([1.0 if n in consensus else 0.0 for n in names], dtype=np.float32)
    cons_i = int(np.flatnonzero((B == cons_b).all(axis=1))[0]) if consensus else None

    def line(label, f, res, tr, te):
        b = f["best_row"]
        return [f"### Train {tr}, test {te}", "",
                f"- Combinations with at least {MIN_PICKS} traded picks in training: {f['eligible']:,}.",
                f"- Best in training: **{f['best_name']}** - training {int(b['n_tr'])} trades, {b['mean_tr']:+.2f}R (t = {b['t_tr']:.2f}); "
                f"test {int(b['n_te'])} trades, **{b['mean_te']:+.2f}R (t = {b['t_te']:.2f})**, better than {f['best_pctile_te']:.0f}% of all combinations in the test period.",
                f"- Top 1% in training ({len(f['top'])} combinations, {f['size_top']:.1f} ingredients on average): test mean {f['top_mean_te']:+.2f}R, "
                f"average t {f['top_t_te']:.2f}, {f['top_pos_share'] * 100:.0f}% positive; better than {f['top_pctile_te']:.0f}% of all combinations.",
                f"- All combinations in the test period: median {f['all_mean_te']:+.2f}R (middle half {f['all_q25']:+.2f}R to {f['all_q75']:+.2f}R).",
                f"- Rank correlation between training and test t-statistics: {f['spearman']:+.2f}.", ""]

    ref_rows = {}
    for label, sel in (("7 pattern items", seven), ("all 12 items", twelve)):
        i = int(np.flatnonzero(sel)[0])
        ref_rows[label] = {"2017-21: trades": A.loc[i, "n_tr"], "2017-21: mean R": A.loc[i, "mean_tr"], "2017-21: t": A.loc[i, "t_tr"],
                           "2022-26: trades (cutoff from 2017-21)": A.loc[i, "n_te"], "2022-26: mean R": A.loc[i, "mean_te"], "2022-26: t": A.loc[i, "t_te"]}
    if cons_i is not None:
        ref_rows["consensus: " + " + ".join(consensus)] = {
            "2017-21: trades": A.loc[cons_i, "n_tr"], "2017-21: mean R": A.loc[cons_i, "mean_tr"], "2017-21: t": A.loc[cons_i, "t_tr"],
            "2022-26: trades (cutoff from 2017-21)": A.loc[cons_i, "n_te"], "2022-26: mean R": A.loc[cons_i, "mean_te"], "2022-26: t": A.loc[cons_i, "t_te"]}
    # single ingredients and pairs, for reading
    singles = pd.DataFrame({names[k]: {"2017-21 mean R": A.loc[2 ** k - 1, "mean_tr"], "2017-21 n": A.loc[2 ** k - 1, "n_tr"],
                                       "2022-26 mean R": Bk.loc[2 ** k - 1, "mean_tr"], "2022-26 n": Bk.loc[2 ** k - 1, "n_tr"]} for k in range(len(names))}).T
    # full-portfolio confirmation
    M0 = mk["M0"].to_numpy()
    Xv = X.to_numpy(dtype=np.float32)
    def port(b_vec, train_rows, period):
        sc = Xv @ b_vec
        keep = sc >= np.quantile(sc[train_rows], 0.75) - 1e-9
        return ld.results(ctx, period, {"x": (ld.mask_from(ctx, ev, keep), M0)}).loc["x"]
    conf = {f"fold winner, trained 2017-21, run on 2022-26: {fa['best_name']}": port(B[fa["best"]], dev, jf.HOLD),
            f"fold winner, trained 2022-26, run on 2017-21: {fb['best_name']}": port(B[fb["best"]], hold, jf.DEV)}
    if cons_i is not None:
        allrows = dev | hold
        conf["consensus, 2017-21 (in-sample)"] = port(cons_b, allrows, jf.DEV)
        conf["consensus, 2022-26 (in-sample)"] = port(cons_b, allrows, jf.HOLD)
        conf["consensus, whole period (in-sample)"] = port(cons_b, allrows, (jf.DEV[0], None))
    conf["7 pattern items, whole period"] = port(B[int(np.flatnonzero(seven)[0])], dev, (jf.DEV[0], None))
    lines = ["# Combinations of score items: exhaustive search, two-fold validation", "", "```", __doc__.strip(), "```", "",
             f"Events: {len(ev)}; with a trade outcome: {int((~np.isnan(R)).sum())} ({int((~np.isnan(R[dev])).sum())} in 2017-21, "
             f"{int((~np.isnan(R[hold])).sum())} in 2022-26). Mean R of all traded events: {np.nanmean(R[dev]):+.2f} / {np.nanmean(R[hold]):+.2f}. "
             f"Combinations: {len(B):,}.", ""]
    lines += line("A", fa, A, "2017-21", "2022-26") + line("B", fb, Bk, "2022-26", "2017-21")
    lines += ["### How often each ingredient is in the top 1% (share of those combinations)", "", freq.round(2).to_markdown(), "",
              f"Consensus (at least half of the top 1% in both folds): **{' + '.join(consensus) if consensus else 'none'}**", "",
              "### Each ingredient alone (picks = events at or above its own 75th percentile; in-sample for each period)", "", singles.round(2).to_markdown(), "",
              "### Reference scores, event level", "", pd.DataFrame(ref_rows).T.round(2).to_markdown(), "",
              "### Full portfolio simulator (0.35% risk per trade, the usual limits)", "", pd.DataFrame(conf).T.round(2).to_markdown(), ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
