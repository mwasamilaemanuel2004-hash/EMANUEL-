"""
CRT Engine (Change of Responsibility Transfer) + TBS Engine (Time-Based Session).

CRT concept:
  A higher-timeframe (HTF) candle creates a wick that sweeps liquidity beyond
  the prior HTF high/low. The body of that HTF candle "transfers responsibility"
  to the opposite side. On the LTF, we look for a CHoCH (Change of Character)
  inside the HTF candle, then enter on the pullback to the HTF candle's 50%
  level (the Order Block / FVG in between).

TBS concept:
  - Asian session  (00:00 - 08:00 UTC): accumulation, defines the range
  - London session (08:00 - 13:00 UTC): first expansion of the day
  - New York      (13:00 - 20:00 UTC): second expansion, often reverses London
  Killzones are the first 2 hours of London and New York — highest probability
  for liquidity sweeps and CRT setups.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class CRTSetup:
    """A Change of Responsibility Transfer setup on the HTF."""
    direction: str           # 'BUY' or 'SELL'
    htf_index: int           # index of the HTF candle that transferred responsibility
    sweep_level: float       # the liquidity level that was swept
    midpoint: float          # 50% of the HTF candle (the Order Block)
    choch_index: int         # LTF index where CHoCH happened
    ltf_entry: float         # suggested LTF entry
    invalidation: float      # structural invalidation (the HTF extreme)
    rr: float                # estimated R:R
    confidence: float        # 0-1


@dataclass
class SessionWindow:
    name: str
    start_utc_hour: int
    end_utc_hour: int
    killzone_start: int
    killzone_end: int


SESSIONS = [
    SessionWindow("ASIAN",  0,  8,  0,  4),
    SessionWindow("LONDON", 8, 13,  8, 10),
    SessionWindow("NEW_YORK", 13, 20, 13, 15),
]


def in_killzone(ts: pd.Timestamp) -> Tuple[bool, str]:
    """Return (is_killzone, session_name) for a given timestamp."""
    h = ts.hour
    for s in SESSIONS:
        if s.killzone_start <= h < s.killzone_end:
            return True, s.name
    return False, ""


def detect_crt(df_ltf: pd.DataFrame, df_htf: pd.DataFrame,
               lookback_htf: int = 3) -> List[CRTSetup]:
    """
    Detect CRT setups:
      1. Find an HTF candle whose wick swept the prior HTF high (bearish CRT)
         or low (bullish CRT) and whose body is in the opposite direction.
      2. On the LTF, find a CHoCH confirming the reversal inside that HTF candle.
      3. The 50% level of the HTF candle is the POI (Point of Interest).
    """
    setups: List[CRTSetup] = []
    if len(df_htf) < 3 or len(df_ltf) < 20:
        return setups

    # Iterate over recent HTF candles
    for i in range(1, min(lookback_htf, len(df_htf))):
        cur = df_htf.iloc[-i]
        prev = df_htf.iloc[-i-1]
        cur_high = float(cur['high']); cur_low = float(cur['low'])
        cur_open = float(cur['open']); cur_close = float(cur['close'])
        prev_high = float(prev['high']); prev_low = float(prev['low'])

        midpoint = (cur_high + cur_low) / 2.0
        body = cur_close - cur_open

        # BEARISH CRT: HTF candle wicks ABOVE prior HTF high and closes back inside
        if cur_high > prev_high and body < 0 and cur_close < midpoint:
            # Sweep level is the prior HTF high
            sweep = prev_high
            # LTF CHoCH: look for a swing high broken downward inside this HTF candle
            choch_idx, ltf_entry = _find_ltf_bearish_choch(
                df_ltf, cur.name, prev_high)
            if choch_idx is not None and ltf_entry is not None:
                rr = (ltf_entry - midpoint) / max(ltf_entry - cur_high, 1e-9)
                conf = 0.7 if abs(body) > (cur_high - cur_low) * 0.3 else 0.5
                setups.append(CRTSetup(
                    direction='SELL', htf_index=len(df_htf) - i,
                    sweep_level=sweep, midpoint=midpoint,
                    choch_index=choch_idx, ltf_entry=ltf_entry,
                    invalidation=cur_high + (cur_high - cur_low) * 0.1,
                    rr=rr, confidence=conf))

        # BULLISH CRT: HTF candle wicks BELOW prior HTF low and closes back inside
        elif cur_low < prev_low and body > 0 and cur_close > midpoint:
            sweep = prev_low
            choch_idx, ltf_entry = _find_ltf_bullish_choch(
                df_ltf, cur.name, prev_low)
            if choch_idx is not None and ltf_entry is not None:
                rr = (midpoint - ltf_entry) / max(prev_low - ltf_entry, 1e-9)
                conf = 0.7 if abs(body) > (cur_high - cur_low) * 0.3 else 0.5
                setups.append(CRTSetup(
                    direction='BUY', htf_index=len(df_htf) - i,
                    sweep_level=sweep, midpoint=midpoint,
                    choch_index=choch_idx, ltf_entry=ltf_entry,
                    invalidation=cur_low - (cur_high - cur_low) * 0.1,
                    rr=rr, confidence=conf))

    return setups


def _find_ltf_bearish_choch(df_ltf: pd.DataFrame, htf_end,
                            prior_high: float) -> Tuple[Optional[int], Optional[float]]:
    """Find a bearish CHoCH (break of a prior LTF swing high to the downside
    after an upward sweep of that swing high)."""
    mask = df_ltf.index <= htf_end
    sub = df_ltf.loc[mask]
    if len(sub) < 10:
        return None, None
    # Find a swing high swept, then a lower low
    sh_idx = sub['high'].idxmax()
    sh = float(sub.loc[sh_idx, 'high'])
    if sh <= prior_high:
        return None, None
    after = sub.loc[sub.index > sh_idx]
    if after.empty:
        return None, None
    choch_idx = after['low'].idxmin()
    return sub.index.get_loc(choch_idx), float(after.loc[choch_idx, 'low'])


def _find_ltf_bullish_choch(df_ltf: pd.DataFrame, htf_end,
                            prior_low: float) -> Tuple[Optional[int], Optional[float]]:
    mask = df_ltf.index <= htf_end
    sub = df_ltf.loc[mask]
    if len(sub) < 10:
        return None, None
    sl_idx = sub['low'].idxmin()
    sl = float(sub.loc[sl_idx, 'low'])
    if sl >= prior_low:
        return None, None
    after = sub.loc[sub.index > sl_idx]
    if after.empty:
        return None, None
    choch_idx = after['high'].idxmax()
    return sub.index.get_loc(choch_idx), float(after.loc[choch_idx, 'high'])
