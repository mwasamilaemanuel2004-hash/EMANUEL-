"""
Analysis & Results API — endpoints for the frontend pages.

GET /api/analysis          -> full analysis (tokenization + risk)
GET /api/analysis?symbol=BTC -> single symbol analysis
GET /api/results           -> backtest + forward test summary
GET /api/results/per-bot   -> per-bot performance
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..core.token_analyzer import (
    TOKEN_UNIVERSE_FALLBACK, compute_token_score, estimate_timing_quality,
    RegulatoryStatus, NetworkPhase, TokenMetrics,
)

router = APIRouter()


# Curated universe (mirrors tokenization_bot.py)
TOKEN_UNIVERSE: Dict[str, TokenMetrics] = {
    "BTC": TokenMetrics(
        symbol="BTC", regulatory_status=RegulatoryStatus.CLEAR,
        rwa_tvl_usd=1_500_000_000, rwa_growth_30d_pct=8.0,
        recent_product_launches=3, ecosystem_score=95,
        macro_liquidity_score=70, network_upgrade_score=75,
        staking_etf_available=True, net_capital_flow_30d=15.0,
        cycle_phase=NetworkPhase.BULL_RUN,
        active_addresses_30d_pct=5.0, real_usage_score=90,
    ),
    "ETH": TokenMetrics(
        symbol="ETH", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=8_000_000_000, rwa_growth_30d_pct=12.0,
        recent_product_launches=4, ecosystem_score=98,
        macro_liquidity_score=68, network_upgrade_score=90,
        staking_etf_available=True, net_capital_flow_30d=10.0,
        cycle_phase=NetworkPhase.UPGRADE_CATALYST,
        active_addresses_30d_pct=4.0, real_usage_score=95,
    ),
    "SOL": TokenMetrics(
        symbol="SOL", regulatory_status=RegulatoryStatus.PENDING,
        rwa_tvl_usd=500_000_000, rwa_growth_30d_pct=20.0,
        recent_product_launches=5, ecosystem_score=88,
        macro_liquidity_score=65, network_upgrade_score=80,
        staking_etf_available=True, net_capital_flow_30d=20.0,
        cycle_phase=NetworkPhase.UPGRADE_CATALYST,
        active_addresses_30d_pct=10.0, real_usage_score=85,
    ),
    "ONDO": TokenMetrics(
        symbol="ONDO", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=800_000_000, rwa_growth_30d_pct=35.0,
        recent_product_launches=3, ecosystem_score=82,
        macro_liquidity_score=70, network_upgrade_score=65,
        staking_etf_available=False, net_capital_flow_30d=25.0,
        cycle_phase=NetworkPhase.BULL_RUN,
        active_addresses_30d_pct=15.0, real_usage_score=75,
    ),
}


class AnalysisResponse(BaseModel):
    symbol: str
    token_score: float
    timing_quality: float
    recommendation: str
    regulatory: str
    rwa_tvl_usd: float
    rwa_growth_30d_pct: float
    ecosystem_score: float
    macro_liquidity_score: float
    network_upgrade_score: float
    staking_etf_available: bool
    capital_flow_30d: float
    cycle_phase: str
    real_usage_score: float
    breakdown: Dict[str, float]
    regulatory_multiplier: float
    factors: List[Dict[str, Any]]


def _analyze_symbol(symbol: str) -> AnalysisResponse:
    m = TOKEN_UNIVERSE.get(symbol.upper())
    if m is None:
        return AnalysisResponse(
            symbol=symbol, token_score=0.0, timing_quality=0.0,
            recommendation="UNKNOWN",
            regulatory="unknown", rwa_tvl_usd=0, rwa_growth_30d_pct=0,
            ecosystem_score=0, macro_liquidity_score=0,
            network_upgrade_score=0, staking_etf_available=False,
            capital_flow_30d=0, cycle_phase="unknown", real_usage_score=0,
            breakdown={}, regulatory_multiplier=1.0, factors=[],
        )
    result = compute_token_score(m)
    token_score = result['total']
    timing = estimate_timing_quality(m)
    if token_score >= 70 and timing >= 0.55:
        rec = "TRADE"
    elif token_score >= 60:
        rec = "WATCH"
    else:
        rec = "SKIP"
    factors = [
        {"name": "Regulatory Clarity", "weight": "gate", "score": result['breakdown']['regulatory'],
         "value": m.regulatory_status.value, "multiplier": result['regulatory_multiplier']},
        {"name": "RWA Growth (30d)", "weight": 0.15, "score": result['breakdown']['rwa_growth'],
         "value": f"{m.rwa_growth_30d_pct:+.1f}%"},
        {"name": "Product Launches", "weight": 0.10, "score": result['breakdown']['product_launches'],
         "value": f"{m.recent_product_launches} launches"},
        {"name": "Ecosystem Adoption", "weight": 0.12, "score": result['breakdown']['ecosystem'],
         "value": f"{m.ecosystem_score}/100"},
        {"name": "Macro Liquidity", "weight": 0.10, "score": result['breakdown']['macro_liquidity'],
         "value": f"{m.macro_liquidity_score}/100"},
        {"name": "Network Upgrades", "weight": 0.08, "score": result['breakdown']['network_upgrade'],
         "value": f"{m.network_upgrade_score}/100"},
        {"name": "Staking / ETFs", "weight": 0.08, "score": result['breakdown']['staking_etf'],
         "value": "Available" if m.staking_etf_available else "Not available"},
        {"name": "Capital Flow (30d)", "weight": 0.12, "score": result['breakdown']['capital_flow'],
         "value": f"{m.net_capital_flow_30d:+.1f}%"},
        {"name": "Market Cycle", "weight": 0.10, "score": result['breakdown']['cycle'],
         "value": m.cycle_phase.value},
        {"name": "Real Usage", "weight": 0.15, "score": result['breakdown']['real_usage'],
         "value": f"{m.real_usage_score}/100"},
    ]
    return AnalysisResponse(
        symbol=symbol, token_score=token_score, timing_quality=round(timing, 3),
        recommendation=rec, regulatory=m.regulatory_status.value,
        rwa_tvl_usd=m.rwa_tvl_usd, rwa_growth_30d_pct=m.rwa_growth_30d_pct,
        ecosystem_score=m.ecosystem_score,
        macro_liquidity_score=m.macro_liquidity_score,
        network_upgrade_score=m.network_upgrade_score,
        staking_etf_available=m.staking_etf_available,
        capital_flow_30d=m.net_capital_flow_30d,
        cycle_phase=m.cycle_phase.value, real_usage_score=m.real_usage_score,
        breakdown=result['breakdown'],
        regulatory_multiplier=result['regulatory_multiplier'],
        factors=factors,
    )


@router.get("/analysis", response_model=List[AnalysisResponse])
async def get_analysis(symbol: Optional[str] = Query(None)):
    """Get tokenization analysis. If symbol is given, returns one entry."""
    if symbol:
        return [_analyze_symbol(symbol)]
    return [_analyze_symbol(s) for s in TOKEN_UNIVERSE.keys()]


# --- Results endpoint ---

BACKTEST_RESULTS = [
    {"seed": 7, "trades": 14, "win_rate": 57.1, "profit_factor": 0.58, "expectancy": -0.79, "pass": False},
    {"seed": 13, "trades": 14, "win_rate": 50.0, "profit_factor": 1.82, "expectancy": 0.91, "pass": False},
    {"seed": 21, "trades": 13, "win_rate": 76.9, "profit_factor": 3.18, "expectancy": 1.76, "pass": True},
    {"seed": 42, "trades": 12, "win_rate": 58.3, "profit_factor": 1.73, "expectancy": 0.96, "pass": False},
    {"seed": 99, "trades": 14, "win_rate": 64.3, "profit_factor": 1.51, "expectancy": 0.60, "pass": True},
    {"seed": 123, "trades": 20, "win_rate": 80.0, "profit_factor": 3.55, "expectancy": 1.76, "pass": True},
    {"seed": 200, "trades": 12, "win_rate": 50.0, "profit_factor": 0.64, "expectancy": -0.84, "pass": False},
]

FORWARD_RESULTS = [
    {"seed": 300, "trades": 14, "win_rate": 64.3, "profit_factor": 2.32, "expectancy": 1.26, "pass": True},
    {"seed": 400, "trades": 10, "win_rate": 50.0, "profit_factor": 1.30, "expectancy": 0.53, "pass": False},
    {"seed": 500, "trades": 12, "win_rate": 83.3, "profit_factor": 10.20, "expectancy": 2.57, "pass": True},
    {"seed": 600, "trades": 14, "win_rate": 71.4, "profit_factor": 2.20, "expectancy": 1.32, "pass": True},
    {"seed": 700, "trades": 13, "win_rate": 84.6, "profit_factor": 5.10, "expectancy": 1.95, "pass": True},
    {"seed": 800, "trades": 14, "win_rate": 50.0, "profit_factor": 1.63, "expectancy": 0.53, "pass": False},
    {"seed": 900, "trades": 14, "win_rate": 64.3, "profit_factor": 1.54, "expectancy": 0.64, "pass": True},
]


@router.get("/results")
async def get_results():
    """Get backtest + forward test results summary."""
    def agg(rows):
        wrs = [r["win_rate"] for r in rows]
        return {
            "avg_win_rate": round(sum(wrs) / len(wrs), 1),
            "pass_count": sum(1 for r in rows if r["pass"]),
            "total_seeds": len(rows),
            "best_seed": max(rows, key=lambda r: r["win_rate"])["seed"],
            "best_win_rate": max(r["win_rate"] for r in rows),
            "total_trades": sum(r["trades"] for r in rows),
        }
    return {
        "backtest": {"seeds": BACKTEST_RESULTS, "summary": agg(BACKTEST_RESULTS)},
        "forward_test": {"seeds": FORWARD_RESULTS, "summary": agg(FORWARD_RESULTS)},
    }


@router.get("/results/per-bot")
async def get_per_bot_results():
    """Per-bot performance summary (from backtest_bots)."""
    return {
        "bots": [
            {"bot": "TrendFollowerBot", "signals": 0, "note": "selective (real data)"},
            {"bot": "ForexScalperBot", "signals": 0, "note": "selective"},
            {"bot": "SmartMoneyBot", "signals": 0, "note": "selective"},
            {"bot": "BreakoutBot", "signals": 0, "note": "selective"},
            {"bot": "NewsBot", "signals": 0, "note": "selective"},
            {"bot": "ArbitrageBot", "signals": 0, "note": "selective (async)"},
            {"bot": "CryptoScalperBot", "signals": 0, "note": "selective"},
            {"bot": "DcaBot", "signals": 0, "note": "selective"},
            {"bot": "GridBot", "signals": 0, "note": "selective"},
            {"bot": "WhaleBot", "signals": 0, "note": "selective"},
            {"bot": "AIStockAnalyzerBot", "signals": 0, "note": "selective (async)"},
            {"bot": "MetalsBot", "signals": 0, "note": "selective"},
            {"bot": "CommoditiesBot", "signals": 0, "note": "selective"},
            {"bot": "TokenizationBot", "signals": "n/a",
             "note": "Fundamental analysis: TokenScore + timing (regulatory, RWA, macro)"},
        ],
        "system": {
            "win_rate_avg": 66.8,
            "pass_count_forward": "5/7",
            "best_forward_seed": {"seed": 700, "win_rate": 84.6, "profit_factor": 5.10},
            "execution": "Mandatory smart SL, breakeven@1R, UNLIMITED runner",
        },
    }
