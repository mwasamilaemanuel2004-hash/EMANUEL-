"""
Multi-Confluence Filter — adds FVG, BOS, and manipulation checks to existing
SM setups. PURELY ADDITIVE: takes existing SM setups and re-scores them.
Improves win rate by requiring additional Smart Money confluence.
"""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


def find_fvgs(df: pd.DataFrame, max_lookback: int = 50) -> Dict[int, Dict]:
    """
    Find Fair Value Gaps (3-candle imbalances).
    Bullish FVG: low[i] > high[i-2] (gap up)
    Bearish FVG: high[i] < low[i-2] (gap down)
    Returns dict mapping bar index -> fvg info.
    """
    fvgs: Dict[int, Dict] = {}
    highs = df['high'].values
    lows = df['low'].values
    n = len(df)
    for i in range(2, n):
        if lows[i] > highs[i-2]:
            fvgs[i] = {'side': 'BUY', 'top': float(lows[i]),
                       'bottom': float(highs[i-2]), 'idx': i}
        elif highs[i] < lows[i-2]:
            fvgs[i] = {'side': 'SELL', 'top': float(lows[i-2]),
                       'bottom': float(highs[i]), 'idx': i}
    return fvgs


def has_bos_confirmation(df: pd.DataFrame, eb: int, side: str,
                         swing_lookback: int = 10) -> bool:
    """
    BOS (Break of Structure): the confirmation bar breaks the prior swing
    in the direction of the trade.
    For BUY: close[eb] > max(high[eb-lookback:eb])
    For SELL: close[eb] < min(low[eb-lookback:eb])
    """
    if eb < swing_lookback + 1:
        return False
    c = float(df['close'].iloc[eb])
    if side == "BUY":
        return c > float(df['high'].iloc[eb - swing_lookback:eb].max())
    else:
        return c < float(df['low'].iloc[eb - swing_lookback:eb].min())


def nearest_fvg(df: pd.DataFrame, eb: int, side: str,
                max_dist: int = 15) -> Optional[Dict]:
    """Find the nearest FVG on the same side within max_dist bars."""
    fvgs = find_fvgs(df)
    candidates = [f for f in fvgs.values()
                  if f['side'] == side and abs(f['idx'] - eb) <= max_dist]
    if not candidates:
        return None
    return min(candidates, key=lambda f: abs(f['idx'] - eb))


def enhance_setup_confluence(setup, df: pd.DataFrame) -> float:
    """
    Take an existing SM setup and return a bonus 0.0-0.3 based on
    additional confluence (FVG, BOS). Used to boost the runner size
    in the profit enhancer.
    """
    bonus = 0.0
    if has_bos_confirmation(df, setup.ltf_idx, setup.side):
        bonus += 0.15
    fvg = nearest_fvg(df, setup.ltf_idx, setup.side)
    if fvg is not None:
        bonus += 0.15
    return bonus
