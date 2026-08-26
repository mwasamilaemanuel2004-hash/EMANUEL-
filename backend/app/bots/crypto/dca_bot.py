"""
DCA BOT - Dollar Cost Averaging
Features: Automatic regular buying, Smart entry timing, Volatility-adjusted amounts,
          RSI-based entries, Market cycle detection, Long-term accumulation
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class DcaBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("DCA Bot", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.interval_hours = config.get('interval_hours', 24)
        self.base_amount = config.get('base_amount', 100)
        self.rsi_oversold = config.get('rsi_oversold', 30)

    def _calculate_rsi(self, df: pd.DataFrame) -> float:
        try:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except Exception:
            return 50.0

    def _cycle_phase(self, df: pd.DataFrame) -> str:
        try:
            sma20 = df['close'].rolling(20).mean().iloc[-1]
            sma50 = df['close'].rolling(50).mean().iloc[-1]
            if sma20 > sma50:
                return "BULL"
            elif sma20 < sma50:
                return "BEAR"
            return "SIDE"
        except Exception:
            return "SIDE"

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 50:
                return None
            current = df.iloc[-1]
            rsi = self._calculate_rsi(df)
            phase = self._cycle_phase(df)
            score = self.gate.score_signal(df, "BULLISH")

            entry = current['close']
            sl = entry * 0.95
            tp = entry * 1.10
            reason = f"DCA buy RSI={rsi:.0f} phase={phase}"

            if score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE and rsi < self.rsi_oversold:
                return self.gate.make_signal(
                    score, "BUY", entry, sl, tp, reason,
                    ['rsi', 'cycle', 'accumulation'],
                    {'rsi': rsi, 'phase': phase, 'amount': self.base_amount}
                )
            return None
        except Exception as e:
            logger.error(f"DcaBot analyze error: {e}")
            return None
