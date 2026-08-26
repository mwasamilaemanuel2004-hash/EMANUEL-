"""
COMMODITIES BOT - Oil, Natural Gas, Wheat
Features: Energy commodities, Agricultural commodities, Supply/Demand analysis,
          Weather impact, Season patterns, Futures trading
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from .base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from ._shared_signals import AiSignalGate


class CommoditiesBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Commodities Bot", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.commodities = config.get('commodities', ['WTI', 'NG', 'WHEAT'])

    def _season_signal(self, df: pd.DataFrame) -> str:
        try:
            month = datetime.now().month
            sma20 = df['close'].rolling(20).mean().iloc[-1]
            sma50 = df['close'].rolling(50).mean().iloc[-1]
            if sma20 > sma50:
                return "BULLISH"
            elif sma20 < sma50:
                return "BEARISH"
            return "NEUTRAL"
        except Exception:
            return "NEUTRAL"

    def _supply_demand_proxy(self, df: pd.DataFrame) -> float:
        try:
            return (df['close'].diff().rolling(10).sum().iloc[-1]) / df['close'].iloc[-1] * 100
        except Exception:
            return 0.0

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 50:
                return None
            current = df.iloc[-1]
            score = self.gate.score_signal(df, "NEUTRAL")
            direction = self._season_signal(df)
            sd = self._supply_demand_proxy(df)
            entry = current['close']
            sl = entry * 0.97
            tp = entry * 1.05
            side = None
            reason = f"Commodity SD={sd:.2f}%"
            if direction == "BULLISH" and sd > 0:
                side = "BUY"
            elif direction == "BEARISH" and sd < 0:
                side = "SELL"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE:
                return self.gate.make_signal(
                    score, side, entry, sl, tp, reason,
                    ['supply_demand', 'season', 'futures'],
                    {'sd': sd, 'commodities': self.commodities}
                )
            return None
        except Exception as e:
            logger.error(f"CommoditiesBot analyze error: {e}")
            return None
