"""
Database Initialization Script
Creates all database tables and initial data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import engine, Base, SessionLocal
from app.models.user import User, AccountTier
from app.models.trade import Trade, TradeStatus, TradeType, OrderType, BotStrategy, AssetClass
from app.models.position import Position
from app.models.portfolio import Portfolio
from app.models.trade_signal import TradeSignal
from app.models.deriv_bot_run import DerivBotRun
from app.models.bot_performance import BotPerformance
from app.models.api_key import APIKey
from app.models.session import Session
from app.models.audit_log import AuditLog
from passlib.context import CryptContext
from datetime import datetime
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    """Initialize database with tables and sample data"""
    db = SessionLocal()
    try:
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Creating admin user...")
            admin = User(
                username="admin",
                email="admin@esmh.trade",
                password_hash=pwd_context.hash("admin123"),
                full_name="ESMH Admin",
                account_tier=AccountTier.VIP.value,
                is_admin=True,
                is_verified=True,
                is_email_verified=True,
                trust_score=100,
                total_balance=100000.0,
                available_balance=100000.0,
                reserved_balance=0.0,
                total_equity=100000.0
            )
            db.add(admin)
            db.commit()
            print("Admin user created: admin / admin123")
            print("CHANGE THIS PASSWORD IMMEDIATELY!")
        
        # Create sample portfolio
        if not db.query(Portfolio).first():
            print("Creating sample portfolio...")
            portfolio = Portfolio(
                user_id=admin.id,
                name="Default Portfolio",
                initial_balance=100000.0,
                current_balance=100000.0,
                available_balance=100000.0,
                total_equity=100000.0
            )
            db.add(portfolio)
            db.commit()
            print("Sample portfolio created")
        
        print("\nDatabase initialized successfully!")
        print(f"Admin: admin@esmh.trade / admin123")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
