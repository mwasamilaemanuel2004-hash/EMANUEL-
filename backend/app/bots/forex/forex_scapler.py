"""
FOREX SCALPER BOT - High-frequency quick trades
Features: High-frequency trading, micro market structure, order book analysis,
          tick velocity detection, spread monitoring, quick profit (5-10 pips), max 100/day
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class ForexScalperBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Forex Scalper", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.pip_value = config.get('pip_value', 0.0001)
        self.target_pips = config.get('target_pips', 8)
        self.max_spread_pip = config.get('max_spread_pip', 1.5)
        self.max_trades_per_day = config.get('max_trades_per_day', 100)
        self.trades_today = 0

    def _tick_velocity(self, df: pd.DataFrame) -> float:
        try:
            return abs(df['close'].pct_change()).iloc[-10:].mean()
        except Exception:
            return 0.0

    def _spread_ok(self, df: pd.DataFrame) -> bool:
        try:
            spread = (df['high'] - df['low']).iloc[-1]
            return spread <= self.max_spread_pip * self.pip_value
        except Exception:
            return True

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1m')
            if df is None or len(df) < 30:
                return None
            if self.trades_today >= self.max_trades_per_day:
                return None

            current = df.iloc[-1]
            prev = df.iloc[-2]
            velocity = self._tick_velocity(df)
            score = self.gate.score_signal(df, "NEUTRAL")

            tp = self.target_pips * self.pip_value
            sl = tp * 0.5

            if velocity < 0.0003 or not self._spread_ok(df):
                return None

            side = None
            entry = current['close']
            stop_loss = entry
            take_profit = entry
            rr = 0.0
            if current['close'] > prev['close'] and current['close'] > df.iloc[-5]['close']:
                side = "BUY"; stop_loss = entry - sl; take_profit = entry + tp
                rr = tp / sl; reason = f"Scalp BUY vel={velocity:.4f}"
            elif current['close'] < prev['close'] and current['close'] < df.iloc[-5]['close']:
                side = "SELL"; stop_loss = entry + sl; take_profit = entry - tp
                rr = tp / sl; reason = f"Scalp SELL vel={velocity:.4f}"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE and rr >= 2.0:
                sig = self.gate.make_signal(
                    score, side, entry, stop_loss, take_profit,
                    reason, ['tick_velocity', 'spread', 'micro_structure'],
                    {'tf': '1m', 'target_pips': self.target_pips}
                )
                if sig:
                    self.trades_today += 1
                return sig
            return None
        except Exception as e:
            logger.error(f"ForexScalper analyze error: {e}")
            return None
