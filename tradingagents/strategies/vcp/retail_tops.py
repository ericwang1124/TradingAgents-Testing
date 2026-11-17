"""Retail TOPS: well-known traders' methods as contributors, weighted by their own track record.

    python -m tradingagents.strategies.vcp.retail_tops

Marshall Wace's TOPS collects trade ideas from sell-side contributors, scores every contributor on
how their ideas did, and sizes ideas by that score. Here the contributors are seven published trading
methods, each turned into daily-bar rules on the same point-in-time US stock universe (unadjusted
price >= $12, 50-day dollar volume >= $20M, delisted names included). Written and committed before
any run; the rules follow the public descriptions cited in reports/散户TOPS_交易员方法加权.md.

Contributors (entry at the close of the signal day unless stated; 5 bp per side):
  1 Minervini VCP      scored setups of vcp.jlaw_flex (seven items, top quarter by the 2017-21 cutoff),
                       close-confirmed breakout entry, stop below the last contraction, SMA20 trail
  2 J Law pullback     the same setups, buy-stop above a quiet pullback to the pivot (jlaw_flex)
  3 Qullamaggie BO     a 30%+ move within the prior 63 sessions, then 15 sessions within a 15% range
                       with SMA10 above SMA20 and the close above SMA20; a close above the range high on
                       volume >= 1.5x the 50-day average. Stop: the day's low (skipped if farther than one
                       ATR14). Trail: close below SMA10 if the 20-day average range is >= 4%, else SMA20.
  4 Qullamaggie EP     open >= 10% above the prior close on volume >= 3x the 50-day average, close at or
                       above the open, prior 63-session return <= +30% (not already extended). Stop: the
                       day's low (skipped if farther than 1.5 ATR14). Trail as 3.
  5 Kell crossback     EMA10 > EMA21 > SMA50, SMA50 rising, at least 10 of the prior 15 closes above EMA21;
                       yesterday's low touched EMA21 and today closes above yesterday's high and EMA10.
                       Stop 0.5% below the lowest low of the past 4 sessions (skipped beyond 8%).
                       Exit: close below EMA21.
  6 Darvas box         box top = 20-session high set at least 3 sessions ago and within 5% of the 52-week
                       high; box bottom = lowest low since the top. Close above the top on volume >= 1.5x
                       the 50-day average. Stop: box bottom (skipped beyond 10%). Trail: lowest low of the
                       prior 10 sessions.
  7 Weinstein stage 2  Fridays: weekly close crosses above the 30-week average, which is flat or rising
                       over 4 weeks; weekly volume >= 2x its 10-week average; relative strength vs SPY above
                       its 52-week average. Stop: lowest low of the prior 8 weeks (skipped beyond 15%).
                       Exit: a weekly close below the 30-week average.
  All: stop moves to entry after 5 sessions if the close is above entry (3, 4) or after a close 10% above
  entry (1, 2, 5, 6, 7); at most 252 sessions; a stock whose data ends is sold at its last close.
  When trailing starts: for 3 and 4 only once the stop has moved to entry (Qullamaggie's low-of-day stop
  first, the moving average after the first days); for 5, 6 and 7 from the day after entry; 1 and 2 keep
  the jlaw_flex rule (SMA20 trail after a close 10% above entry).

Each contributor's ideas are first played out one by one (no capital limits) to give its track record.
The portfolio then takes them with 0.35% of equity at risk per idea (size = risk / stop distance),
at most 15% per stock, gross at most 100%, cash in T-bills, ideas of the day ranked by weight.
Weighting, three variants:
  A equal         every contributor x1
  B skill (PRIMARY)  each month-end, mean R of the contributor's ideas closed in the past 24 months,
                  shrunk by n / (n + 30); weight = shrunk mean / average of the positive ones; zero or
                  negative = paused (its ideas still recorded); fewer than 10 closed ideas = x1
  C skill + consensus  B, and x1.5 when at least two contributors had an idea on the stock in the past
                  10 sessions
Reported: each contributor's record and stand-alone portfolio, A/B/C for 2017-26, 2017-21 and 2022-26,
SPY, and B added to the live core. B is adopted only if it raises the core's Sharpe in 2019-26, 2021-26
and 2024-05 onward. Weights are always computed from the past, so the whole period is out of sample for
the weighting; the rule definitions come from public descriptions, not from this data.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from . import backtest as vb
from . import jlaw as jl
from . import jlaw_flex as jf

OUT = Path("results/opening_reversal/RETAIL_TOPS.md")
START = "2017-01-01"
COST = 5.0 / 1e4
CONTRIBUTORS = ["Minervini VCP", "J Law pullback", "Qullamaggie BO", "Qullamaggie EP", "Kell crossback", "Darvas box", "Weinstein stage 2"]


@dataclass(frozen=True)
class Idea:
    who: str
    t: int          # entry session index (bought at that close, or intraday for J Law)
    j: int
    entry: float
    stop: float
    trail: str      # "sma10", "sma20", "adr", "ema21", "low10", "w30"
    be: str         # "5d" or "10pct"


# ------------------------------------------------------------------ indicators
def indicators(M: Dict[str, pd.DataFrame], spy: pd.Series) -> Dict[str, np.ndarray]:
    O, H, L, C, V = (M[k].astype("float64") for k in ("open", "high", "low", "close", "volume"))
    raw = M["rawclose"].astype("float64")
    dv50 = (C * V).rolling(50, min_periods=45).mean()
    v50 = V.rolling(50, min_periods=45).mean()
    hist = C.notna().rolling(252, min_periods=1).sum()
    uni = (raw >= 12) & (dv50 >= 20e6) & (hist >= 240)
    prev_c = C.shift(1)
    tr = pd.DataFrame(np.fmax(np.fmax((H - L).to_numpy(), (H - prev_c).abs().to_numpy()), (L - prev_c).abs().to_numpy()),
                      index=C.index, columns=C.columns)
    atr = tr.rolling(14, min_periods=14).mean()
    adr = ((H / L - 1) * 100).rolling(20, min_periods=15).mean()
    ema = lambda n: C.ewm(span=n, adjust=False, min_periods=n).mean()
    out = {"O": O, "H": H, "L": L, "C": C, "V": V, "v50": v50, "uni": uni, "atr": atr, "adr": adr,
           "sma10": C.rolling(10, min_periods=10).mean(), "sma20": C.rolling(20, min_periods=20).mean(),
           "sma50": C.rolling(50, min_periods=50).mean(), "ema10": ema(10), "ema21": ema(21),
           "hi252": H.rolling(252, min_periods=240).max()}
    # weekly bars (Friday or the last session of the week)
    wk = C.index.to_period("W-FRI")
    last = pd.Series(C.index, index=C.index).groupby(wk).transform("max") == C.index
    Cw = C[last.to_numpy()]
    Lw = L.groupby(wk).min()
    Lw.index = Cw.index
    Vw = V.groupby(wk).sum()
    Vw.index = Cw.index
    sp = spy.reindex(C.index).ffill()[last.to_numpy()]
    rs = Cw.div(sp, axis=0)
    out.update({"week_end": last.to_numpy(), "Cw": Cw, "Vw": Vw, "Lw": Lw, "w30": Cw.rolling(30, min_periods=30).mean(),
                "rs_w": rs, "rs_w52": rs.rolling(52, min_periods=40).mean()})
    return out


# ------------------------------------------------------------------ contributors
def _ideas_from(mask: pd.DataFrame, stop: pd.DataFrame, entry: pd.DataFrame, who: str, trail: str, be: str,
                i0: int, max_r: Optional[float] = None, max_dist: Optional[pd.DataFrame] = None) -> List[Idea]:
    m = mask.to_numpy() & np.isfinite(stop.to_numpy()) & np.isfinite(entry.to_numpy())
    m[:i0] = False
    out = []
    E, S = entry.to_numpy(), stop.to_numpy()
    D = max_dist.to_numpy() if max_dist is not None else None
    for t, j in zip(*np.nonzero(m)):
        e, s = E[t, j], S[t, j]
        if not s < e:
            continue
        if max_r is not None and (e - s) / e > max_r:
            continue
        if D is not None and (e - s) > D[t, j]:
            continue
        out.append(Idea(who, int(t), int(j), float(e), float(s), trail, be))
    return out


def qullamaggie_bo(x, i0) -> List[Idea]:
    C, H, L, V = x["C"], x["H"], x["L"], x["V"]
    rng_hi = H.shift(1).rolling(15, min_periods=15).max()
    rng_lo = L.shift(1).rolling(15, min_periods=15).min()
    tight = rng_hi / rng_lo - 1 <= 0.15
    prior_move = C.shift(16).rolling(48, min_periods=40).max() / L.shift(16).rolling(63, min_periods=50).min() - 1 >= 0.30
    surf = (x["sma10"].shift(1) > x["sma20"].shift(1)) & (C.shift(1) > x["sma20"].shift(1))
    bo = (C > rng_hi) & (V >= 1.5 * x["v50"].shift(1))
    mask = x["uni"].shift(1, fill_value=False) & tight & prior_move & surf & bo
    return _ideas_from(mask, L, C, "Qullamaggie BO", "adr", "5d", i0, max_dist=x["atr"])


def qullamaggie_ep(x, i0) -> List[Idea]:
    C, O, L, V = x["C"], x["O"], x["L"], x["V"]
    gap = O / C.shift(1) - 1 >= 0.10
    vol = V >= 3.0 * x["v50"].shift(1)
    held = C >= O
    calm = C.shift(1) / C.shift(64) - 1 <= 0.30
    mask = x["uni"].shift(1, fill_value=False) & gap & vol & held & calm
    return _ideas_from(mask, L, C, "Qullamaggie EP", "adr", "5d", i0, max_dist=1.5 * x["atr"])


def kell_crossback(x, i0) -> List[Idea]:
    C, H, L = x["C"], x["H"], x["L"]
    e10, e21, s50 = x["ema10"], x["ema21"], x["sma50"]
    trend = (e10 > e21) & (e21 > s50) & (s50 > s50.shift(10)) & (C > s50)
    above = (C.shift(2) > e21.shift(2)).astype(float).rolling(15, min_periods=15).sum() >= 10
    touch = L.shift(1) <= e21.shift(1)
    turn = (C > H.shift(1)) & (C > e10)
    mask = x["uni"].shift(1, fill_value=False) & trend & above & touch & turn
    stop = L.rolling(4, min_periods=4).min() * 0.995
    return _ideas_from(mask, stop, C, "Kell crossback", "ema21", "10pct", i0, max_r=0.08)


def darvas(x, i0) -> List[Idea]:
    C, H, L, V = x["C"], x["H"], x["L"], x["V"]
    Hy = H.shift(1)
    top = Hy.rolling(20, min_periods=20).max()
    # sessions between the 20-session high and yesterday (0 = set yesterday), from a sliding-window argmax
    filled = np.where(np.isfinite(Hy.to_numpy()), Hy.to_numpy(), -np.inf)
    win = np.lib.stride_tricks.sliding_window_view(filled, 20, axis=0)          # (T-19, N, 20)
    since = np.full(filled.shape, np.nan)
    since[19:] = 19 - win.argmax(axis=2)
    since[~np.isfinite(top.to_numpy())] = np.nan
    arg = pd.DataFrame(since, index=C.index, columns=C.columns)
    Ly = L.shift(1)
    B = np.full(filled.shape, np.nan)
    for d in range(20):                                                         # bottom = lowest low since the top
        mins = Ly.rolling(d + 1, min_periods=d + 1).min().to_numpy()
        sel = since == d
        B[sel] = mins[sel]
    bottom = pd.DataFrame(B, index=C.index, columns=C.columns)
    mask = (x["uni"].shift(1, fill_value=False) & (arg >= 3) & (top >= 0.95 * x["hi252"].shift(1))
            & (C > top) & (V >= 1.5 * x["v50"].shift(1)))
    return _ideas_from(mask, bottom, C, "Darvas box", "low10", "10pct", i0, max_r=0.10)


def weinstein(x, i0) -> List[Idea]:
    Cw, Vw, Lw, w30 = x["Cw"], x["Vw"], x["Lw"], x["w30"]
    cross = (Cw > w30) & (Cw.shift(1) <= w30.shift(1))
    slope = w30 >= w30.shift(4)
    vol = Vw >= 2.0 * Vw.shift(1).rolling(10, min_periods=8).mean()
    rs = x["rs_w"] > x["rs_w52"]
    wmask = cross & slope & vol & rs
    stop_w = Lw.shift(1).rolling(8, min_periods=6).min()
    C = x["C"]
    mask = pd.DataFrame(False, index=C.index, columns=C.columns)
    stop = pd.DataFrame(np.nan, index=C.index, columns=C.columns)
    mask.loc[wmask.index] = wmask.to_numpy()
    stop.loc[stop_w.index] = stop_w.to_numpy()
    mask &= x["uni"].shift(1, fill_value=False)
    return _ideas_from(mask, stop, C, "Weinstein stage 2", "w30", "10pct", i0, max_r=0.15)


def vcp_and_jlaw(i0_date: str) -> Dict[str, List[Idea]]:
    """Minervini and J Law contributors from the scored setups of jlaw_flex, played one by one."""
    ctx = jf.setup()
    sc, ok, cut = ctx["score"]["total"].to_numpy(), ctx["ok"], ctx["cutoff"]
    by_day = jf.to_by_day(ctx["S"], ok & (sc >= cut))
    spy, spy_vol, rf = ctx["mkt"]
    out = {}
    for who, entry in (("Minervini VCP", "close_breakout"), ("J Law pullback", "confirm_pullback")):
        # sized so that capital never binds (jlaw.simulate skips positions under 1% of equity, so not below that)
        p = replace(ctx["base"], entry=entry, risk=0.01, max_pos=0.012, throttle=False, dist_days=False, start=i0_date, end=None)
        tr = jl.simulate(ctx["ind"], by_day, spy, spy_vol, rf, p)["trades"]
        out[who] = tr.assign(who=who)
    return out, ctx["ind"]["C"]


# ------------------------------------------------------------------ playing out one idea
def play(idea: Idea, x) -> Optional[Dict[str, object]]:
    C, O, L = x["Cn"], x["On"], x["Ln"]
    T = C.shape[0]
    j, t0, e = idea.j, idea.t, idea.entry * (1 + COST)
    stop = idea.stop
    r = (e - stop) / e
    if r <= 0:
        return None
    r = max(r, 0.01)
    stop = e * (1 - r)
    trail = idea.trail
    if trail == "adr":
        trail = "sma10" if x["adr"][t0, j] >= 4.0 else "sma20"
    be_done = False
    last = idea.entry
    for t in range(t0 + 1, min(t0 + 253, T)):
        c, o, lo = C[t, j], O[t, j], L[t, j]
        if not np.isfinite(c):
            if t + 5 >= T or not np.isfinite(C[t:t + 5, j]).any():
                return {"exit_t": t, "exit": last * (1 - COST), "reason": "delisted", "r": r, "entry_px": e}
            continue
        last = c
        if lo <= stop:
            return {"exit_t": t, "exit": min(o, stop) * (1 - COST), "reason": "stop", "r": r, "entry_px": e}
        trailing = be_done or idea.be != "5d"
        if not trailing:
            pass
        elif trail == "w30":
            if x["week_end"][t] and np.isfinite(x["w30n"][t, j]) and c < x["w30n"][t, j]:
                return {"exit_t": t, "exit": c * (1 - COST), "reason": "below 30-week", "r": r, "entry_px": e}
        elif trail == "low10":
            if c < x["low10"][t - 1, j]:
                return {"exit_t": t, "exit": c * (1 - COST), "reason": "below 10-day low", "r": r, "entry_px": e}
        else:
            line = x[trail + "n"][t, j]
            if np.isfinite(line) and c < line:
                return {"exit_t": t, "exit": c * (1 - COST), "reason": f"below {trail}", "r": r, "entry_px": e}
        if not be_done and ((idea.be == "5d" and t - t0 >= 5 and c > e) or (idea.be == "10pct" and c >= e * 1.10)):
            stop, be_done = max(stop, e), True
    t = min(t0 + 252, T - 1)
    return {"exit_t": t, "exit": last * (1 - COST), "reason": "time" if t0 + 252 < T else "open at end", "r": r, "entry_px": e}


def track_record(ideas: List[Idea], x, dates: pd.DatetimeIndex, cols) -> pd.DataFrame:
    rows = []
    for idea in ideas:
        res = play(idea, x)
        if res is None:
            continue
        rows.append({"who": idea.who, "symbol": cols[idea.j], "j": idea.j, "entry_t": idea.t, "entry_date": dates[idea.t],
                     "exit_t": res["exit_t"], "exit_date": dates[res["exit_t"]], "entry": res["entry_px"], "exit": res["exit"],
                     "r": res["r"], "reason": res["reason"]})
    df = pd.DataFrame(rows)
    if len(df):
        df["ret"] = df["exit"] / df["entry"] - 1
        df["R"] = df["ret"] / df["r"]
    return df


# ------------------------------------------------------------------ weights and portfolio
def monthly_weights(trades: pd.DataFrame, dates: pd.DatetimeIndex, window_months: int = 24, k: float = 30.0,
                    min_n: int = 10) -> pd.DataFrame:
    month_ends = pd.Series(dates, index=dates).groupby(dates.to_period("M")).max()
    W = pd.DataFrame(1.0, index=month_ends.to_numpy(), columns=CONTRIBUTORS)
    for me in W.index:
        lo = me - pd.DateOffset(months=window_months)
        done = trades[(trades["exit_date"] <= me) & (trades["exit_date"] > lo) & (trades["reason"] != "open at end")]
        g = done.groupby("who")["R"].agg(["mean", "size"])
        raw = {}
        for who in CONTRIBUTORS:
            if who not in g.index or g.at[who, "size"] < min_n:
                raw[who] = np.nan
            else:
                n = g.at[who, "size"]
                raw[who] = g.at[who, "mean"] * n / (n + k)
        pos = [v for v in raw.values() if np.isfinite(v) and v > 0]
        avg = np.mean(pos) if pos else np.nan
        for who, v in raw.items():
            W.at[me, who] = 1.0 if not np.isfinite(v) else (v / avg if v > 0 and np.isfinite(avg) else 0.0)
    return W


def portfolio(trades: pd.DataFrame, x, dates: pd.DatetimeIndex, rf: pd.Series, mode: str = "skill",
              base_risk: float = 0.0035, max_pos: float = 0.15, start: str = START, end: Optional[str] = None,
              weights: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    C = x["Cn"]
    rfn = rf.reindex(dates).fillna(0.0).to_numpy()
    i0 = int(np.searchsorted(dates, pd.Timestamp(start)))
    i1 = len(dates) if end is None else int(np.searchsorted(dates, pd.Timestamp(end), side="right"))
    by_entry: Dict[int, pd.DataFrame] = {t: g for t, g in trades.groupby("entry_t")}
    sig_days = trades.groupby("j")["entry_t"].apply(lambda s: np.sort(s.to_numpy())).to_dict()
    who_by = trades.groupby(["j", "entry_t"])["who"].apply(set).to_dict()
    cash, eq_last = 1.0, 1.0
    open_: Dict[int, Dict[str, float]] = {}
    eq, gross, taken = [], [], []
    for t in range(max(i0, 1), i1):
        cash *= 1 + rfn[t]
        for key in list(open_):
            o = open_[key]
            if o["exit_t"] == t:
                cash += o["shares"] * o["exit"]
                del open_[key]
        mv = sum(o["shares"] * (C[t, o["j"]] if np.isfinite(C[t, o["j"]]) else o["last"]) for o in open_.values())
        for o in open_.values():
            if np.isfinite(C[t, o["j"]]):
                o["last"] = C[t, o["j"]]
        g = by_entry.get(t)
        if g is not None:
            me = dates[t - 1] if t > 0 else dates[t]
            wrow = None
            if weights is not None and mode != "equal":
                wi = weights.index.searchsorted(me, side="right") - 1
                wrow = weights.iloc[wi] if wi >= 0 else None
            cands = []
            for _, row in g.iterrows():
                w = 1.0 if wrow is None else float(wrow[row["who"]])
                if w <= 0:
                    continue
                if mode == "consensus":
                    s = sig_days.get(row["j"], np.array([]))
                    recent = s[(s >= t - 10) & (s <= t)]
                    whos = set().union(*(who_by.get((row["j"], u), set()) for u in recent))
                    if len(whos) >= 2:
                        w *= 1.5
                cands.append((w, row))
            for w, row in sorted(cands, key=lambda z: -z[0]):
                j = int(row["j"])
                if any(o["j"] == j for o in open_.values()):
                    continue
                frac = min(base_risk * w / row["r"], max_pos, 1.0 - mv / eq_last)
                if frac < 0.005:
                    continue
                shares = frac * eq_last / row["entry"]
                cash -= shares * row["entry"]
                key = len(taken)
                taken.append({"who": row["who"], "R": row["R"], "entry_date": row["entry_date"], "w": w})
                if int(row["exit_t"]) <= t:                                     # stopped out the day it was bought
                    cash += shares * float(row["exit"])
                    continue
                open_[key] = {"j": j, "shares": shares, "exit_t": int(row["exit_t"]), "exit": float(row["exit"]), "last": float(row["entry"])}
                mv += shares * row["entry"]
        eq_last = cash + sum(o["shares"] * o["last"] for o in open_.values())
        eq.append(eq_last)
        gross.append(1.0 - cash / eq_last)
    idx = dates[max(i0, 1):i1]
    e = pd.Series(eq, index=idx)
    ret = e.pct_change().fillna(e.iloc[0] - 1.0)
    return {"excess": ret - rf.reindex(idx).fillna(0.0), "gross": pd.Series(gross, index=idx), "taken": pd.DataFrame(taken)}


def pstats(p: Dict[str, object], spy_ex: pd.Series) -> Dict[str, float]:
    ex = p["excess"]
    eq = (1 + ex).cumprod()
    tk = p["taken"]
    out = {"Sharpe": vb.sharpe(ex), "ann %": float((eq.iloc[-1] ** (252 / len(ex)) - 1) * 100),
           "vol %": float(ex.std() * np.sqrt(252) * 100), "maxDD %": float((eq / eq.cummax() - 1).min() * 100),
           "invested %": float(p["gross"].mean() * 100), "trades": len(tk)}
    if len(tk):
        out.update({"win %": float((tk["R"] > 0).mean() * 100), "avg R": float(tk["R"].mean())})
    out["alpha t vs SPY"] = jl.alpha_beta(ex, spy_ex.reindex(ex.index).fillna(0.0))["alpha t"]
    return out


def record_table(trades: pd.DataFrame, a: str, b: Optional[str]) -> pd.DataFrame:
    d = trades[(trades["entry_date"] >= a) & ((trades["entry_date"] <= b) if b else True) & (trades["reason"] != "open at end")]
    g = d.groupby("who")
    t = pd.DataFrame({"ideas": g.size(), "per year": g.size() / max((d["entry_date"].max() - d["entry_date"].min()).days / 365.25, 1),
                      "win %": g["R"].apply(lambda s: (s > 0).mean() * 100), "avg R": g["R"].mean(),
                      "t(avg R)": g["R"].apply(lambda s: s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan),
                      "avg win %": g["ret"].apply(lambda s: s[s > 0].mean() * 100), "avg loss %": g["ret"].apply(lambda s: s[s <= 0].mean() * 100),
                      "avg days": g.apply(lambda s: (s["exit_t"] - s["entry_t"]).mean())})
    return t.reindex(CONTRIBUTORS)


def build():
    from ..strategy_atlas import load_ohlc
    from . import data as vdata

    d = load_ohlc()
    spy, rf = d["SPY"]["Close"], d["BIL"]["Close"].pct_change()
    M = vdata.load()
    x = indicators(M, spy)
    dates, cols = x["C"].index, list(x["C"].columns)
    i0 = int(np.searchsorted(dates, pd.Timestamp(START)))
    for k in ("C", "O", "L", "sma10", "sma20", "ema21"):
        x[k + "n"] = x[k].to_numpy()
    x["Cn"], x["On"], x["Ln"] = x["C"].to_numpy(), x["O"].to_numpy(), x["L"].to_numpy()
    x["adr"] = x["adr"].to_numpy()
    x["low10"] = x["L"].rolling(10, min_periods=10).min().to_numpy()
    w30 = pd.DataFrame(np.nan, index=dates, columns=cols)
    w30.loc[x["w30"].index] = x["w30"].to_numpy()
    x["w30n"] = w30.to_numpy()
    ideas = []
    for fn in (qullamaggie_bo, qullamaggie_ep, kell_crossback, darvas, weinstein):
        ideas += fn(x, i0)
    tr = track_record(ideas, x, dates, cols)
    vj, Cref = vcp_and_jlaw(START)
    colpos = {c: i for i, c in enumerate(cols)}
    pos = pd.Series(np.arange(len(dates)), index=dates)
    for who, t in vj.items():
        if not len(t):
            continue
        add = pd.DataFrame({"who": who, "symbol": t["symbol"], "j": t["symbol"].map(colpos), "entry_t": pos.reindex(t["entry_date"]).to_numpy(),
                            "entry_date": t["entry_date"], "exit_t": pos.reindex(t["exit_date"]).to_numpy(), "exit_date": t["exit_date"],
                            "entry": t["entry"], "exit": t["exit"], "r": t["r"], "reason": t["reason"], "ret": t["ret"], "R": t["R_mult"]})
        tr = pd.concat([tr, add.dropna(subset=["j", "entry_t", "exit_t"])], ignore_index=True)
    tr["j"], tr["entry_t"], tr["exit_t"] = tr["j"].astype(int), tr["entry_t"].astype(int), tr["exit_t"].astype(int)
    return x, dates, tr, spy, rf


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    x, dates, tr, spy, rf = build()
    spy_ex = (spy.pct_change() - rf).reindex(dates).fillna(0.0)
    W = monthly_weights(tr, dates)
    periods = {"2017-26": (START, None), "2017-21": (START, "2021-12-31"), "2022-26": ("2022-01-01", None)}
    port_rows = {}
    for pname, (a, b) in periods.items():
        for mode, label in (("equal", "A equal weights"), ("skill", "B skill-weighted (PRIMARY)"), ("consensus", "C skill + consensus")):
            port_rows[f"{pname} | {label}"] = pstats(portfolio(tr, x, dates, rf, mode, start=a, end=b, weights=W), spy_ex)
        for who in CONTRIBUTORS:
            sub = tr[tr["who"] == who]
            if len(sub):
                port_rows[f"{pname} | alone: {who}"] = pstats(portfolio(sub, x, dates, rf, "equal", start=a, end=b), spy_ex)
        s = spy_ex.loc[a:b] if b else spy_ex.loc[a:]
        eq = (1 + s).cumprod()
        port_rows[f"{pname} | SPY"] = {"Sharpe": vb.sharpe(s), "ann %": float((eq.iloc[-1] ** (252 / len(s)) - 1) * 100),
                                       "vol %": float(s.std() * np.sqrt(252) * 100), "maxDD %": float((eq / eq.cummax() - 1).min() * 100)}
    prim = portfolio(tr, x, dates, rf, "skill", weights=W)
    core = vb.with_core(prim["excess"], prim["gross"])
    corr = pd.DataFrame({who: tr[tr["who"] == who].groupby("entry_date")["R"].mean().resample("ME").mean() for who in CONTRIBUTORS}).corr()
    Wy = W.groupby(W.index.year).mean()
    lines = ["# Retail TOPS: traders' methods weighted by their own record", "", "```", __doc__.strip(), "```", "",
             "## Each contributor's ideas, played one by one", "", "2017-2021:", "", record_table(tr, START, "2021-12-31").round(2).to_markdown(), "",
             "2022-2026:", "", record_table(tr, "2022-01-01", None).round(2).to_markdown(), "",
             "## Weights (yearly average of the monthly weights; 0 = paused)", "", Wy.round(2).to_markdown(), "",
             "## Portfolios (excess over T-bills)", "", pd.DataFrame(port_rows).T.round(2).to_markdown(), "",
             "## Monthly correlation of contributors' average R", "", corr.round(2).to_markdown(), "",
             "## B added to the live core (walk-forward weights)", "", pd.DataFrame(core).T.round(3).to_markdown(), ""]
    ok = all(core["core + VCP"][p] > core["core (live)"][p] for p in ("2019-26", "2021-26", "2024-05+"))
    lines += [f"Verdict: **{'ADOPT' if ok else 'reject'}** (raises the core's Sharpe in all three periods: {ok})"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
