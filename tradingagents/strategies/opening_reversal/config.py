from dataclasses import dataclass, field, replace
from datetime import time
from typing import Dict, Tuple


@dataclass(frozen=True)
class StrategyParams:
    """All tunable knobs of the opening reversal short. Percentages are fractions (0.001 = 0.1%)."""

    # --- which of the three entry conditions are enforced ---------------------------------
    require_gap_down: bool = True
    require_exhaustion: bool = True
    require_zone: bool = True
    # When require_gap_down is False, ``gap_filter`` can restrict to the *opposite* days
    # ("not_gap_down") to build a control group.
    gap_filter: str = "any"  # "any" | "not_gap_down"

    # --- condition 1: gap down ------------------------------------------------------------
    min_gap_pct: float = 0.0015          # open at least 0.15% below prior close
    max_gap_pct: float = 0.02            # skip crash opens (> 2% gap), behaviour differs

    # --- market regime (uses only closes up to the prior session) --------------------------
    # "any" | "below_sma20" | "above_sma20" | "below_sma50" | "above_sma50"
    regime: str = "any"

    # --- the rally that is being faded ----------------------------------------------------
    min_rally_pct: float = 0.0015        # rally off the session low must be >= 0.15%
    max_bars_since_high: int = 5         # trigger must come within N bars of the rally high
    # Reversal bar must close below the lowest low of the previous N bars (1 = prior bar only;
    # larger = wait for a break of short-term structure).
    break_lookback: int = 1

    # --- condition 2: volume exhaustion ---------------------------------------------------
    # Rally volume is divided by the median volume for that minute-of-day over the prior
    # ``volume_lookback_days`` sessions, so the natural post-open volume decay does not
    # count as "exhaustion".
    volume_lookback_days: int = 20
    exhaustion_window: int = 3           # bars compared at the start vs the end of the rally
    max_exhaustion_ratio: float = 0.8    # late-rally rel. volume <= 80% of early-rally rel. volume

    # --- condition 3: supply zones --------------------------------------------------------
    zone_sources: Tuple[str, ...] = (
        "prev_close", "prev_low", "prev_val", "prev_poc", "prev_vah", "prev_high", "premarket_high",
    )
    zone_half_width_pct: float = 0.0005  # zone = level +/- 0.05%
    profile_bin_pct: float = 0.0005      # volume-profile price bin = 0.05% of price
    value_area_share: float = 0.70

    # --- entry / exit ---------------------------------------------------------------------
    entry_start: time = time(9, 35)      # let the first 5 minutes print before acting
    entry_end: time = time(10, 30)       # "only the first hour"
    stop_buffer_pct: float = 0.0003      # stop = max(rally high, zone top) + 0.03%
    max_risk_pct: float = 0.006          # skip setups whose stop is > 0.6% away
    min_risk_pct: float = 0.0005         # and those whose stop is unrealistically tight
    # Scale-out plan: (R multiple, fraction of the original position)
    take_profits: Tuple[Tuple[float, float], ...] = ((1.0, 0.5), (2.0, 0.5))
    move_stop_to_breakeven: bool = True  # after the first target fills
    time_exit: time = time(12, 0)        # flatten whatever is left (0DTE theta)
    slippage_pct: float = 0.00002        # adverse slippage per fill on the underlying (~1c on SPY)


_BASE = StrategyParams()

VARIANTS: Dict[str, StrategyParams] = {
    # Each step adds one condition so its marginal value can be read off the results.
    "gap_only": replace(_BASE, require_exhaustion=False, require_zone=False),
    "gap+exhaustion": replace(_BASE, require_zone=False),
    "gap+zone": replace(_BASE, require_exhaustion=False),
    "full (gap+exhaustion+zone)": _BASE,
    # Control: same exhaustion+zone logic on days that did NOT gap down.
    "control: no gap-down": replace(_BASE, require_gap_down=False, gap_filter="not_gap_down"),
}
