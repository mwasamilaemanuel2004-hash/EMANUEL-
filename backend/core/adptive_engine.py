# backend/app/core/adaptive_engine.py
"""
ADAPTIVE ENGINE - FULLY DEBUGGED & OPTIMIZED
7-Layer AI Self-Learning System with Reinforcement Learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json
import os
import traceback
from loguru import logger

# ============================================
# ENUMS (KAMILI)
# ============================================

class MarketRegime(Enum):
    """Market regimes for adaptive trading"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"
    ACCUMULATION = "ACCUMULATION"
    DISTRIBUTION = "DISTRIBUTION"
    RECOVERY = "RECOVERY"
    CRASH = "CRASH"

class LearningLayer(Enum):
    """7 Learning Layers"""
    TRADE_OUTCOME = "TRADE_OUTCOME"
    MARKET_CONDITION = "MARKET_CONDITION"
    INDICATOR_OPTIMIZATION = "INDICATOR_OPTIMIZATION"
    REINFORCEMENT = "REINFORCEMENT"
    PATTERN_RECOGNITION = "PATTERN_RECOGNITION"
    SENTIMENT = "SENTIMENT"
    VOLATILITY = "VOLATILITY"

class LearningPhase(Enum):
    """Learning progression phases"""
    INITIAL = 1
    BASIC = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5
    MASTER = 6

# ============================================
# DATA CLASSES (KAMILI)
# ============================================

@dataclass
class TradeRecord:
    """Complete trade record for learning"""
    timestamp: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    action: str = ""
    entry_price: float = 0.0
    exit_price: float = 0.0
    profit: float = 0.0
    profit_percent: float = 0.0
    market_regime: str = ""
    strategy_used: str = ""
    confidence: float = 0.0
    indicators: Dict[str, float] = field(default_factory=dict)
    patterns_detected: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    volatility_at_entry: float = 0.0
    exit_reason: str = ""
    trade_duration: float = 0.0
    risk_reward: float = 0.0
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0

@dataclass
class LearningState:
    """Current learning state"""
    win_rate: float = 0.5
    total_trades: int = 0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 1.0
    best_strategy: str = ""
    best_parameters: Dict = field(default_factory=dict)
    market_regime: str = "NEUTRAL"
    confidence_threshold: float = 65.0
    risk_multiplier: float = 1.0
    learning_phase: LearningPhase = LearningPhase.INITIAL
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    expectancy: float = 0.0
    max_drawdown: float = 0.0
    recovery_factor: float = 0.0
    learning_iterations: int = 0
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class PatternData:
    """Pattern recognition data"""
    name: str = ""
    type: str = ""
    strength: float = 0.0
    confidence: float = 0.0
    occurrences: int = 0
    success_rate: float = 0.0
    avg_profit: float = 0.0
    last_detected: datetime = field(default_factory=datetime.now)
    reliability: float = 0.0

@dataclass
class SentimentData:
    """Sentiment analysis data"""
    score: float = 0.0
    strength: float = 0.0
    direction: str = "neutral"
    sample_size: int = 0
    volatility_adjustment: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class VolatilityData:
    """Volatility analysis data"""
    regime: str = "NORMAL"
    current_atr: float = 0.0
    avg_atr: float = 0.0
    percentile: float = 0.0
    trend: str = "STABLE"
    sample_size: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

# ============================================
# ADAPTIVE ENGINE CLASS (KAMILI)
# ============================================

class AdaptiveEngine:
    """
    ULTRA ADVANCED AI ADAPTIVE ENGINE
    - 7 Learning Layers
    - Reinforcement Learning (Q-Learning)
    - Pattern Recognition
    - Sentiment Analysis
    - Market Regime Detection
    - Self-Optimizing Parameters
    - Error Recovery
    - Persistent Learning
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # ============================================
        # LAYER 1: TRADE OUTCOME LEARNING
        # ============================================
        self.trade_history: List[TradeRecord] = []
        self.winning_patterns: List[Dict] = []
        self.losing_patterns: List[Dict] = []
        self.trade_outcome_model = None
        self.max_history = 2000
        
        # ============================================
        # LAYER 2: MARKET CONDITION LEARNING
        # ============================================
        self.market_regimes: List[MarketRegime] = []
        self.market_transitions: Dict[str, int] = {}
        self.regime_performance: Dict[str, Dict] = {}
        self.current_regime = MarketRegime.RANGING
        self.regime_confidence = 0.5
        self.regime_history: List[Dict] = []
        
        # ============================================
        # LAYER 3: INDICATOR OPTIMIZATION
        # ============================================
        self.indicator_params = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bb_std': 2.0,
            'ema_fast': 20,
            'ema_slow': 50,
            'adx_threshold': 25,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stoch_k': 14,
            'stoch_d': 3,
            'atr_period': 14,
            'volume_threshold': 1.5,
            'vwap_period': 20,
            'momentum_period': 10,
            'cci_period': 20,
            'williams_r_period': 14
        }
        self.param_performance: Dict[str, List[float]] = {}
        self.optimal_params: Dict = {}
        self.param_optimization_frequency = 50
        self.param_history: List[Dict] = []
        
        # ============================================
        # LAYER 4: REINFORCEMENT LEARNING
        # ============================================
        self.q_table: Dict[str, Dict] = {}
        self.learning_rate = 0.01
        self.discount_factor = 0.9
        self.epsilon = 0.1
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01
        self.rewards_history: List[float] = []
        self.actions_taken: List[str] = []
        self.state_visits: Dict[str, int] = {}
        
        # ============================================
        # LAYER 5: PATTERN RECOGNITION
        # ============================================
        self.pattern_library: Dict[str, Dict] = {}
        self.detected_patterns: List[PatternData] = []
        self.pattern_accuracy: Dict[str, Dict] = {}
        self.known_patterns = [
            'double_bottom', 'double_top', 'head_shoulders', 'inverse_head_shoulders',
            'ascending_triangle', 'descending_triangle', 'bullish_flag', 'bearish_flag',
            'wedge', 'channel_breakout', 'support_retest', 'resistance_retest',
            'bullish_engulfing', 'bearish_engulfing', 'morning_star', 'evening_star',
            'hammer', 'shooting_star', 'piercing', 'dark_cloud', 'three_white_soldiers'
        ]
        
        # ============================================
        # LAYER 6: SENTIMENT ANALYSIS
        # ============================================
        self.sentiment_scores: deque = deque(maxlen=200)
        self.current_sentiment = SentimentData()
        self.sentiment_indicators = {}
        self.news_sentiment: deque = deque(maxlen=100)
        self.social_sentiment: deque = deque(maxlen=100)
        
        # ============================================
        # LAYER 7: VOLATILITY ANALYSIS
        # ============================================
        self.volatility_history: deque = deque(maxlen=200)
        self.volatility_regime = "NORMAL"
        self.atr_values: deque = deque(maxlen=100)
        self.volatility_data = VolatilityData()
        self.volatility_forecast: List[float] = []
        
        # ============================================
        # STATE & PERFORMANCE
        # ============================================
        self.state = LearningState()
        self.last_update = datetime.now()
        self.is_learning = True
        self.learning_iterations = 0
        self.performance_log: List[Dict] = []
        self.error_log: List[Dict] = []
        self.recovery_attempts = 0
        
        # ============================================
        # CONFIGURATION
        # ============================================
        self.config = {
            'learning_rate': 0.01,
            'discount_factor': 0.9,
            'epsilon': 0.1,
            'min_epsilon': 0.01,
            'epsilon_decay': 0.995,
            'max_history': 2000,
            'optimization_frequency': 50,
            'min_trades_for_learning': 20,
            'confidence_threshold_min': 50,
            'confidence_threshold_max': 85,
            'risk_multiplier_min': 0.3,
            'risk_multiplier_max': 2.0,
            'save_interval_minutes': 60,
            'auto_heal': True
        }
        
        # Load saved state
        self._load_state()
        
        logger.info("🧠 Ultra Advanced Adaptive Engine initialized")
    
    # ============================================
    # MAIN PUBLIC METHODS
    # ============================================
    
    def learn_from_trade(self, trade: TradeRecord) -> Dict:
        """Learn from a single trade - Full pipeline"""
        try:
            # Validate trade data
            if not self._validate_trade(trade):
                return {'success': False, 'error': 'Invalid trade data'}
            
            # Layer 1: Trade Outcome Learning
            layer1_result = self._learn_trade_outcome(trade)
            
            # Layer 2: Market Condition Learning
            layer2_result = self._learn_market_condition(trade)
            
            # Layer 3: Indicator Optimization
            layer3_result = self._optimize_indicators(trade)
            
            # Layer 4: Reinforcement Learning
            layer4_result = self._reinforcement_learning(trade)
            
            # Layer 5: Pattern Recognition
            layer5_result = self._update_patterns(trade)
            
            # Layer 6: Sentiment Analysis
            layer6_result = self._update_sentiment(trade)
            
            # Layer 7: Volatility Analysis
            layer7_result = self._update_volatility(trade)
            
            # Update global state
            self.learning_iterations += 1
            self.state.last_update = datetime.now()
            
            # Save state periodically
            if self.learning_iterations % self.config['optimization_frequency'] == 0:
                self._save_state()
                self._update_learning_phase()
            
            # Return comprehensive result
            return {
                'success': True,
                'layers': {
                    'trade_outcome': layer1_result,
                    'market_condition': layer2_result,
                    'indicator_optimization': layer3_result,
                    'reinforcement': layer4_result,
                    'pattern_recognition': layer5_result,
                    'sentiment': layer6_result,
                    'volatility': layer7_result
                },
                'state': {
                    'win_rate': self.state.win_rate,
                    'profit_factor': self.state.profit_factor,
                    'total_trades': self.state.total_trades,
                    'confidence_threshold': self.state.confidence_threshold,
                    'risk_multiplier': self.state.risk_multiplier,
                    'learning_phase': self.state.learning_phase.value
                }
            }
            
        except Exception as e:
            error_msg = f"Trade learning error: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.error_log.append({
                'timestamp': datetime.now(),
                'error': error_msg,
                'trade': trade.__dict__ if hasattr(trade, '__dict__') else str(trade)
            })
            return {'success': False, 'error': str(e)}
    
    def analyze_market_state(self, data: pd.DataFrame) -> Dict:
        """Complete market analysis - All layers combined"""
        try:
            if data.empty or len(data) < 50:
                return self._default_market_state()
            
            # Layer 2: Market Regime
            regime_result = self._analyze_market_regime(data)
            
            # Layer 5: Pattern Detection
            patterns = self.detect_patterns(data)
            
            # Layer 6: Sentiment
            sentiment = self.get_sentiment()
            
            # Layer 7: Volatility
            volatility = self.get_volatility_status()
            
            # Layer 3: Adaptive Parameters
            params = self.get_adaptive_indicator_params()
            
            # Calculate adjustments
            adjustments = self._calculate_adjustments(regime_result, sentiment, volatility)
            
            # Apply adjustments
            for key, value in adjustments.items():
                if key in params:
                    params[key] = value
            
            # Update current regime
            self.current_regime = MarketRegime(regime_result['regime']) if regime_result.get('regime') else MarketRegime.RANGING
            self.regime_confidence = regime_result.get('confidence', 0.5)
            
            # Update sentiment
            self.current_sentiment = sentiment
            
            # Update volatility
            self.volatility_data = volatility
            
            return {
                'regime': regime_result,
                'patterns': [p.__dict__ for p in patterns] if patterns else [],
                'sentiment': sentiment.__dict__ if hasattr(sentiment, '__dict__') else sentiment,
                'volatility': volatility.__dict__ if hasattr(volatility, '__dict__') else volatility,
                'params': params,
                'adjustments': adjustments,
                'confidence_threshold': self.state.confidence_threshold,
                'risk_multiplier': self.state.risk_multiplier,
                'learning_phase': self.state.learning_phase.value,
                'win_rate': self.state.win_rate,
                'profit_factor': self.state.profit_factor,
                'regime_confidence': self.regime_confidence,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market state analysis error: {e}")
            return self._default_market_state()
    
    def should_trade(self, confidence: float, context: Dict = None) -> Dict:
        """Advanced trade decision with multiple factors"""
        try:
            # Base threshold
            base_threshold = self.state.confidence_threshold
            
            # RL-enhanced threshold
            market_regime = self.current_regime.value if hasattr(self.current_regime, 'value') else "NEUTRAL"
            strategy = context.get('strategy', self.state.best_strategy) if context else self.state.best_strategy
            rl_threshold = self.get_best_confidence(market_regime, strategy)
            
            # Combined threshold
            combined_threshold = (base_threshold * 0.6 + rl_threshold * 0.4)
            
            # Adjust for volatility
            if self.volatility_regime == "HIGH":
                combined_threshold += 5
            elif self.volatility_regime == "LOW":
                combined_threshold -= 5
            
            # Adjust for sentiment
            sentiment_adjustment = self.current_sentiment.score * 5 if hasattr(self.current_sentiment, 'score') else 0
            combined_threshold -= sentiment_adjustment
            
            # Apply limits
            final_threshold = max(50, min(85, combined_threshold))
            
            # Decision
            should_trade = confidence >= final_threshold
            
            return {
                'should_trade': should_trade,
                'confidence': confidence,
                'final_threshold': final_threshold,
                'base_threshold': base_threshold,
                'rl_threshold': rl_threshold,
                'volatility_adjustment': 5 if self.volatility_regime == "HIGH" else -5 if self.volatility_regime == "LOW" else 0,
                'sentiment_adjustment': sentiment_adjustment,
                'win_rate': self.state.win_rate,
                'profit_factor': self.state.profit_factor,
                'consecutive_losses': self.state.consecutive_losses,
                'market_regime': market_regime
            }
            
        except Exception as e:
            logger.error(f"Should trade error: {e}")
            return {
                'should_trade': confidence >= self.state.confidence_threshold,
                'confidence': confidence,
                'final_threshold': self.state.confidence_threshold,
                'error': str(e)
            }
    
    # ============================================
    # LAYER 1: TRADE OUTCOME LEARNING
    # ============================================
    
    def _learn_trade_outcome(self, trade: TradeRecord) -> Dict:
        """Layer 1: Learn from trade outcome"""
        try:
            # Add to history
            self.trade_history.append(trade)
            if len(self.trade_history) > self.max_history:
                self.trade_history = self.trade_history[-self.max_history:]
            
            # Extract pattern
            pattern = self._extract_pattern(trade)
            
            # Update wins/losses
            if trade.profit > 0:
                self.winning_patterns.append(pattern)
                self.state.consecutive_wins += 1
                self.state.consecutive_losses = 0
            else:
                self.losing_patterns.append(pattern)
                self.state.consecutive_losses += 1
                self.state.consecutive_wins = 0
            
            # Update statistics
            self._update_statistics(trade)
            
            # Update strategy performance
            self._update_strategy_performance(trade)
            
            return {
                'success': True,
                'win_rate': self.state.win_rate,
                'profit_factor': self.state.profit_factor,
                'total_trades': self.state.total_trades,
                'consecutive_wins': self.state.consecutive_wins,
                'consecutive_losses': self.state.consecutive_losses
            }
            
        except Exception as e:
            logger.error(f"Trade outcome learning error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _validate_trade(self, trade: TradeRecord) -> bool:
        """Validate trade data"""
        required_fields = ['symbol', 'action', 'entry_price', 'exit_price', 'profit']
        for field in required_fields:
            if not hasattr(trade, field) or getattr(trade, field) is None:
                logger.error(f"Missing required field: {field}")
                return False
        return True
    
    def _extract_pattern(self, trade: TradeRecord) -> Dict:
        """Extract pattern from trade"""
        return {
            'symbol': trade.symbol,
            'market_regime': trade.market_regime,
            'strategy': trade.strategy_used,
            'indicators': trade.indicators,
            'patterns': trade.patterns_detected,
            'confidence': trade.confidence,
            'profit': trade.profit,
            'profit_percent': trade.profit_percent,
            'sentiment': trade.sentiment_score,
            'volatility': trade.volatility_at_entry,
            'exit_reason': trade.exit_reason,
            'risk_reward': trade.risk_reward,
            'duration': trade.trade_duration
        }
    
    def _update_statistics(self, trade: TradeRecord):
        """Update trade statistics"""
        self.state.total_trades += 1
        
        # Win rate
        wins = sum(1 for t in self.trade_history if t.profit > 0)
        self.state.win_rate = wins / len(self.trade_history) if self.trade_history else 0.5
        
        # Average profit/loss
        profits = [t.profit for t in self.trade_history if t.profit > 0]
        losses = [t.profit for t in self.trade_history if t.profit < 0]
        self.state.avg_profit = np.mean(profits) if profits else 0
        self.state.avg_loss = np.mean(losses) if losses else 0
        
        # Profit factor
        total_profit = sum(profits) if profits else 0
        total_loss = abs(sum(losses)) if losses else 1
        self.state.profit_factor = total_profit / total_loss if total_loss > 0 else 1
        
        # Risk-adjusted metrics
        returns = [t.profit for t in self.trade_history if t.profit != 0]
        if returns:
            self.state.sharpe_ratio = np.mean(returns) / (np.std(returns) + 0.0001)
            self.state.sortino_ratio = np.mean(returns) / (np.std([r for r in returns if r < 0]) + 0.0001)
            self.state.expectancy = np.mean(returns)
        
        # Max drawdown
        cumulative = np.cumsum([t.profit for t in self.trade_history])
        if len(cumulative) > 0:
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (running_max - cumulative) / (running_max + 0.0001)
            self.state.max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Adjust risk multiplier
        self._adjust_risk_multiplier()
    
    def _adjust_risk_multiplier(self):
        """Adjust risk multiplier based on performance"""
        win_rate = self.state.win_rate
        profit_factor = self.state.profit_factor
        drawdown = self.state.max_drawdown
        
        # Base on win rate
        if win_rate < 0.35 or profit_factor < 0.8:
            self.state.risk_multiplier = 0.5
        elif win_rate < 0.45 or profit_factor < 1.2:
            self.state.risk_multiplier = 0.7
        elif win_rate < 0.55:
            self.state.risk_multiplier = 1.0
        elif win_rate < 0.65 and profit_factor > 1.5:
            self.state.risk_multiplier = 1.2
        elif win_rate > 0.65 and profit_factor > 2.0:
            self.state.risk_multiplier = 1.5
        
        # Adjust for drawdown
        if drawdown > 0.15:
            self.state.risk_multiplier *= 0.7
        elif drawdown > 0.20:
            self.state.risk_multiplier *= 0.5
        
        # Apply limits
        self.state.risk_multiplier = max(0.3, min(2.0, self.state.risk_multiplier))
        
        # Adjust confidence threshold
        if win_rate < 0.4:
            self.state.confidence_threshold = min(85, self.state.confidence_threshold + 5)
        elif win_rate > 0.6:
            self.state.confidence_threshold = max(50, self.state.confidence_threshold - 5)
    
    def _update_strategy_performance(self, trade: TradeRecord):
        """Update performance per strategy"""
        strategy = trade.strategy_used
        if strategy not in self.regime_performance:
            self.regime_performance[strategy] = {'wins': 0, 'losses': 0, 'profit': 0, 'trades': 0}
        
        self.regime_performance[strategy]['trades'] += 1
        if trade.profit > 0:
            self.regime_performance[strategy]['wins'] += 1
        else:
            self.regime_performance[strategy]['losses'] += 1
        self.regime_performance[strategy]['profit'] += trade.profit
        
        # Find best strategy
        best_profit = -999999
        for strat, perf in self.regime_performance.items():
            if perf['profit'] > best_profit:
                best_profit = perf['profit']
                self.state.best_strategy = strat
    
    def _update_learning_phase(self):
        """Update learning phase based on progress"""
        trades = self.state.total_trades
        win_rate = self.state.win_rate
        profit_factor = self.state.profit_factor
        
        if trades > 500 and win_rate > 0.6 and profit_factor > 1.8:
            self.state.learning_phase = LearningPhase.MASTER
        elif trades > 200 and win_rate > 0.55 and profit_factor > 1.5:
            self.state.learning_phase = LearningPhase.EXPERT
        elif trades > 100 and win_rate > 0.5 and profit_factor > 1.2:
            self.state.learning_phase = LearningPhase.ADVANCED
        elif trades > 50 and win_rate > 0.45:
            self.state.learning_phase = LearningPhase.INTERMEDIATE
        elif trades > 20:
            self.state.learning_phase = LearningPhase.BASIC
    
    # ============================================
    # LAYER 2: MARKET CONDITION LEARNING
    # ============================================
    
    def _analyze_market_regime(self, data: pd.DataFrame) -> Dict:
        """Advanced market regime analysis"""
        try:
            if data.empty or len(data) < 50:
                return {'regime': 'RANGING', 'confidence': 0.3}
            
            # Calculate indicators
            atr = self._calculate_atr(data)
            adx = self._calculate_adx(data)
            rsi = self._calculate_rsi(data)
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            
            # Volatility check
            avg_atr = data['close'].pct_change().std() * 100
            volatility_ratio = atr / avg_atr if avg_atr > 0 else 1
            
            # Trend check
            current_price = data['close'].iloc[-1]
            sma_50 = data['close'].rolling(50).mean().iloc[-1]
            sma_200 = data['close'].rolling(200).mean().iloc[-1]
            price_above_50 = current_price > sma_50
            price_above_200 = current_price > sma_200
            
            # Volume check
            avg_volume = data['volume'].rolling(20).mean().iloc[-1]
            current_volume = data['volume'].iloc[-1]
            volume_spike = current_volume > avg_volume * 1.5
            
            # Determine regime with confidence scoring
            regimes = []
            confidences = []
            
            # Volatility regimes
            if volatility_ratio > 2.0:
                if current_price > sma_50 and current_price > sma_200:
                    regimes.append('BREAKOUT')
                    confidences.append(0.7 + min(0.3, volatility_ratio / 5))
                else:
                    regimes.append('BREAKDOWN')
                    confidences.append(0.7 + min(0.3, volatility_ratio / 5))
            elif volatility_ratio > 1.5:
                regimes.append('HIGH_VOLATILITY')
                confidences.append(0.6 + min(0.3, volatility_ratio / 3))
            elif volatility_ratio < 0.5:
                regimes.append('LOW_VOLATILITY')
                confidences.append(0.6)
            
            # Trend regimes
            if adx > 30:
                if current_price > sma_50 and current_price > sma_200:
                    regimes.append('BULLISH')
                    confidences.append(0.7 + min(0.3, adx / 100))
                elif current_price < sma_50 and current_price < sma_200:
                    regimes.append('BEARISH')
                    confidences.append(0.7 + min(0.3, adx / 100))
            
            if 20 < adx < 30:
                if current_price > sma_50:
                    regimes.append('BULLISH')
                    confidences.append(0.55)
                elif current_price < sma_50:
                    regimes.append('BEARISH')
                    confidences.append(0.55)
            
            # Accumulation/Distribution
            if volume_spike and abs(current_price - sma_50) / sma_50 < 0.01:
                if current_price > sma_50:
                    regimes.append('ACCUMULATION')
                    confidences.append(0.6)
                else:
                    regimes.append('DISTRIBUTION')
                    confidences.append(0.6)
            
            # Crash detection (quick drop > 3% with high volume)
            if len(data) > 20:
                drop = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
                if drop < -0.03 and volume_spike:
                    regimes.append('CRASH')
                    confidences.append(0.8)
            
            # Recovery detection
            if len(data) > 30:
                recovery = (data['close'].iloc[-1] - data['close'].iloc[-10]) / data['close'].iloc[-10]
                if recovery > 0.02 and price_above_50:
                    regimes.append('RECOVERY')
                    confidences.append(0.6)
            
            # Default
            if not regimes:
                regimes.append('RANGING')
                confidences.append(0.5)
            
            # Select regime with highest confidence
            best_idx = np.argmax(confidences)
            regime = regimes[best_idx]
            confidence = confidences[best_idx]
            
            # Store regime
            self.current_regime = MarketRegime(regime) if regime in [r.value for r in MarketRegime] else MarketRegime.RANGING
            self.regime_confidence = confidence
            self.market_regimes.append(self.current_regime)
            if len(self.market_regimes) > 100:
                self.market_regimes = self.market_regimes[-100:]
            
            return {
                'regime': regime,
                'confidence': confidence,
                'adx': adx,
                'rsi': current_rsi,
                'volatility_ratio': volatility_ratio,
                'volume_spike': volume_spike,
                'price_above_50': price_above_50,
                'price_above_200': price_above_200,
                'all_regimes': regimes,
                'all_confidences': confidences
            }
            
        except Exception as e:
            logger.error(f"Market regime analysis error: {e}")
            return {'regime': 'RANGING', 'confidence': 0.3}
    
    def _learn_market_condition(self, trade: TradeRecord) -> Dict:
        """Layer 2: Learn market conditions"""
        try:
            regime = trade.market_regime
            if regime not in self.market_transitions:
                self.market_transitions[regime] = 0
            self.market_transitions[regime] += 1
            
            # Update current regime
            try:
                self.current_regime = MarketRegime(regime)
            except:
                self.current_regime = MarketRegime.RANGING
            
            # Update state
            self.state.market_regime = regime
            
            # Update regime history
            self.regime_history.append({
                'regime': regime,
                'timestamp': datetime.now().isoformat(),
                'trade_profit': trade.profit
            })
            
            return {
                'success': True,
                'regime': regime,
                'transitions': self.market_transitions
            }
            
        except Exception as e:
            logger.error(f"Market condition learning error: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============================================
    # LAYER 3: INDICATOR OPTIMIZATION
    # ============================================
    
    def _optimize_indicators(self, trade: TradeRecord) -> Dict:
        """Layer 3: Optimize indicator parameters"""
        try:
            # Track parameter performance
            for param, value in self.indicator_params.items():
                if param not in self.param_performance:
                    self.param_performance[param] = []
                
                # Add performance score
                score = 1.0 if trade.profit > 0 else -1.0
                self.param_performance[param].append(score)
                
                # Keep only last 100
                if len(self.param_performance[param]) > 100:
                    self.param_performance[param] = self.param_performance[param][-100:]
            
            # Calculate optimal parameters
            self._calculate_optimal_params()
            
            return {
                'success': True,
                'param_performance': {k: np.mean(v) if v else 0 for k, v in self.param_performance.items()}
            }
            
        except Exception as e:
            logger.error(f"Indicator optimization error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_optimal_params(self):
        """Calculate optimal parameters based on performance"""
        try:
            for param, scores in self.param_performance.items():
                if len(scores) > 10:
                    avg_score = np.mean(scores)
                    current = self.indicator_params[param]
                    if isinstance(current, (int, float)):
                        if avg_score > 0.3:
                            self.indicator_params[param] = current * (1 + 0.02)
                        elif avg_score < -0.3:
                            self.indicator_params[param] = current * (1 - 0.02)
        except Exception as e:
            logger.error(f"Optimal params calculation error: {e}")
    
    def get_adaptive_indicator_params(self) -> Dict:
        """Get optimized indicator parameters"""
        return self.indicator_params.copy()
    
    def _calculate_adjustments(self, regime: Dict, sentiment: SentimentData, volatility: VolatilityData) -> Dict:
        """Calculate parameter adjustments based on market conditions"""
        adjustments = {}
        
        regime_type = regime.get('regime', 'RANGING')
        confidence = regime.get('confidence', 0.5)
        
        if regime_type == 'HIGH_VOLATILITY':
            adjustments = {
                'bb_std': self.indicator_params.get('bb_std', 2.0) * 1.25,
                'risk_multiplier': self.state.risk_multiplier * 0.5,
                'confidence_threshold': self.state.confidence_threshold + 10,
                'atr_period': 14,
                'volume_threshold': 2.0
            }
        elif regime_type == 'LOW_VOLATILITY':
            adjustments = {
                'bb_std': self.indicator_params.get('bb_std', 2.0) * 0.75,
                'risk_multiplier': self.state.risk_multiplier * 1.2,
                'confidence_threshold': self.state.confidence_threshold - 5,
                'atr_period': 10,
                'volume_threshold': 1.2
            }
        elif regime_type == 'BULLISH':
            adjustments = {
                'rsi_oversold': 25,
                'rsi_overbought': 80,
                'confidence_threshold': self.state.confidence_threshold - 5,
                'ema_fast': 15,
                'ema_slow': 40
            }
        elif regime_type == 'BEARISH':
            adjustments = {
                'rsi_oversold': 35,
                'rsi_overbought': 65,
                'confidence_threshold': self.state.confidence_threshold + 5,
                'ema_fast': 25,
                'ema_slow': 60
            }
        elif regime_type == 'BREAKOUT' or regime_type == 'BREAKDOWN':
            adjustments = {
                'bb_std': self.indicator_params.get('bb_std', 2.0) * 1.1,
                'risk_multiplier': self.state.risk_multiplier * 0.8,
                'adx_threshold': 20,
                'rsi_oversold': 25,
                'rsi_overbought': 75
            }
        elif regime_type == 'ACCUMULATION':
            adjustments = {
                'rsi_oversold': 35,
                'rsi_overbought': 65,
                'volume_threshold': 1.2,
                'confidence_threshold': self.state.confidence_threshold + 5
            }
        elif regime_type == 'DISTRIBUTION':
            adjustments = {
                'rsi_oversold': 35,
                'rsi_overbought': 65,
                'volume_threshold': 1.2,
                'confidence_threshold': self.state.confidence_threshold + 5
            }
        elif regime_type == 'CRASH':
            adjustments = {
                'risk_multiplier': 0.3,
                'confidence_threshold': 85,
                'bb_std': 3.0
            }
        elif regime_type == 'RECOVERY':
            adjustments = {
                'risk_multiplier': 0.7,
                'confidence_threshold': 70,
                'ema_fast': 10,
                'ema_slow': 30
            }
        
        # Apply confidence adjustment
        if confidence < 0.4:
            adjustments['confidence_threshold'] = adjustments.get('confidence_threshold', self.state.confidence_threshold) + 10
        
        # Apply sentiment adjustment
        if hasattr(sentiment, 'score'):
            if sentiment.score > 0.3:
                adjustments['rsi_oversold'] = adjustments.get('rsi_oversold', self.indicator_params.get('rsi_oversold', 30)) - 3
            elif sentiment.score < -0.3:
                adjustments['rsi_overbought'] = adjustments.get('rsi_overbought', self.indicator_params.get('rsi_overbought', 70)) + 3
        
        # Apply volatility adjustment
        if hasattr(volatility, 'regime'):
            if volatility.regime == "HIGH":
                adjustments['bb_std'] = adjustments.get('bb_std', self.indicator_params.get('bb_std', 2.0)) * 1.1
                adjustments['risk_multiplier'] = adjustments.get('risk_multiplier', self.state.risk_multiplier) * 0.8
            elif volatility.regime == "LOW":
                adjustments['bb_std'] = adjustments.get('bb_std', self.indicator_params.get('bb_std', 2.0)) * 0.9
                adjustments['risk_multiplier'] = adjustments.get('risk_multiplier', self.state.risk_multiplier) * 1.1
        
        return adjustments
    
    # ============================================
    # LAYER 4: REINFORCEMENT LEARNING
    # ============================================
    
    def _reinforcement_learning(self, trade: TradeRecord) -> Dict:
        """Layer 4: Q-Learning"""
        try:
            # State: market regime + strategy
            state_key = f"{trade.market_regime}_{trade.strategy_used}"
            
            # Action: confidence level
            confidence_level = int(trade.confidence / 10) * 10
            action_key = f"conf_{confidence_level}"
            
            # Reward: profit normalized
            reward = min(1.0, max(-1.0, trade.profit / 50))
            
            # Initialize Q-table
            if state_key not in self.q_table:
                self.q_table[state_key] = {}
            if action_key not in self.q_table[state_key]:
                self.q_table[state_key][action_key] = 0.0
            
            # Track state visits
            self.state_visits[state_key] = self.state_visits.get(state_key, 0) + 1
            
            # Update Q-value (Q-learning)
            old_q = self.q_table[state_key][action_key]
            max_future_q = max(self.q_table[state_key].values()) if self.q_table[state_key] else 0
            
            # Bellman equation with learning rate decay
            lr = self.learning_rate / (1 + 0.01 * self.state_visits.get(state_key, 0))
            new_q = old_q + lr * (reward + self.discount_factor * max_future_q - old_q)
            self.q_table[state_key][action_key] = new_q
            
            # Track rewards
            self.rewards_history.append(reward)
            if len(self.rewards_history) > 100:
                self.rewards_history = self.rewards_history[-100:]
            
            # Decay epsilon
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
            
            # Log significant changes
            if abs(new_q - old_q) > 0.1:
                logger.debug(f"RL Update: {state_key} - {action_key}: {old_q:.3f} → {new_q:.3f}")
            
            return {
                'success': True,
                'state': state_key,
                'action': action_key,
                'old_q': old_q,
                'new_q': new_q,
                'reward': reward,
                'epsilon': self.epsilon
            }
            
        except Exception as e:
            logger.error(f"Reinforcement learning error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_best_confidence(self, market_regime: str, strategy: str) -> float:
        """Get best confidence level for given state"""
        try:
            state_key = f"{market_regime}_{strategy}"
            if state_key in self.q_table and self.q_table[state_key]:
                best_action = max(self.q_table[state_key], key=self.q_table[state_key].get)
                confidence = float(best_action.split('_')[1])
                return max(50, min(85, confidence))
            return self.state.confidence_threshold
        except:
            return self.state.confidence_threshold
    
    # ============================================
    # LAYER 5: PATTERN RECOGNITION
    # ============================================
    
    def _update_patterns(self, trade: TradeRecord) -> Dict:
        """Layer 5: Update pattern recognition"""
        try:
            for pattern_name in trade.patterns_detected:
                if pattern_name not in self.pattern_accuracy:
                    self.pattern_accuracy[pattern_name] = {'hits': 0, 'correct': 0, 'accuracy': 0.0, 'total_profit': 0.0}
                
                self.pattern_accuracy[pattern_name]['hits'] += 1
                if trade.profit > 0:
                    self.pattern_accuracy[pattern_name]['correct'] += 1
                    self.pattern_accuracy[pattern_name]['total_profit'] += trade.profit
                
                # Calculate accuracy
                accuracy = self.pattern_accuracy[pattern_name]['correct'] / self.pattern_accuracy[pattern_name]['hits']
                self.pattern_accuracy[pattern_name]['accuracy'] = accuracy
            
            return {
                'success': True,
                'pattern_accuracy': self.pattern_accuracy
            }
            
        except Exception as e:
            logger.error(f"Pattern update error: {e}")
            return {'success': False, 'error': str(e)}
    
    def detect_patterns(self, data: pd.DataFrame) -> List[PatternData]:
        """Detect chart patterns"""
        patterns = []
        
        try:
            close = data['close']
            high = data['high']
            low = data['low']
            
            # Find swing points
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(close)-2):
                if high.iloc[i] > high.iloc[i-1] and high.iloc[i] > high.iloc[i-2]:
                    if high.iloc[i] > high.iloc[i+1] and high.iloc[i] > high.iloc[i+2]:
                        swing_highs.append({'price': high.iloc[i], 'index': i})
                
                if low.iloc[i] < low.iloc[i-1] and low.iloc[i] < low.iloc[i-2]:
                    if low.iloc[i] < low.iloc[i+1] and low.iloc[i] < low.iloc[i+2]:
                        swing_lows.append({'price': low.iloc[i], 'index': i})
            
            current_price = close.iloc[-1]
            
            # Double Bottom
            if len(swing_lows) >= 2:
                if abs(swing_lows[-1]['price'] - swing_lows[-2]['price']) / swing_lows[-2]['price'] < 0.02:
                    if current_price > swing_lows[-1]['price'] and current_price > swing_lows[-2]['price']:
                        patterns.append(PatternData(
                            name='double_bottom',
                            type='bullish_reversal',
                            strength=0.7,
                            confidence=0.7,
                            reliability=self._get_pattern_reliability('double_bottom')
                        ))
            
            # Double Top
            if len(swing_highs) >= 2:
                if abs(swing_highs[-1]['price'] - swing_highs[-2]['price']) / swing_highs[-2]['price'] < 0.02:
                    if current_price < swing_highs[-1]['price'] and current_price < swing_highs[-2]['price']:
                        patterns.append(PatternData(
                            name='double_top',
                            type='bearish_reversal',
                            strength=0.7,
                            confidence=0.7,
                            reliability=self._get_pattern_reliability('double_top')
                        ))
            
            # Head and Shoulders
            if len(swing_highs) >= 3:
                h1, h2, h3 = swing_highs[-3]['price'], swing_highs[-2]['price'], swing_highs[-1]['price']
                if h2 > h1 and h2 > h3 and abs(h1 - h3) / h1 < 0.02:
                    if current_price < h2:
                        patterns.append(PatternData(
                            name='head_shoulders',
                            type='bearish_reversal',
                            strength=0.8,
                            confidence=0.75,
                            reliability=self._get_pattern_reliability('head_shoulders')
                        ))
            
            # Inverse Head and Shoulders
            if len(swing_lows) >= 3:
                l1, l2, l3 = swing_lows[-3]['price'], swing_lows[-2]['price'], swing_lows[-1]['price']
                if l2 < l1 and l2 < l3 and abs(l1 - l3) / l1 < 0.02:
                    if current_price > l2:
                        patterns.append(PatternData(
                            name='inverse_head_shoulders',
                            type='bullish_reversal',
                            strength=0.8,
                            confidence=0.75,
                            reliability=self._get_pattern_reliability('inverse_head_shoulders')
                        ))
            
            # Bullish Flag
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                if (swing_highs[-1]['price'] < swing_highs[-2]['price'] and 
                    swing_lows[-1]['price'] > swing_lows[-2]['price']):
                    if current_price > swing_highs[-1]['price']:
                        patterns.append(PatternData(
                            name='bullish_flag',
                            type='continuation_bullish',
                            strength=0.6,
                            confidence=0.6,
                            reliability=self._get_pattern_reliability('bullish_flag')
                        ))
            
            # Bearish Flag
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                if (swing_highs[-1]['price'] > swing_highs[-2]['price'] and 
                    swing_lows[-1]['price'] < swing_lows[-2]['price']):
                    if current_price < swing_lows[-1]['price']:
                        patterns.append(PatternData(
                            name='bearish_flag',
                            type='continuation_bearish',
                            strength=0.6,
                            confidence=0.6,
                            reliability=self._get_pattern_reliability('bearish_flag')
                        ))
            
            # Support Retest
            if len(swing_lows) >= 2:
                support = swing_lows[-1]['price']
                if abs(current_price - support) / support < 0.02 and current_price > support:
                    patterns.append(PatternData(
                        name='support_retest',
                        type='bullish_reversal',
                        strength=0.65,
                        confidence=0.65,
                        reliability=self._get_pattern_reliability('support_retest')
                    ))
            
            # Resistance Retest
            if len(swing_highs) >= 2:
                resistance = swing_highs[-1]['price']
                if abs(current_price - resistance) / resistance < 0.02 and current_price < resistance:
                    patterns.append(PatternData(
                        name='resistance_retest',
                        type='bearish_reversal',
                        strength=0.65,
                        confidence=0.65,
                        reliability=self._get_pattern_reliability('resistance_retest')
                    ))
            
            # Ascending Triangle
            if len(swing_highs) >= 2 and len(swing_lows) >= 3:
                highs_equal = abs(swing_highs[-1]['price'] - swing_highs[-2]['price']) / swing_highs[-2]['price'] < 0.01
                lows_rising = swing_lows[-1]['price'] > swing_lows[-2]['price'] > swing_lows[-3]['price']
                if highs_equal and lows_rising:
                    patterns.append(PatternData(
                        name='ascending_triangle',
                        type='bullish_continuation',
                        strength=0.7,
                        confidence=0.7,
                        reliability=self._get_pattern_reliability('ascending_triangle')
                    ))
            
            # Descending Triangle
            if len(swing_highs) >= 3 and len(swing_lows) >= 2:
                highs_falling = swing_highs[-1]['price'] < swing_highs[-2]['price'] < swing_highs[-3]['price']
                lows_equal = abs(swing_lows[-1]['price'] - swing_lows[-2]['price']) / swing_lows[-2]['price'] < 0.01
                if highs_falling and lows_equal:
                    patterns.append(PatternData(
                        name='descending_triangle',
                        type='bearish_continuation',
                        strength=0.7,
                        confidence=0.7,
                        reliability=self._get_pattern_reliability('descending_triangle')
                    ))
            
            # Store patterns
            self.detected_patterns = patterns
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern detection error: {e}")
            return []
    
    def _get_pattern_reliability(self, pattern_name: str) -> float:
        """Get pattern reliability based on historical accuracy"""
        if pattern_name in self.pattern_accuracy:
            accuracy = self.pattern_accuracy[pattern_name].get('accuracy', 0.5)
            hits = self.pattern_accuracy[pattern_name].get('hits', 0)
            reliability = 0.5 + (accuracy - 0.5) * min(1.0, hits / 20)
            return max(0.1, min(0.9, reliability))
        return 0.5
    
    def get_best_patterns(self, min_reliability: float = 0.6) -> List[str]:
        """Get patterns with reliability above threshold"""
        return [
            pattern for pattern, data in self.pattern_accuracy.items()
            if data.get('accuracy', 0) >= min_reliability
        ]
    
    # ============================================
    # LAYER 6: SENTIMENT ANALYSIS
    # ============================================
    
    def _update_sentiment(self, trade: TradeRecord) -> Dict:
        """Layer 6: Update sentiment analysis"""
        try:
            self.sentiment_scores.append(trade.sentiment_score)
            
            # Calculate current sentiment
            if self.sentiment_scores:
                avg_score = np.mean(self.sentiment_scores)
                std_score = np.std(self.sentiment_scores) if len(self.sentiment_scores) > 1 else 0.1
                
                self.current_sentiment = SentimentData(
                    score=avg_score,
                    strength=abs(avg_score) / (std_score + 0.01),
                    direction='bullish' if avg_score > 0.2 else 'bearish' if avg_score < -0.2 else 'neutral',
                    sample_size=len(self.sentiment_scores),
                    volatility_adjustment=std_score,
                    timestamp=datetime.now()
                )
            
            return {
                'success': True,
                'sentiment': self.current_sentiment.__dict__ if hasattr(self.current_sentiment, '__dict__') else {}
            }
            
        except Exception as e:
            logger.error(f"Sentiment update error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_sentiment(self) -> SentimentData:
        """Get current sentiment"""
        return self.current_sentiment
    
    # ============================================
    # LAYER 7: VOLATILITY ANALYSIS
    # ============================================
    
    def _update_volatility(self, trade: TradeRecord) -> Dict:
        """Layer 7: Update volatility analysis"""
        try:
            self.volatility_history.append(trade.volatility_at_entry)
            self.atr_values.append(trade.volatility_at_entry)
            
            # Determine volatility regime
            if self.volatility_history:
                avg_vol = np.mean(self.volatility_history)
                std_vol = np.std(self.volatility_history) if len(self.volatility_history) > 1 else 0.1
                current_vol = self.volatility_history[-1]
                percentile = (current_vol - avg_vol) / (std_vol + 0.01)
                
                # Regime detection
                if current_vol > avg_vol + 2 * std_vol:
                    regime = "EXTREME"
                elif current_vol > avg_vol + std_vol:
                    regime = "HIGH"
                elif current_vol < avg_vol - std_vol:
                    regime = "LOW"
                else:
                    regime = "NORMAL"
                
                # Trend detection
                if len(self.volatility_history) > 10:
                    recent = list(self.volatility_history)[-10:]
                    if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                        trend = "INCREASING"
                    elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                        trend = "DECREASING"
                    else:
                        trend = "STABLE"
                else:
                    trend = "STABLE"
                
                self.volatility_regime = regime
                self.volatility_data = VolatilityData(
                    regime=regime,
                    current_atr=current_vol,
                    avg_atr=avg_vol,
                    percentile=percentile,
                    trend=trend,
                    sample_size=len(self.atr_values),
                    timestamp=datetime.now()
                )
            
            return {
                'success': True,
                'volatility': self.volatility_data.__dict__ if hasattr(self.volatility_data, '__dict__') else {}
            }
            
        except Exception as e:
            logger.error(f"Volatility update error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_volatility_status(self) -> VolatilityData:
        """Get current volatility status"""
        return self.volatility_data
    
    # ============================================
    # INDICATOR CALCULATIONS
    # ============================================
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = None) -> float:
        """Calculate Average True Range"""
        try:
            if period is None:
                period = self.indicator_params.get('atr_period', 14)
            high_low = data['high'] - data['low']
            high_close = abs(data['high'] - data['close'].shift())
            low_close = abs(data['low'] - data['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return tr.rolling(period).mean().iloc[-1]
        except:
            return 0.01
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate ADX"""
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()
            
            plus_dm = high.diff()
            minus_dm = low.diff()
            
            plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm.abs()), 0)
            minus_dm = (-minus_dm).where((minus_dm > 0) & (minus_dm > plus_dm.abs()), 0)
            
            plus_smoothed = plus_dm.rolling(period).mean()
            minus_smoothed = minus_dm.rolling(period).mean()
            
            plus_di = 100 * (plus_smoothed / atr)
            minus_di = 100 * (minus_smoothed / atr)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(period).mean()
            
            return adx.iloc[-1] if not adx.empty else 25
        except:
            return 25
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except:
            return pd.Series([50] * len(data))
    
    # ============================================
    # STATE MANAGEMENT
    # ============================================
    
    def _default_market_state(self) -> Dict:
        """Default market state when data is insufficient"""
        return {
            'regime': {'regime': 'RANGING', 'confidence': 0.3},
            'patterns': [],
            'sentiment': {'score': 0.0, 'strength': 0.0, 'direction': 'neutral'},
            'volatility': {'regime': 'NORMAL', 'current_atr': 0.01, 'avg_atr': 0.01},
            'params': self.indicator_params,
            'adjustments': {},
            'confidence_threshold': self.state.confidence_threshold,
            'risk_multiplier': self.state.risk_multiplier,
            'learning_phase': self.state.learning_phase.value,
            'win_rate': self.state.win_rate,
            'profit_factor': self.state.profit_factor,
            'regime_confidence': 0.3,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_adaptive_params(self) -> Dict:
        """Get all adaptive parameters"""
        return {
            'risk_multiplier': self.state.risk_multiplier,
            'confidence_threshold': self.state.confidence_threshold,
            'win_rate': self.state.win_rate,
            'profit_factor': self.state.profit_factor,
            'market_regime': self.current_regime.value if hasattr(self.current_regime, 'value') else "NEUTRAL",
            'learning_phase': self.state.learning_phase.value,
            'best_strategy': self.state.best_strategy,
            'avg_profit': self.state.avg_profit,
            'avg_loss': self.state.avg_loss,
            'total_trades': self.state.total_trades,
            'sharpe_ratio': self.state.sharpe_ratio,
            'sortino_ratio': self.state.sortino_ratio,
            'expectancy': self.state.expectancy,
            'max_drawdown': self.state.max_drawdown,
            'indicator_params': self.indicator_params,
            'sentiment': self.get_sentiment().__dict__ if hasattr(self.get_sentiment(), '__dict__') else {},
            'volatility': self.get_volatility_status().__dict__ if hasattr(self.get_volatility_status(), '__dict__') else {},
            'pattern_accuracy': self.pattern_accuracy,
            'q_table_size': len(self.q_table)
        }
    
    def get_learning_report(self) -> Dict:
        """Get comprehensive learning report"""
        return {
            'layer_1_trade_outcome': {
                'total_trades': self.state.total_trades,
                'win_rate': self.state.win_rate,
                'profit_factor': self.state.profit_factor,
                'avg_profit': self.state.avg_profit,
                'avg_loss': self.state.avg_loss,
                'consecutive_wins': self.state.consecutive_wins,
                'consecutive_losses': self.state.consecutive_losses,
                'sharpe_ratio': self.state.sharpe_ratio,
                'sortino_ratio': self.state.sortino_ratio,
                'expectancy': self.state.expectancy,
                'max_drawdown': self.state.max_drawdown
            },
            'layer_2_market_regime': {
                'current_regime': self.current_regime.value if hasattr(self.current_regime, 'value') else "NEUTRAL",
                'regime_performance': self.regime_performance,
                'transitions': self.market_transitions,
                'regime_confidence': self.regime_confidence,
                'history_length': len(self.regime_history)
            },
            'layer_3_indicator_optimization': {
                'current_params': self.indicator_params,
                'optimal_params': self.optimal_params,
                'param_performance': {k: np.mean(v) if v else 0 for k, v in self.param_performance.items()},
                'optimization_frequency': self.param_optimization_frequency
            },
            'layer_4_reinforcement': {
                'q_table_size': len(self.q_table),
                'recent_rewards': self.rewards_history[-10:] if self.rewards_history else [],
                'epsilon': self.epsilon,
                'state_visits': self.state_visits,
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor
            },
            'layer_5_pattern_recognition': {
                'patterns_detected': len(self.detected_patterns),
                'pattern_accuracy': self.pattern_accuracy,
                'known_patterns': self.known_patterns,
                'best_patterns': self.get_best_patterns()
            },
            'layer_6_sentiment': {
                'current_sentiment': self.current_sentiment.__dict__ if hasattr(self.current_sentiment, '__dict__') else {},
                'sample_size': len(self.sentiment_scores),
                'news_sentiment_size': len(self.news_sentiment),
                'social_sentiment_size': len(self.social_sentiment)
            },
            'layer_7_volatility': {
                'current_volatility': self.volatility_data.__dict__ if hasattr(self.volatility_data, '__dict__') else {},
                'regime': self.volatility_regime,
                'avg_atr': np.mean(self.atr_values) if self.atr_values else 0,
                'sample_size': len(self.atr_values)
            },
            'performance_summary': {
                'sharpe_ratio': self.state.sharpe_ratio,
                'sortino_ratio': self.state.sortino_ratio,
                'profit_factor': self.state.profit_factor,
                'win_rate': self.state.win_rate,
                'max_drawdown': self.state.max_drawdown,
                'expectancy': self.state.expectancy,
                'learning_phase': self.state.learning_phase.value,
                'total_trades': self.state.total_trades
            },
            'errors': self.error_log[-10:] if self.error_log else [],
            'timestamp': datetime.now().isoformat()
        }
    
    # ============================================
    # SAVE/LOAD
    # ============================================
    
    def _save_state(self):
        """Save learned models to disk"""
        try:
            os.makedirs("data/models", exist_ok=True)
            
            # Save Q-table
            q_table_serializable = {
                k: {ak: float(v) for ak, v in action_dict.items()}
                for k, action_dict in self.q_table.items()
            }
            with open("data/models/q_table.json", "w") as f:
                json.dump(q_table_serializable, f, indent=2)
            
            # Save indicator params
            with open("data/models/indicator_params.json", "w") as f:
                json.dump(self.indicator_params, f, indent=2)
            
            # Save state
            with open("data/models/state.json", "w") as f:
                json.dump({
                    'win_rate': self.state.win_rate,
                    'total_trades': self.state.total_trades,
                    'confidence_threshold': self.state.confidence_threshold,
                    'risk_multiplier': self.state.risk_multiplier,
                    'profit_factor': self.state.profit_factor,
                    'best_strategy': self.state.best_strategy,
                    'sharpe_ratio': self.state.sharpe_ratio,
                    'sortino_ratio': self.state.sortino_ratio,
                    'expectancy': self.state.expectancy,
                    'learning_phase': self.state.learning_phase.value,
                    'max_drawdown': self.state.max_drawdown,
                    'learning_iterations': self.learning_iterations
                }, f, indent=2)
            
            # Save pattern accuracy
            with open("data/models/pattern_accuracy.json", "w") as f:
                json.dump(self.pattern_accuracy, f, indent=2)
            
            # Save regime performance
            with open("data/models/regime_performance.json", "w") as f:
                json.dump(self.regime_performance, f, indent=2)
            
            logger.info("💾 Adaptive engine models saved")
            
        except Exception as e:
            logger.error(f"Save models error: {e}")
    
    def _load_state(self):
        """Load saved models from disk"""
        try:
            # Load Q-table
            if os.path.exists("data/models/q_table.json"):
                with open("data/models/q_table.json", "r") as f:
                    self.q_table = json.load(f)
            
            # Load indicator params
            if os.path.exists("data/models/indicator_params.json"):
                with open("data/models/indicator_params.json", "r") as f:
                    self.indicator_params = json.load(f)
            
            # Load state
            if os.path.exists("data/models/state.json"):
                with open("data/models/state.json", "r") as f:
                    state_data = json.load(f)
                    self.state.win_rate = state_data.get('win_rate', 0.5)
                    self.state.total_trades = state_data.get('total_trades', 0)
                    self.state.confidence_threshold = state_data.get('confidence_threshold', 65)
                    self.state.risk_multiplier = state_data.get('risk_multiplier', 1.0)
                    self.state.profit_factor = state_data.get('profit_factor', 1.0)
                    self.state.best_strategy = state_data.get('best_strategy', '')
                    self.state.sharpe_ratio = state_data.get('sharpe_ratio', 0.0)
                    self.state.sortino_ratio = state_data.get('sortino_ratio', 0.0)
                    self.state.expectancy = state_data.get('expectancy', 0.0)
                    self.state.max_drawdown = state_data.get('max_drawdown', 0.0)
                    self.learning_iterations = state_data.get('learning_iterations', 0)
                    
                    learning_phase = state_data.get('learning_phase', 'INITIAL')
                    try:
                        self.state.learning_phase = LearningPhase[learning_phase]
                    except:
                        self.state.learning_phase = LearningPhase.INITIAL
            
            # Load pattern accuracy
            if os.path.exists("data/models/pattern_accuracy.json"):
                with open("data/models/pattern_accuracy.json", "r") as f:
                    self.pattern_accuracy = json.load(f)
            
            # Load regime performance
            if os.path.exists("data/models/regime_performance.json"):
                with open("data/models/regime_performance.json", "r") as f:
                    self.regime_performance = json.load(f)
            
            logger.info("📂 Adaptive engine models loaded")
            
        except Exception as e:
            logger.warning(f"Load models error (starting fresh): {e}")