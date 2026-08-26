"""
BREAKOUT BOT - Trade breakouts from SR and channels
Features: Support/Resistance detection, Volume confirmation, False breakout filter,
          Trendline breakout, Channel breakout, Volatility-based entries
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class BreakoutBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Breakout", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.lookback = config.get('lookback', 20)
        self.min_volume_mult = config.get('min_volume_mult', 1.5)

    def _find_sr(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        try:
            highs = df['high'].rolling(self.lookback).max().dropna().tolist()
            lows = df['low'].rolling(self.lookback).min().dropna().tolist()
            resistance = sorted(set([round(h, 4) for h in highs]))[-3:]
            support = sorted(set([round(l, 4) for l in lows]))[:3]
            return {'resistance': resistance, 'support': support}
        except Exception:
            return {'resistance': [], 'support': []}

    def _is_false_breakout(self, df: pd.DataFrame, level: float, direction: str) -> bool:
        try:
            last3 = df.iloc[-3:]
            if direction == 'BULLISH':
                return not (last3['close'].iloc[-1] > level and last3['volume'].iloc[-1] > last3['volume'].mean() * self.min_volume_mult)
            else:
                return not (last3['close'].iloc[-1] < level and last3['volume'].iloc[-1] > last3['volume'].mean() * self.min_volume_mult)
        except Exception:
            return True

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < self.lookback + 5:
                return None
            current = df.iloc[-1]
            score = self.gate.score_signal(df, "NEUTRAL")
            sr = self._find_sr(df)
            side = None
            entry = current['close']
            stop_loss = entry
            take_profit = entry
            reason = ""

            if sr['resistance'] and not self._is_false_breakout(df, sr['resistance'][-1], 'BULLISH') and current['close'] > sr['resistance'][-1]:
                side = "BUY"
                stop_loss = sr['resistance'][-1] * 0.998
                take_profit = entry + (entry - stop_loss) * 2.0
                reason = f"Breakout BUY above R={sr['resistance'][-1]:.4f}"
            elif sr['support'] and not self._is_false_breakout(df, sr['support'][0], 'BEARISH') and current['close'] < sr['support'][0]:
                side = "SELL"
                stop_loss = sr['support'][0] * 1.002
                take_profit = entry - (stop_loss - entry) * 2.0
                reason = f"Breakout SELL below S={sr['support'][0]:.4f}"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE:
                return self.gate.make_signal(
                    score, side, entry, stop_loss, take_profit, reason,
                    ['support_resistance', 'volume', 'volatility'],
                    {'sr': sr}
                )
            return None
        except Exception as e:
            logger.error(f"Breakout analyze error: {e}")
            return None
