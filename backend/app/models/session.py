"""
User Session Model - Track Active Sessions & Device Management
- Device fingerprinting
- Session security
- Location tracking
- Session timeout
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.sql import func
from ..database import Base


class Session(Base):
    """User Session Model"""
    
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Session Info
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), nullable=True, unique=True)
    
    # Device Info
    device_fingerprint = Column(String(255), nullable=True)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    browser_name = Column(String(100), nullable=True)
    browser_version = Column(String(50), nullable=True)
    os_name = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    
    # Location & IP
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    country = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    is_vpn = Column(Boolean, default=False, nullable=False)
    
    # Security
    is_active = Column(Boolean, default=True, nullable=False)
    is_trusted = Column(Boolean, default=False, nullable=False)
    requires_2fa = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_activity = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Additional Data
    user_agent = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if session is valid"""
        return self.is_active and not self.is_expired()
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<Session user_id={self.user_id} device={self.device_name}>"
