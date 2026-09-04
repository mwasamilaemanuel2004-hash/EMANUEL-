"""
WHALE CRYPTO BOT - SELF-HEALING ADAPTIVE EDITION v8.0
Inajirekebisha yenyewe, Inajifunza, Inabadilika na Soko
Sheria Zote Zinatumika - Full Compliance, Full Adaptation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque
import json
import time
import threading
import asyncio
from functools import lru_cache, partial
import hashlib
import warnings
import traceback
import sys
import gc
warnings.filterwarnings('ignore')

# Optimized imports
try:
    from numba import jit, njit, prange, vectorize, cuda
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

try:
    from scipy import signal, stats, optimize
    from scipy.stats import norm, percentileofscore
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.neural_network import MLPClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ..base_bot import (
    UltraAdvancedBaseBot,
    Position
)

logger = logging.getLogger(__name__)

class BotState(Enum):
    """Bot operational states"""
    INITIALIZING = "initializing"
    LEARNING = "learning"
    TRADING = "trading"
    ADAPTING = "adapting"
    RECOVERING = "recovering"
    PAUSED = "paused"
    EMERGENCY = "emergency"
    OPTIMIZING = "optimizing"

class FailureType(Enum):
    """Types of failures bot can detect"""
    SIGNAL_FAILURE = "signal_failure"
    EXECUTION_FAILURE = "execution_failure"
    RISK_FAILURE = "risk_failure"
    DATA_FAILURE = "data_failure"
    PERFORMANCE_FAILURE = "performance_failure"
    ADAPTATION_FAILURE = "adaptation_failure"
    CONNECTIVITY_FAILURE = "connectivity_failure"

class SelfHealingSystem:
    """Bot inajirekebisha yenyewe inaposhindwa"""
    
    def __init__(self):
        self.failure_history = deque(maxlen=1000)
        self.healing_history = deque(maxlen=1000)
        self.health_score = 100.0
        self.last_health_check = datetime.now()
        self.healing_strategies = {}
        self.failure_counters = {}
        
    def detect_failure(self, bot_state: Dict[str, Any]) -> List[FailureType]:
        """Detect failures in bot operation"""
        failures = []
        
        # Check signal quality
        if bot_state.get('signal_quality', 1.0) < 0.3:
            failures.append(FailureType.SIGNAL_FAILURE)
        
        # Check execution quality
        if bot_state.get('execution_success_rate', 1.0) < 0.5:
            failures.append(FailureType.EXECUTION_FAILURE)
        
        # Check risk compliance
        if bot_state.get('risk_compliance', 1.0) < 0.7:
            failures.append(FailureType.RISK_FAILURE)
        
        # Check data quality
        if bot_state.get('data_quality', 1.0) < 0.5:
            failures.append(FailureType.DATA_FAILURE)
        
        # Check performance
        if bot_state.get('win_rate', 0.5) < 0.3:
            failures.append(FailureType.PERFORMANCE_FAILURE)
        
        return failures
    
    def heal_failure(self, failure: FailureType, bot_instance: Any) -> bool:
        """Heal specific failure"""
        healing_actions = {
            FailureType.SIGNAL_FAILURE: self._heal_signal_failure,
            FailureType.EXECUTION_FAILURE: self._heal_execution_failure,
            FailureType.RISK_FAILURE: self._heal_risk_failure,
            FailureType.DATA_FAILURE: self._heal_data_failure,
            FailureType.PERFORMANCE_FAILURE: self._heal_performance_failure,
            FailureType.ADAPTATION_FAILURE: self._heal_adaptation_failure
        }
        
        healing_func = healing_actions.get(failure)
        if healing_func:
            try:
                success = healing_func(bot_instance)
                
                # Record healing
                self.healing_history.append({
                    'timestamp': datetime.now(),
                    'failure': failure.value,
                    'success': success
                })
                
                # Update failure counter
                if failure.value not in self.failure_counters:
                    self.failure_counters[failure.value] = 0
                self.failure_counters[failure.value] += 1
                
                if success:
                    self.health_score = min(100.0, self.health_score + 5)
                else:
                    self.health_score = max(0.0, self.health_score - 10)
                
                return success
                
            except Exception as e:
                logger.error(f"Healing failed for {failure.value}: {e}")
                return False
        
        return False
    
    def _heal_signal_failure(self, bot: Any) -> bool:
        """Heal signal generation failure"""
        try:
            # Reset signal parameters to conservative
            bot.config['min_confidence'] = max(0.4, bot.config.get('min_confidence', 0.5) - 0.1)
            bot.config['signal_threshold'] = max(0.3, bot.config.get('signal_threshold', 0.5) - 0.1)
            
            # Clear stale signals
            if hasattr(bot, 'signal_history'):
                bot.signal_history.clear()
            
            logger.info("Signal failure healed - parameters reset")
            return True
        except:
            return False
    
    def _heal_execution_failure(self, bot: Any) -> bool:
        """Heal execution failure"""
        try:
            # Reduce position size
            bot.config['max_position_size'] = max(0.05, bot.config.get('max_position_size', 0.2) * 0.7)
            
            # Increase timeout
            bot.config['execution_timeout'] = bot.config.get('execution_timeout', 1.0) * 1.5
            
            # Clear pending orders
            if hasattr(bot, 'pending_orders'):
                bot.pending_orders.clear()
            
            logger.info("Execution failure healed - conservative sizing")
            return True
        except:
            return False
    
    def _heal_risk_failure(self, bot: Any) -> bool:
        """Heal risk management failure"""
        try:
            # Enforce strict risk limits
            bot.config['max_drawdown'] = max(0.05, bot.config.get('max_drawdown', 0.15) * 0.5)
            bot.config['daily_loss_limit'] = max(0.01, bot.config.get('daily_loss_limit', 0.04) * 0.5)
            bot.config['max_leverage'] = max(1, bot.config.get('max_leverage', 3) - 1)
            
            # Close high-risk positions
            if hasattr(bot, 'positions'):
                for pos_id, pos in list(bot.positions.items()):
                    if pos.unrealized_pnl < 0:
                        bot.close_position(pos_id, pos.current_price, "risk_healing")
            
            logger.info("Risk failure healed - strict limits applied")
            return True
        except:
            return False
    
    def _heal_data_failure(self, bot: Any) -> bool:
        """Heal data failure"""
        try:
            # Reset data caches
            if hasattr(bot, 'cache'):
                bot.cache.clear()
            
            # Reset indicators
            if hasattr(bot, 'indicators'):
                bot.indicators.clear()
            
            logger.info("Data failure healed - caches cleared")
            return True
        except:
            return False
    
    def _heal_performance_failure(self, bot: Any) -> bool:
        """Heal performance failure"""
        try:
            # Switch to conservative mode
            bot.config['strategy_mode'] = 'conservative'
            bot.config['position_size_multiplier'] = 0.3
            
            # Reset learning
            if hasattr(bot, 'learning_history'):
                bot.learning_history.clear()
            
            logger.info("Performance failure healed - conservative mode")
            return True
        except:
            return False
    
    def _heal_adaptation_failure(self, bot: Any) -> bool:
        """Heal adaptation failure"""
        try:
            # Reset adaptation parameters
            bot.config['adaptation_rate'] = max(0.05, bot.config.get('adaptation_rate', 0.1) * 0.5)
            bot.config['learning_rate'] = max(0.02, bot.config.get('learning_rate', 0.05) * 0.5)
            
            # Reset optimization
            if hasattr(bot, 'optimizer'):
                bot.optimizer.reset()
            
            logger.info("Adaptation failure healed - slowed learning")
            return True
        except:
            return False

class AdaptiveLearningEngine:
    """Inajifunza na kubadilika na soko"""
    
    def __init__(self):
        self.learning_history = deque(maxlen=5000)
        self.adaptation_history = deque(maxlen=1000)
        self.strategy_performance = {}
        self.market_learning = {}
        self.optimal_parameters = {}
        self.learning_rate = 0.1
        self.adaptation_threshold = 5
        
    def learn_from_trade(self, trade: Dict[str, Any]) -> None:
        """Learn from each trade"""
        self.learning_history.append(trade)
        
        # Extract learning features
        strategy = trade.get('strategy', 'unknown')
        market_state = trade.get('market_state', 'unknown')
        pnl = trade.get('pnl', 0)
        
        # Update strategy performance
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0,
                'avg_pnl': 0
            }
        
        perf = self.strategy_performance[strategy]
        perf['trades'] += 1
        perf['total_pnl'] += pnl
        perf['avg_pnl'] = perf['total_pnl'] / perf['trades']
        if pnl > 0:
            perf['wins'] += 1
        
        # Update market learning
        if market_state not in self.market_learning:
            self.market_learning[market_state] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0
            }
        
        ml = self.market_learning[market_state]
        ml['trades'] += 1
        ml['total_pnl'] += pnl
        if pnl > 0:
            ml['wins'] += 1
    
    def adapt_strategy(self, bot: Any) -> Dict[str, Any]:
        """Adapt strategy based on learning"""
        if len(self.learning_history) < self.adaptation_threshold:
            return {}
        
        adaptations = {}
        
        # Analyze strategy performance
        for strategy, perf in self.strategy_performance.items():
            if perf['trades'] >= 5:
                win_rate = perf['wins'] / perf['trades']
                
                if win_rate < 0.3:
                    # Disable poorly performing strategy
                    adaptations[strategy] = {'enabled': False}
                    logger.warning(f"Strategy {strategy} disabled - win rate {win_rate:.2%}")
                
                elif win_rate > 0.6:
                    # Boost good strategy
                    adaptations[strategy] = {'enabled': True, 'boost': 1.2}
                    logger.info(f"Strategy {strategy} boosted - win rate {win_rate:.2%}")
        
        # Analyze market state performance
        for state, perf in self.market_learning.items():
            if perf['trades'] >= 3:
                win_rate = perf['wins'] / perf['trades']
                
                if win_rate < 0.3:
                    # Avoid this market state
                    adaptations[state] = {'avoid': True}
                    logger.warning(f"Avoiding market state {state} - win rate {win_rate:.2%}")
                
                elif win_rate > 0.6:
                    # Prefer this market state
                    adaptations[state] = {'prefer': True}
                    logger.info(f"Preferring market state {state} - win rate {win_rate:.2%}")
        
        # Record adaptation
        self.adaptation_history.append({
            'timestamp': datetime.now(),
            'adaptations': adaptations
        })
        
        return adaptations
    
    def get_optimal_strategy(self, market_state: str) -> str:
        """Get optimal strategy for market state"""
        best_strategy = 'default'
        best_performance = -float('inf')
        
        for strategy, perf in self.strategy_performance.items():
            if perf['trades'] >= 3:
                win_rate = perf['wins'] / perf['trades']
                if win_rate > best_performance:
                    best_performance = win_rate
                    best_strategy = strategy
        
        return best_strategy

class SelfHealingWhaleBot(UltraAdvancedBaseBot):
    """
    Self-Healing Whale Bot v8.0
    Inajirekebisha, Inajifunza, Inabadilika
    """
    
    def __init__(self,
                 symbol: str = "BTCUSDT",
                 initial_capital: float = 1000.0,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize Self-Healing Whale Bot
        """
        super().__init__(
            bot_name=f"SelfHealingWhale_{symbol}",
            symbol=symbol,
            initial_capital=initial_capital
        )
        
        # Self-healing components
        self.healing_system = SelfHealingSystem()
        self.learning_engine = AdaptiveLearningEngine()
        
        # Bot state
        self.bot_state = BotState.INITIALIZING
        self.state_history = deque(maxlen=1000)
        
        # Configuration
        self.config = self._load_config(config)
        
        # Performance tracking
        self.trade_history = deque(maxlen=5000)
        self.failure_history = deque(maxlen=1000)
        self.healing_history = deque(maxlen=1000)
        
        # Threading
        self.healing_lock = threading.Lock()
        self.learning_lock = threading.Lock()
        self.monitoring_thread = None
        self.is_monitoring = False
        
        self.logger.info("Self-Healing Whale Bot initialized")
        self.bot_state = BotState.LEARNING
    
    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Load configuration with all rules"""
        default_config = {
            # Core settings
            'strategy_mode': 'adaptive',
            'position_size_multiplier': 1.0,
            'min_confidence': 0.5,
            'signal_threshold': 0.5,
            
            # Risk rules
            'max_drawdown': 0.15,
            'daily_loss_limit': 0.04,
            'max_leverage': 3,
            'max_position_size': 0.2,
            'max_total_exposure': 0.5,
            'stop_loss_percentage': 0.03,
            'take_profit_percentage': 0.06,
            
            # Learning rules
            'adaptation_rate': 0.1,
            'learning_rate': 0.05,
            'adaptation_threshold': 5,
            'min_trades_for_learning': 10,
            
            # Execution rules
            'execution_timeout': 1.0,
            'max_slippage': 0.001,
            'retry_attempts': 3,
            
            # Healing rules
            'auto_heal': True,
            'max_healing_attempts': 3,
            'healing_cooldown': 300  # 5 minutes
        }
        
        if config:
            default_config.update(config)
        
        return default_config
    
    def execute_self_healing_strategy(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategy with self-healing"""
        try:
            # Check bot state
            if self.bot_state in [BotState.PAUSED, BotState.EMERGENCY]:
                return {'action': 'hold', 'reason': f'bot_{self.bot_state.value}'}
            
            # Monitor health
            self._monitor_health()
            
            # Execute strategy
            result = self._execute_core_strategy(market_data)
            
            # Learn from result
            if result.get('action') in ['buy', 'sell']:
                self._learn_from_execution(result)
            
            # Check for failures
            failures = self._check_failures(result)
            
            # Heal failures if auto-heal enabled
            if failures and self.config.get('auto_heal', True):
                self._heal_failures(failures)
            
            return result
            
        except Exception as e:
            logger.error(f"Strategy execution error: {e}")
            self.bot_state = BotState.RECOVERING
            return {'action': 'hold', 'reason': 'error', 'error': str(e)}
    
    def _execute_core_strategy(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute core strategy"""
        prices = market_data.get('prices', [])
        
        if not prices:
            return {'action': 'hold', 'reason': 'no_data'}
        
        current_price = prices[-1]
        
        # Detect whale activity
        whale_score = self._detect_whale_score(market_data)
        
        # Calculate risk
        risk_score = self._calculate_risk_score(market_data)
        
        # Check risk limits
        if not self._check_all_risk_limits(risk_score):
            self.bot_state = BotState.PAUSED
            return {'action': 'hold', 'reason': 'risk_limit_exceeded'}
        
        # Generate signal
        signal = self._generate_signal(whale_score, risk_score)
        
        if signal['action'] == 'neutral':
            return {'action': 'hold', 'reason': 'no_signal'}
        
        # Calculate position size
        position_size = self._calculate_position_size(current_price, signal['confidence'])
        
        # Execute trade
        position = self.open_position(
            signal['action'],
            current_price,
            signal['confidence'],
            position_size
        )
        
        if position:
            # Set stop loss and take profit
            stop_loss = self._calculate_stop_loss(current_price, signal['action'])
            take_profit = self._calculate_take_profit(current_price, signal['action'])
            
            position.stop_loss = stop_loss
            position.take_profit = take_profit
            
            self.bot_state = BotState.TRADING
            
            return {
                'action': 'buy' if signal['action'] == 'long' else 'sell',
                'reason': 'whale_signal',
                'position': position,
                'whale_score': whale_score,
                'risk_score': risk_score,
                'confidence': signal['confidence']
            }
        
        return {'action': 'hold', 'reason': 'position_not_opened'}
    
    def _detect_whale_score(self, market_data: Dict[str, Any]) -> float:
        """Detect whale score"""
        volumes = market_data.get('volumes', [])
        prices = market_data.get('prices', [])
        
        if not volumes or not prices:
            return 0.0
        
        # Simple whale detection
        vol_threshold = np.percentile(volumes, 95) if len(volumes) > 20 else max(volumes)
        
        buy_pressure = sum(v for i, v in enumerate(volumes) 
                         if v >= vol_threshold and i > 0 and prices[i] > prices[i-1])
        sell_pressure = sum(v for i, v in enumerate(volumes) 
                          if v >= vol_threshold and i > 0 and prices[i] < prices[i-1])
        
        total = buy_pressure + sell_pressure
        return (buy_pressure - sell_pressure) / total if total > 0 else 0.0
    
    def _calculate_risk_score(self, market_data: Dict[str, Any]) -> float:
        """Calculate risk score"""
        prices = market_data.get('prices', [])
        
        if not prices:
            return 1.0
        
        returns = np.diff(prices[-30:]) / prices[-30:-1] if len(prices) >= 30 else [0]
        volatility = np.std(returns) if returns else 0
        
        return min(1.0, volatility * 20)
    
    def _check_all_risk_limits(self, risk_score: float) -> bool:
        """Check ALL risk limits - SHERIA ZOTE"""
        # Check drawdown
        if self.max_drawdown > self.config.get('max_drawdown', 0.15):
            self.logger.warning("Max drawdown exceeded - SHERIA")
            return False
        
        # Check daily loss
        if self.daily_pnl < -self.current_capital * self.config.get('daily_loss_limit', 0.04):
            self.logger.warning("Daily loss limit exceeded - SHERIA")
            return False
        
        # Check risk score
        if risk_score > 0.8:
            self.logger.warning("Risk score too high - SHERIA")
            return False
        
        # Check total exposure
        total_exposure = sum(p.quantity * p.current_price for p in self.positions.values())
        if total_exposure > self.current_capital * self.config.get('max_total_exposure', 0.5):
            self.logger.warning("Total exposure exceeded - SHERIA")
            return False
        
        # Check number of positions
        if len(self.positions) >= 10:
            self.logger.warning("Too many positions - SHERIA")
            return False
        
        return True
    
    def _generate_signal(self, whale_score: float, risk_score: float) -> Dict[str, Any]:
        """Generate signal with all rules"""
        signal = {
            'action': 'neutral',
            'confidence': 0,
            'strength': 0
        }
        
        # Check minimum confidence
        if risk_score > 0.6:
            return signal
        
        # Whale signal
        if whale_score > 0.3:
            signal['action'] = 'long'
            signal['strength'] = min(1.0, whale_score)
            signal['confidence'] = min(0.9, 0.5 + whale_score * 0.4)
        elif whale_score < -0.3:
            signal['action'] = 'short'
            signal['strength'] = min(1.0, abs(whale_score))
            signal['confidence'] = min(0.9, 0.5 + abs(whale_score) * 0.4)
        
        # Check minimum confidence rule
        if signal['confidence'] < self.config.get('min_confidence', 0.5):
            signal['action'] = 'neutral'
        
        return signal
    
    def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Calculate position size with all rules"""
        max_size = self.config.get('max_position_size', 0.2)
        position_value = self.current_capital * max_size * confidence
        
        return position_value / price if price > 0 else 0
    
    def _calculate_stop_loss(self, price: float, action: str) -> float:
        """Calculate stop loss"""
        stop_pct = self.config.get('stop_loss_percentage', 0.03)
        
        if action == 'long':
            return price * (1 - stop_pct)
        else:
            return price * (1 + stop_pct)
    
    def _calculate_take_profit(self, price: float, action: str) -> float:
        """Calculate take profit"""
        tp_pct = self.config.get('take_profit_percentage', 0.06)
        
        if action == 'long':
            return price * (1 + tp_pct)
        else:
            return price * (1 - tp_pct)
    
    def _monitor_health(self) -> None:
        """Monitor bot health"""
        current_time = datetime.now()
        
        # Check health every minute
        if (current_time - self.healing_system.last_health_check).total_seconds() < 60:
            return
        
        self.healing_system.last_health_check = current_time
        
        # Collect health metrics
        health_metrics = {
            'win_rate': self._calculate_win_rate(),
            'signal_quality': self._calculate_signal_quality(),
            'execution_success_rate': self._calculate_execution_success(),
            'risk_compliance': self._calculate_risk_compliance(),
            'data_quality': self._calculate_data_quality()
        }
        
        # Detect failures
        failures = self.healing_system.detect_failure(health_metrics)
        
        # Heal if needed
        if failures:
            logger.warning(f"Failures detected: {[f.value for f in failures]}")
            self._heal_failures(failures)
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        if not self.closed_positions:
            return 0.5
        
        wins = sum(1 for p in self.closed_positions if p.realized_pnl > 0)
        return wins / len(self.closed_positions)
    
    def _calculate_signal_quality(self) -> float:
        """Calculate signal quality"""
        if not self.trade_history:
            return 1.0
        
        successful_signals = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0)
        return successful_signals / len(self.trade_history)
    
    def _calculate_execution_success(self) -> float:
        """Calculate execution success rate"""
        if not self.trade_history:
            return 1.0
        
        executed = sum(1 for t in self.trade_history if t.get('executed', False))
        return executed / len(self.trade_history)
    
    def _calculate_risk_compliance(self) -> float:
        """Calculate risk compliance"""
        violations = 0
        total_checks = 5
        
        if self.max_drawdown > self.config.get('max_drawdown', 0.15):
            violations += 1
        if self.daily_pnl < -self.current_capital * self.config.get('daily_loss_limit', 0.04):
            violations += 1
        if len(self.positions) >= 10:
            violations += 1
        
        return 1.0 - (violations / total_checks)
    
    def _calculate_data_quality(self) -> float:
        """Calculate data quality"""
        if not self.trade_history:
            return 1.0
        
        valid_trades = sum(1 for t in self.trade_history if t.get('valid', True))
        return valid_trades / len(self.trade_history)
    
    def _check_failures(self, result: Dict[str, Any]) -> List[Any]:
        """Check for failures in result"""
        failures = []
        
        if result.get('action') == 'hold' and result.get('reason') == 'error':
            failures.append(FailureType.EXECUTION_FAILURE)
        
        if result.get('action') == 'hold' and result.get('reason') == 'risk_limit_exceeded':
            failures.append(FailureType.RISK_FAILURE)
        
        return failures
    
    def _heal_failures(self, failures: List[Any]) -> None:
        """Heal detected failures"""
        with self.healing_lock:
            for failure in failures:
                success = self.healing_system.heal_failure(failure, self)
                
                if success:
                    logger.info(f"Healed: {failure.value}")
                    self.healing_history.append({
                        'timestamp': datetime.now(),
                        'failure': failure.value,
                        'healed': True
                    })
                else:
                    logger.warning(f"Failed to heal: {failure.value}")
                    
                    # Check if emergency stop needed
                    if self.healing_system.health_score < 30:
                        self.bot_state = BotState.EMERGENCY
                        self._emergency_stop()
    
    def _emergency_stop(self) -> None:
        """Emergency stop - close all positions"""
        logger.critical("EMERGENCY STOP - Closing all positions")
        
        for position_id in list(self.positions.keys()):
            position = self.positions[position_id]
            self.close_position(position_id, position.current_price, "emergency_stop")
        
        self.bot_state = BotState.PAUSED
    
    def _learn_from_execution(self, result: Dict[str, Any]) -> None:
        """Learn from execution"""
        with self.learning_lock:
            trade_data = {
                'timestamp': datetime.now(),
                'action': result.get('action'),
                'whale_score': result.get('whale_score', 0),
                'risk_score': result.get('risk_score', 0),
                'confidence': result.get('confidence', 0),
                'pnl': 0,  # Will update on close
                'strategy': 'whale_following',
                'market_state': str(self.bot_state.value),
                'valid': True,
                'executed': True
            }
            
            self.trade_history.append(trade_data)
            self.learning_engine.learn_from_trade(trade_data)
    
    def start_self_healing(self) -> None:
        """Start self-healing monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.start()
        
        self.logger.info("Self-healing monitoring started")
    
    def _monitoring_loop(self) -> None:
        """Monitoring loop"""
        while self.is_monitoring:
            try:
                # Monitor health
                self._monitor_health()
                
                # Check for adaptation
                if len(self.trade_history) >= self.config.get('adaptation_threshold', 5):
                    adaptations = self.learning_engine.adapt_strategy(self)
                    
                    if adaptations:
                        logger.info(f"Adaptations applied: {adaptations}")
                        self.bot_state = BotState.ADAPTING
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(10)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = super().get_performance_metrics()
        
        # Self-healing metrics
        healing_metrics = {
            'bot_state': self.bot_state.value,
            'health_score': self.healing_system.health_score,
            'failures_detected': len(self.healing_system.failure_history),
            'healings_performed': len(self.healing_system.healing_history),
            'learning_trades': len(self.learning_engine.learning_history),
            'adaptations': len(self.learning_engine.adaptation_history),
            'win_rate': self._calculate_win_rate(),
            'signal_quality': self._calculate_signal_quality(),
            'risk_compliance': self._calculate_risk_compliance()
        }
        
        metrics.update(healing_metrics)
        return metrics



WhaleBot = SelfHealingWhaleBot