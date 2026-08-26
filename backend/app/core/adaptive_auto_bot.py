"""
Adaptive Auto-Trading Bot - Self-Learning Trading System
Features: Multi-strategy, adaptive parameters, risk management, market regime detection
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger

from .adaptive_engine import AdaptiveEngine, TradeRecord, MarketRegime
from .indicator_engine import IndicatorEngine
from .candle_analyzer import CandleAnalyzer
from .risk_management_engine import RiskEngine
from .bot_state_manager import BotStateManager, BotState, StopTrigger
from .backtest_engine import BacktestEngine, BacktestConfig, BacktestStrategy


@dataclass
class AdaptiveBotConfig:
    """Adaptive bot configuration"""
    bot_id: str = "adaptive_bot"
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT"])
    timeframes: List[str] = field(default_factory=lambda: ["1h", "4h"])
    risk_per_trade: float = 2.0
    max_positions: int = 3
    min_confidence: float = 60.0
    adaptive_enabled: bool = True
    multi_timeframe: bool = True
    use_candle_patterns: bool = True
    use_smart_money: bool = True
    auto_optimize: bool = True
    recovery_enabled: bool = True


class AdaptiveAutoBot:
    """
    Adaptive Auto-Trading Bot
    - Self-learning from market data
    - Multi-strategy adaptation
    - Market regime detection
    - Smart money concepts
    - Advanced risk management
    - Multi-timeframe analysis
    """

    def __init__(self, config: Optional[AdaptiveBotConfig] = None):
        self.config = config or AdaptiveBotConfig()
        self.bot_id = self.config.bot_id

        # Core engines
        self.adaptive_engine = AdaptiveEngine()
        self.indicator_engine = IndicatorEngine()
        self.candle_analyzer = CandleAnalyzer()
        self.risk_engine = RiskEngine()
        self.bot_state_manager = BotStateManager(self.bot_id)
        self.backtest_engine = BacktestEngine()

        # Trading state
        self.is_running = False
        self.is_initialized = False
        self.positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.signals: List[Dict] = []

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0

        # Strategy weights (adaptive)
        self.strategy_weights = {
            'trend_following': 0.25,
            'mean_reversion': 0.25,
            'breakout': 0.25,
            'smart_money': 0.25
        }

        logger.info(f"🤖 Adaptive Bot {self.bot_id} created")

    async def initialize(self) -> bool:
        """Initialize the bot"""
        try:
            logger.info(f"Initializing bot {self.bot_id}...")
            self.is_initialized = True
            logger.info(f"✅ Bot {self.bot_id} initialized")
            return True
        except Exception as e:
            logger.error(f"Bot initialization error: {e}")
            return False

    async def start(self) -> bool:
        """Start the bot"""
        try:
            if not self.is_initialized:
                await self.initialize()

            self.is_running = True
            self.bot_state_manager.start()
            logger.info(f"🚀 Bot {self.bot_id} started")
            return True
        except Exception as e:
            logger.error(f"Bot start error: {e}")
            return False

    async def stop(self) -> bool:
        """Stop the bot"""
        try:
            self.is_running = False
            self.bot_state_manager.stop(StopTrigger.USER_PAUSE, "Bot stopped by user")
            logger.info(f"🛑 Bot {self.bot_id} stopped")
            return True
        except Exception as e:
            logger.error(f"Bot stop error: {e}")
            return False

    async def analyze_and_trade(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze market and execute trade if conditions met"""
        try:
            if not self.is_running:
                return None

            # Multi-timeframe analysis
            if self.config.multi_timeframe:
                signal = await self._multi_timeframe_analysis(symbol, data)
            else:
                signal = await self._single_timeframe_analysis(symbol, data)

            if signal is None:
                return None

            # Check confidence
            confidence = signal.get('confidence', 0)
            if confidence < self.config.min_confidence:
                return {'action': 'hold', 'reason': 'Low confidence', 'confidence': confidence}

            # Check adaptive engine
            if self.config.adaptive_enabled:
                if not self.adaptive_engine.should_trade(confidence):
                    return {'action': 'hold', 'reason': 'Adaptive engine rejected'}

            # Execute trade
            if signal.get('side') in ['BUY', 'SELL']:
                trade_result = await self._execute_signal(symbol, signal)
                return trade_result

            return {'action': 'hold', 'signal': signal}

        except Exception as e:
            logger.error(f"Analyze and trade error: {e}")
            self.bot_state_manager.record_error(str(e))
            return None

    async def _multi_timeframe_analysis(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Multi-timeframe analysis"""
        try:
            timeframe_signals = []

            for timeframe in self.config.timeframes:
                tf_data = data.get(timeframe, data.get('1h'))
                if tf_data is None:
                    continue

                signal = await self._single_timeframe_analysis(symbol, tf_data, timeframe)
                if signal:
                    timeframe_signals.append(signal)

            if not timeframe_signals:
                return None

            # Aggregate signals
            buy_count = sum(1 for s in timeframe_signals if s.get('side') == 'BUY')
            sell_count = sum(1 for s in timeframe_signals if s.get('side') == 'SELL')
            avg_confidence = sum(s.get('confidence', 0) for s in timeframe_signals) / len(timeframe_signals)

            # Require confluence (majority agreement)
            if buy_count > sell_count and buy_count >= len(timeframe_signals) / 2:
                side = 'BUY'
            elif sell_count > buy_count and sell_count >= len(timeframe_signals) / 2:
                side = 'SELL'
            else:
                return None

            return {
                'side': side,
                'confidence': avg_confidence,
                'timeframes': len(timeframe_signals),
                'confluence': max(buy_count, sell_count) / len(timeframe_signals),
                'signals': timeframe_signals
            }

        except Exception as e:
            logger.error(f"Multi-timeframe analysis error: {e}")
            return None

    async def _single_timeframe_analysis(self, symbol: str, data: Dict, timeframe: str = "1h") -> Optional[Dict]:
        """Single timeframe analysis"""
        try:
            import pandas as pd
            if not isinstance(data, pd.DataFrame):
                return None

            # Technical indicators
            indicators = self.indicator_engine.analyze(data)

            # Candle patterns
            patterns = {}
            if self.config.use_candle_patterns:
                patterns = self.candle_analyzer.analyze(data)

            # Market regime
            regime = self.adaptive_engine.analyze_market_state(data)

            # Smart money analysis
            smart_money = {}
            if self.config.use_smart_money:
                smart_money = indicators.get('smart_money', {})

            # Generate composite signal
            signal = self._generate_composite_signal(indicators, patterns, regime, smart_money)

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'side': signal.get('side', 'HOLD'),
                'confidence': signal.get('confidence', 0),
                'regime': regime.get('state', 'NEUTRAL'),
                'indicators_summary': {
                    'rsi': indicators.get('rsi', 50),
                    'trend': 'bullish' if indicators.get('ema_fast', 0) > indicators.get('ema_slow', 0) else 'bearish'
                }
            }

        except Exception as e:
            logger.error(f"Single timeframe analysis error: {e}")
            return None

    def _generate_composite_signal(self, indicators: Dict, patterns: Dict, regime: Dict, smart_money: Dict) -> Dict:
        """Generate composite signal from multiple sources"""
        score = 0
        reasons = []

        # Trend following (weight: 0.25)
        ema_fast = indicators.get('ema_fast', 0)
        ema_slow = indicators.get('ema_slow', 0)
        if ema_fast > ema_slow:
            score += self.strategy_weights['trend_following'] * 10
            reasons.append('Trend: bullish')
        elif ema_fast < ema_slow:
            score -= self.strategy_weights['trend_following'] * 10
            reasons.append('Trend: bearish')

        # Mean reversion (weight: 0.25)
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            score += self.strategy_weights['mean_reversion'] * 10
            reasons.append('RSI oversold')
        elif rsi > 70:
            score -= self.strategy_weights['mean_reversion'] * 10
            reasons.append('RSI overbought')

        # Breakout (weight: 0.25)
        regime_state = regime.get('state', 'NEUTRAL')
        if regime_state in ['BREAKOUT', 'BULLISH']:
            score += self.strategy_weights['breakout'] * 10
            reasons.append('Breakout detected')
        elif regime_state in ['BREAKDOWN', 'BEARISH']:
            score -= self.strategy_weights['breakout'] * 10
            reasons.append('Breakdown detected')

        # Smart money (weight: 0.25)
        if smart_money.get('order_blocks', {}).get('bullish'):
            score += self.strategy_weights['smart_money'] * 10
            reasons.append('Bullish order block')
        elif smart_money.get('order_blocks', {}).get('bearish'):
            score -= self.strategy_weights['smart_money'] * 10
            reasons.append('Bearish order block')

        # Candle patterns
        if patterns.get('bullish_engulfing'):
            score += 5
            reasons.append('Bullish engulfing')
        if patterns.get('bearish_engulfing'):
            score -= 5
            reasons.append('Bearish engulfing')

        # Determine side and confidence
        if score > 3:
            side = 'BUY'
        elif score < -3:
            side = 'SELL'
        else:
            side = 'HOLD'

        confidence = min(100, abs(score) * 5)

        return {
            'side': side,
            'confidence': confidence,
            'score': score,
            'reasons': reasons
        }

    async def _execute_signal(self, symbol: str, signal: Dict) -> Dict:
        """Execute trading signal"""
        try:
            side = signal.get('side')
            confidence = signal.get('confidence', 0)

            # Calculate position size
            position_size = self._calculate_position_size(symbol, confidence)

            if position_size <= 0:
                return {'action': 'hold', 'reason': 'Position size too small'}

            # Create trade record
            trade = {
                'symbol': symbol,
                'side': side,
                'quantity': position_size,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'signal': signal
            }

            # Update tracking
            self.positions[symbol] = trade
            self.trade_history.append(trade)
            self.total_trades += 1

            # Learn from trade
            if self.config.adaptive_enabled:
                self._learn_from_trade(trade)

            logger.info(f"✅ Trade executed: {symbol} {side} (confidence: {confidence:.1f}%)")
            return {'action': 'traded', 'trade': trade}

        except Exception as e:
            logger.error(f"Execute signal error: {e}")
            return {'action': 'error', 'error': str(e)}

    def _calculate_position_size(self, symbol: str, confidence: float) -> float:
        """Calculate position size based on confidence and risk"""
        try:
            # Base position size
            base_size = 0.01  # 0.01 BTC

            # Adjust by confidence
            confidence_multiplier = confidence / 100

            # Adjust by adaptive risk multiplier
            risk_multiplier = self.adaptive_engine.state.risk_multiplier

            # Final size
            size = base_size * confidence_multiplier * risk_multiplier

            return max(0.001, min(size, 0.1))  # Min 0.001, Max 0.1

        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            return 0.001

    def _learn_from_trade(self, trade: Dict):
        """Learn from trade outcome"""
        try:
            record = TradeRecord(
                timestamp=datetime.now(),
                symbol=trade.get('symbol', ''),
                action=trade.get('side', ''),
                entry_price=trade.get('price', 0),
                exit_price=trade.get('price', 0),
                profit=trade.get('pnl', 0),
                profit_percent=trade.get('pnl_percent', 0),
                market_regime=self.adaptive_engine.current_regime.value,
                strategy_used='adaptive_composite',
                confidence=trade.get('confidence', 0)
            )
            self.adaptive_engine.learn_from_trade(record)
        except Exception as e:
            logger.error(f"Learn from trade error: {e}")

    def get_status(self) -> Dict:
        """Get bot status"""
        return {
            'bot_id': self.bot_id,
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            'total_pnl': self.total_pnl,
            'open_positions': len(self.positions),
            'bot_state': self.bot_state_manager.get_state(),
            'adaptive_params': self.adaptive_engine.get_adaptive_params(),
            'strategy_weights': self.strategy_weights
        }

    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        return {
            'bot_status': self.get_status(),
            'adaptive_learning': self.adaptive_engine.get_learning_report(),
            'bot_state': self.bot_state_manager.get_stats(),
            'trade_history': self.trade_history[-50:],
            'strategy_weights': self.strategy_weights
        }

    def optimize_strategy_weights(self):
        """Auto-optimize strategy weights based on performance"""
        try:
            if not self.config.auto_optimize:
                return

            # Get performance per strategy
            performance = self.adaptive_engine.regime_performance

            if not performance:
                return

            # Calculate weights based on profit
            total_profit = sum(p.get('profit', 0) for p in performance.values())

            if total_profit > 0:
                for strategy, perf in performance.items():
                    if strategy in self.strategy_weights:
                        profit_ratio = perf.get('profit', 0) / total_profit
                        # Smooth update
                        self.strategy_weights[strategy] = (
                            self.strategy_weights[strategy] * 0.8 + profit_ratio * 0.2
                        )

                # Normalize weights
                total_weight = sum(self.strategy_weights.values())
                if total_weight > 0:
                    for key in self.strategy_weights:
                        self.strategy_weights[key] /= total_weight

                logger.info(f"Strategy weights optimized: {self.strategy_weights}")

        except Exception as e:
            logger.error(f"Strategy optimization error: {e}")
