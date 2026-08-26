"""
Portfolio Model - User Portfolio Management
Tracks user's overall portfolio, allocation, and performance
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
)
from sqlalchemy.sql import func
from ..database import Base


class Portfolio(Base):
    """
    Portfolio Model - Aggregate Portfolio Tracking
    
    Tracks:
    - Total balance & equity
    - Asset allocation
    - Performance metrics
    - Risk metrics
    - Portfolio-level P&L
    """
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Portfolio Identity
    name = Column(String(255), default="Main Portfolio")
    portfolio_type = Column(String(50))  # LIVE, DEMO, BACKTESTING
    
    # Balance
    initial_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    reserved_balance = Column(Float, default=0.0)
    
    # Equity
    total_equity = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    
    # Performance
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Risk Metrics
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_percent = Column(Float, default=0.0)
    current_drawdown = Column(Float, default=0.0)
    
    # Asset Allocation
    allocation = Column(JSON, nullable=True)  # {"FOREX": 30%, "CRYPTO": 50%, "STOCK": 20%}
    open_positions_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<Portfolio user_id={self.user_id} equity={self.total_equity}>"
