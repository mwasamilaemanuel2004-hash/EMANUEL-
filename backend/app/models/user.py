# backend/app/models/user.py
"""
ESH.TRADE - User Model
Ina manage users, authentication, API keys, na settings
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    UniqueConstraint, CheckConstraint, Index, JSON
)
from sqlalchemy.sql import func
from ..database import Base
from pydantic import EmailStr, validator
from enum import Enum
from typing import Optional, Dict, List, Any


# ==================== ENUMS ====================
class KYCStatus(str, Enum):
    """KYC Verification Status"""
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class AccountTier(str, Enum):
    """User Account Tier/Level"""
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


# ==================== MAIN USER MODEL ====================
class User(Base):
    """
    Advanced User Model with Enterprise Features
    
    Tracks:
    - Authentication & Security
    - API Keys & Permissions
    - Device & Session Management
    - Trading Activity & Performance
    - Compliance & KYC Status
    - Risk Management Settings
    - Notification Preferences
    """
    
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('username', name='uq_user_username'),
        CheckConstraint('trust_score >= 0 AND trust_score <= 100', name='ck_trust_score'),
        CheckConstraint('commission_rate >= 0 AND commission_rate <= 100', name='ck_commission_rate'),
        CheckConstraint('default_risk_percent > 0', name='ck_default_risk'),
    )
    
    # ==================== PRIMARY FIELDS ====================
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
    
    # ==================== SECURITY & AUTHENTICATION ====================
    # Basic
    token = Column(String(500), nullable=True, unique=True)
    refresh_token = Column(String(500), nullable=True, unique=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # 2FA - Time-based One-Time Password (TOTP)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(32), nullable=True)
    two_factor_backup_codes = Column(Text, nullable=True)  # JSON: ["code1", "code2", ...]
    
    # 2FA - Email OTP
    is_2fa_email_enabled = Column(Boolean, default=False, nullable=False)
    
    # WebAuthn/FIDO2 Support
    is_webauthn_enabled = Column(Boolean, default=False, nullable=False)
    webauthn_credentials = Column(JSON, nullable=True)  # Store credential IDs and public keys
    
    # Account Security
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_failed_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # ==================== TRACKING & AUDIT ====================
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    last_login_user_agent = Column(String(500), nullable=True)
    last_login_device = Column(String(255), nullable=True)
    
    # Account Activity
    total_logins = Column(Integer, default=0, nullable=False)
    suspicious_activity_count = Column(Integer, default=0, nullable=False)
    
    # ==================== DEVICE MANAGEMENT ====================
    trusted_devices = Column(JSON, nullable=True)  # List of trusted device fingerprints
    device_count = Column(Integer, default=0, nullable=False)
    last_device_fingerprint = Column(String(255), nullable=True)
    
    # ==================== API KEY MANAGEMENT ====================
    # Binance
    encrypted_binance_api_key = Column(Text, nullable=True)
    encrypted_binance_secret_key = Column(Text, nullable=True)
    binance_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    binance_api_key_rotated_at = Column(DateTime, nullable=True)
    binance_api_permissions = Column(JSON, nullable=True)
    
    # Bybit
    encrypted_bybit_api_key = Column(Text, nullable=True)
    encrypted_bybit_secret_key = Column(Text, nullable=True)
    bybit_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    bybit_api_key_rotated_at = Column(DateTime, nullable=True)
    bybit_api_permissions = Column(JSON, nullable=True)
    
    # KuCoin
    encrypted_kucoin_api_key = Column(Text, nullable=True)
    encrypted_kucoin_secret_key = Column(Text, nullable=True)
    encrypted_kucoin_passphrase = Column(Text, nullable=True)
    kucoin_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    kucoin_api_key_rotated_at = Column(DateTime, nullable=True)
    kucoin_api_permissions = Column(JSON, nullable=True)
    
    # OKX
    encrypted_okx_api_key = Column(Text, nullable=True)
    encrypted_okx_secret_key = Column(Text, nullable=True)
    encrypted_okx_passphrase = Column(Text, nullable=True)
    okx_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    okx_api_key_rotated_at = Column(DateTime, nullable=True)
    okx_api_permissions = Column(JSON, nullable=True)
    
    # Coinbase
    encrypted_coinbase_api_key = Column(Text, nullable=True)
    encrypted_coinbase_secret_key = Column(Text, nullable=True)
    coinbase_api_key_status = Column(String(20), default=APIKeyStatus.ACTIVE.value, nullable=True)
    coinbase_api_key_rotated_at = Column(DateTime, nullable=True)
    coinbase_api_permissions = Column(JSON, nullable=True)
    
    # API Rate Limiting
    api_calls_today = Column(Integer, default=0, nullable=False)
    api_calls_limit = Column(Integer, default=10000, nullable=False)
    last_api_call = Column(DateTime, nullable=True)
    
    # ==================== KYC & COMPLIANCE ====================
    kyc_status = Column(String(20), default=KYCStatus.PENDING.value, nullable=False)
    kyc_submitted_at = Column(DateTime, nullable=True)
    kyc_verified_at = Column(DateTime, nullable=True)
    kyc_rejection_reason = Column(Text, nullable=True)
    
    # KYC Documents
    kyc_id_document_url = Column(String(500), nullable=True)
    kyc_id_document_type = Column(String(50), nullable=True)  # PASSPORT, DRIVER_LICENSE, ID_CARD
    kyc_id_document_verified = Column(Boolean, default=False, nullable=False)
    
    kyc_proof_of_residence_url = Column(String(500), nullable=True)
    kyc_proof_of_residence_verified = Column(Boolean, default=False, nullable=False)
    
    kyc_selfie_url = Column(String(500), nullable=True)
    kyc_selfie_verified = Column(Boolean, default=False, nullable=False)
    
    # Compliance Fields
    country_of_residence = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    date_of_birth = Column(DateTime, nullable=True)
    pep_status = Column(Boolean, default=False, nullable=False)  # Politically Exposed Person
    sanctions_check_passed = Column(Boolean, default=False, nullable=False)
    
    # ==================== TRUST & REPUTATION ====================
    trust_score = Column(Integer, default=0, nullable=False)  # 0-100
    reputation_score = Column(Float, default=0.0, nullable=False)  # 0-5.0
    verified_trades = Column(Integer, default=0, nullable=False)
    successful_trades_percent = Column(Float, default=0.0, nullable=False)
    
    # ==================== TRADING STATISTICS ====================
    total_trades = Column(Integer, default=0, nullable=False)
    total_winning_trades = Column(Integer, default=0, nullable=False)
    total_losing_trades = Column(Integer, default=0, nullable=False)
    total_volume = Column(Float, default=0.0, nullable=False)
    total_profit_loss = Column(Float, default=0.0, nullable=False)
    
    # Performance Metrics
    win_rate = Column(Float, default=0.0, nullable=False)
    profit_factor = Column(Float, default=0.0, nullable=False)
    best_trade = Column(Float, default=0.0, nullable=False)
    worst_trade = Column(Float, default=0.0, nullable=False)
    average_trade = Column(Float, default=0.0, nullable=False)
    max_consecutive_wins = Column(Integer, default=0, nullable=False)
    max_consecutive_losses = Column(Integer, default=0, nullable=False)
    max_drawdown = Column(Float, default=0.0, nullable=False)
    
    # ==================== PORTFOLIO & WALLET ====================
    total_balance = Column(Float, default=0.0, nullable=False)
    available_balance = Column(Float, default=0.0, nullable=False)
    reserved_balance = Column(Float, default=0.0, nullable=False)
    total_equity = Column(Float, default=0.0, nullable=False)
    portfolio_currency = Column(String(10), default='USD', nullable=False)
    
    # Wallet Addresses
    crypto_wallets = Column(JSON, nullable=True)  # {"BTC": "address", "ETH": "address"}
    
    # ==================== RISK MANAGEMENT ====================
    default_risk_percent = Column(Float, default=2.0, nullable=False)
    default_take_profit = Column(Float, default=1.5, nullable=False)
    default_stop_loss = Column(Float, default=0.5, nullable=False)
    max_position_size = Column(Float, default=1000.0, nullable=False)
    max_daily_loss = Column(Float, default=5000.0, nullable=False)
    max_open_positions = Column(Integer, default=10, nullable=False)
    
    # Risk Limits (for safety)
    is_risk_limited = Column(Boolean, default=False, nullable=False)
    daily_loss_today = Column(Float, default=0.0, nullable=False)
    risk_limit_reset_at = Column(DateTime, nullable=True)
    
    # ==================== COMMISSION & REFERRAL ====================
    commission_rate = Column(Float, default=0.0, nullable=False)  # 0-100 %
    total_commission_earned = Column(Float, default=0.0, nullable=False)
    total_commission_withdrawn = Column(Float, default=0.0, nullable=False)
    pending_commission = Column(Float, default=0.0, nullable=False)
    
    # Referral Program
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    referral_count = Column(Integer, default=0, nullable=False)
    referral_commission_rate = Column(Float, default=0.0, nullable=False)
    referral_earnings = Column(Float, default=0.0, nullable=False)
    
    # ==================== NOTIFICATIONS & PREFERENCES ====================
    notification_preferences = Column(JSON, nullable=True)  # {"email": True, "sms": False, "push": True}
    email_notifications_enabled = Column(Boolean, default=True, nullable=False)
    sms_notifications_enabled = Column(Boolean, default=False, nullable=False)
    push_notifications_enabled = Column(Boolean, default=True, nullable=False)
    
    # Notification Topics
    notify_on_trade_executed = Column(Boolean, default=True, nullable=False)
    notify_on_position_closed = Column(Boolean, default=True, nullable=False)
    notify_on_sl_hit = Column(Boolean, default=True, nullable=False)
    notify_on_tp_hit = Column(Boolean, default=True, nullable=False)
    notify_on_login = Column(Boolean, default=True, nullable=False)
    notify_on_kyc_update = Column(Boolean, default=True, nullable=False)
    
    # ==================== RELATIONSHIPS ====================
    # Will be added when other models are defined
    # sessions = relationship("Session", back_populates="user")
    # api_keys = relationship("APIKey", back_populates="user")
    # trades = relationship("Trade", back_populates="user")
    # positions = relationship("Position", back_populates="user")
    # devices = relationship("Device", back_populates="user")
    
    # ==================== METHODS ====================
    
    def is_account_locked(self) -> bool:
        """Check if account is locked due to failed login attempts"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def can_login(self) -> bool:
        """Check if user can login (not locked and active)"""
        return self.is_active and not self.is_account_locked()
    
    def is_2fa_configured(self) -> bool:
        """Check if any 2FA method is enabled"""
        return self.is_2fa_enabled or self.is_2fa_email_enabled or self.is_webauthn_enabled
    
    def is_kyc_complete(self) -> bool:
        """Check if KYC verification is complete and approved"""
        return self.kyc_status == KYCStatus.APPROVED.value
    
    def is_kyc_compliant(self) -> bool:
        """Check if user passed KYC and compliance checks"""
        return (self.is_kyc_complete() and 
                self.kyc_id_document_verified and
                self.sanctions_check_passed)
    
    def can_trade(self) -> bool:
        """Check if user can execute trades"""
        return (self.is_active and 
                self.is_email_verified and 
                self.is_kyc_complete() and
                not self.is_account_locked())
    
    def reached_api_limit(self) -> bool:
        """Check if user reached daily API call limit"""
        return self.api_calls_today >= self.api_calls_limit
    
    def has_hit_daily_loss_limit(self) -> bool:
        """Check if user has hit daily loss limit"""
        if not self.is_risk_limited:
            return False
        return self.daily_loss_today >= self.max_daily_loss
    
    def get_available_trading_balance(self) -> float:
        """Calculate available balance for trading"""
        return max(0, self.available_balance - self.reserved_balance)
    
    def get_account_status_summary(self) -> Dict[str, any]:
        """Get comprehensive account status"""
        return {
            "tier": self.account_tier,
            "is_active": self.is_active,
            "is_verified": self.is_email_verified,
            "kyc_status": self.kyc_status,
            "account_locked": self.is_account_locked(),
            "can_trade": self.can_trade(),
            "2fa_enabled": self.is_2fa_configured(),
            "trust_score": self.trust_score,
            "reputation_score": self.reputation_score,
        }
    
    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} email={self.email}>"
    
    def __str__(self) -> str:
        return f"{self.full_name or self.username} ({self.account_tier})"
