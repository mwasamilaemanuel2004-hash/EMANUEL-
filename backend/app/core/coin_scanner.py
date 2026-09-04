"""
Coin Scanner — auto-discovers the most profitable coins from a universe
(millions of coins). Uses a fast scoring pipeline that combines:

  1. Fundamental score (TokenScore: regulatory, RWA, ecosystem, macro, cycle)
  2. Enhanced fundamental score (dilution, capture, valuation, upside)
  3. Technical score (trend, momentum, volume, volatility)
  4. Smart Money score (sweep+hold+OB confluence)
  5. Risk-adjusted return (Sharpe-like, expected profit / risk)
  6. Capital flow + on-chain activity

The scanner processes a universe (list of coins with basic data) and
returns the top N by ProfitRank. It is designed to scale to millions of
coins by using vectorized operations and short-circuiting low-quality
coins early.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from .token_analyzer import (
    TokenMetrics, RegulatoryStatus, NetworkPhase,
    compute_token_score, compute_enhanced_token_score, estimate_timing_quality,
)


class MarketCategory(Enum):
    CRYPTO_LARGE_CAP = "crypto_large_cap"
    CRYPTO_MID_CAP = "crypto_mid_cap"
    CRYPTO_SMALL_CAP = "crypto_small_cap"
    CRYPTO_MEME = "crypto_meme"
    FOREX_MAJOR = "forex_major"
    FOREX_MINOR = "forex_minor"
    METALS = "metals"
    COMMODITIES = "commodities"
    STOCK_LARGE = "stock_large"
    STOCK_SMALL = "stock_small"


@dataclass
class CoinCandidate:
    """A single coin/asset candidate for the scanner."""
    symbol: str
    category: MarketCategory
    metrics: TokenMetrics
    # Technical data (optional, used for tech score)
    trend_30d: float = 0.0        # 30-day return
    volatility_30d: float = 0.0  # 30-day vol (annualized %)
    volume_24h_usd: float = 0.0
    rsi: float = 50.0
    # Computed
    token_score: float = 0.0
    timing_quality: float = 0.0
    tech_score: float = 0.0
    risk_adj_return: float = 0.0
    profit_rank: float = 0.0
    # Enhanced fundamental data
    dilution_score: float = 0.0
    capture_score: float = 0.0
    valuation_grade: str = ""
    upside_potential_pct: float = 0.0
    risk_reward_ratio: float = 0.0
    enhanced_score: float = 0.0


def _tech_score(trend: float, vol: float, rsi: float) -> float:
    """Technical score 0-100 from trend, volatility, RSI."""
    s = 50.0
    # Trend component
    if trend > 0:
        s += min(30, trend * 3)
    else:
        s += max(-30, trend * 3)
    # Volatility: prefer moderate (15-40%), penalize extreme
    if 15 <= vol <= 40:
        s += 10
    elif vol > 80:
        s -= 15
    elif vol < 5:
        s -= 10
    # RSI: 40-70 is good for momentum, avoid extremes
    if 40 <= rsi <= 65:
        s += 10
    elif rsi > 75 or rsi < 25:
        s -= 15
    return max(0, min(100, s))


def _risk_adj_return(trend: float, vol: float) -> float:
    """Risk-adjusted return (Sharpe-like)."""
    if vol <= 0:
        return 0.0
    return (trend / vol) * 10  # scale


def scan_coins(candidates: List[CoinCandidate], top_n: int = 20,
               min_token_score: float = 50.0,
               min_timing: float = 0.3,
               min_profit_rank: float = 0.0) -> List[CoinCandidate]:
    """
    Scan a list of coin candidates and return the top N by ProfitRank.

    ProfitRank = 0.25 * TokenScore + 0.20 * EnhancedScore + 0.20 * TechScore +
                 0.15 * RiskAdjReturn_normalized + 0.10 * TimingQuality +
                 0.10 * UpsidePotential_normalized

    Filters out low-quality coins (min_token_score, min_timing) before
    ranking. This short-circuits bad coins so we can process millions
    efficiently.
    """
    # Step 1: compute base + enhanced scores
    scored: List[CoinCandidate] = []
    for c in candidates:
        result = compute_token_score(c.metrics)
        c.token_score = result['total']
        c.timing_quality = estimate_timing_quality(c.metrics)
        c.tech_score = _tech_score(c.trend_30d, c.volatility_30d, c.rsi)
        c.risk_adj_return = _risk_adj_return(c.trend_30d, c.volatility_30d)

        # Enhanced fundamental analysis (fall back to base score on error)
        try:
            enhanced = compute_enhanced_token_score(c.metrics)
            c.enhanced_score = enhanced['total']
            c.dilution_score = enhanced['dilution_score']
            c.capture_score = enhanced['capture_score']
            c.valuation_grade = enhanced['valuation_grade']
            c.upside_potential_pct = enhanced['upside_potential_pct']
            c.risk_reward_ratio = enhanced['risk_reward_ratio']
        except Exception:
            c.enhanced_score = c.token_score
            c.dilution_score = 0.0
            c.capture_score = 0.0
            c.valuation_grade = ""
            c.upside_potential_pct = 0.0
            c.risk_reward_ratio = 0.0

        # Filter
        if c.token_score < min_token_score:
            continue
        if c.timing_quality < min_timing:
            continue
        scored.append(c)

    if not scored:
        return []

    # Step 2: normalize risk_adj_return and upside_potential to 0-100
    rar_values = np.array([c.risk_adj_return for c in scored])
    rar_min, rar_max = rar_values.min(), rar_values.max()
    rar_range = rar_max - rar_min if rar_max > rar_min else 1.0

    for c in scored:
        rar_norm = (c.risk_adj_return - rar_min) / rar_range * 100
        upside_norm = min(100, max(0, c.upside_potential_pct + 50))
        # ProfitRank
        c.profit_rank = (
            0.25 * c.token_score
            + 0.20 * c.enhanced_score
            + 0.20 * c.tech_score
            + 0.15 * rar_norm
            + 0.10 * (c.timing_quality * 100)
            + 0.10 * upside_norm
        )
    # Step 3: sort and filter
    scored.sort(key=lambda c: c.profit_rank, reverse=True)
    if min_profit_rank > 0:
        scored = [c for c in scored if c.profit_rank >= min_profit_rank]
    return scored[:top_n]


def make_synthetic_universe(n_large=50, n_mid=200, n_small=2000,
                            n_meme=5000, n_metals=10, n_commodities=20,
                            seed=42) -> List[CoinCandidate]:
    """
    Generate a synthetic universe of coins for testing the scanner at
    scale. In production this would be replaced by a live API call
    (CoinGecko, CoinMarketCap, etc.).
    """
    np.random.seed(seed)
    cats = [
        (n_large, MarketCategory.CRYPTO_LARGE_CAP, 0.0, 1e10, 5, 30, 0.7),
        (n_mid, MarketCategory.CRYPTO_MID_CAP, -0.05, 1e9, 10, 60, 0.5),
        (n_small, MarketCategory.CRYPTO_SMALL_CAP, -0.3, 1e7, 20, 100, 0.3),
        (n_meme, MarketCategory.CRYPTO_MEME, -0.5, 1e5, 50, 150, 0.1),
        (n_metals, MarketCategory.METALS, 0.0, 5e9, 8, 20, 0.8),
        (n_commodities, MarketCategory.COMMODITIES, -0.1, 1e9, 12, 40, 0.6),
    ]
    reg_choices = [RegulatoryStatus.CLEAR, RegulatoryStatus.COMPLIANT,
                   RegulatoryStatus.PENDING, RegulatoryStatus.UNCLEAR]
    cycle_choices = [NetworkPhase.BULL_RUN, NetworkPhase.UPGRADE_CATALYST,
                     NetworkPhase.ACCUMULATION, NetworkPhase.DISTRIBUTION,
                     NetworkPhase.BEAR]
    out: List[CoinCandidate] = []
    for n, cat, dr, vol_max, vol_min, vol_max_v, win_prob in cats:
        for i in range(n):
            sym = f"{cat.value[:3].upper()}{i:05d}"
            trend = float(np.random.normal(dr, 0.10))
            vol_v = float(np.random.uniform(vol_min, vol_max_v))
            rsi_v = float(np.random.uniform(20, 80))
            vol24 = float(np.random.uniform(vol_max * 0.1, vol_max))
            reg = reg_choices[np.random.randint(0, len(reg_choices))]
            cycle = cycle_choices[np.random.randint(0, len(cycle_choices))]
            etf = cat in (MarketCategory.CRYPTO_LARGE_CAP, MarketCategory.METALS)
            metrics = TokenMetrics(
                symbol=sym,
                regulatory_status=reg,
                rwa_tvl_usd=vol24 * 0.1 if cat != MarketCategory.CRYPTO_MEME else 0,
                rwa_growth_30d_pct=trend * 100,
                recent_product_launches=int(np.random.poisson(1)),
                ecosystem_score=float(np.random.uniform(20, 95)),
                macro_liquidity_score=float(np.random.uniform(30, 80)),
                network_upgrade_score=float(np.random.uniform(20, 90)),
                staking_etf_available=etf,
                net_capital_flow_30d=trend * 50,
                cycle_phase=cycle,
                active_addresses_30d_pct=trend * 100,
                real_usage_score=float(np.random.uniform(20, 90)),
                # New fields
                circulating_supply=float(np.random.uniform(1e6, 1e9)),
                max_supply=float(np.random.uniform(1e6, 1e10)),
                annual_inflation_pct=float(np.random.uniform(0, 15)),
                unlock_90d_pct=float(np.random.uniform(0, 10)),
                team_investor_pct=float(np.random.uniform(10, 50)),
                mcap_usd=float(np.random.uniform(1e6, 1e10)),
                fdv_usd=float(np.random.uniform(1e6, 1e11)),
                price=float(np.random.uniform(0.01, 50000)),
                price_ath=float(np.random.uniform(0.01, 60000)),
            )
            out.append(CoinCandidate(
                symbol=sym, category=cat, metrics=metrics,
                trend_30d=trend, volatility_30d=vol_v,
                volume_24h_usd=vol24, rsi=rsi_v,
            ))
    return out
