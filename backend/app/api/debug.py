"""
Debug Entry API - Manual trade entry and system debugging endpoints
Used for testing, debugging, and manual trade execution
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..admin.admin_controller import AdminController
from ..core.trading_engine import TradingEngine
from ..core.risk_management_engine import RiskEngine
from ..core.bot_state_manager import BotStateManager
from ..core.adaptive_engine import AdaptiveEngine

router = APIRouter(prefix="/api/debug", tags=["Debug"])

# ============================================
# MODELS
# ============================================

class DebugEntryRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., EURUSD, BTCUSD)")
    side: str = Field(..., description="Trade direction: BUY or SELL")
    quantity: float = Field(..., gt=0, description="Trade quantity/volume")
    entry_price: Optional[float] = Field(None, description="Entry price (optional, uses market price)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    reason: str = Field(default="Debug entry", description="Reason for debug entry")
    bot_id: Optional[str] = Field(None, description="Associated bot ID")
    strategy: Optional[str] = Field(None, description="Trading strategy used")
    tag: Optional[str] = Field(None, description="Tag for identification")


class DebugCloseRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol to close")
    reason: str = Field(default="Debug close", description="Reason for debug close")
    partial: bool = Field(default=False, description="Partial close only")
    close_percent: float = Field(default=100.0, ge=0, le=100, description="Percentage to close")


class DebugSystemRequest(BaseModel):
    action: str = Field(..., description="System action: restart, shutdown, backup, status")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")


class DebugBotRequest(BaseModel):
    bot_id: str = Field(..., description="Bot ID to control")
    action: str = Field(..., description="Bot action: start, stop, pause, resume, restart")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")


# ============================================
# SINGLETONS (initialized on first use)
# ============================================

_admin_controller: Optional[AdminController] = None
_trading_engine: Optional[TradingEngine] = None
_risk_engine: Optional[RiskEngine] = None
_bot_state_manager: Optional[BotStateManager] = None
_adaptive_engine: Optional[AdaptiveEngine] = None


def get_admin_controller() -> AdminController:
    global _admin_controller
    if _admin_controller is None:
        _admin_controller = AdminController()
    return _admin_controller


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
        _bot_state_manager = BotStateManager("debug_bot")
    return _bot_state_manager


def get_adaptive_engine() -> AdaptiveEngine:
    global _adaptive_engine
    if _adaptive_engine is None:
        _adaptive_engine = AdaptiveEngine()
    return _adaptive_engine


# ============================================
# DEBUG ENTRY ENDPOINTS
# ============================================

@router.post("/entry", summary="Debug trade entry - manually enter a trade")
async def debug_entry(
    request: DebugEntryRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Manually enter a trade for debugging purposes.
    Creates a trade record with DEBUG tag.
    """
    try:
        admin = get_admin_controller()
        
        # Validate side
        if request.side.upper() not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Side must be BUY or SELL"
            )
        
        # Execute debug entry via admin controller
        result = await admin.execute_command(
            type=admin.CommandType.TRADE,
            action="force_open",
            params={
                "symbol": request.symbol.upper(),
                "side": request.side.upper(),
                "quantity": request.quantity,
                "reason": f"[DEBUG] {request.reason}"
            }
        )
        
        # Enhance result with debug metadata
        result["debug"] = True
        result["entry_price"] = request.entry_price
        result["stop_loss"] = request.stop_loss
        result["take_profit"] = request.take_profit
        result["bot_id"] = request.bot_id
        result["strategy"] = request.strategy
        result["tags"] = ["debug", request.tag] if request.tag else ["debug"]
        result["timestamp"] = datetime.now().isoformat()
        
        logger.warning(f"🔧 DEBUG ENTRY: {request.symbol} {request.side} {request.quantity} @ {request.entry_price or 'MARKET'}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug entry error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug entry failed: {str(e)}"
        )


@router.post("/close", summary="Debug trade close - manually close a trade")
async def debug_close(
    request: DebugCloseRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Manually close a trade for debugging purposes.
    """
    try:
        admin = get_admin_controller()
        
        result = await admin.execute_command(
            type=admin.CommandType.TRADE,
            action="force_close",
            params={
                "symbol": request.symbol.upper(),
                "reason": f"[DEBUG] {request.reason}"
            }
        )
        
        result["debug"] = True
        result["partial"] = request.partial
        result["close_percent"] = request.close_percent
        result["timestamp"] = datetime.now().isoformat()
        
        logger.warning(f"🔧 DEBUG CLOSE: {request.symbol} - {request.reason}")
        
        return result
        
    except Exception as e:
        logger.error(f"Debug close error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug close failed: {str(e)}"
        )


@router.get("/status", summary="Get debug system status")
async def debug_status() -> Dict:
    """
    Get comprehensive debug system status.
    Shows trading engine, risk engine, bot state, and adaptive engine status.
    """
    try:
        admin = get_admin_controller()
        risk = get_risk_engine()
        bot_mgr = get_bot_state_manager()
        adaptive = get_adaptive_engine()
        
        return {
            "debug_mode": True,
            "timestamp": datetime.now().isoformat(),
            "system": admin.get_system_status(),
            "risk": risk.get_status(),
            "bot_state": bot_mgr.get_state(),
            "adaptive": adaptive.get_adaptive_params(),
            "trading_engine": {
                "positions": len(get_trading_engine().positions),
                "orders": len(get_trading_engine().orders)
            }
        }
        
    except Exception as e:
        logger.error(f"Debug status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug status failed: {str(e)}"
        )


@router.post("/system", summary="Execute debug system command")
async def debug_system(
    request: DebugSystemRequest
) -> Dict:
    """
    Execute system-level debug commands.
    Actions: restart, shutdown, backup, status, pause_all, resume_all
    """
    try:
        admin = get_admin_controller()
        
        action = request.action.lower()
        
        if action == "restart":
            result = await admin._restart_system()
        elif action == "shutdown":
            result = await admin._shutdown_system()
        elif action == "backup":
            result = await admin.system_updater.create_backup()
        elif action == "status":
            result = admin.get_system_status()
        elif action == "pause_all":
            result = await admin.trade_override.pause_all("Debug pause")
        elif action == "resume_all":
            result = await admin.trade_override.resume_all()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown system action: {action}"
            )
        
        result["debug"] = True
        result["action"] = action
        result["timestamp"] = datetime.now().isoformat()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug system error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug system command failed: {str(e)}"
        )


@router.post("/bot", summary="Execute debug bot command")
async def debug_bot(
    request: DebugBotRequest
) -> Dict:
    """
    Execute bot-level debug commands.
    Actions: start, stop, pause, resume, restart, status
    """
    try:
        admin = get_admin_controller()
        
        result = await admin.execute_command(
            type=admin.CommandType.BOT,
            action=request.action,
            params={"bot_id": request.bot_id, **request.params}
        )
        
        result["debug"] = True
        result["bot_id"] = request.bot_id
        result["action"] = request.action
        result["timestamp"] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"Debug bot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug bot command failed: {str(e)}"
        )


@router.get("/trades", summary="Get debug trade history")
async def debug_trades(
    limit: int = 50,
    symbol: Optional[str] = None,
    tag: Optional[str] = None
) -> Dict:
    """
    Get trade history filtered for debug trades.
    """
    try:
        # In production, query from database
        # For now, return structure
        return {
            "debug": True,
            "trades": [],
            "total": 0,
            "limit": limit,
            "filters": {
                "symbol": symbol,
                "tag": tag
            }
        }
        
    except Exception as e:
        logger.error(f"Debug trades error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug trades failed: {str(e)}"
        )


@router.get("/logs", summary="Get debug logs")
async def debug_logs(
    limit: int = 100,
    level: str = "DEBUG"
) -> Dict:
    """
    Get recent debug logs.
    """
    try:
        # In production, read from log files
        return {
            "debug": True,
            "logs": [],
            "total": 0,
            "limit": limit,
            "level": level
        }
        
    except Exception as e:
        logger.error(f"Debug logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug logs failed: {str(e)}"
        )


@router.post("/reset", summary="Reset debug system state")
async def debug_reset() -> Dict:
    """
    Reset debug system state (clear overrides, reset counters).
    """
    try:
        global _admin_controller, _trading_engine, _risk_engine, _bot_state_manager, _adaptive_engine
        
        _admin_controller = None
        _trading_engine = None
        _risk_engine = None
        _bot_state_manager = None
        _adaptive_engine = None
        
        logger.warning("🔧 DEBUG SYSTEM RESET")
        
        return {
            "success": True,
            "message": "Debug system state reset",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug reset failed: {str(e)}"
        )
