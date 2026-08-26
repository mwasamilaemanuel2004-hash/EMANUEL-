"""
ESH.TRADE - Position Metrics Model
ULTRA ADVANCED EDITION
Time-series Position Metrics with Analytics
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


class MetricStatus(Enum):
    """Position status at snapshot"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"
    LIQUIDATED = "liquidated"
    CANCELLED = "cancelled"


class MarketRegime(Enum):
    """Market regime at snapshot"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    CHOPPY = "choppy"
    UNKNOWN = "unknown"


class PositionMetrics:
    """
    ULTRA ADVANCED Position Metrics Model
    Records historical snapshots for analytics
    """
    
    def __init__(self,
                 position_id: str,
                 user_id: str,
                 symbol: str,
                 open_volume: float,
                 current_price: float,
                 unrealized_pnl: float = 0.0):
        
        # FIX: Validate
        if not position_id:
            raise ValueError("position_id required")
        if not user_id:
            raise ValueError("user_id required")
        if not symbol:
            raise ValueError("symbol required")
        if open_volume <= 0:
            raise ValueError("open_volume must be positive")
        if current_price <= 0:
            raise ValueError("current_price must be positive")
        
        # Basic
        self.id = str(uuid.uuid4())
        self.position_id = position_id
        self.user_id = user_id
        self.snapshot_time = datetime.utcnow()
        
        # Position data
        self.symbol = symbol.upper()
        self.open_volume = float(open_volume)
        self.current_price = float(current_price)
        self.current_value = open_volume * current_price
        
        # PnL
        self.unrealized_pnl = float(unrealized_pnl)
        self.unrealized_pnl_percent = (unrealized_pnl / (open_volume * current_price) * 100) if (open_volume * current_price) > 0 else 0
        
        # Extremes
        self.max_profit = max(0.0, unrealized_pnl)
        self.max_drawdown = min(0.0, unrealized_pnl)
        
        # Risk
        self.risk_reward_ratio: Optional[float] = None
        self.portfolio_weight: Optional[float] = None
        
        # Status
        self.status = MetricStatus.OPEN
        self.is_hedged = False
        
        # Market context
        self.volatility: Optional[float] = None
        self.volume: Optional[float] = None
        self.market_regime: Optional[MarketRegime] = None
        
        # Entry info
        self.entry_price: float = current_price
        self.entry_time: Optional[datetime] = None
        
        # Hash for integrity
        self.hash = self._generate_hash()
        
        # Thread safety
        self._lock = threading.RLock()
    
    def _generate_hash(self) -> str:
        """Generate integrity hash"""
        data = json.dumps({
            'position_id': self.position_id,
            'snapshot_time': self.snapshot_time.isoformat(),
            'symbol': self.symbol,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def update_snapshot(self, current_price: float, unrealized_pnl: float = None) -> bool:
        """FIX: Update snapshot with new data"""
        try:
            with self._lock:
                if current_price <= 0:
                    return False
                
                self.current_price = current_price
                self.current_value = self.open_volume * current_price
                
                if unrealized_pnl is not None:
                    self.unrealized_pnl = unrealized_pnl
                else:
                    self.unrealized_pnl = (current_price - self.entry_price) * self.open_volume
                
                self.unrealized_pnl_percent = (self.unrealized_pnl / self.current_value * 100) if self.current_value > 0 else 0
                
                # Update extremes
                if self.unrealized_pnl > self.max_profit:
                    self.max_profit = self.unrealized_pnl
                if self.unrealized_pnl < self.max_drawdown:
                    self.max_drawdown = self.unrealized_pnl
                
                self.snapshot_time = datetime.utcnow()
                self.hash = self._generate_hash()
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating snapshot: {e}")
            return False
    
    def set_entry_info(self, entry_price: float, entry_time: datetime) -> None:
        """FIX: Set entry info"""
        try:
            self.entry_price = entry_price
            self.entry_time = entry_time
        except Exception as e:
            logger.error(f"Error setting entry info: {e}")
    
    def set_market_context(self, volatility: float = None, volume: float = None,
                          market_regime: MarketRegime = None) -> None:
        """FIX: Set market context"""
        try:
            if volatility is not None:
                self.volatility = volatility
            if volume is not None:
                self.volume = volume
            if market_regime is not None:
                self.market_regime = market_regime
        except Exception as e:
            logger.error(f"Error setting market context: {e}")
    
    def set_risk_metrics(self, risk_reward_ratio: float = None, portfolio_weight: float = None) -> None:
        """FIX: Set risk metrics"""
        try:
            self.risk_reward_ratio = risk_reward_ratio
            self.portfolio_weight = portfolio_weight
        except Exception as e:
            logger.error(f"Error setting risk metrics: {e}")
    
    def verify_integrity(self) -> bool:
        """Verify data integrity"""
        return self.hash == self._generate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """FIX: Safe dict conversion"""
        try:
            return {
                'id': self.id,
                'position_id': self.position_id,
                'user_id': self.user_id,
                'snapshot_time': self.snapshot_time.isoformat(),
                'symbol': self.symbol,
                'open_volume': self.open_volume,
                'current_price': self.current_price,
                'current_value': self.current_value,
                'entry_price': self.entry_price,
                'unrealized_pnl': self.unrealized_pnl,
                'unrealized_pnl_percent': round(self.unrealized_pnl_percent, 4),
                'max_profit': self.max_profit,
                'max_drawdown': self.max_drawdown,
                'risk_reward_ratio': self.risk_reward_ratio,
                'portfolio_weight': self.portfolio_weight,
                'status': self.status.value,
                'is_hedged': self.is_hedged,
                'volatility': self.volatility,
                'volume': self.volume,
                'market_regime': self.market_regime.value if self.market_regime else None,
                'hash': self.hash
            }
        except Exception as e:
            logger.error(f"Error converting to dict: {e}")
            return {'id': self.id}
    
    def __repr__(self) -> str:
        return f"<PositionMetrics pos={self.position_id} pnl={self.unrealized_pnl}>"


class PositionMetricsManager:
    """ULTRA ADVANCED Position Metrics Manager"""
    
    def __init__(self):
        self.metrics: Dict[str, PositionMetrics] = {}
        self._lock = threading.RLock()
    
    def create_snapshot(self, position_id: str, user_id: str, symbol: str,
                       open_volume: float, current_price: float,
                       unrealized_pnl: float = 0.0) -> Optional[PositionMetrics]:
        """FIX: Create snapshot"""
        try:
            metric = PositionMetrics(
                position_id=position_id,
                user_id=user_id,
                symbol=symbol,
                open_volume=open_volume,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl
            )
            
            with self._lock:
                self.metrics[metric.id] = metric
            
            return metric
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return None
    
    def get_snapshot(self, metric_id: str) -> Optional[PositionMetrics]:
        """Get snapshot"""
        with self._lock:
            return self.metrics.get(metric_id)
    
    def get_position_metrics(self, position_id: str) -> List[PositionMetrics]:
        """FIX: Get all metrics for position"""
        with self._lock:
            return [m for m in self.metrics.values() if m.position_id == position_id]
    
    def get_user_metrics(self, user_id: str) -> List[PositionMetrics]:
        """Get user metrics"""
        with self._lock:
            return [m for m in self.metrics.values() if m.user_id == user_id]
    
    def get_position_stats(self, position_id: str) -> Dict[str, Any]:
        """FIX: Calculate position statistics"""
        metrics = self.get_position_metrics(position_id)
        
        if not metrics:
            return {}
        
        pnls = [m.unrealized_pnl for m in metrics]
        prices = [m.current_price for m in metrics]
        values = [m.current_value for m in metrics]
        
        return {
            'snapshots': len(metrics),
            'avg_pnl': round(sum(pnls) / len(pnls), 4),
            'max_profit': max(m.max_profit for m in metrics),
            'max_drawdown': min(m.max_drawdown for m in metrics),
            'avg_price': round(sum(prices) / len(prices), 4),
            'avg_value': round(sum(values) / len(values), 4),
            'volatility': self._calculate_volatility(prices),
            'first_snapshot': metrics[0].snapshot_time.isoformat(),
            'last_snapshot': metrics[-1].snapshot_time.isoformat()
        }
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        try:
            if len(prices) < 2:
                return 0.0
            
            returns = [
                (prices[i] - prices[i-1]) / prices[i-1]
                for i in range(1, len(prices))
                if prices[i-1] > 0
            ]
            
            return round(statistics.stdev(returns), 6) if returns else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def cleanup(self, older_than: timedelta = timedelta(days=30)) -> int:
        """Cleanup old metrics"""
        count = 0
        cutoff = datetime.utcnow() - older_than
        
        with self._lock:
            old = [
                mid for mid, m in self.metrics.items()
                if m.snapshot_time < cutoff
            ]
            for mid in old:
                del self.metrics[mid]
                count += 1
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        with self._lock:
            return {
                'total_snapshots': len(self.metrics),
                'unique_positions': len(set(m.position_id for m in self.metrics.values())),
                'unique_users': len(set(m.user_id for m in self.metrics.values()))
            }


# Global manager
position_metrics_manager = PositionMetricsManager()