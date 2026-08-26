"""
BotLanes — route/lane assignment for the 13 bots.

Defines which lane (regime + session + asset class) each bot is best suited
for. The AgentDispatcher uses this to route signals to the right bot.
ADDITIVE: does not modify any bot class.
"""
from typing import Dict, List
from .bot_context import BotLane, BotPreferences


# Canonical mapping: bot name -> BotPreferences (lane + regime + session + assets)
DEFAULT_LANES: Dict[str, BotPreferences] = {
    "TrendFollowerBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "WEAK_TREND"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
        preferred_lane=BotLane.TREND_FOLLOWING,
        min_confidence=70.0,
    ),
    "ForexScalperBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "HIGH_VOLATILITY"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["EURUSD", "GBPUSD", "USDJPY"],
        preferred_lane=BotLane.SCALPING,
        min_confidence=75.0,
    ),
    "SmartMoneyBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "RANGE"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["EURUSD", "GBPUSD", "XAUUSD", "BTCUSDT"],
        preferred_lane=BotLane.SMART_MONEY,
        min_confidence=80.0,
    ),
    "BreakoutBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "RANGE"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["EURUSD", "GBPUSD", "BTCUSDT"],
        preferred_lane=BotLane.BREAKOUT,
        min_confidence=75.0,
    ),
    "NewsBot": BotPreferences(
        preferred_regimes=["HIGH_VOLATILITY", "STRONG_TREND"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["EURUSD", "XAUUSD", "BTCUSDT"],
        preferred_lane=BotLane.NEWS,
        min_confidence=80.0,
    ),
    "ArbitrageBot": BotPreferences(
        preferred_regimes=["RANGE", "LOW_VOLATILITY"],
        preferred_sessions=["LONDON", "NEW_YORK", "ASIAN"],
        preferred_assets=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        preferred_lane=BotLane.ARBITRAGE,
        min_confidence=90.0,
    ),
    "CryptoScalperBot": BotPreferences(
        preferred_regimes=["HIGH_VOLATILITY", "STRONG_TREND"],
        preferred_sessions=["NEW_YORK", "LONDON"],
        preferred_assets=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        preferred_lane=BotLane.SCALPING,
        min_confidence=75.0,
    ),
    "DcaBot": BotPreferences(
        preferred_regimes=["RANGE", "WEAK_TREND"],
        preferred_sessions=["ASIAN", "LONDON"],
        preferred_assets=["BTCUSDT", "ETHUSDT"],
        preferred_lane=BotLane.ACCUMULATION,
        min_confidence=60.0,
    ),
    "GridBot": BotPreferences(
        preferred_regimes=["RANGE"],
        preferred_sessions=["ASIAN", "LONDON"],
        preferred_assets=["BTCUSDT", "ETHUSDT", "XRPUSDT"],
        preferred_lane=BotLane.GRID,
        min_confidence=70.0,
    ),
    "WhaleBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "HIGH_VOLATILITY"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["BTCUSDT", "ETHUSDT", "DOGEUSDT"],
        preferred_lane=BotLane.WHALE_FOLLOW,
        min_confidence=80.0,
    ),
    "AIStockAnalyzerBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "WEAK_TREND"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["AAPL", "MSFT", "GOOGL", "NVDA"],
        preferred_lane=BotLane.STOCK_FUNDAMENTAL,
        min_confidence=70.0,
    ),
    "MetalsBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "HIGH_VOLATILITY"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["XAUUSD", "XAGUSD", "XPTUSD"],
        preferred_lane=BotLane.METALS_MACRO,
        min_confidence=75.0,
    ),
    "CommoditiesBot": BotPreferences(
        preferred_regimes=["STRONG_TREND", "WEAK_TREND"],
        preferred_sessions=["LONDON", "NEW_YORK"],
        preferred_assets=["WTI", "NATGAS", "WHEAT", "CORN"],
        preferred_lane=BotLane.COMMODITIES_SUPPLY,
        min_confidence=70.0,
    ),
}


class BotLaneAssigner:
    """Assigns bots to lanes and checks if a signal fits a bot's lane."""

    def __init__(self, custom_lanes: Dict[str, BotPreferences] = None):
        self.lanes = custom_lanes or DEFAULT_LANES

    def get_preferences(self, bot_name: str) -> BotPreferences:
        return self.lanes.get(bot_name, BotPreferences())

    def is_good_fit(self, bot_name: str, regime: str, session: str,
                    symbol: str = "") -> bool:
        """
        Return True if a signal in this regime/session/symbol is a good fit
        for the bot. Used to boost or suppress signals.
        """
        prefs = self.get_preferences(bot_name)
        if regime not in prefs.preferred_regimes:
            return False
        if session and session not in prefs.preferred_sessions:
            return False
        if symbol:
            # Loose match: any of the bot's preferred assets contains the symbol
            if not any(s in symbol for s in prefs.preferred_assets):
                return False
        return True

    def fit_score(self, bot_name: str, regime: str, session: str,
                  symbol: str = "") -> float:
        """0.0 (bad fit) to 1.0 (perfect fit)."""
        prefs = self.get_preferences(bot_name)
        score = 0.5
        if regime in prefs.preferred_regimes:
            score += 0.25
        if session and session in prefs.preferred_sessions:
            score += 0.15
        if symbol and any(s in symbol for s in prefs.preferred_assets):
            score += 0.1
        return min(1.0, score)
