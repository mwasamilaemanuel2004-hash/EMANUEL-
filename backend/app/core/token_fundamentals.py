"""
Token Fundamentals Engine — Economic Quality, Token Capture, Dilution/Downside,
Valuation & Upside analysis for crypto tokens.

Extends the base TokenScore with four critical missing dimensions:
  1. Economic Quality — macro regime + liquidity + risk environment
  2. Token Capture — value accrual efficiency (fees, burn, revenue)
  3. Dilution & Downside — supply dynamics + tail-risk quantification
  4. Valuation & Upside — fair value models + asymmetric payoff scoring
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


# =============================================================================
# 1. ECONOMIC QUALITY
# =============================================================================

class MacroRegime(Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    TRANSITION = "transition"
    CRISIS = "crisis"


class LiquidityCondition(Enum):
    ABUNDANT = "abundant"
    ADEQUATE = "adequate"
    TIGHT = "tight"
    CRISIS = "crisis"


@dataclass
class MacroData:
    """Macro economic inputs for economic quality scoring."""
    global_m2_yoy_pct: float = 0.0       # Global M2 YoY growth %
    fed_policy_rate: float = 5.25         # Current Fed funds rate
    vix: float = 15.0                     # Volatility index
    credit_spread_bps: float = 150.0      # IG credit spread in bps
    dxy_yoy_pct: float = 0.0             # Dollar index YoY %
    correlation_risk: float = 0.5         # Cross-asset correlation 0-1
    inflation_yoy_pct: float = 3.0       # CPI YoY %
    unemployment_rate: float = 3.7       # Unemployment %


def compute_economic_quality(data: MacroData) -> Dict[str, Any]:
    """
    Compute Economic Quality Score (0-100) from macro inputs.
    
    Combines:
      - Liquidity conditions (M2 growth, Fed policy)
      - Risk environment (VIX, credit spreads, correlation)
      - Growth backdrop (inflation, unemployment)
    
    Returns dict with score, regime, liquidity_grade, components.
    """
    scores = {}
    
    # --- Liquidity component (40% of score) ---
    # M2 growth: positive = good for risk assets
    m2_score = min(100, max(0, 50 + data.global_m2_yoy_pct * 5))
    # Fed policy: lower rates = better for risk assets
    fed_score = min(100, max(0, 100 - (data.fed_policy_rate - 1.0) * 15))
    scores['liquidity'] = 0.6 * m2_score + 0.4 * fed_score
    
    # --- Risk environment (35% of score) ---
    # VIX: lower = better (inverted, capped)
    vix_score = min(100, max(0, 100 - (data.vix - 10) * 2.5))
    # Credit spread: lower = better
    spread_score = min(100, max(0, 100 - (data.credit_spread_bps - 100) * 0.3))
    # Correlation: moderate is fine, extreme = systemic risk
    corr_score = 100 - abs(data.correlation_risk - 0.4) * 100
    scores['risk_env'] = 0.4 * vix_score + 0.35 * spread_score + 0.25 * corr_score
    
    # --- Growth backdrop (25% of score) ---
    # Inflation: moderate (2-3%) is ideal, too high or deflation = bad
    infl_score = 100 - abs(data.inflation_yoy_pct - 2.5) * 20
    # Unemployment: lower is better
    unemp_score = min(100, max(0, 100 - (data.unemployment_rate - 3.0) * 15))
    scores['growth'] = 0.5 * infl_score + 0.5 * unemp_score
    
    # Total economic quality
    total = 0.40 * scores['liquidity'] + 0.35 * scores['risk_env'] + 0.25 * scores['growth']
    total = min(100, max(0, total))
    
    # Determine regime
    if total >= 75:
        regime = MacroRegime.RISK_ON
    elif total >= 55:
        regime = MacroRegime.TRANSITION
    elif total >= 35:
        regime = MacroRegime.RISK_OFF
    else:
        regime = MacroRegime.CRISIS
    
    # Liquidity condition
    if scores['liquidity'] >= 70:
        liq_cond = LiquidityCondition.ABUNDANT
    elif scores['liquidity'] >= 50:
        liq_cond = LiquidityCondition.ADEQUATE
    elif scores['liquidity'] >= 30:
        liq_cond = LiquidityCondition.TIGHT
    else:
        liq_cond = LiquidityCondition.CRISIS
    
    return {
        'score': round(total, 1),
        'regime': regime.value,
        'liquidity_condition': liq_cond.value,
        'liquidity_score': round(scores['liquidity'], 1),
        'risk_env_score': round(scores['risk_env'], 1),
        'growth_score': round(scores['growth'], 1),
        'components': {
            'm2_score': round(m2_score, 1),
            'fed_score': round(fed_score, 1),
            'vix_score': round(vix_score, 1),
            'credit_spread_score': round(spread_score, 1),
            'correlation_score': round(corr_score, 1),
            'inflation_score': round(infl_score, 1),
            'unemployment_score': round(unemp_score, 1),
        }
    }


# =============================================================================
# 2. TOKEN CAPTURE ANALYSIS
# =============================================================================

@dataclass
class CaptureMetrics:
    """Metrics for token value capture analysis."""
    annual_fees_usd: float = 0.0          # Protocol annual fees
    annual_revenue_usd: float = 0.0       # Protocol annual revenue
    annual_burn_usd: float = 0.0          # Annual token burn value
    staking_yield_pct: float = 0.0        # Staking APR %
    tvl_usd: float = 0.0                  # Total Value Locked
    mcap_usd: float = 0.0                 # Market cap
    circulating_supply: float = 0.0       # Circulating supply
    daily_volume_usd: float = 0.0         # 24h trading volume
    active_addresses: int = 0             # Daily active addresses
    tx_count_24h: int = 0                 # 24h transaction count


def compute_token_capture(m: CaptureMetrics) -> Dict[str, Any]:
    """
    Compute Token Capture Score (0-100) measuring how efficiently a token
    accrues value from its ecosystem.
    
    Factors:
      - Fee capture: fees / mcap (how much value flows to token)
      - Revenue yield: revenue / mcap
      - Burn efficiency: burn / supply (deflationary pressure)
      - Staking yield: real yield to holders
      - TVL/MCAP ratio: capital efficiency
      - Volume/MCAP: turnover / speculation ratio
    
    Higher score = token captures more economic value per unit of market cap.
    """
    scores = {}
    
    # --- Fee Capture (25%) ---
    # fees/mcap ratio: >5% is excellent, <0.1% is poor
    fee_yield = (m.annual_fees_usd / m.mcap_usd * 100) if m.mcap_usd > 0 else 0
    scores['fee_capture'] = min(100, fee_yield * 15)  # 6.67% yield = 100 score
    
    # --- Revenue Yield (20%) ---
    rev_yield = (m.annual_revenue_usd / m.mcap_usd * 100) if m.mcap_usd > 0 else 0
    scores['revenue_yield'] = min(100, rev_yield * 12)  # 8.3% = 100
    
    # --- Burn Efficiency (15%) ---
    burn_pct = (m.annual_burn_usd / m.mcap_usd * 100) if m.mcap_usd > 0 else 0
    scores['burn_efficiency'] = min(100, burn_pct * 30)  # 3.3% burn = 100
    
    # --- Staking Yield (15%) ---
    # Real yield >5% is excellent, 0% is neutral, negative (inflation) is bad
    scores['staking_yield'] = min(100, max(0, 40 + m.staking_yield_pct * 8))
    
    # --- TVL/MCAP Ratio (15%) ---
    # TVL > MCAP = undervalued/productive, TVL < 0.1*MCAP = speculative
    tvl_mcap_ratio = m.tvl_usd / m.mcap_usd if m.mcap_usd > 0 else 0
    scores['capital_efficiency'] = min(100, tvl_mcap_ratio * 70)  # 1.4x = 100
    
    # --- Volume Turnover (10%) ---
    # High turnover = liquidity but also speculation
    vol_mcap = m.daily_volume_usd / m.mcap_usd if m.mcap_usd > 0 else 0
    # Sweet spot: 5-20% daily turnover
    if 0.05 <= vol_mcap <= 0.20:
        scores['turnover'] = 80 + (vol_mcap - 0.05) / 0.15 * 20
    elif vol_mcap > 0.20:
        scores['turnover'] = max(30, 100 - (vol_mcap - 0.20) * 200)
    else:
        scores['turnover'] = min(60, vol_mcap / 0.05 * 60)
    
    # Weighted total
    weights = {
        'fee_capture': 0.25, 'revenue_yield': 0.20, 'burn_efficiency': 0.15,
        'staking_yield': 0.15, 'capital_efficiency': 0.15, 'turnover': 0.10,
    }
    total = sum(scores[k] * w for k, w in weights.items())
    total = min(100, max(0, total))
    
    # Capture ratio: composite value accrual metric
    capture_ratio = (fee_yield + rev_yield + burn_pct + m.staking_yield_pct) / 4
    
    # Grade
    if total >= 80:
        grade = "EXCELLENT"
    elif total >= 65:
        grade = "GOOD"
    elif total >= 45:
        grade = "FAIR"
    elif total >= 25:
        grade = "WEAK"
    else:
        grade = "POOR"
    
    return {
        'capture_score': round(total, 1),
        'capture_ratio': round(capture_ratio, 2),
        'value_accrual_grade': grade,
        'fee_yield_pct': round(fee_yield, 3),
        'revenue_yield_pct': round(rev_yield, 3),
        'burn_yield_pct': round(burn_pct, 3),
        'components': {k: round(v, 1) for k, v in scores.items()},
    }


# =============================================================================
# 3. DILUTION & DOWNSIDE ANALYSIS
# =============================================================================

@dataclass
class SupplyMetrics:
    """Token supply dynamics for dilution analysis."""
    circulating_supply: float = 0.0
    total_supply: float = 0.0
    max_supply: float = 0.0
    annual_inflation_pct: float = 0.0     # Token inflation rate
    unlock_30d_usd: float = 0.0           # Vesting unlocks next 30d ($)
    unlock_60d_usd: float = 0.0           # Vesting unlocks next 60d ($)
    unlock_90d_usd: float = 0.0           # Vesting unlocks next 90d ($)
    team_investor_pct: float = 0.0        # % held by team/investors
    top10_holder_pct: float = 0.0         # % held by top 10 wallets
    mcap_usd: float = 0.0
    fdv_usd: float = 0.0                  # Fully diluted valuation


def compute_dilution_risk(m: SupplyMetrics) -> Dict[str, Any]:
    """
    Compute Dilution Risk Score (0-100, higher = LESS dilution risk).
    
    Factors:
      - Supply release: circulating / max supply
      - Inflation rate: annual token emission
      - Unlock pressure: upcoming vesting as % of MCAP
      - Concentration: team/investor holdings + top 10 concentration
      - FDV/MCAP ratio: gap to fully diluted
    """
    scores = {}
    
    # --- Supply Release (25%) ---
    # Higher circulation % = less future dilution
    if m.max_supply > 0:
        circ_ratio = m.circulating_supply / m.max_supply
    elif m.total_supply > 0:
        circ_ratio = m.circulating_supply / m.total_supply
    else:
        circ_ratio = 0.5  # unknown, neutral
    scores['supply_release'] = min(100, circ_ratio * 110)  # 90%+ = 100
    
    # --- Inflation Rate (25%) ---
    # 0% or negative (deflationary) = 100, >20% = 0
    infl = m.annual_inflation_pct
    if infl <= 0:
        scores['inflation'] = 100.0  # deflationary = best
    elif infl <= 5:
        scores['inflation'] = 80 + (5 - infl) * 4  # 80-100
    elif infl <= 20:
        scores['inflation'] = max(0, 80 - (infl - 5) * 5.33)
    else:
        scores['inflation'] = 0.0
    
    # --- Unlock Pressure (25%) ---
    # Upcoming unlocks as % of MCAP
    total_unlock_90d = m.unlock_30d_usd + m.unlock_60d_usd + m.unlock_90d_usd
    unlock_pct = (total_unlock_90d / m.mcap_usd * 100) if m.mcap_usd > 0 else 0
    # <1% = minimal, >20% = severe
    if unlock_pct <= 1:
        scores['unlock_pressure'] = 100.0
    elif unlock_pct <= 20:
        scores['unlock_pressure'] = max(0, 100 - (unlock_pct - 1) * 5.26)
    else:
        scores['unlock_pressure'] = 0.0
    
    # --- Concentration Risk (15%) ---
    # Team/investor + top10 holdings
    conc = m.team_investor_pct + m.top10_holder_pct
    if conc <= 20:
        scores['concentration'] = 100.0
    elif conc <= 60:
        scores['concentration'] = max(0, 100 - (conc - 20) * 2.5)
    else:
        scores['concentration'] = 0.0
    
    # --- FDV/MCAP Gap (10%) ---
    # Large gap = more dilution ahead
    fdv_mcap_ratio = m.fdv_usd / m.mcap_usd if m.mcap_usd > 0 else 1.0
    if fdv_mcap_ratio <= 1.5:
        scores['fdv_gap'] = 100.0
    elif fdv_mcap_ratio <= 5:
        scores['fdv_gap'] = max(0, 100 - (fdv_mcap_ratio - 1.5) * 28.6)
    else:
        scores['fdv_gap'] = 0.0
    
    # Weighted total (higher = less dilution risk = better)
    weights = {
        'supply_release': 0.25, 'inflation': 0.25,
        'unlock_pressure': 0.25, 'concentration': 0.15, 'fdv_gap': 0.10,
    }
    total = sum(scores[k] * w for k, w in weights.items())
    total = min(100, max(0, total))
    
    # Grade
    if total >= 80:
        grade = "MINIMAL"
    elif total >= 60:
        grade = "LOW"
    elif total >= 40:
        grade = "MODERATE"
    elif total >= 20:
        grade = "HIGH"
    else:
        grade = "SEVERE"
    
    return {
        'dilution_score': round(total, 1),
        'dilution_risk_grade': grade,
        'unlock_pressure_90d_pct': round(unlock_pct, 2),
        'circulating_ratio': round(circ_ratio, 3),
        'fdv_mcap_ratio': round(fdv_mcap_ratio, 2),
        'components': {k: round(v, 1) for k, v in scores.items()},
    }


def compute_downside_risk(prices: np.ndarray, supply_m: SupplyMetrics) -> Dict[str, Any]:
    """
    Compute Downside Risk metrics from price data and supply dynamics.
    
    Returns VaR, CVaR, max drawdown estimate, stress scenarios, and a
    downside grade (A=best, F=worst).
    """
    if len(prices) < 5:
        return {
            'var_95': 0.0, 'cvar_95': 0.0, 'max_drawdown_est': 0.0,
            'stress_loss': 0.0, 'downside_grade': 'N/A',
        }
    
    # Returns
    returns = np.diff(prices) / prices[:-1]
    
    # Historical VaR (95th percentile of losses)
    var_95 = float(np.percentile(returns, 5))
    
    # Conditional VaR (average of losses beyond VaR)
    losses_beyond = returns[returns <= var_95]
    cvar_95 = float(np.mean(losses_beyond)) if len(losses_beyond) > 0 else var_95
    
    # Max drawdown from data
    peak = prices[0]
    max_dd = 0.0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak
        if dd > max_dd:
            max_dd = dd
    max_drawdown_est = float(max_dd)
    
    # Stress scenario: combine historical worst with dilution shock
    # Dilution shock = upcoming unlocks as % of price
    dilution_shock = (supply_m.unlock_90d_usd / supply_m.mcap_usd) if supply_m.mcap_usd > 0 else 0
    stress_loss = min(0.95, abs(cvar_95) * 5 + dilution_shock * 0.5)
    
    # Downside grade based on VaR and stress
    risk_score = abs(var_95) * 100 * 3 + stress_loss * 50  # composite
    if risk_score < 10:
        grade = "A"
    elif risk_score < 20:
        grade = "B"
    elif risk_score < 35:
        grade = "C"
    elif risk_score < 50:
        grade = "D"
    else:
        grade = "F"
    
    return {
        'var_95': round(var_95 * 100, 2),  # as positive % loss
        'cvar_95': round(cvar_95 * 100, 2),
        'max_drawdown_est': round(max_drawdown_est * 100, 2),
        'stress_loss': round(stress_loss * 100, 2),
        'downside_grade': grade,
        'daily_vol': round(float(np.std(returns)) * 100, 2),
    }


# =============================================================================
# 4. VALUATION & UPSIDE
# =============================================================================

@dataclass
class ValuationMetrics:
    """Metrics for token valuation models."""
    price: float = 0.0
    mcap_usd: float = 0.0
    fdv_usd: float = 0.0
    tvl_usd: float = 0.0
    annual_revenue_usd: float = 0.0
    annual_fees_usd: float = 0.0
    circulating_supply: float = 0.0
    max_supply: float = 0.0
    active_addresses: int = 0
    daily_volume_usd: float = 0.0
    daily_tx_count: int = 0
    staking_yield_pct: float = 0.0
    # Price history for percentile
    price_ath: float = 0.0
    price_200d_avg: float = 0.0


def compute_valuation(m: ValuationMetrics) -> Dict[str, Any]:
    """
    Compute fair value estimate and valuation grade using multiple models:
      - NVT Ratio (Network Value to Transactions)
      - MCAP/TVL ratio
      - Price-to-Revenue (P/S)
      - Metcalfe-based valuation (active addresses)
      - ATH discount
    
    Returns fair_value_estimate, valuation_grade, upside_potential_pct.
    """
    estimates = []
    model_weights = []
    
    # --- NVT-based valuation ---
    # NVT = MCAP / daily tx volume annualized
    # Healthy NVT: 20-90 (like P/E for networks)
    if m.daily_volume_usd > 0:
        nvt = m.mcap_usd / (m.daily_volume_usd * 365)
        # Target NVT = 50 (median)
        if nvt > 0:
            nvt_fair_value = m.price * (50 / nvt)  # adjust to target NVT
            estimates.append(nvt_fair_value)
            model_weights.append(0.20)
    
    # --- MCAP/TVL ---
    # TVL/MCAP > 1 = undervalued, < 0.1 = overvalued
    if m.tvl_usd > 0 and m.mcap_usd > 0:
        tvl_mcap = m.tvl_usd / m.mcap_usd
        # Target TVL/MCAP = 1.0
        tvl_fair_value = m.price * (1.0 / tvl_mcap) if tvl_mcap > 0 else m.price
        estimates.append(tvl_fair_value)
        model_weights.append(0.20)
    
    # --- Price-to-Revenue ---
    # P/S ratio: < 10 = cheap for protocols with revenue
    if m.annual_revenue_usd > 0 and m.mcap_usd > 0:
        ps_ratio = m.mcap_usd / m.annual_revenue_usd
        # Target P/S = 15
        if ps_ratio > 0:
            rev_fair_value = m.price * (15 / ps_ratio)
            estimates.append(rev_fair_value)
            model_weights.append(0.20)
    
    # --- Metcalfe's Law ---
    # Value ∝ n² (active addresses squared) / supply
    if m.active_addresses > 0 and m.circulating_supply > 0:
        # Normalize: compare current to a reference (e.g., 1M addresses = $10B MCAP)
        metcalfe_ratio = (m.active_addresses ** 2) / (1_000_000 ** 2)
        reference_mcap = 10_000_000_000
        metcalfe_mcap = reference_mcap * metcalfe_ratio
        if m.mcap_usd > 0:
            metcalfe_fair_value = m.price * (metcalfe_mcap / m.mcap_usd)
            estimates.append(metcalfe_fair_value)
            model_weights.append(0.15)
    
    # --- ATH Discount Recovery ---
    # If price is > 50% below ATH, partial recovery to 50% discount is fair
    if m.price_ath > 0 and m.price < m.price_ath * 0.5:
        ath_fair_value = m.price_ath * 0.6  # recover to 60% of ATH
        estimates.append(ath_fair_value)
        model_weights.append(0.15)
    
    # --- 200d MA Mean Reversion ---
    if m.price_200d_avg > 0:
        # If price > 2x 200d MA, likely overvalued
        ma_fair_value = m.price_200d_avg * 1.2  # slight premium to MA
        estimates.append(ma_fair_value)
        model_weights.append(0.10)
    
    # Weighted fair value estimate
    if estimates:
        # Normalize weights
        w_sum = sum(model_weights)
        normalized_weights = [w / w_sum for w in model_weights]
        fair_value = sum(e * w for e, w in zip(estimates, normalized_weights))
    else:
        fair_value = m.price  # no data, use current
    
    fair_value = max(0, fair_value)
    
    # Upside potential
    upside_pct = ((fair_value - m.price) / m.price * 100) if m.price > 0 else 0
    
    # Valuation grade
    if m.mcap_usd > 0 and m.price_ath > 0:
        ath_discount = (m.price_ath - m.price) / m.price_ath * 100
    else:
        ath_discount = 50  # unknown
    
    # Grade based on upside + discount from ATH
    if upside_pct > 100 and ath_discount > 50:
        grade = "DEEP_VALUE"
    elif upside_pct > 50:
        grade = "UNDERVALUED"
    elif upside_pct > 20:
        grade = "FAIR_VALUE"
    elif upside_pct > -20:
        grade = "FAIR"
    elif upside_pct > -50:
        grade = "OVERVALUED"
    else:
        grade = "SPECULATIVE"
    
    # Support levels (simplified)
    supports = []
    if m.price_200d_avg > 0:
        supports.append(round(m.price_200d_avg, 4))
    if m.price_ath > 0:
        supports.append(round(m.price_ath * 0.5, 4))
        supports.append(round(m.price_ath * 0.382, 4))  # fib
    supports = sorted(set(s for s in supports if s < m.price), reverse=True)[:3]
    
    return {
        'fair_value_estimate': round(fair_value, 4),
        'upside_potential_pct': round(upside_pct, 1),
        'valuation_grade': grade,
        'support_levels': supports,
        'model_estimates': {f"model_{i}": round(e, 4) for i, e in enumerate(estimates)},
        'components': {
            'nvt_based': round(estimates[0], 4) if len(estimates) > 0 else None,
            'tvl_based': round(estimates[1], 4) if len(estimates) > 1 else None,
            'revenue_based': round(estimates[2], 4) if len(estimates) > 2 else None,
            'metcalfe_based': round(estimates[3], 4) if len(estimates) > 3 else None,
        },
    }


def compute_upside_score(valuation: Dict, economic_quality: float,
                         token_capture: float, dilution_score: float) -> Dict[str, Any]:
    """
    Compute final upside score combining:
      - Valuation upside potential
      - Economic quality tailwind
      - Token capture efficiency
      - Low dilution tailwind
    
    Returns upside_score (0-100), expected_return, risk_reward_ratio.
    """
    # Valuation component (40%)
    upside_pct = valuation.get('upside_potential_pct', 0)
    # Normalize: >200% = 100, <0% = 0
    valuation_component = min(100, max(0, (upside_pct + 50) / 2.5))
    
    # Economic quality tailwind (25%)
    econ_component = economic_quality  # already 0-100
    
    # Token capture efficiency (20%)
    capture_component = token_capture  # already 0-100
    
    # Dilution safety (15%)
    dilution_component = dilution_score  # already 0-100
    
    # Weighted upside score
    upside_score = (
        0.40 * valuation_component
        + 0.25 * econ_component
        + 0.20 * capture_component
        + 0.15 * dilution_component
    )
    upside_score = min(100, max(0, upside_score))
    
    # Expected return: upside * probability-weighted by quality
    probability_factor = (economic_quality / 100) * (token_capture / 100)
    expected_return = upside_pct * probability_factor
    
    # Risk-reward ratio
    # Reward = expected return, Risk = (100 - dilution_score) as downside proxy
    risk = max(5, 100 - dilution_score)  # min 5% risk floor
    risk_reward = expected_return / risk if risk > 0 else 0
    
    return {
        'upside_score': round(upside_score, 1),
        'expected_return_pct': round(expected_return, 1),
        'risk_reward_ratio': round(risk_reward, 2),
        'probability_weighted_return': round(expected_return, 1),
        'components': {
            'valuation_component': round(valuation_component, 1),
            'economic_tailwind': round(econ_component, 1),
            'capture_efficiency': round(capture_component, 1),
            'dilution_safety': round(dilution_component, 1),
        },
    }


# =============================================================================
# 5. MASTER FUNDAMENTAL SCORE
# =============================================================================

def compute_master_fundamental_score(
    token_metrics: Any,  # TokenMetrics from token_analyzer
    price: float,
    price_data: np.ndarray,
    macro_data: Optional[MacroData] = None,
    capture_metrics: Optional[CaptureMetrics] = None,
    supply_metrics: Optional[SupplyMetrics] = None,
    valuation_metrics: Optional[ValuationMetrics] = None,
) -> Dict[str, Any]:
    """
    Master function combining all fundamental analysis modules.
    
    Returns comprehensive score breakdown with recommendation.
    """
    # Default macro data if not provided
    if macro_data is None:
        macro_data = MacroData()
    
    # Default capture metrics from token_metrics if available
    if capture_metrics is None:
        capture_metrics = CaptureMetrics(
            annual_fees_usd=getattr(token_metrics, 'rwa_tvl_usd', 0) * 0.02,
            annual_revenue_usd=getattr(token_metrics, 'rwa_tvl_usd', 0) * 0.01,
            tvl_usd=getattr(token_metrics, 'rwa_tvl_usd', 0),
            mcap_usd=price * getattr(token_metrics, 'circulating_supply', 1e9),
        )
    
    # Default supply metrics
    if supply_metrics is None:
        supply_metrics = SupplyMetrics(
            circulating_supply=getattr(token_metrics, 'circulating_supply', 0),
            max_supply=getattr(token_metrics, 'max_supply', 0),
            annual_inflation_pct=getattr(token_metrics, 'annual_inflation_pct', 5.0),
            mcap_usd=price * getattr(token_metrics, 'circulating_supply', 1e9),
            fdv_usd=price * getattr(token_metrics, 'max_supply', 0) if getattr(token_metrics, 'max_supply', 0) > 0 else price * getattr(token_metrics, 'circulating_supply', 1e9),
        )
    
    # Default valuation metrics
    if valuation_metrics is None:
        valuation_metrics = ValuationMetrics(
            price=price,
            mcap_usd=price * getattr(token_metrics, 'circulating_supply', 1e9),
            tvl_usd=getattr(token_metrics, 'rwa_tvl_usd', 0),
            active_addresses=int(getattr(token_metrics, 'active_addresses_30d_pct', 0) * 10000),
            daily_tx_count=int(getattr(token_metrics, 'real_usage_score', 50) * 1000),
        )
    
    # 1. Economic Quality
    econ = compute_economic_quality(macro_data)
    
    # 2. Token Capture
    capture = compute_token_capture(capture_metrics)
    
    # 3. Dilution Risk
    dilution = compute_dilution_risk(supply_metrics)
    
    # 4. Downside Risk
    downside = compute_downside_risk(price_data, supply_metrics)
    
    # 5. Valuation
    valuation = compute_valuation(valuation_metrics)
    
    # 6. Upside Score
    upside = compute_upside_score(
        valuation, econ['score'], capture['capture_score'], dilution['dilution_score']
    )
    
    # --- Master Score ---
    # Weighted combination of all dimensions
    master_score = (
        0.20 * econ['score']           # economic quality
        + 0.20 * capture['capture_score']  # token capture
        + 0.20 * dilution['dilution_score']  # low dilution
        + 0.15 * upside['upside_score']  # upside potential
        + 0.15 * (100 - abs(downside['var_95']) * 10)  # low downside (var)
        + 0.10 * (token_metrics.real_usage_score if hasattr(token_metrics, 'real_usage_score') else 50)
    )
    master_score = min(100, max(0, master_score))
    
    # --- Recommendation ---
    if master_score >= 80 and upside['risk_reward_ratio'] > 3:
        recommendation = "STRONG_BUY"
    elif master_score >= 65 and upside['risk_reward_ratio'] > 1.5:
        recommendation = "BUY"
    elif master_score >= 50:
        recommendation = "HOLD"
    elif master_score >= 35:
        recommendation = "SELL"
    else:
        recommendation = "AVOID"
    
    return {
        'master_score': round(master_score, 1),
        'recommendation': recommendation,
        'economic_quality': econ,
        'token_capture': capture,
        'dilution': dilution,
        'downside': downside,
        'valuation': valuation,
        'upside': upside,
        'summary': {
            'economic_quality_score': econ['score'],
            'token_capture_score': capture['capture_score'],
            'dilution_score': dilution['dilution_score'],
            'downside_grade': downside['downside_grade'],
            'valuation_grade': valuation['valuation_grade'],
            'upside_score': upside['upside_score'],
            'fair_value_estimate': valuation['fair_value_estimate'],
            'upside_potential_pct': valuation['upside_potential_pct'],
            'risk_reward_ratio': upside['risk_reward_ratio'],
            'expected_return_pct': upside['expected_return_pct'],
            'var_95': downside['var_95'],
        },
    }
