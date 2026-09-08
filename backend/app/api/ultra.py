"""
ULTRA PROFIT API - Profit Per Trade, Level Analysis, Tick Options, AI Guardian
Endpoints exposing the new super-power engines.
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from ..core.profit_per_trade_engine import (
    profit_per_trade_engine, ProfitPerTradeEngine, TradeDirection,
)
from ..core.profit_level_engine import ultra_profit_engine, UltraProfitEngine
from ..core.tick_option_engine import tick_option_engine, OptionType
from ..security.ai_guardian import ai_guardian

router = APIRouter()


class ProfitPlanRequest(BaseModel):
    symbol: str
    entry_price: float
    capital: float = 100.0
    risk_percent: float = 2.0
    leverage: float = 50.0
    direction: str = "long"
    momentum: float = 0.7
    volatility: float = 0.4
    volume: float = 0.6
    trend: float = 0.7


class LevelAnalysisRequest(BaseModel):
    symbol: str
    entry_price: float
    current_price: float
    momentum: float = 0.5
    volatility: float = 0.2
    volume: float = 0.5
    trend: float = 0.5


class TickOptionRequest(BaseModel):
    symbol: str
    current_price: float
    option_type: str = "binary_one_touch"
    barrier: float = 0.0
    barrier2: float = 0.0
    premium: float = 100.0
    payout_multiple: float = 2.5
    duration_seconds: int = 3600


class TickUpdateRequest(BaseModel):
    symbol: str
    price: float


class ProtectRequest(BaseModel):
    ip: str
    endpoint: str
    query: Optional[str] = None
    body: Optional[str] = None
# ============ PROFIT PER TRADE ENDPOINTS ============

@router.post("/profit-plan", tags=["Ultra Profit"])
async def compute_profit_plan(req: ProfitPlanRequest):
    """Compute ULTRA profit-per-trade plan"""
    direction = TradeDirection.SHORT if req.direction.lower() == "short" else TradeDirection.LONG
    plan = profit_per_trade_engine.compute_plan(
        symbol=req.symbol, entry_price=req.entry_price,
        capital=req.capital, risk_percent=req.risk_percent,
        leverage=req.leverage, direction=direction,
        momentum=req.momentum, volatility=req.volatility,
        volume=req.volume, trend=req.trend,
    )
    return profit_per_trade_engine._serialize(plan)


@router.get("/profit-plan", tags=["Ultra Profit"])
async def get_profit_plans(limit: int = 10):
    return profit_per_trade_engine.get_plans(limit)


@router.get("/profit-plan/latest", tags=["Ultra Profit"])
async def get_latest_profit_plan(symbol: Optional[str] = None):
    result = profit_per_trade_engine.get_latest(symbol)
    if not result:
        raise HTTPException(404, "No plans yet")
    return result


@router.get("/profit-plan/stats", tags=["Ultra Profit"])
async def get_profit_plan_stats():
    return profit_per_trade_engine.get_stats()


# ============ LEVEL ANALYSIS ENDPOINTS ============

@router.post("/levels", tags=["Ultra Profit"])
async def analyze_levels(req: LevelAnalysisRequest):
    result = ultra_profit_engine.analyze(
        symbol=req.symbol, entry_price=req.entry_price,
        current_price=req.current_price, momentum=req.momentum,
        volatility=req.volatility, volume=req.volume, trend=req.trend,
    )
    return ultra_profit_engine._serialize(result)


@router.get("/levels/stats", tags=["Ultra Profit"])
async def get_level_stats():
    return ultra_profit_engine.get_stats()


# ============ TICK OPTION ENDPOINTS ============

@router.post("/tick-option", tags=["Tick Options"])
async def create_tick_option(req: TickOptionRequest):
    """Create a tick option contract"""
    try:
        otype = OptionType(req.option_type)
    except ValueError:
        raise HTTPException(400, f"Unknown option type: {req.option_type}. Valid: {[t.value for t in OptionType]}")
    option = tick_option_engine.create_option(
        option_type=otype, symbol=req.symbol, current_price=req.current_price,
        barrier=req.barrier, barrier2=req.barrier2,
        premium=req.premium, payout_multiple=req.payout_multiple,
        duration_seconds=req.duration_seconds,
    )
    return tick_option_engine._serialize(option)


@router.post("/tick-option/update", tags=["Tick Options"])
async def update_tick(req: TickUpdateRequest):
    """Process a price tick, returns triggered options"""
    triggered = tick_option_engine.process_tick(req.symbol, req.price)
    return {
        "triggered": [tick_option_engine._serialize(t) for t in triggered],
        "active": len(tick_option_engine.get_active_options()),
        "stats": tick_option_engine.get_stats(),
    }


@router.get("/tick-option", tags=["Tick Options"])
async def get_tick_options():
    return tick_option_engine.get_active_options()


@router.get("/tick-option/stats", tags=["Tick Options"])
async def get_tick_stats():
    return tick_option_engine.get_stats()


# ============ AI GUARDIAN ENDPOINTS ============

@router.post("/guardian/protect", tags=["AI Guardian"])
async def guardian_protect(req: ProtectRequest):
    """Protect an incoming request with AI Guardian"""
    data = {"ip": req.ip, "endpoint": req.endpoint}
    if req.query:
        data["query"] = req.query
    if req.body:
        data["body"] = req.body
    result = ai_guardian.protect_request(data)
    return {
        "allowed": result["allowed"],
        "action": result["action"],
        "threat_level": result["threat_level"].value,
        "reason": result["reason"],
    }


@router.get("/guardian/status", tags=["AI Guardian"])
async def guardian_status():
    return ai_guardian.get_status()


@router.post("/guardian/block", tags=["AI Guardian"])
async def guardian_block(ip: str, duration: int = 3600, reason: str = "admin block"):
    ai_guardian.block_ip(ip, duration, reason)
    return {"blocked": True, "ip": ip, "duration": duration}


@router.post("/guardian/unblock", tags=["AI Guardian"])
async def guardian_unblock(ip: str):
    return {"unblocked": ai_guardian.unblock_ip(ip), "ip": ip}