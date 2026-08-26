"""
Position Alert Model - Real-time Position Alerts
Triggers alerts for position-level events
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
)
from sqlalchemy.sql import func
from ..database import Base


class AlertType(str, Enum):
    """Alert Type"""
    PRICE_ALERT = "PRICE_ALERT"
    PROFIT_TARGET = "PROFIT_TARGET"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    BREAKEVEN = "BREAKEVEN"
    SCALE_IN = "SCALE_IN"
    SCALE_OUT = "SCALE_OUT"
    RISK_LIMIT = "RISK_LIMIT"
    MARGIN_CALL = "MARGIN_CALL"
    LIQUIDATION = "LIQUIDATION"
    CORRELATION_ALERT = "CORRELATION_ALERT"
    VOLATILITY_ALERT = "VOLATILITY_ALERT"
    EXECUTION_ALERT = "EXECUTION_ALERT"
    EXPIRY_ALERT = "EXPIRY_ALERT"
    MANUAL = "MANUAL"


class AlertSeverity(str, Enum):
    """Alert Severity"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Alert Status"""
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    DISMISSED = "DISMISSED"
    EXPIRED = "EXPIRED"


class PositionAlert(Base):
    """
    Position Alert Model - Position-level Alerts
    
    Tracks:
    - Price-based alerts
    - P&L-based alerts
    - Risk-based alerts
    - Execution alerts
    - Manual alerts
    """
    
    __tablename__ = "position_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Alert Type
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default=AlertSeverity.WARNING.value)
    status = Column(String(20), default=AlertStatus.ACTIVE.value)
    
    # Alert Condition
    condition = Column(String(255), nullable=False)  # "Price > 50000"
    condition_met = Column(Boolean, default=False)
    
    # Trigger Value
    trigger_price = Column(Float, nullable=True)
    trigger_pnl = Column(Float, nullable=True)
    trigger_percent = Column(Float, nullable=True)
    
    # Current Value
    current_value = Column(Float, nullable=True)
    
    # Actions
    auto_action = Column(String(100), nullable=True)  # "CLOSE_POSITION", "SCALE_OUT", etc.
    action_executed = Column(Boolean, default=False)
    action_time = Column(DateTime, nullable=True)
    
    # Notification
    notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    notification_channel = Column(String(50), nullable=True)  # EMAIL, SMS, PUSH
    
    # Description
    message = Column(String(500), nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Lifecycle
    created_at = Column(DateTime, server_default=func.now())
    triggered_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    
    def is_active(self) -> bool:
        """Check if alert is still active"""
        if self.status == AlertStatus.TRIGGERED.value:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def __repr__(self) -> str:
        return f"<PositionAlert pos={self.position_id} type={self.alert_type} status={self.status}>"
