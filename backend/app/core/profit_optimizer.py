"""
Profit Optimizer — finds the most profitable opportunities across
ALL bots, ALL markets, and ALL asset classes.

Pipeline:
  1. Scan crypto universe (millions of coins) -> top N by ProfitRank
  2. Scan forex/metals/commodities/stocks -> top M by ProfitRank
  3. Cross-reference with the 14 bots' lane preferences
  4. Apply BotContext adaptive confidence
  5. Return ranked, bot-assigned opportunities ready for execution

The optimizer is PURELY ADDITIVE: it does not modify any bot, the
execution engine, or the scoring. It produces an opportunity list.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np

from .coin_scanner import CoinCandidate, scan_coins, MarketCategory
from .multi_market_scanner import (
    MarketCandidate, scan_markets,
)
from .bot_lanes import BotLaneAssigner
from .bot_context import BotContext
from .agent_dispatcher import AgentDispatcher


@dataclass
class Opportunity:
    """A trading opportunity with bot assignment."""
    symbol: str
    category: MarketCategory
    side: str          # BUY or SELL
    profit_rank: float  # 0-100
    token_score: float
    tech_score: float
    timing_quality: float
    assigned_bot: str
    bot_confidence: float
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_pct: float = 1.0
    reason: str = ""


def _build_opportunity_from_coin(c: CoinCandidate, dispatcher: AgentDispatcher,
                                 lane_assigner: BotLaneAssigner) -> Optional[Opportunity]:
    """Assign a CoinCandidate to the best-fit bot and build an opportunity."""
    # Find best-fit bot via lane + dispatcher
    regime = "STRONG_TREND" if c.token_score > 70 else "WEAK_TREND"
    session = "LONDON"
    best_bot = None; best_conf = 0.0
    import pandas as pd
    fake_ts = pd.Timestamp.now(tz="UTC")
    for agent_name in dispatcher.contexts:
        res = dispatcher.dispatch(agent_name, regime, fake_ts, c.symbol,
                                  base_confidence=70.0)
        if res.accepted and res.adjusted_confidence > best_conf:
            best_bot = agent_name; best_conf = res.adjusted_confidence
    if best_bot is None:
        return None
    side = "BUY" if c.trend_30d > 0 else "SELL"
    # Risk-adjusted return proxy
    rar = c.risk_adj_return
    risk_pct = 1.0
    if rar < 0:
        risk_pct = 0.5
    return Opportunity(
        symbol=c.symbol, category=c.category, side=side,
        profit_rank=c.profit_rank, token_score=c.token_score,
        tech_score=c.tech_score, timing_quality=c.timing_quality,
        assigned_bot=best_bot, bot_confidence=best_conf,
        risk_pct=risk_pct,
        reason=f"Rank={c.profit_rank:.0f} Bot={best_bot} score={c.token_score:.0f}",
    )


def _build_opportunity_from_market(m: MarketCandidate, dispatcher: AgentDispatcher,
                                    lane_assigner: BotLaneAssigner) -> Optional[Opportunity]:
    """Assign a MarketCandidate to the best-fit bot."""
    regime = "STRONG_TREND" if m.fundamental_score > 70 else "WEAK_TREND"
    session = "LONDON"
    best_bot = None; best_conf = 0.0
    import pandas as pd
    fake_ts = pd.Timestamp.now(tz="UTC")
    for agent_name in dispatcher.contexts:
        res = dispatcher.dispatch(agent_name, regime, fake_ts, m.symbol,
                                  base_confidence=70.0)
        if res.accepted and res.adjusted_confidence > best_conf:
            best_bot = agent_name; best_conf = res.adjusted_confidence
    if best_bot is None:
        return None
    side = "BUY" if m.trend_30d > 0 else "SELL"
    return Opportunity(
        symbol=m.symbol, category=m.category, side=side,
        profit_rank=m.profit_rank,
        token_score=m.fundamental_score,
        tech_score=m.tech_score, timing_quality=0.5,
        assigned_bot=best_bot, bot_confidence=best_conf,
        risk_pct=1.0 if m.profit_rank > 60 else 0.5,
        reason=f"Rank={m.profit_rank:.0f} Bot={best_bot}",
    )


def find_best_opportunities(
    coin_universe: List[CoinCandidate],
    market_universe: List[MarketCandidate],
    dispatcher: AgentDispatcher,
    top_coins: int = 20,
    top_markets: int = 10,
    min_profit_rank: float = 40.0,
) -> List[Opportunity]:
    """
    Scan all markets, assign bots, and return the best opportunities
    sorted by ProfitRank.
    """
    lane_assigner = BotLaneAssigner()
    # Scan crypto
    top_coins_ranked = scan_coins(
        coin_universe, top_n=top_coins, min_token_score=40.0, min_timing=0.3)
    opps: List[Opportunity] = []
    for c in top_coins_ranked:
        opp = _build_opportunity_from_coin(c, dispatcher, lane_assigner)
        if opp and opp.profit_rank >= min_profit_rank:
            opps.append(opp)
    # Scan markets
    top_markets_ranked = scan_markets(
        market_universe, top_n=top_markets, min_fundamental=40.0, min_tech=30.0)
    for m in top_markets_ranked:
        opp = _build_opportunity_from_market(m, dispatcher, lane_assigner)
        if opp and opp.profit_rank >= min_profit_rank:
            opps.append(opp)
    opps.sort(key=lambda o: o.profit_rank, reverse=True)
    return opps


def summarize_by_bot(opportunities: List[Opportunity]) -> Dict[str, int]:
    """Count opportunities assigned to each bot."""
    out: Dict[str, int] = {}
    for o in opportunities:
        out[o.assigned_bot] = out.get(o.assigned_bot, 0) + 1
    return out


def summarize_by_market(opportunities: List[Opportunity]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for o in opportunities:
        key = o.category.value
        out[key] = out.get(key, 0) + 1
    return out
