"""
News Filter — avoid trading on / around high-impact economic events.

For forex: NFP, FOMC, CPI, ECB, BOE, etc. cause abnormal spreads, slippage,
and unpredictable whipsaws. Win rate drops sharply on these days.
For crypto: exchange exploits, regulatory announcements, major liquidations
(> $500M in 24h).

The filter takes a timestamp and returns whether trading is allowed,
plus a confidence penalty applied during the event window.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd


# Built-in high-impact forex events (day-of-year pattern). In production this
# would be loaded from an economic calendar API (ForexFactory, Investing.com).
# Here we use a heuristic: flag Fridays (NFP), FOMC meeting days (every 6
# weeks on Wednesday), and the first Friday of each month (NFP).
def _is_high_impact_forex(ts: pd.Timestamp) -> Tuple[bool, str]:
    if not isinstance(ts, pd.Timestamp):
        ts = pd.Timestamp(ts)
    # First Friday of month -> NFP
    if ts.dayofweek == 4 and ts.day <= 7:
        return True, "NFP"
    # Wednesday 18:00-20:00 UTC approx FOMC (every ~6 weeks; flag all Wed PM)
    if ts.dayofweek == 2 and 17 <= ts.hour <= 20:
        return True, "FOMC_Window"
    # Month-end / quarter-end (last 2 days) -> rebalancing, whipsaw
    import calendar
    last_day = calendar.monthrange(ts.year, ts.month)[1]
    if ts.day >= last_day - 1:
        return True, "MonthEnd"
    return False, ""


def _is_high_impact_crypto(ts: pd.Timestamp,
                            large_liquidation_24h: Optional[float] = None) -> Tuple[bool, str]:
    """
    For crypto, high impact = large 24h liquidations (> $500M) or known
    scheduled events. The liquidation amount is passed in if available.
    """
    if large_liquidation_24h is not None and large_liquidation_24h > 500_000_000:
        return True, "LargeLiquidations"
    # Weekend low-liquidity (crypto 24/7 but volume drops, more whipsaw)
    if ts.dayofweek in (5, 6) and 2 <= ts.hour <= 8:
        return True, "WeekendLowLiq"
    return False, ""


class NewsFilter:
    """
    Trading permission filter based on news / event risk.
    Usage:
        nf = NewsFilter()
        allowed, reason, penalty = nf.check(ts, market="forex")
        if not allowed: skip trade
        score *= (1 - penalty)  # reduce confidence near events
    """
    def __init__(self, buffer_minutes_before: int = 60,
                 buffer_minutes_after: int = 120):
        self.buf_before = timedelta(minutes=buffer_minutes_before)
        self.buf_after = timedelta(minutes=buffer_minutes_after)

    def check(self, ts: pd.Timestamp, market: str = "forex",
              liquidation_24h: Optional[float] = None) -> Tuple[bool, str, float]:
        """
        Return (allowed, reason, confidence_penalty 0-0.5).
        During the event window, confidence is reduced (penalty).
        """
        if market == "forex":
            hit, reason = _is_high_impact_forex(ts)
        else:
            hit, reason = _is_high_impact_crypto(ts, liquidation_24h)
        if hit:
            return False, reason, 0.5
        # Soft penalty within buffer window
        # (we don't know exact event time here; the buffer applies to known
        # events when the caller provides them. Without an event list we
        # use the hit check as the gate.)
        return True, "", 0.0


# Schedule of KNOWN recurring high-impact events (for the buffer penalty).
# In production, fetch from ForexFactory / investing.com daily.
KNOWN_EVENTS: List[Dict] = [
    # NFP: first Friday of month 13:30 UTC
    {"name": "NFP", "monthday": (1, 7), "dow": 4, "hour": 13, "minute": 30,
     "importance": "HIGH"},
    # FOMC: roughly every 6 weeks on Wednesday 19:00 UTC
    # (a real calendar would list exact dates; we approximate)
    {"name": "FOMC", "dow": 2, "hour": 19, "minute": 0, "importance": "HIGH"},
    # ECB: roughly every 6 weeks Thursday 13:45 UTC
    {"name": "ECB", "dow": 3, "hour": 13, "minute": 45, "importance": "HIGH"},
    # CPI (US): around 13th of month 13:30 UTC
    {"name": "CPI", "monthday": (10, 14), "dow": 2, "hour": 13, "minute": 30,
     "importance": "HIGH"},
]


def is_near_known_event(ts: pd.Timestamp) -> Tuple[bool, str]:
    """Check if `ts` is within the buffer window of a known recurring event."""
    for ev in KNOWN_EVENTS:
        if "dow" in ev and ts.dayofweek != ev["dow"]:
            continue
        if "monthday" in ev:
            lo, hi = ev["monthday"]
            if not (lo <= ts.day <= hi):
                continue
        event_time = ts.replace(hour=ev["hour"], minute=ev["minute"],
                                second=0, microsecond=0)
        if abs((ts - event_time).total_seconds()) <= 7200:  # 2h window
            return True, ev["name"]
    return False, ""
