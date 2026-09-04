# backend/app/models/user.py
"""
ESMH.TRADE - User Model
Advanced User Model with Enterprise Security & Features
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

# SQLAlchemy imports
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Boolean, 
    DateTime, 
    Text, 
    Float, 
    JSON, 
    UniqueConstraint, 
    CheckConstraint, 
    Index
)
from sqlalchemy.sql import func

# Database Base
from ..database import Base

# Standard libraries
import logging
import json
import base64
import hashlib
import hmac
import os
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== ENUMS ====================
class KYCStatus(str, Enum):
    """KYC Verification Status"""
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class AccountTier(str, Enum):
    """User Account Tier"""
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    VIP = "VIP"


class APIKeyStatus(str, Enum):
    """API Key Status"""
    ACTIVE = "ACTIVE"
    ROTATED = "ROTATED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


# ==================== ENCRYPTION HELPER ====================
class APIKeyEncryption:
    """API Key encryption using standard libraries only"""
    
    @staticmethod
    def _get_key() -> bytes:
        """Get encryption key from environment"""
        key_str = os.environ.get('API_KEY_ENCRYPTION_KEY', 'ESMH_TRADE_SECURE_KEY_2024')
        return hashlib.sha256(key_str.encode()).digest()
    
    @staticmethod
    def encrypt(api_key: str) -> str:
        """Encrypt API key"""
        if not api_key:
            return None
        
        try:
            key = APIKeyEncryption._get_key()
            iv = os.urandom(16)
            
            # XOR encryption
            plaintext = api_key.encode()
            encrypted = bytearray()
            
            for i, byte in enumerate(plaintext):
                key_byte = key[i % len(key)]
                iv_byte = iv[i % len(iv)]
                encrypted.append(byte ^ key_byte ^ iv_byte)
            
            # HMAC for integrity
            hmac_hash = hmac.new(key, bytes(encrypted), hashlib.sha256).digest()
            
            # Combine: iv + hmac + encrypted
            combined = iv + hmac_hash[:16] + bytes(encrypted)
            
            return base64.b64encode(combined).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return base64.b64encode(api_key.encode()).decode()
    
    @staticmethod
    def decrypt(encrypted_key: str) -> str:
        """Decrypt API key"""
        if not encrypted_key:
            return None
        
        try:
            key = APIKeyEncryption._get_key()
            
            # Decode base64
            combined = base64.b64decode(encrypted_key.encode())
            
            # Extract components
            iv = combined[:16]
            stored_hmac = combined[16:32]
            encrypted_data = combined[32:]
            
            # Verify HMAC
            calculated_hmac = hmac.new(key, encrypted_data, hashlib.sha256).digest()[:16]
            if not hmac.compare_digest(stored_hmac, calculated_hmac):
                logger.warning("HMAC verification failed")
                return None
            
            # XOR decryption
            decrypted = bytearray()
            for i, byte in enumerate(encrypted_data):
                key_byte = key[i % len(key)]
                iv_byte = iv[i % len(iv)]
                decrypted.append(byte ^ key_byte ^ iv_byte)
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            try:
                return base64.b64decode(encrypted_key.encode()).decode()
            except:
                return None


# ==================== MAIN USER MODEL ====================
class User(Base):
    """
    Advanced User Model with Enterprise Features
    
    Features:
    - Authentication & Security
    - API Keys Management (Encrypted)
    - Device & Session Management
    - Trading Activity & Performance
    - KYC/AML Compliance
    - Risk Management
    - Notification Preferences
    """
    
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('username', name='uq_user_username'),
        CheckConstraint('trust_score >= 0 AND trust_score <= 100', name='ck_trust_score'),
        CheckConstraint('commission_rate >= 0 AND commission_rate <= 100', name='ck_commission_rate'),
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_kyc_status', 'kyc_status'),
        Index('idx_user_referral_code', 'referral_code'),
    )
    
    # ==================== BASIC INFO ====================
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # ==================== PROFILE & STATUS ====================
    account_tier = Column(String(20), default=AccountTier.BRONZE.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_phone_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile Information
    phone_number = Column(String(20), nullable=True, unique=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default='UTC', nullable=False)
    
    # ==================== AUTHENTICATION ====================
    token = Column(String(500), nullable=True, unique=True)
    refresh_token = Column(String(500), nullable=True, unique=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # 2FA - TOTP
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(100), nullable=True)
    two_factor_backup_codes = Column(Text, nullable=True)
    
    # 2FA - Email
    is_2fa_email_enabled = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(100), nullable=True)
    
    # Account Security
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_failed_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # ==================== API KEYS (ENCRYPTED) ====================
    # Binance
    binance_api_key_encrypted = Column(Text, nullable=True)
    binance_secret_key_encrypted = Column(Text, nullable=True)
    binance_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    binance_api_key_rotated_at = Column(DateTime, nullable=True)
    binance_api_key_last_used = Column(DateTime, nullable=True)
    
    # Bybit
    bybit_api_key_encrypted = Column(Text, nullable=True)
    bybit_secret_key_encrypted = Column(Text, nullable=True)
    bybit_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    bybit_api_key_rotated_at = Column(DateTime, nullable=True)
    bybit_api_key_last_used = Column(DateTime, nullable=True)
    
    # KuCoin
    kucoin_api_key_encrypted = Column(Text, nullable=True)
    kucoin_secret_key_encrypted = Column(Text, nullable=True)
    kucoin_passphrase_encrypted = Column(Text, nullable=True)
    kucoin_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    kucoin_api_key_rotated_at = Column(DateTime, nullable=True)
    
    # OKX
    okx_api_key_encrypted = Column(Text, nullable=True)
    okx_secret_key_encrypted = Column(Text, nullable=True)
    okx_passphrase_encrypted = Column(Text, nullable=True)
    okx_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    okx_api_key_rotated_at = Column(DateTime, nullable=True)
    
    # Coinbase
    coinbase_api_key_encrypted = Column(Text, nullable=True)
    coinbase_secret_key_encrypted = Column(Text, nullable=True)
    coinbase_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    coinbase_api_key_rotated_at = Column(DateTime, nullable=True)
    
    # API Rate Limiting
    api_calls_today = Column(Integer, default=0, nullable=False)
    api_calls_limit = Column(Integer, default=10000, nullable=False)
    last_api_call = Column(DateTime, nullable=True)
    
    # ==================== TRADING SETTINGS ====================
    default_risk_percent = Column(Float, default=1.5, nullable=False)
    default_take_profit = Column(Float, default=2.0, nullable=False)
    default_stop_loss = Column(Float, default=0.8, nullable=False)
    max_position_size = Column(Float, default=5000.0, nullable=False)
    max_daily_loss = Column(Float, default=5000.0, nullable=False)
    max_open_positions = Column(Integer, default=10, nullable=False)
    default_timeframe = Column(String(20), default="1h", nullable=False)
    default_currency = Column(String(10), default="USD", nullable=False)
    
    # Risk Limits
    is_risk_limited = Column(Boolean, default=False, nullable=False)
    daily_loss_today = Column(Float, default=0.0, nullable=False)
    risk_limit_reset_at = Column(DateTime, nullable=True)
    
    # ==================== DEVICE MANAGEMENT ====================
    trusted_devices = Column(JSON, nullable=True)
    device_count = Column(Integer, default=0, nullable=False)
    last_device_fingerprint = Column(String(255), nullable=True)
    active_sessions = Column(JSON, nullable=True)
    
    # ==================== TRACKING & AUDIT ====================
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    last_login_user_agent = Column(String(500), nullable=True)
    last_login_device = Column(String(255), nullable=True)
    
    # Activity
    total_logins = Column(Integer, default=0, nullable=False)
    suspicious_activity_count = Column(Integer, default=0, nullable=False)
    
    # ==================== KYC & COMPLIANCE ====================
    kyc_status = Column(String(20), default=KYCStatus.PENDING.value, nullable=False)
    kyc_submitted_at = Column(DateTime, nullable=True)
    kyc_verified_at = Column(DateTime, nullable=True)
    kyc_rejection_reason = Column(Text, nullable=True)
    
    kyc_id_document_url = Column(String(500), nullable=True)
    kyc_id_document_type = Column(String(50), nullable=True)
    kyc_id_document_verified = Column(Boolean, default=False, nullable=False)
    
    kyc_proof_of_residence_url = Column(String(500), nullable=True)
    kyc_proof_of_residence_verified = Column(Boolean, default=False, nullable=False)
    
    kyc_selfie_url = Column(String(500), nullable=True)
    kyc_selfie_verified = Column(Boolean, default=False, nullable=False)
    
    country_of_residence = Column(String(2), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    pep_status = Column(Boolean, default=False, nullable=False)
    sanctions_check_passed = Column(Boolean, default=False, nullable=False)
    
    # ==================== TRUST & REPUTATION ====================
    trust_score = Column(Integer, default=0, nullable=False)
    reputation_score = Column(Float, default=0.0, nullable=False)
    verified_trades = Column(Integer, default=0, nullable=False)
    
    # ==================== TRADING STATISTICS ====================
    total_trades = Column(Integer, default=0, nullable=False)
    total_winning_trades = Column(Integer, default=0, nullable=False)
    total_losing_trades = Column(Integer, default=0, nullable=False)
    total_volume = Column(Float, default=0.0, nullable=False)
    total_profit_loss = Column(Float, default=0.0, nullable=False)
    
    win_rate = Column(Float, default=0.0, nullable=False)
    profit_factor = Column(Float, default=0.0, nullable=False)
    best_trade = Column(Float, default=0.0, nullable=False)
    worst_trade = Column(Float, default=0.0, nullable=False)
    average_trade = Column(Float, default=0.0, nullable=False)
    max_drawdown = Column(Float, default=0.0, nullable=False)
    
    # ==================== PORTFOLIO ====================
    total_balance = Column(Float, default=0.0, nullable=False)
    available_balance = Column(Float, default=0.0, nullable=False)
    reserved_balance = Column(Float, default=0.0, nullable=False)
    total_equity = Column(Float, default=0.0, nullable=False)
    portfolio_currency = Column(String(10), default='USD', nullable=False)
    crypto_wallets = Column(JSON, nullable=True)
    
    # ==================== COMMISSION & REFERRAL ====================
    commission_rate = Column(Float, default=0.0, nullable=False)
    total_commission = Column(Float, default=0.0, nullable=False)
    pending_commission = Column(Float, default=0.0, nullable=False)
    
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    referral_count = Column(Integer, default=0, nullable=False)
    referral_earnings = Column(Float, default=0.0, nullable=False)
    
    # ==================== NOTIFICATIONS ====================
    notification_preferences = Column(JSON, nullable=True)
    email_notifications_enabled = Column(Boolean, default=True, nullable=False)
    sms_notifications_enabled = Column(Boolean, default=False, nullable=False)
    push_notifications_enabled = Column(Boolean, default=True, nullable=False)
    
    # ==================== METHODS ====================
    
    def is_account_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def can_login(self) -> bool:
        """Check if user can login"""
        return self.is_active and not self.is_account_locked()
    
    def is_2fa_configured(self) -> bool:
        """Check if 2FA is configured"""
        return self.is_2fa_enabled or self.is_2fa_email_enabled
    
    def is_kyc_complete(self) -> bool:
        """Check if KYC is complete"""
        return self.kyc_status == KYCStatus.APPROVED.value
    
    def can_trade(self) -> bool:
        """Check if user can trade"""
        return (self.is_active and 
                self.is_email_verified and 
                self.is_kyc_complete() and
                not self.is_account_locked())
    
    def get_available_trading_balance(self) -> float:
        """Get available trading balance"""
        return max(0, self.available_balance - self.reserved_balance)
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "account_tier": self.account_tier,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "is_verified": self.is_verified,
            "is_email_verified": self.is_email_verified,
            "is_phone_verified": self.is_phone_verified,
            "is_2fa_enabled": self.is_2fa_enabled,
            "phone_number": self.phone_number,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "timezone": self.timezone,
            "kyc_status": self.kyc_status,
            "trust_score": self.trust_score,
            "reputation_score": self.reputation_score,
            "default_risk_percent": self.default_risk_percent,
            "default_take_profit": self.default_take_profit,
            "default_stop_loss": self.default_stop_loss,
            "max_position_size": self.max_position_size,
            "max_daily_loss": self.max_daily_loss,
            "max_open_positions": self.max_open_positions,
            "default_timeframe": self.default_timeframe,
            "default_currency": self.default_currency,
            "commission_rate": self.commission_rate,
            "total_commission": self.total_commission,
            "referral_code": self.referral_code,
            "referral_count": self.referral_count,
            "total_trades": self.total_trades,
            "total_volume": self.total_volume,
            "total_profit_loss": self.total_profit_loss,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_balance": self.total_balance,
            "available_balance": self.available_balance,
            "total_equity": self.total_equity,
            "country_of_residence": self.country_of_residence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data.update({
                "api_keys": {
                    "binance": {
                        "status": self.binance_api_key_status,
                        "has_key": bool(self.binance_api_key_encrypted),
                        "last_used": self.binance_api_key_last_used.isoformat() if self.binance_api_key_last_used else None,
                    },
                    "bybit": {
                        "status": self.bybit_api_key_status,
                        "has_key": bool(self.bybit_api_key_encrypted),
                        "last_used": self.bybit_api_key_last_used.isoformat() if self.bybit_api_key_last_used else None,
                    },
                    "kucoin": {
                        "status": self.kucoin_api_key_status,
                        "has_key": bool(self.kucoin_api_key_encrypted),
                    },
                    "okx": {
                        "status": self.okx_api_key_status,
                        "has_key": bool(self.okx_api_key_encrypted),
                    },
                    "coinbase": {
                        "status": self.coinbase_api_key_status,
                        "has_key": bool(self.coinbase_api_key_encrypted),
                    }
                },
                "api_calls_today": self.api_calls_today,
                "api_calls_limit": self.api_calls_limit,
                "crypto_wallets": self.crypto_wallets,
                "notification_preferences": self.notification_preferences,
                "trusted_devices": self.trusted_devices,
                "active_sessions": self.active_sessions,
            })
        
        return data
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    def __str__(self) -> str:
        return f"{self.full_name or self.username} ({self.account_tier})"