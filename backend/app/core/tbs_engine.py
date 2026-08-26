"""
Time-Based Session (TBS) Engine — session-aware trading filter.

Most institutional Smart Money setups (CRT, liquidity sweeps, BOS) occur
during specific session killzones:
  - London  killzone: 08:00 - 10:00 UTC
  - New York killzone: 13:00 - 15:00 UTC

Entering during these windows dramatically increases hit rate because:
  1. Liquidity providers are most active (stop hunts are common)
  2. The prior session's high/low is the obvious target
  3. Volatility expands, creating the impulse needed for our setups

The TBS engine is a TIME FILTER that boosts the score of trades taken during
killzones and downgrades trades taken in dead zones (between sessions).
"""
from typing import Tuple
import pandas as pd
from .crt_engine import in_killzone, SESSIONS


def session_multiplier(ts: pd.Timestamp) -> float:
    """
    Score multiplier based on session timing.
      1.0  = killzone (highest priority)
      0.6  = active session but not killzone
      0.3  = dead zone (between sessions, Asian)
    """
    in_kz, name = in_killzone(ts)
    if in_kz:
        return 1.0
    h = ts.hour
    # Active London or NY (outside killzone)
    if 8 <= h < 13 or 13 <= h < 20:
        return 0.6
    # Asian (00-08) and weekends -> dead zone
    return 0.3


def best_session_window(start_utc_hour: int, end_utc_hour: int) -> str:
    """Return the name of the best session for a given UTC hour range."""
    for s in SESSIONS:
        if s.start_utc_hour == start_utc_hour and s.end_utc_hour == end_utc_hour:
            return s.name
    return "CUSTOM"
