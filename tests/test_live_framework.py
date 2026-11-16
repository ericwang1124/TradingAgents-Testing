"""Checks for the live core portfolio and intraday add-on helpers (no network)."""

import numpy as np
import pandas as pd
import pytest

from tradingagents.strategies import core_portfolio as cp
from tradingagents.strategies.opening_reversal.live import addon
from tradingagents.strategies.opening_reversal.live.core_rebalance import plan_orders

NY = "America/New_York"


def _first30(path):
    idx = pd.date_range("2026-01-05 09:30", periods=30, freq="1min", tz=NY)
    c = np.asarray(path, float)
    return pd.DataFrame({"open": np.r_[c[0], c[:-1]], "close": c}, index=idx)


def test_efficiency_matches_day_type_definition():
    up = _first30(np.linspace(100, 101, 30))
    e = addon.efficiency(up)
    assert e["direction"] == 1 and e["efficiency"] == pytest.approx(1.0)
    zig = _first30(100 + 0.2 * np.sin(np.arange(30)))
    assert addon.efficiency(zig)["efficiency"] < 0.2


def test_plan_orders_long_only_whole_shares_sells_first():
    orders = plan_orders({"SPY": 10_000, "TLT": 0.0, "GLD": 100.0}, {"TLT": 50.0, "GLD": 1.0, "QQQ": 3.0},
                         {"SPY": 500.0, "TLT": 90.0, "GLD": 300.0, "QQQ": 600.0})
    by = {o["symbol"]: o for o in orders}
    assert by["SPY"] == {"symbol": "SPY", "side": "buy", "qty": 20, "est_usd": 10_000.0}
    assert by["TLT"]["side"] == "sell" and by["TLT"]["qty"] == 50          # target 0 -> close out
    assert by["QQQ"]["side"] == "sell" and by["QQQ"]["qty"] == 3           # not in targets -> close out
    assert "GLD" not in by                                                  # change below $250
    assert [o["side"] for o in orders] == ["sell", "sell", "buy"]


def test_turn_of_month_unknown_next_session_is_not_month_end():
    sessions = pd.bdate_range("2026-03-20", "2026-04-08")
    C = pd.DataFrame({t: 100.0 for t in cp.UNIVERSE}, index=sessions[sessions <= "2026-03-27"])
    C = C.mul(np.linspace(1, 1.01, len(C)), axis=0)
    P_short = cp.strategy_positions(C, C["SPY"], C["SPY"], C.index)          # data ends 03-27, next day unknown
    P_full = cp.strategy_positions(C, C["SPY"], C["SPY"], sessions)          # real calendar known
    tom = "turn of month (last day + first 3)"
    assert P_short[tom]["SPY"].iloc[-1] == 0.0
    assert P_full[tom]["SPY"].iloc[-1] == 0.0       # 03-30 is not the last session of March either
    end = pd.Timestamp("2026-03-30")                # Monday 03-30: next session 03-31 is March's last day
    C2 = pd.DataFrame({t: 100.0 for t in cp.UNIVERSE}, index=sessions[sessions <= end])
    assert cp.strategy_positions(C2, C2["SPY"], C2["SPY"], sessions)[tom]["SPY"].iloc[-1] == 1.0


def test_addon_shadow_uses_threshold_and_long_side(monkeypatch):
    monkeypatch.setattr(addon, "load_threshold", lambda: 0.3)
    idx = pd.date_range("2026-01-05 09:30", periods=150, freq="1min", tz=NY)
    up = pd.DataFrame({"open": np.linspace(100, 102, 150), "close": np.linspace(100.01, 102.01, 150)}, index=idx)
    s = addon.shadow(idx[0].date(), up)
    assert s["take"] and s["return_pct"] > 0
    down = up.iloc[::-1].copy()
    down.index = idx
    assert not addon.shadow(idx[0].date(), down)["take"]                  # long side only


class _FakeClient:
    """Fills each first attempt only partly (half, rounded down); later attempts fill completely."""

    def __init__(self):
        self.sent, self.cancelled, self._orders = [], [], {}

    def submit_order(self, symbol, qty, side, time_in_force="day", client_order_id=None, **_):
        oid = f"o{len(self.sent)}"
        first = not any(s[0] == symbol for s in self.sent)
        filled = qty // 2 if first else qty
        self.sent.append((symbol, qty, side, time_in_force))
        self._orders[oid] = {"id": oid, "status": "partially_filled" if filled < qty else "filled",
                             "filled_qty": str(filled), "filled_avg_price": "100"}
        return {"id": oid, "status": "accepted"}

    def wait_filled(self, oid, timeout_s=60.0):
        return self._orders[oid]

    def get_order(self, oid):
        return self._orders[oid]

    def cancel_order(self, oid):
        self.cancelled.append(oid)


def test_core_execute_resends_unfilled_part_once():
    from tradingagents.strategies.opening_reversal.live.core_rebalance import execute

    c = _FakeClient()
    out = execute(c, [{"symbol": "TLT", "side": "buy", "qty": 81}], pd.Timestamp("2026-11-16").date())
    assert [s[1] for s in c.sent] == [81, 41] and all(s[3] == "day" for s in c.sent)
    assert c.cancelled == ["o0"] and out[0]["filled_qty"] == 81


def test_addon_qty_caps_by_buying_power():
    assert addon.addon_qty(100_000, {"daytrading_buying_power": "400000"}, 500.0) == int(addon.ADDON_NOTIONAL * 100_000 // 500)
    assert addon.addon_qty(100_000, {"daytrading_buying_power": "100000"}, 500.0) == int(addon.BP_USE * 100_000 // 500)
    assert addon.addon_qty(100_000, {"daytrading_buying_power": "0", "buying_power": "50000"}, 500.0) == 90
    assert addon.addon_qty(100_000, {}, 500.0, size=0.0) == 0


def test_core_has_rsi30_dip_buying_on_spy_qqq_iwm():
    idx = pd.bdate_range("2020-01-01", periods=400)
    path = np.r_[np.linspace(100, 70, 150), np.linspace(70, 130, 250)]     # long slide, then recovery
    C = pd.DataFrame({t: path for t in cp.UNIVERSE}, index=idx)
    P = cp.strategy_positions(C, C["SPY"], C["SPY"], idx)
    for t in ("SPY", "QQQ", "IWM"):
        pos = P[f"RSI(30)<35 buy, >65 sell: {t}"][t]
        assert pos.iloc[:90].sum() == 0                     # warm-up
        assert pos.max() == 1.0 and pos.iloc[-1] == 0.0     # bought in the slide, sold in the recovery


# ------------------------------------------------------------------ LEAP sleeve
from datetime import date

from tradingagents.strategies.opening_reversal.live import leaps_sleeve as ls


def test_leaps_entry_signal_needs_drop_and_uptrend():
    up = pd.Series(np.linspace(400, 600, 300), index=pd.bdate_range("2025-01-01", periods=300))
    assert ls.entry_signal(up, 600 * 0.979)["signal"]                        # -2.1% in an uptrend
    assert not ls.entry_signal(up, 600 * 0.985)["signal"]                    # only -1.5%
    down = pd.Series(np.linspace(600, 400, 300), index=up.index)
    s = ls.entry_signal(down, 400 * 0.97)
    assert s["drop"] and not s["uptrend"] and not s["signal"]


def test_leaps_contract_choice_exit_rules_and_size():
    today = date(2026, 11, 16)
    cons = [{"symbol": "A", "expiration_date": "2027-09-17", "strike_price": "600", "tradable": True},
            {"symbol": "B", "expiration_date": "2027-12-17", "strike_price": "650", "tradable": True},
            {"symbol": "C", "expiration_date": "2027-12-17", "strike_price": "680", "tradable": True},
            {"symbol": "D", "expiration_date": "2028-06-16", "strike_price": "680", "tradable": True}]
    assert ls.pick_contract(cons, 676.0, today)["symbol"] == "C"             # 396 days (closest to 365), strike closest to spot
    assert ls.pick_contract(cons[:1], 676.0, today)["symbol"] == "A"         # 305 days: still inside 300-450
    assert ls.pick_contract([dict(cons[0], expiration_date="2027-08-20")], 676.0, today) is None   # 277 days: too short
    pos = {"cost": 50.0, "expiry": "2027-12-17", "entry_date": "2026-11-16"}
    assert ls.exit_reason(pos, 60.0, today, 10) == "take profit"
    assert ls.exit_reason(pos, 55.0, today, 10) is None
    assert ls.exit_reason(pos, 55.0, today, 189) == "held 9 months"
    assert ls.exit_reason(pos, 55.0, date(2027, 9, 20), 100) == "90 days to expiry"
    assert ls.contracts_to_buy(100_000, 87.0) == 1                          # 6.5% buys none, one costs 8.7% <= 10%
    assert ls.contracts_to_buy(100_000, 105.0) == 0                         # one would cost 10.5% of equity
    assert ls.contracts_to_buy(300_000, 65.0) == 3


class _OptClient:
    """Fake broker: QQQ at `price`, one listed LEAP, fills every limit order at its limit."""

    def __init__(self, price, bid=60.0, ask=61.0, held=None):
        self.price, self.bid, self.ask, self.held, self.orders = price, bid, ask, held or [], []

    def calendar(self, a, b):
        return [{"date": a.isoformat(), "close": "16:00"}]

    def positions(self):
        return self.held

    def option_quote(self, symbol):
        return {"bid": self.bid, "ask": self.ask}

    def latest_trade_price(self, symbol):
        return self.price

    def call_contracts(self, *a):
        return [{"symbol": "QQQ271217C00590000", "expiration_date": "2027-12-17", "strike_price": "590", "tradable": True}]

    def account(self):
        return {"equity": "100000"}

    def submit_order(self, symbol, qty, side, order_type="market", limit_price=None, client_order_id=None, time_in_force="day"):
        self.orders.append((symbol, qty, side, limit_price))
        return {"id": str(len(self.orders))}

    def wait_filled(self, oid, timeout_s=60.0):
        sym, qty, side, px = self.orders[int(oid) - 1]
        return {"status": "filled", "filled_qty": str(qty), "filled_avg_price": str(px)}

    def get_order(self, oid):
        return self.wait_filled(oid)

    def cancel_order(self, oid):
        pass


def test_leaps_run_buys_on_signal_then_takes_profit(tmp_path, monkeypatch):
    monkeypatch.setattr(ls, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(ls.journal, "write", lambda *a, **k: None)
    hist = pd.Series(np.linspace(450, 600, 300), index=pd.bdate_range(end="2026-11-13", periods=300))
    c = _OptClient(price=600 * 0.975)
    rec = ls.run(date(2026, 11, 16), client=c, history=hist)
    assert rec["signal"]["signal"] and c.orders == [("QQQ271217C00590000", 1, "buy", 60.5)]     # one contract at the mid
    st = ls.load_state()
    assert st["last_entry"] == "2026-11-16" and st["positions"]["QQQ271217C00590000"]["cost"] == 60.5
    # next day: no new entry inside the cooldown, and a bid 25% above cost sells
    held = [{"symbol": "QQQ271217C00590000", "asset_class": "us_option", "qty": "1", "avg_entry_price": "60.5"}]
    c2 = _OptClient(price=600 * 0.975, bid=75.6, ask=76.4, held=held)
    hist2 = pd.concat([hist, pd.Series([585.0], index=[pd.Timestamp("2026-11-16")])])
    rec2 = ls.run(date(2026, 11, 17), client=c2, history=hist2)
    assert rec2["exits"][0]["reason"] == "take profit" and c2.orders[0][2] == "sell"
    assert all(o[2] != "buy" for o in c2.orders) and ls.load_state()["positions"] == {}
