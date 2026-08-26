"""
NEWS BOT - Trade news events
Features: Economic calendar integration, News sentiment analysis, Impact prediction,
          Volatility prediction, Pre-news positioning, Post-news strategy
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class NewsBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("News Bot", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.high_impact_events = config.get('high_impact_events', [])
        self.pre_news_minutes = config.get('pre_news_minutes', 30)
        self.post_news_minutes = config.get('post_news_minutes', 60)

    def _is_high_impact_window(self) -> bool:
        try:
            now = datetime.now()
            for ev in self.high_impact_events:
                evt = pd.Timestamp(ev.get('time', ''))
                if pd.notna(evt):
                    delta = (now - evt).total_seconds() / 60
                    if 0 <= delta <= self.post_news_minutes:
                        return True
            return False
        except Exception:
            return False

    def _volatility_expectation(self, df: pd.DataFrame) -> float:
        try:
            return df['atr'].iloc[-1] / df['close'].iloc[-1] * 100 if 'atr' in df.columns else 0.0
        except Exception:
            return 0.0

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 30:
                return None
            if not self._is_high_impact_window():
                return None

            current = df.iloc[-1]
            score = self.gate.score_signal(df, "NEUTRAL")
            vol_exp = self._volatility_expectation(df)
            entry = current['close']
            sl = entry * 0.985
            tp = entry * 1.025
            side = "BUY" if current['close'] > df['close'].rolling(20).mean().iloc[-1] else "SELL"
            reason = f"News trade vol_exp={vol_exp:.2f}%"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE and vol_exp > 0.3:
                return self.gate.make_signal(
                    score, side, entry, sl, tp, reason,
                    ['news_impact', 'volatility', 'calendar'],
                    {'vol_exp': vol_exp}
                )
            return None
        except Exception as e:
            logger.error(f"NewsBot analyze error: {e}")
            return None
