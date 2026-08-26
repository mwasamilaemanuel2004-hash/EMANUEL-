"""
SMART MONEY BOT - Follow institutional traders
Features: Order block detection, Fair Value Gap (FVG), Liquidity pool identification,
          Supply/Demand zones, Premium/Discount zones, Market manipulation detection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class SmartMoneyBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Smart Money", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.ob_lookback = config.get('ob_lookback', 20)
        self.fvg_threshold = config.get('fvg_threshold', 0.001)

    def _detect_order_blocks(self, df: pd.DataFrame) -> List[Dict]:
        try:
            blocks = []
            for i in range(self.ob_lookback, len(df)):
                if df['close'].iloc[i] > df['open'].iloc[i] and df['volume'].iloc[i] > df['volume'].rolling(20).mean().iloc[i] * 1.3:
                    blocks.append({'type': 'BULLISH', 'price': df['low'].iloc[i], 'idx': i})
                elif df['close'].iloc[i] < df['open'].iloc[i] and df['volume'].iloc[i] > df['volume'].rolling(20).mean().iloc[i] * 1.3:
                    blocks.append({'type': 'BEARISH', 'price': df['high'].iloc[i], 'idx': i})
            return blocks[-5:]
        except Exception:
            return []

    def _detect_fvg(self, df: pd.DataFrame) -> List[Dict]:
        try:
            fvgs = []
            for i in range(2, len(df)):
                h1, l1 = df['high'].iloc[i-2], df['low'].iloc[i-2]
                h3, l3 = df['high'].iloc[i], df['low'].iloc[i]
                if h1 < l3:
                    fvgs.append({'type': 'BULLISH', 'gap': [h1, l3], 'idx': i})
                elif l1 > h3:
                    fvgs.append({'type': 'BEARISH', 'gap': [h3, l1], 'idx': i})
            return [f for f in fvgs if abs(f['gap'][1] - f['gap'][0]) / df['close'].iloc[-1] > self.fvg_threshold][-5:]
        except Exception:
            return []

    def _detect_liquidity(self, df: pd.DataFrame) -> Dict:
        try:
            highs = df['high'].rolling(20).max().iloc[-1]
            lows = df['low'].rolling(20).min().iloc[-1]
            return {'buy_liquidity': highs, 'sell_liquidity': lows}
        except Exception:
            return {}

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 30:
                return None
            current = df.iloc[-1]
            ob = self._detect_order_blocks(df)
            fvg = self._detect_fvg(df)
            liq = self._detect_liquidity(df)
            score = self.gate.score_signal(df, "NEUTRAL")

            side = None
            entry = current['close']
            stop_loss = entry
            take_profit = entry
            reason = ""

            if ob and fvg:
                last_ob = ob[-1]
                last_fvg = fvg[-1]
                if last_ob['type'] == 'BULLISH' and last_fvg['type'] == 'BULLISH' and current['close'] > last_ob['price']:
                    side = "BUY"
                    stop_loss = last_ob['price'] * 0.999
                    take_profit = entry + (entry - stop_loss) * 2.5
                    reason = f"SmartMoney BUY OB+FVG above {last_ob['price']:.4f}"
                elif last_ob['type'] == 'BEARISH' and last_fvg['type'] == 'BEARISH' and current['close'] < last_ob['price']:
                    side = "SELL"
                    stop_loss = last_ob['price'] * 1.001
                    take_profit = entry - (stop_loss - entry) * 2.5
                    reason = f"SmartMoney SELL OB+FVG below {last_ob['price']:.4f}"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE:
                return self.gate.make_signal(
                    score, side, entry, stop_loss, take_profit, reason,
                    ['order_block', 'fvg', 'liquidity', 'volume'],
                    {'ob_count': len(ob), 'fvg_count': len(fvg), 'liq': liq}
                )
            return None
        except Exception as e:
            logger.error(f"SmartMoney analyze error: {e}")
            return None
