"""
Multi-Market Scanner — scans forex, metals, commodities, and stocks to
find the most profitable opportunities across ALL asset classes.

Each market has its own scoring framework (based on the coin scanner for
crypto; macro/liquidity/cycle for forex; supply/demand/seasonality for
commodities; etc.). The scanner returns a unified ranking by ProfitRank.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np

from .coin_scanner import CoinCandidate, MarketCategory, _tech_score, _risk_adj_return
from .token_analyzer import (
    TokenMetrics, RegulatoryStatus, NetworkPhase,
    compute_token_score, estimate_timing_quality,
)


@dataclass
class MarketCandidate:
    """A non-crypto asset candidate (forex pair, metal, commodity, stock)."""
    symbol: str
    category: MarketCategory
    trend_30d: float = 0.0
    volatility_30d: float = 0.0
    volume_24h_usd: float = 0.0
    rsi: float = 50.0
    # Fundamental
    macro_score: float = 50.0
    central_bank_score: float = 50.0
    seasonality_score: float = 50.0
    supply_demand_score: float = 50.0
    # Computed
    tech_score: float = 0.0
    fundamental_score: float = 0.0
    profit_rank: float = 0.0


def _fundamental_score(m: MarketCandidate) -> float:
    """Fundamental score 0-100 from macro, CB, seasonality, supply/demand."""
    return (
        0.35 * m.macro_score
        + 0.25 * m.central_bank_score
        + 0.20 * m.seasonality_score
        + 0.20 * m.supply_demand_score
    )


def scan_markets(candidates: List[MarketCandidate], top_n: int = 10,
                 min_fundamental: float = 40.0,
                 min_tech: float = 30.0) -> List[MarketCandidate]:
    """Scan forex/metals/commodities/stocks, return top N by ProfitRank."""
    scored: List[MarketCandidate] = []
    for c in candidates:
        c.tech_score = _tech_score(c.trend_30d, c.volatility_30d, c.rsi)
        c.fundamental_score = _fundamental_score(c)
        if c.fundamental_score < min_fundamental:
            continue
        if c.tech_score < min_tech:
            continue
        rar = _risk_adj_return(c.trend_30d, c.volatility_30d)
        scored.append((c, rar))

    if not scored:
        return []
    rars = np.array([r for _, r in scored])
    rar_min, rar_max = rars.min(), rars.max()
    rar_range = rar_max - rar_min if rar_max > rar_min else 1.0
    for c, rar in scored:
        rar_norm = (rar - rar_min) / rar_range * 100
        c.profit_rank = (
            0.40 * c.fundamental_score
            + 0.30 * c.tech_score
            + 0.30 * rar_norm
        )
    scored.sort(key=lambda x: x[0].profit_rank, reverse=True)
    return [c for c, _ in scored[:top_n]]


# Default universe of forex/metal/commodity candidates
DEFAULT_FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD",
    "EURJPY", "GBPJPY", "EURGBP", "AUDJPY",
]

DEFAULT_METALS = ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD"]

DEFAULT_COMMODITIES = ["WTI", "BRENT", "NATGAS", "WHEAT", "CORN", "SOYBEAN", "COFFEE", "SUGAR"]

DEFAULT_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META"]


def make_synthetic_markets(seed: int = 7) -> List[MarketCandidate]:
    """Generate synthetic forex/metals/commodities/stocks for testing."""
    np.random.seed(seed)
    out: List[MarketCandidate] = []
    cat_map = {
        "forex": (MarketCategory.FOREX_MAJOR, DEFAULT_FOREX_PAIRS, 1e10, 5, 12),
        "metals": (MarketCategory.METALS, DEFAULT_METALS, 5e9, 8, 25),
        "commodities": (MarketCategory.COMMODITIES, DEFAULT_COMMODITIES, 2e9, 10, 35),
        "stocks": (MarketCategory.STOCK_LARGE, DEFAULT_STOCKS, 1e10, 15, 30),
    }
    for kind, (cat, symbols, vol24_base, vol_min, vol_max) in cat_map.items():
        for sym in symbols:
            trend = float(np.random.normal(0, 0.08))
            vol_v = float(np.random.uniform(vol_min, vol_max))
            rsi_v = float(np.random.uniform(30, 70))
            vol24 = vol24_base * float(np.random.uniform(0.5, 2.0))
            out.append(MarketCandidate(
                symbol=sym, category=cat,
                trend_30d=trend, volatility_30d=vol_v,
                volume_24h_usd=vol24, rsi=rsi_v,
                macro_score=float(np.random.uniform(40, 85)),
                central_bank_score=float(np.random.uniform(40, 85)),
                seasonality_score=float(np.random.uniform(30, 80)),
                supply_demand_score=float(np.random.uniform(30, 85)),
            ))
    return out
