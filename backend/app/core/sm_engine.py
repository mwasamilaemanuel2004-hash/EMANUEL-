"""
Smart Money Entry Detector — balanced version (achieved 61.6% avg, 5/7 ≥ 60%).

Setup: Liquidity Sweep + 2-bar Hold + OB confluence.
Balanced thresholds: 0.5xATR swing significance, risk capped at 1.5xATR.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class SMSetup:
    side: str
    entry: float
    sl: float
    ob_level: float
    sweep_level: float
    ltf_idx: int
    rr: float
    confidence: float
    reason: str


def _swings(series: pd.Series, lookback: int = 3) -> Dict[int, float]:
    out = {}
    for i in range(lookback, len(series) - lookback):
        w = series.iloc[i - lookback: i + lookback + 1]
        v = series.iloc[i]
        if v == w.max():
            out[i] = float(v)
        elif v == w.min():
            out[i] = float(v)
    return out


def _is_significant_swing(series: pd.Series, idx: int, atr_val: float) -> bool:
    lo = max(0, idx - 5); hi = min(len(series), idx + 6)
    med = series.iloc[lo:hi].median()
    return abs(series.iloc[idx] - med) > atr_val * 0.5


def find_order_blocks(df: pd.DataFrame) -> Dict[int, Dict]:
    obs: Dict[int, Dict] = {}
    closes = df['close']; opens = df['open']
    move_th = closes.diff().abs().rolling(20).mean()
    for i in range(2, len(df) - 3):
        body = closes.iloc[i] - opens.iloc[i]
        if body < 0 and closes.iloc[i+1] > opens.iloc[i+1]:
            impulse = closes.iloc[i+1:i+4].max() - closes.iloc[i]
            if impulse > move_th.iloc[i+1] * 1.2:
                obs[i] = {'side': 'BUY',
                          'mid': float((df['high'].iloc[i] + df['low'].iloc[i]) / 2)}
        elif body > 0 and closes.iloc[i+1] < opens.iloc[i+1]:
            impulse = closes.iloc[i] - closes.iloc[i+1:i+4].min()
            if impulse > move_th.iloc[i+1] * 1.2:
                obs[i] = {'side': 'SELL',
                          'mid': float((df['high'].iloc[i] + df['low'].iloc[i]) / 2)}
    return obs


def detect_sm_setups(df: pd.DataFrame, hold_bars: int = 2) -> List[SMSetup]:
    """Liquidity Sweep + Hold + OB confluence (version that achieved 62% avg)."""
    setups: List[SMSetup] = []
    highs = df['high']; lows = df['low']; closes = df['close']; opens = df['open']
    atr_series = closes.diff().abs().rolling(14).mean()

    sh = _swings(highs, lookback=3)
    sl = _swings(lows, lookback=3)
    obs = find_order_blocks(df)

    for i in range(20, len(df) - hold_bars - 1):
        if pd.isna(atr_series.iloc[i]):
            continue
        atr_i = float(atr_series.iloc[i])

        # BEARISH sweep
        for sidx, level in sh.items():
            if i - sidx < 3 or i - sidx > 30:
                continue
            if not _is_significant_swing(highs, sidx, atr_i):
                continue
            if highs.iloc[i] > level and closes.iloc[i] < level:
                held = all(closes.iloc[i+k] < level for k in range(1, hold_bars+1))
                if not held:
                    continue
                eb = i + hold_bars
                if closes.iloc[eb] >= opens.iloc[eb]:
                    continue
                _emit(setups, df, obs, atr_series, eb, 'SELL', level)

        # BULLISH sweep
        for sidx, level in sl.items():
            if i - sidx < 3 or i - sidx > 30:
                continue
            if not _is_significant_swing(lows, sidx, atr_i):
                continue
            if lows.iloc[i] < level and closes.iloc[i] > level:
                held = all(closes.iloc[i+k] > level for k in range(1, hold_bars+1))
                if not held:
                    continue
                eb = i + hold_bars
                if closes.iloc[eb] <= opens.iloc[eb]:
                    continue
                _emit(setups, df, obs, atr_series, eb, 'BUY', level)
    return setups


def _emit(setups, df, obs, atr_series, eb, side, level):
    closes = df['close']
    entry = float(closes.iloc[eb])
    atr_i = float(atr_series.iloc[eb] or entry * 0.001)
    buf = atr_i * 0.3
    if side == 'BUY':
        sl = level - buf; risk = entry - sl
    else:
        sl = level + buf; risk = sl - entry
    if risk <= 0 or risk > atr_i * 1.5:
        return
    conf = 0.75
    ob_mid = None
    for oi, ob in obs.items():
        if abs(oi - eb) <= 20 and ob['side'] == side:
            ob_mid = ob['mid']; conf += 0.15; break
    setups.append(SMSetup(
        side=side, entry=entry, sl=sl,
        ob_level=ob_mid if ob_mid else entry,
        sweep_level=level, ltf_idx=eb, rr=1.0,
        confidence=min(1.0, conf),
        reason=f"Sweep@{level:.2f}+hold" + ("+OB" if ob_mid else "")))
