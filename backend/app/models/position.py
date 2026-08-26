"""
ULTRA-ADVANCED Position Model - Professional Portfolio Management
Supports:
- Multi-leg positions (Entry + SL + TP + Hedges)
- Position grouping & aggregation
- Portfolio integration & weight tracking
- IATS adaptive management
- Advanced risk management
- Hedging strategies
- Scaling & averaging
- Performance analytics
- Real-time P&L updates
- Correlation-based management
- Compliance & audit logging
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

class PositionStatus(str, Enum):
    """Position Status"""
    PENDING = "PENDING"
    OPENING = "OPENING"
    PARTIALLY_OPEN = "PARTIALLY_OPEN"
    OPEN = "OPEN"
    SCALING_IN = "SCALING_IN"
    SCALING_OUT = "SCALING_OUT"
    CLOSING = "CLOSING"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED = "CLOSED"
    LIQUIDATED = "LIQUIDATED"
    SUSPENDED = "SUSPENDED"


class PositionType(str, Enum):
    """Position Type"""
    LONG = "LONG"
    SHORT = "SHORT"


class HedgeStrategy(str, Enum):
    """Hedging Strategy"""
    DIRECT = "DIRECT"  # Opposite position on same asset
    CORRELATION = "CORRELATION"  # Correlated asset hedge
    MULTI_LEG = "MULTI_LEG"  # Options or complex hedge
    NONE = "NONE"


class PositionMode(str, Enum):
    """Position Mode"""
    ONE_WAY = "ONE_WAY"  # Single position
    HEDGE_MODE = "HEDGE_MODE"  # Long + Short simultaneously
    NETTING = "NETTING"  # Net positions


# ==================== MAIN POSITION MODEL ====================

class Position(Base):
    """
    Ultra-Advanced Position Model - Professional Portfolio Management
    
    Aggregates multiple trades into strategic positions with:
    - Multi-leg position tracking (Entry + SL + TP + Hedges)
    - Portfolio integration & risk management
    - IATS adaptive features
    - Hedging strategy support
    - Real-time P&L updates
    - Performance analytics
    - Compliance & audit logging
    """
    
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint('user_id', 'position_group_id', name='uq_user_position_group'),
        CheckConstraint('open_volume >= 0', name='ck_open_volume_positive'),
        CheckConstraint('avg_entry_price > 0', name='ck_entry_price_positive'),
        CheckConstraint('risk_reward_ratio >= 0', name='ck_position_rrr_non_negative'),
        Index('idx_user_id', 'user_id'),
        Index('idx_symbol', 'symbol'),
        Index('idx_status', 'status'),
        Index('idx_portfolio_id', 'portfolio_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_closed_at', 'closed_at'),
    )
    
    # ==================== PRIMARY FIELDS ====================
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    
    # Position Identification
    position_group_id = Column(String(50), unique=True, nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    
    # ==================== POSITION DETAILS ====================
    position_type = Column(String(20), nullable=False)  # LONG, SHORT
    status = Column(String(30), default=PositionStatus.PENDING.value, nullable=False)
    position_mode = Column(String(30), default=PositionMode.ONE_WAY.value)
    
    # Entry Details (Aggregate)
    avg_entry_price = Column(Float, nullable=False)
    total_entry_volume = Column(Float, nullable=False)
    total_entry_value = Column(Float, nullable=False)
    entry_commission = Column(Float, default=0.0)
    
    # Current Status
    current_price = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    open_volume = Column(Float, nullable=False)
    closed_volume = Column(Float, default=0.0)
    
    # Fill Tracking
    fill_percent = Column(Float, default=0.0)
    partial_fills = Column(JSON, nullable=True)  # [{price, volume, time}, ...]
    
    # ==================== RISK MANAGEMENT ====================
    # Static Levels
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Dynamic Stops
    trailing_stop = Column(Float, nullable=True)
    trailing_stop_distance = Column(Float, nullable=True)
    trailing_stop_highest = Column(Float, nullable=True)  # For LONG
    trailing_stop_lowest = Column(Float, nullable=True)   # For SHORT
    trailing_stop_triggered = Column(Boolean, default=False)
    
    # Breakeven
    breakeven_price = Column(Float, nullable=True)
    breakeven_triggered = Column(Boolean, default=False)
    
    # Risk Parameters
    risk_amount = Column(Float, default=0.0)
    risk_percent = Column(Float, default=0.0)  # % of account
    reward_amount = Column(Float, default=0.0)
    risk_reward_ratio = Column(Float, default=0.0)
    
    # ==================== SCALING & AVERAGING ====================
    is_scaled = Column(Boolean, default=False)
    scale_in_count = Column(Integer, default=0)
    scale_out_count = Column(Integer, default=0)
    
    # Scale details
    scale_in_details = Column(JSON, nullable=True)  # [{price, volume, time}, ...]
    scale_out_details = Column(JSON, nullable=True)  # [{price, volume, time}, ...]
    
    # Averaging
    avg_exit_price = Column(Float, nullable=True)  # Weighted avg for partial closes
    
    # ==================== HEDGING ====================
    is_hedged = Column(Boolean, default=False)
    hedge_strategy = Column(String(30), default=HedgeStrategy.NONE.value)
    hedge_position_id = Column(Integer, ForeignKey('positions.id'), nullable=True)  # Reference to hedge
    hedge_ratio = Column(Float, nullable=True)  # % of position hedged
    hedge_details = Column(JSON, nullable=True)  # {"type": "inverse", "instrument": "..."
    
    # ==================== MULTI-LEG POSITIONS ====================
    is_multi_leg = Column(Boolean, default=False)
    leg_trades = Column(JSON, nullable=True)  # List of trade IDs that make up position
    leg_count = Column(Integer, default=1)
    
    # ==================== P&L TRACKING ====================
    # Unrealized (for open positions)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)
    unrealized_pnl_value = Column(Float, default=0.0)  # In account currency
    
    # Realized (for closed portions)
    realized_pnl = Column(Float, default=0.0)
    realized_pnl_percent = Column(Float, default=0.0)
    
    # Total
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    total_pnl_after_commission = Column(Float, default=0.0)
    
    # Extreme Metrics
    max_profit = Column(Float, default=0.0)
    max_profit_percent = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_percent = Column(Float, default=0.0)
    
    # ==================== DURATION & TIMING ====================
    opened_at = Column(DateTime, server_default=func.now(), nullable=False)
    closed_at = Column(DateTime, nullable=True)
    open_duration_seconds = Column(Integer, nullable=True)
    
    # Time-based metrics
    is_intraday = Column(Boolean, default=False)
    open_hour = Column(Integer, nullable=True)
    close_hour = Column(Integer, nullable=True)
    
    # ==================== BOT & STRATEGY ====================
    bot_id = Column(String(100), nullable=True)
    bot_name = Column(String(255), nullable=True)
    bot_strategy = Column(String(50), nullable=True)
    is_bot_managed = Column(Boolean, default=False)
    
    # Strategy adaptive features
    strategy_settings = Column(JSON, nullable=True)
    strategy_signals = Column(JSON, nullable=True)
    
    # ==================== PORTFOLIO INTEGRATION ====================
    portfolio_weight = Column(Float, nullable=True)  # % of portfolio
    portfolio_risk = Column(Float, default=0.0)  # Risk in portfolio
    asset_allocation = Column(String(50), nullable=True)  # Which allocation bucket
    
    # Correlation tracking
    correlated_positions = Column(JSON, nullable=True)  # [pos_id1, pos_id2, ...]
    correlation_coefficient = Column(Float, nullable=True)  # -1 to 1
    
    # ==================== IATS (INTELLIGENT ADAPTIVE TRADING SYSTEM) ====================
    # AI Scoring
    ai_confidence_score = Column(Float, default=0.0)  # 0-1.0
    ai_signal_strength = Column(Float, default=0.0)  # Signal power
    ai_recommendation = Column(String(50), nullable=True)  # HOLD, SCALE_IN, SCALE_OUT, CLOSE
    
    # Market Context at Entry
    market_regime_at_entry = Column(String(50), nullable=True)  # TRENDING, RANGING, etc.
    volatility_at_entry = Column(Float, nullable=True)
    volume_at_entry = Column(Float, nullable=True)
    
    # IATS Adaptations
    iats_adaptations = Column(JSON, nullable=True)  # AI modifications made
    iats_ensemble_signal = Column(Float, nullable=True)  # Combined signal 0-1
    
    # Performance vs Expected
    expected_win_rate = Column(Float, nullable=True)
    expected_max_drawdown = Column(Float, nullable=True)
    
    # ==================== LEVERAGE & MARGIN ====================
    is_margin_position = Column(Boolean, default=False)
    is_futures_position = Column(Boolean, default=False)
    leverage = Column(Integer, default=1)
    margin_used = Column(Float, default=0.0)
    margin_level = Column(Float, nullable=True)
    
    # ==================== TRADE REFERENCES ====================
    trade_count = Column(Integer, default=1)  # Number of trades in position
    entry_trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    exit_trade_ids = Column(JSON, nullable=True)  # List of exit trade IDs
    
    # ==================== COMPLIANCE & AUDIT ====================
    is_compliant = Column(Boolean, default=True)
    compliance_notes = Column(Text, nullable=True)
    
    # Audit trail
    audit_trail = Column(JSON, nullable=True)
    created_by = Column(String(100), nullable=True)
    modified_by = Column(String(100), nullable=True)
    
    # ==================== METADATA ====================
    exchange = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["important", "test", etc.]
    custom_data = Column(JSON, nullable=True)
    
    # ==================== TIMESTAMPS ====================
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ==================== METHODS ====================
    
    def is_open(self) -> bool:
        """Check if position is still open"""
        return self.status in [PositionStatus.OPEN.value, 
                              PositionStatus.PARTIALLY_CLOSED.value,
                              PositionStatus.SCALING_IN.value,
                              PositionStatus.SCALING_OUT.value]
    
    def is_fully_closed(self) -> bool:
        """Check if position is fully closed"""
        return self.status == PositionStatus.CLOSED.value
    
    def is_breakeven(self) -> bool:
        """Check if position is at breakeven"""
        return abs(self.unrealized_pnl) < 0.01  # Within $0.01
    
    def is_profitable(self) -> bool:
        """Check if position is profitable"""
        pnl = self.total_pnl if self.is_fully_closed() else self.unrealized_pnl
        return pnl > 0
    
    def is_losing(self) -> bool:
        """Check if position is losing"""
        pnl = self.total_pnl if self.is_fully_closed() else self.unrealized_pnl
        return pnl < 0
    
    def get_open_quantity(self) -> float:
        """Get remaining open quantity"""
        return self.total_entry_volume - self.closed_volume
    
    def get_close_percent(self) -> float:
        """Get percentage closed (0-100)"""
        if self.total_entry_volume == 0:
            return 0.0
        return (self.closed_volume / self.total_entry_volume) * 100
    
    def update_unrealized_pnl(self, current_price: float) -> None:
        """Update unrealized P&L for open positions"""
        if not self.is_open():
            return
        
        self.current_price = current_price
        self.current_value = current_price * self.open_volume
        
        # Calculate P&L based on position type
        if self.position_type == PositionType.LONG.value:
            pnl = (current_price - self.avg_entry_price) * self.open_volume
        else:  # SHORT
            pnl = (self.avg_entry_price - current_price) * self.open_volume
        
        pnl_after_commission = pnl - self.entry_commission
        self.unrealized_pnl = pnl_after_commission
        
        if self.total_entry_value > 0:
            self.unrealized_pnl_percent = (pnl_after_commission / self.total_entry_value) * 100
        
        # Update max drawdown
        if pnl < self.max_drawdown:
            self.max_drawdown = pnl
            if self.total_entry_value > 0:
                self.max_drawdown_percent = (pnl / self.total_entry_value) * 100
        
        # Update max profit
        if pnl > self.max_profit:
            self.max_profit = pnl
            if self.total_entry_value > 0:
                self.max_profit_percent = (pnl / self.total_entry_value) * 100
    
    def update_trailing_stop(self, current_price: float) -> bool:
        """Update trailing stop, return True if triggered"""
        if self.trailing_stop is None or self.trailing_stop_distance is None:
            return False
        
        if self.position_type == PositionType.LONG.value:
            # For long, trailing stop is below price
            if current_price > (self.trailing_stop_highest or current_price):
                self.trailing_stop_highest = current_price
                self.trailing_stop = current_price - self.trailing_stop_distance
            
            if current_price <= self.trailing_stop:
                self.trailing_stop_triggered = True
                return True
        
        else:  # SHORT
            # For short, trailing stop is above price
            if current_price < (self.trailing_stop_lowest or current_price):
                self.trailing_stop_lowest = current_price
                self.trailing_stop = current_price + self.trailing_stop_distance
            
            if current_price >= self.trailing_stop:
                self.trailing_stop_triggered = True
                return True
        
        return False
    
    def get_position_summary(self) -> Dict:
        """Get comprehensive position summary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "type": self.position_type,
            "status": self.status,
            "open_volume": self.open_volume,
            "avg_entry_price": self.avg_entry_price,
            "current_price": self.current_price,
            "pnl": self.unrealized_pnl if self.is_open() else self.total_pnl,
            "pnl_percent": self.unrealized_pnl_percent if self.is_open() else self.total_pnl_percent,
            "portfolio_weight": self.portfolio_weight,
            "ai_confidence": self.ai_confidence_score,
            "is_hedged": self.is_hedged,
            "duration": self.open_duration_seconds,
        }
    
    def scale_in(self, price: float, volume: float) -> None:
        """Record a scale-in"""
        self.is_scaled = True
        self.scale_in_count += 1
        self.total_entry_volume += volume
        self.open_volume += volume
        
        # Update average entry price
        old_value = self.avg_entry_price * (self.total_entry_volume - volume)
        new_value = old_value + (price * volume)
        self.avg_entry_price = new_value / self.total_entry_volume
        
        # Record in history
        if self.scale_in_details is None:
            self.scale_in_details = []
        self.scale_in_details.append({
            "price": price,
            "volume": volume,
            "time": datetime.utcnow().isoformat()
        })
    
    def scale_out(self, price: float, volume: float) -> None:
        """Record a scale-out"""
        self.is_scaled = True
        self.scale_out_count += 1
        self.closed_volume += volume
        self.open_volume -= volume
        
        # Update average exit price
        if self.avg_exit_price is None:
            self.avg_exit_price = price
        else:
            old_value = self.avg_exit_price * (self.closed_volume - volume)
            new_value = old_value + (price * volume)
            self.avg_exit_price = new_value / self.closed_volume
        
        # Record in history
        if self.scale_out_details is None:
            self.scale_out_details = []
        self.scale_out_details.append({
            "price": price,
            "volume": volume,
            "time": datetime.utcnow().isoformat()
        })
    
    def __repr__(self) -> str:
        return (f"<Position id={self.id} symbol={self.symbol} type={self.position_type} "
                f"status={self.status} pnl={self.unrealized_pnl or self.total_pnl}>")
    
    def __str__(self) -> str:
        return (f"{self.symbol} {self.position_type} "
                f"@ {self.avg_entry_price} (Vol: {self.open_volume})")
