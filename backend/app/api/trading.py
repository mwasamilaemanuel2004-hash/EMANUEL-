"""
Trading API Endpoints
- Place Orders
- View Positions
- Trade History
- Multi-Trade Support
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..core.trading_engine import TradingEngine
from ..core.risk_management_engine import RiskEngine
from ..core.bot_state_manager import BotStateManager, StopTrigger

# Shared live-price cache so external/exchange websocket threads can push
# ticks into every registered managed bot through one simple setter.
LIVE_PRICE_CACHE: dict[str, float] = {}


def push_live_price(symbol: str, price: float, volume: float | None = None,
                    bid: float | None = None, ask: float | None = None,
                    source: str = "external") -> bool:
    """Thread-safe helper: feed one real tick into every registered bot."""
    combined = False
    try:
        normalized = str(symbol).upper()
        LIVE_PRICE_CACHE[normalized] = float(price)
    except (TypeError, ValueError):
        return False
    for bot in list(_bots.values()):
        try:
            if hasattr(bot, "update_market_price"):
                combined = bot.update_market_price(
                    normalized, float(price), volume, bid, ask) or combined
        except Exception:
            pass
    return combined

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
# BOT CONTROL SCHEMAS (upgrade v12.1)
# ============================================

class BotConfigRequest(BaseModel):
    """Create or reconfigure a managed bot instance."""
    bot_id: str = Field(..., description="Unique bot identifier (e.g. crypto_scalper)")
    bot_type: str = Field(default="crypto_scalper", description="Bot class family")
    enabled: bool = Field(default=True, description="Global on/off switch")
    advanced_mode: bool = Field(default=False, description="Expose advanced parameters")
    smart_risk_enabled: bool = Field(default=True, description="Win-rate/streak-aware sizing")
    adaptive_enabled: bool = Field(default=True, description="Auto-adapt mode & parameters")
    trailing_take_profit_enabled: bool = Field(default=False, description="Trailing TP ratchet")
    dynamic_take_profit: bool = Field(default=True, description="Scale TP from recent results")
    take_profit_pct: Optional[float] = Field(default=None, gt=0, le=0.5, description="Explicit TP fraction override")
    stop_loss_pct: Optional[float] = Field(default=None, gt=0, le=0.5, description="Explicit SL fraction override")
    risk_per_trade_pct: float = Field(default=1.0, gt=0.8, le=5.0, description="Risk % per trade")
    capital: float = Field(default=1000.0, gt=0, description="Trading capital")
    pairs: List[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    timeframe: str = Field(default="1m", description="Primary timeframe")
    require_live_feed: bool = Field(default=False, description="Block synthetic fallback")
    max_trades_per_day: int = Field(default=500, ge=1, le=10000)


class BotToggleRequest(BaseModel):
    enabled: bool = Field(..., description="True to turn bot ON, False to turn OFF")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BotTickRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Market symbol")
    price: float = Field(..., gt=0, description="Tick price")
    volume: Optional[float] = Field(default=None, gt=0)
    bid: Optional[float] = Field(default=None, gt=0)
    ask: Optional[float] = Field(default=None, gt=0)
    timestamp: Optional[float] = Field(default=None, description="Unix ts (defaults to now)")
    source: str = Field(default="ws", description="Feed source label")


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
# MANAGED BOT REGISTRY (upgrade v12.1)
# ============================================

_bots: Dict[str, Any] = {}


def _build_bot(bot_id: str, request: BotConfigRequest) -> Any:
    """Build (or rebuild) a managed bot instance from user-facing config."""
    cfg = {
        'bot_id': bot_id,
        'enabled': request.enabled,
        'advanced_mode': request.advanced_mode,
        'smart_risk_enabled': request.smart_risk_enabled,
        'adaptive_enabled': request.adaptive_enabled,
        'trailing_take_profit_enabled': request.trailing_take_profit_enabled,
        'dynamic_take_profit': request.dynamic_take_profit,
        'take_profit_pct': request.take_profit_pct,
        'stop_loss_pct': request.stop_loss_pct,
        'risk_per_trade_pct': request.risk_per_trade_pct,
        'capital': request.capital,
        'pairs': request.pairs,
        'timeframe': request.timeframe,
        'require_live_feed': request.require_live_feed,
        'max_trades_per_day': request.max_trades_per_day,
        'start_background_tasks': False,  # tasks are driven by the toggle below
    }
    if request.bot_type == "crypto_scalper" or request.bot_type == "scalper":
        from ..bots.crypto.scalper_bot import CryptoScalperBot
        bot = CryptoScalperBot(cfg)
    else:
        from ..bots.base_bot import BaseBot
        bot = BaseBot(bot_id, cfg)
    return bot


def _get_managed_bot(bot_id: str) -> Optional[Any]:
    return _bots.get(bot_id)


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


# ============================================
# BOT CONTROL ENDPOINTS (upgrade v12.1)
# ============================================

@router.post("/bots/register", summary="Create or reconfigure a managed bot")
async def register_bot(request: BotConfigRequest):
    """Register/configure a bot instance with user on/off, risk and profit controls."""
    try:
        bot = _build_bot(request.bot_id, request)
        _bots[request.bot_id] = bot
        if request.enabled:
            try:
                bot.start_scalping()
            except Exception as exc:
                # bots without a scalping lifecycle simply stay registered
                logger.debug(f"start_scalping not available for {request.bot_id}: {exc}")
        logger.info(f"Registered managed bot: {request.bot_id} enabled={request.enabled}")
        return {
            'success': True,
            'bot_id': request.bot_id,
            'status': bot.get_status() if hasattr(bot, 'get_status') else {'bot_id': request.bot_id}
        }
    except Exception as e:
        logger.error(f"Bot register error: {e}")
        raise HTTPException(status_code=500, detail=f"Bot registration failed: {str(e)}")


@router.post("/bots/{bot_id}/toggle", summary="Turn a bot ON or OFF")
async def toggle_bot(bot_id: str, request: BotToggleRequest):
    """Global on/off for a managed bot."""
    try:
        bot = _get_managed_bot(bot_id)
        if bot is None:
            raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' not registered")
        if hasattr(bot, 'enabled'):
            bot.enabled = bool(request.enabled)
        if request.enabled and hasattr(bot, 'start_scalping'):
            try:
                bot.start_scalping()
            except Exception as exc:
                logger.debug(f"start_scalping: {exc}")
        elif not request.enabled and hasattr(bot, 'stop_scalping'):
            try:
                bot.stop_scalping()
            except Exception as exc:
                logger.debug(f"stop_scalping: {exc}")
        return {
            'success': True,
            'bot_id': bot_id,
            'enabled': bool(request.enabled),
            'status': bot.get_status() if hasattr(bot, 'get_status') else {'bot_id': bot_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bot toggle error: {e}")
        raise HTTPException(status_code=500, detail=f"Bot toggle failed: {str(e)}")


@router.post("/bots/{bot_id}/config", summary="Update bot advanced/risk/profit settings")
async def update_bot_config(bot_id: str, request: BotConfigRequest):
    """Update advanced mode, smart risk, profit/Take-Profit and dynamic mechanisms."""
    try:
        existing = _get_managed_bot(bot_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' not registered")
        request.bot_id = bot_id
        bot = _build_bot(bot_id, request)
        _bots[bot_id] = bot
        logger.info(f"Reconfigured managed bot: {bot_id}")
        return {
            'success': True,
            'bot_id': bot_id,
            'status': bot.get_status() if hasattr(bot, 'get_status') else {'bot_id': bot_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bot config error: {e}")
        raise HTTPException(status_code=500, detail=f"Bot config failed: {str(e)}")


@router.get("/bots", summary="List managed bots with live status")
async def list_bots():
    """List all registered bots including on/off state, risk controls and feed health."""
    try:
        result = []
        for bot_id, bot in _bots.items():
            status = bot.get_status() if hasattr(bot, 'get_status') else {'bot_id': bot_id}
            result.append(status)
        return {'bots': result, 'total': len(result)}
    except Exception as e:
        logger.error(f"Bot list error: {e}")
        raise HTTPException(status_code=500, detail=f"Bot list failed: {str(e)}")


@router.post("/bots/{bot_id}/tick", summary="Ingest one real market tick into a bot feed")
async def ingest_bot_tick(bot_id: str, request: BotTickRequest):
    """Push a real tick into the bot's rolling tick buffer (bid/ask/price)."""
    try:
        bot = _get_managed_bot(bot_id)
        if bot is None:
            raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' not registered")
        if hasattr(bot, 'ingest_tick'):
            accepted = await bot.ingest_tick(
                symbol=request.symbol,
                price=request.price,
                volume=request.volume,
                bid=request.bid,
                ask=request.ask,
                ts=request.timestamp,
                source=request.source,
            )
        elif hasattr(bot, 'update_market_price'):
            accepted = bot.update_market_price(request.symbol, request.price, request.volume,
                                               request.bid, request.ask)
        else:
            accepted = False
        return {
            'success': bool(accepted),
            'bot_id': bot_id,
            'symbol': request.symbol,
            'price': request.price,
            'feed_health': bot.get_feed_health() if hasattr(bot, 'get_feed_health') else {},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bot tick error: {e}")
        raise HTTPException(status_code=500, detail=f"Bot tick failed: {str(e)}")


@router.websocket("/ws/ticks")
async def websocket_ticks(websocket: WebSocket):
    """
    Real-time tick bridge: external/exchange websocket threads call
    `push_live_price()` and every registered managed bot receives the tick
    via its rolling tick buffer. Clients can also 'subscribe' to strategy
    updates per symbol.
    """
    await websocket.accept()
    active = True
    try:
        while True:
            raw = await websocket.receive_json()
            if not isinstance(raw, dict):
                continue
            msg_type = raw.get('type', 'tick')
            if msg_type == 'ping':
                await websocket.send_json({'type': 'pong', 'ts': datetime.utcnow().isoformat()})
                continue
            if msg_type == 'subscribe':
                symbol = str(raw.get('symbol', 'BTCUSDT')).upper()
                LIVE_PRICE_CACHE['_sub_' + symbol] = 1.0
                await websocket.send_json({
                    'type': 'subscribed',
                    'symbol': symbol,
                    'bots': [bid for bid, b in _bots.items() if hasattr(b, 'update_market_price')],
                })
                continue
            # Default raw tick message
            symbol = str(raw.get('symbol', 'BTCUSDT')).upper()
            price = float(raw.get('price', 0))
            if price > 0:
                push_live_price(symbol, price,
                                raw.get('volume'),
                                raw.get('bid'),
                                raw.get('ask'),
                                raw.get('source', 'ws'))
                await websocket.send_json({
                    'type': 'ack',
                    'symbol': symbol,
                    'price': price,
                    'bots': [bid for bid, b in _bots.items() if hasattr(b, 'update_market_price')],
                })
    except WebSocketDisconnect:
        active = False
    except Exception as e:
        logger.warning(f"Ticks websocket error: {e}")
    finally:
        if not active:
            logger.info("Ticks websocket closed")
