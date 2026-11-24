import numpy as np
import pandas as pd

from tradingagents.strategies import bruni as br


def _frame(rows, day=None):
    idx = pd.date_range("2024-03-04 09:30", periods=len(rows), freq="15min", tz="America/New_York")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)
    df["volume"] = 1000.0
    df["day"] = day if day is not None else 0
    df["slot"] = np.arange(len(df))
    for k, v in {"vah": 100.0, "val": 95.0, "prev_close": 99.0, "sma20": 98.0, "sess_open": 101.0,
                 "atr": 1.0, "atr_pct": 0.6, "hot_run": 5, "relvol": 1.5}.items():
        df[k] = v
    return df


def _sig(df, long_at=(), short_at=()):
    s = pd.DataFrame(False, index=df.index, columns=["long", "short", "q_body", "q_vol", "q_noon"])
    for i in long_at:
        s.iloc[i, 0] = True
    for i in short_at:
        s.iloc[i, 1] = True
    return s


def test_stop_counts_first_when_a_bar_touches_both():
    df = _frame([(101, 101.5, 100.5, 101), (101, 102, 100, 101), (101, 101.2, 99.5, 101), (101, 104, 99.0, 103)])
    t = br.simulate(df, _sig(df, long_at=[2]), br.P(structure=False, slip=0.0), "X")
    # entry 101, stop 99.5 (risk 1.5), target 104; bar 3 touches both -> stop
    assert len(t) == 1 and t["why"][0] == "stop" and abs(t["R"][0] + 1.0) < 1e-9


def test_target_and_flat_at_close():
    df = _frame([(101, 101.5, 100.5, 101), (101, 102, 100, 101), (101, 101.2, 100.0, 101), (101, 103.1, 100.5, 102)])
    t = br.simulate(df, _sig(df, long_at=[2]), br.P(structure=False, slip=0.0), "X")
    assert t["why"][0] == "target" and abs(t["R"][0] - 2.0) < 1e-9
    df2 = _frame([(101, 101.5, 100.5, 101), (101, 102, 100, 101), (101, 101.2, 100.0, 101), (101, 102.0, 100.5, 101.5)])
    t2 = br.simulate(df2, _sig(df2, long_at=[2]), br.P(structure=False, slip=0.0), "X")
    assert t2["why"][0] == "close" and abs(t2["R"][0] - 0.5) < 1e-9


def test_skip_after_loss_then_resets():
    rows = [(101, 101.5, 100.5, 101), (101, 102, 100, 101), (101, 101.2, 100.0, 101), (100.5, 100.6, 99.0, 99.5),
            (100, 101.2, 100.0, 101), (101, 101.1, 99.0, 99.5), (100, 101.2, 100.0, 101), (101, 103.5, 100.5, 103)]
    df = _frame(rows)
    t = br.simulate(df, _sig(df, long_at=[2, 4, 6]), br.P(structure=False, slip=0.0), "X")
    assert list(t["skipped"]) == [False, True, False]
    assert t["R"].iloc[0] < 0 and t["R"].iloc[2] > 0


def test_structure_room_blocks_a_nearby_swing_high():
    # swing high 101.8 at bar 2 (confirmed at bar 4); signal at bar 5 enters 101 with stop 100.5 -> target 102
    rows = [(100, 100.5, 99.5, 100), (100, 101.0, 99.8, 100.5), (100.5, 101.8, 100.2, 101), (101, 101.2, 100.4, 100.8),
            (100.8, 101.0, 100.3, 100.6), (100.6, 101.1, 100.5, 101.0), (101, 101.5, 100.9, 101.2)]
    df = _frame(rows)
    blocked = br.simulate(df, _sig(df, long_at=[5]), br.P(structure=True, slip=0.0), "X")
    free = br.simulate(df, _sig(df, long_at=[5]), br.P(structure=False, slip=0.0), "X")
    assert len(blocked) == 0 and len(free) == 1


def test_swing_known_only_after_k_bars():
    df = _frame([(100, 100.5, 99.5, 100), (100, 101.0, 99.8, 100.5), (100.5, 101.8, 100.2, 101), (101, 101.2, 100.4, 100.8),
                 (100.8, 101.0, 100.3, 100.6)])
    sh, sl = br.swing_points(df, 2)
    assert sh[2] and not sh[1]
    h, l, d = df["high"].to_numpy(), df["low"].to_numpy(), df["day"].to_numpy()
    # at bar 3 the swing at bar 2 is not yet confirmed: no swing above, room is fine
    assert br.room_ok(3, 1, 101.0, 102.0, d, h, l, sh, sl, 2)
    assert not br.room_ok(4, 1, 101.0, 102.0, d, h, l, sh, sl, 2)


def test_engulfing_long_signal_conditions():
    rows = [(101.0, 101.5, 100.6, 101.2), (101.2, 101.4, 100.8, 101.1), (101.3, 101.5, 100.7, 100.9),
            (100.8, 102.2, 100.1, 102.0)]
    df = _frame(rows)
    s = br.candidates(df, br.P(fresh_max=30))
    assert bool(s["long"].iloc[3]) and not s["long"].iloc[2]
    df.loc[df.index[3], "relvol"] = 1.0
    assert not br.candidates(df, br.P())["long"].iloc[3]
