"""
Market Data Service
Real-time and historical market data management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np


class MarketDataService:
    """Service for market data operations"""
    
    def __init__(self):
        self.cache: Dict[str, pd.DataFrame] = {}
        self.cache_ttl = 60  # seconds
        self.last_update: Dict[str, datetime] = {}
    
    def get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get cached market data"""
        if symbol in self.cache:
            if symbol in self.last_update:
                if (datetime.now() - self.last_update[symbol]).total_seconds() < self.cache_ttl:
                    return self.cache[symbol]
        return None
    
    def cache_data(self, symbol: str, data: pd.DataFrame):
        """Cache market data"""
        self.cache[symbol] = data
        self.last_update[symbol] = datetime.now()
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic indicators from market data"""
        try:
            if data.empty or len(data) < 20:
                return {}
            
            close = data['close']
            
            indicators = {
                'sma_20': close.rolling(20).mean().iloc[-1],
                'sma_50': close.rolling(50).mean().iloc[-1],
                'ema_20': close.ewm(span=20, adjust=False).mean().iloc[-1],
                'rsi': self._calc_rsi(close).iloc[-1],
                'volatility': close.pct_change().std() * 100,
                'last_price': close.iloc[-1],
                'timestamp': datetime.now().isoformat()
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            return {}
    
    def _calc_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
