"""Deriv analysis, staking, risk controls, and execution planning."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class DerivMode(str, Enum):
    DEMO = "demo"
    PAPER = "paper"
    LIVE = "live"


class DerivStrategy(str, Enum):
    DIGITAL_OPTION = "digital_option"
    TURBO = "turbo"
    MULTIPLIER = "multiplier"
    CFD = "cfd"
    SYNTHETIC = "synthetic"
    VANILLA = "vanilla"
    ACCUMULATOR = "accumulator"
    MARTINGALE = "martingale"
    DALEMBERT = "dalembert"
    OSCARS_GRIND = "oscars_grind"
    REVERSE_MARTINGALE = "reverse_martingale"
    SEQUENCE_1326 = "1-3-2-6"
    VOLATILITY_ADAPTATION = "volatility_adaptation"
    AI_ADAPTIVE = "ai_adaptive"


class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    MEDIUM = "medium"
    AGGRESSIVE = "aggressive"
    ULTRA_AGGRESSIVE = "ultra_aggressive"
    CUSTOM = "custom"


class GrowthMode(str, Enum):
    SAFE = "safe_growth"
    BALANCED = "balanced_growth"
    FAST = "fast_growth"
    ULTRA = "ultra_growth"
    CUSTOM = "custom"


RISK_PROFILES = {
    RiskLevel.CONSERVATIVE: (0.005, 0.01, 0.03, 2),
    RiskLevel.MEDIUM: (0.01, 0.02, 0.05, 3),
    RiskLevel.AGGRESSIVE: (0.02, 0.04, 0.08, 4),
    RiskLevel.ULTRA_AGGRESSIVE: (0.03, 0.06, 0.12, 5),
}


class DerivRequest(BaseModel):
    symbol: str = Field(default="R_75", min_length=2, max_length=24, pattern=r"^[A-Za-z0-9_]+$")
    mode: DerivMode = DerivMode.DEMO
    strategy: Optional[DerivStrategy] = None
    growth_mode: GrowthMode = GrowthMode.SAFE
    confidence_threshold: float = Field(default=70, ge=0, le=100)
    probability_threshold: float = Field(default=0.55, ge=0.5, le=1)
    minimum_ev: float = Field(default=0.02, ge=0, le=10)
    risk_level: RiskLevel = RiskLevel.CONSERVATIVE
    balance: float = Field(default=10000, gt=0, le=10_000_000)
    risk_per_trade: Optional[float] = Field(default=None, gt=0, le=0.03)
    max_daily_loss: Optional[float] = Field(default=None, gt=0, le=0.20)
    max_losses: Optional[int] = Field(default=None, ge=1, le=20)
    max_stake: Optional[float] = Field(default=None, gt=0)
    max_drawdown: Optional[float] = Field(default=None, gt=0, le=0.95)
    max_exposure: Optional[float] = Field(default=None, gt=0, le=1)
    profit_lock_at: Optional[float] = Field(default=None, ge=0, le=10)
    execute: bool = False

    @field_validator("execute")
    @classmethod
    def block_live_execution(cls, value: bool, info: Any) -> bool:
        if value and info.data.get("mode") == DerivMode.LIVE:
            raise ValueError("Live execution requires the authenticated execution service")
        return value

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.upper()


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    stake: float
    reason: str


def _returns(prices: list[float]) -> list[float]:
    return [math.log(current / previous) for previous, current in zip(prices, prices[1:]) if previous > 0 and current > 0]


def _hurst(prices: list[float]) -> float:
    values = _returns(prices)
    if len(values) < 8 or statistics.pstdev(values) == 0:
        return 0.5
    cumulative = []
    running = 0.0
    for value in values:
        running += value
        cumulative.append(running)
    spread = max(cumulative) - min(cumulative)
    deviation = statistics.pstdev(values)
    return max(0.0, min(1.0, math.log(max(spread / deviation, 1.0)) / math.log(len(values))))


def analyze_prices(prices: list[float]) -> dict[str, Any]:
    """Return explainable random-market features and a conservative signal."""
    if len(prices) < 20 or any(price <= 0 for price in prices):
        raise ValueError("At least 20 positive prices are required")
    if any(current == previous for previous, current in zip(prices, prices[1:])) and len(set(prices)) < 3:
        raise ValueError("Price stream has insufficient variation")
    if any(current < 0 for current in prices):
        raise ValueError("Prices must be positive")
    values = _returns(prices)
    mean = statistics.fmean(values)
    volatility = statistics.pstdev(values)
    recent = values[-10:]
    z_score = (statistics.fmean(recent) - mean) / (volatility or 1e-12)
    autocorrelation = 0.0
    if len(values) > 2 and statistics.pstdev(values[:-1]) and statistics.pstdev(values[1:]):
        autocorrelation = statistics.correlation(values[:-1], values[1:])
    counts = (sum(value >= 0 for value in values), sum(value < 0 for value in values))
    entropy = -sum((count / len(values)) * math.log(count / len(values), 2) for count in counts if count)
    hurst = _hurst(prices)
    randomness = min(1.0, entropy)
    structure = max(0.0, 1.0 - randomness) * 0.5 + abs(autocorrelation) * 0.5
    sample_reliable = len(values) >= 30
    signal = "HOLD" if abs(z_score) < 0.5 or not sample_reliable else ("BUY" if z_score > 0 else "SELL")
    confidence = min(99.0, 50.0 + abs(z_score) * 12 + abs(autocorrelation) * 20 + structure * 10)
    probability = min(0.95, max(0.5, 0.5 + (confidence - 50) / 200)) if signal != "HOLD" else 0.5
    fractal_dimension = round(2.0 - hurst, 4)
    transition_probability = round(max(counts) / len(values), 4)
    volatility_percentile = min(1.0, volatility / (abs(mean) + volatility + 1e-12))
    regime = "trending" if hurst > 0.55 else "mean_reverting" if hurst < 0.45 else "random_walk"
    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "hurst_exponent": round(hurst, 4),
        "z_score": round(z_score, 4),
        "volatility": round(volatility, 6),
        "autocorrelation": round(autocorrelation, 4),
        "entropy": round(entropy, 4),
        "fractal_dimension": fractal_dimension,
        "randomness_score": round(randomness, 4),
        "structure_score": round(structure, 4),
        "predictability_score": round(structure * (1 - volatility_percentile), 4),
        "transition_probability": transition_probability,
        "volatility_percentile": round(volatility_percentile, 4),
        "sample_size": len(values),
        "probability_up": round(probability if signal == "BUY" else 1 - probability if signal == "SELL" else 0.5, 4),
        "probability_down": round(1 - probability if signal == "BUY" else probability if signal == "SELL" else 0.5, 4),
        "data_quality": "valid",
        "statistically_reliable": sample_reliable,
        "regime": regime,
        "positive_expected_value": signal != "HOLD" and confidence >= 60 and sample_reliable,
    }


class DerivBotService:
    """Safe-by-default service. Network execution is intentionally separate."""

    def plan(
        self,
        request: DerivRequest,
        prices: list[float],
        daily_loss: float = 0,
        losses: int = 0,
        equity: Optional[float] = None,
        drawdown: float = 0,
    ) -> dict[str, Any]:
        analysis = analyze_prices(prices)
        risk_per_trade, daily_limit, _, loss_limit = RISK_PROFILES.get(request.risk_level, (0, 0, 0, 0))
        risk_per_trade = request.risk_per_trade or risk_per_trade
        daily_limit = request.max_daily_loss or daily_limit
        loss_limit = request.max_losses or loss_limit
        current_equity = equity or request.balance
        base_probability = analysis["probability_up"] if analysis["signal"] == "BUY" else analysis["probability_down"]
        payout = 0.8
        required_probability = 1 / (1 + payout)
        edge = base_probability - required_probability
        expected_value = base_probability * payout - (1 - base_probability)
        volatility_factor = max(0.25, 1 - analysis["volatility_percentile"])
        confidence_factor = max(0.25, analysis["confidence"] / 100)
        edge_factor = max(0.25, min(1.25, edge / 0.15))
        drawdown_factor = max(0.2, 1 - drawdown / max(request.max_drawdown or RISK_PROFILES.get(request.risk_level, (0, 0, 0, 0))[2], 0.01))
        recovery_factor = max(0.3, 1 - losses * 0.15)
        dynamic_risk = risk_per_trade * confidence_factor * edge_factor * volatility_factor * drawdown_factor * recovery_factor
        if request.growth_mode == GrowthMode.SAFE:
            dynamic_risk *= 0.75
        elif request.growth_mode == GrowthMode.FAST:
            dynamic_risk *= 1.1 if edge >= 0.1 and analysis["confidence"] >= 85 else 0.75
        elif request.growth_mode == GrowthMode.ULTRA:
            dynamic_risk = min(dynamic_risk * 1.2, risk_per_trade)
        dynamic_risk = min(dynamic_risk, risk_per_trade, request.max_drawdown or risk_per_trade)
        stake = round(min(current_equity * dynamic_risk, request.max_stake or current_equity * dynamic_risk), 2)
        hard_limit = daily_loss >= current_equity * daily_limit or losses >= loss_limit or drawdown >= (request.max_drawdown or 0.12)
        allowed = (
            analysis["data_quality"] == "valid"
            and analysis["positive_expected_value"]
            and analysis["confidence"] >= request.confidence_threshold
            and base_probability >= request.probability_threshold
            and expected_value >= request.minimum_ev
            and not hard_limit
            and stake > 0
        )
        reason = "validated positive EV and risk limits passed" if allowed else "HOLD: signal or hard safety gate rejected entry"
        strategy = request.strategy or (DerivStrategy.REVERSE_MARTINGALE if analysis["regime"] == "trending" else DerivStrategy.VOLATILITY_ADAPTATION)
        return {
            "mode": request.mode,
            "symbol": request.symbol,
            "decision": "TRADE" if allowed else "HOLD",
            "strategy": strategy,
            "analysis": analysis,
            "edge": round(edge, 4),
            "expected_value": round(expected_value, 4),
            "required_probability": round(required_probability, 4),
            "risk": {"allowed": allowed, "stake": stake, "risk_fraction": round(dynamic_risk, 6), "reason": reason, "max_losses": loss_limit, "recovery_factor": round(recovery_factor, 3)},
            "execution": "demo_ledger" if request.mode == DerivMode.DEMO else "paper_ledger" if request.mode == DerivMode.PAPER else "live_websocket_requires_explicit_execution_service",
            "safety": {"hard_limit_hit": hard_limit, "live_execution_blocked": request.mode == DerivMode.LIVE, "loss_response": "re-analyze, reduce risk, or hold; never double stake"},
        }