"""
ULTRA PROFIT LEVEL ENGINE - AGGRESSIVE PROFIT ANALYSIS
Analysis na Level za Profit ULTRA - Aggressive Profit Multilayer

Analyzes market conditions and computes ULTRA profit levels:
- Profit Level Assessment (PLA)
- Aggressive Entry Timing (AET)
- Ultra Profit Optimization (UPO)
- Multi-Level Profit Staging (MLPS)
- Aggression Scoring (0-100)
"""
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class AggressionLevel(Enum):
    SAFE = "safe"                # 0-25
    NORMAL = "normal"            # 26-50
    AGGRESSIVE = "aggressive"    # 51-75
    ULTRA = "ultra"              # 76-90
    EXTREME = "extreme"          # 91-100


@dataclass
class ProfitLevelResult:
    """Profit level analysis result"""
    symbol: str
    timestamp: datetime
    entry_price: float
    current_price: float
    aggression_score: int
    aggression_level: AggressionLevel
    projected_profit: float
    projected_percent: float
    levels: Dict[str, Dict[str, float]]
    confidence: float
    recommendation: str
class UltraProfitEngine:
    """ULTRA PROFIT - Aggressive Profit Level Analysis Engine"""
    def __init__(self):
        self.history: List[ProfitLevelResult] = []
        self._scores: Dict[str, float] = {}
        self.stats = {
            'analyses': 0, 'avg_confidence': 0.0,
            'total_projected_profit': 0.0, 'best_level': 'safe',
        }
        logger.info("ULTRA PROFIT ENGINE initialized - AGGRESSIVE MODE")

    def analyze(self, symbol: str, entry_price: float, current_price: float,
                momentum: float = 0.5, volatility: float = 0.2,
                volume: float = 0.5, trend: float = 0.5) -> ProfitLevelResult:
        """Analyze and compute ultra profit levels"""
        move_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price else 0

        score = self._aggression_score(momentum, volatility, volume, trend, move_pct)
        aggression = self._level_from_score(score)

        mult = self._multipliers_from_aggression(score)
        levels = self._compute_levels(entry_price, move_pct, mult)

        projected_pct = move_pct * mult['runner']
        confidence = min(99.0, 60.0 + score * 0.35 + abs(move_pct) * 2)
        rec = self._recommendation(score, move_pct, momentum)

        result = ProfitLevelResult(
            symbol=symbol, timestamp=datetime.now(),
            entry_price=entry_price, current_price=current_price,
            aggression_score=score, aggression_level=aggression,
            projected_profit=round(abs(move_pct) / 100 * entry_price * mult['runner'], 2),
            projected_percent=round(projected_pct, 2),
            levels=levels, confidence=round(confidence, 1), recommendation=rec
        )

        self.history.append(result)
        self.stats['analyses'] += 1
        self.stats['total_projected_profit'] += result.projected_profit
        self.stats['avg_confidence'] = round(
            (self.stats['avg_confidence'] * (self.stats['analyses'] - 1) + confidence) / self.stats['analyses'], 1)
        if aggression.value not in ('safe', 'normal'):
            self.stats['best_level'] = aggression.value

        logger.info(f"ULTRA PROFIT: {symbol} score={score} level={aggression.value} proj%={result.projected_percent}%")
        return result

    @staticmethod
    def _aggression_score(momentum: float, volatility: float,
                          volume: float, trend: float, move_pct: float) -> int:
        score = (momentum * 30 + volatility * 20 + volume * 20 + trend * 20 + min(abs(move_pct), 10) * 2)
        return max(0, min(100, int(score)))

    @staticmethod
    def _level_from_score(score: int) -> AggressionLevel:
        if score >= 91: return AggressionLevel.EXTREME
        if score >= 76: return AggressionLevel.ULTRA
        if score >= 51: return AggressionLevel.AGGRESSIVE
        if score >= 26: return AggressionLevel.NORMAL
        return AggressionLevel.SAFE

    @staticmethod
    def _multipliers_from_aggression(score: int) -> Dict[str, float]:
        base_mult = 0.5 + (score / 100) * 2.5
        return {
            'l1': round(base_mult, 2),
            'l2': round(base_mult * 1.8, 2),
            'l3': round(base_mult * 3.0, 2),
            'runner': round(base_mult * (4.5 if score > 75 else 3.0), 2),
            'entry': round(0.35 + score / 100, 2),
        }

    def _compute_levels(self, base: float, move_pct: float,
                        mult: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        direction = 1 if move_pct >= 0 else -1
        step = abs(move_pct) / 100 or 0.002   # convert % to fraction
        levels = {}
        for key, m in mult.items():
            price = base + direction * base * step * m
            levels[key] = {
                'target_price': round(price, 6),
                'profit_pct': round(step * m * 100 * direction, 2),
            }
        return levels

    @staticmethod
    def _recommendation(score: int, move_pct: float, momentum: float) -> str:
        if score >= 76 and move_pct >= 0 and momentum > 0.6:
            return "ULTRA AGGRESSIVE: Enter now, ride the runner, 3-level staging"
        if score >= 51 and move_pct >= 0:
            return "AGGRESSIVE: Enter with staged take-profits + trailing stop"
        if move_pct < 0:
            return "CAUTION: Counter-trend - wait for momentum confirmation"
        return "CONSERVATIVE: Small position, tighten stop-loss, wait"

    def get_latest(self, symbol: str = None) -> Optional[Dict]:
        if not self.history:
            return None
        r = self.history[-1] if symbol is None else next(
            (x for x in reversed(self.history) if x.symbol == symbol), self.history[-1])
        return self._serialize(r)

    def get_history(self, limit: int = 50) -> List[Dict]:
        return [self._serialize(r) for r in self.history[-limit:]]

    @staticmethod
    def _serialize(r: ProfitLevelResult) -> Dict:
        return {
            'symbol': r.symbol, 'timestamp': r.timestamp.isoformat(),
            'entry_price': r.entry_price, 'current_price': r.current_price,
            'aggression_score': r.aggression_score,
            'aggression_level': r.aggression_level.value,
            'projected_profit': round(r.projected_profit, 2),
            'projected_percent': r.projected_percent,
            'levels': r.levels, 'confidence': r.confidence,
            'recommendation': r.recommendation,
        }

    def get_stats(self) -> Dict:
        return self.stats


ultra_profit_engine = UltraProfitEngine()

__all__ = ['UltraProfitEngine', 'ProfitLevelResult', 'AggressionLevel', 'ultra_profit_engine']