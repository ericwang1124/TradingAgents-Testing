"""Strategy x scenario atlas: which strategies have worked in which market scenarios.

    python -m tradingagents.strategies.strategy_atlas

Breadth first: ~37 daily strategy return streams (2007-2026; SPY intraday streams 2019-2026) are
cut by ~11 scenario dimensions, each known at the prior close. For every (strategy, scenario
state) the Sharpe ratio is reported for the whole sample and for two halves; a cell is flagged
"usable" when positive (>= 0.5) in both halves and "avoid" when negative (<= -0.3) in both.
This is descriptive: no parameter is fitted, but scanning many cells will throw up false
positives, so flagged cells are candidates to test, not conclusions.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .opening_reversal.data import default_cache_dir

TICKERS = ["SPY", "QQQ", "IWM", "RSP", "IWD", "IWF", "USMV", "TLT", "IEF", "GLD", "DBC", "UUP", "HYG", "LQD",
           "BIL", "XLU", "XLP", "XLV", "XLY", "XLK", "XLI", "XLE", "XLF", "XLB", "^VIX", "^VIX3M", "^TNX",
           "^PUT", "VIXY", "SVXY", "USO", "FXE", "FXY", "BTC-USD",
           # macro gauges (scenarios only)
           "EURUSD=X", "JPY=X", "DX-Y.NYB", "GC=F", "CL=F", "HG=F", "^MOVE"]
FRED_SERIES = {"DGS2": "2y Treasury yield", "T10Y2Y": "10y-2y spread", "DFII10": "10y real yield",
               "T10YIE": "10y breakeven inflation"}
VOLUME_TICKERS = ("SPY", "QQQ", "IWM")
# policy: fed funds, target upper bound, Fed assets (weekly), Treasury General Account (weekly),
# overnight reverse repo, daily news-based Economic Policy Uncertainty, monthly trade-policy uncertainty
POLICY_SERIES = ("DFF", "DFEDTARU", "WALCL", "WTREGEN", "RRPONTSYD", "USEPUINDXD", "EPUTRADE")
SECTORS = ["XLU", "XLP", "XLV", "XLY", "XLK", "XLI", "XLE", "XLF", "XLB"]
START = "2007-06-01"
INTRADAY_CSV = Path("results/opening_reversal/regime_now_streams.csv")


# ----------------------------------------------------------------------------------- data
def load_ohlc(refresh: bool = False) -> Dict[str, pd.DataFrame]:
    cache = default_cache_dir() / "atlas"
    cache.mkdir(parents=True, exist_ok=True)
    out = {}
    for t in TICKERS:
        path = cache / f"{t.replace('^', '_')}.csv"
        if path.exists() and not refresh:
            cached = pd.read_csv(path, index_col=0, parse_dates=True)
            if "Volume" in cached.columns or t not in VOLUME_TICKERS:
                out[t] = cached
                continue
        import yfinance as yf

        h = yf.Ticker(t).history(period="max", auto_adjust=True)[["Open", "High", "Low", "Close", "Volume"]]
        h.index = pd.DatetimeIndex(h.index.date)
        h.to_csv(path)
        out[t] = h
    return out


def load_fred(series_id: str, refresh: bool = False) -> pd.Series:
    path = default_cache_dir() / "atlas" / f"fred_{series_id}.csv"
    if refresh or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}").to_csv(path, index=False)
    s = pd.read_csv(path, parse_dates=["observation_date"]).set_index("observation_date")[series_id]
    return pd.to_numeric(s, errors="coerce")


def load_cpi() -> pd.Series:
    return load_fred("CPIAUCSL")


# ----------------------------------------------------------------------------- strategies
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
    return pd.Series(out, index=enter.index)


def build_strategies(d: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    cal = d["SPY"].index[d["SPY"].index >= START]
    C = pd.DataFrame({t: d[t]["Close"] for t in TICKERS}).reindex(cal)
    r = C.pct_change()
    rf = r["BIL"].fillna(0.0)
    ex = r.sub(rf, axis=0)
    spy = d["SPY"].reindex(cal)
    S = pd.DataFrame(index=cal)
    lag = lambda s: s.shift(1).fillna(0)  # position decided at the prior close

    # equity beta / timing
    for t in ("SPY", "QQQ", "IWM", "RSP"):
        S[f"long {t}"] = ex[t]
    S["SPY trend: above SMA200"] = ex["SPY"] * lag((C["SPY"] > C["SPY"].rolling(200).mean()).astype(float))
    S["SPY trend: above SMA50"] = ex["SPY"] * lag((C["SPY"] > C["SPY"].rolling(50).mean()).astype(float))
    S["SPY 1-month momentum (21d ret > 0)"] = ex["SPY"] * lag((C["SPY"].pct_change(21) > 0).astype(float))
    S["SPY overnight only"] = spy["Open"] / spy["Close"].shift(1) - 1 - rf / 2
    S["SPY intraday only"] = spy["Close"] / spy["Open"] - 1 - rf / 2
    dom = pd.Series(cal.day, index=cal)
    month = pd.Series(cal.month, index=cal)
    last_day = month != month.shift(-1)
    nth = dom.groupby([cal.year, cal.month]).cumcount() + 1
    # calendar rule, known in advance: hold on the month's last trading day and its first three
    S["turn of month (last day + first 3)"] = ex["SPY"] * (last_day | (nth <= 3)).astype(float)
    # short-term mean reversion
    rs = _rsi(C["SPY"], 2)
    S["MR: RSI(2)<10 until RSI(2)>70"] = ex["SPY"] * lag(_hold_until(rs < 10, rs > 70).astype(float))
    down3 = (r["SPY"] < 0) & (r["SPY"].shift(1) < 0) & (r["SPY"].shift(2) < 0)
    S["MR: after 3 down days, exit on up close"] = ex["SPY"] * lag(_hold_until(down3, r["SPY"] > 0).astype(float))
    ibs = (spy["Close"] - spy["Low"]) / (spy["High"] - spy["Low"]).replace(0, np.nan)
    S["MR: IBS<0.2, hold 1 day"] = ex["SPY"] * lag((ibs < 0.2).astype(float))
    # multi-asset
    for t, name in (("TLT", "long bonds TLT"), ("IEF", "long bonds IEF"), ("GLD", "long gold"),
                    ("DBC", "long commodities DBC"), ("UUP", "long US dollar UUP"), ("HYG", "long high yield HYG"),
                    ("USO", "long oil USO"), ("FXE", "long euro FXE"), ("FXY", "long yen FXY"),
                    ("BTC-USD", "long bitcoin")):
        S[name] = ex[t]
    assets = ["SPY", "TLT", "GLD", "DBC"]
    vol = r[assets].ewm(span=60).std() * np.sqrt(252)
    legs = [np.sign(C[a].pct_change(252)).shift(1) * (0.10 / vol[a]).clip(upper=2).shift(1) * ex[a] for a in assets]
    S["trend: TSMOM SPY/TLT/GLD/DBC"] = pd.concat(legs, axis=1).mean(axis=1)
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0).shift(1)
    S["risk parity SPY/TLT/GLD/DBC"] = (w * ex[assets]).sum(axis=1)
    mom6 = C[assets].pct_change(126)
    month_start = month != month.shift(1)
    pick = mom6.fillna(-np.inf).idxmax(axis=1).where(mom6.max(axis=1) > 0, "BIL").where(month_start).ffill().shift(1)
    S["dual momentum: best of SPY/TLT/GLD/DBC"] = pd.Series(
        [ex.at[i, p] if isinstance(p, str) and p != "BIL" else 0.0 for i, p in zip(cal, pick)], index=cal)
    # styles / sectors (long-short spreads)
    S["value - growth (IWD-IWF)"] = r["IWD"] - r["IWF"]
    S["small - large (IWM-SPY)"] = r["IWM"] - r["SPY"]
    S["low vol - market (USMV-SPY)"] = r["USMV"] - r["SPY"]
    S["defensive - cyclical sectors"] = r[["XLU", "XLP", "XLV"]].mean(axis=1) - r[["XLY", "XLK", "XLI"]].mean(axis=1)
    S["energy - market (XLE-SPY)"] = r["XLE"] - r["SPY"]
    S["tech - market (XLK-SPY)"] = r["XLK"] - r["SPY"]
    smom = C[SECTORS].pct_change(126)
    top = smom.rank(axis=1, ascending=False).le(3).astype(float).where(month_start).ffill().shift(1)
    S["sector momentum: top-3 minus SPY"] = (top * r[SECTORS]).sum(axis=1) / 3 - r["SPY"]
    # volatility
    S["put writing (Cboe PUT index)"] = ex["^PUT"]
    S["long VIX futures (VIXY)"] = ex["VIXY"]
    S["short VIX futures (SVXY)"] = ex["SVXY"]

    # intraday SPY streams (2019+), from our own 1-minute backtests
    if INTRADAY_CSV.exists():
        intr = pd.read_csv(INTRADAY_CSV, index_col=0, parse_dates=True)
        for col, name in (("high-eff continuation (2021+)", "intraday: high-efficiency open continuation"),
                          ("morning noise-area momentum", "intraday: morning noise-area momentum"),
                          ("full-day noise-area momentum", "intraday: full-day noise-area momentum"),
                          ("always continuation 10:00->close", "intraday: follow first 30 min to close"),
                          ("fade (gap-down rally short)", "intraday: fade gap-down rally (short)")):
            if col in intr:
                S[name] = intr[col].reindex(cal)
    return S


# ------------------------------------------------------------------------------ scenarios
def build_scenarios(d: Dict[str, pd.DataFrame], cpi: pd.Series, cal: pd.DatetimeIndex) -> pd.DataFrame:
    C = pd.DataFrame({t: d[t]["Close"] for t in TICKERS}).reindex(cal)
    spy = C["SPY"]
    sc = pd.DataFrame(index=cal)
    sc["trend vs SMA200"] = np.where(spy > spy.rolling(200).mean(), "above", "below")
    sc["trend vs SMA50"] = np.where(spy > spy.rolling(50).mean(), "above", "below")
    sc["VIX level"] = pd.cut(C["^VIX"], [0, 15, 20, 30, 1000], labels=["<15", "15-20", "20-30", ">=30"], right=False).astype(str)
    sc["VIX term structure"] = np.where(C["^VIX"] / C["^VIX3M"] >= 1, "backwardation", "contango")
    dd = spy / spy.rolling(252, min_periods=60).max() - 1
    sc["drawdown from 52w high"] = pd.cut(-dd, [-1, 0.05, 0.10, 0.20, 2], labels=["<5%", "5-10%", "10-20%", ">=20%"]).astype(str)
    sc["1-month SPY return"] = np.where(spy.pct_change(21) > 0, "up", "down")
    yoy = cpi.pct_change(12)
    infl_up = pd.Series(((yoy - yoy.shift(6)) > 0).to_numpy(), index=cpi.index + pd.DateOffset(days=45))
    sc["inflation direction (CPI y/y vs 6m ago)"] = np.where(infl_up.sort_index().reindex(cal, method="ffill").fillna(False).astype(bool), "rising", "falling")
    sc["10y yield 3-month change"] = np.where(C["^TNX"].diff(63) > 0, "rising", "falling")
    credit = C["HYG"] / C["LQD"]
    sc["credit (HYG/LQD vs SMA50)"] = np.where(credit > credit.rolling(50).mean(), "risk-on", "risk-off")
    sc["US dollar (UUP vs SMA50)"] = np.where(C["UUP"] > C["UUP"].rolling(50).mean(), "strong", "weak")
    rv = np.log(spy).diff().rolling(20).std() * np.sqrt(252) * 100
    sc["implied - realized vol (VIX - RV20)"] = np.where(C["^VIX"] - rv > 0, "VIX > realized", "VIX < realized")

    # ---- macro gauges (FX, commodities, rates) --------------------------------------------
    def px(t):  # 24h / differently-scheduled markets: last print on or before each SPY close
        s = d[t]["Close"].where(d[t]["Close"] > 0)  # WTI printed negative in April 2020
        return s.reindex(s.index.union(cal)).ffill().reindex(cal)

    def shock(s: pd.Series, down: str, up: str) -> pd.Series:
        """21-day log move vs its own trailing-year spread: <= -1 sd / normal / >= +1 sd."""
        m = np.log(s).diff(21)
        z = m / m.rolling(252, min_periods=126).std()
        return pd.Series(np.where(z >= 1, up, np.where(z <= -1, down, "normal")), index=s.index).where(z.notna())

    sc["EUR/USD 1-month move"] = shock(px("EURUSD=X"), "euro plunge (USD up)", "euro surge (USD down)")
    sc["USD/JPY 1-month move"] = shock(px("JPY=X"), "yen surge (USDJPY down)", "yen plunge (USDJPY up)")
    sc["dollar index DXY 1-month move"] = shock(px("DX-Y.NYB"), "DXY plunge", "DXY surge")
    sc["gold 1-month move"] = shock(px("GC=F"), "gold plunge", "gold surge")
    sc["oil (WTI) 1-month move"] = shock(px("CL=F"), "oil plunge", "oil surge")
    sc["bitcoin 1-month move"] = shock(px("BTC-USD"), "BTC plunge", "BTC surge")
    cg = px("HG=F") / px("GC=F")
    sc["copper/gold ratio vs SMA50"] = np.where(cg > cg.rolling(50).mean(), "rising (growth)", "falling").astype(object)
    sc.loc[cg.rolling(50).mean().isna(), "copper/gold ratio vs SMA50"] = None
    move = px("^MOVE")
    sc["bond volatility MOVE vs 1y median"] = np.where(move > move.rolling(252, min_periods=126).median(), "high", "low").astype(object)
    # FRED: values dated t are typically published on t+1, so lag one extra session
    fred = {k: load_fred(k).reindex(load_fred(k).index.union(cal)).ffill().reindex(cal).shift(1) for k in FRED_SERIES}
    curve = fred["T10Y2Y"]
    sc["yield curve 10y-2y level"] = pd.cut(curve, [-10, 0, 0.5, 10], labels=["inverted", "flat 0-0.5", "steep >0.5"]).astype(str)
    sc["yield curve 3-month change"] = np.where(curve.diff(63) > 0, "steepening", "flattening")
    sc["2y yield 3-month change"] = np.where(fred["DGS2"].diff(63) > 0, "rising", "falling")
    sc["10y real yield 3-month change"] = np.where(fred["DFII10"].diff(63) > 0, "rising", "falling")
    sc["10y breakeven inflation 3-month change"] = np.where(fred["T10YIE"].diff(63) > 0, "rising", "falling")

    # ---- trading volume (SPY shares, relative to its own history) ------------------------
    vol = d["SPY"]["Volume"].reindex(cal).replace(0, np.nan)
    rel = vol / vol.rolling(20, min_periods=15).median().shift(1)
    sc["SPY volume vs 20d median"] = pd.cut(rel, [0, 0.8, 1.3, 2.0, 1e9], labels=["low <0.8x", "normal", "high 1.3-2x", "spike >=2x"]).astype(str)
    sc.loc[rel.isna(), "SPY volume vs 20d median"] = None
    act = vol.rolling(20).mean() / vol.rolling(252, min_periods=126).median()
    sc["SPY 20d volume vs 1y median"] = np.where(act > 1.15, "active", np.where(act < 0.85, "quiet", "normal")).astype(object)
    sc.loc[act.isna(), "SPY 20d volume vs 1y median"] = None
    ret = spy.pct_change()
    upv, dnv = vol.where(ret > 0, 0).rolling(10).sum(), vol.where(ret < 0, 0).rolling(10).sum()
    bal = upv / dnv.replace(0, np.nan)
    sc["up/down volume balance (10d)"] = np.where(bal > 1.25, "accumulation", np.where(bal < 0.8, "distribution", "neutral")).astype(object)
    heavy = rel > 1.2
    sc["price-volume (last day)"] = np.select([(ret > 0) & heavy, (ret > 0) & ~heavy, (ret < 0) & heavy, (ret < 0) & ~heavy],
                                              ["up on heavy volume", "up on light volume", "down on heavy volume", "down on light volume"],
                                              default="flat").astype(object)
    sc.loc[rel.isna(), "price-volume (last day)"] = None

    # ---- policy -----------------------------------------------------------------------------
    pol = {k: load_fred(k) for k in POLICY_SERIES}
    daily = lambda s, lag=1: s.reindex(s.index.union(cal)).ffill().reindex(cal).shift(lag)
    ff = daily(pol["DFF"])
    chg = ff - ff.shift(126)
    sc["Fed policy cycle (fed funds 6m change)"] = np.where(chg > 0.25, "hiking", np.where(chg < -0.25, "cutting", "on hold")).astype(object)
    from .opening_reversal.events import load_fomc_days

    fomc = sorted(pd.Timestamp(x) for x in load_fomc_days())
    tgt = pol["DFEDTARU"].combine_first(pol["DFF"].rolling(5).median()).sort_index()
    decision = pd.Series(index=cal, dtype=object)
    for m in fomc:
        if m > cal[-1] or m < cal[0]:
            continue
        before, after = tgt.asof(m - pd.Timedelta(days=1)), tgt.asof(m + pd.Timedelta(days=2))
        verdict = "hike" if after - before > 0.1 else ("cut" if after - before < -0.1 else "hold")
        decision.loc[decision.index > m] = verdict  # from the session after the statement on
    sc["last FOMC decision"] = decision
    # session index of each statement day (first session on/after it), then distance in sessions
    mpos = np.unique(cal.searchsorted(pd.DatetimeIndex(fomc)))
    mpos = mpos[mpos < len(cal)]
    i = np.arange(len(cal))
    k = np.searchsorted(mpos, i, side="left")           # first meeting at or after session i
    to_next = pd.Series(np.where(k < len(mpos), mpos[np.minimum(k, len(mpos) - 1)] - i, np.nan), index=cal)
    kp = np.searchsorted(mpos, i, side="left") - 1      # last meeting strictly before session i
    since_prev = pd.Series(np.where(kp >= 0, i - mpos[np.maximum(kp, 0)], np.nan), index=cal)
    sc["FOMC calendar"] = np.select([to_next == 0, to_next == 1, since_prev == 1, (to_next > 1) & (to_next <= 4)],
                                    ["FOMC day", "day before FOMC", "day after FOMC", "FOMC week (other)"],
                                    default="no FOMC").astype(object)
    assets = daily(pol["WALCL"], lag=2)  # weekly, Wednesday level published Thursday
    sc["Fed balance sheet 13w change"] = np.where(assets.pct_change(63) > 0.01, "expanding (QE)",
                                                  np.where(assets.pct_change(63) < -0.01, "shrinking (QT)", "flat")).astype(object)
    net = assets - daily(pol["WTREGEN"], lag=2) - daily(pol["RRPONTSYD"]).fillna(0) * 1000  # RRP is in $bn
    sc["net liquidity (Fed assets - TGA - RRP) 13w change"] = np.where(net.diff(63) > 0, "rising", "falling")
    epu = daily(pol["USEPUINDXD"])
    e = epu.rolling(5).mean() / epu.rolling(252, min_periods=126).median()
    sc["policy uncertainty EPU (5d avg vs 1y median)"] = np.where(e > 1.5, "spike >1.5x", np.where(e > 1.0, "elevated", "low")).astype(object)
    sc.loc[e.isna(), "policy uncertainty EPU (5d avg vs 1y median)"] = None
    tpu = pol["EPUTRADE"]
    tpu = pd.Series(tpu.to_numpy(), index=tpu.index + pd.DateOffset(days=45))  # monthly, published with a lag
    tpu_d = tpu.reindex(tpu.index.union(cal)).ffill().reindex(cal)
    sc["trade policy uncertainty vs 3y median"] = np.where(tpu_d > tpu_d.rolling(756, min_periods=252).median() * 1.5, "high", "normal").astype(object)
    out = sc.shift(1)  # market data: known at the prior close
    # The FOMC calendar is published in advance, and the decision series already starts on the
    # session after the statement, so neither gets the extra one-day lag.
    out["FOMC calendar"] = sc["FOMC calendar"]
    out["last FOMC decision"] = sc["last FOMC decision"]
    return out


# --------------------------------------------------------------------------------- atlas
def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(252) if len(x) > 20 and x.std() > 0 else np.nan


def atlas(S: pd.DataFrame, sc: pd.DataFrame) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    tables, flags = {}, []
    for dim in sc.columns:
        rows = {}
        states = sorted(s for s in sc[dim].dropna().unique() if s not in ("nan", "None"))
        for strat in S.columns:
            x = S[strat]
            valid = x.dropna()
            if valid.empty:
                continue
            first, last = valid.index[0], valid.index[-1]
            mid = first + (last - first) / 2
            row = {}
            for st in states:
                mask = sc[dim] == st
                full = _sharpe(x[mask])
                h1, h2 = _sharpe(x[mask & (x.index < mid)]), _sharpe(x[mask & (x.index >= mid)])
                n = int(x[mask].notna().sum())
                tag = ""
                if not np.isnan(h1) and not np.isnan(h2):
                    if h1 >= 0.5 and h2 >= 0.5:
                        tag = " ✓"
                    elif h1 <= -0.3 and h2 <= -0.3:
                        tag = " ✗"
                row[st] = f"{full:+.2f}{tag}" if not np.isnan(full) else "–"
                if tag:
                    flags.append({"scenario": dim, "state": st, "strategy": strat, "verdict": "usable" if tag == " ✓" else "avoid",
                                  "sharpe": round(full, 2), "half1": round(h1, 2), "half2": round(h2, 2), "days": n})
            rows[strat] = row
        tables[dim] = pd.DataFrame(rows).T
    return tables, pd.DataFrame(flags)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="results/opening_reversal/STRATEGY_ATLAS.md")
    p.add_argument("--refresh", action="store_true")
    args = p.parse_args(argv)
    d = load_ohlc(args.refresh)
    S = build_strategies(d)
    sc = build_scenarios(d, load_cpi(), S.index)
    tables, flags = atlas(S, sc)

    def md(df, index=True):
        try:
            return df.to_markdown(index=index)
        except ImportError:
            return "```\n" + df.to_string(index=index) + "\n```"

    overall = pd.DataFrame({s: {"Sharpe all days": _sharpe(S[s]), "from": S[s].dropna().index[0].date()} for s in S}).T
    today = sc.iloc[-1:].T.rename(columns=lambda c: "today (" + str(c.date()) + ")")
    days = {dim: sc[dim].value_counts().to_dict() for dim in sc}
    lines = ["# Strategy x scenario atlas", "",
             "Sharpe of daily excess returns per scenario state (state known at the prior close). "
             "✓ = Sharpe >= 0.5 in both halves of the strategy's history; ✗ = <= -0.3 in both halves. "
             "Daily strategies start 2007-06 (later where the ETF is younger); intraday streams 2019+.", "",
             "## Today's scenario", "", md(today), "", "## Each strategy overall", "", md(overall), ""]
    if not flags.empty:
        for verdict in ("usable", "avoid"):
            f = flags[flags.verdict == verdict].sort_values(["scenario", "state", "sharpe"], ascending=[True, True, verdict == "avoid"])
            lines += [f"## Consistent '{verdict}' cells", "", md(f.drop(columns="verdict"), index=False), ""]
    for dim, t in tables.items():
        lines += [f"## {dim}", "", f"days per state: {days[dim]}", "", md(t), ""]
    Path(args.out).write_text("\n".join(lines))
    flags.to_csv(args.out.replace(".md", "_flags.csv"), index=False)
    S.to_csv(args.out.replace(".md", "_streams.csv"))
    print(f"{S.shape[1]} strategies x {sc.shape[1]} scenario dimensions; "
          f"{(flags.verdict == 'usable').sum() if not flags.empty else 0} usable / "
          f"{(flags.verdict == 'avoid').sum() if not flags.empty else 0} avoid cells -> {args.out}")


if __name__ == "__main__":
    main()
