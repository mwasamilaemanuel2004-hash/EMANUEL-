"""
Master Trade Filter — the centralized intelligent risk & trade-quality layer.

Every bot MUST pass through this before opening a live trade. It classifies
the market regime, confirms across multiple timeframes, scores the trade
quality (0-100, configurable thresholds), checks portfolio exposure, and
only then returns an EXECUTE / WATCH / REJECT decision.

This is the single gate specified in section 12 (Bot Orchestrator pipeline):
    Market Data -> Market Regime -> Bot Signal -> Master Trade Filter
    -> Trade Score -> Risk Engine -> Portfolio Exposure -> Execution
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from .ai_overseer import AIOverseer, MarketCondition, TradeScore


class Regime(Enum):
    STRONG_UPTREND = "STRONG_UPTREND"
    STRONG_DOWNTREND = "STRONG_DOWNTREND"
    WEAK_TREND = "WEAK_TREND"
    RANGE = "RANGE"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    NEWS_RISK = "NEWS_RISK"
    UNSAFE = "UNSAFE"


class Decision(Enum):
    EXECUTE = "EXECUTE"
    WATCH = "WATCH"
    REJECT = "REJECT"


@dataclass
class FilterResult:
    decision: Decision
    score: float
    regime: Regime
    reason: str
    multi_tf_aligned: bool
    rr: float
    details: Dict[str, Any] = field(default_factory=dict)


class PortfolioExposureManager:
    """
    Prevents stacking highly-correlated risk. Tracks per-asset, per-sector,
    directional and total exposure. Rejects new trades that would breach
    configured limits.
    """
    def __init__(self, max_total_risk_pct: float = 20.0,
                 max_asset_risk_pct: float = 5.0,
                 max_correlated_risk_pct: float = 8.0,
                 correlation_threshold: float = 0.7):
        self.max_total = max_total_risk_pct
        self.max_asset = max_asset_risk_pct
        self.max_corr = max_correlated_risk_pct
        self.corr_thr = correlation_threshold
        self.positions: Dict[str, Dict[str, Any]] = {}
        # crude correlation groups (same group = highly correlated)
        self.groups: Dict[str, str] = {}

    def set_group(self, symbol: str, group: str):
        self.groups[symbol] = group

    def add_position(self, symbol: str, risk_pct: float, direction: str):
        g = self.groups.get(symbol, symbol)
        self.positions[symbol] = {'risk': risk_pct, 'dir': direction, 'group': g}

    def remove_position(self, symbol: str):
        self.positions.pop(symbol, None)

    def correlation_exposure(self, group: str) -> float:
        return sum(p['risk'] for p in self.positions.values() if p['group'] == group)

    def total_exposure(self) -> float:
        return sum(p['risk'] for p in self.positions.values())

    def can_open(self, symbol: str, risk_pct: float) -> tuple[bool, str]:
        g = self.groups.get(symbol, symbol)
        if self.total_exposure() + risk_pct > self.max_total:
            return False, f"total exposure {self.total_exposure()+risk_pct:.1f}% > {self.max_total}%"
        if self.positions.get(symbol, {}).get('risk', 0) + risk_pct > self.max_asset:
            return False, f"asset {symbol} exposure would exceed {self.max_asset}%"
        if self.correlation_exposure(g) + risk_pct > self.max_corr:
            return False, f"correlated group '{g}' exposure would exceed {self.max_corr}%"
        return True, "ok"


class MasterTradeFilter:
    """
    Centralized trade-quality + regime + exposure filter.

    Scoring weights (configurable via `weights`):
        trend 20 | structure 20 | momentum 15 | volume/flow 15 |
        liquidity/SR 10 | volatility 10 | risk/reward 10  -> 100
    Thresholds (configurable):
        0-64 NO TRADE | 65-74 WATCH | 75-84 NORMAL | 85-100 HIGH
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        self.ai = AIOverseer(
            min_confidence=cfg.get('min_confidence', 75.0),
            min_risk_reward=cfg.get('min_risk_reward', 2.0),
        )
        self.weights = cfg.get('weights', {
            'trend': 20, 'structure': 20, 'momentum': 15,
            'volume': 15, 'liquidity_sr': 10, 'volatility': 10, 'rr': 10,
        })
        self.thresholds = cfg.get('thresholds', {
            'no_trade': 64, 'watch': 65, 'normal': 75, 'high': 85,
        })
        self.min_rr = cfg.get('min_rr', 2.0)
        self.prefer_rr = cfg.get('prefer_rr', 2.5)
        self.timeframes = cfg.get('timeframes', ['5m', '15m', '1h', '4h', '1d'])
        self.exposure = PortfolioExposureManager(
            max_total_risk_pct=cfg.get('max_total_risk_pct', 20.0),
            max_asset_risk_pct=cfg.get('max_asset_risk_pct', 5.0),
            max_correlated_risk_pct=cfg.get('max_correlated_risk_pct', 8.0),
        )
        self.daily_loss_pct = 0.0
        self.max_daily_loss_pct = cfg.get('max_daily_loss_pct', 5.0)
        self.consecutive_losses = 0
        self.max_consecutive_losses = cfg.get('max_consecutive_losses', 3)

    # ----------------------------------------------------------------
    # REGIME (matches spec section 1)
    # ----------------------------------------------------------------
    def classify_regime(self, mtf_data: Dict[str, pd.DataFrame]) -> Regime:
        try:
            # use highest timeframe for regime, lower for confirmation
            htf = mtf_data.get('1d')
            if htf is None:
                htf = mtf_data.get('4h')
            if htf is None:
                htf = mtf_data.get('1h')
            ltf = mtf_data.get('1h')
            if ltf is None:
                ltf = mtf_data.get('15m')
            if ltf is None:
                ltf = htf
            if htf is None:
                return Regime.RANGE
            ema_f = htf['close'].ewm(span=20).mean().iloc[-1]
            ema_m = htf['close'].ewm(span=50).mean().iloc[-1]
            ema_s = htf['close'].ewm(span=200).mean().iloc[-1]
            adx = self.ai._calc_adx(htf).iloc[-1]
            atr = self.ai._calc_atr(htf).iloc[-1]
            vol = atr / htf['close'].iloc[-1] if htf['close'].iloc[-1] else 0.01
            vol_avg = self.ai._calc_atr(htf).mean() / htf['close'].mean()

            if vol > 3 * vol_avg:
                return Regime.HIGH_VOLATILITY
            if adx > 30:
                if ema_f > ema_m > ema_s:
                    return Regime.STRONG_UPTREND
                if ema_f < ema_m < ema_s:
                    return Regime.STRONG_DOWNTREND
                return Regime.WEAK_TREND
            if adx < 18:
                return Regime.RANGE
            return Regime.WEAK_TREND
        except Exception:
            return Regime.RANGE

    def multi_timeframe_aligned(self, mtf_data: Dict[str, pd.DataFrame], side: str) -> bool:
        """Higher TFs set direction; do not trade against strong HTF structure."""
        try:
            dirs = []
            for tf in ['1d', '4h', '1h']:
                d = mtf_data.get(tf)
                if d is None or len(d) < 60:
                    continue
                ef = d['close'].ewm(span=20).mean().iloc[-1]
                es = d['close'].ewm(span=50).mean().iloc[-1]
                dirs.append(1 if ef > es else -1)
            if not dirs:
                return True
            want = 1 if side == 'BUY' else -1
            # require majority of available HTFs aligned (allow some missing)
            aligned = sum(1 for x in dirs if x == want)
            return aligned >= max(1, len(dirs) - 1)
        except Exception:
            return True

    # ----------------------------------------------------------------
    # SCORE (0-100, weighted, configurable)
    # ----------------------------------------------------------------
    def score(self, data: pd.DataFrame, side: str, entry: float,
              sl: float, tp: float) -> TradeScore:
        base = self.ai.score_trade(data, side, entry, sl, tp)
        # re-weight to spec: trend 20 / structure 20 / momentum 15 /
        # volume 15 / liquidity_sr 10 / volatility 10 / rr 10
        w = self.weights
        total = (
            base.trend_score / 20 * w['trend']
            + base.structure_score / 15 * w['structure']
            + base.momentum_score / 15 * w['momentum']
            + base.volume_score / 10 * w['volume']
            + base.liquidity_score / 10 * w['liquidity_sr']
            + base.volatility_score / 10 * w['volatility']
            + base.risk_reward_score / 20 * w['rr']
        )
        grade = self._grade_from_score(total)
        return TradeScore(
            total_score=round(total, 1),
            trend_score=base.trend_score, structure_score=base.structure_score,
            momentum_score=base.momentum_score, volume_score=base.volume_score,
            volatility_score=base.volatility_score, liquidity_score=base.liquidity_score,
            risk_reward_score=base.risk_reward_score, grade=grade,
            should_trade=base.should_trade, reasons=base.reasons,
        )

    def _grade_from_score(self, s: float) -> str:
        t = self.thresholds
        if s < t['no_trade']:
            return "NO_TRADE"
        if s < t['normal']:
            return "WATCH"
        if s < t['high']:
            return "NORMAL_ENTRY"
        return "HIGH_CONFIDENCE"

    # ----------------------------------------------------------------
    # MAIN FILTER
    # ----------------------------------------------------------------
    def evaluate(self, mtf_data: Dict[str, pd.DataFrame], side: str,
                 entry: float, sl: float, tp: float,
                 symbol: str = "UNKNOWN", risk_pct: float = 1.0,
                 spread_pct: float = 0.0, liquidity_ok: bool = True,
                 news_risk: bool = False) -> FilterResult:
        try:
            regime = self.classify_regime(mtf_data)
            tf_aligned = self.multi_timeframe_aligned(mtf_data, side)

            # Hard regime blocks (spec section 1)
            if regime == Regime.UNSAFE or regime == Regime.LOW_LIQUIDITY:
                return FilterResult(Decision.REJECT, 0.0, regime,
                                    "market UNSAFE / LOW_LIQUIDITY", tf_aligned, 0.0)
            if news_risk and regime not in (Regime.STRONG_UPTREND, Regime.STRONG_DOWNTREND):
                return FilterResult(Decision.REJECT, 0.0, regime,
                                    "NEWS_RISK and no strong trend", tf_aligned, 0.0)

            # Use the finest timeframe available for scoring
            score_data = mtf_data.get('1h')
            if score_data is None:
                score_data = mtf_data.get('15m')
            if score_data is None:
                score_data = next(iter(mtf_data.values()))
            sc = self.score(score_data, side, entry, sl, tp)
            rr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0

            # Reject conditions (spec section 5)
            reasons = []
            if rr < self.min_rr:
                reasons.append(f"R:R {rr:.2f} < {self.min_rr}")
            if spread_pct > 0.1:
                reasons.append(f"spread {spread_pct:.2f}% too high")
            if not liquidity_ok:
                reasons.append("liquidity too low")
            if not tf_aligned:
                reasons.append("counter HTF structure")
            if self.daily_loss_pct >= self.max_daily_loss_pct:
                reasons.append("daily loss limit hit")
            if self.consecutive_losses >= self.max_consecutive_losses:
                reasons.append("consecutive-loss cooldown")

            can_open, exp_reason = self.exposure.can_open(symbol, risk_pct)
            if not can_open:
                reasons.append(f"exposure: {exp_reason}")

            reject = bool(reasons) or sc.total_score < self.thresholds['no_trade']
            if reject:
                return FilterResult(Decision.REJECT, sc.total_score, regime,
                                    "; ".join(reasons) or "score below NO_TRADE",
                                    tf_aligned, rr,
                                    details={'score_breakdown': sc.reasons})

            # WATCH vs EXECUTE
            if sc.total_score < self.thresholds['normal'] or not tf_aligned:
                return FilterResult(Decision.WATCH, sc.total_score, regime,
                                    "score in WATCH band", tf_aligned, rr,
                                    details={'score_breakdown': sc.reasons})

            return FilterResult(Decision.EXECUTE, sc.total_score, regime,
                                "high-quality setup", tf_aligned, rr,
                                details={'score_breakdown': sc.reasons})
        except Exception as e:
            return FilterResult(Decision.REJECT, 0.0, Regime.RANGE,
                                f"filter error: {e}", False, 0.0)

    # ----------------------------------------------------------------
    # TRADE LIFECYCLE (loss control section 10)
    # ----------------------------------------------------------------
    def on_win(self):
        self.consecutive_losses = 0

    def on_loss(self, pnl_pct: float):
        self.consecutive_losses += 1
        self.daily_loss_pct += abs(pnl_pct)

    def reduce_risk_after_losses(self) -> float:
        """Scale risk down after consecutive losses (no martingale)."""
        if self.consecutive_losses >= 3:
            return 0.5
        if self.consecutive_losses == 2:
            return 0.75
        return 1.0
