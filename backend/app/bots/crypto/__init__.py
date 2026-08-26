"""
CRYPTO BOTS PACKAGE
- Arbitrage, Scalper, DCA, Grid, Whale
"""

from .arbitrage_bot import ArbitrageBot
from .scalper_bot import CryptoScalperBot
from .dca_bot import DcaBot
from .grib_bot import GridBot
from .whale_bot import WhaleBot

__all__ = [
    "ArbitrageBot",
    "CryptoScalperBot",
    "DcaBot",
    "GridBot",
    "WhaleBot",
]
