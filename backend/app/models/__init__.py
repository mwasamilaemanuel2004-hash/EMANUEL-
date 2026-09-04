"""
ESH.TRADE - Database Models Package
ULTRA ADVANCED EDITION v5.0.0
All SQLAlchemy ORM models for ESMH.TRADE platform

Models:
- User: User account with security & compliance
- Trade: Ultra-advanced trade tracking with IATS support
- Position: Open position aggregation with risk management
- Portfolio: Portfolio management & analytics
- TradeSignal: IATS signal tracking & learning
- BotPerformance: Bot metrics & adaptation
- APIKey: Exchange API management
- Session: Active session tracking
- AuditLog: Compliance & audit logging
- Settings: System configuration management
- Token: Authentication token management
- Verification: User verification tracking
- KYC: Know Your Customer compliance
- Alert: System and user alerts
- Stock: Stock/asset information
- ScannerResult: Market scanner results
- PositionRisk: Position risk metrics
- PositionAlert: Position-specific alerts
- PositionMetrics: Position performance metrics
"""

# User Models
from .user import (
    User, UserRole, UserStatus, AccountTier, KYCStatus
)

# Trading Models
from .trade import (
    Trade, TradeSide, TradeStatus, TradeType, OrderType, 
    ExitReason, BotStrategy, AssetClass
)

# Position Models
from .position import (
    Position, PositionStatus, PositionType, HedgeStrategy, PositionMode
)
from .position_risk import PositionRisk
from .position_alert import (
    PositionAlert, AlertType as PositionAlertType, 
    AlertSeverity as PositionAlertSeverity, AlertStatus
)
from .position_metrics import PositionMetrics

# Portfolio & Analytics
from .portfolio import Portfolio

# Signal & Bot Models
from .trade_signal import (
    TradeSignal, SignalType, SignalSource
)
from .deriv_bot_run import DerivBotRun
from .bot_performance import BotPerformance

# Security & Management
from .api_key import (
    APIKey, ExchangeName, APIKeyStatus
)
from .session import Session, SessionStatus
from .token import Token, TokenType

# Compliance & Verification
from .audit_log import (
    AuditLog, AuditEventType, AuditSeverity
)
from .verification import Verification, VerificationType
from .kyc import KYC

# Alerts & Notifications
from .alert import Alert, AlertType, AlertSeverity

# Market Data
from .stock import Stock, StockType
from .scanner_result import ScannerResult, ScannerType

# System Configuration
from .settings import Settings, SettingType

__version__ = '5.0.0'

__all__ = [
    # User Models
    'User', 'UserRole', 'UserStatus', 'AccountTier', 'KYCStatus',
    
    # Trading Models
    'Trade', 'TradeSide', 'TradeStatus', 'TradeType', 'OrderType',
    'ExitReason', 'BotStrategy', 'AssetClass',
    
    # Position Models
    'Position', 'PositionStatus', 'PositionType', 'HedgeStrategy', 'PositionMode',
    'PositionRisk', 'PositionMetrics',
    'PositionAlert', 'PositionAlertType', 'PositionAlertSeverity', 'AlertStatus',
    
    # Portfolio & Analytics
    'Portfolio',
    
    # Signal & Bot Models
    'TradeSignal', 'SignalType', 'SignalSource',
    'BotPerformance',
    'DerivBotRun',
    
    # Security & Management
    'APIKey', 'ExchangeName', 'APIKeyStatus',
    'Session', 'SessionStatus',
    'Token', 'TokenType',
    
    # Compliance & Verification
    'AuditLog', 'AuditEventType', 'AuditSeverity',
    'Verification', 'VerificationType',
    'KYC',
    
    # Alerts & Notifications
    'Alert', 'AlertType', 'AlertSeverity',
    
    # Market Data
    'Stock', 'StockType',
    'ScannerResult', 'ScannerType',
    
    # System Configuration
    'Settings', 'SettingType',
]