"""
Displacement + Premium/Discount + Accumulation/Distribution engine.

Displacement: a strong, impulsive candle (or 2-3 candle sequence) that
breaks market structure. It leaves an imbalance (FVG) behind. These are
the "footprints" of institutional order flow.

Premium/Discount: price relative to the equilibrium (50% of a range).
  - Premium zone: above equilibrium -> sellers have edge
  - Discount zone: below equilibrium -> buyers have edge
  Best buys in discount, best sells in premium.

Accumulation/Distribution: volume + price action patterns that show
institutional positioning before a big move.
  - Accumulation: range-bound, rising volume on up-bars, falling on down-bars
  - Distribution: range-bound, falling volume on up-bars, rising on down-bars
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def detect_displacement(df: pd.DataFrame, atr_period: int = 14,
                        body_mult: float = 1.5) -> List[int]:
    """
    Find displacement candles: body > 1.5*ATR and close in the direction.
    Returns list of indices of displacement candles.
    """
    atr = df['close'].diff().abs().rolling(atr_period).mean()
    out = []
    for i in range(atr_period, len(df)):
        if pd.isna(atr.iloc[i]):
            continue
        body = abs(float(df['close'].iloc[i] - df['open'].iloc[i]))
        if body > atr.iloc[i] * body_mult:
            out.append(i)
    return out


def premium_discount_zone(df: pd.DataFrame, lookback: int = 50,
                          current_idx: Optional[int] = None) -> str:
    """
    Return 'PREMIUM' (above 50% of range -> sell), 'DISCOUNT' (below -> buy),
    or 'EQUILIBRIUM' (at 50%).
    """
    if current_idx is None:
        current_idx = len(df) - 1
    sub = df.iloc[max(0, current_idx - lookback): current_idx + 1]
    if sub.empty:
        return "EQUILIBRIUM"
    rng_high = float(sub['high'].max())
    rng_low = float(sub['low'].min())
    eq = (rng_high + rng_low) / 2
    price = float(df['close'].iloc[current_idx])
    if price > eq * 1.001:
        return "PREMIUM"
    if price < eq * 0.999:
        return "DISCOUNT"
    return "EQUILIBRIUM"


def accumulation_distribution_signal(df: pd.DataFrame, lookback: int = 20,
                                     current_idx: Optional[int] = None) -> str:
    """
    Detect accumulation / distribution using volume + price range.
    Accumulation: tight range + rising OBV-like measure -> bullish
    Distribution: tight range + falling OBV-like measure -> bearish
    """
    if current_idx is None:
        current_idx = len(df) - 1
    sub = df.iloc[max(0, current_idx - lookback): current_idx + 1]
    if len(sub) < 5:
        return "NEUTRAL"
    rng = float(sub['high'].max() - sub['low'].min())
    avg_range = float((sub['high'] - sub['low']).mean())
    tight = rng < avg_range * lookback * 0.8  # tight range
    # OBV proxy: sign(close-open) * volume, cumulative
    sign = np.sign(sub['close'].values - sub['open'].values)
    obv = (sign * sub['volume'].values).cumsum()
    if not tight:
        return "NEUTRAL"
    if obv[-1] > obv[0] * 1.1:
        return "ACCUMULATION"
    if obv[-1] < obv[0] * 0.9:
        return "DISTRIBUTION"
    return "NEUTRAL"


def manipulation_check(df: pd.DataFrame, current_idx: int,
                       lookback: int = 5) -> bool:
    """
    Detect potential manipulation: a sharp wick beyond a prior swing that
    immediately reverses (the classic 'stop hunt before the real move').
    """
    if current_idx < lookback + 3:
        return False
    recent = df.iloc[current_idx - lookback: current_idx + 1]
    prior = df.iloc[current_idx - lookback - 5: current_idx - lookback]
    if recent['high'].iloc[-1] > prior['high'].max() and \
       recent['close'].iloc[-1] < recent['high'].iloc[-1] - \
       (recent['high'].iloc[-1] - recent['low'].iloc[-1]) * 0.5:
        return True  # bearish manipulation
    if recent['low'].iloc[-1] < prior['low'].min() and \
       recent['close'].iloc[-1] > recent['low'].iloc[-1] + \
       (recent['high'].iloc[-1] - recent['low'].iloc[-1]) * 0.5:
        return True  # bullish manipulation
    return False
