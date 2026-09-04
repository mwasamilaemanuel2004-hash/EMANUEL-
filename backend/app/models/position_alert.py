"""
ESH.TRADE - Position Alert Model
ULTRA ADVANCED EDITION
Real-time Position Alerts with Auto-Actions
"""

import uuid
import json
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Position Alert Types - EXPANDED"""
    # Price alerts
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CROSS_UP = "price_cross_up"
    PRICE_CROSS_DOWN = "price_cross_down"
    
    # PnL alerts
    PROFIT_TARGET = "profit_target"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    BREAKEVEN = "breakeven"
    
    # Risk alerts
    RISK_LIMIT = "risk_limit"
    MARGIN_CALL = "margin_call"
    LIQUIDATION = "liquidation"
    MAX_DRAWDOWN = "max_drawdown"
    CORRELATION = "correlation"
    VOLATILITY = "volatility"
    
    # Position management
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    PARTIAL_CLOSE = "partial_close"
    FULL_CLOSE = "full_close"
    
    # Execution alerts
    ORDER_FILLED = "order_filled"
    ORDER_PARTIAL = "order_partial"
    ORDER_REJECTED = "order_rejected"
    ORDER_EXPIRED = "order_expired"
    EXECUTION_ERROR = "execution_error"
    
    # Time-based alerts
    POSITION_EXPIRY = "position_expiry"
    TIME_BASED = "time_based"
    
    # Manual
    MANUAL = "manual"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Alert severity"""
    INFO = "info"
    LOW = "low"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    PENDING = "pending"
    TRIGGERED = "triggered"
    DISMISSED = "dismissed"
    EXPIRED = "expired"
    EXECUTED = "executed"
    FAILED = "failed"


class AutoAction(Enum):
    """Auto actions when alert triggers"""
    NONE = "none"
    CLOSE_POSITION = "close_position"
    PARTIAL_CLOSE = "partial_close"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    MOVE_STOP_LOSS = "move_stop_loss"
    MOVE_TAKE_PROFIT = "move_take_profit"
    SET_BREAKEVEN = "set_breakeven"
    REDUCE_SIZE = "reduce_size"
    INCREASE_SIZE = "increase_size"
    CANCEL_ORDERS = "cancel_orders"


class NotificationChannel(Enum):
    """Notification channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    PUSH = "push"
    WEBHOOK = "webhook"
    ALL = "all"


class PositionAlert:
    """
    ULTRA ADVANCED Position Alert Model
    """
    
    def __init__(self,
                 position_id: str,
                 user_id: str,
                 alert_type: AlertType,
                 condition: str,
                 severity: AlertSeverity = AlertSeverity.WARNING,
                 trigger_price: float = None,
                 trigger_pnl: float = None,
                 trigger_percent: float = None,
                 auto_action: AutoAction = AutoAction.NONE,
                 message: str = None):
        
        # FIX: Validate
        if not position_id:
            raise ValueError("position_id required")
        if not user_id:
            raise ValueError("user_id required")
        
        # Basic
        self.id = str(uuid.uuid4())
        self.position_id = position_id
        self.user_id = user_id
        self.alert_type = alert_type
        self.severity = severity
        self.status = AlertStatus.ACTIVE
        self.condition = condition
        
        # Trigger values
        self.trigger_price = trigger_price
        self.trigger_pnl = trigger_pnl
        self.trigger_percent = trigger_percent
        self.current_value: Optional[float] = None
        
        # Auto action
        self.auto_action = auto_action
        self.action_executed = False
        self.action_time: Optional[datetime] = None
        
        # Notification
        self.notified = False
        self.notification_sent_at: Optional[datetime] = None
        self.notification_channels: List[str] = [NotificationChannel.IN_APP.value]
        
        # Message
        self.message = message or self._generate_default_message()
        
        # Timestamps
        self.created_at = datetime.utcnow()
        self.triggered_at: Optional[datetime] = None
        self.expires_at: Optional[datetime] = None
        self.dismissed_at: Optional[datetime] = None
        
        # History
        self.history: List[Dict[str, Any]] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        self._add_history("created", f"Alert created: {alert_type.value}")
    
    def _generate_default_message(self) -> str:
        """Generate default alert message"""
        messages = {
            AlertType.PROFIT_TARGET: "Take profit target reached",
            AlertType.STOP_LOSS: "Stop loss triggered",
            AlertType.TRAILING_STOP: "Trailing stop hit",
            AlertType.BREAKEVEN: "Position at breakeven",
            AlertType.MARGIN_CALL: "Margin call warning",
            AlertType.LIQUIDATION: "Liquidation risk warning",
            AlertType.PRICE_ABOVE: f"Price above {self.trigger_price}",
            AlertType.PRICE_BELOW: f"Price below {self.trigger_price}",
        }
        return messages.get(self.alert_type, self.condition)
    
    def _add_history(self, action: str, description: str) -> None:
        """Add history entry"""
        self.history.append({
            'action': action,
            'description': description,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        if len(self.history) > 100:
            self.history = self.history[-100:]
    
    def check_condition(self, current_price: float = None, current_pnl: float = None,
                       current_percent: float = None) -> bool:
        """FIX: Check if alert condition is met"""
        try:
            with self._lock:
                if not self.is_active():
                    return False
                
                # Update current values
                if current_price is not None:
                    self.current_value = current_price
                elif current_pnl is not None:
                    self.current_value = current_pnl
                elif current_percent is not None:
                    self.current_value = current_percent
                
                # Check trigger
                triggered = False
                
                if self.trigger_price is not None and current_price is not None:
                    if self.alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_CROSS_UP]:
                        triggered = current_price >= self.trigger_price
                    elif self.alert_type in [AlertType.PRICE_BELOW, AlertType.PRICE_CROSS_DOWN]:
                        triggered = current_price <= self.trigger_price
                
                elif self.trigger_pnl is not None and current_pnl is not None:
                    if self.alert_type == AlertType.PROFIT_TARGET:
                        triggered = current_pnl >= self.trigger_pnl
                    elif self.alert_type == AlertType.STOP_LOSS:
                        triggered = current_pnl <= -abs(self.trigger_pnl)
                
                elif self.trigger_percent is not None and current_percent is not None:
                    triggered = abs(current_percent) >= abs(self.trigger_percent)
                
                if triggered:
                    self.trigger()
                
                return triggered
                
        except Exception as e:
            logger.error(f"Error checking condition: {e}")
            return False
    
    def trigger(self) -> bool:
        """FIX: Trigger alert"""
        try:
            with self._lock:
                if self.status != AlertStatus.ACTIVE:
                    return False
                
                self.status = AlertStatus.TRIGGERED
                self.triggered_at = datetime.utcnow()
                self._add_history("triggered", "Alert condition met")
                
                return True
                
        except Exception as e:
            logger.error(f"Error triggering: {e}")
            return False
    
    def dismiss(self) -> bool:
        """FIX: Dismiss alert"""
        try:
            with self._lock:
                if self.status not in [AlertStatus.ACTIVE, AlertStatus.PENDING]:
                    return False
                
                self.status = AlertStatus.DISMISSED
                self.dismissed_at = datetime.utcnow()
                self._add_history("dismissed", "Alert dismissed")
                
                return True
                
        except Exception as e:
            logger.error(f"Error dismissing: {e}")
            return False
    
    def mark_notified(self, channel: str = None) -> bool:
        """FIX: Mark as notified"""
        try:
            with self._lock:
                self.notified = True
                self.notification_sent_at = datetime.utcnow()
                
                if channel and channel not in self.notification_channels:
                    self.notification_channels.append(channel)
                
                self._add_history("notified", f"Notification sent via {channel or 'default'}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error marking notified: {e}")
            return False
    
    def execute_action(self) -> bool:
        """FIX: Execute auto action"""
        try:
            with self._lock:
                if self.action_executed:
                    return False
                
                if self.auto_action == AutoAction.NONE:
                    return False
                
                self.action_executed = True
                self.action_time = datetime.utcnow()
                self.status = AlertStatus.EXECUTED
                self._add_history("action_executed", f"Auto action: {self.auto_action.value}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return False
    
    def set_expiry(self, hours: int = 24) -> bool:
        """FIX: Set expiry"""
        try:
            with self._lock:
                self.expires_at = datetime.utcnow() + timedelta(hours=hours)
                return True
        except Exception as e:
            logger.error(f"Error setting expiry: {e}")
            return False
    
    def is_active(self) -> bool:
        """FIX: Check if active"""
        if self.status != AlertStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.status = AlertStatus.EXPIRED
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """FIX: Safe dict conversion"""
        try:
            return {
                'id': self.id,
                'position_id': self.position_id,
                'user_id': self.user_id,
                'alert_type': self.alert_type.value,
                'severity': self.severity.value,
                'status': self.status.value,
                'condition': self.condition,
                'trigger_price': self.trigger_price,
                'trigger_pnl': self.trigger_pnl,
                'trigger_percent': self.trigger_percent,
                'current_value': self.current_value,
                'auto_action': self.auto_action.value,
                'action_executed': self.action_executed,
                'notified': self.notified,
                'message': self.message,
                'created_at': self.created_at.isoformat(),
                'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None
            }
        except Exception as e:
            logger.error(f"Error converting to dict: {e}")
            return {'id': self.id}
    
    def __repr__(self) -> str:
        return f"<PositionAlert pos={self.position_id} type={self.alert_type.value} status={self.status.value}>"


class PositionAlertManager:
    """ULTRA ADVANCED Position Alert Manager"""
    
    def __init__(self):
        self.alerts: Dict[str, PositionAlert] = {}
        self._lock = threading.RLock()
    
    def create_alert(self, position_id: str, user_id: str, alert_type: AlertType,
                    condition: str, **kwargs) -> Optional[PositionAlert]:
        """FIX: Create alert"""
        try:
            alert = PositionAlert(
                position_id=position_id,
                user_id=user_id,
                alert_type=alert_type,
                condition=condition,
                **kwargs
            )
            
            with self._lock:
                self.alerts[alert.id] = alert
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    def get_alert(self, alert_id: str) -> Optional[PositionAlert]:
        """Get alert"""
        with self._lock:
            return self.alerts.get(alert_id)
    
    def get_position_alerts(self, position_id: str, active_only: bool = True) -> List[PositionAlert]:
        """FIX: Get position alerts"""
        with self._lock:
            alerts = [a for a in self.alerts.values() if a.position_id == position_id]
            if active_only:
                alerts = [a for a in alerts if a.is_active()]
            return alerts
    
    def get_user_alerts(self, user_id: str, active_only: bool = True) -> List[PositionAlert]:
        """Get user alerts"""
        with self._lock:
            alerts = [a for a in self.alerts.values() if a.user_id == user_id]
            if active_only:
                alerts = [a for a in alerts if a.is_active()]
            return alerts
    
    def check_alerts(self, position_id: str, current_price: float = None,
                    current_pnl: float = None) -> List[PositionAlert]:
        """FIX: Check all alerts for position"""
        triggered = []
        
        for alert in self.get_position_alerts(position_id):
            if alert.check_condition(current_price=current_price, current_pnl=current_pnl):
                triggered.append(alert)
        
        return triggered
    
    def dismiss_all(self, position_id: str) -> int:
        """Dismiss all position alerts"""
        count = 0
        for alert in self.get_position_alerts(position_id):
            if alert.dismiss():
                count += 1
        return count
    
    def cleanup(self) -> int:
        """Cleanup expired alerts"""
        count = 0
        with self._lock:
            expired = [
                aid for aid, a in self.alerts.items()
                if not a.is_active() and a.status in [AlertStatus.TRIGGERED, AlertStatus.DISMISSED, AlertStatus.EXPIRED]
            ]
            for aid in expired:
                del self.alerts[aid]
                count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        with self._lock:
            type_counts = {}
            status_counts = {}
            
            for alert in self.alerts.values():
                type_counts[alert.alert_type.value] = type_counts.get(alert.alert_type.value, 0) + 1
                status_counts[alert.status.value] = status_counts.get(alert.status.value, 0) + 1
            
            return {
                'total': len(self.alerts),
                'active': sum(1 for a in self.alerts.values() if a.is_active()),
                'triggered': sum(1 for a in self.alerts.values() if a.status == AlertStatus.TRIGGERED),
                'type_counts': type_counts,
                'status_counts': status_counts
            }


# Global manager
position_alert_manager = PositionAlertManager()