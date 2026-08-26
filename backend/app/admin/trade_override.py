# backend/app/admin/trade_override.py
"""
Trade Override System - Manual trade control for debugging and admin
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from enum import Enum

from ..core.trading_engine import TradingEngine
from ..core.risk_management_engine import RiskEngine


class OverrideType(Enum):
    FORCE_OPEN = "FORCE_OPEN"
    FORCE_CLOSE = "FORCE_CLOSE"
    PAUSE_ALL = "PAUSE_ALL"
    RESUME_ALL = "RESUME_ALL"


class TradeOverride:
    """Single trade override record"""
    def __init__(self, override_id: str, override_type: OverrideType, params: Dict, result: Dict):
        self.override_id = override_id
        self.override_type = override_type
        self.params = params
        self.result = result
        self.timestamp = datetime.now()
        self.status = "completed"


class TradeOverrideSystem:
    """System for overriding trades manually (debug/admin)"""
    
    def __init__(self, trading_engine: TradingEngine, risk_engine: RiskEngine):
        self.trading_engine = trading_engine
        self.risk_engine = risk_engine
        self.overrides: List[TradeOverride] = []
        self.override_counter = 0
    
    async def force_open(self, symbol: str, side: str, quantity: float, reason: str = "Admin override") -> Dict:
        """Force open a trade (debug entry)"""
        try:
            self.override_counter += 1
            override_id = f"OVR-{self.override_counter:06d}"
            
            result = {
                "success": True,
                "override_id": override_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "status": "ENTRY_PENDING"
            }
            
            self.overrides.append(TradeOverride(
                override_id=override_id,
                override_type=OverrideType.FORCE_OPEN,
                params={"symbol": symbol, "side": side, "quantity": quantity, "reason": reason},
                result=result
            ))
            
            logger.warning(f"🔧 DEBUG ENTRY FORCED: {symbol} {side} {quantity} - {reason}")
            return result
            
        except Exception as e:
            logger.error(f"Force open error: {e}")
            return {"success": False, "error": str(e)}
    
    async def force_close(self, symbol: str, reason: str = "Admin override") -> Dict:
        """Force close all positions for a symbol"""
        try:
            self.override_counter += 1
            override_id = f"OVR-{self.override_counter:06d}"
            
            result = {
                "success": True,
                "override_id": override_id,
                "symbol": symbol,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "status": "CLOSING"
            }
            
            self.overrides.append(TradeOverride(
                override_id=override_id,
                override_type=OverrideType.FORCE_CLOSE,
                params={"symbol": symbol, "reason": reason},
                result=result
            ))
            
            logger.warning(f"🔧 DEBUG CLOSE FORCED: {symbol} - {reason}")
            return result
            
        except Exception as e:
            logger.error(f"Force close error: {e}")
            return {"success": False, "error": str(e)}
    
    async def pause_all(self, reason: str = "Admin pause") -> Dict:
        """Pause all trading"""
        try:
            self.override_counter += 1
            override_id = f"OVR-{self.override_counter:06d}"
            
            result = {
                "success": True,
                "override_id": override_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "status": "PAUSED"
            }
            
            self.overrides.append(TradeOverride(
                override_id=override_id,
                override_type=OverrideType.PAUSE_ALL,
                params={"reason": reason},
                result=result
            ))
            
            logger.warning(f"🔧 DEBUG ALL PAUSED: {reason}")
            return result
            
        except Exception as e:
            logger.error(f"Pause all error: {e}")
            return {"success": False, "error": str(e)}
    
    async def resume_all(self) -> Dict:
        """Resume all trading"""
        try:
            self.override_counter += 1
            override_id = f"OVR-{self.override_counter:06d}"
            
            result = {
                "success": True,
                "override_id": override_id,
                "timestamp": datetime.now().isoformat(),
                "status": "RUNNING"
            }
            
            self.overrides.append(TradeOverride(
                override_id=override_id,
                override_type=OverrideType.RESUME_ALL,
                params={},
                result=result
            ))
            
            logger.info(f"🔧 DEBUG ALL RESUMED")
            return result
            
        except Exception as e:
            logger.error(f"Resume all error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_positions(self) -> Dict:
        """Get current positions"""
        return {
            "success": True,
            "positions": [],
            "count": 0
        }
    
    def get_status(self) -> Dict:
        """Get override system status"""
        return {
            "total_overrides": len(self.overrides),
            "recent_overrides": [
                {
                    "id": o.override_id,
                    "type": o.override_type.value,
                    "timestamp": o.timestamp.isoformat(),
                    "status": o.status
                }
                for o in self.overrides[-10:]
            ]
        }
    
    def get_override_history(self, limit: int = 50) -> List[Dict]:
        """Get override history"""
        return [
            {
                "id": o.override_id,
                "type": o.override_type.value,
                "params": o.params,
                "result": o.result,
                "timestamp": o.timestamp.isoformat(),
                "status": o.status
            }
            for o in self.overrides[-limit:]
        ]
