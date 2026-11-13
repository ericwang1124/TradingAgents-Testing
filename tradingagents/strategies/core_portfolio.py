"""Core diversified portfolio as ETF positions (end-of-day), for backtest and live rebalancing.

Each strategy is a rule mapping data up to day t's close to ETF positions held from that close
(units of strategy capital, e.g. {"SPY": 1.0}). Strategy return on day t+1 = sum over ETFs of
position(t) * excess return(t+1) — identical to the atlas streams for the same rules.

Portfolio (walk-forward, refit each January on earlier years only):
  * every strategy scaled to 10% vol (trailing 60 days); weight proportional to its past mean
    scaled return when positive, else 0 (the "no-scenario baseline" that the selector study
    found hard to beat)
  * portfolio scaled to a volatility target (trailing 60 days), gross exposure capped
  * long-only: the paper account cannot short, so net negative ETF exposures are clipped to 0
"""

from __future__ import annotations

from typing import Callable, Dict, List

import numpy as np
import pandas as pd

ETFS = ["SPY", "QQQ", "IWM", "RSP", "TLT", "IEF", "GLD", "DBC", "UUP", "HYG", "USO", "XLK", "SVXY", "FXE", "FXY"]
SECTORS = ["XLU", "XLP", "XLV", "XLY", "XLK", "XLI", "XLE", "XLF", "XLB"]
UNIVERSE = sorted(set(ETFS + SECTORS + ["BIL", "BTC-USD"]))
# backtest series -> instrument actually traded (bitcoin is held through the spot ETF in market hours)
LIVE_TICKER = {"BTC-USD": "IBIT"}
TARGET_STRAT_VOL = 0.10
PORTFOLIO_VOL = 0.10
MAX_GROSS = 2.0
LEVERAGE = 2.0   # constant multiplier on the combined book (vol targeting tested worse: 0.70 vs 0.73)


def _rsi(c: pd.Series, n: int = 2) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _hold_until(enter: pd.Series, exit_: pd.Series) -> pd.Series:
    state, out = 0, []
    for e, x in zip(enter.fillna(False).to_numpy(), exit_.fillna(False).to_numpy()):
        if state == 0 and e:
            state = 1
        elif state == 1 and x:
            state = 0
        out.append(state)
    return pd.Series(out, index=enter.index, dtype=float)


def _one(index, ticker: str, amount) -> pd.DataFrame:
    return pd.DataFrame({ticker: amount}, index=index)


def strategy_positions(C: pd.DataFrame, H: pd.Series, L: pd.Series, sessions: pd.DatetimeIndex) -> Dict[str, pd.DataFrame]:
    """Positions decided at each close (index = decision date). ``sessions`` must extend at least
    one session past the last decision date so calendar rules know the next session."""
    idx = C.index
    r = C.pct_change()
    spy = C["SPY"]
    P: Dict[str, pd.DataFrame] = {}
    for t in ("SPY", "QQQ", "IWM", "RSP"):
        P[f"long {t}"] = _one(idx, t, 1.0)
    P["SPY trend: above SMA200"] = _one(idx, "SPY", (spy > spy.rolling(200).mean()).astype(float))
    P["SPY trend: above SMA50"] = _one(idx, "SPY", (spy > spy.rolling(50).mean()).astype(float))
    P["SPY 1-month momentum (21d ret > 0)"] = _one(idx, "SPY", (spy.pct_change(21) > 0).astype(float))
    # turn of month: hold over the next session if it is the month's last trading day or among its first 3
    s = pd.Series(sessions, index=sessions)
    last_day = (s.dt.month != s.dt.month.shift(-1)) & s.shift(-1).notna()  # unknown next session != month end
    nth = s.groupby([s.dt.year, s.dt.month]).cumcount() + 1
    tom = (last_day | (nth <= 3)).astype(float)
    nxt = tom.shift(-1).reindex(idx)  # position decided at close t applies to session t+1
    P["turn of month (last day + first 3)"] = _one(idx, "SPY", nxt.fillna(0.0))
    rs = _rsi(spy, 2)
    P["MR: RSI(2)<10 until RSI(2)>70"] = _one(idx, "SPY", _hold_until(rs < 10, rs > 70))
    down3 = (r["SPY"] < 0) & (r["SPY"].shift(1) < 0) & (r["SPY"].shift(2) < 0)
    P["MR: after 3 down days, exit on up close"] = _one(idx, "SPY", _hold_until(down3, r["SPY"] > 0))
    ibs = (spy - L) / (H - L).replace(0, np.nan)
    P["MR: IBS<0.2, hold 1 day"] = _one(idx, "SPY", (ibs < 0.2).astype(float))
    for t, name in (("TLT", "long bonds TLT"), ("IEF", "long bonds IEF"), ("GLD", "long gold"),
                    ("DBC", "long commodities DBC"), ("UUP", "long US dollar UUP"), ("HYG", "long high yield HYG"),
                    ("USO", "long oil USO"), ("FXE", "long euro FXE"), ("FXY", "long yen FXY")):
        P[name] = _one(idx, t, 1.0)
    assets = ["SPY", "TLT", "GLD", "DBC"]
    vol = r[assets].ewm(span=60).std() * np.sqrt(252)
    P["trend: TSMOM SPY/TLT/GLD/DBC"] = pd.DataFrame(
        {a: np.sign(C[a].pct_change(252)) * (0.10 / vol[a]).clip(upper=2) / len(assets) for a in assets}, index=idx)
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0)
    P["risk parity SPY/TLT/GLD/DBC"] = w
    mom6 = C[assets].pct_change(126)
    month = pd.Series(idx.month, index=idx)
    month_start = month != month.shift(1)
    # the atlas picks on the first session of each month and holds from that close
    pick = mom6.fillna(-np.inf).idxmax(axis=1).where(mom6.max(axis=1) > 0, "BIL").where(month_start).ffill()
    P["dual momentum: best of SPY/TLT/GLD/DBC"] = pd.DataFrame({a: (pick == a).astype(float) for a in assets}, index=idx)
    P["tech - market (XLK-SPY)"] = pd.DataFrame({"XLK": 1.0, "SPY": -1.0}, index=idx)
    smom = C[SECTORS].pct_change(126)
    top = smom.rank(axis=1, ascending=False).le(3).astype(float).where(month_start).ffill()
    sm = top / 3.0
    sm["SPY"] = -1.0
    P["sector momentum: top-3 minus SPY"] = sm
    P["short VIX futures (SVXY)"] = _one(idx, "SVXY", 1.0)
    if "BTC-USD" in C.columns:
        P["long bitcoin"] = _one(idx, "BTC-USD", 1.0)
    return P


def strategy_returns(P: Dict[str, pd.DataFrame], C: pd.DataFrame) -> pd.DataFrame:
    r = C.pct_change()
    rf = r["BIL"].fillna(0.0)
    ex = r.sub(rf, axis=0)
    out = {}
    for name, pos in P.items():
        cols = list(pos.columns)
        spread = name in ("tech - market (XLK-SPY)", "sector momentum: top-3 minus SPY")
        base = r[cols] if spread else ex[cols]  # long-short spreads are self-financing (no T-bill leg)
        out[name] = (pos.shift(1) * base).sum(axis=1, min_count=1).where(base.notna().any(axis=1))
    return pd.DataFrame(out)


def strategy_scale(R: pd.DataFrame) -> pd.DataFrame:
    vol = R.rolling(60, min_periods=40).std() * np.sqrt(252)
    return (TARGET_STRAT_VOL / vol).clip(upper=5.0)


def fit_weights(R_scaled_past: pd.DataFrame) -> pd.Series:
    mu = R_scaled_past.mean().where(R_scaled_past.notna().sum() >= 250)
    m = mu.clip(lower=0).fillna(0.0)
    return m / m.sum() if m.sum() > 0 else m


def combine(P: Dict[str, pd.DataFrame], weights: pd.DataFrame, scale_: pd.DataFrame) -> pd.DataFrame:
    """Net ETF exposure per decision date (before portfolio scaling)."""
    etfs = sorted({c for p in P.values() for c in p.columns})
    E = pd.DataFrame(0.0, index=weights.index, columns=etfs)
    for name, pos in P.items():
        if name not in weights.columns:
            continue
        k = (weights[name] * scale_[name]).fillna(0.0)
        E = E.add(pos.reindex(weights.index).fillna(0.0).mul(k, axis=0), fill_value=0.0)
    return E


def backtest(C: pd.DataFrame, H: pd.Series, L: pd.Series, years: List[int], long_only: bool = True,
             multiplier: pd.Series = None, vol_target: bool = False) -> Dict[str, pd.Series]:
    """Walk-forward core portfolio on ETF positions. Returns daily excess returns and diagnostics."""
    P = strategy_positions(C, H, L, C.index)
    R = strategy_returns(P, C)
    sc_ = strategy_scale(R)
    Rs = R * sc_.shift(1)
    W = pd.DataFrame(0.0, index=C.index, columns=R.columns)
    for y in years:
        past = Rs[Rs.index.year < y]
        W.loc[W.index.year == y] = fit_weights(past).to_numpy()
    E = combine(P, W, sc_)
    r = C.pct_change()
    ex = r.sub(r["BIL"].fillna(0.0), axis=0)
    raw = (E.shift(1) * ex[E.columns]).sum(axis=1)
    gross = E.abs().sum(axis=1)
    cap = MAX_GROSS / gross.replace(0, np.nan)
    if vol_target:
        pvol = raw.rolling(60, min_periods=40).std() * np.sqrt(252)
        lev = (PORTFOLIO_VOL / pvol).clip(upper=cap).fillna(0.0)
    else:
        lev = pd.Series(LEVERAGE, index=E.index).clip(upper=cap).fillna(0.0)
    if multiplier is not None:
        lev = (lev * multiplier.reindex(lev.index).fillna(1.0)).clip(upper=MAX_GROSS / gross.replace(0, np.nan)).fillna(0.0)
    Ef = E.mul(lev, axis=0)
    if long_only:
        Ef = Ef.clip(lower=0.0)
    ret = (Ef.shift(1) * ex[Ef.columns]).sum(axis=1)
    turnover = Ef.diff().abs().sum(axis=1).fillna(0.0)
    ret = ret - turnover * 2.0 / 1e4
    start = pd.Timestamp(f"{years[0]}-01-01")
    return {"returns": ret[ret.index >= start], "exposures": Ef[Ef.index >= start], "weights": W[W.index >= start],
            "strategy_returns": R}
