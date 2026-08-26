"""
AgentDispatcher — employs each bot as an AGENT with context, lane, and
adaptive performance. Routes signals to the right bot, boosts scores
when the bot is in its lane, and pauses underperforming agents.

ADDITIVE: does not modify any existing bot class. Works alongside the
existing MasterTradeFilter, SmartEntryEngine, and SM/CRT/TBS detectors.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .bot_context import BotContext, BotPreferences, TradeRecord
from .bot_lanes import BotLaneAssigner, DEFAULT_LANES
from .tbs_engine import session_multiplier, in_killzone


@dataclass
class DispatchResult:
    """Result of dispatching a signal to a bot-agent."""
    bot_name: str
    accepted: bool
    reason: str
    confidence: float
    adjusted_confidence: float
    regime: str
    session: str


class AgentDispatcher:
    """
    Employs the 13 bots as agents. Each agent has:
      - BotContext (memory + adaptive performance)
      - Lane (preferred regime/session/asset)
      - Pause/resume logic (bad recent performance -> pause)
    The dispatcher routes signals, adjusts confidence, and decides whether
    each agent is allowed to trade.
    """

    def __init__(self, custom_lanes: Dict[str, BotPreferences] = None):
        self.lanes_assigner = BotLaneAssigner(custom_lanes)
        self.contexts: Dict[str, BotContext] = {}
        for name, prefs in self.lanes_assigner.lanes.items():
            self.contexts[name] = BotContext(name, prefs)

    def get_context(self, bot_name: str) -> BotContext:
        return self.contexts.setdefault(
            bot_name, BotContext(bot_name, self.lanes_assigner.get_preferences(bot_name)))

    def get_session_name(self, ts) -> str:
        _, name = in_killzone(ts)
        return name or "OTHER"

    def dispatch(self, bot_name: str, regime: str, ts, symbol: str = "",
                 base_confidence: float = 70.0) -> DispatchResult:
        """
        Route a potential signal to a bot-agent. Returns whether the agent
        accepts and the adjusted confidence (lane fit + adaptive boost).
        """
        ctx = self.get_context(bot_name)
        session = self.get_session_name(ts)

        # 1) Adaptive pause: if the agent is underperforming, refuse
        if ctx.should_pause():
            return DispatchResult(bot_name, False, "agent_paused_poor_performance",
                                  base_confidence, 0.0, regime, session)

        # 2) Lane fit: does this regime/session/symbol fit the bot?
        fit = self.lanes_assigner.fit_score(bot_name, regime, session, symbol)
        if fit < 0.4:
            return DispatchResult(bot_name, False, f"bad_lane_fit(fit={fit:.2f})",
                                  base_confidence, 0.0, regime, session)

        # 3) Adaptive confidence multiplier (from context memory)
        mult = ctx.confidence_multiplier(regime, session)
        adjusted = base_confidence * fit * mult

        # 4) Lane preference multiplier
        if not ctx.is_preferred_regime(regime):
            adjusted *= 0.7

        return DispatchResult(
            bot_name=bot_name,
            accepted=adjusted >= ctx.prefs.min_confidence * 0.85,
            reason="accepted" if adjusted >= ctx.prefs.min_confidence * 0.85
                   else "low_adjusted_confidence",
            confidence=base_confidence,
            adjusted_confidence=round(adjusted, 1),
            regime=regime, session=session,
        )

    def record_trade(self, bot_name: str, trade: TradeRecord) -> None:
        """Record a trade outcome into the agent's memory."""
        self.get_context(bot_name).record_trade(trade)

    def active_agents(self) -> List[str]:
        """Return bots that are not paused (can still trade)."""
        return [n for n, c in self.contexts.items() if not c.should_pause()]

    def summary(self) -> Dict[str, Any]:
        return {
            bot: ctx.summary()
            for bot, ctx in self.contexts.items()
        }
