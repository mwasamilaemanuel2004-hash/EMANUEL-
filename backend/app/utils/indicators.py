"""
Technical Indicators
- Moving Averages
- RSI, MACD
- Bollinger Bands
- Stochastic
"""

import pandas as pd
import numpy as np

class TechnicalIndicators:
    """Technical indicators calculation"""
    
    @staticmethod
    def moving_average(data: pd.Series, period: int):
        """Calculate moving average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14):
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series):
        """Calculate MACD"""
        exp1 = data.ewm(span=12, adjust=False).mean()
        exp2 = data.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

indicators = TechnicalIndicators()
