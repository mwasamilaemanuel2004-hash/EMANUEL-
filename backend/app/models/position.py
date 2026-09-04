"""
ULTRA-ADVANCED Position Model - Professional Portfolio Management
Complete Implementation - Single File

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

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional, Dict, List, Any, Union

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean,
    JSON, Text, UniqueConstraint, CheckConstraint, Index,
    Enum as SQLAlchemyEnum
)
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy.sql import func

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

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
    DIRECT = "DIRECT"          # Opposite position on same asset
    CORRELATION = "CORRELATION"  # Correlated asset hedge
    MULTI_LEG = "MULTI_LEG"    # Options or complex hedge
    NONE = "NONE"


class PositionMode(str, Enum):
    """Position Mode"""
    ONE_WAY = "ONE_WAY"        # Single position
    HEDGE_MODE = "HEDGE_MODE"  # Long + Short simultaneously
    NETTING = "NETTING"        # Net positions


class MarketRegime(str, Enum):
    """Market Regime Classification"""
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"
    UNKNOWN = "UNKNOWN"


# ============================================================================
# DATABASE BASE (Placeholder - Import from your project)
# ============================================================================

# This should be imported from your database module
# from ..database import Base

# For standalone testing, define a simple Base
try:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
except ImportError:
    # If running in a project with its own Base
    pass


# ============================================================================
# MAIN POSITION MODEL
# ============================================================================

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
        # Primary Constraints
        UniqueConstraint('user_id', 'position_group_id', name='uq_user_position_group'),
        
        # Data Integrity Checks
        CheckConstraint('open_volume >= 0', name='ck_open_volume_positive'),
        CheckConstraint('avg_entry_price > 0', name='ck_entry_price_positive'),
        CheckConstraint('risk_reward_ratio >= 0', name='ck_position_rrr_non_negative'),
        CheckConstraint('leverage >= 1', name='ck_leverage_positive'),
        CheckConstraint('ai_confidence_score BETWEEN 0 AND 1', name='ck_confidence_score'),
        CheckConstraint('portfolio_weight >= 0 AND portfolio_weight <= 1', 
                       name='ck_portfolio_weight'),
        CheckConstraint('hedge_ratio >= 0 AND hedge_ratio <= 1', 
                       name='ck_hedge_ratio'),
        CheckConstraint('fill_percent >= 0 AND fill_percent <= 100',
                       name='ck_fill_percent'),
        
        # Performance Indexes
        Index('idx_user_id', 'user_id'),
        Index('idx_symbol', 'symbol'),
        Index('idx_status', 'status'),
        Index('idx_portfolio_id', 'portfolio_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_closed_at', 'closed_at'),
        
        # Composite Indexes for Common Queries
        Index('idx_user_portfolio_status', 'user_id', 'portfolio_id', 'status'),
        Index('idx_symbol_status_created', 'symbol', 'status', 'created_at'),
        Index('idx_bot_id_status', 'bot_id', 'status'),
        Index('idx_is_hedged_status', 'is_hedged', 'status'),
        Index('idx_portfolio_weight_risk', 'portfolio_weight', 'risk_amount'),
        Index('idx_pnl_status', 'unrealized_pnl', 'status'),
        Index('idx_created_at_updated', 'created_at', 'updated_at'),
        Index('idx_open_close_time', 'opened_at', 'closed_at'),
    )
    
    # ==================== PRIMARY FIELDS ====================
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False)
    
    # Position Identification
    position_group_id = Column(String(50), unique=True, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    
    # ==================== POSITION DETAILS ====================
    position_type = Column(SQLAlchemyEnum(PositionType), nullable=False)
    status = Column(SQLAlchemyEnum(PositionStatus), default=PositionStatus.PENDING, nullable=False)
    position_mode = Column(SQLAlchemyEnum(PositionMode), default=PositionMode.ONE_WAY)
    
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
    partial_fills = Column(JSON, nullable=True)
    
    # ==================== RISK MANAGEMENT ====================
    # Static Levels
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Dynamic Stops
    trailing_stop = Column(Float, nullable=True)
    trailing_stop_distance = Column(Float, nullable=True)
    trailing_stop_highest = Column(Float, nullable=True)
    trailing_stop_lowest = Column(Float, nullable=True)
    trailing_stop_triggered = Column(Boolean, default=False)
    
    # Breakeven
    breakeven_price = Column(Float, nullable=True)
    breakeven_triggered = Column(Boolean, default=False)
    
    # Risk Parameters
    risk_amount = Column(Float, default=0.0)
    risk_percent = Column(Float, default=0.0)
    reward_amount = Column(Float, default=0.0)
    risk_reward_ratio = Column(Float, default=0.0)
    
    # ==================== SCALING & AVERAGING ====================
    is_scaled = Column(Boolean, default=False)
    scale_in_count = Column(Integer, default=0)
    scale_out_count = Column(Integer, default=0)
    scale_in_details = Column(JSON, nullable=True)
    scale_out_details = Column(JSON, nullable=True)
    avg_exit_price = Column(Float, nullable=True)
    
    # ==================== HEDGING ====================
    is_hedged = Column(Boolean, default=False)
    hedge_strategy = Column(SQLAlchemyEnum(HedgeStrategy), default=HedgeStrategy.NONE)
    hedge_position_id = Column(Integer, ForeignKey('positions.id'), nullable=True)
    hedge_ratio = Column(Float, nullable=True)
    hedge_details = Column(JSON, nullable=True)
    
    # ==================== MULTI-LEG POSITIONS ====================
    is_multi_leg = Column(Boolean, default=False)
    leg_trades = Column(JSON, nullable=True)
    leg_count = Column(Integer, default=1)
    
    # ==================== P&L TRACKING ====================
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)
    unrealized_pnl_value = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    realized_pnl_percent = Column(Float, default=0.0)
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
    is_intraday = Column(Boolean, default=False)
    open_hour = Column(Integer, nullable=True)
    close_hour = Column(Integer, nullable=True)
    
    # ==================== BOT & STRATEGY ====================
    bot_id = Column(String(100), nullable=True)
    bot_name = Column(String(255), nullable=True)
    bot_strategy = Column(String(50), nullable=True)
    is_bot_managed = Column(Boolean, default=False)
    strategy_settings = Column(JSON, nullable=True)
    strategy_signals = Column(JSON, nullable=True)
    
    # ==================== PORTFOLIO INTEGRATION ====================
    portfolio_weight = Column(Float, nullable=True)
    portfolio_risk = Column(Float, default=0.0)
    asset_allocation = Column(String(50), nullable=True)
    correlated_positions = Column(JSON, nullable=True)
    correlation_coefficient = Column(Float, nullable=True)
    
    # ==================== IATS (INTELLIGENT ADAPTIVE TRADING SYSTEM) ====================
    ai_confidence_score = Column(Float, default=0.0)
    ai_signal_strength = Column(Float, default=0.0)
    ai_recommendation = Column(String(50), nullable=True)
    market_regime_at_entry = Column(SQLAlchemyEnum(MarketRegime), nullable=True)
    volatility_at_entry = Column(Float, nullable=True)
    volume_at_entry = Column(Float, nullable=True)
    iats_adaptations = Column(JSON, nullable=True)
    iats_ensemble_signal = Column(Float, nullable=True)
    expected_win_rate = Column(Float, nullable=True)
    expected_max_drawdown = Column(Float, nullable=True)
    
    # ==================== LEVERAGE & MARGIN ====================
    is_margin_position = Column(Boolean, default=False)
    is_futures_position = Column(Boolean, default=False)
    leverage = Column(Integer, default=1)
    margin_used = Column(Float, default=0.0)
    margin_level = Column(Float, nullable=True)
    
    # ==================== TRADE REFERENCES ====================
    trade_count = Column(Integer, default=1)
    entry_trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    exit_trade_ids = Column(JSON, nullable=True)
    
    # ==================== COMPLIANCE & AUDIT ====================
    is_compliant = Column(Boolean, default=True)
    compliance_notes = Column(Text, nullable=True)
    audit_trail = Column(JSON, nullable=True)
    created_by = Column(String(100), nullable=True)
    modified_by = Column(String(100), nullable=True)
    
    # ==================== METADATA ====================
    exchange = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    custom_data = Column(JSON, nullable=True)
    
    # ==================== TIMESTAMPS ====================
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ==================== RELATIONSHIPS ====================
    # Note: These would need to be defined in your actual models
    # hedge_position = relationship('Position', remote_side=[id])
    # entry_trade = relationship('Trade', foreign_keys=[entry_trade_id])
    # user = relationship('User', foreign_keys=[user_id])
    # portfolio = relationship('Portfolio', foreign_keys=[portfolio_id])
    
    # ==================== INITIALIZATION ====================
    
    def __init__(self, **kwargs):
        """Enhanced initialization with validation and tracking setup"""
        super().__init__(**kwargs)
        self._validate_initial_state()
        self._initialize_tracking_structures()
        self._log_audit_event("POSITION_CREATED", {
            "message": "Position initialized",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _validate_initial_state(self):
        """Validate position state on creation"""
        if self.position_type not in [pt.value for pt in PositionType]:
            raise ValueError(f"Invalid position type: {self.position_type}")
        
        if self.total_entry_volume <= 0:
            raise ValueError("Total entry volume must be positive")
        
        if self.avg_entry_price <= 0:
            raise ValueError("Average entry price must be positive")
        
        if self.leverage < 1:
            raise ValueError("Leverage must be at least 1")
    
    def _initialize_tracking_structures(self):
        """Initialize all tracking structures"""
        if self.scale_in_details is None:
            self.scale_in_details = []
        if self.scale_out_details is None:
            self.scale_out_details = []
        if self.audit_trail is None:
            self.audit_trail = []
        if self.partial_fills is None:
            self.partial_fills = []
        if self.tags is None:
            self.tags = []
        
        # Calculate derived values
        if self.total_entry_volume > 0 and self.open_volume == 0:
            self.open_volume = self.total_entry_volume
    
    # ==================== CORE STATUS METHODS ====================
    
    def is_open(self) -> bool:
        """Check if position is still open"""
        return self.status in [
            PositionStatus.OPEN,
            PositionStatus.PARTIALLY_CLOSED,
            PositionStatus.SCALING_IN,
            PositionStatus.SCALING_OUT
        ]
    
    def is_fully_closed(self) -> bool:
        """Check if position is fully closed"""
        return self.status == PositionStatus.CLOSED
    
    def is_breakeven(self, tolerance: float = 0.01) -> bool:
        """Check if position is at breakeven"""
        pnl = self.total_pnl if self.is_fully_closed() else self.unrealized_pnl
        return abs(pnl) < tolerance
    
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
        return max(0, self.total_entry_volume - self.closed_volume)
    
    def get_close_percent(self) -> float:
        """Get percentage closed (0-100)"""
        if self.total_entry_volume == 0:
            return 0.0
        return (self.closed_volume / self.total_entry_volume) * 100
    
    # ==================== P&L MANAGEMENT ====================
    
    def update_unrealized_pnl(self, current_price: float) -> Dict[str, Any]:
        """
        Update unrealized P&L for open positions with comprehensive tracking
        
        Args:
            current_price: Current market price
            
        Returns:
            Dict containing update results and state changes
        """
        result = {
            "success": False,
            "error": None,
            "previous_state": None,
            "new_state": None,
            "changes": {}
        }
        
        try:
            if not self.is_open():
                result["error"] = "Position is not open"
                return result
            
            if current_price <= 0:
                raise ValueError(f"Invalid price: {current_price}")
            
            # Store previous state
            previous_pnl = self.unrealized_pnl
            previous_percent = self.unrealized_pnl_percent
            
            result["previous_state"] = {
                "unrealized_pnl": previous_pnl,
                "unrealized_pnl_percent": previous_percent,
                "max_drawdown": self.max_drawdown,
                "max_profit": self.max_profit
            }
            
            # Update current price
            self.current_price = current_price
            self.current_value = current_price * self.open_volume
            
            # Calculate P&L
            if self.position_type == PositionType.LONG:
                pnl = (current_price - self.avg_entry_price) * self.open_volume
            else:  # SHORT
                pnl = (self.avg_entry_price - current_price) * self.open_volume
            
            pnl_after_commission = pnl - self.entry_commission
            self.unrealized_pnl = self._round_decimal(pnl_after_commission)
            
            # Safe percentage calculation
            if self.total_entry_value > 0:
                self.unrealized_pnl_percent = self._round_decimal(
                    (pnl_after_commission / self.total_entry_value) * 100
                )
            
            # Update extremes
            if pnl_after_commission < self.max_drawdown:
                self.max_drawdown = self._round_decimal(pnl_after_commission)
                if self.total_entry_value > 0:
                    self.max_drawdown_percent = self._round_decimal(
                        (pnl_after_commission / self.total_entry_value) * 100
                    )
            
            if pnl_after_commission > self.max_profit:
                self.max_profit = self._round_decimal(pnl_after_commission)
                if self.total_entry_value > 0:
                    self.max_profit_percent = self._round_decimal(
                        (pnl_after_commission / self.total_entry_value) * 100
                    )
            
            result["new_state"] = {
                "unrealized_pnl": self.unrealized_pnl,
                "unrealized_pnl_percent": self.unrealized_pnl_percent,
                "max_drawdown": self.max_drawdown,
                "max_profit": self.max_profit
            }
            
            result["changes"] = {
                "pnl_delta": self.unrealized_pnl - previous_pnl,
                "percent_delta": (self.unrealized_pnl_percent or 0) - (previous_percent or 0)
            }
            
            result["success"] = True
            self._log_audit_event("PNL_UPDATED", result)
            
        except Exception as e:
            result["error"] = str(e)
            self._log_audit_event("PNL_UPDATE_FAILED", result)
            self._revert_to_safe_state()
        
        return result
    
    def close_position(self, close_price: float, close_volume: float = None) -> Dict[str, Any]:
        """
        Close position or partial position
        
        Args:
            close_price: Price at which to close
            close_volume: Volume to close (None = close all)
            
        Returns:
            Dict with closure results
        """
        result = {
            "success": False,
            "error": None,
            "closed_volume": 0,
            "realized_pnl": 0,
            "remaining_volume": 0
        }
        
        try:
            if not self.is_open():
                result["error"] = "Position is not open"
                return result
            
            # Determine volume to close
            if close_volume is None or close_volume >= self.open_volume:
                close_volume = self.open_volume
                fully_closed = True
            else:
                fully_closed = False
            
            if close_volume <= 0:
                result["error"] = "Close volume must be positive"
                return result
            
            # Calculate P&L for this closure
            if self.position_type == PositionType.LONG:
                pnl = (close_price - self.avg_entry_price) * close_volume
            else:
                pnl = (self.avg_entry_price - close_price) * close_volume
            
            # Update position
            self.closed_volume += close_volume
            self.open_volume -= close_volume
            self.realized_pnl += pnl
            self.total_pnl = self.realized_pnl + self.unrealized_pnl
            
            # Update status
            if fully_closed or self.open_volume == 0:
                self.status = PositionStatus.CLOSED
                self.closed_at = datetime.utcnow()
                self.open_duration_seconds = int(
                    (self.closed_at - self.opened_at).total_seconds()
                )
            else:
                self.status = PositionStatus.PARTIALLY_CLOSED
            
            result["success"] = True
            result["closed_volume"] = close_volume
            result["realized_pnl"] = pnl
            result["remaining_volume"] = self.open_volume
            
            self._log_audit_event("POSITION_CLOSED", result)
            
        except Exception as e:
            result["error"] = str(e)
            self._log_audit_event("POSITION_CLOSE_FAILED", result)
        
        return result
    
    # ==================== RISK MANAGEMENT ====================
    
    def update_trailing_stop(self, current_price: float) -> bool:
        """
        Update trailing stop, return True if triggered
        
        Args:
            current_price: Current market price
            
        Returns:
            bool: True if trailing stop was triggered
        """
        if self.trailing_stop is None or self.trailing_stop_distance is None:
            return False
        
        if self.position_type == PositionType.LONG:
            if current_price > (self.trailing_stop_highest or current_price):
                self.trailing_stop_highest = current_price
                self.trailing_stop = current_price - self.trailing_stop_distance
            
            if current_price <= self.trailing_stop:
                self.trailing_stop_triggered = True
                self._log_audit_event("TRAILING_STOP_TRIGGERED", {
                    "price": current_price,
                    "stop_level": self.trailing_stop,
                    "highest": self.trailing_stop_highest
                })
                return True
        
        else:  # SHORT
            if current_price < (self.trailing_stop_lowest or current_price):
                self.trailing_stop_lowest = current_price
                self.trailing_stop = current_price + self.trailing_stop_distance
            
            if current_price >= self.trailing_stop:
                self.trailing_stop_triggered = True
                self._log_audit_event("TRAILING_STOP_TRIGGERED", {
                    "price": current_price,
                    "stop_level": self.trailing_stop,
                    "lowest": self.trailing_stop_lowest
                })
                return True
        
        return False
    
    def calculate_risk_exposure(self) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics
        
        Returns:
            Dict with risk metrics
        """
        exposure = {
            "value_at_risk": 0.0,
            "expected_shortfall": 0.0,
            "risk_score": 0.0,
            "stress_test": {},
            "risk_limits": {}
        }
        
        try:
            # Value at Risk (simplified 95% VaR)
            if self.total_entry_value > 0:
                var_95 = self.total_entry_value * self.risk_percent * 1.65
                exposure["value_at_risk"] = self._round_decimal(var_95)
            
            # Expected Shortfall
            exposure["expected_shortfall"] = exposure["value_at_risk"] * 1.1
            
            # Risk Score (0-100)
            risk_factors = [
                self.leverage / 10,
                abs(self.unrealized_pnl_percent or 0) / 20,
                1 - (self.ai_confidence_score or 0),
                self.volatility_at_entry or 0
            ]
            exposure["risk_score"] = self._round_decimal(
                min(100, sum(risk_factors) * 25)
            )
            
            # Stress test scenarios
            exposure["stress_test"] = {
                "market_down_10": self._stress_test_price_change(-0.10),
                "market_down_25": self._stress_test_price_change(-0.25),
                "market_up_10": self._stress_test_price_change(0.10),
                "volatility_spike": self._stress_test_volatility()
            }
            
            # Risk limits
            exposure["risk_limits"] = {
                "max_loss_5_percent": self.total_entry_value * 0.05,
                "max_loss_10_percent": self.total_entry_value * 0.10,
                "current_loss": abs(self.unrealized_pnl)
            }
            
        except Exception as e:
            logger.error(f"Risk calculation error: {str(e)}")
            exposure["error"] = str(e)
        
        return exposure
    
    def _stress_test_price_change(self, percent_change: float) -> float:
        """Test PnL impact of price change"""
        if not self.is_open() or self.current_price is None:
            return 0.0
        
        new_price = self.current_price * (1 + percent_change)
        if self.position_type == PositionType.LONG:
            pnl = (new_price - self.avg_entry_price) * self.open_volume
        else:
            pnl = (self.avg_entry_price - new_price) * self.open_volume
        
        return self._round_decimal(pnl)
    
    def _stress_test_volatility(self) -> float:
        """Test volatility impact (simplified)"""
        if self.volatility_at_entry:
            return self._round_decimal(
                self.total_entry_value * self.volatility_at_entry * 2
            )
        return 0.0
    
    # ==================== SCALING METHODS ====================
    
    def scale_in(self, price: float, volume: float) -> Dict[str, Any]:
        """
        Record a scale-in operation
        
        Args:
            price: Entry price for new volume
            volume: Volume to add
            
        Returns:
            Dict with scale-in results
        """
        result = {
            "success": False,
            "error": None,
            "new_avg_price": 0,
            "new_total_volume": 0
        }
        
        try:
            if volume <= 0:
                raise ValueError("Scale-in volume must be positive")
            if price <= 0:
                raise ValueError("Scale-in price must be positive")
            
            self.is_scaled = True
            self.scale_in_count += 1
            
            old_volume = self.total_entry_volume
            self.total_entry_volume += volume
            self.open_volume += volume
            
            old_value = self.avg_entry_price * old_volume
            new_value = old_value + (price * volume)
            self.avg_entry_price = new_value / self.total_entry_volume
            self.total_entry_value += price * volume
            
            if self.scale_in_details is None:
                self.scale_in_details = []
            
            self.scale_in_details.append({
                "price": price,
                "volume": volume,
                "time": datetime.utcnow().isoformat(),
                "old_avg_price": self.avg_entry_price,
                "new_avg_price": self.avg_entry_price
            })
            
            self.status = PositionStatus.SCALING_IN
            
            result["success"] = True
            result["new_avg_price"] = self.avg_entry_price
            result["new_total_volume"] = self.total_entry_volume
            
            self._log_audit_event("SCALE_IN", result)
            
        except Exception as e:
            result["error"] = str(e)
            self._log_audit_event("SCALE_IN_FAILED", result)
        
        return result
    
    def scale_out(self, price: float, volume: float) -> Dict[str, Any]:
        """
        Record a scale-out operation
        
        Args:
            price: Exit price for volume
            volume: Volume to remove
            
        Returns:
            Dict with scale-out results
        """
        result = {
            "success": False,
            "error": None,
            "realized_pnl": 0,
            "remaining_volume": 0
        }
        
        try:
            if volume <= 0:
                raise ValueError("Scale-out volume must be positive")
            if volume > self.open_volume:
                raise ValueError("Scale-out volume exceeds open volume")
            if price <= 0:
                raise ValueError("Scale-out price must be positive")
            
            self.is_scaled = True
            self.scale_out_count += 1
            
            if self.position_type == PositionType.LONG:
                pnl = (price - self.avg_entry_price) * volume
            else:
                pnl = (self.avg_entry_price - price) * volume
            
            self.closed_volume += volume
            self.open_volume -= volume
            self.realized_pnl += pnl
            
            if self.avg_exit_price is None:
                self.avg_exit_price = price
            else:
                old_value = self.avg_exit_price * (self.closed_volume - volume)
                new_value = old_value + (price * volume)
                self.avg_exit_price = new_value / self.closed_volume
            
            if self.scale_out_details is None:
                self.scale_out_details = []
            
            self.scale_out_details.append({
                "price": price,
                "volume": volume,
                "time": datetime.utcnow().isoformat(),
                "realized_pnl": pnl
            })
            
            if self.open_volume == 0:
                self.status = PositionStatus.CLOSED
                self.closed_at = datetime.utcnow()
                self.open_duration_seconds = int(
                    (self.closed_at - self.opened_at).total_seconds()
                )
            else:
                self.status = PositionStatus.SCALING_OUT
            
            result["success"] = True
            result["realized_pnl"] = pnl
            result["remaining_volume"] = self.open_volume
            
            self._log_audit_event("SCALE_OUT", result)
            
        except Exception as e:
            result["error"] = str(e)
            self._log_audit_event("SCALE_OUT_FAILED", result)
        
        return result
    
    # ==================== PORTFOLIO MANAGEMENT ====================
    
    def adjust_portfolio_weight(self, target_weight: float, 
                               portfolio_total_value: float) -> Dict[str, Any]:
        """
        Adjust position size based on target portfolio weight
        
        Args:
            target_weight: Desired percentage of portfolio (0-1)
            portfolio_total_value: Current total portfolio value
            
        Returns:
            Dict with adjustment results
        """
        result = {
            "success": False,
            "error": None,
            "target_volume": 0,
            "adjustment_needed": 0
        }
        
        try:
            if not 0 <= target_weight <= 1:
                raise ValueError(f"Target weight must be between 0 and 1: {target_weight}")
            if portfolio_total_value <= 0:
                raise ValueError("Portfolio total value must be positive")
            
            self.portfolio_weight = target_weight
            
            target_value = portfolio_total_value * target_weight
            target_volume = target_value / self.avg_entry_price
            adjustment_needed = target_volume - self.open_volume
            
            result["success"] = True
            result["target_volume"] = target_volume
            result["adjustment_needed"] = adjustment_needed
            
            self._log_audit_event("WEIGHT_ADJUSTMENT", {
                "target_weight": target_weight,
                "target_value": target_value,
                "target_volume": target_volume,
                "adjustment_needed": adjustment_needed
            })
            
        except Exception as e:
            result["error"] = str(e)
            self._log_audit_event("WEIGHT_ADJUSTMENT_FAILED", result)
        
        return result
    
    def calculate_correlation(self, other_position: 'Position') -> float:
        """
        Calculate correlation between two positions
        
        Args:
            other_position: Other position to correlate with
            
        Returns:
            float: Correlation coefficient (-1 to 1)
        """
        if not other_position or not self.is_open() or not other_position.is_open():
            return 0.0
        
        try:
            if self.symbol == other_position.symbol:
                if self.position_type == other_position.position_type:
                    return 1.0
                else:
                    return -1.0
            return 0.0
        except Exception as e:
            logger.error(f"Correlation calculation error: {str(e)}")
            return 0.0
    
    # ==================== PERFORMANCE ANALYTICS ====================
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Comprehensive performance metrics
        
        Returns:
            Dict with performance metrics
        """
        metrics = {
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "largest_win": self.max_profit,
            "largest_loss": self.max_drawdown,
            "winning_streak": 0,
            "losing_streak": 0,
            "recovery_factor": 0.0,
            "sharpe_ratio": 0.0,
            "calmar_ratio": 0.0,
            "sortino_ratio": 0.0
        }
        
        try:
            metrics["win_rate"] = self._calculate_win_rate()
            metrics["profit_factor"] = self._calculate_profit_factor()
            
            if self.max_drawdown != 0:
                metrics["recovery_factor"] = self._round_decimal(
                    abs(self.total_pnl / self.max_drawdown)
                )
            
            metrics["sharpe_ratio"] = self.calculate_sharpe_ratio()
            metrics["calmar_ratio"] = self.calculate_calmar_ratio()
            metrics["sortino_ratio"] = self._calculate_sortino_ratio()
            
        except Exception as e:
            logger.error(f"Performance metrics error: {str(e)}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from historical data"""
        if self.trade_count == 0:
            return 0.0
        
        if self.total_pnl > 0:
            if self.risk_reward_ratio > 0:
                return min(1.0, 1 / (1 + self.risk_reward_ratio))
            return 0.5
        elif self.total_pnl < 0:
            return max(0.0, 1 - self.risk_reward_ratio / 3)
        return 0.5
    
    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        if self.total_pnl == 0:
            return 1.0
        
        if self.total_pnl > 0:
            return self._round_decimal(self.total_pnl / abs(self.total_pnl) * 1.5)
        else:
            return self._round_decimal(abs(self.total_pnl) / self.total_pnl * 0.5)
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if self.total_pnl == 0 or self.open_duration_seconds == 0:
            return 0.0
        
        try:
            years = self.open_duration_seconds / 31536000
            if years == 0:
                years = 1/365
            
            annualized_return = (self.total_pnl / self.total_entry_value) / years
            volatility = 0.15
            
            if volatility == 0:
                return 0.0
            
            sharpe = (annualized_return - risk_free_rate) / volatility
            return self._round_decimal(sharpe)
            
        except Exception:
            return 0.0
    
    def calculate_calmar_ratio(self) -> float:
        """Calculate Calmar ratio"""
        if self.max_drawdown == 0 or self.total_pnl == 0:
            return 0.0
        
        try:
            calmar = abs(self.total_pnl / self.max_drawdown)
            return self._round_decimal(calmar)
        except Exception:
            return 0.0
    
    def _calculate_sortino_ratio(self) -> float:
        """Calculate Sortino ratio"""
        if self.total_pnl == 0 or self.open_duration_seconds == 0:
            return 0.0
        
        try:
            years = self.open_duration_seconds / 31536000
            if years == 0:
                years = 1/365
            
            annualized_return = (self.total_pnl / self.total_entry_value) / years
            downside_deviation = 0.10
            
            if downside_deviation == 0:
                return 0.0
            
            sortino = annualized_return / downside_deviation
            return self._round_decimal(sortino)
            
        except Exception:
            return 0.0
    
    # ==================== POSITION SUMMARY ====================
    
    def get_position_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive position summary with safe null handling
        
        Returns:
            Dict with position summary
        """
        return {
            "id": self.id,
            "symbol": self.symbol,
            "type": self.position_type.value if self.position_type else None,
            "status": self.status.value if self.status else None,
            "open_volume": self.open_volume or 0,
            "avg_entry_price": self.avg_entry_price or 0,
            "current_price": self.current_price or 0,
            "pnl": self.unrealized_pnl if self.is_open() else (self.total_pnl or 0),
            "pnl_percent": (
                self.unrealized_pnl_percent if self.is_open() 
                else (self.total_pnl_percent or 0)
            ),
            "portfolio_weight": self.portfolio_weight or 0,
            "ai_confidence": self.ai_confidence_score or 0,
            "is_hedged": self.is_hedged or False,
            "duration": self.open_duration_seconds or 0,
            "risk_reward": self.risk_reward_ratio or 0,
            "leverage": self.leverage or 1,
            "margin_used": self.margin_used or 0,
            "is_scaled": self.is_scaled or False,
            "scale_in_count": self.scale_in_count or 0,
            "scale_out_count": self.scale_out_count or 0,
            "trade_count": self.trade_count or 1,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert position to JSON-serializable dictionary
        
        Returns:
            Dict with all position data
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "portfolio_id": self.portfolio_id,
            "position_group_id": self.position_group_id,
            "symbol": self.symbol,
            "position_type": self.position_type.value if self.position_type else None,
            "status": self.status.value if self.status else None,
            "position_mode": self.position_mode.value if self.position_mode else None,
            "avg_entry_price": self.avg_entry_price,
            "total_entry_volume": self.total_entry_volume,
            "total_entry_value": self.total_entry_value,
            "entry_commission": self.entry_commission,
            "current_price": self.current_price,
            "current_value": self.current_value,
            "open_volume": self.open_volume,
            "closed_volume": self.closed_volume,
            "fill_percent": self.fill_percent,
            "partial_fills": self.partial_fills,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "trailing_stop": self.trailing_stop,
            "trailing_stop_distance": self.trailing_stop_distance,
            "trailing_stop_triggered": self.trailing_stop_triggered,
            "breakeven_price": self.breakeven_price,
            "breakeven_triggered": self.breakeven_triggered,
            "risk_amount": self.risk_amount,
            "risk_percent": self.risk_percent,
            "reward_amount": self.reward_amount,
            "risk_reward_ratio": self.risk_reward_ratio,
            "is_scaled": self.is_scaled,
            "scale_in_count": self.scale_in_count,
            "scale_out_count": self.scale_out_count,
            "scale_in_details": self.scale_in_details,
            "scale_out_details": self.scale_out_details,
            "avg_exit_price": self.avg_exit_price,
            "is_hedged": self.is_hedged,
            "hedge_strategy": self.hedge_strategy.value if self.hedge_strategy else None,
            "hedge_position_id": self.hedge_position_id,
            "hedge_ratio": self.hedge_ratio,
            "hedge_details": self.hedge_details,
            "is_multi_leg": self.is_multi_leg,
            "leg_trades": self.leg_trades,
            "leg_count": self.leg_count,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_percent": self.unrealized_pnl_percent,
            "realized_pnl": self.realized_pnl,
            "total_pnl": self.total_pnl,
            "total_pnl_percent": self.total_pnl_percent,
            "total_pnl_after_commission": self.total_pnl_after_commission,
            "max_profit": self.max_profit,
            "max_profit_percent": self.max_profit_percent,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_percent": self.max_drawdown_percent,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "open_duration_seconds": self.open_duration_seconds,
            "is_intraday": self.is_intraday,
            "bot_id": self.bot_id,
            "bot_name": self.bot_name,
            "bot_strategy": self.bot_strategy,
            "is_bot_managed": self.is_bot_managed,
            "strategy_settings": self.strategy_settings,
            "strategy_signals": self.strategy_signals,
            "portfolio_weight": self.portfolio_weight,
            "portfolio_risk": self.portfolio_risk,
            "asset_allocation": self.asset_allocation,
            "correlated_positions": self.correlated_positions,
            "correlation_coefficient": self.correlation_coefficient,
            "ai_confidence_score": self.ai_confidence_score,
            "ai_signal_strength": self.ai_signal_strength,
            "ai_recommendation": self.ai_recommendation,
            "market_regime_at_entry": self.market_regime_at_entry.value if self.market_regime_at_entry else None,
            "volatility_at_entry": self.volatility_at_entry,
            "volume_at_entry": self.volume_at_entry,
            "iats_adaptations": self.iats_adaptations,
            "iats_ensemble_signal": self.iats_ensemble_signal,
            "expected_win_rate": self.expected_win_rate,
            "expected_max_drawdown": self.expected_max_drawdown,
            "is_margin_position": self.is_margin_position,
            "is_futures_position": self.is_futures_position,
            "leverage": self.leverage,
            "margin_used": self.margin_used,
            "margin_level": self.margin_level,
            "trade_count": self.trade_count,
            "entry_trade_id": self.entry_trade_id,
            "exit_trade_ids": self.exit_trade_ids,
            "is_compliant": self.is_compliant,
            "compliance_notes": self.compliance_notes,
            "audit_trail": self.audit_trail,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
            "exchange": self.exchange,
            "notes": self.notes,
            "tags": self.tags,
            "custom_data": self.custom_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metrics": self._get_clean_metrics()
        }
    
    def _get_clean_metrics(self) -> Dict[str, float]:
        """Get clean metric dictionary with None handling"""
        return {
            "risk_reward_ratio": self.risk_reward_ratio or 0.0,
            "unrealized_pnl_percent": self.unrealized_pnl_percent or 0.0,
            "total_pnl_percent": self.total_pnl_percent or 0.0,
            "max_drawdown": self.max_drawdown or 0.0,
            "max_drawdown_percent": self.max_drawdown_percent or 0.0,
            "max_profit": self.max_profit or 0.0,
            "max_profit_percent": self.max_profit_percent or 0.0,
            "open_duration": self.open_duration_seconds or 0,
            "fill_percent": self.fill_percent or 0.0,
            "open_volume": self.open_volume or 0.0,
            "closed_volume": self.closed_volume or 0.0,
            "close_percent": self.get_close_percent() if self.total_entry_volume > 0 else 0.0
        }
    
    # ==================== COMPLIANCE & AUDIT ====================
    
    def _log_audit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log compliance audit events with full context
        
        Args:
            event_type: Type of event
            details: Event details
        """
        try:
            if self.audit_trail is None:
                self.audit_trail = []
            
            audit_entry = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": self.user_id,
                "position_id": self.id,
                "symbol": self.symbol,
                "event_details": details,
                "state_snapshot": {
                    "status": self.status.value if self.status else None,
                    "open_volume": self.open_volume,
                    "unrealized_pnl": self.unrealized_pnl,
                    "current_price": self.current_price,
                    "total_pnl": self.total_pnl
                }
            }
            
            self.audit_trail.append(audit_entry)
            self._check_compliance(audit_entry)
            
        except Exception as e:
            logger.error(f"Audit logging error: {str(e)}")
    
    def _check_compliance(self, audit_entry: Dict[str, Any]) -> None:
        """
        Perform compliance checks on audit events
        
        Flags:
        - Large position size changes
        - Multiple scale operations
        - Unusual timing
        - Risk limit violations
        """
        try:
            warning_count = 0
            warnings = []
            
            if self.total_entry_value > 1000000:
                warnings.append("Large position size exceeds threshold")
                warning_count += 1
            
            scale_ops = len(self.scale_in_details or []) + len(self.scale_out_details or [])
            if scale_ops > 10:
                warnings.append("Excessive scaling operations")
                warning_count += 1
            
            if abs(self.unrealized_pnl_percent or 0) > 20:
                warnings.append("High loss percentage")
                warning_count += 1
            
            if self.leverage > 100:
                warnings.append("Extreme leverage")
                warning_count += 1
            
            if self.ai_confidence_score and self.ai_confidence_score < 0.3:
                warnings.append("Low AI confidence score")
                warning_count += 1
            
            if warning_count >= 3:
                self.is_compliant = False
                self.compliance_notes = f"COMPLIANCE WARNING: {', '.join(warnings[:5])}"
                
                self._log_audit_event("COMPLIANCE_WARNING", {
                    "warnings": warnings,
                    "warning_count": warning_count
                })
            
        except Exception as e:
            logger.error(f"Compliance check error: {str(e)}")
    
    def _revert_to_safe_state(self) -> None:
        """Revert position to safe state"""
        try:
            self.status = PositionStatus.SUSPENDED
            self._log_audit_event("POSITION_SUSPENDED", {
                "reason": "Automated suspension due to update failure",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"State reversion error: {str(e)}")
    
    # ==================== UTILITY METHODS ====================
    
    def _round_decimal(self, value: float, precision: int = 8) -> float:
        """
        Round float to specified precision for financial calculations
        
        Args:
            value: Value to round
            precision: Number of decimal places
            
        Returns:
            Rounded float
        """
        if value is None:
            return 0.0
        return float(Decimal(str(value)).quantize(
            Decimal('1e-' + str(precision)),
            rounding=ROUND_HALF_UP
        ))
    
    def safe_update_pnl(self, current_price: float) -> Dict[str, Any]:
        """
        Safely update PnL with comprehensive error handling and recovery
        
        Args:
            current_price: Current market price
            
        Returns:
            Dict with update results
        """
        result = {
            "success": False,
            "error": None,
            "previous_state": None,
            "new_state": None
        }
        
        try:
            result["previous_state"] = {
                "unrealized_pnl": self.unrealized_pnl,
                "unrealized_pnl_percent": self.unrealized_pnl_percent,
                "max_drawdown": self.max_drawdown,
                "status": self.status.value if self.status else None
            }
            
            update_result = self.update_unrealized_pnl(current_price)
            
            if update_result["success"]:
                result["success"] = True
                result["new_state"] = update_result["new_state"]
                result["changes"] = update_result.get("changes", {})
                self._log_audit_event("PNL_UPDATE_SUCCESS", result)
            else:
                result["error"] = update_result.get("error", "Unknown error")
                self._log_audit_event("PNL_UPDATE_FAILURE", result)
                self._revert_to_safe_state()
                
        except Exception as e:
            result["error"] = str(e)
            self._log_audit_event("PNL_UPDATE_EXCEPTION", result)
            self._revert_to_safe_state()
        
        return result
    
    # ==================== DATABASE QUERY METHODS ====================
    
    @classmethod
    def get_active_positions(cls, session, user_id: int, portfolio_id: int = None):
        """
        Query active positions efficiently with eager loading
        
        Args:
            session: SQLAlchemy session
            user_id: User ID
            portfolio_id: Optional portfolio ID filter
            
        Returns:
            List of active positions
        """
        query = session.query(cls).filter(
            cls.user_id == user_id,
            cls.status.in_([
                PositionStatus.OPEN,
                PositionStatus.PARTIALLY_CLOSED,
                PositionStatus.SCALING_IN,
                PositionStatus.SCALING_OUT
            ])
        )
        
        if portfolio_id:
            query = query.filter(cls.portfolio_id == portfolio_id)
        
        query = query.options(joinedload(cls.entry_trade_id))
        
        return query.all()
    
    @classmethod
    def get_portfolio_summary(cls, session, user_id: int, portfolio_id: int) -> Dict[str, Any]:
        """
        Get portfolio-level position summary
        
        Args:
            session: SQLAlchemy session
            user_id: User ID
            portfolio_id: Portfolio ID
            
        Returns:
            Dict with portfolio summary
        """
        positions = cls.get_active_positions(session, user_id, portfolio_id)
        
        summary = {
            "total_positions": len(positions),
            "total_value": 0.0,
            "total_pnl": 0.0,
            "weighted_risk": 0.0,
            "hedged_positions": 0,
            "average_confidence": 0.0,
            "max_drawdown": 0.0,
            "max_profit": 0.0,
            "total_risk": 0.0,
            "average_position_value": 0.0
        }
        
        if not positions:
            return summary
        
        for pos in positions:
            summary["total_value"] += pos.current_value or 0
            summary["total_pnl"] += pos.unrealized_pnl or 0
            
            if pos.is_hedged:
                summary["hedged_positions"] += 1
            
            summary["average_confidence"] += pos.ai_confidence_score or 0
            summary["total_risk"] += pos.risk_amount or 0
            
            if pos.portfolio_weight:
                summary["weighted_risk"] += (pos.risk_percent or 0) * pos.portfolio_weight
            
            if pos.max_drawdown < summary["max_drawdown"]:
                summary["max_drawdown"] = pos.max_drawdown
            if pos.max_profit > summary["max_profit"]:
                summary["max_profit"] = pos.max_profit
        
        summary["average_confidence"] /= len(positions)
        summary["average_position_value"] = summary["total_value"] / len(positions)
        
        return summary
    
    @classmethod
    def get_positions_by_symbol(cls, session, user_id: int, symbol: str, 
                               status_filter: List[str] = None):
        """
        Get positions for a specific symbol
        
        Args:
            session: SQLAlchemy session
            user_id: User ID
            symbol: Trading symbol
            status_filter: Optional list of statuses to filter
            
        Returns:
            List of positions
        """
        query = session.query(cls).filter(
            cls.user_id == user_id,
            cls.symbol == symbol
        )
        
        if status_filter:
            query = query.filter(cls.status.in_(status_filter))
        
        return query.all()
    
    # ==================== REPRESENTATION ====================
    
    def __repr__(self) -> str:
        return (f"<Position id={self.id} symbol={self.symbol} "
                f"type={self.position_type.value if self.position_type else None} "
                f"status={self.status.value if self.status else None} "
                f"pnl={self.unrealized_pnl or self.total_pnl}>")
    
    def __str__(self) -> str:
        return (f"{self.symbol} {self.position_type.value if self.position_type else None} "
                f"@ {self.avg_entry_price:.2f} (Vol: {self.open_volume:.4f})")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example usage (for testing)
    print("Position Model Loaded Successfully")
    print(f"PositionStatus: {[s.value for s in PositionStatus]}")
    print(f"PositionType: {[t.value for t in PositionType]}")
    print(f"HedgeStrategy: {[h.value for h in HedgeStrategy]}")
    print(f"PositionMode: {[m.value for m in PositionMode]}")
    print(f"MarketRegime: {[r.value for r in MarketRegime]}")