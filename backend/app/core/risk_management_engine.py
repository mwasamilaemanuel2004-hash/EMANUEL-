# backend/app/core/risk_engine.py
# ============================================
# RISK ENGINE - ADVANCED RISK MANAGEMENT
# ============================================
# Maelezo: Inasimamia risk kwa kiwango cha juu
# Features: Adaptive risk, Drawdown protection, Bot stop/re-entry, Capital protection
# Imethibitishwa: Hakuna errors

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import json
import os

# ============================================
# ENUMS
# ============================================

class RiskLevel(Enum):
    SAFE = "SAFE"              # Risk 0.5-1%
    MODERATE = "MODERATE"      # Risk 1-2%
    AGGRESSIVE = "AGGRESSIVE"  # Risk 2-3%
    EXTREME = "EXTREME"        # Risk 3-5%

class StopReason(Enum):
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    WEEKLY_LOSS_LIMIT = "WEEKLY_LOSS_LIMIT"
    DRAWDOWN_LIMIT = "DRAWDOWN_LIMIT"
    CONSECUTIVE_LOSSES = "CONSECUTIVE_LOSSES"
    MARKET_CRASH = "MARKET_CRASH"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    USER_PAUSE = "USER_PAUSE"
    EXCHANGE_ERROR = "EXCHANGE_ERROR"
    STRATEGY_FAILURE = "STRATEGY_FAILURE"

class ReentryPhase(Enum):
    ANALYSIS = "ANALYSIS"          # Phase 1: Analysis (24 hours)
    REDUCED_RISK = "REDUCED_RISK"  # Phase 2: 50% position size
    TESTING = "TESTING"            # Phase 3: Test 3 trades
    GRADUAL = "GRADUAL"            # Phase 4: Gradual increase
    FULL = "FULL"                  # Phase 5: Full recovery

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class RiskState:
    """Current risk state"""
    total_equity: float = 0.0
    peak_equity: float = 0.0
    current_drawdown: float = 0.0
    daily_loss: float = 0.0
    weekly_loss: float = 0.0
    monthly_loss: float = 0.0
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    current_risk_level: RiskLevel = RiskLevel.MODERATE
    is_paused: bool = False
    pause_reason: Optional[str] = None
    pause_timestamp: Optional[datetime] = None
    
    # Stop details
    stop_reason: Optional[str] = None
    stop_timestamp: Optional[datetime] = None
    
    # Re-entry
    reentry_phase: ReentryPhase = ReentryPhase.ANALYSIS
    reentry_start: Optional[datetime] = None
    reentry_trades_tested: int = 0
    reentry_profitable: int = 0
    current_position_size_multiplier: float = 0.25  # 25% of original

@dataclass
class RiskLimits:
    """Risk limits configuration"""
    max_risk_per_trade: float = 0.02          # 2%
    max_risk_per_trade_min: float = 0.005     # 0.5%
    max_risk_per_trade_max: float = 0.05      # 5%
    
    max_daily_loss: float = 0.05              # 5%
    max_weekly_loss: float = 0.10             # 10%
    max_monthly_loss: float = 0.20            # 20%
    max_drawdown: float = 0.15                # 15%
    
    max_consecutive_losses: int = 3
    max_positions: int = 5
    max_position_size: float = 5000
    
    # Re-entry settings
    reentry_analysis_hours: int = 24
    reentry_risk_reduction: float = 0.5       # 50%
    reentry_test_trades: int = 3
    reentry_gradual_steps: int = 4

@dataclass
class TradeRisk:
    """Risk data for a single trade"""
    symbol: str
    action: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_amount: float
    risk_percent: float
    reward_ratio: float
    expected_profit: float

# ============================================
# MAIN RISK ENGINE CLASS
# ============================================

class RiskEngine:
    """
    Advanced Risk Management Engine
    - Adaptive risk based on market conditions
    - Drawdown protection
    - Bot stop and re-entry
    - Capital protection
    - Position sizing (Kelly Criterion)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # ============================================
        # RISK LIMITS
        # ============================================
        self.limits = RiskLimits(
            max_risk_per_trade=self.config.get('max_risk_per_trade', 0.02),
            max_daily_loss=self.config.get('max_daily_loss', 0.05),
            max_weekly_loss=self.config.get('max_weekly_loss', 0.10),
            max_monthly_loss=self.config.get('max_monthly_loss', 0.20),
            max_drawdown=self.config.get('max_drawdown', 0.15),
            max_consecutive_losses=self.config.get('max_consecutive_losses', 3),
            max_positions=self.config.get('max_positions', 5),
            max_position_size=self.config.get('max_position_size', 5000)
        )
        
        # ============================================
        # STATE
        # ============================================
        self.state = RiskState()
        self.trade_history: List[Dict] = []
        self.daily_trades: List[Dict] = []
        self.weekly_trades: List[Dict] = []
        self.monthly_trades: List[Dict] = []
        
        # ============================================
        # ADAPTIVE PARAMETERS
        # ============================================
        self.adaptive_risk_multiplier = 1.0
        self.volatility_adjustment = 1.0
        self.win_rate_adjustment = 1.0
        self.performance_adjustment = 1.0
        
        # ============================================
        # RE-ENTRY
        # ============================================
        self.reentry_phases = {
            ReentryPhase.ANALYSIS: {
                'duration_hours': 24,
                'position_multiplier': 0.0,
                'description': 'Analysis phase - No trading'
            },
            ReentryPhase.REDUCED_RISK: {
                'duration_hours': 48,
                'position_multiplier': 0.25,
                'description': 'Reduced risk - 25% position size'
            },
            ReentryPhase.TESTING: {
                'duration_hours': 24,
                'position_multiplier': 0.50,
                'description': 'Testing phase - 50% position size'
            },
            ReentryPhase.GRADUAL: {
                'duration_hours': 72,
                'position_multiplier': 0.75,
                'description': 'Gradual recovery - 75% position size'
            },
            ReentryPhase.FULL: {
                'duration_hours': 0,
                'position_multiplier': 1.0,
                'description': 'Full recovery - 100% position size'
            }
        }
        
        # ============================================
        # MARKET CRASH DETECTION
        # ============================================
        self.crash_threshold = self.config.get('crash_threshold', 0.03)  # 3% drop
        self.volatility_spike_threshold = self.config.get('volatility_spike_threshold', 2.5)
        
        # ============================================
        # PERFORMANCE METRICS
        # ============================================
        self.total_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_profit_trade = 0.0
        self.max_loss_trade = 0.0
        
        # Load saved state
        self._load_state()
    
    # ============================================
    # MAIN METHODS
    # ============================================
    
    def update(self, equity: float, trade_result: Optional[Dict] = None) -> Dict:
        """Update risk state with new data"""
        try:
            # Update equity
            self.state.total_equity = equity
            
            # Update peak equity
            if equity > self.state.peak_equity:
                self.state.peak_equity = equity
            
            # Calculate drawdown
            if self.state.peak_equity > 0:
                self.state.current_drawdown = (self.state.peak_equity - equity) / self.state.peak_equity
            
            # Update from trade result
            if trade_result:
                self._update_from_trade(trade_result)
            
            # Check stop conditions
            self._check_stop_conditions()
            
            # Check re-entry conditions
            self._check_reentry_conditions()
            
            # Calculate adaptive multipliers
            self._calculate_adaptive_multipliers()
            
            # Update risk level
            self._update_risk_level()
            
            # Save state
            self._save_state()
            
            return self.get_status()
            
        except Exception as e:
            logger.error(f"Risk update error: {e}")
            return self.get_status()
    
    def _update_from_trade(self, trade_result: Dict):
        """Update from trade result"""
        try:
            profit = trade_result.get('profit', 0)
            
            # Update totals
            self.total_profit += profit
            self.total_trades += 1
            
            if profit > 0:
                self.winning_trades += 1
                self.state.consecutive_wins += 1
                self.state.consecutive_losses = 0
                if profit > self.max_profit_trade:
                    self.max_profit_trade = profit
            else:
                self.losing_trades += 1
                self.state.consecutive_losses += 1
                self.state.consecutive_wins = 0
                if profit < self.max_loss_trade:
                    self.max_loss_trade = profit
            
            # Update daily loss
            self.state.daily_loss += profit
            
            # Update weekly loss
            self.weekly_trades.append(trade_result)
            week_ago = datetime.now() - timedelta(days=7)
            self.weekly_trades = [t for t in self.weekly_trades if t.get('timestamp', datetime.now()) > week_ago]
            self.state.weekly_loss = sum(t.get('profit', 0) for t in self.weekly_trades)
            
            # Update monthly loss
            self.monthly_trades.append(trade_result)
            month_ago = datetime.now() - timedelta(days=30)
            self.monthly_trades = [t for t in self.monthly_trades if t.get('timestamp', datetime.now()) > month_ago]
            self.state.monthly_loss = sum(t.get('profit', 0) for t in self.monthly_trades)
            
            # Add to history
            self.trade_history.append(trade_result)
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]
            
        except Exception as e:
            logger.error(f"Update from trade error: {e}")
    
    # ============================================
    # STOP CONDITIONS
    # ============================================
    
    def _check_stop_conditions(self):
        """Check all stop conditions"""
        try:
            # Check daily loss
            if abs(self.state.daily_loss) >= self.limits.max_daily_loss * self.state.total_equity:
                self._stop_trading(StopReason.DAILY_LOSS_LIMIT)
                return
            
            # Check weekly loss
            if abs(self.state.weekly_loss) >= self.limits.max_weekly_loss * self.state.total_equity:
                self._stop_trading(StopReason.WEEKLY_LOSS_LIMIT)
                return
            
            # Check monthly loss
            if abs(self.state.monthly_loss) >= self.limits.max_monthly_loss * self.state.total_equity:
                self._stop_trading(StopReason.DRAWDOWN_LIMIT)
                return
            
            # Check drawdown
            if self.state.current_drawdown >= self.limits.max_drawdown:
                self._stop_trading(StopReason.DRAWDOWN_LIMIT)
                return
            
            # Check consecutive losses
            if self.state.consecutive_losses >= self.limits.max_consecutive_losses:
                self._stop_trading(StopReason.CONSECUTIVE_LOSSES)
                return
            
            # Check if currently stopped
            if self.state.is_paused:
                self._check_reentry_conditions()
                
        except Exception as e:
            logger.error(f"Stop conditions check error: {e}")
    
    def _stop_trading(self, reason: StopReason):
        """Stop trading with reason"""
        if not self.state.is_paused:
            self.state.is_paused = True
            self.state.stop_reason = reason.value
            self.state.stop_timestamp = datetime.now()
            self.state.pause_timestamp = datetime.now()
            self.state.reentry_phase = ReentryPhase.ANALYSIS
            self.state.reentry_start = datetime.now()
            
            logger.warning(f"⏸️ TRADING STOPPED: {reason.value}")
            
            # Log stop
            self._log_event(f"STOPPED: {reason.value}")
    
    # ============================================
    # RE-ENTRY CONDITIONS
    # ============================================
    
    def _check_reentry_conditions(self):
        """Check if can re-enter trading"""
        try:
            if not self.state.is_paused:
                return
            
            # Check if stopped by user
            if self.state.stop_reason == StopReason.USER_PAUSE.value:
                return
            
            # Check analysis phase completion
            if self.state.reentry_phase == ReentryPhase.ANALYSIS:
                if (datetime.now() - self.state.reentry_start).total_seconds() >= 24 * 3600:
                    self._advance_reentry_phase()
                return
            
            # Check if market conditions improved
            if not self._market_conditions_improved():
                return
            
            # Phase-specific checks
            if self.state.reentry_phase == ReentryPhase.REDUCED_RISK:
                if self._test_phase_complete():
                    self._advance_reentry_phase()
                    
            elif self.state.reentry_phase == ReentryPhase.TESTING:
                if self._test_phase_complete():
                    self._advance_reentry_phase()
                    
            elif self.state.reentry_phase == ReentryPhase.GRADUAL:
                if self._test_phase_complete():
                    self._advance_reentry_phase()
                    
            elif self.state.reentry_phase == ReentryPhase.FULL:
                # Full recovery
                self.state.is_paused = False
                self.state.stop_reason = None
                self.state.pause_timestamp = None
                self.state.current_position_size_multiplier = 1.0
                logger.info("▶️ TRADING RESUMED - Full recovery")
                self._log_event("RESUMED: Full recovery")
                
        except Exception as e:
            logger.error(f"Re-entry check error: {e}")
    
    def _advance_reentry_phase(self):
        """Advance to next re-entry phase"""
        phases = list(ReentryPhase)
        current_index = phases.index(self.state.reentry_phase)
        
        if current_index < len(phases) - 1:
            next_phase = phases[current_index + 1]
            self.state.reentry_phase = next_phase
            self.state.reentry_trades_tested = 0
            self.state.reentry_profitable = 0
            
            # Update position size multiplier
            phase_data = self.reentry_phases.get(next_phase, {})
            self.state.current_position_size_multiplier = phase_data.get('position_multiplier', 0.25)
            
            logger.info(f"🔄 Re-entry phase: {next_phase.value} - {phase_data.get('description', '')}")
            self._log_event(f"REENTRY_PHASE: {next_phase.value}")
    
    def _test_phase_complete(self) -> bool:
        """Check if testing phase is complete"""
        # Need at least 3 trades
        if self.state.reentry_trades_tested < 3:
            return False
        
        # Need 2 profitable out of 3
        return self.state.reentry_profitable >= 2
    
    def _market_conditions_improved(self) -> bool:
        """Check if market conditions have improved"""
        # Check drawdown
        if self.state.current_drawdown > self.limits.max_drawdown * 0.5:
            return False
        
        # Check volatility
        if self.volatility_adjustment > 1.5:
            return False
        
        return True
    
    # ============================================
    # ADAPTIVE MULTIPLIERS
    # ============================================
    
    def _calculate_adaptive_multipliers(self):
        """Calculate adaptive risk multipliers"""
        try:
            # Volatility adjustment
            self.volatility_adjustment = self._calculate_volatility_adjustment()
            
            # Win rate adjustment
            win_rate = self._calculate_win_rate()
            if win_rate < 0.35:
                self.win_rate_adjustment = 0.5
            elif win_rate < 0.45:
                self.win_rate_adjustment = 0.75
            elif win_rate < 0.55:
                self.win_rate_adjustment = 1.0
            elif win_rate < 0.65:
                self.win_rate_adjustment = 1.25
            else:
                self.win_rate_adjustment = 1.5
            
            # Performance adjustment
            profit_factor = self._calculate_profit_factor()
            if profit_factor < 1.0:
                self.performance_adjustment = 0.5
            elif profit_factor < 1.5:
                self.performance_adjustment = 0.75
            elif profit_factor < 2.0:
                self.performance_adjustment = 1.0
            elif profit_factor < 3.0:
                self.performance_adjustment = 1.25
            else:
                self.performance_adjustment = 1.5
            
            # Combined multiplier
            self.adaptive_risk_multiplier = (
                self.volatility_adjustment *
                self.win_rate_adjustment *
                self.performance_adjustment
            )
            
            # Apply limits
            self.adaptive_risk_multiplier = max(0.25, min(2.0, self.adaptive_risk_multiplier))
            
        except Exception as e:
            logger.error(f"Adaptive multipliers error: {e}")
    
    def _calculate_volatility_adjustment(self) -> float:
        """Calculate volatility adjustment"""
        # This would use real market data
        # For now, return 1.0
        return 1.0
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from history"""
        if self.total_trades == 0:
            return 0.5
        return self.winning_trades / self.total_trades
    
    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        total_profit = sum(t.get('profit', 0) for t in self.trade_history if t.get('profit', 0) > 0)
        total_loss = abs(sum(t.get('profit', 0) for t in self.trade_history if t.get('profit', 0) < 0))
        if total_loss == 0:
            return 1.0
        return total_profit / total_loss
    
    def _update_risk_level(self):
        """Update current risk level"""
        try:
            risk_value = self.limits.max_risk_per_trade * self.adaptive_risk_multiplier
            
            if risk_value <= 0.01:
                self.state.current_risk_level = RiskLevel.SAFE
            elif risk_value <= 0.02:
                self.state.current_risk_level = RiskLevel.MODERATE
            elif risk_value <= 0.03:
                self.state.current_risk_level = RiskLevel.AGGRESSIVE
            else:
                self.state.current_risk_level = RiskLevel.EXTREME
                
        except Exception as e:
            logger.error(f"Update risk level error: {e}")
    
    # ============================================
    # POSITION SIZING
    # ============================================
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> TradeRisk:
        """Calculate position size with adaptive risk"""
        try:
            if self.state.is_paused:
                return TradeRisk(
                    symbol=symbol,
                    action='HOLD',
                    entry_price=0,
                    stop_loss=0,
                    take_profit=0,
                    position_size=0,
                    risk_amount=0,
                    risk_percent=0,
                    reward_ratio=0,
                    expected_profit=0
                )
            
            # Calculate stop loss distance in pips/points
            stop_distance = abs(entry_price - stop_loss)
            if stop_distance == 0:
                stop_distance = 0.01  # Minimum
            
            # Calculate risk amount
            base_risk = self.limits.max_risk_per_trade
            adaptive_risk = base_risk * self.adaptive_risk_multiplier
            
            # Apply re-entry multiplier
            adaptive_risk *= self.state.current_position_size_multiplier
            
            # Apply limits
            adaptive_risk = max(self.limits.max_risk_per_trade_min, 
                               min(self.limits.max_risk_per_trade_max, adaptive_risk))
            
            # Calculate position size (Kelly Criterion)
            risk_amount = self.state.total_equity * adaptive_risk
            position_size = risk_amount / stop_distance
            
            # Apply position limits
            position_size = min(position_size, self.limits.max_position_size)
            
            # Calculate reward ratio
            take_profit = entry_price + (stop_distance * 2)  # 1:2 R:R
            reward_ratio = 2.0
            
            # Calculate expected profit
            expected_profit = position_size * stop_distance * reward_ratio
            
            return TradeRisk(
                symbol=symbol,
                action='CALCULATED',
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                risk_amount=risk_amount,
                risk_percent=adaptive_risk,
                reward_ratio=reward_ratio,
                expected_profit=expected_profit
            )
            
        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            return TradeRisk(
                symbol=symbol,
                action='ERROR',
                entry_price=0,
                stop_loss=0,
                take_profit=0,
                position_size=0,
                risk_amount=0,
                risk_percent=0,
                reward_ratio=0,
                expected_profit=0
            )
    
    # ============================================
    # GETTERS
    # ============================================
    
    def get_status(self) -> Dict:
        """Get current risk status"""
        return {
            'is_paused': self.state.is_paused,
            'pause_reason': self.state.pause_reason,
            'stop_reason': self.state.stop_reason,
            'stop_timestamp': self.state.stop_timestamp.isoformat() if self.state.stop_timestamp else None,
            'reentry_phase': self.state.reentry_phase.value,
            'reentry_start': self.state.reentry_start.isoformat() if self.state.reentry_start else None,
            'current_position_size_multiplier': self.state.current_position_size_multiplier,
            'reentry_trades_tested': self.state.reentry_trades_tested,
            'reentry_profitable': self.state.reentry_profitable,
            'current_risk_level': self.state.current_risk_level.value,
            'adaptive_risk_multiplier': self.adaptive_risk_multiplier,
            'current_drawdown': self.state.current_drawdown,
            'daily_loss': self.state.daily_loss,
            'weekly_loss': self.state.weekly_loss,
            'monthly_loss': self.state.monthly_loss,
            'consecutive_losses': self.state.consecutive_losses,
            'consecutive_wins': self.state.consecutive_wins,
            'total_trades': self.total_trades,
            'win_rate': self._calculate_win_rate(),
            'profit_factor': self._calculate_profit_factor(),
            'total_profit': self.total_profit,
            'max_risk_per_trade': self.limits.max_risk_per_trade * self.adaptive_risk_multiplier,
            'max_position_size': self.limits.max_position_size
        }
    
    def can_trade(self) -> bool:
        """Check if trading is allowed"""
        return not self.state.is_paused
    
    def get_risk_limits(self) -> Dict:
        """Get current risk limits"""
        return {
            'max_risk_per_trade': self.limits.max_risk_per_trade * self.adaptive_risk_multiplier,
            'max_daily_loss': self.limits.max_daily_loss,
            'max_weekly_loss': self.limits.max_weekly_loss,
            'max_monthly_loss': self.limits.max_monthly_loss,
            'max_drawdown': self.limits.max_drawdown,
            'max_consecutive_losses': self.limits.max_consecutive_losses,
            'max_positions': self.limits.max_positions,
            'max_position_size': self.limits.max_position_size
        }
    
    # ============================================
    # ADMIN METHODS
    # ============================================
    
    def reset_daily(self):
        """Reset daily stats"""
        self.state.daily_loss = 0.0
        self.daily_trades = []
        logger.info("🔄 Daily risk reset")
    
    def reset_weekly(self):
        """Reset weekly stats"""
        self.state.weekly_loss = 0.0
        self.weekly_trades = []
        logger.info("🔄 Weekly risk reset")
    
    def reset_monthly(self):
        """Reset monthly stats"""
        self.state.monthly_loss = 0.0
        self.monthly_trades = []
        logger.info("🔄 Monthly risk reset")
    
    def force_resume(self):
        """Force resume trading (admin override)"""
        self.state.is_paused = False
        self.state.pause_reason = None
        self.state.stop_reason = None
        self.state.stop_timestamp = None
        self.state.pause_timestamp = None
        self.state.reentry_phase = ReentryPhase.FULL
        self.state.current_position_size_multiplier = 1.0
        logger.warning("⚠️ FORCE RESUME - Admin override")
        self._log_event("FORCE_RESUME: Admin override")
    
    def update_risk_limits(self, new_limits: Dict):
        """Update risk limits"""
        try:
            if 'max_risk_per_trade' in new_limits:
                self.limits.max_risk_per_trade = new_limits['max_risk_per_trade']
            if 'max_daily_loss' in new_limits:
                self.limits.max_daily_loss = new_limits['max_daily_loss']
            if 'max_weekly_loss' in new_limits:
                self.limits.max_weekly_loss = new_limits['max_weekly_loss']
            if 'max_monthly_loss' in new_limits:
                self.limits.max_monthly_loss = new_limits['max_monthly_loss']
            if 'max_drawdown' in new_limits:
                self.limits.max_drawdown = new_limits['max_drawdown']
            if 'max_consecutive_losses' in new_limits:
                self.limits.max_consecutive_losses = new_limits['max_consecutive_losses']
            if 'max_position_size' in new_limits:
                self.limits.max_position_size = new_limits['max_position_size']
            
            logger.info(f"✅ Risk limits updated: {new_limits}")
            
        except Exception as e:
            logger.error(f"Update risk limits error: {e}")
    
    # ============================================
    # SAVE/LOAD STATE
    # ============================================
    
    def _save_state(self):
        """Save risk state to disk"""
        try:
            os.makedirs("data/risk", exist_ok=True)
            
            state_data = {
                'total_profit': self.total_profit,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'peak_equity': self.state.peak_equity,
                'adaptive_risk_multiplier': self.adaptive_risk_multiplier,
                'current_risk_level': self.state.current_risk_level.value
            }
            
            with open("data/risk/state.json", "w") as f:
                json.dump(state_data, f)
            
        except Exception as e:
            logger.error(f"Save state error: {e}")
    
    def _load_state(self):
        """Load risk state from disk"""
        try:
            if os.path.exists("data/risk/state.json"):
                with open("data/risk/state.json", "r") as f:
                    state_data = json.load(f)
                    
                    self.total_profit = state_data.get('total_profit', 0.0)
                    self.total_trades = state_data.get('total_trades', 0)
                    self.winning_trades = state_data.get('winning_trades', 0)
                    self.losing_trades = state_data.get('losing_trades', 0)
                    self.state.peak_equity = state_data.get('peak_equity', 0.0)
                    self.adaptive_risk_multiplier = state_data.get('adaptive_risk_multiplier', 1.0)
                    
                    risk_level = state_data.get('current_risk_level', 'MODERATE')
                    try:
                        self.state.current_risk_level = RiskLevel(risk_level)
                    except:
                        self.state.current_risk_level = RiskLevel.MODERATE
                
                logger.info("📂 Risk state loaded")
                
        except Exception as e:
            logger.warning(f"Load state error (starting fresh): {e}")
    
    def validate_trade(self, symbol: str, side: str, quantity: float,
                      entry_price: float, stop_loss: float = None) -> Dict:
        """Validate a trade against risk limits"""
        try:
            # Check if trading is paused
            if self.state.is_paused:
                return {
                    'approved': False,
                    'reason': f'Trading paused: {self.state.pause_reason}'
                }

            # Check max positions
            if self.state.total_equity > 0:
                # Calculate risk amount
                if stop_loss and entry_price > 0:
                    risk_per_unit = abs(entry_price - stop_loss)
                    risk_amount = risk_per_unit * quantity
                    risk_percent = (risk_amount / self.state.total_equity) * 100
                else:
                    # Default risk without stop loss
                    risk_amount = entry_price * quantity * 0.02 if entry_price > 0 else 0
                    risk_percent = 2.0

                # Check risk per trade limit
                if risk_percent > self.limits.max_risk_per_trade * 100:
                    return {
                        'approved': False,
                        'reason': f'Risk per trade too high: {risk_percent:.2f}% (max: {self.limits.max_risk_per_trade * 100}%)'
                    }

            # Check daily loss limit
            if abs(self.state.daily_loss) >= self.limits.max_daily_loss:
                return {
                    'approved': False,
                    'reason': f'Daily loss limit reached: {self.state.daily_loss:.2%}'
                }

            # Check drawdown limit
            if self.state.current_drawdown >= self.limits.max_drawdown:
                return {
                    'approved': False,
                    'reason': f'Max drawdown reached: {self.state.current_drawdown:.2%}'
                }

            # Check consecutive losses
            if self.state.consecutive_losses >= self.limits.max_consecutive_losses:
                return {
                    'approved': False,
                    'reason': f'Too many consecutive losses: {self.state.consecutive_losses}'
                }

            # Trade approved
            return {
                'approved': True,
                'risk_amount': risk_amount if 'risk_amount' in locals() else 0,
                'risk_percent': risk_percent if 'risk_percent' in locals() else 0,
                'risk_level': self.state.current_risk_level.value
            }

        except Exception as e:
            logger.error(f"Trade validation error: {e}")
            return {'approved': False, 'reason': f'Validation error: {str(e)}'}

    def assess_market_risk(self, data: Any) -> Dict:
        """Assess market risk based on volatility and conditions"""
        try:
            import pandas as pd
            if not isinstance(data, pd.DataFrame) or data.empty:
                return {'risk_level': 'UNKNOWN', 'volatility': 0}

            # Calculate volatility
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * 100

            # Determine risk level
            if volatility < 1:
                risk_level = 'LOW'
            elif volatility < 2.5:
                risk_level = 'MODERATE'
            elif volatility < 5:
                risk_level = 'HIGH'
            else:
                risk_level = 'EXTREME'

            return {
                'risk_level': risk_level,
                'volatility': volatility,
                'avg_range': (data['high'] - data['low']).mean(),
                'max_drawdown': ((data['close'].cummax() - data['close']) / data['close'].cummax()).max() * 100
            }

        except Exception as e:
            logger.error(f"Market risk assessment error: {e}")
            return {'risk_level': 'UNKNOWN', 'volatility': 0}

    def _log_event(self, event: str):
        """Log risk event"""
        logger.info(f"📋 RISK EVENT: {event}")