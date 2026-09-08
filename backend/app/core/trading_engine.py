"""
Core Trading Engine
- Order Execution
- Position Management
- Portfolio Tracking
- Performance Analytics
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from .advanced_engine import AdvancedEngine, AdvancedTradeConfig
from .ai_overseer import TradeScore, TradeGrade, AIOverseer
from loguru import logger
from enum import Enum


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Order:
    symbol: str
    side: str
    quantity: float
    price: float
    order_type: str
    status: OrderStatus = OrderStatus.PENDING
    order_id: Optional[str] = None
    filled_quantity: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime = field(default_factory=datetime.now)


class TradingEngine:
    """Main Trading Engine - Order Execution and Position Management"""
    
    def __init__(self):
        self.positions: List[Position] = []
        self.orders: List[Order] = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0
        }
    
    async def execute_order(self, symbol: str, side: str, quantity: float, 
                            price: float = 0.0, order_type: str = "MARKET") -> Dict:
        """Execute a trading order"""
        try:
            order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type=order_type
            )
            self.orders.append(order)
            logger.info(f"Order executed: {side} {quantity} {symbol} @ {price}")
            return {
                'success': True,
                'order_id': order.order_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'status': order.status.value
            }
        except Exception as e:
            logger.error(f"Order execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def manage_risk(self, position_size: float, stop_loss: float) -> Dict:
        """Manage risk for a position"""
        try:
            risk_amount = position_size * stop_loss
            return {
                'risk_amount': risk_amount,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'risk_percent': stop_loss * 100
            }
        except Exception as e:
            logger.error(f"Risk management error: {e}")
            return {'error': str(e)}
    
    def close_position(self, position_id: str) -> Dict:
        """Close an open position"""
        try:
            for i, pos in enumerate(self.positions):
                if pos.symbol == position_id:
                    closed_pos = self.positions.pop(i)
                    self.performance_metrics['total_trades'] += 1
                    if closed_pos.realized_pnl > 0:
                        self.performance_metrics['winning_trades'] += 1
                    else:
                        self.performance_metrics['losing_trades'] += 1
                    self.performance_metrics['total_pnl'] += closed_pos.realized_pnl
                    logger.info(f"Position closed: {position_id} PnL: {closed_pos.realized_pnl}")
                    return {
                        'success': True,
                        'position': position_id,
                        'pnl': closed_pos.realized_pnl
                    }
            return {'success': False, 'error': 'Position not found'}
        except Exception as e:
            logger.error(f"Close position error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_performance(self) -> Dict:
        """Get trading performance metrics"""
        total = self.performance_metrics['total_trades']
        wins = self.performance_metrics['winning_trades']
        return {
            **self.performance_metrics,
            'win_rate': (wins / total * 100) if total > 0 else 0.0,
            'open_positions': len(self.positions),
            'pending_orders': len([o for o in self.orders if o.status == OrderStatus.PENDING])
        }
