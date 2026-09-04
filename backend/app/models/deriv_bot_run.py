"""Persistence model for explainable Deriv analysis and backtest runs."""

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String
from sqlalchemy.sql import func

from ..database import Base


class DerivBotRun(Base):
    __tablename__ = "deriv_bot_runs"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(24), nullable=False, index=True)
    mode = Column(String(12), nullable=False, default="demo")
    strategy = Column(String(40), nullable=False)
    run_type = Column(String(20), nullable=False, default="plan")
    confidence = Column(Float, nullable=True)
    allowed = Column(Integer, nullable=False, default=0)
    request = Column(JSON, nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)