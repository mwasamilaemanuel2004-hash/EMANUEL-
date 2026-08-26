"""
FOREX BOTS PACKAGE
- Trend Follower, Scalper, Smart Money, Breakout, News
"""

from .trend_follower import TrendFollowerBot
from .forex_scapler import ForexScalperBot
from .smart_money import SmartMoneyBot
from .breakout import BreakoutBot
from .news_bot import NewsBot

__all__ = [
    "TrendFollowerBot",
    "ForexScalperBot",
    "SmartMoneyBot",
    "BreakoutBot",
    "NewsBot",
]
