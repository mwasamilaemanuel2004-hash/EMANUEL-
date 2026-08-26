"""
System Coordinator - Central Trading Orchestration
Coordinates all trading engines, bots, risk management, and notifications
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from .trading_engine import TradingEngine, Order, OrderStatus, PositionSide
from .risk_management_engine import RiskEngine
from .bot_state_manager import BotStateManager, BotState, StopTrigger
from .adaptive_engine import AdaptiveEngine, TradeRecord, MarketRegime
from .indicator_engine import IndicatorEngine
from .candle_analyzer import CandleAnalyzer


class SystemMode(Enum):
    """System operating modes"""
    LIVE = "LIVE"
    PAPER = "PAPER"
    BACKTEST = "BACKTEST"
    PAUSED = "PAUSED"


@dataclass
class SystemConfig:
    """System configuration"""
    mode: SystemMode = SystemMode.PAPER
    max_concurrent_trades: int = 5
    max_daily_loss_percent: float = 5.0
    max_drawdown_percent: float = 10.0
    risk_per_trade_percent: float = 2.0
    enable_adaptive: bool = True
    enable_multi_trade: bool = False
    notification_on_trade: bool = True
    notification_on_stop: bool = True
    auto_recovery: bool = True
    trading_pairs: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    timeframes: List[str] = field(default_factory=lambda: ["1h", "4h", "1d"])


class SystemCoordinator:
    """
    Central System Coordinator
    - Orchestrates all trading engines
    - Manages bot lifecycle
    - Coordinates risk management
    - Handles adaptive learning
    - Multi-trade coordination
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        self.start_time = datetime.now()

        # Core engines
        self.trading_engine = TradingEngine()
        self.risk_engine = RiskEngine()
        self.bot_state_manager = BotStateManager("main_coordinator")
        self.adaptive_engine = AdaptiveEngine()
        self.indicator_engine = IndicatorEngine()
        self.candle_analyzer = CandleAnalyzer()

        # Trading bots registry
        self.registered_bots: Dict[str, Any] = {}
        self.active_bots: Dict[str, Any] = {}

        # System state
        self.is_running = False
        self.current_mode = self.config.mode
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0
        self.trade_count_today: int = 0

        # Multi-trade management
        self.multi_trade_enabled = self.config.enable_multi_trade
        self.max_concurrent = self.config.max_concurrent_trades
        self.pending_orders: List[Dict] = []

        # Performance tracking
        self.performance_history: List[Dict] = []
        self.daily_stats: Dict[str, Any] = {}

        logger.info("🎯 System Coordinator initialized")

    # ============================================
    # SYSTEM LIFECYCLE
    # ============================================

    async def start(self) -> bool:
        """Start the system coordinator"""
        try:
            logger.info("🚀 Starting System Coordinator...")
            self.is_running = True

            # Initialize bots
            await self._initialize_bots()

            # Start bot state manager
            self.bot_state_manager.start()

            logger.info(f"✅ System Coordinator started in {self.current_mode.value} mode")
            self._log_system_event("SYSTEM_STARTED", f"Mode: {self.current_mode.value}")
            return True

        except Exception as e:
            logger.error(f"System start error: {e}")
            self.is_running = False
            return False

    async def stop(self) -> bool:
        """Stop the system coordinator"""
        try:
            logger.info("🛑 Stopping System Coordinator...")
            self.is_running = False

            # Stop all bots
            for bot_id, bot in self.active_bots.items():
                try:
                    if hasattr(bot, 'stop'):
                        await bot.stop()
                except Exception as e:
                    logger.error(f"Error stopping bot {bot_id}: {e}")

            self.active_bots.clear()

            logger.info("✅ System Coordinator stopped")
            self._log_system_event("SYSTEM_STOPPED", "All bots stopped")
            return True

        except Exception as e:
            logger.error(f"System stop error: {e}")
            return False

    async def pause(self) -> bool:
        """Pause the system"""
        self.current_mode = SystemMode.PAUSED
        self.bot_state_manager.pause(StopTrigger.USER_PAUSE, "System paused by user")
        logger.info("⏸️ System paused")
        return True

    async def resume(self) -> bool:
        """Resume the system"""
        self.bot_state_manager.resume()
        self.current_mode = SystemMode.PAPER if self.current_mode == SystemMode.PAUSED else self.current_mode
        logger.info("▶️ System resumed")
        return True

    # ============================================
    # BOT MANAGEMENT
    # ============================================

    def register_bot(self, bot_id: str, bot_instance: Any) -> bool:
        """Register a trading bot"""
        try:
            self.registered_bots[bot_id] = bot_instance
            logger.info(f"Bot registered: {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Bot registration error: {e}")
            return False

    async def start_bot(self, bot_id: str) -> bool:
        """Start a specific bot"""
        try:
            if bot_id not in self.registered_bots:
                logger.error(f"Bot not registered: {bot_id}")
                return False

            bot = self.registered_bots[bot_id]
            if hasattr(bot, 'start'):
                await bot.start()

            self.active_bots[bot_id] = bot
            logger.info(f"Bot started: {bot_id}")
            return True

        except Exception as e:
            logger.error(f"Bot start error: {e}")
            return False

    async def stop_bot(self, bot_id: str) -> bool:
        """Stop a specific bot"""
        try:
            if bot_id in self.active_bots:
                bot = self.active_bots[bot_id]
                if hasattr(bot, 'stop'):
                    await bot.stop()
                del self.active_bots[bot_id]
                logger.info(f"Bot stopped: {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Bot stop error: {e}")
            return False

    async def _initialize_bots(self):
        """Initialize all registered bots"""
        for bot_id, bot in self.registered_bots.items():
            try:
                if hasattr(bot, 'initialize'):
                    await bot.initialize()
                    logger.info(f"Bot initialized: {bot_id}")
            except Exception as e:
                logger.error(f"Bot initialization error: {e}")

    # ============================================
    # TRADING COORDINATION
    # ============================================

    async def execute_trade(self, symbol: str, side: str, quantity: float,
                           price: float = 0.0, order_type: str = "MARKET",
                           stop_loss: float = None, take_profit: float = None) -> Dict:
        """Execute a coordinated trade with full risk management"""
        try:
            # Pre-trade checks
            if not self.is_running:
                return {'success': False, 'error': 'System not running'}

            if self.current_mode == SystemMode.PAUSED:
                return {'success': False, 'error': 'System paused' }

            # Check concurrent trades limit
            active_positions = len(self.trading_engine.positions)
            if active_positions >= self.max_concurrent:
                return {'success': False, 'error': f'Max concurrent trades ({self.max_concurrent}) reached'}

            # Risk validation
            risk_check = self.risk_engine.validate_trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=price,
                stop_loss=stop_loss
            )

            if not risk_check.get('approved', True):
                logger.warning(f"Trade rejected by risk engine: {risk_check.get('reason')}")
                return {'success': False, 'error': risk_check.get('reason', 'Risk check failed')}

            # Adaptive engine check
            if self.config.enable_adaptive:
                confidence = self._calculate_confidence(symbol, side)
                if not self.adaptive_engine.should_trade(confidence):
                    return {'success': False, 'error': 'Adaptive engine rejected trade', 'confidence': confidence}

            # Execute order
            result = await self.trading_engine.execute_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type=order_type
            )

            if result.get('success'):
                # Update tracking
                self.trade_count_today += 1
                self._update_daily_stats(result)

                # Learn from trade
                if self.config.enable_adaptive:
                    self._record_trade_for_learning(result)

                # Check stop conditions
                self.bot_state_manager.update_stats(result)

                logger.info(f"✅ Coordinated trade executed: {symbol} {side} {quantity}")

            return result

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def execute_multi_trade(self, orders: List[Dict]) -> Dict:
        """Execute multiple coordinated trades"""
        try:
            if not self.multi_trade_enabled:
                return {'success': False, 'error': 'Multi-trade not enabled'}

            if len(orders) > self.max_concurrent:
                return {'success': False, 'error': f'Max {self.max_concurrent} orders allowed'}

            results = []
            for order in orders:
                result = await self.execute_trade(
                    symbol=order.get('symbol'),
                    side=order.get('side'),
                    quantity=order.get('quantity'),
                    price=order.get('price', 0),
                    stop_loss=order.get('stop_loss'),
                    take_profit=order.get('take_profit')
                )
                results.append(result)

            successful = sum(1 for r in results if r.get('success'))
            return {
                'success': True,
                'results': results,
                'total': len(results),
                'successful': successful,
                'failed': len(results) - successful
            }

        except Exception as e:
            logger.error(f"Multi-trade execution error: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_confidence(self, symbol: str, side: str) -> float:
        """Calculate trade confidence using indicators and patterns"""
        try:
            # Get adaptive parameters
            params = self.adaptive_engine.get_adaptive_indicator_params()

            # Base confidence from win rate
            base_confidence = self.adaptive_engine.state.win_rate * 100

            # Adjust based on market regime
            regime = self.adaptive_engine.current_regime
            if regime in [MarketRegime.BULLISH, MarketRegime.BEARISH]:
                base_confidence *= 1.1
            elif regime == MarketRegime.HIGH_VOLATILITY:
                base_confidence *= 0.8

            return min(100, max(0, base_confidence))

        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 50.0

    def _record_trade_for_learning(self, trade_result: Dict):
        """Record trade for adaptive learning"""
        try:
            record = TradeRecord(
                timestamp=datetime.now(),
                symbol=trade_result.get('symbol', ''),
                action=trade_result.get('side', ''),
                entry_price=trade_result.get('price', 0),
                exit_price=trade_result.get('price', 0),
                profit=trade_result.get('pnl', 0),
                profit_percent=trade_result.get('pnl_percent', 0),
                market_regime=self.adaptive_engine.current_regime.value,
                strategy_used='coordinated',
                confidence=self._calculate_confidence(
                    trade_result.get('symbol', ''),
                    trade_result.get('side', '')
                )
            )
            self.adaptive_engine.learn_from_trade(record)
        except Exception as e:
            logger.error(f"Record trade error: {e}")

    def _update_daily_stats(self, trade_result: Dict):
        """Update daily trading statistics"""
        try:
            pnl = trade_result.get('pnl', 0)
            self.daily_pnl += pnl
            self.total_pnl += pnl

            # Check daily loss limit
            if self.daily_pnl < 0 and abs(self.daily_pnl) > self.config.max_daily_loss_percent:
                logger.warning(f"⚠️ Daily loss limit approaching: {self.daily_pnl:.2f}%")
                self.bot_state_manager.pause(
                    StopTrigger.DAILY_LOSS_LIMIT,
                    f"Daily loss limit reached: {self.daily_pnl:.2f}%"
                )

        except Exception as e:
            logger.error(f"Daily stats update error: {e}")

    # ============================================
    # ANALYSIS COORDINATION
    # ============================================

    async def analyze_market(self, symbol: str, data: Any) -> Dict:
        """Comprehensive market analysis using all engines"""
        try:
            # Technical indicators
            indicators = self.indicator_engine.analyze(data)

            # Candlestick patterns
            patterns = self.candle_analyzer.analyze(data)

            # Market regime
            regime = self.adaptive_engine.analyze_market_state(data)

            # Risk assessment
            risk = self.risk_engine.assess_market_risk(data)

            # Generate signal
            signal = self._generate_signal(indicators, patterns, regime, risk)

            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'indicators': indicators,
                'patterns': patterns,
                'regime': regime,
                'risk': risk,
                'signal': signal,
                'confidence': self._calculate_confidence(symbol, signal.get('side', 'BUY'))
            }

        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return {'error': str(e)}

    def _generate_signal(self, indicators: Dict, patterns: Dict, regime: Dict, risk: Dict) -> Dict:
        """Generate trading signal from analysis"""
        try:
            signal_score = 0
            reasons = []

            # RSI signal
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                signal_score += 2
                reasons.append('RSI oversold')
            elif rsi > 70:
                signal_score -= 2
                reasons.append('RSI overbought')

            # MACD signal
            macd = indicators.get('macd', {})
            if macd.get('histogram', 0) > 0:
                signal_score += 1
                reasons.append('MACD bullish')
            else:
                signal_score -= 1
                reasons.append('MACD bearish')

            # Pattern signals
            if patterns.get('bullish_engulfing'):
                signal_score += 3
                reasons.append('Bullish engulfing pattern')
            if patterns.get('bearish_engulfing'):
                signal_score -= 3
                reasons.append('Bearish engulfing pattern')

            # Regime adjustment
            regime_state = regime.get('state', 'NEUTRAL')
            if regime_state == 'BULLISH':
                signal_score += 1
            elif regime_state == 'BEARISH':
                signal_score -= 1

            # Determine side
            side = 'BUY' if signal_score > 0 else 'SELL' if signal_score < 0 else 'HOLD'

            return {
                'side': side,
                'score': signal_score,
                'reasons': reasons,
                'strength': abs(signal_score) / 10
            }

        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return {'side': 'HOLD', 'score': 0, 'reasons': [], 'strength': 0}

    # ============================================
    # SYSTEM STATUS
    # ============================================

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'is_running': self.is_running,
            'mode': self.current_mode.value,
            'uptime': str(datetime.now() - self.start_time),
            'registered_bots': len(self.registered_bots),
            'active_bots': len(self.active_bots),
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'trade_count_today': self.trade_count_today,
            'open_positions': len(self.trading_engine.positions),
            'pending_orders': len(self.pending_orders),
            'bot_state': self.bot_state_manager.get_state(),
            'adaptive_params': self.adaptive_engine.get_adaptive_params(),
            'risk_status': self.risk_engine.get_status(),
            'multi_trade_enabled': self.multi_trade_enabled,
            'max_concurrent_trades': self.max_concurrent
        }

    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        return {
            'trading_engine': self.trading_engine.get_performance(),
            'adaptive_engine': self.adaptive_engine.get_learning_report(),
            'bot_state': self.bot_state_manager.get_stats(),
            'risk_engine': self.risk_engine.get_status(),
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'trade_count_today': self.trade_count_today
        }

    def _log_system_event(self, event: str, details: str):
        """Log system event"""
        logger.info(f"🎯 SYSTEM EVENT: {event} - {details}")
        self.performance_history.append({
            'event': event,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    # ============================================
    # MULTI-TRADE PERMISSION
    # ============================================

    def enable_multi_trade(self, enabled: bool = True):
        """Enable or disable multi-trade mode"""
        self.multi_trade_enabled = enabled
        self.config.enable_multi_trade = enabled
        logger.info(f"Multi-trade {'enabled' if enabled else 'disabled'}")

    def set_max_concurrent_trades(self, max_trades: int):
        """Set maximum concurrent trades"""
        self.max_concurrent = max(max_trades, 1)
        self.config.max_concurrent_trades = self.max_concurrent
        logger.info(f"Max concurrent trades set to: {self.max_concurrent}")

    # ============================================
    # ADAPTIVE CONFIGURATION
    # ============================================

    def configure_adaptive(self, enabled: bool = True, learning_rate: float = 0.01):
        """Configure adaptive engine"""
        self.config.enable_adaptive = enabled
        self.adaptive_engine.is_learning = enabled
        self.adaptive_engine.learning_rate = learning_rate
        logger.info(f"Adaptive engine {'enabled' if enabled else 'disabled'}")

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_pnl = 0.0
        self.trade_count_today = 0
        self.daily_stats = {}
        logger.info("Daily stats reset")
