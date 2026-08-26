"""
Tokenization & RWA Analysis Engine — ultra-advanced fundamental analysis for
crypto tokenization, Real-World Assets (RWA), regulatory clarity, ecosystem
adoption, macro liquidity, network upgrades, staking/ETFs, capital flow,
and timing.

This engine computes a TokenScore (0-100) for crypto assets based on:
  1. Regulatory Clarity (SEC approval, MiCA, licenses)
  2. Tokenization & RWA Growth (TVL, asset types, issuer quality)
  3. Product Launches (recent protocol/token launches, roadmap)
  4. Ecosystem Adoption (active users, developers, integrations)
  5. Macro Liquidity (Fed policy, global M2, risk-on/off)
  6. Network Upgrades (Ethereum, Solana, L2 progress)
  7. Staking & ETFs (institutional product availability)
  8. Capital Flow (on-chain flows, exchange net position)
  9. Timing (market cycle, halving, macro events)
 10. Real Usage (active addresses, tx volume, fees burned)
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class RegulatoryStatus(Enum):
    CLEAR = "clear"               # SEC-approved, fully regulated
    COMPLIANT = "compliant"       # Operating under regulatory framework
    PENDING = "pending"           # Application in review
    UNCLEAR = "unclear"           # Regulatory uncertainty
    HOSTILE = "hostile"           # Banned or restricted


class NetworkPhase(Enum):
    BULL_RUN = "bull_run"
    ACCUMULATION = "accumulation"
    UPGRADE_CATALYST = "upgrade_catalyst"
    DISTRIBUTION = "distribution"
    BEAR = "bear"


@dataclass
class TokenMetrics:
    """Fundamental metrics for a tokenized asset / RWA."""
    symbol: str
    regulatory_status: RegulatoryStatus = RegulatoryStatus.UNCLEAR
    rwa_tvl_usd: float = 0.0
    rwa_growth_30d_pct: float = 0.0
    recent_product_launches: int = 0
    ecosystem_score: float = 50.0       # 0-100
    macro_liquidity_score: float = 50.0
    network_upgrade_score: float = 50.0
    staking_etf_available: bool = False
    net_capital_flow_30d: float = 0.0   # + = inflow, - = outflow
    cycle_phase: NetworkPhase = NetworkPhase.ACCUMULATION
    active_addresses_30d_pct: float = 0.0
    real_usage_score: float = 50.0


def compute_token_score(m: TokenMetrics) -> Dict[str, float]:
    """
    Compute a 0-100 TokenScore from the metrics.
    Each factor weighted, with regulatory clarity as a hard multiplier.
    """
    scores = {}

    # 1. Regulatory clarity (gate + score)
    reg_map = {
        RegulatoryStatus.CLEAR: 100,
        RegulatoryStatus.COMPLIANT: 85,
        RegulatoryStatus.PENDING: 60,
        RegulatoryStatus.UNCLEAR: 35,
        RegulatoryStatus.HOSTILE: 10,
    }
    scores['regulatory'] = reg_map[m.regulatory_status]
    reg_multiplier = 0.5 + (scores['regulatory'] / 100.0)  # 0.5 to 1.5

    # 2. RWA growth
    growth = m.rwa_growth_30d_pct
    scores['rwa_growth'] = min(100, max(0, 50 + growth * 1.0))

    # 3. Product launches
    scores['product_launches'] = min(100, m.recent_product_launches * 20)

    # 4. Ecosystem adoption
    scores['ecosystem'] = m.ecosystem_score

    # 5. Macro liquidity
    scores['macro_liquidity'] = m.macro_liquidity_score

    # 6. Network upgrades
    scores['network_upgrade'] = m.network_upgrade_score

    # 7. Staking/ETF (binary 50 or 100)
    scores['staking_etf'] = 100 if m.staking_etf_available else 50

    # 8. Capital flow
    flow = m.net_capital_flow_30d
    scores['capital_flow'] = min(100, max(0, 50 + flow * 0.5))

    # 9. Cycle phase
    cycle_map = {
        NetworkPhase.BULL_RUN: 90,
        NetworkPhase.UPGRADE_CATALYST: 80,
        NetworkPhase.ACCUMULATION: 60,
        NetworkPhase.DISTRIBUTION: 40,
        NetworkPhase.BEAR: 25,
    }
    scores['cycle'] = cycle_map[m.cycle_phase]

    # 10. Real usage
    scores['real_usage'] = m.real_usage_score

    # Weighted total (regulatory is a multiplier, not additive)
    weights = {
        'rwa_growth': 0.15, 'product_launches': 0.10, 'ecosystem': 0.12,
        'macro_liquidity': 0.10, 'network_upgrade': 0.08, 'staking_etf': 0.08,
        'capital_flow': 0.12, 'cycle': 0.10, 'real_usage': 0.15,
    }
    base = sum(scores[k] * w for k, w in weights.items())
    total = base * reg_multiplier
    return {
        'total': round(min(100, max(0, total)), 1),
        'breakdown': scores,
        'regulatory_multiplier': round(reg_multiplier, 2),
    }


def should_trade(score: float, threshold: float = 65.0) -> bool:
    """TokenScore >= threshold means trade-worthy."""
    return score >= threshold


def estimate_timing_quality(m: TokenMetrics) -> float:
    """
    Timing quality 0-1: how good is the current moment to enter?
    Combines cycle phase + capital flow + upgrade catalyst.
    """
    timing = 0.5
    if m.cycle_phase == NetworkPhase.BULL_RUN: timing += 0.2
    elif m.cycle_phase == NetworkPhase.UPGRADE_CATALYST: timing += 0.15
    elif m.cycle_phase == NetworkPhase.BEAR: timing -= 0.2
    if m.net_capital_flow_30d > 0: timing += min(0.15, m.net_capital_flow_30d * 0.01)
    else: timing -= min(0.15, abs(m.net_capital_flow_30d) * 0.01)
    if m.network_upgrade_score > 70: timing += 0.1
    if m.recent_product_launches >= 2: timing += 0.05
    return min(1.0, max(0.0, timing))
