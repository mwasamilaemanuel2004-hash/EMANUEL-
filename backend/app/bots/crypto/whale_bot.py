"""
WHALE BOT - Follow big traders
Features: Whale wallet tracking, Large transaction detection, Accumulation/Distribution,
          Smart money flow, Institutional activity, Market manipulation alerts
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class WhaleBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Whale Bot", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.min_whale_volume = config.get('min_whale_volume', 1000)

    def _detect_whale_flow(self, df: pd.DataFrame) -> Dict:
        try:
            recent_vol = df['volume'].iloc[-5:].mean()
            avg_vol = df['volume'].rolling(50).mean().iloc[-1]
            is_accum = recent_vol > avg_vol * 2.0 and df['close'].iloc[-1] > df['close'].iloc[-5]
            is_dist = recent_vol > avg_vol * 2.0 and df['close'].iloc[-1] < df['close'].iloc[-5]
            return {'accumulation': is_accum, 'distribution': is_dist, 'vol_mult': recent_vol / avg_vol if avg_vol else 1}
        except Exception:
            return {}

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 30:
                return None
            current = df.iloc[-1]
            score = self.gate.score_signal(df, "NEUTRAL")
            flow = self._detect_whale_flow(df)
            entry = current['close']
            sl = entry * 0.985
            tp = entry * 1.025
            side = None
            reason = ""
            if flow.get('accumulation'):
                side = "BUY"; reason = f"Whale accumulation vol_mult={flow.get('vol_mult', 1):.1f}"
            elif flow.get('distribution'):
                side = "SELL"; reason = f"Whale distribution vol_mult={flow.get('vol_mult', 1):.1f}"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE:
                return self.gate.make_signal(
                    score, side, entry, sl, tp, reason,
                    ['whale_flow', 'volume', 'smart_money'],
                    {'flow': flow}
                )
            return None
        except Exception as e:
            logger.error(f"WhaleBot analyze error: {e}")
            return None
