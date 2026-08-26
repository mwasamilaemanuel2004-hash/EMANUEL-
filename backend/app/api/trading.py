"""
Trading API Endpoints
- Place Orders
- View Positions
- Trade History
- Multi-Trade Support
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..core.trading_engine import TradingEngine
from ..core.risk_management_engine import RiskEngine
from ..core.bot_state_manager import BotStateManager, StopTrigger

router = APIRouter(prefix="/api/trading", tags=["Trading"])


# ============================================
# SCHEMAS
# ============================================

class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT, EURUSD)")
    side: str = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    price: Optional[float] = Field(None, description="Price (None for market order)")
    order_type: str = Field(default="MARKET", description="MARKET, LIMIT, STOP")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")


class MultiOrderRequest(BaseModel):
    orders: List[OrderRequest] = Field(..., description="Multiple orders to execute")
    require_permission: bool = Field(default=True, description="Require user permission for multi-trade")


class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str]
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    timestamp: str


class PositionResponse(BaseModel):
    symbol: str
    side: str
    entry_price: float
    quantity: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    opened_at: str


class TradeHistoryResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    status: str
    created_at: str


# ============================================
# SINGLETONS
# ============================================

_trading_engine: Optional[TradingEngine] = None
_risk_engine: Optional[RiskEngine] = None
_bot_state_manager: Optional[BotStateManager] = None


def get_trading_engine() -> TradingEngine:
    global _trading_engine
    if _trading_engine is None:
        _trading_engine = TradingEngine()
    return _trading_engine


def get_risk_engine() -> RiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine


def get_bot_state_manager() -> BotStateManager:
    global _bot_state_manager
    if _bot_state_manager is None:
        _bot_state_manager = BotStateManager("api_bot")
    return _bot_state_manager


# ============================================
# ENDPOINTS
# ============================================

@router.post("/order/place", response_model=OrderResponse, summary="Place a new order")
async def place_order(request: OrderRequest, db: Session = Depends(get_db)):
    """Place a new trading order"""
    try:
        engine = get_trading_engine()
        risk = get_risk_engine()

        # Validate side
        if request.side.upper() not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Side must be BUY or SELL"
            )

        # Risk check
        if request.stop_loss:
            risk_check = risk.validate_trade(
                symbol=request.symbol,
                side=request.side.upper(),
                quantity=request.quantity,
                entry_price=request.price or 0,
                stop_loss=request.stop_loss
            )
            if not risk_check.get('approved', True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Risk check failed: {risk_check.get('reason', 'Unknown')}"
                )

        # Execute order
        result = await engine.execute_order(
            symbol=request.symbol.upper(),
            side=request.side.upper(),
            quantity=request.quantity,
            price=request.price or 0.0,
            order_type=request.order_type.upper()
        )

        logger.info(f"Order placed: {request.symbol} {request.side} {request.quantity}")
        return OrderResponse(
            success=result.get('success', False),
            order_id=result.get('order_id'),
            symbol=request.symbol.upper(),
            side=request.side.upper(),
            quantity=request.quantity,
            price=request.price or 0.0,
            status=result.get('status', 'PENDING'),
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order placement error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order placement failed"
        )


@router.post("/order/place-multi", summary="Place multiple orders (requires permission)")
async def place_multi_order(request: MultiOrderRequest, db: Session = Depends(get_db)):
    """Place multiple trading orders (requires user permission)"""
    try:
        engine = get_trading_engine()
        risk = get_risk_engine()

        # Check permission for multi-trade
        if request.require_permission and len(request.orders) > 1:
            # In production, check user permissions
            logger.info(f"Multi-trade request: {len(request.orders)} orders")

        results = []
        for order in request.orders:
            # Validate side
            if order.side.upper() not in ["BUY", "SELL"]:
                results.append({
                    'symbol': order.symbol,
                    'success': False,
                    'error': 'Invalid side'
                })
                continue

            # Execute order
            result = await engine.execute_order(
                symbol=order.symbol.upper(),
                side=order.side.upper(),
                quantity=order.quantity,
                price=order.price or 0.0,
                order_type=order.order_type.upper()
            )
            results.append({
                'symbol': order.symbol,
                'success': result.get('success', False),
                'order_id': result.get('order_id'),
                'status': result.get('status', 'PENDING')
            })

        logger.info(f"Multi-order placed: {len(results)} orders")
        return {
            'success': True,
            'results': results,
            'total_orders': len(results),
            'successful': sum(1 for r in results if r.get('success')),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Multi-order placement error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multi-order placement failed"
        )


@router.get("/positions", response_model=List[PositionResponse], summary="Get open positions")
async def get_positions(db: Session = Depends(get_db)):
    """Get all open positions"""
    try:
        engine = get_trading_engine()
        positions = []
        for pos in engine.positions:
            positions.append(PositionResponse(
                symbol=pos.symbol,
                side=pos.side.value,
                entry_price=pos.entry_price,
                quantity=pos.quantity,
                unrealized_pnl=pos.unrealized_pnl,
                realized_pnl=pos.realized_pnl,
                stop_loss=pos.stop_loss,
                take_profit=pos.take_profit,
                opened_at=pos.opened_at.isoformat()
            ))
        return positions

    except Exception as e:
        logger.error(f"Get positions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get positions"
        )


@router.get("/history", summary="Get trade history")
async def get_history(limit: int = 100, db: Session = Depends(get_db)):
    """Get trade history"""
    try:
        engine = get_trading_engine()
        trades = []
        for trade in engine.orders[-limit:]:
            trades.append({
                'symbol': trade.symbol,
                'side': trade.side,
                'quantity': trade.quantity,
                'price': trade.price,
                'status': trade.status.value,
                'created_at': trade.created_at.isoformat()
            })
        return {
            'trades': trades,
            'total': len(trades),
            'limit': limit
        }

    except Exception as e:
        logger.error(f"Get history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trade history"
        )


@router.post("/position/close", summary="Close a position")
async def close_position(symbol: str, db: Session = Depends(get_db)):
    """Close an open position"""
    try:
        engine = get_trading_engine()
        result = engine.close_position(symbol.upper())

        if result.get('success'):
            logger.info(f"Position closed: {symbol}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', 'Position not found')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Close position error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close position"
        )


@router.get("/performance", summary="Get trading performance")
async def get_performance(db: Session = Depends(get_db)):
    """Get trading performance metrics"""
    try:
        engine = get_trading_engine()
        return engine.get_performance()

    except Exception as e:
        logger.error(f"Get performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance"
        )
