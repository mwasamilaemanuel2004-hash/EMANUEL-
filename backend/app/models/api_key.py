"""
API Key Model - Secure Management of Exchange API Keys
- Rotation tracking
- Permission management
- Audit logging
- Expiration handling
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class ExchangeName(str, Enum):
    """Supported Exchanges"""
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    KUCOIN = "KUCOIN"
    OKX = "OKX"
    COINBASE = "COINBASE"


class APIKeyStatus(str, Enum):
    """API Key Status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ROTATED = "ROTATED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class APIKey(Base):
    """API Key Management Model"""
    
    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint('user_id', 'exchange', name='uq_user_exchange'),
        Index('idx_user_id', 'user_id'),
        Index('idx_exchange', 'exchange'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Exchange Info
    exchange = Column(String(20), nullable=False)
    exchange_user_id = Column(String(255), nullable=True)  # User ID on exchange
    
    # Encrypted Keys
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_secret_key = Column(Text, nullable=False)
    encrypted_passphrase = Column(Text, nullable=True)  # For KuCoin, OKX
    
    # Status & Validation
    status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=False)
    is_testnet = Column(Boolean, default=False, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    last_validation = Column(DateTime, nullable=True)
    validation_error = Column(Text, nullable=True)
    
    # Permissions
    permissions = Column(JSON, nullable=True)  # {"spot": True, "margin": False, "futures": True}
    ip_restriction = Column(String(255), nullable=True)
    
    # Tracking
    rotation_count = Column(Integer, default=0, nullable=False)
    last_rotated_at = Column(DateTime, nullable=True)
    next_rotation_recommended = Column(DateTime, nullable=True)
    
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Activity
    last_used = Column(DateTime, nullable=True)
    total_requests = Column(Integer, default=0, nullable=False)
    
    # Audit Trail
    created_by = Column(String(255), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deletion_reason = Column(String(255), nullable=True)
    
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def should_rotate(self) -> bool:
        """Check if key should be rotated"""
        if self.next_rotation_recommended is None:
            return False
        return datetime.utcnow() > self.next_rotation_recommended
    
    def is_usable(self) -> bool:
        """Check if API key can be used"""
        return (self.status == APIKeyStatus.ACTIVE.value and 
                self.is_valid and 
                not self.is_expired())
    
    def __repr__(self) -> str:
        return f"<APIKey exchange={self.exchange} status={self.status}>"
