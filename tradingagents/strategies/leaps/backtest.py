"""Buy a one-year call on QQQ (or VGT) after a 2% down day: per-trade record and a small portfolio.

    python -m tradingagents.strategies.leaps.backtest

Written and committed before the first run. Every variant below is reported; none is picked.

Signal: the underlying closes 2% or more below the previous close. At most one new entry per 20
sessions per underlying (low frequency, and repeated signals in one selloff do not stack up).
Entry at that day's close. Variant: only while the underlying is above its 200-day average.
Option: expiry one year after entry; strike 100% of spot (at the money) or 80% (deep in the money,
delta about 0.85). Priced with Black-Scholes, implied vol from the model in leaps.pricing (VXN,
moneyness, time; fitted to 2024-26 QQQ quotes), T-bill rate, 0.6% dividend yield, every day of the
holding period, so exits use the vol of that day.
Exits:  E1 sell after 6 months
        E2 sell after 9 months (3 months before expiry)
        E3 sell at the first close 50% above cost, else after 9 months
        E4 sell at the first close 20% above cost, else after 9 months
Costs: 1% of the option price per side for QQQ; 4% for VGT, whose options trade thinly.
Controls, same exits: the same option bought on every session (the base rate the signal must beat);
QQQ shares bought on the same signal days and held as long; buy-and-hold.
Portfolio: each entry spends 5% of equity on premium, at most 6 positions open, the rest in T-bills.
Data: QQQ and VGT daily closes (Yahoo), VXN from 2001-01, 13-week T-bill yield.

Limits: modelled prices, not quotes, before 2024; the vol model was fitted in 2024-26 and is applied
back to VXN levels of up to 80 (2008); intraday paths and early assignment are ignored.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from . import pricing as pr

OUT = Path("results/opening_reversal/LEAPS.md")
START = "2001-02-01"
EXITS = {"E1 6 months": (126, None), "E2 9 months": (189, None), "E3 +50% or 9 months": (189, 0.50), "E4 +20% or 9 months": (189, 0.20)}
STRIKES = {"ATM": 1.00, "ITM 80%": 0.80}
COST = {"QQQ": 0.01, "VGT": 0.04}
COOLDOWN = 20
DROP = -0.02


@dataclass(frozen=True)
class Spec:
    under: str
    strike: float
    hold: int
    target: Optional[float]
    trend: bool = False


def load():
    m = pr.market()
    coef = json.loads((pr.CACHE / "iv_coef.json").read_text())
    return m, coef


def signal_days(px: pd.Series, trend: bool, cooldown: int = COOLDOWN) -> List[int]:
    r = px.pct_change()
    ok = (r <= DROP)
    if trend:
        ok &= px > px.rolling(200).mean()
    ok &= px.index >= START
    out, last = [], -10 ** 9
    for i in np.flatnonzero(ok.to_numpy()):
        if i - last >= cooldown:
            out.append(int(i)); last = int(i)
    return out


def trade(m: pd.DataFrame, coef, i: int, s: Spec) -> Optional[Dict[str, float]]:
    S = m[s.under].to_numpy(); vxn = m["VXN"].to_numpy(); r = m["r"].to_numpy()
    dates = m.index
    end = min(i + s.hold, len(m) - 1)
    if end <= i or np.isnan(S[i]):
        return None
    K = s.strike * S[i]
    exp_day = dates[i] + pd.Timedelta(days=365)
    path = np.arange(i, end + 1)
    T = (exp_day - dates[path]).days.to_numpy() / 365.0
    iv = pr.model_iv(vxn[path], S[path], K, T, coef)
    px = pr.bs_call(S[path], K, T, r[path], iv)
    c = COST[s.under]
    cost_in = px[0] * (1 + c)
    val = px * (1 - c) / cost_in - 1
    j = len(path) - 1
    if s.target is not None:
        hit = np.flatnonzero(val[1:] >= s.target)
        if len(hit):
            j = int(hit[0]) + 1
    shares = S[path[j]] / S[i] - 1
    return {"entry": dates[i], "exit": dates[path[j]], "days": int(j), "ret": float(val[j]), "under_ret": float(shares),
            "delta": float(pr.bs_delta(S[i], K, T[0], r[i], iv[0])), "iv": float(iv[0]), "premium_pct": float(px[0] / S[i] * 100),
            "complete": bool(i + s.hold < len(m) or j < len(path) - 1)}


def trades(m, coef, s: Spec, days: List[int]) -> pd.DataFrame:
    rows = [trade(m, coef, i, s) for i in days]
    return pd.DataFrame([x for x in rows if x is not None])


def stats(t: pd.DataFrame, col: str = "ret") -> Dict[str, float]:
    t = t[t["complete"]] if "complete" in t else t
    x = t[col]
    if not len(x):
        return {"trades": 0}
    return {"trades": len(x), "win %": float((x > 0).mean() * 100), "avg %": float(x.mean() * 100), "median %": float(x.median() * 100),
            "avg win %": float(x[x > 0].mean() * 100) if (x > 0).any() else np.nan,
            "avg loss %": float(x[x <= 0].mean() * 100) if (x <= 0).any() else np.nan,
            "worst %": float(x.min() * 100), "lost > 50% (share)": float((x < -0.5).mean() * 100), "avg days": float(t["days"].mean())}


def portfolio(m: pd.DataFrame, coef, s: Spec, days: List[int], frac: float = 0.05, max_open: int = 6) -> pd.Series:
    """Daily equity: 5% of equity in premium per entry, at most max_open, cash in T-bills."""
    S = m[s.under].to_numpy(); vxn = m["VXN"].to_numpy(); r = m["r"].to_numpy(); dates = m.index
    rf = (m["r"].shift(1).fillna(0.0) / 252.0).to_numpy()
    c = COST[s.under]
    i0 = int(np.searchsorted(dates, pd.Timestamp(START)))
    entries = set(days)
    cash, eq = 1.0, []
    opens: List[Dict[str, float]] = []
    for t in range(i0, len(m)):
        cash *= 1 + rf[t]
        val = 0.0
        for o in list(opens):
            T = max((o["exp"] - dates[t]).days / 365.0, 1e-6)
            p = float(pr.bs_call(S[t], o["K"], T, r[t], pr.model_iv(vxn[t], S[t], o["K"], T, coef)))
            age = t - o["i"]
            if age >= s.hold or (s.target is not None and p * (1 - c) / o["cost"] - 1 >= s.target):
                cash += o["n"] * p * (1 - c)
                opens.remove(o)
            else:
                val += o["n"] * p
        if t in entries and len(opens) < max_open:
            K = s.strike * S[t]
            T = 1.0
            p = float(pr.bs_call(S[t], K, T, r[t], pr.model_iv(vxn[t], S[t], K, T, coef)))
            spend = frac * (cash + val)
            n = spend / (p * (1 + c))
            cash -= spend
            opens.append({"i": t, "K": K, "exp": dates[t] + pd.Timedelta(days=365), "n": n, "cost": p * (1 + c)})
            val += n * p
        eq.append(cash + val)
    e = pd.Series(eq, index=dates[i0:])
    return e.pct_change().fillna(0.0) - m["r"].shift(1).fillna(0.0).reindex(e.index) / 252.0


def pstats(x: pd.Series) -> Dict[str, float]:
    eq = (1 + x).cumprod()
    return {"Sharpe": float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan,
            "ann % (excess)": float((eq.iloc[-1] ** (252 / len(x)) - 1) * 100), "vol %": float(x.std() * np.sqrt(252) * 100),
            "maxDD %": float((eq / eq.cummax() - 1).min() * 100)}


def main(argv=None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    m, coef = load()
    rows, base_rows, by_year = {}, {}, {}
    sig = {(u, tr): signal_days(m[u].dropna().reindex(m.index), tr) for u in ("QQQ", "VGT") for tr in (False, True)}
    every = {u: [i for i in range(len(m)) if m.index[i] >= pd.Timestamp(START) and not np.isnan(m[u].iloc[i])] for u in ("QQQ", "VGT")}
    for u in ("QQQ", "VGT"):
        for kname, k in STRIKES.items():
            for ename, (hold, tgt) in EXITS.items():
                for tr in (False, True):
                    s = Spec(u, k, hold, tgt, tr)
                    t = trades(m, coef, s, sig[(u, tr)])
                    label = f"{u} | {kname} | {ename}" + (" | above SMA200 only" if tr else "")
                    rows[label] = stats(t)
                    if u == "QQQ" and not tr:
                        base = trades(m, coef, s, every[u][::5])            # every 5th session: base rate, same exits
                        base_rows[f"{kname} | {ename}"] = {"signal: win %": rows[label]["win %"], "any day: win %": stats(base)["win %"],
                                                           "signal: avg %": rows[label]["avg %"], "any day: avg %": stats(base)["avg %"],
                                                           "signal: worst %": rows[label]["worst %"], "any day: worst %": stats(base)["worst %"]}
                        if kname == "ATM" and ename.startswith("E2"):
                            by_year["ATM, 9 months"] = t.groupby(t["entry"].dt.year)["ret"].agg(["size", lambda x: (x > 0).mean() * 100, "mean"])
                        if kname == "ITM 80%" and ename.startswith("E2"):
                            by_year["ITM 80%, 9 months"] = t.groupby(t["entry"].dt.year)["ret"].agg(["size", lambda x: (x > 0).mean() * 100, "mean"])
    # shares on the same signals
    shares = {}
    for hold, name in ((126, "6 months"), (189, "9 months")):
        t = trades(m, coef, Spec("QQQ", 1.0, hold, None), sig[("QQQ", False)])
        shares[f"QQQ shares, {name}, signal days"] = stats(t, "under_ret")
        tb = trades(m, coef, Spec("QQQ", 1.0, hold, None), every["QQQ"][::5])
        shares[f"QQQ shares, {name}, any day"] = stats(tb, "under_ret")
    # portfolios
    port = {}
    for kname, k in STRIKES.items():
        for ename in ("E2 9 months", "E4 +20% or 9 months"):
            hold, tgt = EXITS[ename]
            port[f"QQQ {kname}, {ename}, 5% premium per entry"] = pstats(portfolio(m, coef, Spec("QQQ", k, hold, tgt), sig[("QQQ", False)]))
    q = (m["QQQ"].pct_change() - m["r"].shift(1) / 252.0).loc[START:].fillna(0.0)
    port["QQQ buy and hold"] = pstats(q)
    yr = {k: v.set_axis(["trades", "win %", "avg"], axis=1).assign(avg=lambda d: d["avg"] * 100) for k, v in by_year.items()}
    n_sig = {f"{u}{' above SMA200' if tr else ''}": len(v) for (u, tr), v in sig.items()}
    lines = ["# One-year calls after a 2% down day", "", "```", __doc__.strip(), "```", "",
             f"IV model: {json.dumps({k: round(v, 4) for k, v in coef.items()})}. Signals (after the 20-session cooldown): {n_sig}.", "",
             "## Every variant, per trade (option return after costs)", "", pd.DataFrame(rows).T.round(1).to_markdown(), "",
             "## Does the 2% drop help? Same QQQ option bought on any day (every 5th session) vs on signal days", "",
             pd.DataFrame(base_rows).T.round(1).to_markdown(), "", "## QQQ shares on the same days", "", pd.DataFrame(shares).T.round(1).to_markdown(), "",
             "## By entry year, QQQ, 9-month hold", ""]
    for k, v in yr.items():
        lines += [f"{k}:", "", v.round(1).T.to_markdown(), ""]
    lines += ["## Portfolios 2001-2026 (excess over T-bills)", "", pd.DataFrame(port).T.round(2).to_markdown()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
