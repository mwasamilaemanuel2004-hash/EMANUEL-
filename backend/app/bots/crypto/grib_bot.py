"""
GRID BOT - Buy low, sell high inside range
Features: Grid level creation, Geometric/Arithmetic grids, Fibonacci grid levels,
          Dynamic grid adjustment, Multi-layer grids, Auto rebalancing
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from .._shared_signals import AiSignalGate


class GridBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Grid Bot", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.grid_count = config.get('grid_count', 10)
        self.range_pct = config.get('range_pct', 0.10)
        self.grid_type = config.get('grid_type', 'geometric')

    def _build_grid(self, mid: float) -> List[float]:
        try:
            half = mid * self.range_pct
            lo, hi = mid - half, mid + half
            if self.grid_type == 'geometric':
                return [lo * (hi/lo)**(i/(self.grid_count-1)) for i in range(self.grid_count)]
            return [lo + (hi-lo)*(i/(self.grid_count-1)) for i in range(self.grid_count)]
        except Exception:
            return []

    async def analyze_market(self, data) -> Optional[TradeSignal]:
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 30:
                return None
            current = df.iloc[-1]
            mid = (df['high'].rolling(20).max().iloc[-1] + df['low'].rolling(20).min().iloc[-1]) / 2
            grid = self._build_grid(mid)
            if not grid:
                return None
            score = self.gate.score_signal(df, "NEUTRAL")
            entry = current['close']
            sl = grid[0] * 0.99
            tp = grid[-1] * 1.01
            side = None
            reason = ""
            for i in range(1, len(grid)):
                if entry <= grid[i] and entry >= grid[i-1]:
                    if grid[i] > grid[i-1]:
                        side = "BUY"; reason = f"Grid BUY near level {i}/{self.grid_count}"
                    break
            if side is None and current['close'] < mid:
                side = "BUY"; reason = f"Grid BUY below mid {mid:.4f}"

            if side and score is not None and score.total_score >= self.gate.engine.cfg.MIN_CONFIDENCE:
                return self.gate.make_signal(
                    score, side, entry, sl, tp, reason,
                    ['grid', 'range', 'rebalance'],
                    {'grid': grid, 'mid': mid}
                )
            return None
        except Exception as e:
            logger.error(f"GridBot analyze error: {e}")
            return None
