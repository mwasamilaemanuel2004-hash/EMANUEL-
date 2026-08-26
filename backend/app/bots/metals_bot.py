"""
METALS BOT - Gold, Silver, Platinum
Features: Precious metals trading, Safe haven analysis, Inflation hedge,
          Multi-metal portfolio, Physical holdings tracking, Futures contracts
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from .base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from ._shared_signals import AiSignalGate


class MetalsBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Metals Bot", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.metals = config.get('metals', ['XAUUSD', 'XAGUSD', 'XPTUSD'])

    def _safe_haven_signal(self, df: pd.DataFrame) -> str:
        try:
            sma20 = df['close'].rolling(20).mean().iloc[-1]
            sma50 = df['close'].rolling(50).mean().iloc[-1]
            rsi = 100 - (100 / (1 + (df['close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / df['close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean())))
            rsi_v = rsi.iloc[-1]
            if sma20 > sma50 and rsi_v < 70:
                return "BULLISH"
            elif sma20 < sma50 and rsi_v > 30:
                return "BEARISH"
            return "NEUTRAL"
        except Exception:
            return "NEUTRAL"

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 50:
                return None
            current = df.iloc[-1]
            score = self.gate.score_signal(df, "BULLISH")
            direction = self._safe_haven_signal(df)
            entry = current['close']
            sl = entry * 0.98
            tp = entry * 1.04
            side = None
            reason = ""
            if direction == "BULLISH":
                side = "BUY"; reason = f"Metals safe-haven BUY {entry:.2f}"
            elif direction == "BEARISH":
                side = "SELL"; reason = f"Metals correction SELL {entry:.2f}"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE:
                return self.gate.make_signal(
                    score, side, entry, sl, tp, reason,
                    ['safe_haven', 'inflation_hedge', 'trend'],
                    {'metals': self.metals}
                )
            return None
        except Exception as e:
            logger.error(f"MetalsBot analyze error: {e}")
            return None
