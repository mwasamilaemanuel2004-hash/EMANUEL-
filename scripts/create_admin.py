#!/usr/bin/env python3
"""
Create admin user script
Run this to create the initial admin user
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.models.user import User, AccountTier
from app.database import Base, engine, SessionLocal
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    db = SessionLocal()
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin
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
            available_balance=100000.0
        )
        
        db.add(admin)
        db.commit()
        print("Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
        print("CHANGE THIS PASSWORD IMMEDIATELY!")
        
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
