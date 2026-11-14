"""J Law's VCP, flexible version: scored setups and confirmed entries, tuned on 2017-21, tested once on 2022-26.

    python -m tradingagents.strategies.vcp.jlaw_flex             # development period only
    python -m tradingagents.strategies.vcp.jlaw_flex --holdout   # once the development choice is frozen

Why. The fixed-rule version (vcp.jlaw) has the average win and loss J Law reports (+11.5% / -4.1%) but a
30% win rate against his 45-50%. Three places where those rules were more rigid than his description:
they accept any two contractions (he speaks of three or four), they buy the first touch of the pivot
zone without waiting for the price to turn, and they treat every rule as pass/fail although he weighs
them. This version changes those three things and nothing else. Written and committed before any run.

1. Pattern. The hard limits become sanity bounds and a quality score ranks what is left.
   Bounds: at least 2 contractions, counted from the first one no deeper than 50%; that first one at
   least 8%; the last one at most 15%; base at least 15 sessions; pivot at least 3 sessions old; last
   low before today; nothing in the 250-session window deeper than 60%.
   Score, one point each, 0 to 7:
     count     3 or 4 contractions
     tight     last contraction: 1 at 6% or less, 0 at 12% or more, linear in between
     first     first contraction between 20% and 35%
     dry       volume during the last decline / 50-day average: 1 at 0.6 or less, 0 at 1.0 or more, linear
     level     earlier highs of the base within 3% above the pivot (a flat top, i.e. horizontal
               resistance): two or more = 1, one = 0.5
     catalyst  in the past 60 sessions, a day up 8% or more on at least twice its average volume
               (a price-and-volume stand-in for an earnings beat or raised guidance)
     strength  1-year return percentile: 0 at 80, 1 at 100, linear
   Traded: setups whose score is at or above the 75th percentile of all bounded setup-days of the
   development period. The cutoff comes from the score distribution, not from returns.
2. Entries, both confirmed.
   close breakout: bought at the close of a day that closes above the pivot, no more than 5% above
     it, on volume above both the prior day's and the 50-day average. Stop 1% below the last contraction low.
   confirmed pullback: after such a breakout, a quiet day back in the pivot zone with SMA10 or SMA20
     nearby (the original pullback conditions) only arms a buy-stop at that day's high. Bought when
     one of the next 3 sessions trades above it (not when it opens more than 2% above). Stop 1% below
     the lowest of the pivot, that day's low and the supporting averages.
3. Everything else is unchanged from vcp.jlaw: screen, 3-8% stops, 0.35% of equity at risk per trade,
   the two risk reductions, breakeven after +10%, SMA20 trail, SMA50 backstop, 5 bp costs.

Protocol.
  Development, 2017-01 to 2021-12. Four candidates on the scored setups:
    A touch pullback (the original entry)      B confirmed pullback
    C close breakout                           D close breakout + confirmed pullback
  The one with the highest development Sharpe among those with at least 50 trades is frozen.
  Holdout, 2022-01 to 2026-11. The frozen candidate is run once and that is the result. The other
  candidates' holdout numbers are printed for information only.

Caveat. The fixed version's whole-period results were seen before this was written, including that
three-contraction setups beat two-contraction ones in both halves. The "count" item is therefore not
a clean test on the holdout. The other six items, both entries and the cutoff rule had not been run.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from . import backtest as vb
from . import data as vdata
from . import jlaw as jl

OUT = Path("results/opening_reversal/VCP_JLAW_FLEX.md")
DEV = ("2017-01-01", "2021-12-31")
HOLD = ("2022-01-01", None)
CANDIDATES = {"A touch pullback": "pullback", "B confirmed pullback": "confirm_pullback",
              "C close breakout": "close_breakout", "D close breakout + confirmed pullback": "flex"}
MIN_TRADES = 50
SCORE_ITEMS = ["count", "tight", "first", "dry", "level", "catalyst", "strength"]


def catalyst_matrix(ind: Dict[str, pd.DataFrame]) -> np.ndarray:
    C, V, v50 = ind["C"], ind["V"], ind["v50"]
    day = (C.pct_change(fill_method=None) >= 0.08) & (V >= 2.0 * v50.shift(1))
    return day.astype(float).rolling(60, min_periods=1).max().fillna(0.0).to_numpy()


def features(S: Dict[str, np.ndarray], cat: np.ndarray) -> pd.DataFrame:
    D, HI, HV, t = S["depths"], S["his"], S["hvals"], S["t"]
    rows = np.arange(len(t))
    nval = (~np.isnan(D)).sum(axis=1)
    ok = D <= 0.50
    k = ok.argmax(axis=1)
    pivot = S["pivot"]
    cols = np.arange(D.shape[1])[None, :]
    with np.errstate(invalid="ignore"):
        earlier = (cols >= k[:, None]) & (cols < (nval - 1)[:, None]) & (HV <= pivot[:, None] * 1.03)
        deepest = np.nanmax(D, axis=1)
    return pd.DataFrame({"t": t, "j": S["j"], "has": ok.any(axis=1), "n": nval - k, "d_first": D[rows, k],
                         "d_last": D[rows, nval - 1], "deepest": deepest, "base": t - HI[rows, k],
                         "pivot_age": t - S["piv_idx"], "low_before": S["low_idx"] <= t - 1, "volr": S["volr"],
                         "rs": S["rs"], "touches": earlier.sum(axis=1), "catalyst": cat[t, S["j"]]})


def bounded(F: pd.DataFrame) -> pd.Series:
    return (F["has"] & (F["n"] >= 2) & (F["d_first"] >= 0.08) & (F["d_last"] <= 0.15) & (F["deepest"] <= 0.60)
            & (F["base"] >= 15) & (F["pivot_age"] >= 3) & F["low_before"])


def score(F: pd.DataFrame) -> pd.DataFrame:
    s = pd.DataFrame({
        "count": F["n"].isin([3, 4]).astype(float),
        "tight": ((0.12 - F["d_last"]) / 0.06).clip(0, 1),
        "first": F["d_first"].between(0.20, 0.35).astype(float),
        "dry": ((1.0 - F["volr"]) / 0.4).clip(0, 1).fillna(0.0),
        "level": F["touches"].clip(upper=2) / 2.0,
        "catalyst": (F["catalyst"] > 0).astype(float),
        "strength": ((F["rs"] - 80.0) / 20.0).clip(0, 1).fillna(0.0)})
    s["total"] = s[SCORE_ITEMS].sum(axis=1)
    return s


def to_by_day(S: Dict[str, np.ndarray], mask: np.ndarray) -> Dict[int, List[Tuple[int, float, float]]]:
    out: Dict[int, List[Tuple[int, float, float]]] = {}
    for i in np.flatnonzero(mask):
        out.setdefault(int(S["t"][i]), []).append((int(S["j"][i]), float(S["pivot"][i]), float(S["low"][i])))
    return out


def row(sim: Dict[str, object], spy_ex: pd.Series) -> Dict[str, float]:
    ex, tr = sim["excess"], sim["trades"]
    eq = (1 + ex).cumprod()
    out = {"Sharpe": vb.sharpe(ex), "ann %": float((eq.iloc[-1] ** (252 / len(ex)) - 1) * 100),
           "maxDD %": float((eq / eq.cummax() - 1).min() * 100), "invested %": float(sim["gross"].mean() * 100),
           **jl.trade_stats(tr)}
    if len(tr) > 2:
        out["t(avg R)"] = float(tr["R_mult"].mean() / tr["R_mult"].std() * np.sqrt(len(tr)))
    out["alpha t vs SPY"] = jl.alpha_beta(ex, spy_ex.reindex(ex.index).fillna(0.0))["alpha t"]
    return out


def setup(use_cache: bool = True):
    from ..strategy_atlas import load_ohlc

    M = vdata.load()
    d = load_ohlc()
    mkt = (d["SPY"]["Close"], d["SPY"]["Volume"], d["BIL"]["Close"].pct_change())
    base = jl.JParams()
    ind = jl.prepare(M, base)
    cache = vdata.CACHE / "jlaw_scan.npz"
    if use_cache and cache.exists():
        z = np.load(cache)
        S = {k: z[k] for k in z.files}
    else:
        i_start = int(np.searchsorted(ind["C"].index, pd.Timestamp(base.start))) - 1
        S = jl.scan(*(ind[k].to_numpy() for k in ("H", "L", "V", "v50", "rs", "screen")), i_start, base.lookback, base.min_depth)
        np.savez_compressed(cache, **S)
    F = features(S, catalyst_matrix(ind))
    sc = score(F)
    ok = bounded(F).to_numpy()
    dates = ind["C"].index
    in_dev = (dates[S["t"]] <= pd.Timestamp(DEV[1])) & (dates[S["t"]] >= pd.Timestamp(DEV[0]) - pd.Timedelta(days=5))
    cutoff = float(np.quantile(sc.loc[ok & in_dev, "total"], 0.75))
    return {"ind": ind, "S": S, "F": F, "score": sc, "ok": ok, "in_dev": in_dev, "cutoff": cutoff, "mkt": mkt, "base": base}


def run_period(ctx, period, mask: np.ndarray, entry: str) -> Dict[str, object]:
    spy, spy_vol, rf = ctx["mkt"]
    p = replace(ctx["base"], entry=entry, start=period[0], end=period[1])
    return jl.simulate(ctx["ind"], to_by_day(ctx["S"], mask), spy, spy_vol, rf, p)


def table(ctx, period, masks: Dict[str, Tuple[np.ndarray, str]]) -> pd.DataFrame:
    spy, _, rf = ctx["mkt"]
    spy_ex = spy.pct_change() - rf
    sims = {name: run_period(ctx, period, m, entry) for name, (m, entry) in masks.items()}
    rows = {name: row(sim, spy_ex) for name, sim in sims.items()}
    s = spy_ex.reindex(next(iter(sims.values()))["excess"].index).fillna(0.0)
    eq = (1 + s).cumprod()
    rows["SPY buy and hold"] = {"Sharpe": vb.sharpe(s), "ann %": float((eq.iloc[-1] ** (252 / len(s)) - 1) * 100),
                                "maxDD %": float((eq / eq.cummax() - 1).min() * 100), "invested %": 100.0}
    return pd.DataFrame(rows).T


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--holdout", action="store_true")
    args = ap.parse_args(argv)
    ctx = setup()
    sc, ok, cutoff = ctx["score"], ctx["ok"], ctx["cutoff"]
    chosen_mask = ok & (sc["total"].to_numpy() >= cutoff)
    fixed_by_day = jl.select(ctx["S"], ctx["base"])
    fixed_keys = {(t, j) for t, lst in fixed_by_day.items() for j, _, _ in lst}
    fixed_mask = np.fromiter(((int(t), int(j)) in fixed_keys for t, j in zip(ctx["S"]["t"], ctx["S"]["j"])), dtype=bool, count=len(ok))
    cands = {name: (chosen_mask, entry) for name, entry in CANDIDATES.items()}
    dev = table(ctx, DEV, {**cands, "fixed rules (vcp.jlaw primary)": (fixed_mask, "pullback")})
    eligible = dev.loc[list(CANDIDATES)]
    eligible = eligible[eligible["trades"] >= MIN_TRADES]
    frozen = eligible["Sharpe"].idxmax() if len(eligible) else None
    # development-only diagnostics: does the score rank setups?
    lo = ok & (sc["total"].to_numpy() < np.quantile(sc.loc[ok & ctx["in_dev"], "total"], 0.5))
    mid = ok & ~lo & ~chosen_mask
    rank = table(ctx, DEV, {"score: bottom half": (lo, "close_breakout"), "score: 50-75%": (mid, "close_breakout"),
                            "score: top quarter": (chosen_mask, "close_breakout")}).drop(index="SPY buy and hold")
    n_dev = int((ok & ctx["in_dev"]).sum())
    lines = ["# J Law's VCP, flexible version", "", "```", __doc__.strip(), "```", "",
             f"Bounded setup-days in the development period: {n_dev:,}; score cutoff (75th percentile): {cutoff:.2f}; "
             f"setup-days at or above it: {int((chosen_mask & ctx['in_dev']).sum()):,}.", "",
             "Average score items of bounded setups (development):", "",
             sc.loc[ok & ctx["in_dev"], SCORE_ITEMS + ["total"]].mean().round(2).to_frame("mean").T.to_markdown(), "",
             "## Development 2017-2021", "", dev.round(2).to_markdown(), "",
             f"Frozen for the holdout: **{frozen}**", "",
             "Does the score rank setups? (development only, close-breakout entry)", "", rank.round(2).to_markdown(), ""]
    if args.holdout and frozen:
        hold = table(ctx, HOLD, {**cands, "fixed rules (vcp.jlaw primary)": (fixed_mask, "pullback")})
        both = table(ctx, (DEV[0], None), {frozen: cands[frozen], "fixed rules (vcp.jlaw primary)": (fixed_mask, "pullback")})
        sim = run_period(ctx, HOLD, *cands[frozen])
        tr = sim["trades"]
        lines += ["## Holdout 2022-2026 (run once)", "", f"The result is the row **{frozen}**; the others are for information.", "",
                  hold.round(2).to_markdown(), "", "## Whole period 2017-2026, for reference", "", both.round(2).to_markdown(), ""]
        if len(tr):
            yearly = tr.groupby(tr["entry_date"].dt.year).agg(trades=("ret", "size"), win_pct=("ret", lambda x: (x > 0).mean() * 100),
                                                               avg_R=("R_mult", "mean"))
            lines += ["Holdout trades of the frozen candidate by entry year:", "", yearly.round(2).to_markdown(), ""]
        core = vb.with_core(run_period(ctx, (DEV[0], None), *cands[frozen])["excess"], run_period(ctx, (DEV[0], None), *cands[frozen])["gross"])
        lines += ["## Added to the live core (whole-period stream, walk-forward weights)", "", pd.DataFrame(core).T.round(3).to_markdown(), ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
