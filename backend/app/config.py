"""
Configuration Management
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import field_validator
import os

class Settings(BaseSettings):
    """Application Settings"""
    
    # App
    APP_NAME: str = "ESMH.TRADE"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/estrade.db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Security
    ENCRYPTION_KEY: str = "your-encryption-key-change-this"
    
    # API Keys (from .env)
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() not in ('false', '0', 'no', 'off', 'release')
        return bool(v)

settings = Settings()
