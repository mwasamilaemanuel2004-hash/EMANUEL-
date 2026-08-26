"""
CRYPTO SCALPER BOT - 24/7 micro price movement trading
Features: 24/7 trading, micro price movements, order flow analysis,
          liquidity detection, fast execution (ms), multiple crypto pairs
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class CryptoScalperBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Crypto Scalper", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.active_pairs = config.get('pairs', ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
        self.max_spread_pct = config.get('max_spread_pct', 0.05)
        self.position_time_limit = config.get('position_time_seconds', 5)

    def _order_flow_imbalance(self, df: pd.DataFrame) -> bool:
        try:
            oi = df['close'] * df['volume']
            oi_change = oi.pct_change().iloc[-3:].mean()
            return abs(oi_change) > 0.02
        except Exception:
            return False

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1m')
            if df is None or len(df) < 20:
                return None

            current = df.iloc[-1]
            prev = df.iloc[-2]
            score = self.gate.score_signal(df, "NEUTRAL")

            risk_distance = max(abs(current['close'] * 0.003), 1.0)
            volatility_ok = (current['high'] - current['low']) / current['close'] < 0.02

            side = None
            entry = current['close']
            stop_loss = entry
            take_profit = entry
            if current['close'] > prev['close'] and self._order_flow_imbalance(df) and volatility_ok:
                side = "BUY"
                stop_loss = entry - risk_distance
                take_profit = entry + risk_distance * 2.5
                reason = f"Scalp BUY {entry:.4f} OF-imbalance, low vol"
            elif current['close'] < prev['close'] and self._order_flow_imbalance(df) and volatility_ok:
                side = "SELL"
                stop_loss = entry + risk_distance
                take_profit = entry - risk_distance * 2.5
                reason = f"Scalp SELL {entry:.4f} OF-imbalance, low vol"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE:
                return self.gate.make_signal(
                    score, side, entry, stop_loss, take_profit,
                    reason, ['order_flow', 'liquidity', 'micro_price'],
                    {'pair': str(getattr(current, 'name', 'pair')), 'tf': '1m'}
                )
            return None
        except Exception as e:
            logger.error(f"CryptoScalper analyze error: {e}")
            return None
