"""Systematic Minervini-style VCP on US stocks, 2017-2026, delisted names included.

    python -m tradingagents.strategies.vcp.backtest

Rules (fixed before the first run; the PRIMARY variant decides adoption):

Universe on day t: unadjusted close >= $10, 50-day average dollar volume >= $20M, >= 240 closes in the past year.
Trend template at t (Minervini's eight conditions): close > SMA150 and SMA200; SMA150 > SMA200;
  SMA200 above its value 21 sessions earlier; SMA50 > SMA150 and SMA200; close > SMA50;
  close >= 1.30 x 52-week low; close >= 0.75 x 52-week high; RS rating >= 70, where RS rating is the
  percentile, within the day's universe, of 0.4 r63 + 0.2 r126 + 0.2 r189 + 0.2 r252.
Contraction at t: three consecutive 15-session windows ending at t, depth = (high - low) / high in each.
  depth1 > depth2 > depth3, 8% <= depth1 <= 35%, depth3 <= 10%; average volume in the last window below
  the first window's and below the 50-day average; pivot = last window's high, at least 85% of the
  52-week high.
Entry at the close of t+1 (decided near the close): close above the pivot but no more than 5% above,
  volume >= 1.4 x the 50-day average, SPY above its 200-day average at t. Candidates ranked by RS.
Risk: R = (entry - low of the last window) / entry, clipped to 3%..8%; initial stop at entry x (1 - R).
  Each trade risks 0.5% of equity (position = 0.5% / R of equity), capped at 10% per position and 100%
  gross. No leverage. Cash earns T-bills.
Exits: stop (intraday; a gap below fills at the open); stop moves to the entry price once a close is
  2R above entry; close below SMA50 sells at that close; a stock whose data ends is sold at its last close.
Costs: 5 bp per side.

Robustness (reported, not used to choose): no market filter; no volume condition; 1% risk per trade
(20% cap); $50M liquidity; exit on a close below SMA20 instead of SMA50.
Comparison: plain trend-template momentum, each Friday the 20 highest-RS stocks that pass the trend
template, 5% each, same market filter and costs: does the VCP pattern add anything beyond it?

Adoption into the live core (walk-forward weights as live): the VCP stream must raise the core Sharpe in
2019-26, 2021-26 and 2024-05 onward, and have a positive Sharpe in each half of 2017-26 on its own.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from . import data as vdata

OUT = Path("results/opening_reversal/VCP.md")


@dataclass(frozen=True)
class Params:
    min_price: float = 10.0
    min_dv: float = 20e6
    rs_min: float = 70.0
    win: int = 15
    depth1_min: float = 0.08
    depth1_max: float = 0.35
    depth3_max: float = 0.10
    pivot_vs_high: float = 0.85
    chase_max: float = 0.05
    vol_mult: float = 1.4
    market_filter: bool = True
    use_volume: bool = True
    r_min: float = 0.03
    r_max: float = 0.08
    risk: float = 0.005
    max_pos: float = 0.10
    be_at_r: float = 2.0
    exit_sma: int = 50
    cost: float = 5.0 / 1e4
    start: str = "2017-01-01"


# ------------------------------------------------------------------ indicators
def indicators(M: Dict[str, pd.DataFrame], p: Params) -> Dict[str, pd.DataFrame]:
    O, H, L, C, V = (M[k].astype("float64") for k in ("open", "high", "low", "close", "volume"))
    dv50 = (C * V).rolling(50, min_periods=45).mean()
    v50 = V.rolling(50, min_periods=45).mean()
    hist = C.notna().rolling(252, min_periods=1).sum()
    raw = M["rawclose"].astype("float64") if "rawclose" in M else C        # price actually traded, for the $ filter
    universe = (raw >= p.min_price) & (dv50 >= p.min_dv) & (hist >= 240)
    s50, s150, s200 = (C.rolling(n, min_periods=n).mean() for n in (50, 150, 200))
    hi252, lo252 = H.rolling(252, min_periods=240).max(), L.rolling(252, min_periods=240).min()
    rs_raw = 0.4 * C.pct_change(63) + 0.2 * C.pct_change(126) + 0.2 * C.pct_change(189) + 0.2 * C.pct_change(252)
    rs = rs_raw.where(universe).rank(axis=1, pct=True) * 100
    tt = ((C > s150) & (C > s200) & (s150 > s200) & (s200 > s200.shift(21)) & (s50 > s150) & (s50 > s200)
          & (C > s50) & (C >= 1.3 * lo252) & (C >= 0.75 * hi252) & (rs >= p.rs_min) & universe)
    w = p.win

    def window(k):  # k = 0 most recent window ending at t
        hh = H.shift(k * w).rolling(w, min_periods=w).max()
        ll = L.shift(k * w).rolling(w, min_periods=w).min()
        vv = V.shift(k * w).rolling(w, min_periods=w).mean()
        return hh, ll, vv

    h3, l3, v3 = window(0)
    h2, l2, _ = window(1)
    h1, l1, v1 = window(2)
    d1, d2, d3 = (h1 - l1) / h1, (h2 - l2) / h2, (h3 - l3) / h3
    setup = (tt & (d1 > d2) & (d2 > d3) & (d1 >= p.depth1_min) & (d1 <= p.depth1_max) & (d3 <= p.depth3_max)
             & (v3 < v1) & (v3 < v50) & (h3 >= p.pivot_vs_high * hi252))
    sma_exit = C.rolling(p.exit_sma, min_periods=p.exit_sma).mean()
    return {"O": O, "H": H, "L": L, "C": C, "V": V, "v50": v50, "rs": rs, "tt": tt, "setup": setup,
            "pivot": h3, "base_low": l3, "sma_exit": sma_exit, "universe": universe}


# ------------------------------------------------------------------ simulation
@dataclass
class Pos:
    sym: str
    entry_date: pd.Timestamp
    entry: float
    shares: float
    stop: float
    r: float
    be_done: bool = False


def simulate(ind: Dict[str, pd.DataFrame], spy: pd.Series, rf: pd.Series, p: Params) -> Dict[str, object]:
    C, O, L, V = ind["C"], ind["O"], ind["L"], ind["V"]
    dates = C.index
    syms = np.array(C.columns)
    Cn, On, Ln, Vn = C.to_numpy(), O.to_numpy(), L.to_numpy(), V.to_numpy()
    setup, piv, blow, v50, rs, smx = (ind[k].to_numpy() for k in ("setup", "pivot", "base_low", "v50", "rs", "sma_exit"))
    spy_ok = (spy > spy.rolling(200).mean()).reindex(dates).fillna(False).to_numpy()
    rfn = rf.reindex(dates).fillna(0.0).to_numpy()
    col = {s: i for i, s in enumerate(syms)}
    cash, positions = 1.0, {}
    equity, gross, trades = [], [], []
    last_px: Dict[str, float] = {}
    i0 = int(np.searchsorted(dates, pd.Timestamp(p.start)))
    for t in range(i0, len(dates)):
        cash *= 1 + rfn[t]
        # ---- exits on day t (stops intraday, then close-based exits)
        for s in list(positions):
            ps, j = positions[s], col[s]
            c, o, lo = Cn[t, j], On[t, j], Ln[t, j]
            if np.isnan(c):
                # data gap: delisted if nothing for 5 sessions -> sell at the last close
                if t + 5 >= len(dates) or np.all(np.isnan(Cn[t:t + 5, j])):
                    px = last_px.get(s, ps.entry) * (1 - p.cost)
                    cash += ps.shares * px
                    trades.append((s, ps.entry_date, dates[t], ps.entry, px, ps.r, "delisted"))
                    del positions[s]
                continue
            last_px[s] = c
            if lo <= ps.stop:
                px = min(o, ps.stop) * (1 - p.cost)
                cash += ps.shares * px
                trades.append((s, ps.entry_date, dates[t], ps.entry, px, ps.r, "stop"))
                del positions[s]
                continue
            if c < smx[t, j]:
                px = c * (1 - p.cost)
                cash += ps.shares * px
                trades.append((s, ps.entry_date, dates[t], ps.entry, px, ps.r, f"below SMA{p.exit_sma}"))
                del positions[s]
                continue
            if not ps.be_done and c >= ps.entry * (1 + p.be_at_r * ps.r):
                ps.stop, ps.be_done = max(ps.stop, ps.entry), True
        # ---- mark to market
        mv = sum(ps.shares * (Cn[t, col[s]] if not np.isnan(Cn[t, col[s]]) else last_px.get(s, ps.entry))
                 for s, ps in positions.items())
        eq = cash + mv
        # ---- entries at the close of t from setups at t-1
        if t >= 1 and (spy_ok[t - 1] or not p.market_filter):
            cand = np.where(setup[t - 1])[0]
            picks = []
            for j in cand:
                s = syms[j]
                if s in positions:
                    continue
                c, pv = Cn[t, j], piv[t - 1, j]
                if np.isnan(c) or not (pv < c <= pv * (1 + p.chase_max)):
                    continue
                if p.use_volume and not (Vn[t, j] >= p.vol_mult * v50[t - 1, j]):
                    continue
                picks.append((rs[t - 1, j], j))
            for _, j in sorted(picks, reverse=True):
                s = syms[j]
                c = Cn[t, j]
                entry = c * (1 + p.cost)
                r = float(np.clip((entry - blow[t - 1, j]) / entry, p.r_min, p.r_max))
                frac = min(p.risk / r, p.max_pos)
                room = 1.0 - mv / eq
                frac = min(frac, room)
                if frac < 0.01:
                    break
                shares = frac * eq / entry
                cash -= shares * entry
                mv += shares * c
                positions[s] = Pos(s, dates[t], entry, shares, entry * (1 - r), r)
                last_px[s] = c
        equity.append(cash + mv)
        gross.append(mv / (cash + mv))
    idx = dates[i0:]
    eqs = pd.Series(equity, index=idx)
    ret = eqs.pct_change().fillna(eqs.iloc[0] - 1.0)
    tr = pd.DataFrame(trades, columns=["symbol", "entry_date", "exit_date", "entry", "exit", "r", "reason"])
    if len(tr):
        tr["ret"] = tr["exit"] / tr["entry"] - 1
        tr["R_mult"] = tr["ret"] / tr["r"]
        tr["days"] = [(dates.get_loc(b) - dates.get_loc(a)) for a, b in zip(tr["entry_date"], tr["exit_date"])]
    return {"ret": ret, "excess": ret - rf.reindex(idx).fillna(0.0), "gross": pd.Series(gross, index=idx),
            "trades": tr, "open": len(positions)}


def momentum_comparison(ind: Dict[str, pd.DataFrame], spy: pd.Series, rf: pd.Series, p: Params, n: int = 20) -> pd.Series:
    """Each Friday hold the n highest-RS trend-template stocks, 1/n each (same filter, costs)."""
    C, tt, rs = ind["C"], ind["tt"], ind["rs"]
    dates = C.index
    spy_ok = (spy > spy.rolling(200).mean()).reindex(dates).fillna(False)
    fri = pd.Series(dates.dayofweek == 4, index=dates)
    W = pd.DataFrame(np.nan, index=dates, columns=C.columns)
    for t in dates[fri.to_numpy()]:
        row = pd.Series(0.0, index=C.columns)
        if spy_ok[t]:
            top = rs.loc[t].where(tt.loc[t]).dropna().nlargest(n).index
            row[top] = 1.0 / n
        W.loc[t] = row
    W = W.ffill().fillna(0.0)
    r = C.pct_change().fillna(0.0)
    gross_ret = (W.shift(1) * r).sum(axis=1) - W.diff().abs().sum(axis=1) * p.cost
    cash = (1 - W.shift(1).sum(axis=1)).clip(lower=0) * rf.reindex(dates).fillna(0.0)
    out = gross_ret + cash - rf.reindex(dates).fillna(0.0)
    return out[out.index >= p.start]


# ------------------------------------------------------------------ evaluation
def sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 20 and x.std() > 0 else float("nan")


def stats(ex: pd.Series, gross: Optional[pd.Series] = None, tr: Optional[pd.DataFrame] = None) -> Dict[str, float]:
    mid = ex.index[0] + (ex.index[-1] - ex.index[0]) / 2
    eq = (1 + ex).cumprod()
    out = {"Sharpe": sharpe(ex), "1st half": sharpe(ex[ex.index < mid]), "2nd half": sharpe(ex[ex.index >= mid]),
           "ann % (excess)": float((eq.iloc[-1] ** (252 / len(ex)) - 1) * 100),
           "vol %": float(ex.std() * np.sqrt(252) * 100), "maxDD %": float((eq / eq.cummax() - 1).min() * 100)}
    if gross is not None:
        out["avg gross %"] = float(gross.mean() * 100)
    if tr is not None and len(tr):
        out.update({"trades": len(tr), "win %": float((tr["ret"] > 0).mean() * 100),
                    "avg R": float(tr["R_mult"].mean()), "avg trade %": float(tr["ret"].mean() * 100),
                    "avg days": float(tr["days"].mean())})
    return out


def with_core(stream: pd.Series, gross: pd.Series) -> Dict[str, Dict[str, float]]:
    """Add the stream to the live core as one more strategy (walk-forward weights, 2x leverage, gross <= 2)."""
    from .. import core_portfolio as cp
    from .. import regime_overlays as ro

    ctx = ro.setup()
    R = ctx.Rs.copy()
    s = stream.reindex(R.index)
    s_scale = (cp.TARGET_STRAT_VOL / (s.rolling(60, min_periods=40).std() * np.sqrt(252))).clip(upper=5.0)
    R["VCP"] = s * s_scale.shift(1)
    W = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    for y in range(2011, R.index[-1].year + 1):
        W.loc[W.index.year == y] = cp.fit_weights(R[R.index.year < y]).to_numpy()
    E = cp.combine(ctx.P, W.drop(columns="VCP"), ctx.scale)
    k = (W["VCP"] * s_scale).fillna(0.0)                                  # VCP capital share (pre-leverage)
    g_vcp = k * gross.reindex(R.index).fillna(0.0)
    tot_gross = E.abs().sum(axis=1) + g_vcp
    lev = pd.Series(cp.LEVERAGE, index=E.index).clip(upper=cp.MAX_GROSS / tot_gross.replace(0, np.nan)).fillna(0.0)
    Ef = E.mul(lev, axis=0).clip(lower=0.0)
    etf = (Ef.shift(1) * ctx.ex[Ef.columns]).sum(axis=1) - Ef.diff().abs().sum(axis=1).fillna(0.0) * 2.0 / 1e4
    with_vcp = etf + (lev * k).shift(1).fillna(0.0) * s.fillna(0.0)
    base = ro.book(ctx, ctx.W0)
    out = {}
    for name, r in (("core (live)", base), ("core + VCP", with_vcp)):
        out[name] = {per: sharpe(r[r.index >= a]) for per, a in (("2019-26", "2019-01-01"), ("2021-26", "2021-01-01"),
                                                                 ("2024-05+", "2024-05-01"))}
    out["VCP weight 2026"] = {"2019-26": float(W["VCP"].iloc[-1])}
    return out


def run() -> Dict[str, object]:
    from ..strategy_atlas import load_ohlc

    M = vdata.load()
    d = load_ohlc()
    spy = d["SPY"]["Close"]
    rf = d["BIL"]["Close"].pct_change()
    base = Params()
    variants = {"PRIMARY": base, "no market filter": replace(base, market_filter=False),
                "no volume condition": replace(base, use_volume=False),
                "1% risk per trade": replace(base, risk=0.01, max_pos=0.20),
                "$50M liquidity": replace(base, min_dv=50e6), "exit below SMA20": replace(base, exit_sma=20)}
    rows, sims = {}, {}
    ind_cache = {}
    for name, p in variants.items():
        key = (p.min_dv, p.exit_sma)
        if key not in ind_cache:
            ind_cache[key] = indicators(M, p)
        sim = simulate(ind_cache[key], spy, rf, p)
        sims[name] = sim
        rows[name] = stats(sim["excess"], sim["gross"], sim["trades"])
    mom = momentum_comparison(ind_cache[(base.min_dv, base.exit_sma)], spy, rf, base)
    rows["comparison: trend-template momentum top 20"] = stats(mom)
    spy_ex = (spy.pct_change() - rf).reindex(sims["PRIMARY"]["excess"].index).fillna(0.0)
    rows["SPY buy and hold"] = stats(spy_ex)
    table = pd.DataFrame(rows).T
    prim = sims["PRIMARY"]
    yearly = pd.DataFrame({"VCP": prim["excess"].groupby(prim["excess"].index.year).apply(lambda x: (1 + x).prod() - 1) * 100,
                           "SPY": spy_ex.groupby(spy_ex.index.year).apply(lambda x: (1 + x).prod() - 1) * 100,
                           "VCP avg gross %": prim["gross"].groupby(prim["gross"].index.year).mean() * 100,
                           "trades": prim["trades"].groupby(prim["trades"]["entry_date"].dt.year).size()})
    core = with_core(prim["excess"], prim["gross"])
    corr = float(prim["excess"].corr(spy_ex))
    return {"table": table, "yearly": yearly, "core": core, "corr_spy": corr, "trades": prim["trades"],
            "universe_size": float(ind_cache[(base.min_dv, base.exit_sma)]["universe"].sum(axis=1).loc[base.start:].median()),
            "columns": M["close"].shape[1]}


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    res = run()
    core = pd.DataFrame(res["core"]).T
    prim_ok = all(core.loc["core + VCP", p] > core.loc["core (live)", p] for p in ("2019-26", "2021-26", "2024-05+"))
    halves_ok = res["table"].loc["PRIMARY", "1st half"] > 0 and res["table"].loc["PRIMARY", "2nd half"] > 0
    tr = res["trades"]
    by_reason = tr.groupby("reason").agg(n=("ret", "size"), avg_ret_pct=("ret", lambda x: x.mean() * 100), avg_R=("R_mult", "mean"))
    best = tr.nlargest(10, "ret")[["symbol", "entry_date", "exit_date", "ret", "R_mult", "days", "reason"]]
    lines = ["# Systematic VCP on US stocks", "", "```", __doc__.strip(), "```", "",
             f"Data: {res['columns']} stock columns (delisted included); median daily universe {res['universe_size']:.0f} stocks.", "",
             "## Results 2017-2026 (excess over T-bills)", "", res["table"].round(2).to_markdown(), "",
             f"Correlation of daily VCP returns with SPY: {res['corr_spy']:.2f}", "",
             "## By year (primary)", "", res["yearly"].round(1).to_markdown(), "",
             "## Exits (primary)", "", by_reason.round(2).to_markdown(), "",
             "## Ten best trades (primary)", "", best.round(3).to_markdown(index=False), "",
             "## Added to the live core", "", core.round(3).to_markdown(), "",
             f"Verdict: **{'ADOPT' if (prim_ok and halves_ok) else 'reject'}** "
             f"(raises core in all periods: {prim_ok}; positive in both halves: {halves_ok})"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
