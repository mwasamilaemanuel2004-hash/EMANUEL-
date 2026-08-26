"""
ULTRA-ADVANCED Trade Model - Enterprise-Grade Trading System
Supports:
- All 11 Trading Bots (5 Forex, 5 Crypto, 1 Stock)
- 3 Asset Classes (Forex, Crypto, Stock)
- 5+ Exchanges (Binance, Bybit, KuCoin, OKX, Coinbase, MT5)
- Advanced Order Types (Market, Limit, OCO, Iceberg, Trailing, Bracket)
- Leverage & Margin Trading
- Position Grouping & Portfolio Management
- IATS Integration (Intelligent Adaptive Trading System)
- Risk Management & Portfolio-level Tracking
- Performance Analytics & Metrics
- Partial Close & Scale In/Out
- Slippage & Execution Analysis
- Bot Performance Scoring
- Compliance & Audit Logging
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean,
    JSON, Text, UniqueConstraint, CheckConstraint, Index, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


# ==================== ENUMS ====================

class AssetClass(str, Enum):
    """Asset Class Type"""
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    STOCK = "STOCK"


class TradeStatus(str, Enum):
    """Trade Status"""
    PENDING = "PENDING"
    ENTRY_PENDING = "ENTRY_PENDING"
    ENTRY_PARTIAL = "ENTRY_PARTIAL"
    ENTRY_FILLED = "ENTRY_FILLED"
    OPEN = "OPEN"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    LIQUIDATED = "LIQUIDATED"
    SUSPENDED = "SUSPENDED"


class TradeType(str, Enum):
    """Trade Direction"""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(str, Enum):
    """Order Type"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    OCO = "OCO"  # One Cancels Other
    ICEBERG = "ICEBERG"
    BRACKET = "BRACKET"  # Entry + SL + TP


class ExitReason(str, Enum):
    """Exit Reason"""
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    MANUAL = "MANUAL"
    LIQUIDATION = "LIQUIDATION"
    MARGIN_CALL = "MARGIN_CALL"
    FORCE_CLOSE = "FORCE_CLOSE"
    BOT_SIGNAL = "BOT_SIGNAL"
    RISK_LIMIT_HIT = "RISK_LIMIT_HIT"
    MARKET_CLOSE = "MARKET_CLOSE"
    TIMEOUT = "TIMEOUT"


class BotStrategy(str, Enum):
    """Bot Strategy Type"""
    # Forex Bots
    TREND_FOLLOWER = "TREND_FOLLOWER"
    SCALPER_FOREX = "SCALPER_FOREX"
    SMART_MONEY = "SMART_MONEY"
    BREAKOUT = "BREAKOUT"
    NEWS_TRADER = "NEWS_TRADER"
    
    # Crypto Bots
    ARBITRAGE = "ARBITRAGE"
    DCA = "DCA"
    GRID = "GRID"
    WHALE_TRACKER = "WHALE_TRACKER"
    SCALPER_CRYPTO = "SCALPER_CRYPTO"
    
    # Stock Bot
    AI_STOCK_ANALYZER = "AI_STOCK_ANALYZER"
    
    # Manual
    MANUAL = "MANUAL"


class ExecutionStatus(str, Enum):
    """Execution Status"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


# ==================== MAIN TRADE MODEL ====================

class Trade(Base):
    """
    Ultra-Advanced Trade Model for ESMH.TRADE Platform
    
    Tracks complete trade lifecycle from entry signal to final exit
    with comprehensive metrics, risk analysis, and bot performance scoring.
    
    Supports:
    - Multiple asset classes (Forex, Crypto, Stock)
    - Multiple bot strategies
    - Advanced order types
    - Partial closes & scaling
    - Leverage & margin tracking
    - Portfolio integration
    - IATS compatibility
    """
    
    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint('user_id', 'order_id', name='uq_user_order_id'),
        CheckConstraint('entry_quantity > 0', name='ck_entry_quantity_positive'),
        CheckConstraint('risk_reward_ratio >= 0', name='ck_rrr_non_negative'),
    )
    
    # ==================== PRIMARY FIELDS ====================
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True)  # Optional
    
    # Order Identification
    order_id = Column(String(100), nullable=False, index=True)  # Exchange order ID
    exchange_order_id = Column(String(100), nullable=True)  # Specific exchange ID
    internal_trade_id = Column(String(50), unique=True, nullable=False)  # UUID for IATS
    
    # ==================== INSTRUMENT DETAILS ====================
    asset_class = Column(String(20), nullable=False, index=True)  # FOREX, CRYPTO, STOCK
    symbol = Column(String(50), nullable=False, index=True)  # EURUSD, BTCUSD, AAPL
    base_asset = Column(String(20), nullable=True)  # BTC, EUR, AAPL
    quote_asset = Column(String(20), nullable=True)  # USD, USDT
    
    exchange = Column(String(50), nullable=False)  # Binance, MT5, Bybit, etc.
    market_type = Column(String(50), nullable=True)  # SPOT, FUTURES, MARGIN
    
    # ==================== TRADE DIRECTION & STATUS ====================
    trade_type = Column(String(20), nullable=False)  # LONG, SHORT
    status = Column(String(30), default=TradeStatus.PENDING.value, nullable=False)
    
    entry_order_status = Column(String(30), default=ExecutionStatus.PENDING.value)
    exit_order_status = Column(String(30), nullable=True)
    
    # ==================== ENTRY DETAILS ====================
    entry_price = Column(Float, nullable=False)
    entry_quantity = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    entry_commission = Column(Float, default=0.0)
    entry_slippage = Column(Float, default=0.0)
    
    # Entry fills (for partial orders)
    entry_fill_price = Column(Float, nullable=True)  # Weighted avg if partial
    entry_filled_quantity = Column(Float, default=0.0)
    entry_fill_percent = Column(Float, default=0.0)
    
    order_type = Column(String(30), default=OrderType.MARKET.value)
    
    # ==================== EXIT DETAILS ====================
    exit_price = Column(Float, nullable=True)
    exit_quantity = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    exit_commission = Column(Float, default=0.0)
    exit_slippage = Column(Float, default=0.0)
    
    # Exit fills (for partial closes)
    exit_filled_quantity = Column(Float, default=0.0)
    exit_fill_percent = Column(Float, default=0.0)
    
    exit_reason = Column(String(50), nullable=True)
    
    # Multiple exits tracking
    total_closes = Column(Integer, default=0)
    partial_close_details = Column(JSON, nullable=True)  # [{price, qty, time}, ...]
    
    # ==================== RISK MANAGEMENT ====================
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    trailing_stop = Column(Float, nullable=True)
    trailing_stop_distance = Column(Float, nullable=True)
    trailing_stop_triggered = Column(Boolean, default=False)
    
    # OCO Orders
    is_oco_order = Column(Boolean, default=False)
    oco_sl_order_id = Column(String(100), nullable=True)
    oco_tp_order_id = Column(String(100), nullable=True)
    
    # Risk Parameters
    risk_amount = Column(Float, default=0.0)
    risk_percent = Column(Float, default=0.0)  # % of account
    reward_amount = Column(Float, default=0.0)
    risk_reward_ratio = Column(Float, default=0.0)
    
    # ==================== LEVERAGE & MARGIN ====================
    is_margin_trade = Column(Boolean, default=False)
    is_futures_trade = Column(Boolean, default=False)
    leverage = Column(Integer, default=1)  # 1x to 125x
    margin_used = Column(Float, default=0.0)
    margin_level = Column(Float, nullable=True)  # For margin calls
    
    # ==================== PROFIT & LOSS ====================
    # Entry value
    entry_value = Column(Float, nullable=True)  # entry_price * entry_quantity
    
    # Exit value
    exit_value = Column(Float, nullable=True)
    
    # Current metrics (for open trades)
    current_price = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)
    
    # Final metrics (for closed trades)
    profit_loss = Column(Float, nullable=True)
    profit_loss_percent = Column(Float, nullable=True)
    profit_loss_after_commission = Column(Float, nullable=True)
    total_commission = Column(Float, default=0.0)
    
    # Maximum metrics
    max_profit = Column(Float, default=0.0)
    max_profit_percent = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_percent = Column(Float, default=0.0)
    
    # ==================== TRADE DURATION & TIMING ====================
    open_duration_seconds = Column(Integer, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Intraday tracking
    is_daytrader = Column(Boolean, default=False)
    open_hour = Column(Integer, nullable=True)  # Hour of day (0-23)
    close_hour = Column(Integer, nullable=True)
    
    # ==================== BOT & STRATEGY DETAILS ====================
    bot_id = Column(String(100), nullable=True, index=True)
    bot_name = Column(String(255), nullable=True)
    bot_version = Column(String(50), nullable=True)
    bot_strategy = Column(String(50), nullable=True)  # Enum name
    is_automated = Column(Boolean, default=False)
    is_bot_optimized = Column(Boolean, default=False)  # Used optimization
    
    # Strategy metadata
    strategy_settings = Column(JSON, nullable=True)  # {period: 14, threshold: 2, ...}
    bot_signals = Column(JSON, nullable=True)  # [{"type": "MA_CROSS", "strength": 0.8}, ...]
    signal_confirmation = Column(JSON, nullable=True)  # Confirmations from other indicators
    
    # ==================== PRICE & MARKET DATA ====================
    entry_candle = Column(JSON, nullable=True)  # {open, high, low, close, volume}
    exit_candle = Column(JSON, nullable=True)
    
    entry_market_condition = Column(String(50), nullable=True)  # TRENDING, RANGING, CHOPPY
    entry_volatility = Column(Float, nullable=True)  # ATR or Std Dev
    entry_volume = Column(Float, nullable=True)
    
    # ==================== CORRELATION & HEDGING ====================
    correlated_trades = Column(JSON, nullable=True)  # [trade_id1, trade_id2, ...]
    hedge_trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    is_hedge = Column(Boolean, default=False)
    
    # ==================== SCALING & POSITION MANAGEMENT ====================
    is_scaled_in = Column(Boolean, default=False)
    scale_in_details = Column(JSON, nullable=True)  # [{price, qty, time}, ...]
    
    is_scaled_out = Column(Boolean, default=False)
    scale_out_details = Column(JSON, nullable=True)  # [{price, qty, time}, ...]
    
    position_group_id = Column(String(50), nullable=True)  # Group multiple trades
    is_position_group = Column(Boolean, default=False)
    
    # ==================== PORTFOLIO & RISK TRACKING ====================
    portfolio_weight = Column(Float, nullable=True)  # % of portfolio
    account_risk = Column(Float, default=0.0)  # Risk in account currency
    account_reward = Column(Float, default=0.0)
    
    # ==================== EXECUTION QUALITY ====================
    execution_quality_score = Column(Float, default=0.0)  # 0-100
    
    # Slippage
    slippage_pips = Column(Float, default=0.0)
    slippage_percent = Column(Float, default=0.0)
    
    # Fill time
    time_to_fill = Column(Integer, nullable=True)  # Milliseconds
    
    # Rejections/Errors
    rejection_reason = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # ==================== IATS (INTELLIGENT ADAPTIVE TRADING SYSTEM) ====================
    # AI Overseer scoring
    ai_confidence_score = Column(Float, default=0.0)  # 0-1.0
    ai_signal_strength = Column(Float, default=0.0)  # 0-1.0
    ai_recommendation = Column(String(50), nullable=True)  # STRONG_BUY, BUY, HOLD, etc.
    
    # Bot performance vs expected
    bot_performance_percentile = Column(Float, nullable=True)  # vs historical
    expected_win_rate = Column(Float, nullable=True)  # Based on strategy
    
    # Market regime at entry
    market_regime = Column(String(50), nullable=True)  # TRENDING, RANGING, VOLATILE, CHOPPY
    regime_confidence = Column(Float, nullable=True)
    
    # IATS adaptations
    iats_adaptations = Column(JSON, nullable=True)  # Modifications made by AI
    iats_ensemble_signal = Column(Float, nullable=True)  # Combined signal 0-1
    
    # ==================== COMPLIANCE & AUDIT ====================
    is_compliant = Column(Boolean, default=True)
    compliance_notes = Column(Text, nullable=True)
    verified_by = Column(String(100), nullable=True)  # Compliance officer
    
    # Audit trail
    audit_trail = Column(JSON, nullable=True)  # Log all changes
    created_by = Column(String(100), nullable=True)  # User or Bot
    modified_by = Column(String(100), nullable=True)
    
    # ==================== TIMESTAMPS ====================
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    executed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ==================== METADATA & NOTES ====================
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["scalp", "breakout", "news", "test"]
    custom_data = Column(JSON, nullable=True)  # For bot-specific data
    
    # ==================== METHODS ====================
    
    def is_open(self) -> bool:
        """Check if trade is still open"""
        return self.status in [TradeStatus.OPEN.value, TradeStatus.PARTIALLY_CLOSED.value, 
                              TradeStatus.ENTRY_PARTIAL.value]
    
    def is_closed(self) -> bool:
        """Check if trade is fully closed"""
        return self.status == TradeStatus.CLOSED.value
    
    def is_profitable(self) -> bool:
        """Check if trade made profit"""
        pnl = self.profit_loss if self.profit_loss is not None else self.unrealized_pnl
        return pnl > 0
    
    def calculate_rr_ratio(self, entry: float, sl: float, tp: float) -> float:
        """Calculate risk-reward ratio"""
        if sl == 0 or entry == sl:
            return 0.0
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        return reward / risk if risk > 0 else 0.0
    
    def update_unrealized_pnl(self, current_price: float) -> None:
        """Update unrealized P&L for open trades"""
        if not self.is_open():
            return
        
        self.current_price = current_price
        current_value = current_price * self.entry_filled_quantity
        self.current_value = current_value
        
        if self.trade_type == TradeType.LONG.value:
            pnl = (current_price - self.entry_fill_price) * self.entry_filled_quantity
        else:
            pnl = (self.entry_fill_price - current_price) * self.entry_filled_quantity
        
        pnl_after_commission = pnl - (self.entry_commission + self.exit_commission)
        self.unrealized_pnl = pnl_after_commission
        
        if self.entry_value and self.entry_value > 0:
            self.unrealized_pnl_percent = (pnl_after_commission / self.entry_value) * 100
    
    def get_trade_summary(self) -> Dict:
        """Get comprehensive trade summary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "type": self.trade_type,
            "status": self.status,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "pnl": self.profit_loss or self.unrealized_pnl,
            "pnl_percent": self.profit_loss_percent or self.unrealized_pnl_percent,
            "bot_strategy": self.bot_strategy,
            "duration": self.open_duration_seconds,
            "rr_ratio": self.risk_reward_ratio,
            "ai_confidence": self.ai_confidence_score,
        }
    
    def __repr__(self) -> str:
        return (f"<Trade id={self.id} {self.symbol} {self.trade_type} "
                f"status={self.status} pnl={self.profit_loss or self.unrealized_pnl}>")
    
    def __str__(self) -> str:
        return (f"{self.symbol} {self.trade_type} @ {self.entry_price} "
                f"({self.bot_strategy or 'Manual'})")
