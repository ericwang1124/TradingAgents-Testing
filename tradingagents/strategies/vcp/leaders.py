"""Leader breakouts: the scored VCP setups plus earnings news, peer strength and a market overlay.

    python -m tradingagents.strategies.vcp.leaders             # development period only
    python -m tradingagents.strategies.vcp.leaders --holdout   # once the development choice is frozen

Starting point: vcp.jlaw_flex (seven pattern items, confirmed entries). J Law's method is used as an
idea, not a target. Added here, each for a reason that does not depend on him. Written and committed
before any of it was run.

A. Five more score items, one point each (twelve in total with the seven of jlaw_flex):
   earnings   the latest quarterly report within 95 days, from timestamped news headlines: 1 if both
              EPS and sales beat estimates (older headlines give year-over-year numbers instead: EPS
              up and sales up 10% or more), 0.5 if one did and the other did not miss, else 0.
              Post-earnings drift is among the best-documented regularities.
   guidance   1 if guidance was raised (or set above estimates) on balance in those 95 days.
   analysts   price-target raises and upgrades minus cuts and downgrades in the past 60 days:
              3 or more = 1, 1 or 2 = 0.5.
   group      average 1-year-return percentile of the 20 stocks whose daily returns, net of the
              market, were most correlated with this one over the past 126 sessions (peers found
              from prices each month-end, since no industry codes are at hand): 0 at 50, 1 at 80.
   trendline  the base's highs descend (the earlier high more than 3% above the pivot) and the close
              is already above the line through the last two of them.
   Only what was published before 19:00 UTC on the breakout day counts.
B. Events and cutoff. An event is a bounded setup followed the next day by a close above the pivot on
   volume above the prior day's and the 50-day average. Traded: events whose 12-item score is at or above
   the 75th percentile of development-period events.
C. Entries: both confirmed ones of jlaw_flex (the close of the breakout day if within 5% of the
   pivot; else or later, a buy-stop above a quiet pullback day's high). The development period showed
   the choice between them to be noise, so both are taken.
D. Market overlay, three candidates:
   M0  none beyond the two reductions already in vcp.jlaw.
   M1  environment E = SPY above its 50-day average + at least half the stock universe above its
       50-day average + VIX below 3-month VIX + high-yield vs investment-grade bonds (HYG/LQD) above
       its 50-day average. New-trade risk x1 at E >= 3, x0.5 at E = 2, none at E <= 1; halved again
       while fewer than 30% of the market's breakouts of the past 30 sessions held their pivot five
       sessions later (needs at least five such breakouts).
   M2  M1, and in a reversal window - SPY was 8% or more below its 52-week high within the past 40
       sessions, is now above its 20-day average and above its close 10 sessions ago - new-trade
       risk is x1.5 whatever E says. Breakouts as a correction ends are the classic best case.
E. Unchanged: screen, 3-8% stops, 0.35% of equity at risk per trade, exits, 5 bp costs.

Protocol. Development 2017-01 to 2021-12: M0, M1, M2 compared; the highest Sharpe with at least 50
trades is frozen. Holdout 2022-01 to 2026-11: the frozen one is run once. Reported next to it: the
seven-item score on the same events (what the new information adds) and each item's own record.

Caveats. The holdout was already used once for jlaw_flex, so it is clean only for what is new here:
the five items, the event cutoff and the overlay. Renamed companies are looked up under old and new
tickers, but news coverage is thinner for small companies and for the earliest years.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from . import backtest as vb
from . import jlaw as jl
from . import jlaw_flex as jf
from . import news

OUT = Path("results/opening_reversal/LEADERS.md")
DEV, HOLD = jf.DEV, jf.HOLD
NEW_ITEMS = ["earnings", "guidance", "analysts", "group", "trendline"]
ALL_ITEMS = jf.SCORE_ITEMS + NEW_ITEMS
MIN_TRADES = 50


# ------------------------------------------------------------------ events
def events(ctx) -> pd.DataFrame:
    S, ind = ctx["S"], ctx["ind"]
    C, V, v50 = (ind[k].to_numpy() for k in ("C", "V", "v50"))
    dates, cols = ind["C"].index, np.array(ind["C"].columns)
    t, j, P = S["t"], S["j"], S["pivot"]
    nxt = np.minimum(t + 1, len(dates) - 1)
    conf = ctx["ok"] & (t + 1 < len(dates)) & (C[nxt, j] > P) & (V[nxt, j] > V[t, j]) & (V[nxt, j] > v50[t, j])
    rows = np.flatnonzero(conf)
    return pd.DataFrame({"row": rows, "t": t[rows], "b": nxt[rows], "j": j[rows], "col": cols[j[rows]],
                         "day": dates[nxt[rows]], "pivot": P[rows]}).reset_index(drop=True)


# ------------------------------------------------------------------ new items
def news_items(ev: pd.DataFrame, fetch: bool = False) -> pd.DataFrame:
    alias = news.aliases() if fetch else {}
    out = []
    for col, day in zip(ev["col"], ev["day"]):
        rec = news.ensure(col, day - pd.Timedelta(days=100), day, alias) if fetch else news.load(col)
        out.append(news.signals([tuple(x) for x in rec["items"]], pd.Timestamp(day) + pd.Timedelta(hours=19)))
    s = pd.DataFrame(out, index=ev.index)
    eps, sales = s["eps"], s["sales"]
    pts = (eps > 0).astype(float) + (sales > 0).astype(float) - (eps < 0).astype(float) - (sales < 0).astype(float)
    return pd.DataFrame({"earnings": (pts.clip(lower=0) / 2.0).where(s["report"].notna(), 0.0),
                         "guidance": (s["guidance"] > 0).astype(float),
                         "analysts": np.select([s["analyst"] >= 3, s["analyst"] >= 1], [1.0, 0.5], 0.0),
                         "has_report": s["report"].notna().astype(float), "headlines": s["headlines"]}, index=ev.index)


def peer_strength(ind: Dict[str, pd.DataFrame], ev: pd.DataFrame, k: int = 20, window: int = 126) -> pd.Series:
    """Mean relative-strength percentile, on the setup day, of each stock's k closest peers."""
    C = ind["C"]
    R = C.pct_change(fill_method=None).to_numpy()
    uni, rs = ind["universe"].to_numpy(), ind["rs"].to_numpy()
    dates = C.index
    month = dates.to_period("M")
    last_of_month = np.flatnonzero(np.r_[month[1:] != month[:-1], True])
    out = pd.Series(np.nan, index=ev.index)
    ev_month_end = np.searchsorted(last_of_month, ev["t"].to_numpy() - 1, side="right") - 1   # latest month-end before the setup day
    for m_pos in np.unique(ev_month_end):
        if m_pos < 0:
            continue
        im = int(last_of_month[m_pos])
        if im < window:
            continue
        cols = np.flatnonzero(uni[im])
        X = R[im - window + 1:im + 1][:, cols]
        good = np.isfinite(X).sum(axis=0) >= int(window * 0.9)
        cols, X = cols[good], X[:, good]
        X = X - np.nanmean(X, axis=1, keepdims=True)                     # net of the equal-weight market
        Z = np.nan_to_num((X - np.nanmean(X, axis=0)) / np.nanstd(X, axis=0))
        corr = Z.T @ Z / window
        np.fill_diagonal(corr, -np.inf)
        pos = {c: i for i, c in enumerate(cols)}
        for e in ev.index[ev_month_end == m_pos]:
            i = pos.get(int(ev.at[e, "j"]))
            if i is None:
                continue
            nb = cols[np.argpartition(-corr[i], k)[:k]]
            out.at[e] = np.nanmean(rs[int(ev.at[e, "t"]), nb])
    return out


def trendline(ctx, ev: pd.DataFrame) -> pd.Series:
    S, C = ctx["S"], ctx["ind"]["C"].to_numpy()
    out = []
    for row, t, j in zip(ev["row"], ev["t"], ev["j"]):
        d, hi, hv = S["depths"][row], S["his"][row], S["hvals"][row]
        n = int((~np.isnan(d)).sum())
        if n < 2 or not hv[n - 2] > hv[n - 1] * 1.03 or hi[n - 1] <= hi[n - 2]:
            out.append(0.0)
            continue
        slope = (hv[n - 1] - hv[n - 2]) / (hi[n - 1] - hi[n - 2])
        out.append(float(C[t, j] > hv[n - 1] + slope * (t - hi[n - 1])))
    return pd.Series(out, index=ev.index)


def item_table(ctx, ev: pd.DataFrame, fetch: bool = False) -> pd.DataFrame:
    base = ctx["score"].loc[ev["row"], jf.SCORE_ITEMS].reset_index(drop=True)
    base.index = ev.index
    nw = news_items(ev, fetch)
    grp = ((peer_strength(ctx["ind"], ev) - 50.0) / 30.0).clip(0, 1).fillna(0.0)
    items = pd.concat([base, nw[["earnings", "guidance", "analysts"]], grp.rename("group"), trendline(ctx, ev).rename("trendline")], axis=1)
    items["score7"] = items[jf.SCORE_ITEMS].sum(axis=1)
    items["score12"] = items[ALL_ITEMS].sum(axis=1)
    items["has_report"], items["headlines"] = nw["has_report"], nw["headlines"]
    return items


# ------------------------------------------------------------------ market overlay
def market(ctx, ev: pd.DataFrame) -> pd.DataFrame:
    from ..strategy_atlas import load_ohlc

    ind = ctx["ind"]
    dates = ind["C"].index
    d = load_ohlc()
    spy = d["SPY"]["Close"]
    f = lambda s: s.reindex(dates).ffill()
    above50 = (ind["C"] > ind["s50"]) & ind["universe"]
    breadth = above50.sum(axis=1) / ind["universe"].sum(axis=1).replace(0, np.nan)
    credit = d["HYG"]["Close"] / d["LQD"]["Close"]
    E = ((f(spy) > f(spy.rolling(50).mean())).astype(int) + (breadth >= 0.5).astype(int)
         + (f(d["^VIX"]["Close"]) < f(d["^VIX3M"]["Close"])).astype(int) + (f(credit) > f(credit.rolling(50).mean())).astype(int))
    # follow-through of the market's own breakouts: did the close hold the pivot five sessions later?
    C = ind["C"].to_numpy()
    b, j, P = ev["b"].to_numpy(), ev["j"].to_numpy(), ev["pivot"].to_numpy()
    known = b + 5
    okk = known < len(dates)
    held = np.where(okk, C[np.minimum(known, len(dates) - 1), j] > P, False)
    follow = np.full(len(dates), np.nan)
    for t in range(len(dates)):
        m = okk & (known <= t) & (b >= t - 30)
        if m.sum() >= 5:
            follow[t] = held[m].mean()
    m1 = np.select([E >= 3, E == 2], [1.0, 0.5], 0.0) * np.where(follow < 0.30, 0.5, 1.0)
    off_high = f(spy / spy.rolling(252).max() - 1)
    reversal = ((off_high.rolling(40).min() <= -0.08) & (f(spy) > f(spy.rolling(20).mean())) & (f(spy) > f(spy).shift(10))).to_numpy()
    m2 = np.where(reversal, 1.5, m1)
    return pd.DataFrame({"E": E.to_numpy(), "breadth": breadth.to_numpy(), "follow": follow, "reversal": reversal,
                         "M0": 1.0, "M1": m1, "M2": m2}, index=dates)


# ------------------------------------------------------------------ runs
def mask_from(ctx, ev: pd.DataFrame, keep: np.ndarray) -> np.ndarray:
    m = np.zeros(len(ctx["ok"]), dtype=bool)
    m[ev.loc[keep, "row"].to_numpy()] = True
    return m


def run(ctx, period, mask: np.ndarray, mult: np.ndarray, entry: str = "flex") -> Dict[str, object]:
    spy, spy_vol, rf = ctx["mkt"]
    p = replace(ctx["base"], entry=entry, start=period[0], end=period[1])
    return jl.simulate(ctx["ind"], jf.to_by_day(ctx["S"], mask), spy, spy_vol, rf, p, risk_mult=mult)


def results(ctx, period, specs: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> pd.DataFrame:
    spy, _, rf = ctx["mkt"]
    spy_ex = spy.pct_change() - rf
    sims = {k: run(ctx, period, m, mult) for k, (m, mult) in specs.items()}
    rows = {k: jf.row(s, spy_ex) for k, s in sims.items()}
    s = spy_ex.reindex(next(iter(sims.values()))["excess"].index).fillna(0.0)
    eq = (1 + s).cumprod()
    rows["SPY buy and hold"] = {"Sharpe": vb.sharpe(s), "ann %": float((eq.iloc[-1] ** (252 / len(s)) - 1) * 100),
                                "maxDD %": float((eq / eq.cummax() - 1).min() * 100), "invested %": 100.0}
    return pd.DataFrame(rows).T


def item_record(ctx, ev: pd.DataFrame, items: pd.DataFrame, period) -> pd.DataFrame:
    """Every event bought at its confirmed close, no score filter: average R when an item is high vs low."""
    sim = run(ctx, period, mask_from(ctx, ev, np.ones(len(ev), dtype=bool)), np.ones(len(ctx["ind"]["C"])), entry="close_breakout")
    tr = sim["trades"]
    if not len(tr):
        return pd.DataFrame()
    key = pd.Series(ev.index, index=pd.MultiIndex.from_arrays([ev["col"], ev["day"]]))
    key = key[~key.index.duplicated()]
    idx = key.reindex(pd.MultiIndex.from_arrays([tr["symbol"], tr["entry_date"]])).to_numpy()
    ok = ~np.isnan(idx)
    it = items.loc[idx[ok].astype(int)].reset_index(drop=True)
    R = tr.loc[ok, "R_mult"].reset_index(drop=True)
    out = {}
    for c in ALL_ITEMS + ["score7", "score12"]:
        hi = it[c] >= (0.5 if c in ALL_ITEMS else it[c].quantile(0.75))
        a, b = R[hi], R[~hi]
        se = np.sqrt(a.var() / max(len(a), 1) + b.var() / max(len(b), 1)) if len(a) > 2 and len(b) > 2 else np.nan
        out[c] = {"n high": int(hi.sum()), "avg R high": a.mean(), "n low": int((~hi).sum()), "avg R low": b.mean(),
                  "difference t": (a.mean() - b.mean()) / se if se and se > 0 else np.nan}
    return pd.DataFrame(out).T


def build(fetch: bool = False):
    ctx = jf.setup()
    ev = events(ctx)
    items = item_table(ctx, ev, fetch)
    mk = market(ctx, ev)
    in_dev = (ev["day"] >= DEV[0]) & (ev["day"] <= DEV[1])
    return ctx, ev, items, mk, in_dev


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--holdout", action="store_true")
    ap.add_argument("--fetch", action="store_true", help="download missing news (needs Alpaca credentials)")
    args = ap.parse_args(argv)
    ctx, ev, items, mk, in_dev = build(args.fetch)
    cut12 = float(items.loc[in_dev, "score12"].quantile(0.75))
    cut7 = float(items.loc[in_dev, "score7"].quantile(0.75))
    m12 = mask_from(ctx, ev, (items["score12"] >= cut12).to_numpy())
    m7 = mask_from(ctx, ev, (items["score7"] >= cut7).to_numpy())
    cands = {f"12 items, {k}": (m12, mk[k].to_numpy()) for k in ("M0", "M1", "M2")}
    ref = {"7 items (jlaw_flex score), M0": (m7, mk["M0"].to_numpy())}
    dev = results(ctx, DEV, {**cands, **ref})
    elig = dev.loc[list(cands)]
    elig = elig[elig["trades"] >= MIN_TRADES]
    frozen = elig["Sharpe"].idxmax() if len(elig) else None
    cover = items.groupby(ev["day"].dt.year)[["has_report", "earnings", "guidance", "analysts", "group", "trendline"]].mean()
    cover["events"] = ev.groupby(ev["day"].dt.year).size()
    mkt_dev = mk.loc[DEV[0]:DEV[1]]
    lines = ["# Leader breakouts", "", "```", __doc__.strip(), "```", "",
             f"Events: {len(ev)} ({int(in_dev.sum())} in the development period). Score cutoffs from development events: "
             f"12 items {cut12:.2f}, 7 items {cut7:.2f}.", "",
             "Share of events with a parsed quarterly report, and average new items, by year:", "", cover.round(2).to_markdown(), "",
             f"Market overlay in development: M1 blocks new trades on {float((mkt_dev['M1'] == 0).mean()) * 100:.0f}% of days and halves or "
             f"quarters them on {float(((mkt_dev['M1'] > 0) & (mkt_dev['M1'] < 1)).mean()) * 100:.0f}%; reversal windows cover "
             f"{float(mkt_dev['reversal'].mean()) * 100:.0f}% of days.", "",
             "## Development 2017-2021", "", dev.round(2).to_markdown(), "", f"Frozen for the holdout: **{frozen}**", "",
             "Each item's own record, development (all events bought at the confirmed close, no score filter):", "",
             item_record(ctx, ev, items, DEV).round(2).to_markdown(), ""]
    if args.holdout and frozen:
        hold = results(ctx, HOLD, {**cands, **ref})
        whole = results(ctx, (DEV[0], None), {frozen: cands[frozen], **ref})
        sim = run(ctx, (DEV[0], None), *cands[frozen])
        tr = sim["trades"]
        yearly = tr.groupby(tr["entry_date"].dt.year).agg(trades=("ret", "size"), win_pct=("ret", lambda x: (x > 0).mean() * 100),
                                                           avg_R=("R_mult", "mean")) if len(tr) else pd.DataFrame()
        lines += ["## Holdout 2022-2026 (run once)", "", f"The result is the row **{frozen}**; the others are for information.", "",
                  hold.round(2).to_markdown(), "", "Each item's own record, holdout:", "",
                  item_record(ctx, ev, items, HOLD).round(2).to_markdown(), "",
                  "## Whole period 2017-2026, for reference", "", whole.round(2).to_markdown(), "",
                  "Trades of the frozen candidate by entry year:", "", yearly.round(2).to_markdown(), "",
                  "## Added to the live core (whole-period stream, walk-forward weights)", "",
                  pd.DataFrame(vb.with_core(sim["excess"], sim["gross"])).T.round(3).to_markdown(), ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
