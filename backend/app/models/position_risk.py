"""
ESH.TRADE - Position Risk Model
ULTRA ADVANCED DEBUGGED EDITION
Complete Risk Analysis System
"""

import uuid
import json
import hashlib
import logging
import threading
import statistics
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class RiskRating(Enum):
    """Risk ratings"""
    ULTRA_LOW = "ultra_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA_HIGH = "ultra_high"
    CRITICAL = "critical"


class RiskWarningType(Enum):
    """Risk warning types"""
    OVER_LEVERAGED = "over_leveraged"
    HIGH_CORRELATION = "high_correlation"
    HIGH_VOLATILITY = "high_volatility"
    CONCENTRATION = "concentration"
    LIQUIDATION_RISK = "liquidation_risk"
    MARGIN_CALL = "margin_call"
    STOP_LOSS_TOO_WIDE = "stop_loss_too_wide"
    TAKE_PROFIT_TOO_CLOSE = "take_profit_too_close"
    HIGH_VAR = "high_var"
    HIGH_CVAR = "high_cvar"


class PositionRisk:
    """
    ULTRA ADVANCED DEBUGGED Position Risk Model
    """
    
    def __init__(self, position_id: str, user_id: str):
        # FIX: Validate
        if not position_id:
            raise ValueError("position_id required")
        if not user_id:
            raise ValueError("user_id required")
        
        # Basic
        self.id = str(uuid.uuid4())
        self.position_id = position_id
        self.user_id = user_id
        
        # Value at Risk (VaR)
        self.var_95: Optional[float] = None
        self.var_99: Optional[float] = None
        self.var_updated_at: Optional[datetime] = None
        
        # Expected Shortfall (CVaR)
        self.cvar_95: Optional[float] = None
        self.cvar_99: Optional[float] = None
        
        # Greeks
        self.delta: Optional[float] = None
        self.gamma: Optional[float] = None
        self.vega: Optional[float] = None
        self.theta: Optional[float] = None
        
        # Market Risk
        self.beta: Optional[float] = None
        self.alpha: Optional[float] = None
        self.correlation_market: Optional[float] = None
        
        # Leverage Risk
        self.leverage: float = 1.0
        self.leverage_risk_score: Optional[float] = None
        self.is_over_leveraged: bool = False
        
        # Stress Test
        self.stress_loss_scenario_1: Optional[float] = None
        self.stress_loss_scenario_2: Optional[float] = None
        self.stress_loss_scenario_3: Optional[float] = None
        self.stress_test_date: Optional[datetime] = None
        
        # Sensitivity
        self.price_sensitivity: Optional[float] = None
        self.volatility_sensitivity: Optional[float] = None
        
        # Risk Rating
        self.risk_rating: Optional[RiskRating] = None
        self.risk_score: Optional[float] = None  # 0-100
        
        # Warnings
        self.has_risk_warnings: bool = False
        self.risk_warnings: List[str] = []
        
        # Position data
        self.position_value: float = 0.0
        self.entry_price: float = 0.0
        self.current_price: float = 0.0
        self.stop_loss: Optional[float] = None
        self.take_profit: Optional[float] = None
        
        # History
        self.risk_history: List[Dict[str, Any]] = []
        
        # Timestamps
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Calculate initial risk score
        self._calculate_risk_score()
    
    def _add_warning(self, warning: RiskWarningType) -> None:
        """FIX: Add warning if not exists"""
        try:
            if warning.value not in self.risk_warnings:
                self.risk_warnings.append(warning.value)
                self.has_risk_warnings = True
                
                self._add_history("warning_added", f"Warning: {warning.value}")
        except Exception as e:
            logger.error(f"Error adding warning: {e}")
    
    def _remove_warning(self, warning: RiskWarningType) -> None:
        """FIX: Remove warning"""
        try:
            if warning.value in self.risk_warnings:
                self.risk_warnings.remove(warning.value)
                
                if not self.risk_warnings:
                    self.has_risk_warnings = False
        except Exception as e:
            logger.error(f"Error removing warning: {e}")
    
    def _add_history(self, action: str, description: str) -> None:
        """FIX: Add history entry"""
        self.risk_history.append({
            'action': action,
            'description': description,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        if len(self.risk_history) > 100:
            self.risk_history = self.risk_history[-100:]
    
    def _calculate_risk_score(self) -> float:
        """FIX: Calculate comprehensive risk score 0-100"""
        try:
            score = 0.0
            factors = 0
            
            # Leverage factor (30%)
            if self.leverage > 1:
                leverage_factor = min(30, (self.leverage - 1) * 5)
                score += leverage_factor
                factors += 1
                
                if self.leverage > 5:
                    self._add_warning(RiskWarningType.OVER_LEVERAGED)
                    self.is_over_leveraged = True
            
            # VaR factor (25%)
            if self.var_95 is not None:
                var_factor = min(25, (self.var_95 / max(self.position_value, 1)) * 100)
                score += var_factor
                factors += 1
                
                if var_factor > 20:
                    self._add_warning(RiskWarningType.HIGH_VAR)
            
            # Correlation factor (20%)
            if self.correlation_market is not None:
                corr_factor = min(20, abs(self.correlation_market) * 20)
                score += corr_factor
                factors += 1
                
                if abs(self.correlation_market) > 0.7:
                    self._add_warning(RiskWarningType.HIGH_CORRELATION)
            
            # Volatility factor (15%)
            if self.volatility_sensitivity is not None:
                vol_factor = min(15, self.volatility_sensitivity * 100)
                score += vol_factor
                factors += 1
                
                if vol_factor > 12:
                    self._add_warning(RiskWarningType.HIGH_VOLATILITY)
            
            # Stop loss factor (10%)
            if self.stop_loss and self.entry_price > 0:
                stop_distance = abs(self.entry_price - self.stop_loss) / self.entry_price
                stop_factor = min(10, stop_distance * 1000)
                score += stop_factor
                factors += 1
                
                if stop_distance > 0.05:
                    self._add_warning(RiskWarningType.STOP_LOSS_TOO_WIDE)
            
            self.risk_score = round(min(100, score), 2)
            
            # Set rating
            self.risk_rating = self._get_rating(self.risk_score)
            
            self._add_history("score_calculated", f"Risk score: {self.risk_score}")
            
            return self.risk_score
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            self.risk_score = 50.0
            self.risk_rating = RiskRating.MEDIUM
            return 50.0
    
    def _get_rating(self, score: float) -> RiskRating:
        """FIX: Get rating from score"""
        try:
            if score < 10:
                return RiskRating.ULTRA_LOW
            elif score < 25:
                return RiskRating.LOW
            elif score < 50:
                return RiskRating.MEDIUM
            elif score < 75:
                return RiskRating.HIGH
            elif score < 90:
                return RiskRating.ULTRA_HIGH
            else:
                return RiskRating.CRITICAL
        except Exception:
            return RiskRating.MEDIUM
    
    def calculate_var(self, returns: List[float], confidence: float = 0.95) -> Optional[float]:
        """FIX: Calculate Value at Risk"""
        try:
            if not returns or len(returns) < 2:
                return None
            
            sorted_returns = sorted(returns)
            index = int((1 - confidence) * len(sorted_returns))
            index = max(0, min(index, len(sorted_returns) - 1))
            
            var = abs(sorted_returns[index] * self.position_value)
            
            if confidence == 0.95:
                self.var_95 = var
            elif confidence == 0.99:
                self.var_99 = var
            
            self.var_updated_at = datetime.utcnow()
            self._calculate_risk_score()
            
            return var
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return None
    
    def calculate_cvar(self, returns: List[float], confidence: float = 0.95) -> Optional[float]:
        """FIX: Calculate Expected Shortfall"""
        try:
            if not returns or len(returns) < 2:
                return None
            
            sorted_returns = sorted(returns)
            tail_size = max(1, int((1 - confidence) * len(sorted_returns)))
            tail_returns = sorted_returns[:tail_size]
            
            cvar = abs(statistics.mean(tail_returns) * self.position_value)
            
            if confidence == 0.95:
                self.cvar_95 = cvar
            elif confidence == 0.99:
                self.cvar_99 = cvar
            
            self._calculate_risk_score()
            
            return cvar
            
        except Exception as e:
            logger.error(f"Error calculating CVaR: {e}")
            return None
    
    def set_leverage(self, leverage: float) -> bool:
        """FIX: Set leverage"""
        try:
            if leverage <= 0:
                return False
            
            with self._lock:
                self.leverage = leverage
                self.leverage_risk_score = min(100, (leverage - 1) * 10)
                
                if leverage > 5:
                    self._add_warning(RiskWarningType.OVER_LEVERAGED)
                    self.is_over_leveraged = True
                else:
                    self._remove_warning(RiskWarningType.OVER_LEVERAGED)
                    self.is_over_leveraged = False
                
                self.last_updated = datetime.utcnow()
                self._calculate_risk_score()
                
                return True
                
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            return False
    
    def set_position_data(self, position_value: float, entry_price: float,
                         current_price: float, stop_loss: float = None,
                         take_profit: float = None) -> bool:
        """FIX: Set position data"""
        try:
            with self._lock:
                self.position_value = position_value
                self.entry_price = entry_price
                self.current_price = current_price
                self.stop_loss = stop_loss
                self.take_profit = take_profit
                
                self.last_updated = datetime.utcnow()
                self._calculate_risk_score()
                
                return True
                
        except Exception as e:
            logger.error(f"Error setting position data: {e}")
            return False
    
    def run_stress_test(self, scenarios: List[float] = None) -> Dict[str, float]:
        """FIX: Run stress test"""
        try:
            if scenarios is None:
                scenarios = [-0.05, -0.10, -0.20]  # 5%, 10%, 20% drops
            
            results = {}
            
            if len(scenarios) >= 1:
                self.stress_loss_scenario_1 = self.position_value * abs(scenarios[0])
                results['scenario_1'] = self.stress_loss_scenario_1
            
            if len(scenarios) >= 2:
                self.stress_loss_scenario_2 = self.position_value * abs(scenarios[1])
                results['scenario_2'] = self.stress_loss_scenario_2
            
            if len(scenarios) >= 3:
                self.stress_loss_scenario_3 = self.position_value * abs(scenarios[2])
                results['scenario_3'] = self.stress_loss_scenario_3
            
            self.stress_test_date = datetime.utcnow()
            self._add_history("stress_test", f"Stress test: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running stress test: {e}")
            return {}
    
    def calculate_sensitivities(self) -> Dict[str, float]:
        """FIX: Calculate price and volatility sensitivities"""
        try:
            if self.position_value > 0:
                self.price_sensitivity = self.position_value * 0.01  # 1% price move
                self.volatility_sensitivity = self.price_sensitivity * 0.5
            
            self.last_updated = datetime.utcnow()
            
            return {
                'price_sensitivity': self.price_sensitivity,
                'volatility_sensitivity': self.volatility_sensitivity
            }
            
        except Exception as e:
            logger.error(f"Error calculating sensitivities: {e}")
            return {}
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """FIX: Get risk summary"""
        try:
            return {
                'risk_score': self.risk_score,
                'risk_rating': self.risk_rating.value if self.risk_rating else None,
                'var_95': self.var_95,
                'var_99': self.var_99,
                'cvar_95': self.cvar_95,
                'cvar_99': self.cvar_99,
                'leverage': self.leverage,
                'is_over_leveraged': self.is_over_leveraged,
                'warnings': self.risk_warnings,
                'has_warnings': self.has_risk_warnings,
                'stress_loss_scenario_1': self.stress_loss_scenario_1,
                'stress_loss_scenario_2': self.stress_loss_scenario_2,
                'stress_loss_scenario_3': self.stress_loss_scenario_3
            }
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """FIX: Safe dict conversion"""
        try:
            return {
                'id': self.id,
                'position_id': self.position_id,
                'user_id': self.user_id,
                'risk_score': self.risk_score,
                'risk_rating': self.risk_rating.value if self.risk_rating else None,
                'var_95': self.var_95,
                'var_99': self.var_99,
                'cvar_95': self.cvar_95,
                'cvar_99': self.cvar_99,
                'leverage': self.leverage,
                'is_over_leveraged': self.is_over_leveraged,
                'risk_warnings': self.risk_warnings,
                'stress_loss_scenario_1': self.stress_loss_scenario_1,
                'stress_loss_scenario_2': self.stress_loss_scenario_2,
                'stress_loss_scenario_3': self.stress_loss_scenario_3,
                'price_sensitivity': self.price_sensitivity,
                'volatility_sensitivity': self.volatility_sensitivity,
                'last_updated': self.last_updated.isoformat()
            }
        except Exception as e:
            logger.error(f"Error converting to dict: {e}")
            return {'id': self.id}
    
    def __repr__(self) -> str:
        return f"<PositionRisk pos={self.position_id} score={self.risk_score}>"


class PositionRiskManager:
    """ULTRA ADVANCED Position Risk Manager"""
    
    def __init__(self):
        self.risks: Dict[str, PositionRisk] = {}
        self._lock = threading.RLock()
    
    def create_risk(self, position_id: str, user_id: str) -> Optional[PositionRisk]:
        """FIX: Create risk record"""
        try:
            with self._lock:
                # Check if exists
                for risk in self.risks.values():
                    if risk.position_id == position_id:
                        return risk
                
                risk = PositionRisk(position_id, user_id)
                self.risks[risk.id] = risk
                return risk
                
        except Exception as e:
            logger.error(f"Error creating risk: {e}")
            return None
    
    def get_risk(self, risk_id: str) -> Optional[PositionRisk]:
        """Get risk"""
        with self._lock:
            return self.risks.get(risk_id)
    
    def get_position_risk(self, position_id: str) -> Optional[PositionRisk]:
        """FIX: Get risk by position"""
        with self._lock:
            for risk in self.risks.values():
                if risk.position_id == position_id:
                    return risk
            return None
    
    def get_high_risk_positions(self, threshold: float = 75.0) -> List[PositionRisk]:
        """FIX: Get high risk positions"""
        with self._lock:
            return [
                r for r in self.risks.values()
                if r.risk_score and r.risk_score >= threshold
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """FIX: Get statistics"""
        try:
            with self._lock:
                scores = [r.risk_score for r in self.risks.values() if r.risk_score is not None]
                
                return {
                    'total': len(self.risks),
                    'avg_risk_score': round(statistics.mean(scores), 2) if scores else 0,
                    'high_risk_count': len(self.get_high_risk_positions()),
                    'over_leveraged': sum(1 for r in self.risks.values() if r.is_over_leveraged),
                    'with_warnings': sum(1 for r in self.risks.values() if r.has_risk_warnings)
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


# Global manager
position_risk_manager = PositionRiskManager()