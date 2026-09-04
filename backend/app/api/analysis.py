# -*- coding: cp1252 -*-
"""
Analysis & Results API � endpoints for the frontend pages.

GET /api/analysis          -> full analysis (tokenization + risk)
GET /api/analysis?symbol=BTC -> single symbol analysis
GET /api/results           -> backtest + forward test summary
GET /api/results/per-bot   -> per-bot performance
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..core.token_analyzer import (
    compute_token_score, compute_enhanced_token_score, estimate_timing_quality,
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
        circulating_supply=19_700_000, total_supply=19_700_000, max_supply=21_000_000,
        annual_inflation_pct=0.8, unlock_30d_pct=0.0, unlock_90d_pct=0.0,
        team_investor_pct=0.0, top10_holder_pct=5.0,
        annual_fees_usd=1_200_000_000, annual_revenue_usd=800_000_000,
        annual_burn_usd=0, staking_yield_pct=0.0, daily_volume_usd=25_000_000_000,
        price=65000, mcap_usd=1_280_000_000_000, fdv_usd=1_365_000_000_000,
        price_ath=73750, price_200d_avg=55000, active_addresses=900000,
    ),
    "ETH": TokenMetrics(
        symbol="ETH", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=8_000_000_000, rwa_growth_30d_pct=12.0,
        recent_product_launches=4, ecosystem_score=98,
        macro_liquidity_score=68, network_upgrade_score=90,
        staking_etf_available=True, net_capital_flow_30d=10.0,
        cycle_phase=NetworkPhase.UPGRADE_CATALYST,
        active_addresses_30d_pct=4.0, real_usage_score=95,
        circulating_supply=120_000_000, total_supply=120_000_000, max_supply=0,
        annual_inflation_pct=0.5, unlock_30d_pct=0.0, unlock_90d_pct=0.0,
        team_investor_pct=0.0, top10_holder_pct=8.0,
        annual_fees_usd=2_500_000_000, annual_revenue_usd=1_800_000_000,
        annual_burn_usd=500_000_000, staking_yield_pct=3.5, daily_volume_usd=15_000_000_000,
        price=3500, mcap_usd=420_000_000_000, fdv_usd=420_000_000_000,
        price_ath=4878, price_200d_avg=2800, active_addresses=500000,
    ),
    "SOL": TokenMetrics(
        symbol="SOL", regulatory_status=RegulatoryStatus.PENDING,
        rwa_tvl_usd=500_000_000, rwa_growth_30d_pct=20.0,
        recent_product_launches=5, ecosystem_score=88,
        macro_liquidity_score=65, network_upgrade_score=80,
        staking_etf_available=True, net_capital_flow_30d=20.0,
        cycle_phase=NetworkPhase.UPGRADE_CATALYST,
        active_addresses_30d_pct=10.0, real_usage_score=85,
        circulating_supply=440_000_000, total_supply=580_000_000, max_supply=0,
        annual_inflation_pct=5.0, unlock_30d_pct=2.0, unlock_90d_pct=5.0,
        team_investor_pct=20.0, top10_holder_pct=25.0,
        annual_fees_usd=150_000_000, annual_revenue_usd=100_000_000,
        annual_burn_usd=30_000_000, staking_yield_pct=6.5, daily_volume_usd=3_000_000_000,
        price=150, mcap_usd=66_000_000_000, fdv_usd=87_000_000_000,
        price_ath=260, price_200d_avg=120, active_addresses=1_200_000,
    ),
    "ONDO": TokenMetrics(
        symbol="ONDO", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=800_000_000, rwa_growth_30d_pct=35.0,
        recent_product_launches=3, ecosystem_score=82,
        macro_liquidity_score=70, network_upgrade_score=65,
        staking_etf_available=False, net_capital_flow_30d=25.0,
        cycle_phase=NetworkPhase.BULL_RUN,
        active_addresses_30d_pct=15.0, real_usage_score=75,
        circulating_supply=1_400_000_000, total_supply=10_000_000_000, max_supply=10_000_000_000,
        annual_inflation_pct=15.0, unlock_30d_pct=5.0, unlock_90d_pct=12.0,
        team_investor_pct=35.0, top10_holder_pct=45.0,
        annual_fees_usd=20_000_000, annual_revenue_usd=15_000_000,
        annual_burn_usd=0, staking_yield_pct=0.0, daily_volume_usd=200_000_000,
        price=0.85, mcap_usd=1_190_000_000, fdv_usd=8_500_000_000,
        price_ath=1.50, price_200d_avg=0.70, active_addresses=50000,
    ),
}


class AnalysisResponse(BaseModel):
    symbol: str
    token_score: float
    enhanced_score: float = 0.0
    base_score: float = 0.0
    dilution_score: float = 0.0
    capture_score: float = 0.0
    valuation_grade: str = ""
    upside_potential_pct: float = 0.0
    risk_reward_ratio: float = 0.0
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
    fundamentals: Dict[str, Any] = {}


def _analyze_symbol(symbol: str) -> AnalysisResponse:
    m = TOKEN_UNIVERSE.get(symbol.upper())
    if m is None:
        return AnalysisResponse(
            symbol=symbol, token_score=0.0, enhanced_score=0.0, base_score=0.0,
            dilution_score=0.0, capture_score=0.0, valuation_grade="",
            upside_potential_pct=0.0, risk_reward_ratio=0.0,
            timing_quality=0.0, recommendation="UNKNOWN",
            regulatory="unknown", rwa_tvl_usd=0, rwa_growth_30d_pct=0,
            ecosystem_score=0, macro_liquidity_score=0,
            network_upgrade_score=0, staking_etf_available=False,
            capital_flow_30d=0, cycle_phase="unknown", real_usage_score=0,
            breakdown={}, regulatory_multiplier=1.0, factors=[], fundamentals={},
        )
    # Enhanced score with dilution, capture, valuation
    result = compute_enhanced_token_score(m)
    token_score = result['total']
    base_score = result['base_score']
    dilution_score = result['dilution_score']
    capture_score = result['capture_score']
    valuation_grade = result['valuation_grade']
    upside_potential = result['upside_potential_pct']
    risk_reward = result['risk_reward_ratio']
    timing = estimate_timing_quality(m)
    
    if token_score >= 75 and timing >= 0.55 and risk_reward > 2:
        rec = "STRONG_BUY"
    elif token_score >= 65 and timing >= 0.45:
        rec = "BUY"
    elif token_score >= 50:
        rec = "HOLD"
    elif token_score >= 35:
        rec = "SELL"
    else:
        rec = "AVOID"
    
    factors = [
        {"name": "Regulatory Clarity", "weight": "gate", "score": result['breakdown']['base']['breakdown']['regulatory'],
         "value": m.regulatory_status.value, "multiplier": result['breakdown']['base']['regulatory_multiplier']},
        {"name": "RWA Growth (30d)", "weight": 0.15, "score": result['breakdown']['base']['breakdown']['rwa_growth'],
         "value": f"{m.rwa_growth_30d_pct:+.1f}%"},
        {"name": "Product Launches", "weight": 0.10, "score": result['breakdown']['base']['breakdown']['product_launches'],
         "value": f"{m.recent_product_launches} launches"},
        {"name": "Ecosystem Adoption", "weight": 0.12, "score": result['breakdown']['base']['breakdown']['ecosystem'],
         "value": f"{m.ecosystem_score}/100"},
        {"name": "Macro Liquidity", "weight": 0.10, "score": result['breakdown']['base']['breakdown']['macro_liquidity'],
         "value": f"{m.macro_liquidity_score}/100"},
        {"name": "Network Upgrades", "weight": 0.08, "score": result['breakdown']['base']['breakdown']['network_upgrade'],
         "value": f"{m.network_upgrade_score}/100"},
        {"name": "Staking / ETFs", "weight": 0.08, "score": result['breakdown']['base']['breakdown']['staking_etf'],
         "value": "Available" if m.staking_etf_available else "Not available"},
        {"name": "Capital Flow (30d)", "weight": 0.12, "score": result['breakdown']['base']['breakdown']['capital_flow'],
         "value": f"{m.net_capital_flow_30d:+.1f}%"},
        {"name": "Market Cycle", "weight": 0.10, "score": result['breakdown']['base']['breakdown']['cycle'],
         "value": m.cycle_phase.value},
        {"name": "Real Usage", "weight": 0.15, "score": result['breakdown']['base']['breakdown']['real_usage'],
         "value": f"{m.real_usage_score}/100"},
        {"name": "Dilution Risk", "weight": "enhanced", "score": dilution_score,
         "value": result['breakdown']['dilution']['dilution_risk_grade']},
        {"name": "Token Capture", "weight": "enhanced", "score": capture_score,
         "value": result['breakdown']['token_capture']['value_accrual_grade']},
        {"name": "Valuation", "weight": "enhanced", "score": min(100, max(0, 50 + upside_potential / 2)),
         "value": valuation_grade},
        {"name": "Upside Potential", "weight": "enhanced", "score": min(100, max(0, 50 + upside_potential / 2)),
         "value": f"{upside_potential:+.0f}%"},
        {"name": "Risk/Reward", "weight": "enhanced", "score": min(100, risk_reward * 25),
         "value": f"{risk_reward:.1f}x"},
    ]
    return AnalysisResponse(
        symbol=symbol, token_score=token_score, enhanced_score=token_score,
        base_score=base_score, dilution_score=dilution_score, capture_score=capture_score,
        valuation_grade=valuation_grade, upside_potential_pct=upside_potential,
        risk_reward_ratio=risk_reward, timing_quality=round(timing, 3),
        recommendation=rec, regulatory=m.regulatory_status.value,
        rwa_tvl_usd=m.rwa_tvl_usd, rwa_growth_30d_pct=m.rwa_growth_30d_pct,
        ecosystem_score=m.ecosystem_score,
        macro_liquidity_score=m.macro_liquidity_score,
        network_upgrade_score=m.network_upgrade_score,
        staking_etf_available=m.staking_etf_available,
        capital_flow_30d=m.net_capital_flow_30d,
        cycle_phase=m.cycle_phase.value, real_usage_score=m.real_usage_score,
        breakdown=result['breakdown']['base']['breakdown'],
        regulatory_multiplier=result['breakdown']['base']['regulatory_multiplier'],
        factors=factors,
        fundamentals={
            'dilution': result['breakdown']['dilution'],
            'token_capture': result['breakdown']['token_capture'],
            'valuation': result['breakdown']['valuation'],
            'upside': result['breakdown']['upside'],
        },
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