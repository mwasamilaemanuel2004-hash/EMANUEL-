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
        self.symbol = config.get('symbol', 'EURUSD')
        self.timeframes = tuple(config.get('timeframes', ('1m', '5m', '10m', '15m')))
        self.timeframe = config.get('timeframe', '1m')
        if self.timeframe not in self.timeframes:
            raise ValueError(f"Unsupported scalper timeframe: {self.timeframe}")
        self.risk_per_trade_pct = float(config.get('risk_per_trade_pct', config.get('risk_per_trade', 1.0)))
        if not 0.8 <= self.risk_per_trade_pct <= 5.0:
            raise ValueError("Forex scalper risk_per_trade_pct must be between 0.8 and 5.0")
        self.capital = float(config.get('capital', 1000.0))
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
            df = data if isinstance(data, pd.DataFrame) else data.get(self.timeframe)
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
                    {self.timeframe: df}, side, entry, reason,
                    ['tick_velocity', 'spread', 'micro_structure'],
                    {'tf': self.timeframe, 'target_pips': self.target_pips},
                    symbol=self.symbol, risk_pct=self.risk_per_trade_pct,
                    atr=sl
                )
                if sig:
                    sig.position_size = (self.capital * self.risk_per_trade_pct / 100) / sl
                    self.trades_today += 1
                return sig
            return None
        except Exception as e:
            logger.error(f"ForexScalper analyze error: {e}")
            return None
