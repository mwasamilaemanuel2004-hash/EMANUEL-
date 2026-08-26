"""
Audit Log Model - Comprehensive Logging & Compliance
- All user actions
- Security events
- Changes to sensitive data
- Compliance tracking
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.sql import func
from ..database import Base


class AuditEventType(str, Enum):
    """Audit Event Types"""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    FAILED_LOGIN = "FAILED_LOGIN"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    TWO_FA_ENABLED = "2FA_ENABLED"
    TWO_FA_DISABLED = "2FA_DISABLED"
    API_KEY_CREATED = "API_KEY_CREATED"
    API_KEY_ROTATED = "API_KEY_ROTATED"
    API_KEY_REVOKED = "API_KEY_REVOKED"
    TRADE_EXECUTED = "TRADE_EXECUTED"
    POSITION_CLOSED = "POSITION_CLOSED"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_VERIFIED = "KYC_VERIFIED"
    DEVICE_ADDED = "DEVICE_ADDED"
    DEVICE_REMOVED = "DEVICE_REMOVED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    UNKNOWN = "UNKNOWN"


class AuditSeverity(str, Enum):
    """Audit Event Severity"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditLog(Base):
    """Audit Log Model for Compliance & Security"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Event Info
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default=AuditSeverity.MEDIUM.value, nullable=False)
    
    # Details
    action = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Resource & Changes
    resource_type = Column(String(50), nullable=True)  # user, trade, position, etc.
    resource_id = Column(String(255), nullable=True)
    changes = Column(JSON, nullable=True)  # {"old": {}, "new": {}}
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(50), nullable=False)  # success, failure
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Compliance
    is_suspicious = Column(Boolean, default=False, nullable=False)
    requires_investigation = Column(Boolean, default=False, nullable=False)
    investigated = Column(Boolean, default=False, nullable=False)
    investigation_notes = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} event={self.event_type} user_id={self.user_id}>"
