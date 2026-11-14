"""J Law's VCP method as fixed daily-bar rules, US stocks 2017-2026 (delisted names included).

    python -m tradingagents.strategies.vcp.jlaw

Translated from the user's notes on J Law's method. Written and committed before the first run on
real data. PRIMARY decides; the other rows are reported for information, not to pick a winner.

1. Screen at each close: price >= $12; 50-day average dollar volume >= $20M; >= 240 closes in the
   past year; close > SMA50 > SMA200, both averages above their value 21 sessions earlier; close within
   15% of the 52-week high; 1-year return in the top 20% of the day's universe.
2. Pattern at the close of t, over the past 250 sessions: start at the highest high, take the lowest
   low after it (contraction 1 = high -> low), then the highest high after that low and the lowest
   low after it (contraction 2), and so on; moves smaller than 3% are ignored. The VCP is the run of
   contractions starting with the first one <= 35% deep. Needed: at least 2 contractions, the first
   10%..35%, each shallower than the one before, the last <= 10%, average volume during the last
   decline below the 50-day average, the last high (the pivot) at least 3 sessions old, the last low
   before t, the base at least 15 sessions long, nothing in the window deeper than 60%.
3. Entries.
   pullback (PRIMARY): a breakout day is a close above the pivot on volume above both the prior
     day's and the 50-day average. Within the next 15 sessions, on the first day whose low is within
     2% above the pivot (or below it), whose close is no more than 3% below the pivot and above SMA50,
     whose volume is below the 50-day average, and with SMA10 or SMA20 within 3% of the pivot: buy at
     that close. The watch ends if a close falls more than 3% below the pivot.
   breakout: buy when price crosses the pivot intraday (at the pivot, or the open if it gaps above;
     skipped if the open is more than 2% above). If by the close the price is back below the pivot
     or the volume condition fails, sell at that close.
4. Stops and size. Pullback: 1% below the lowest of the pivot, the day's low and the supporting
   average(s). Breakout: 1% below the last contraction's low. A stop farther than 8% skips the trade;
   closer than 3% is set to 3%. Each trade risks 0.35% of equity; a position is at most 15% of
   equity; no leverage (gross <= 100%); cash earns T-bills. New trades risk half as much while fewer
   than 3 of the last 10 closed trades were winners, and half as much while SPY has had 4 or more
   distribution days (down >= 0.2% on higher volume than the day before) in the past 20 sessions.
   Candidates on the same day are taken in order of 1-year relative strength.
5. Exits. Initial stop (a gap below fills at the open). After a close 10% above entry the stop moves
   to 0.5% above entry and from then on a close below SMA20 sells. A close below SMA50 always sells.
   A stock whose data ends is sold at its last close. Costs 5 bp per side.

Reported alongside: breakout entry; both entries; SMA10 trail; sell into strength at 4x the risk;
at least 3 contractions; first contraction up to 50%; relative strength top 10%; no reduction after
losing streaks; no trades while SPY is below its 200-day average; 1% risk per trade (25% cap).
References: the fixed-window Minervini version (vcp.backtest), a screen-only momentum book (each Friday
the 20 highest relative-strength stocks that pass the screen, 5% each), SPY and 60/40 buy and hold.

Not testable here: revenue acceleration, earnings surprises and guidance, sector moves, hand-drawn
trend lines, the leverage of the competition account, and discretion.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from . import backtest as vb
from . import data as vdata

OUT = Path("results/opening_reversal/VCP_JLAW.md")
MAX_K = 6  # contractions kept per setup (the most recent ones)


@dataclass(frozen=True)
class JParams:
    min_price: float = 12.0
    min_dv: float = 20e6
    rs_min: float = 80.0
    near_high: float = 0.85
    lookback: int = 250
    min_depth: float = 0.03
    first_min: float = 0.10
    first_max: float = 0.35
    last_max: float = 0.10
    min_contractions: int = 2
    min_base: int = 15
    pivot_age: int = 3
    entry: str = "pullback"            # "pullback", "breakout" or "both"
    chase_max: float = 0.02
    pb_window: int = 15
    pb_above: float = 0.02
    pb_below: float = 0.03
    ma_tol: float = 0.03
    stop_pad: float = 0.01
    r_min: float = 0.03
    r_max: float = 0.08
    risk: float = 0.0035
    max_pos: float = 0.15
    throttle: bool = True
    dist_days: bool = True
    spy200: bool = False
    be_gain: float = 0.10
    trail_sma: int = 20
    target_r: Optional[float] = None
    cost: float = 5.0 / 1e4
    start: str = "2017-01-01"


# ------------------------------------------------------------------ screen
def prepare(M: Dict[str, pd.DataFrame], p: JParams) -> Dict[str, pd.DataFrame]:
    O, H, L, C, V = (M[k].astype("float64") for k in ("open", "high", "low", "close", "volume"))
    dv50 = (C * V).rolling(50, min_periods=45).mean()
    v50 = V.rolling(50, min_periods=45).mean()
    hist = C.notna().rolling(252, min_periods=1).sum()
    universe = (C >= p.min_price) & (dv50 >= p.min_dv) & (hist >= 240)
    s10, s20, s50, s200 = (C.rolling(n, min_periods=n).mean() for n in (10, 20, 50, 200))
    hi252 = H.rolling(252, min_periods=240).max()
    rs = C.pct_change(252, fill_method=None).where(universe).rank(axis=1, pct=True) * 100
    screen = (universe & (C > s50) & (s50 > s200) & (s50 > s50.shift(21)) & (s200 > s200.shift(21))
              & (C >= p.near_high * hi252) & (rs >= min(p.rs_min, 80.0)))
    return {"O": O, "H": H, "L": L, "C": C, "V": V, "v50": v50, "s10": s10, "s20": s20, "s50": s50,
            "rs": rs, "screen": screen, "universe": universe}


# ------------------------------------------------------------------ pattern
def contractions(h: np.ndarray, l: np.ndarray, t: int, lookback: int, min_depth: float) -> List[Tuple[int, int, float]]:
    """Nested swings on [t-lookback+1, t]: (index of high, index of low, depth). ``h`` must hold -inf
    and ``l`` +inf where data is missing."""
    s = max(0, t - lookback + 1)
    hh, ll = h[s:t + 1], l[s:t + 1]
    n = len(hh)
    a = int(np.argmax(hh))
    out = []
    while a < n - 1:
        i_lo = a + 1 + int(np.argmin(ll[a + 1:]))
        depth = 1.0 - ll[i_lo] / hh[a]
        if not depth >= min_depth:
            break
        out.append((s + a, s + i_lo, float(depth)))
        if i_lo >= n - 1:
            break
        a = i_lo + 1 + int(np.argmax(hh[i_lo + 1:]))
    return out


def scan(H: np.ndarray, L: np.ndarray, V: np.ndarray, v50: np.ndarray, rs: np.ndarray, screen: np.ndarray,
         i_start: int, lookback: int, min_depth: float) -> Dict[str, np.ndarray]:
    """Every (day, stock) that passes the screen and shows at least two contractions."""
    Hn = np.where(np.isnan(H), -np.inf, H)
    Ln = np.where(np.isnan(L), np.inf, L)
    ts, js, piv, piv_idx, low, low_idx, volr, rss, deps, his = ([] for _ in range(10))
    for j in range(Hn.shape[1]):
        idx = np.flatnonzero(screen[:, j])
        idx = idx[idx >= i_start]
        if not len(idx):
            continue
        h, l, v = Hn[:, j], Ln[:, j], V[:, j]
        for t in idx:
            seq = contractions(h, l, int(t), lookback, min_depth)
            if len(seq) < 2:
                continue
            a, i_lo, _ = seq[-1]
            seq = seq[-MAX_K:]
            d = np.full(MAX_K, np.nan, dtype=np.float32)
            hi = np.full(MAX_K, -1, dtype=np.int32)
            d[:len(seq)] = [x[2] for x in seq]
            hi[:len(seq)] = [x[0] for x in seq]
            ts.append(t); js.append(j); piv.append(h[a]); piv_idx.append(a); low.append(l[i_lo]); low_idx.append(i_lo)
            volr.append(np.nanmean(v[a + 1:i_lo + 1]) / v50[t, j] if v50[t, j] > 0 else np.nan)
            rss.append(rs[t, j]); deps.append(d); his.append(hi)
    return {"t": np.asarray(ts, dtype=np.int32), "j": np.asarray(js, dtype=np.int32), "pivot": np.asarray(piv),
            "piv_idx": np.asarray(piv_idx, dtype=np.int32), "low": np.asarray(low),
            "low_idx": np.asarray(low_idx, dtype=np.int32), "volr": np.asarray(volr), "rs": np.asarray(rss),
            "depths": np.asarray(deps, dtype=np.float32).reshape(-1, MAX_K),
            "his": np.asarray(his, dtype=np.int32).reshape(-1, MAX_K)}


def select(S: Dict[str, np.ndarray], p: JParams) -> Dict[int, List[Tuple[int, float, float]]]:
    """Setups that meet the pattern rules: day index -> [(stock column, pivot, last contraction low)]."""
    if not len(S["t"]):
        return {}
    D, HI, t = S["depths"], S["his"], S["t"]
    rows = np.arange(len(t))
    nval = (~np.isnan(D)).sum(axis=1)
    ok = D <= p.first_max                                   # NaN compares False
    k = ok.argmax(axis=1)
    d_first, d_last = D[rows, k], D[rows, nval - 1]
    with np.errstate(invalid="ignore"):
        shrinking = np.all(np.isnan(np.diff(D, axis=1)) | (np.diff(D, axis=1) < 0), axis=1)
        good = (ok.any(axis=1) & (nval - k >= p.min_contractions) & (d_first >= p.first_min) & (d_last <= p.last_max)
                & shrinking & (np.nanmax(D, axis=1) <= 0.60) & (t - HI[rows, k] >= p.min_base)
                & (t - S["piv_idx"] >= p.pivot_age) & (S["low_idx"] <= t - 1) & (S["volr"] < 1.0) & (S["rs"] >= p.rs_min))
    out: Dict[int, List[Tuple[int, float, float]]] = {}
    for i in np.flatnonzero(good):
        out.setdefault(int(t[i]), []).append((int(S["j"][i]), float(S["pivot"][i]), float(S["low"][i])))
    return out


# ------------------------------------------------------------------ simulation
@dataclass
class Pos:
    entry_i: int
    entry: float
    shares: float
    stop: float
    r: float
    kind: str
    target: Optional[float] = None
    active: bool = False


def simulate(ind: Dict[str, pd.DataFrame], by_day: Dict[int, List[Tuple[int, float, float]]], spy: pd.Series,
             spy_vol: pd.Series, rf: pd.Series, p: JParams) -> Dict[str, object]:
    C = ind["C"]
    dates, syms = C.index, np.array(C.columns)
    Cn, On, Hn, Ln, Vn = (ind[k].to_numpy() for k in ("C", "O", "H", "L", "V"))
    v50, s10, s20, s50, rs = (ind[k].to_numpy() for k in ("v50", "s10", "s20", "s50", "rs"))
    strail = s10 if p.trail_sma == 10 else s20
    spy_ok = (spy > spy.rolling(200).mean()).reindex(dates).fillna(False).to_numpy()
    dday = (spy.pct_change() <= -0.002) & (spy_vol > spy_vol.shift(1))
    dist = dday.astype(float).rolling(20).sum().reindex(dates).fillna(0.0).to_numpy()
    rfn = rf.reindex(dates).fillna(0.0).to_numpy()
    T = len(dates)
    i0 = int(np.searchsorted(dates, pd.Timestamp(p.start)))
    cash, eq_last = 1.0, 1.0
    positions: Dict[int, Pos] = {}
    pending: Dict[int, Tuple[float, int]] = {}
    recent: deque = deque(maxlen=10)
    last_px: Dict[int, float] = {}
    equity, gross, trades = [], [], []

    def close_out(j: int, t: int, px: float, reason: str) -> None:
        nonlocal cash
        ps = positions.pop(j)
        cash += ps.shares * px
        trades.append((syms[j], dates[ps.entry_i], dates[t], ps.kind, ps.entry, px, ps.r, reason, t - ps.entry_i))
        recent.append(1 if px > ps.entry else 0)

    for t in range(max(i0, 1), T):
        cash *= 1 + rfn[t]
        # ---- exits for positions carried into today
        for j in list(positions):
            ps = positions[j]
            c, o, h, l = Cn[t, j], On[t, j], Hn[t, j], Ln[t, j]
            if np.isnan(c):
                if t + 5 >= T or np.all(np.isnan(Cn[t:t + 5, j])):
                    close_out(j, t, last_px.get(j, ps.entry) * (1 - p.cost), "delisted")
                continue
            last_px[j] = c
            if l <= ps.stop:
                close_out(j, t, min(o, ps.stop) * (1 - p.cost), "breakeven stop" if ps.active else "stop")
            elif ps.target is not None and h >= ps.target:
                close_out(j, t, max(o, ps.target) * (1 - p.cost), "target")
            elif ps.active and c < strail[t, j]:
                close_out(j, t, c * (1 - p.cost), f"close below SMA{p.trail_sma}")
            elif c < s50[t, j]:
                close_out(j, t, c * (1 - p.cost), "close below SMA50")
            elif not ps.active and c >= ps.entry * (1 + p.be_gain):
                ps.active, ps.stop = True, max(ps.stop, ps.entry * 1.005)
        # ---- today's candidates
        mult = 1.0
        if p.throttle and len(recent) == 10 and sum(recent) < 3:
            mult *= 0.5
        if p.dist_days and dist[t - 1] >= 4:
            mult *= 0.5
        allowed = (not p.spy200) or bool(spy_ok[t - 1])
        cands = []                                           # (rs, j, kind, price, stop, confirmed)
        for j, P, low_p in by_day.get(t - 1, ()):
            c, o, h, v = Cn[t, j], On[t, j], Hn[t, j], Vn[t, j]
            if np.isnan(c) or np.isnan(o):
                continue
            confirmed = bool(c > P and v > Vn[t - 1, j] and v > v50[t - 1, j])
            if confirmed and p.entry in ("pullback", "both"):
                pending[j] = (P, t)
            if p.entry in ("breakout", "both") and h > P and o <= P * (1 + p.chase_max):
                cands.append((rs[t - 1, j], j, "breakout", max(o, P), low_p * (1 - p.stop_pad), confirmed))
        for j, (P, b) in list(pending.items()):
            if t <= b:
                continue
            c, l, v = Cn[t, j], Ln[t, j], Vn[t, j]
            if np.isnan(c) or t - b > p.pb_window or c < P * (1 - p.pb_below):
                del pending[j]
                continue
            if l <= P * (1 + p.pb_above) and v < v50[t - 1, j] and c > s50[t, j]:
                mas = [m for m in (s10[t, j], s20[t, j]) if abs(m / P - 1) <= p.ma_tol]
                if mas:
                    cands.append((rs[t - 1, j], j, "pullback", c, min([P, l] + mas) * (1 - p.stop_pad), True))
                    del pending[j]
        # ---- entries (sized on yesterday's equity)
        mv = sum(ps.shares * last_px.get(j, ps.entry) for j, ps in positions.items())
        for _, j, kind, px, stop, confirmed in sorted(cands, key=lambda x: -np.nan_to_num(x[0])):
            if j in positions or not allowed:
                continue
            entry = px * (1 + p.cost)
            r = (entry - stop) / entry
            if r > p.r_max:
                continue
            r = max(r, p.r_min)
            stop = entry * (1 - r)
            frac = min(p.risk * mult / r, p.max_pos, 1.0 - mv / eq_last)
            if frac < 0.01:
                continue
            shares = frac * eq_last / entry
            cash -= shares * entry
            c, l = Cn[t, j], Ln[t, j]
            positions[j] = Pos(t, entry, shares, stop, r, kind, entry * (1 + p.target_r * r) if p.target_r else None)
            last_px[j] = c
            mv += shares * c
            if kind == "breakout":                           # bought intraday: the rest of the day still counts
                if l <= stop:
                    close_out(j, t, stop * (1 - p.cost), "stop")
                    mv -= shares * c
                elif not confirmed:
                    close_out(j, t, c * (1 - p.cost), "breakout not confirmed")
                    mv -= shares * c
        eq_last = cash + sum(ps.shares * last_px.get(j, ps.entry) for j, ps in positions.items())
        equity.append(eq_last)
        gross.append(1.0 - cash / eq_last)
    idx = dates[max(i0, 1):]
    eqs = pd.Series(equity, index=idx)
    ret = eqs.pct_change().fillna(eqs.iloc[0] - 1.0)
    tr = pd.DataFrame(trades, columns=["symbol", "entry_date", "exit_date", "kind", "entry", "exit", "r", "reason", "days"])
    if len(tr):
        tr["ret"] = tr["exit"] / tr["entry"] - 1
        tr["R_mult"] = tr["ret"] / tr["r"]
    return {"ret": ret, "excess": ret - rf.reindex(idx).fillna(0.0), "gross": pd.Series(gross, index=idx),
            "trades": tr, "open": len(positions)}


# ------------------------------------------------------------------ evaluation
def trade_stats(tr: pd.DataFrame) -> Dict[str, float]:
    if not len(tr):
        return {"trades": 0}
    w, lo = tr.loc[tr["ret"] > 0, "ret"], tr.loc[tr["ret"] <= 0, "ret"]
    return {"trades": len(tr), "win %": float(len(w) / len(tr) * 100), "avg win %": float(w.mean() * 100) if len(w) else np.nan,
            "avg loss %": float(lo.mean() * 100) if len(lo) else np.nan, "avg R": float(tr["R_mult"].mean()),
            "avg days": float(tr["days"].mean())}


def alpha_beta(y: pd.Series, x: pd.Series) -> Dict[str, float]:
    d = pd.concat([y, x], axis=1).dropna()
    Y, X = d.iloc[:, 0].to_numpy(), np.c_[np.ones(len(d)), d.iloc[:, 1].to_numpy()]
    b = np.linalg.solve(X.T @ X, X.T @ Y)
    e = Y - X @ b
    se = np.sqrt(np.diag(e @ e / (len(Y) - 2) * np.linalg.inv(X.T @ X)))
    return {"beta": float(b[1]), "alpha %/yr": float(b[0] * 252 * 100), "alpha t": float(b[0] / se[0])}


def screen_momentum(ind: Dict[str, pd.DataFrame], rf: pd.Series, p: JParams, n: int = 20) -> pd.Series:
    """Each Friday the n highest relative-strength stocks that pass the screen, 1/n each (no pattern)."""
    C, ok, rs = ind["C"], ind["screen"], ind["rs"]
    dates = C.index
    W = pd.DataFrame(np.nan, index=dates, columns=C.columns)
    for t in dates[dates.dayofweek == 4]:
        row = pd.Series(0.0, index=C.columns)
        top = rs.loc[t].where(ok.loc[t]).dropna().nlargest(n).index
        row[top] = 1.0 / n
        W.loc[t] = row
    W = W.ffill().fillna(0.0)
    r = C.pct_change(fill_method=None).fillna(0.0)
    rfr = rf.reindex(dates).fillna(0.0)
    out = (W.shift(1) * r).sum(axis=1) - W.diff().abs().sum(axis=1) * p.cost - W.shift(1).sum(axis=1) * rfr
    return out[out.index >= p.start]


def run() -> Dict[str, object]:
    from ..strategy_atlas import load_ohlc

    M = vdata.load()
    d = load_ohlc()
    spy, spy_vol = d["SPY"]["Close"], d["SPY"]["Volume"]
    rf = d["BIL"]["Close"].pct_change()
    base = JParams()
    # reference: fixed-window Minervini version
    mp = vb.Params()
    mind = vb.indicators(M, mp)
    msim = vb.simulate(mind, spy, rf, mp)
    del mind
    ind = prepare(M, base)
    i_start = int(np.searchsorted(ind["C"].index, pd.Timestamp(base.start))) - 1
    S = scan(ind["H"].to_numpy(), ind["L"].to_numpy(), ind["V"].to_numpy(), ind["v50"].to_numpy(), ind["rs"].to_numpy(),
             ind["screen"].to_numpy(), i_start, base.lookback, base.min_depth)
    variants = {
        "PRIMARY: pullback entry, SMA20 trail": base,
        "breakout entry": replace(base, entry="breakout"),
        "both entries": replace(base, entry="both"),
        "pullback, SMA10 trail": replace(base, trail_sma=10),
        "pullback, sell at 4R": replace(base, target_r=4.0),
        "pullback, >= 3 contractions": replace(base, min_contractions=3),
        "pullback, first contraction up to 50%": replace(base, first_max=0.50),
        "pullback, RS top 10%": replace(base, rs_min=90.0),
        "pullback, no losing-streak reduction": replace(base, throttle=False),
        "pullback, no trades while SPY < SMA200": replace(base, spy200=True),
        "pullback, 1% risk per trade": replace(base, risk=0.01, max_pos=0.25),
    }
    rows, sims, setups_per_day = {}, {}, {}
    for name, p in variants.items():
        by_day = select(S, p)
        sim = simulate(ind, by_day, spy, spy_vol, rf, p)
        sims[name] = sim
        rows[name] = {**vb.stats(sim["excess"], sim["gross"]), **trade_stats(sim["trades"])}
        setups_per_day[name] = float(np.mean([len(v) for v in by_day.values()])) if by_day else 0.0
    prim = sims["PRIMARY: pullback entry, SMA20 trail"]
    idx = prim["excess"].index
    spy_ex = (spy.pct_change() - rf).reindex(idx).fillna(0.0)
    s6040 = (0.6 * spy.pct_change() + 0.4 * d["IEF"]["Close"].pct_change() - rf).reindex(idx).fillna(0.0)
    rows["reference: Minervini fixed-window VCP"] = {**vb.stats(msim["excess"].reindex(idx).fillna(0.0), msim["gross"].reindex(idx)),
                                                     **trade_stats(msim["trades"].assign(kind="breakout") if len(msim["trades"]) else msim["trades"])}
    mom = screen_momentum(ind, rf, base).reindex(idx).fillna(0.0)
    rows["reference: screen only, top-20 momentum"] = vb.stats(mom)
    rows["SPY buy and hold"] = vb.stats(spy_ex)
    rows["60/40 SPY/IEF"] = vb.stats(s6040)
    table = pd.DataFrame(rows).T
    regress = {name: alpha_beta(r, spy_ex) for name, r in (
        ("PRIMARY", prim["excess"]), ("breakout entry", sims["breakout entry"]["excess"]),
        ("both entries", sims["both entries"]["excess"]), ("screen only, top-20 momentum", mom),
        ("Minervini fixed-window", msim["excess"].reindex(idx).fillna(0.0)))}
    tr = prim["trades"]
    yearly = pd.DataFrame({
        "J Law %": prim["excess"].groupby(idx.year).apply(lambda x: (1 + x).prod() - 1) * 100,
        "SPY %": spy_ex.groupby(idx.year).apply(lambda x: (1 + x).prod() - 1) * 100,
        "avg invested %": prim["gross"].groupby(idx.year).mean() * 100,
        "trades": tr.groupby(tr["entry_date"].dt.year).size() if len(tr) else 0})
    both_tr = sims["both entries"]["trades"]
    by_kind = pd.DataFrame({k: trade_stats(g) for k, g in both_tr.groupby("kind")}).T if len(both_tr) else pd.DataFrame()
    core = vb.with_core(prim["excess"], prim["gross"])
    return {"table": table, "regress": pd.DataFrame(regress).T, "yearly": yearly, "by_kind": by_kind, "core": core,
            "trades": tr, "all_sims": sims, "setups_per_day": setups_per_day, "n_scan": len(S["t"]),
            "universe": float(ind["universe"].sum(axis=1).loc[base.start:].median()),
            "screened": float(ind["screen"].sum(axis=1).loc[base.start:].median()), "columns": M["close"].shape[1]}


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    res = run()
    tr = res["trades"]
    core = pd.DataFrame(res["core"]).T
    lines = ["# J Law's VCP method as fixed rules", "", "```", __doc__.strip(), "```", "",
             f"Data: {res['columns']} stock columns (delisted included). Median day: {res['universe']:.0f} stocks in the universe, "
             f"{res['screened']:.0f} pass the screen; {res['n_scan']:,} stock-days with at least two contractions.", "",
             "## Results 2017-2026 (excess over T-bills)", "", res["table"].round(2).to_markdown(), "",
             "## Against SPY (daily regression)", "", res["regress"].round(2).to_markdown(), "",
             "## By year (primary)", "", res["yearly"].round(1).to_markdown(), "",
             "## Breakout vs pullback entries (from the run that takes both)", "", res["by_kind"].round(2).to_markdown(), ""]
    if len(tr):
        by_reason = tr.groupby("reason").agg(n=("ret", "size"), avg_ret_pct=("ret", lambda x: x.mean() * 100), avg_R=("R_mult", "mean"))
        best = tr.nlargest(10, "ret")[["symbol", "entry_date", "exit_date", "ret", "R_mult", "days", "reason"]]
        worst = tr.nsmallest(5, "ret")[["symbol", "entry_date", "exit_date", "ret", "R_mult", "days", "reason"]]
        lines += ["## Exits (primary)", "", by_reason.round(2).to_markdown(), "",
                  "## Ten best and five worst trades (primary)", "", best.round(3).to_markdown(index=False), "",
                  worst.round(3).to_markdown(index=False), ""]
    lines += ["## Added to the live core (walk-forward weights)", "", core.round(3).to_markdown()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
