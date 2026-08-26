"""
Bot Performance Model - Track Bot Metrics & Learning
Supports IATS adaptive selection and optimization
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
)
from sqlalchemy.sql import func
from ..database import Base


class BotPerformance(Base):
    """
    Bot Performance Model - Track Bot Statistics
    
    Records:
    - Bot performance metrics
    - Win rates per timeframe/asset
    - Strategy effectiveness
    - Learning data for IATS
    - Performance vs expected
    """
    
    __tablename__ = "bot_performances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Bot Identity
    bot_id = Column(String(100), nullable=False)
    bot_name = Column(String(255), nullable=False)
    bot_strategy = Column(String(50), nullable=False)
    bot_version = Column(String(50))
    
    # Scope
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=True)  # 1m, 5m, 15m, 1h, 4h, 1d
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=True)
    
    # Trade Statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # P&L Metrics
    total_pnl = Column(Float, default=0.0)
    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)  # Gross Profit / Gross Loss
    
    # Risk Metrics
    max_drawdown = Column(Float, default=0.0)
    max_consecutive_wins = Column(Integer, default=0)
    max_consecutive_losses = Column(Integer, default=0)
    
    # Performance vs Expected
    expected_win_rate = Column(Float, nullable=True)
    actual_vs_expected = Column(Float, nullable=True)
    
    # Sharpe Ratio / Risk-Adjusted Returns
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    
    # Strategy Effectiveness
    effectiveness_score = Column(Float, default=0.0)  # 0-100
    performance_percentile = Column(Float, nullable=True)  # vs historical
    
    # Learning Data for IATS
    best_time_of_day = Column(String(50), nullable=True)
    worst_time_of_day = Column(String(50), nullable=True)
    best_market_condition = Column(String(50), nullable=True)  # TRENDING, RANGING, etc.
    
    # Adaptations
    recommended_adaptations = Column(JSON, nullable=True)
    applied_adaptations = Column(JSON, nullable=True)
    adaptation_results = Column(JSON, nullable=True)
    
    # Status & Updates
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return (f"<BotPerformance bot={self.bot_name} symbol={self.symbol} "
                f"win_rate={self.win_rate:.2f}%>")
