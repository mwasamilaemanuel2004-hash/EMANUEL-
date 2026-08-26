"""
Trade Service
Business logic for trade execution and management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from ..core.trading_engine import TradingEngine
from ..core.risk_management_engine import RiskEngine
from ..core.bot_state_manager import BotStateManager


class TradeService:
    """Service for trade operations"""
    
    def __init__(self):
        self.trading_engine = TradingEngine()
        self.risk_engine = RiskEngine()
        self.bot_state_manager = BotStateManager("trade_service")
    
    async def execute_trade(self, symbol: str, side: str, quantity: float, 
                           price: float = 0.0) -> Dict:
        """Execute a trade with risk checks"""
        try:
            # Check if trading is allowed
            if not self.risk_engine.can_trade():
                return {
                    'success': False,
                    'error': 'Trading paused due to risk limits',
                    'risk_status': self.risk_engine.get_status()
                }
            
            # Execute order
            result = await self.trading_engine.execute_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price
            )
            
            if result.get('success'):
                logger.info(f"Trade executed: {side} {quantity} {symbol}")
            
            return result
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        return {
            'trading_engine': self.trading_engine.get_performance(),
            'risk': self.risk_engine.get_status(),
            'bot_state': self.bot_state_manager.get_state()
        }
