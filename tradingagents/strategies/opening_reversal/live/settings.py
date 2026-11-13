"""Fixed settings for paper trading. Changing these changes what the forward test measures."""

from dataclasses import replace
from datetime import time
from pathlib import Path

from ..config import VARIANTS

# Signal traded on GO days: gap-down reversal (gap >= 0.15%, rally >= 0.15%, bearish bar breaking the
# prior bar's low, 09:35-10:30), single target at 1R, flat by 10:45. Historically (2019-2026, major
# event days skipped) this is ~0R per trade: the daily decision has to add the edge.
LIVE_PARAMS = replace(VARIANTS["gap_only"], take_profits=((1.0, 1.0),), time_exit=time(10, 45))
# Also evaluated in shadow every day for comparison.
SHADOW_PARAMS = {"original_rules": VARIANTS["full (gap+exhaustion+zone)"]}

SYMBOL = "SPY"
HISTORY_DAYS = 160                 # calendar days of 1-minute history for levels / averages / volume
RISK_PER_TRADE = 0.005             # of account equity, sized on the underlying stop distance
EST_PUT_DELTA = 0.45               # used only for sizing: option loss ~ delta * stop distance
MAX_PREMIUM_FRACTION = 0.02        # never spend more than 2% of equity on premium
MAX_CONTRACTS = 20
ENTRY_LIMIT_SLIPPAGE = 0.05        # buy limit = ask + this; unfilled after 30s -> cancelled
POLL_SECONDS = 5                   # exit monitoring cadence on the underlying's last trade

# Days the strategy never trades, whatever the decision says (event study, both periods worse).
HARD_RULES = ("fomc_day", "fomc_next_day", "cpi_day", "jobs_day", "half_day", "market_closed")

REPO_ROOT = Path(__file__).resolve().parents[4]
JOURNAL_DIR = REPO_ROOT / "journal" / "opening_reversal"
STATS_PATH = Path(__file__).with_name("historical_stats.json")
