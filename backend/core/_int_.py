# ============================================
# ESH.TRADE - CORE PACKAGE (FULLY DEBUGGED)
# ============================================
# backend/app/core/__init__.py

"""
ESH.TRADE Core Package - Ultra Advanced Trading Engine
All core modules for trading, risk management, AI, and analysis
"""

from .adaptive_engine import AdaptiveEngine, MarketRegime, LearningState
from .risk_engine import RiskEngine, RiskLevel, StopReason, RiskState
from .bot_state_manager import BotStateManager, BotState, StopTrigger, RecoveryPhase, BotStats
from .trading_engine import TradingEngine, OrderType, OrderSide, OrderStatus, ExecutionResult
from .indicator_engine import IndicatorEngine, IndicatorType, SignalType, IndicatorResult
from .candle_analyzer import CandleAnalyzer, CandlePatternType, CandleStrength, PatternResult
from .ai_overseer import AIOverseer, BotHealth, AdjustmentAction, AdjustmentType
from .adaptive_controller import AdaptiveController, ParameterAdjustment, AdjustmentPriority

__all__ = [
    "AdaptiveEngine",
    "MarketRegime",
    "LearningState",
    "RiskEngine",
    "RiskLevel",
    "StopReason",
    "RiskState",
    "BotStateManager",
    "BotState",
    "StopTrigger",
    "RecoveryPhase",
    "BotStats",
    "TradingEngine",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "ExecutionResult",
    "IndicatorEngine",
    "IndicatorType",
    "SignalType",
    "IndicatorResult",
    "CandleAnalyzer",
    "CandlePatternType",
    "CandleStrength",
    "PatternResult",
    "AIOverseer",
    "BotHealth",
    "AdjustmentAction",
    "AdjustmentType",
    "AdaptiveController",
    "ParameterAdjustment",
    "AdjustmentPriority"
]