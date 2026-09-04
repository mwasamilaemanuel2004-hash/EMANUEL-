"""
Enhanced Crypto Bot - ultra-advanced fundamental + technical analysis
combining TokenScore gating, SmartEntryEngine execution, ADX trend
strength, volume confirmation, and EMA100 trend direction filters.

Signal generation pipeline:
  1. compute_enhanced_token_score >= score_threshold (fundamental gate)
  2. estimate_timing_quality >= timing_threshold (cycle/flow timing)
  3. ADX > 18 (trend strength filter)
  4. Volume > 20-period average (volume confirmation)
  5. Price vs EMA100 (trend direction filter)
  6. SmartEntryEngine plan with min_rr=2.5 (execution)
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from ...core.token_analyzer import (
    TokenMetrics, RegulatoryStatus, NetworkPhase,
    compute_token_score, compute_enhanced_token_score, should_trade, estimate_timing_quality,
)
from ...core.smart_entry import SmartEntryEngine, SmartPlan


# Curated 8-token universe with comprehensive fundamental metrics
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
    "MATIC": TokenMetrics(
        symbol="MATIC", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=300_000_000, rwa_growth_30d_pct=18.0,
        recent_product_launches=2, ecosystem_score=85,
        macro_liquidity_score=60, network_upgrade_score=88,
        staking_etf_available=False, net_capital_flow_30d=8.0,
        cycle_phase=NetworkPhase.ACCUMULATION,
        active_addresses_30d_pct=6.0, real_usage_score=80,
        circulating_supply=9_300_000_000, total_supply=10_000_000_000, max_supply=10_000_000_000,
        annual_inflation_pct=3.0, unlock_30d_pct=1.5, unlock_90d_pct=4.0,
        team_investor_pct=15.0, top10_holder_pct=20.0,
        annual_fees_usd=80_000_000, annual_revenue_usd=50_000_000,
        annual_burn_usd=10_000_000, staking_yield_pct=4.5, daily_volume_usd=500_000_000,
        price=0.45, mcap_usd=4_185_000_000, fdv_usd=4_500_000_000,
        price_ath=2.92, price_200d_avg=0.55, active_addresses=350000,
    ),
    "LINK": TokenMetrics(
        symbol="LINK", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=600_000_000, rwa_growth_30d_pct=25.0,
        recent_product_launches=4, ecosystem_score=90,
        macro_liquidity_score=65, network_upgrade_score=85,
        staking_etf_available=False, net_capital_flow_30d=12.0,
        cycle_phase=NetworkPhase.UPGRADE_CATALYST,
        active_addresses_30d_pct=8.0, real_usage_score=88,
        circulating_supply=587_000_000, total_supply=1_000_000_000, max_supply=1_000_000_000,
        annual_inflation_pct=4.0, unlock_30d_pct=1.0, unlock_90d_pct=3.0,
        team_investor_pct=25.0, top10_holder_pct=30.0,
        annual_fees_usd=120_000_000, annual_revenue_usd=80_000_000,
        annual_burn_usd=0, staking_yield_pct=5.0, daily_volume_usd=800_000_000,
        price=14.50, mcap_usd=8_511_500_000, fdv_usd=14_500_000_000,
        price_ath=52.70, price_200d_avg=12.00, active_addresses=200000,
    ),
    "AAVE": TokenMetrics(
        symbol="AAVE", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=1_200_000_000, rwa_growth_30d_pct=22.0,
        recent_product_launches=3, ecosystem_score=88,
        macro_liquidity_score=62, network_upgrade_score=82,
        staking_etf_available=False, net_capital_flow_30d=18.0,
        cycle_phase=NetworkPhase.BULL_RUN,
        active_addresses_30d_pct=12.0, real_usage_score=85,
        circulating_supply=14_800_000, total_supply=16_000_000, max_supply=16_000_000,
        annual_inflation_pct=2.0, unlock_30d_pct=0.5, unlock_90d_pct=1.5,
        team_investor_pct=20.0, top10_holder_pct=35.0,
        annual_fees_usd=180_000_000, annual_revenue_usd=120_000_000,
        annual_burn_usd=20_000_000, staking_yield_pct=6.0, daily_volume_usd=400_000_000,
        price=245, mcap_usd=3_626_000_000, fdv_usd=3_920_000_000,
        price_ath=666, price_200d_avg=180, active_addresses=75000,
    ),
    "UNI": TokenMetrics(
        symbol="UNI", regulatory_status=RegulatoryStatus.COMPLIANT,
        rwa_tvl_usd=400_000_000, rwa_growth_30d_pct=15.0,
        recent_product_launches=2, ecosystem_score=86,
        macro_liquidity_score=58, network_upgrade_score=78,
        staking_etf_available=False, net_capital_flow_30d=6.0,
        cycle_phase=NetworkPhase.ACCUMULATION,
        active_addresses_30d_pct=5.0, real_usage_score=82,
        circulating_supply=600_000_000, total_supply=1_000_000_000, max_supply=1_000_000_000,
        annual_inflation_pct=2.5, unlock_30d_pct=1.0, unlock_90d_pct=3.0,
        team_investor_pct=20.0, top10_holder_pct=25.0,
        annual_fees_usd=350_000_000, annual_revenue_usd=280_000_000,
        annual_burn_usd=0, staking_yield_pct=3.0, daily_volume_usd=300_000_000,
        price=6.20, mcap_usd=3_720_000_000, fdv_usd=6_200_000_000,
        price_ath=44.92, price_200d_avg=7.50, active_addresses=150000,
    ),
}


def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Average Directional Index (ADX)."""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    condition = plus_dm > minus_dm
    plus_dm = plus_dm.where(condition, 0)
    minus_dm = minus_dm.where(~condition, 0)

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/period, min_periods=period).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, min_periods=period).mean() / atr)
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.ewm(alpha=1/period, min_periods=period).mean()
    return adx


def compute_ema(series: pd.Series, span: int) -> pd.Series:
    """Compute Exponential Moving Average."""
    return series.ewm(span=span, adjust=False).mean()


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


class EnhancedCryptoBot(BaseBot):
    """
    Ultra-advanced crypto analysis bot combining fundamental gating,
    technical filters, and SmartEntryEngine execution.

    Signal generation pipeline:
      1. compute_enhanced_token_score >= score_threshold (fundamental gate)
      2. estimate_timing_quality >= timing_threshold (cycle/flow timing)
      3. ADX > 18 (trend strength filter)
      4. Volume > 20-period average (volume confirmation)
      5. Price vs EMA100 (trend direction filter)
      6. SmartEntryEngine plan with min_rr=2.5 (execution)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("Enhanced Crypto Bot", config)
        self.engine = SmartEntryEngine(min_rr=2.5)
        self.score_threshold = config.get('score_threshold', 65.0)
        self.timing_threshold = config.get('timing_threshold', 0.50)
        self.adx_threshold = config.get('adx_threshold', 18.0)
        self.volume_ma_period = config.get('volume_ma_period', 20)
        self.ema_trend_period = config.get('ema_trend_period', 100)
        self.universe = config.get('universe', TOKEN_UNIVERSE)
        self.risk_pct = config.get('risk_pct', 1.0)

    async def analyze_market(self, data: pd.DataFrame) -> Optional[TradeSignal]:
        """
        Main analysis method implementing the full signal generation pipeline.

        Args:
            data: DataFrame with columns [open, high, low, close, volume]

        Returns:
            TradeSignal if all filters pass, None otherwise
        """
        try:
            if data is None or len(data) < 120:
                logger.debug("Insufficient data for analysis")
                return None

            symbol = str(getattr(self, 'bot_id', 'BTC')).upper()
            metrics = self.universe.get(symbol)
            if metrics is None:
                metrics = self._derive_metrics_from_price(data, symbol)

            # === STEP 1: Fundamental Gate (compute_enhanced_token_score) ===
            enhanced_result = compute_enhanced_token_score(metrics)
            token_score = enhanced_result['total']
            base_score = enhanced_result['base_score']
            dilution_score = enhanced_result['dilution_score']
            capture_score = enhanced_result['capture_score']
            upside_potential = enhanced_result['upside_potential_pct']
            risk_reward = enhanced_result['risk_reward_ratio']

            if token_score < self.score_threshold:
                logger.debug(f"{symbol}: token_score {token_score:.1f} < threshold {self.score_threshold}")
                return None

            # === STEP 2: Timing Quality ===
            timing = estimate_timing_quality(metrics)
            if timing < self.timing_threshold:
                logger.debug(f"{symbol}: timing {timing:.2f} < threshold {self.timing_threshold}")
                return None

            # === Technical Analysis ===
            closes = data['close']
            highs = data['high']
            lows = data['low']
            volumes = data['volume']

            # === STEP 3: ADX Trend Strength Filter (ADX > 18) ===
            adx_series = compute_adx(highs, lows, closes, period=14)
            current_adx = float(adx_series.iloc[-1])

            if current_adx <= self.adx_threshold:
                logger.debug(f"{symbol}: ADX {current_adx:.1f} <= threshold {self.adx_threshold}")
                return None

            # === STEP 4: Volume Confirmation (volume > 20-period average) ===
            volume_ma = volumes.rolling(window=self.volume_ma_period).mean()
            current_volume = float(volumes.iloc[-1])
            avg_volume = float(volume_ma.iloc[-1])

            if current_volume <= avg_volume:
                logger.debug(f"{symbol}: volume {current_volume:.0f} <= avg {avg_volume:.0f}")
                return None

            # === STEP 5: Trend Direction Filter (price vs EMA100) ===
            ema100 = compute_ema(closes, self.ema_trend_period)
            current_price = float(closes.iloc[-1])
            current_ema100 = float(ema100.iloc[-1])

            if current_price > current_ema100:
                side = "BUY"
            elif current_price < current_ema100:
                side = "SELL"
            else:
                logger.debug(f"{symbol}: price exactly at EMA100, no direction")
                return None

            # === Cycle Phase Alignment ===
            if (side == "BUY" and metrics.cycle_phase == NetworkPhase.BEAR) or \
               (side == "SELL" and metrics.cycle_phase == NetworkPhase.BULL_RUN):
                logger.debug(f"{symbol}: {side} conflicts with cycle phase {metrics.cycle_phase}")
                return None

            # === STEP 6: SmartEntryEngine Plan (min_rr=2.5) ===
            atr = float(compute_atr(highs, lows, closes, period=14).iloc[-1])
            atr = max(atr, current_price * 0.002)

            # Determine regime based on ADX and volume
            if current_adx > 30:
                regime = "STRONG_TREND"
            elif current_adx > 22:
                regime = "WEAK_TREND"
            else:
                regime = "RANGE"

            plan = self.engine.build_plan(side, current_price, atr, regime)

            # Validate risk-reward meets minimum
            risk = abs(plan.entry - plan.sl)
            reward = abs(plan.tp2 - plan.entry)
            if risk > 0 and reward / risk < 2.5:
                logger.debug(f"{symbol}: RR {reward/risk:.1f} < 2.5 minimum")
                return None

            # === Build Signal ===
            confidence = min(95.0, token_score * 0.7 + current_adx * 0.3)
            strength = (
                SignalStrength.VERY_STRONG if confidence >= 85
                else SignalStrength.STRONG if confidence >= 70
                else SignalStrength.MODERATE
            )
            quality = (
                TradeQuality.PERFECT if confidence >= 90
                else TradeQuality.EXCELLENT if confidence >= 80
                else TradeQuality.GOOD if confidence >= 70
                else TradeQuality.AVERAGE
            )

            # Compile detailed metadata with all fundamental scores
            metadata = {
                'symbol': symbol,
                'side': side,
                'token_score': token_score,
                'base_score': base_score,
                'dilution_score': dilution_score,
                'capture_score': capture_score,
                'upside_potential_pct': upside_potential,
                'risk_reward_ratio': risk_reward,
                'timing_quality': timing,
                'adx': current_adx,
                'volume': current_volume,
                'volume_avg': avg_volume,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
                'ema100': current_ema100,
                'atr': atr,
                'regime': regime,
                'plan_entry': plan.entry,
                'plan_sl': plan.sl,
                'plan_tp1': plan.tp1,
                'plan_tp2': plan.tp2,
                'plan_runner_size': plan.runner_size,
                'cycle_phase': metrics.cycle_phase.value,
                'regulatory_status': metrics.regulatory_status.value,
                'rwa_growth_30d': metrics.rwa_growth_30d_pct,
                'ecosystem_score': metrics.ecosystem_score,
                'real_usage_score': metrics.real_usage_score,
                'net_capital_flow_30d': metrics.net_capital_flow_30d,
                'enhanced_breakdown': enhanced_result.get('breakdown', {}),
            }

            reason = (
                f"Enhanced {symbol} {side} score={token_score:.0f} "
                f"base={base_score:.0f} dilution={dilution_score:.0f} "
                f"capture={capture_score:.0f} upside={upside_potential:.0f}% "
                f"rr={risk_reward:.1f} timing={timing:.2f} "
                f"adx={current_adx:.1f} vol_ratio={current_volume/avg_volume:.2f} "
                f"regime={regime}"
            )

            signal = TradeSignal(
                action=side,
                confidence=confidence,
                strength=strength,
                quality=quality,
                entry_price=plan.entry,
                stop_loss=plan.sl,
                take_profit=plan.tp2,
                position_size=self.risk_pct,
                reason=reason,
                supporting_indicators=[
                    'enhanced_token_score', 'base_score', 'dilution_score',
                    'capture_score', 'upside_potential', 'risk_reward',
                    'timing_quality', 'adx', 'volume_confirmation',
                    'ema100_trend', 'cycle_phase', 'regulatory_status',
                    'rwa_growth', 'ecosystem', 'real_usage', 'capital_flow',
                ],
                ai_reasoning=(
                    f"score={token_score:.0f} timing={timing:.2f} "
                    f"adx={current_adx:.1f} regime={regime} rr={risk_reward:.1f}"
                ),
                risk_score=100 - confidence,
                expected_return=abs(plan.tp2 - plan.entry) / plan.entry * 100,
                time_horizon='MEDIUM',
                metadata=metadata,
            )

            logger.info(
                f"Enhanced {symbol} {signal.action} signal: "
                f"confidence={confidence:.0f} score={token_score:.0f} "
                f"adx={current_adx:.1f} rr={risk_reward:.1f}"
            )
            return signal

        except Exception as e:
            logger.error(f"EnhancedCryptoBot error: {e}")
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

    def scan_universe(self, data_dict: Dict[str, pd.DataFrame]) -> List[TradeSignal]:
        """
        Scan all tokens in the universe and return valid signals.

        Args:
            data_dict: Dict mapping symbol -> DataFrame with OHLCV data

        Returns:
            List of TradeSignal objects for tokens passing all filters
        """
        signals = []
        for symbol, data in data_dict.items():
            try:
                # Temporarily set bot_id for symbol-specific analysis
                original_bot_id = getattr(self, 'bot_id', None)
                self.bot_id = symbol
                import asyncio
                signal = asyncio.run(self.analyze_market(data))
                if signal:
                    signals.append(signal)
                if original_bot_id is not None:
                    self.bot_id = original_bot_id
            except Exception as e:
                logger.debug(f"Scan error for {symbol}: {e}")
                continue
        return signals

    def get_universe_symbols(self) -> List[str]:
        """Return list of symbols in the token universe."""
        return list(self.universe.keys())

    def get_token_metrics(self, symbol: str) -> Optional[TokenMetrics]:
        """Return metrics for a specific token."""
        return self.universe.get(symbol.upper())

    def get_fundamental_summary(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Return comprehensive fundamental analysis for a token.

        Args:
            symbol: Token symbol (e.g., "BTC")

        Returns:
            Dict with all fundamental scores and breakdowns
        """
        metrics = self.universe.get(symbol.upper())
        if metrics is None:
            return None

        enhanced = compute_enhanced_token_score(metrics)
        timing = estimate_timing_quality(metrics)

        return {
            'symbol': symbol.upper(),
            'token_score': enhanced['total'],
            'base_score': enhanced['base_score'],
            'dilution_score': enhanced['dilution_score'],
            'capture_score': enhanced['capture_score'],
            'valuation_grade': enhanced['valuation_grade'],
            'upside_potential_pct': enhanced['upside_potential_pct'],
            'risk_reward_ratio': enhanced['risk_reward_ratio'],
            'timing_quality': timing,
            'cycle_phase': metrics.cycle_phase.value,
            'regulatory_status': metrics.regulatory_status.value,
            'rwa_tvl_usd': metrics.rwa_tvl_usd,
            'rwa_growth_30d_pct': metrics.rwa_growth_30d_pct,
            'ecosystem_score': metrics.ecosystem_score,
            'real_usage_score': metrics.real_usage_score,
            'net_capital_flow_30d': metrics.net_capital_flow_30d,
            'staking_etf_available': metrics.staking_etf_available,
            'breakdown': enhanced.get('breakdown', {}),
        }

    def get_strategies(self) -> List[str]:
        """Return list of strategies used by this bot."""
        return [
            'enhanced_token_scoring',
            'adx_trend_strength',
            'volume_confirmation',
            'ema100_trend_direction',
            'smart_entry_execution',
            'cycle_phase_alignment',
        ]

    def get_indicators(self) -> List[str]:
        """Return list of indicators used by this bot."""
        return [
            'ADX', 'EMA100', 'Volume', 'ATR',
            'TokenScore', 'DilutionScore', 'CaptureScore',
            'UpsidePotential', 'RiskReward', 'TimingQuality',
        ]
