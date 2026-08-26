"""
BotContext — per-bot memory, preferences, and adaptive performance tracking.

Gives every bot CONTEXT (recent trades, regime fit, session lane, symbol
preference, win rate by regime/session) so it makes better decisions over
time. PURELY ADDITIVE: does not modify any existing bot class.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


class BotLane(Enum):
    """Trading lane / specialization for a bot."""
    TREND_FOLLOWING = "trend_following"
    SCALPING = "scalping"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SMART_MONEY = "smart_money"
    NEWS = "news"
    ARBITRAGE = "arbitrage"
    ACCUMULATION = "accumulation"
    GRID = "grid"
    WHALE_FOLLOW = "whale_follow"
    STOCK_FUNDAMENTAL = "stock_fundamental"
    METALS_MACRO = "metals_macro"
    COMMODITIES_SUPPLY = "commodities_supply"


@dataclass
class BotPreferences:
    """What a bot prefers to trade (lane, regime, sessions, assets)."""
    preferred_regimes: List[str] = field(default_factory=lambda: ["STRONG_TREND"])
    preferred_sessions: List[str] = field(default_factory=lambda: ["LONDON", "NEW_YORK"])
    preferred_assets: List[str] = field(default_factory=lambda: ["EURUSD", "GBPUSD"])
    preferred_lane: BotLane = BotLane.TREND_FOLLOWING
    min_confidence: float = 70.0
    max_risk_pct: float = 2.0


@dataclass
class TradeRecord:
    """One completed trade for the bot's memory."""
    timestamp: Any
    side: str
    entry: float
    exit_price: float
    pnl_pct: float
    regime: str
    session: str
    won: bool
    hold_bars: int


class BotContext:
    """
    Per-bot context: preferences + rolling memory of recent trades +
    adaptive performance (win rate by regime/session).
    Improves over time without modifying the bot class.
    """

    def __init__(self, bot_name: str, preferences: Optional[BotPreferences] = None):
        self.bot_name = bot_name
        self.prefs = preferences or BotPreferences()
        self.recent_trades: deque = deque(maxlen=100)
        self.recent_by_regime: Dict[str, deque] = {}
        self.recent_by_session: Dict[str, deque] = {}
        self.consecutive_losses = 0
        self.total_trades = 0
        self.total_wins = 0
        self._last_trade_time: Any = None

    def is_preferred_regime(self, regime: str) -> bool:
        return regime in self.prefs.preferred_regimes

    def is_preferred_session(self, session: str) -> bool:
        return session in self.prefs.preferred_sessions

    def record_trade(self, trade: TradeRecord) -> None:
        """Record a trade and update adaptive stats."""
        self.recent_trades.append(trade)
        self.recent_by_regime.setdefault(trade.regime, deque(maxlen=30)).append(trade)
        self.recent_by_session.setdefault(trade.session, deque(maxlen=30)).append(trade)
        self.total_trades += 1
        if trade.won:
            self.total_wins += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
        self._last_trade_time = trade.timestamp

    def win_rate(self, last_n: int = 30) -> float:
        """Overall recent win rate."""
        sub = list(self.recent_trades)[-last_n:]
        if not sub: return 0.0
        return sum(1 for t in sub if t.won) / len(sub)

    def win_rate_regime(self, regime: str, last_n: int = 20) -> Optional[float]:
        """Win rate in a specific regime. None if insufficient data."""
        sub = list(self.recent_by_regime.get(regime, []))[-last_n:]
        if len(sub) < 5: return None
        return sum(1 for t in sub if t.won) / len(sub)

    def win_rate_session(self, session: str, last_n: int = 20) -> Optional[float]:
        sub = list(self.recent_by_session.get(session, []))[-last_n:]
        if len(sub) < 5: return None
        return sum(1 for t in sub if t.won) / len(sub)

    def confidence_multiplier(self, regime: str, session: str) -> float:
        """
        ADAPTIVE: adjust confidence based on the bot's recent performance
        in this regime + session. Good performance -> boost; poor -> reduce.
        Returns multiplier 0.5 to 1.2.
        """
        mult = 1.0
        wr_r = self.win_rate_regime(regime)
        if wr_r is not None:
            if wr_r >= 0.7: mult *= 1.15
            elif wr_r <= 0.4: mult *= 0.7
        wr_s = self.win_rate_session(session)
        if wr_s is not None:
            if wr_s >= 0.7: mult *= 1.05
            elif wr_s <= 0.4: mult *= 0.85
        if self.consecutive_losses >= 3:
            mult *= 0.5
        return max(0.3, min(1.2, mult))

    def should_pause(self) -> bool:
        """Adaptive: pause bot if recent performance is bad or many losses."""
        if self.consecutive_losses >= 4:
            return True
        if self.total_trades >= 10 and self.win_rate(20) < 0.35:
            return True
        return False

    def summary(self) -> Dict[str, Any]:
        return {
            'bot': self.bot_name,
            'total_trades': self.total_trades,
            'win_rate': round(self.win_rate(), 3),
            'consecutive_losses': self.consecutive_losses,
            'preferred_regimes': self.prefs.preferred_regimes,
            'preferred_sessions': self.prefs.preferred_sessions,
        }
