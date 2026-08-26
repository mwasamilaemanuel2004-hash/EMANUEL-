"""
BOTS PACKAGE
All trading bots for ESMH.TRADE platform (13 bots across Forex/Crypto/Stocks/Metals/Commodities)
"""

from .base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality, BotState
from .forex.trend_follower import TrendFollowerBot
from .forex.forex_scapler import ForexScalperBot
from .forex.smart_money import SmartMoneyBot
from .forex.breakout import BreakoutBot
from .forex.news_bot import NewsBot
from .crypto.arbitrage_bot import ArbitrageBot
from .crypto.scalper_bot import CryptoScalperBot
from .crypto.dca_bot import DcaBot
from .crypto.grib_bot import GridBot
from .crypto.whale_bot import WhaleBot
from .stock_analyzer import AIStockAnalyzerBot
from .metals_bot import MetalsBot
from .commodities_bot import CommoditiesBot

__all__ = [
    "BaseBot", "TradeSignal", "SignalStrength", "TradeQuality", "BotState",
    "TrendFollowerBot", "ForexScalperBot", "SmartMoneyBot", "BreakoutBot", "NewsBot",
    "ArbitrageBot", "CryptoScalperBot", "DcaBot", "GridBot", "WhaleBot",
    "AIStockAnalyzerBot", "MetalsBot", "CommoditiesBot",
]
