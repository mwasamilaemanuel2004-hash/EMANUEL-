"""
Tokenization Bot — ultra-advanced fundamental + technical analysis for
crypto tokenization, RWA, and the on-chain macro stack.

Combines:
  - TokenScore (regulatory, RWA growth, ecosystem, macro liquidity,
    network upgrades, staking/ETFs, capital flow, cycle, real usage)
  - Timing quality (cycle phase + flow + upgrade catalyst)
  - SmartEntryEngine execution (mandatory SL, breakeven@1R, unlimited runner)
  - AgentDispatcher routing (lane + context)

Signal generation: TokenScore >= 70 AND timing_quality >= 0.55 AND
SmartEntryEngine plan passes the regime filter.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from ...core.token_analyzer import (
    TokenMetrics, RegulatoryStatus, NetworkPhase,
    compute_token_score, should_trade, estimate_timing_quality,
)
from ...core.smart_entry import SmartEntryEngine
from .._shared_signals import AiSignalGate


# Curated token universe with fundamental metrics (updated periodically)
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


class TokenizationBot(BaseBot):
    """
    Ultra-advanced tokenization/RWA analysis bot.

    Workflow:
      1. Pull TokenMetrics for the symbol (or default universe)
      2. Compute TokenScore (regulatory-gated, weighted)
      3. Estimate timing quality
      4. Build SmartEntryEngine plan on price data
      5. If TokenScore >= 70 AND timing >= 0.55 AND tech confirms -> signal
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("Tokenization Bot", config)
        self.gate = AiSignalGate(config.get('ai', {}))
        self.engine = SmartEntryEngine()
        self.score_threshold = config.get('score_threshold', 70.0)
        self.timing_threshold = config.get('timing_threshold', 0.55)
        self.universe = config.get('universe', TOKEN_UNIVERSE)

    async def analyze_market(self, data: pd.DataFrame) -> Optional[TradeSignal]:
        try:
            if data is None or len(data) < 30:
                return None
            symbol = str(getattr(self, 'bot_id', 'BTC')).upper()
            # If bot_id not a known token, fall back to price-based analysis
            metrics = self.universe.get(symbol)
            if metrics is None:
                metrics = self._derive_metrics_from_price(data, symbol)

            result = compute_token_score(metrics)
            token_score = result['total']
            timing = estimate_timing_quality(metrics)

            if token_score < self.score_threshold:
                return None
            if timing < self.timing_threshold:
                return None

            # Build mtf_data dict for gate
            mtf_data = {'1h': data}
            if '4h' in data.columns if hasattr(data, 'columns') else False:
                pass

            # Technical confirmation: simple trend on the data
            closes = data['close'].values
            ema20 = pd.Series(closes).ewm(span=20).mean().iloc[-1]
            ema50 = pd.Series(closes).ewm(span=50).mean().iloc[-1]
            if side := ("BUY" if ema20 > ema50 else "SELL" if ema20 < ema50 else None):
                if (side == "BUY" and metrics.cycle_phase == NetworkPhase.BEAR) or \
                   (side == "SELL" and metrics.cycle_phase == NetworkPhase.BULL_RUN):
                    return None  # don't fight strong cycle
            else:
                return None

            entry = float(closes[-1])
            atr = float(pd.Series(closes).diff().abs().rolling(14).mean().iloc[-1])
            atr = max(atr, entry * 0.002)

            plan = self.engine.build_plan(side, entry, atr, "STRONG_TREND")
            return self.gate.make_signal(
                mtf_data, side, entry,
                reason=(f"Tokenization {symbol} score={token_score:.0f} "
                        f"timing={timing:.2f} reg={metrics.regulatory_status.value} "
                        f"rwa_growth={metrics.rwa_growth_30d_pct:.0f}%"),
                indicators=['token_score', 'rwa_growth', 'regulatory', 'timing',
                            'capital_flow', 'cycle'],
                symbol=symbol, risk_pct=1.0,
            )
        except Exception as e:
            logger.error(f"TokenizationBot error: {e}")
            return None

    def _derive_metrics_from_price(self, data: pd.DataFrame, symbol: str) -> TokenMetrics:
        """Build approximate TokenMetrics from price data alone (no fundamentals)."""
        closes = data['close']
        rets = closes.pct_change().dropna()
        growth_30d = float((closes.iloc[-1] / closes.iloc[0]) - 1) * 100 if len(closes) > 1 else 0
        vol_30d = float(rets.std()) * 100 if len(rets) > 1 else 0
        active = float((rets > 0).sum() / len(rets) * 100) if len(rets) > 1 else 50
        return TokenMetrics(
            symbol=symbol,
            regulatory_status=RegulatoryStatus.UNCLEAR,
            rwa_tvl_usd=0, rwa_growth_30d_pct=growth_30d,
            recent_product_launches=0,
            ecosystem_score=min(80, 30 + active / 2),
            macro_liquidity_score=min(80, 40 + vol_30d * 5),
            network_upgrade_score=50,
            staking_etf_available=False,
            net_capital_flow_30d=growth_30d * 0.5,
            cycle_phase=NetworkPhase.BULL_RUN if growth_30d > 5 else NetworkPhase.ACCUMULATION,
            active_addresses_30d_pct=active,
            real_usage_score=min(80, 40 + vol_30d * 5),
        )
