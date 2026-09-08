"""
PROFIT PER TRADE ENGINE - ULTRA
Trade Profit Per Trade - kuchukuwa profit per trade
"""
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class TradeProfitPlan:
    """Profit per trade plan"""
    symbol: str
    direction: TradeDirection
    entry_price: float
    capital: float
    risk_percent: float
    lot_size: float
    take_profit_levels: List[Dict[str, float]]
    max_profit_per_trade: float
    max_profit_pct: float
    expected_profit: float
    profit_factor: float
    stop_loss: float
    recommendation: str
class ProfitPerTradeEngine:
    """ULTRA Profit Per Trade Engine - max profit per trade"""
    def __init__(self):
        self.plans: List[TradeProfitPlan] = []
        self.stats = {
            'plans_created': 0, 'total_expected_profit': 0.0,
            'avg_profit_factor': 1.0, 'best_trade': None,
        }
        logger.info("PROFIT PER TRADE ENGINE initialized - ULTRA MODE")

    def compute_plan(self, symbol: str, entry_price: float, capital: float = 100.0,
                     risk_percent: float = 2.0, leverage: float = 50.0,
                     direction: TradeDirection = TradeDirection.LONG,
                     momentum: float = 0.7, volatility: float = 0.4,
                     volume: float = 0.6, trend: float = 0.7) -> TradeProfitPlan:
        """Compute optimal profit-per-trade plan with aggressive TP ladder"""
        risk_amount = capital * (risk_percent / 100)
        position_size = capital * leverage
        lot_size = round(position_size / max(entry_price, 0.0001), 6)
        structure = min(1.0, (momentum + volatility + volume + trend) / 4)
        dm = 1 if direction == TradeDirection.LONG else -1

        # Aggressive TP ladder
        tp1 = entry_price + dm * entry_price * (0.004 + structure * 0.006)
        tp2 = entry_price + dm * entry_price * (0.010 + structure * 0.015)
        tp3 = entry_price + dm * entry_price * (0.025 + structure * 0.035)
        runner = entry_price + dm * entry_price * (0.06 + structure * 0.09)
        stop = entry_price - dm * entry_price * (risk_percent / 500)
        alloc = [0.30, 0.30, 0.25, 0.15]

        prices = [tp1, tp2, tp3, runner]
        profits = []
        for i, tp in enumerate(prices):
            diff = (tp - entry_price) * dm if direction == TradeDirection.LONG else (entry_price - tp)
            profits.append(round(diff * lot_size * alloc[i], 2))

        loss_amount = abs(entry_price - stop) * lot_size
        max_profit = sum(profits)
        profit_factor = max_profit / max(loss_amount, 1e-8)
        expected = max_profit * structure * 0.7

        plan = TradeProfitPlan(
            symbol=symbol, direction=direction, entry_price=entry_price,
            capital=capital, risk_percent=risk_percent, lot_size=round(lot_size, 6),
            take_profit_levels=[
                {'level': 1, 'tp': round(tp1, 6), 'allocation': alloc[0], 'profit': profits[0]},
                {'level': 2, 'tp': round(tp2, 6), 'allocation': alloc[1], 'profit': profits[1]},
                {'level': 3, 'tp': round(tp3, 6), 'allocation': alloc[2], 'profit': profits[2]},
                {'level': 4, 'tp': round(runner, 6), 'allocation': alloc[3], 'profit': profits[3]},
            ],
            max_profit_per_trade=round(max_profit, 2),
            max_profit_pct=round((max_profit / capital) * 100, 2),
            expected_profit=round(expected, 2),
            profit_factor=round(profit_factor, 2),
            stop_loss=round(stop, 6),
            recommendation=self._recommendation(profit_factor, structure, momentum)
        )

        self.plans.append(plan)
        self.stats['plans_created'] += 1
        self.stats['total_expected_profit'] += plan.expected_profit
        if self.stats['best_trade'] is None or plan.profit_factor > self.stats['best_trade']['profit_factor']:
            self.stats['best_trade'] = {
                'symbol': symbol, 'profit_factor': plan.profit_factor,
                'max_profit_per_trade': plan.max_profit_per_trade,
            }

        logger.info(f"PROFIT/TRADE: {symbol} {direction.value} max=${plan.max_profit_per_trade} factor={plan.profit_factor}")
        return plan

    @staticmethod
    def _recommendation(profit_factor: float, structure: float, momentum: float) -> str:
        if profit_factor >= 8:
            return "ULTRA: Excellent risk/reward - full size + runner trail"
        if profit_factor >= 5:
            return "AGGRESSIVE: Strong profile - 4-level scaling"
        if profit_factor >= 3:
            return "NORMAL: Acceptable profile - tier 1-3"
        if momentum > 0.8:
            return "MOMENTUM: High momentum - enter but tight TP1"
        return "WAIT: Poor profile - reduce size or sit out"

    def get_latest(self, symbol: str = None) -> Optional[Dict]:
        if not self.plans:
            return None
        p = self.plans[-1] if symbol is None else next(
            (x for x in reversed(self.plans) if x.symbol == symbol), self.plans[-1])
        return self._serialize(p)

    def get_plans(self, limit: int = 50) -> List[Dict]:
        return [self._serialize(p) for p in self.plans[-limit:]]

    @staticmethod
    def _serialize(p: TradeProfitPlan) -> Dict:
        return {
            'symbol': p.symbol, 'direction': p.direction.value,
            'entry_price': p.entry_price, 'capital': p.capital,
            'risk_percent': p.risk_percent, 'lot_size': p.lot_size,
            'take_profit_levels': p.take_profit_levels,
            'max_profit_per_trade': p.max_profit_per_trade,
            'max_profit_pct': p.max_profit_pct,
            'expected_profit': p.expected_profit,
            'profit_factor': p.profit_factor,
            'stop_loss': p.stop_loss,
            'recommendation': p.recommendation,
        }

    def get_stats(self) -> Dict:
        return self.stats


profit_per_trade_engine = ProfitPerTradeEngine()

__all__ = ['ProfitPerTradeEngine', 'TradeProfitPlan', 'TradeDirection', 'profit_per_trade_engine']