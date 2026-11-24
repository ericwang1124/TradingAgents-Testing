"""Gianluca Bruni's rules as posted (value-area pullback + engulfing candle, ATR-percentile filter),
on SPY / QQQ / IWM intraday bars, 2018-10 to 2026-10.

    python -m tradingagents.strategies.bruni

Pre-registered: the rules, parameters, samples and adoption test below were written and committed
before the first run on market data. Every variant is reported; none is picked after the fact.

The post (user's summary): 1 market filter: ATR percentile 51-75%, volatility regime no older than
30 bars; 2 direction from the value area, structure highs/lows as boundaries; 3 entry: pullback to
the value area, engulfing candle of sufficient size, volume requirement; 4 enter at the signal
bar's close, stop at that bar's low, fixed 1:2, flat at the structure high; 5 skip the signal after
a losing trade, five-question score -> Kelly size; 6 test on two samples, drop the rule if the
expectancy falls by more than half.

Our reading, one number per vague term, fixed in advance:
Bars       15-minute regular-session bars (main test); 5-minute bars reported as a second test.
ATR        14 bars; true range within the session (a day's first bar uses high - low).
Filter     ATR percentile among the previous 20 sessions of bars in [51%, 75%], and the run of
           consecutive bars with percentile above 50% is 30 bars or shorter (a fresh expansion).
Value area prior session's 70% volume profile (VAH / VAL) from 1-minute bars.
Direction  long when at least 2 of the 4 previous bars of the session closed above VAH;
           short when at least 2 of them closed below VAL.
Pullback   long: bar low at or below VAH + 0.25 ATR and close above VAH (short mirrored on VAL).
Engulfing  bullish bar after a bearish bar, its body covering the previous body, body >= 0.5 ATR.
Volume     bar volume >= 1.2x the median of the same time slot over the previous 20 sessions.
Structure  swing high = a bar's high above the 2 bars on each side, known 2 bars later. The nearest
           swing high above entry (this or the previous session) must be >= 2R away, or none
           exists (short mirrored with swing lows).
Trade      enter at the signal bar's close; stop at its low (long) / high (short); target 2R; a
           bar touching both counts as a stop; flat at the session's last bar. Signal bars from
           the second bar of the session to the bar ending 15:00. One position per symbol.
           Slippage 0.002% of price per fill (about 1 cent on SPY); stress test 0.01%.
Skip       after a losing trade in a symbol, that symbol's next signal is not taken.
Score      five yes/no questions: body >= 1 ATR; volume >= 2x; prior close on the trade side of its
           20-day average; the session opened outside value on the trade side; entry before 12:00.
Kelly      win rate and payoff by score bucket (0-2, 3, 4-5) measured in sample A; half Kelly,
           capped at 1% of equity at risk per trade, applied unchanged in sample B. Compared with a
           fixed 0.5% risk per trade.
Samples    A 2018-10..2022-09, B 2022-10..2026-10.
Adopt      only if the average R after costs is > 0 in both samples, B is at least half of A, the
           pooled t-stat is >= 2, and each sample has >= 30 trades; only then is it tested in the
           live book (core + add-on).
Controls   each ingredient removed one at a time; direction + pullback with no candle or volume
           condition; the same exits from every bar that has a direction (the base rate).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import date, time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

OUT = Path("results/opening_reversal/BRUNI.md")
SYMBOLS = ("SPY", "QQQ", "IWM")
DATA_START, DATA_END = date(2018, 9, 1), date(2026, 10, 31)
SAMPLES = {"A 2018-10..2022-09": ("2018-10-01", "2022-09-30"), "B 2022-10..2026-10": ("2022-10-01", "2026-10-31")}
SLIP, SLIP_STRESS = 0.00002, 0.0001
FIXED_RISK = 0.005
KELLY_CAP = 0.01


@dataclass(frozen=True)
class P:
    bar: int = 15
    atr_n: int = 14
    pct_sessions: int = 20
    band: tuple = (0.51, 0.75)
    fresh_max: Optional[int] = 30
    accept_look: int = 4
    accept_min: int = 2
    touch: float = 0.25
    candle: bool = True
    engulf_min: float = 0.5
    relvol_min: Optional[float] = 1.2
    structure: bool = True
    swing_k: int = 2
    target_r: float = 2.0
    skip_after_loss: bool = True
    pullback: bool = True
    use_band: bool = True
    slip: float = SLIP
    last_entry: time = time(15, 0)
    min_risk_atr: Optional[float] = None   # post-hoc diagnostics only: stop at least this many ATR away


# ------------------------------------------------------------------ data
def session_bars(symbol: str, bar: int) -> pd.DataFrame:
    """Continuous N-minute RTH bars with per-session value area and context columns."""
    from .opening_reversal.data import load_alpaca_minutes, resample_bars
    from .opening_reversal.levels import build_day_contexts

    m = load_alpaca_minutes(symbol, DATA_START, DATA_END, verbose=False)
    ctxs = build_day_contexts(m)
    frames = []
    for d, c in enumerate(ctxs):
        if "prev_vah" not in c.levels:
            continue
        b = resample_bars(c.rth[["open", "high", "low", "close", "volume"]], bar)
        b = b.assign(day=d, date=c.day, slot=np.arange(len(b)), vah=c.levels["prev_vah"], val=c.levels["prev_val"],
                     prev_close=c.prev_close, sma20=c.features.get("sma20", np.nan), sess_open=c.open)
        frames.append(b)
    return add_features(pd.concat(frames), bar)


def add_features(df: pd.DataFrame, bar: int, p: P = P()) -> pd.DataFrame:
    df = df.copy()
    same = df["day"].eq(df["day"].shift(1))
    pc = df["close"].shift(1)
    tr = np.where(same, np.maximum(df["high"], pc) - np.minimum(df["low"], pc), df["high"] - df["low"])
    df["atr"] = pd.Series(tr, index=df.index).rolling(p.atr_n, min_periods=p.atr_n).mean()
    per_session = int(round(390 / bar))
    w = p.pct_sessions * per_session
    df["atr_pct"] = df["atr"].rolling(w + 1, min_periods=w // 2).rank(pct=True)
    hot = (df["atr_pct"] > 0.50).astype(int)
    run = hot.groupby((hot == 0).cumsum()).cumsum()
    df["hot_run"] = run
    # volume relative to the same slot over the previous 20 sessions
    tab = df.pivot_table(index="day", columns="slot", values="volume")
    base = tab.rolling(p.pct_sessions, min_periods=p.pct_sessions // 2).median().shift(1)
    rel = (tab / base.replace(0, np.nan)).stack()
    df["relvol"] = rel.reindex(pd.MultiIndex.from_arrays([df["day"], df["slot"]])).to_numpy()
    return df


# ------------------------------------------------------------------ signals
def candidates(df: pd.DataFrame, p: P) -> pd.DataFrame:
    """Per-bar long / short signal flags (known at the bar's close) and the score items."""
    o, h, l, c, a = df["open"], df["high"], df["low"], df["close"], df["atr"]
    out = pd.DataFrame(index=df.index)
    above, below = (c > df["vah"]), (c < df["val"])
    n_above = sum((above.shift(k, fill_value=False) & df["day"].eq(df["day"].shift(k))).astype(int) for k in range(1, p.accept_look + 1))
    n_below = sum((below.shift(k, fill_value=False) & df["day"].eq(df["day"].shift(k))).astype(int) for k in range(1, p.accept_look + 1))
    dir_long, dir_short = n_above >= p.accept_min, n_below >= p.accept_min
    filt = pd.Series(True, index=df.index)
    if p.use_band:
        filt &= df["atr_pct"].between(*p.band)
    if p.fresh_max is not None:
        filt &= df["hot_run"].between(1, p.fresh_max)
    pb_long = (l <= df["vah"] + p.touch * a) & (c > df["vah"]) if p.pullback else pd.Series(True, index=df.index)
    pb_short = (h >= df["val"] - p.touch * a) & (c < df["val"]) if p.pullback else pd.Series(True, index=df.index)
    same_prev = df["day"].eq(df["day"].shift(1))
    po, pc = o.shift(1), c.shift(1)
    body = (c - o).abs()
    if p.candle:
        eng_long = same_prev & (c > o) & (pc < po) & (c >= po) & (o <= pc) & (body >= p.engulf_min * a)
        eng_short = same_prev & (c < o) & (pc > po) & (c <= po) & (o >= pc) & (body >= p.engulf_min * a)
    else:
        eng_long = eng_short = pd.Series(True, index=df.index)
    vol = df["relvol"] >= p.relvol_min if p.relvol_min is not None else pd.Series(True, index=df.index)
    t = df.index.time
    end_ok = pd.Series([(pd.Timestamp.combine(date(2000, 1, 1), x) + pd.Timedelta(minutes=p.bar)).time() <= p.last_entry for x in t], index=df.index)
    when = (df["slot"] >= 1) & end_ok & a.notna()
    out["long"] = when & filt & dir_long & pb_long & eng_long & vol
    out["short"] = when & filt & dir_short & pb_short & eng_short & vol & ~out["long"]
    # score items (direction-specific ones are resolved at trade time)
    out["q_body"] = body >= 1.0 * a
    out["q_vol"] = df["relvol"] >= 2.0
    out["q_noon"] = pd.Series([x < time(12, 0) for x in t], index=df.index)
    return out


def swing_points(df: pd.DataFrame, k: int) -> tuple:
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    n = len(h)
    sh = np.zeros(n, bool); sl = np.zeros(n, bool)
    for j in range(k, n - k):
        nb = np.r_[h[j - k:j], h[j + 1:j + k + 1]]
        sh[j] = h[j] > nb.max()
        nb = np.r_[l[j - k:j], l[j + 1:j + k + 1]]
        sl[j] = l[j] < nb.min()
    return sh, sl


def room_ok(i: int, side: int, entry: float, target: float, df_day: np.ndarray, h: np.ndarray, l: np.ndarray,
            sh: np.ndarray, sl: np.ndarray, k: int) -> bool:
    """Nearest confirmed swing beyond entry (this or the previous session) must be at or past target."""
    d = df_day[i]
    j = i - k                         # swing at j is confirmed once bar j+k has closed
    nearest = None
    while j >= 0 and df_day[j] >= d - 1:
        if side > 0 and sh[j] and h[j] > entry:
            nearest = h[j] if nearest is None else min(nearest, h[j])
        if side < 0 and sl[j] and l[j] < entry:
            nearest = l[j] if nearest is None else max(nearest, l[j])
        j -= 1
    if nearest is None:
        return True
    return nearest >= target if side > 0 else nearest <= target


def simulate(df: pd.DataFrame, sig: pd.DataFrame, p: P, symbol: str) -> pd.DataFrame:
    o, h, l, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    day = df["day"].to_numpy()
    atr = df["atr"].to_numpy()
    sh, sl = swing_points(df, p.swing_k)
    L, S = sig["long"].to_numpy(), sig["short"].to_numpy()
    idx = df.index
    trades: List[Dict] = []
    i, n, last_loss = 0, len(df), False
    while i < n:
        side = 1 if L[i] else (-1 if S[i] else 0)
        if side == 0:
            i += 1
            continue
        entry_raw = c[i]
        stop = l[i] if side > 0 else h[i]
        if p.min_risk_atr is not None:
            gap = p.min_risk_atr * atr[i]
            stop = min(stop, entry_raw - gap) if side > 0 else max(stop, entry_raw + gap)
        risk = (entry_raw - stop) * side
        if not risk > 0:
            i += 1
            continue
        target = entry_raw + side * p.target_r * risk
        if p.structure and not room_ok(i, side, entry_raw, target, day, h, l, sh, sl, p.swing_k):
            i += 1
            continue
        skipped = p.skip_after_loss and last_loss
        j, exit_px, why = i + 1, None, None
        while j < n and day[j] == day[i]:
            if side > 0:
                if o[j] <= stop: exit_px, why = o[j], "stop"
                elif l[j] <= stop: exit_px, why = stop, "stop"
                elif o[j] >= target: exit_px, why = o[j], "target"
                elif h[j] >= target: exit_px, why = target, "target"
            else:
                if o[j] >= stop: exit_px, why = o[j], "stop"
                elif h[j] >= stop: exit_px, why = stop, "stop"
                elif o[j] <= target: exit_px, why = o[j], "target"
                elif l[j] <= target: exit_px, why = target, "target"
            if why:
                break
            j += 1
        if why is None:                                   # flat at the session's last bar
            j = j - 1
            exit_px, why = c[j], "close"
        if j <= i:                                         # signal on the session's last bar: no trade
            i += 1
            continue
        ent = entry_raw * (1 + side * p.slip)
        ext = exit_px * (1 - side * p.slip)
        r = (ext - ent) * side / risk
        trades.append({"symbol": symbol, "entry_time": idx[i], "exit_time": idx[j], "side": side, "R": r, "why": why,
                       "skipped": skipped, "risk_pct": risk / entry_raw * 100,
                       "q_body": bool(sig["q_body"].iloc[i]), "q_vol": bool(sig["q_vol"].iloc[i]), "q_noon": bool(sig["q_noon"].iloc[i]),
                       "q_trend": bool((df["prev_close"].iloc[i] - df["sma20"].iloc[i]) * side > 0),
                       "q_open": bool((df["sess_open"].iloc[i] > df["vah"].iloc[i]) if side > 0 else (df["sess_open"].iloc[i] < df["val"].iloc[i]))})
        if not skipped:
            last_loss = r < 0
        else:
            last_loss = False                              # the skip is used up
        i = i + 1 if skipped else j + 1                    # a skipped signal does not occupy the symbol
    t = pd.DataFrame(trades)
    if len(t):
        t["score"] = t[["q_body", "q_vol", "q_noon", "q_trend", "q_open"]].sum(axis=1)
    return t


# ------------------------------------------------------------------ evaluation
def stats(r: pd.Series, years: float) -> Dict[str, float]:
    if len(r) == 0:
        return {"trades": 0}
    sd = r.std(ddof=1) if len(r) > 1 else np.nan
    return {"trades": len(r), "per year": len(r) / years, "win %": (r > 0).mean() * 100, "avg R": r.mean(),
            "t": r.mean() / sd * np.sqrt(len(r)) if sd and sd > 0 else np.nan, "total R": r.sum()}


def split(t: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    out = {}
    for name, (a, b) in SAMPLES.items():
        et = t["entry_time"].dt.tz_localize(None) if t["entry_time"].dt.tz is not None else t["entry_time"]
        out[name] = t[(et >= pd.Timestamp(a)) & (et < pd.Timestamp(b) + pd.Timedelta(days=1))]
    return out


def years_of(name: str) -> float:
    a, b = SAMPLES[name]
    return (pd.Timestamp(b) - pd.Timestamp(a)).days / 365.25


def taken(t: pd.DataFrame) -> pd.DataFrame:
    return t[~t["skipped"]] if len(t) else t


def run_variant(data: Dict[str, pd.DataFrame], p: P) -> pd.DataFrame:
    ts = [simulate(df, candidates(df, p), p, s) for s, df in data.items()]
    ts = [t for t in ts if len(t)]
    return pd.concat(ts, ignore_index=True) if ts else pd.DataFrame(columns=["entry_time", "R", "skipped"])


def verdict(t: pd.DataFrame) -> Dict[str, object]:
    sp = split(taken(t))
    a, b = (sp[k]["R"] for k in SAMPLES)
    pooled = stats(pd.concat([a, b]), 8.0)
    ok = (len(a) >= 30 and len(b) >= 30 and a.mean() > 0 and b.mean() > 0 and b.mean() >= 0.5 * a.mean()
          and pooled.get("t", 0) >= 2)
    return {"A avg R": a.mean() if len(a) else np.nan, "B avg R": b.mean() if len(b) else np.nan,
            "B / A": b.mean() / a.mean() if len(a) and a.mean() > 0 else np.nan, "pooled t": pooled.get("t", np.nan), "passes": ok}


def bucket(s: int) -> str:
    return "0-2" if s <= 2 else ("3" if s == 3 else "4-5")


def kelly_table(tA: pd.DataFrame) -> Dict[str, float]:
    out = {}
    for b, g in tA.groupby(tA["score"].map(bucket)):
        w, lo = g["R"][g["R"] > 0], g["R"][g["R"] <= 0]
        if len(g) < 10 or not len(w) or not len(lo):
            out[b] = 0.0
            continue
        pwin, payoff = len(w) / len(g), w.mean() / -lo.mean()
        out[b] = float(np.clip(0.5 * (pwin - (1 - pwin) / payoff), 0.0, KELLY_CAP))
    return out


def daily_returns(t: pd.DataFrame, risk: pd.Series, start: str, end: str) -> pd.Series:
    days = pd.bdate_range(start, end)
    d = t["exit_time"].dt.tz_localize(None).dt.normalize() if t["exit_time"].dt.tz is not None else t["exit_time"].dt.normalize()
    pnl = (t["R"] * risk).groupby(d).sum()
    return pnl.reindex(days, fill_value=0.0)


def sharpe(x: pd.Series) -> float:
    return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan


def report(results: Dict[str, Dict[str, pd.DataFrame]], kelly: Dict[str, object]) -> str:
    lines = ["# Gianluca Bruni's rules, as posted: SPY / QQQ / IWM intraday", "", "```", __doc__.strip(), "```", ""]
    for bar, res in results.items():
        lines += [f"## {bar}-minute bars", "", "### Every variant: taken trades, R after costs, by sample", ""]
        rows = {}
        for name, t in res.items():
            sp = split(taken(t))
            for s, g in sp.items():
                rows[(name, s)] = stats(g["R"], years_of(s))
            rows[(name, "verdict")] = verdict(t)
        tab = pd.DataFrame({k: v for k, v in rows.items() if k[1] != "verdict"}).T
        lines += [tab.round(3).to_markdown(), "", "### Adoption test per variant", "",
                  pd.DataFrame({k[0]: v for k, v in rows.items() if k[1] == "verdict"}).T.round(3).to_markdown(), ""]
        main = res["rules as posted"]
        if len(main):
            sk = main[main["skipped"]]
            lines += ["### Skip-after-loss: the skipped signals", "",
                      pd.DataFrame({s: stats(g["R"], years_of(s)) for s, g in split(sk).items()}).T.round(3).to_markdown(), ""]
            tk = taken(main)
            lines += ["### By symbol and side (taken, both samples)", "",
                      pd.DataFrame({f"{s} {'long' if d > 0 else 'short'}": stats(g["R"], 8.0) for (s, d), g in tk.groupby(["symbol", "side"])}).T.round(3).to_markdown(), "",
                      "### By score bucket (taken)", ""]
            sp = split(tk)
            lines += [pd.DataFrame({(b, s): stats(g[g["score"].map(bucket) == b]["R"], years_of(s)) for s, g in sp.items() for b in ("0-2", "3", "4-5")}).T.round(3).to_markdown(), ""]
            lines += ["### Exit reasons (taken)", "", tk["why"].value_counts().to_frame().to_markdown(), ""]
        if bar in kelly:
            lines += ["### Sizing in sample B: fixed 0.5% risk vs five-question half Kelly (fitted on A)", "",
                      f"Kelly risk per bucket from A: {kelly[bar]['table']}", "", pd.DataFrame(kelly[bar]["rows"]).T.round(3).to_markdown(), ""]
    return "\n".join(lines) + "\n"


VARIANTS = {
    "rules as posted": {},
    "no ATR band": {"use_band": False},
    "no freshness (30 bars)": {"fresh_max": None},
    "no ATR filter at all": {"use_band": False, "fresh_max": None},
    "any engulfing size": {"engulf_min": 0.0},
    "no volume rule": {"relvol_min": None},
    "no structure room": {"structure": False},
    "no skip after loss": {"skip_after_loss": False},
    "slippage 0.01% per fill": {"slip": SLIP_STRESS},
    "direction + pullback, no candle / volume": {"candle": False, "relvol_min": None},
    "base rate: every bar with a direction": {"candle": False, "relvol_min": None, "pullback": False, "use_band": False,
                                              "fresh_max": None, "structure": False, "skip_after_loss": False},
}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bars", default="15,5")
    args = ap.parse_args(argv)
    results, kelly = {}, {}
    for bar in (int(x) for x in args.bars.split(",")):
        data = {s: session_bars(s, bar) for s in SYMBOLS}
        res = {}
        for name, kw in VARIANTS.items():
            res[name] = run_variant(data, replace(P(bar=bar), **kw))
            v = verdict(res[name])
            print(f"{bar}m | {name}: {len(taken(res[name]))} trades | A {v['A avg R']:.3f} B {v['B avg R']:.3f} t {v['pooled t']:.2f} pass {v['passes']}", flush=True)
        results[bar] = res
        main_t = taken(res["rules as posted"])
        if len(main_t):
            sp = split(main_t)
            ka, kb = sp[list(SAMPLES)[0]], sp[list(SAMPLES)[1]]
            table = kelly_table(ka)
            b0, b1 = SAMPLES[list(SAMPLES)[1]]
            fixed = daily_returns(kb, pd.Series(FIXED_RISK, index=kb.index), b0, b1)
            kel = daily_returns(kb, kb["score"].map(bucket).map(table).fillna(0.0), b0, b1)
            kelly[bar] = {"table": table, "rows": {
                "fixed 0.5% risk": {"Sharpe": sharpe(fixed), "ann %": fixed.mean() * 252 * 100, "trades": len(kb)},
                "half Kelly by score": {"Sharpe": sharpe(kel), "ann %": kel.mean() * 252 * 100,
                                        "trades sized > 0": int((kb["score"].map(bucket).map(table).fillna(0) > 0).sum())}}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report(results, kelly))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
