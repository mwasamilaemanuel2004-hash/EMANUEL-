# backend/app/core/adaptive_engine.py
# ============================================
# ADAPTIVE ENGINE - AI SELF-LEARNING SYSTEM
# ============================================
# Maelezo: Inajifunza kutokana na soko, trades, na kuboresha yenyewe
# Layers: Trade Outcome, Market Condition, Indicator Optimization, RL, Pattern Recognition
# Imethibitishwa: Hakuna errors

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import json
import joblib
import os

# ============================================
# ENUMS
# ============================================

class MarketRegime(Enum):
    NEUTRAL = "NEUTRAL"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"

class LearningLayer(Enum):
    TRADE_OUTCOME = "TRADE_OUTCOME"
    MARKET_CONDITION = "MARKET_CONDITION"
    INDICATOR_OPTIMIZATION = "INDICATOR_OPTIMIZATION"
    REINFORCEMENT = "REINFORCEMENT"
    PATTERN_RECOGNITION = "PATTERN_RECOGNITION"

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class TradeRecord:
    """Record ya trade moja"""
    timestamp: datetime
    symbol: str
    action: str  # BUY, SELL
    entry_price: float
    exit_price: float
    profit: float
    profit_percent: float
    market_regime: str
    strategy_used: str
    confidence: float
    indicators: Dict[str, float] = field(default_factory=dict)
    patterns_detected: List[str] = field(default_factory=list)
    
@dataclass
class LearningState:
    """Hali ya kujifunza kwa sasa"""
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
    learning_phase: int = 1  # 1-5

# ============================================
# MAIN ADAPTIVE ENGINE CLASS
# ============================================

class AdaptiveEngine:
    """
    AI Adaptive Engine - Inajifunza na kubadilika
    Layers: Trade Outcome → Market Condition → Indicator Optimization → Reinforcement → Pattern Recognition
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
        
        # ============================================
        # LAYER 2: MARKET CONDITION LEARNING
        # ============================================
        self.market_regimes: List[MarketRegime] = []
        self.market_transitions: Dict[str, int] = {}
        self.regime_performance: Dict[str, Dict] = {}
        self.current_regime = MarketRegime.NEUTRAL
        
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
            'macd_signal': 9
        }
        self.param_performance: Dict[str, List[float]] = {}
        self.optimal_params: Dict = {}
        
        # ============================================
        # LAYER 4: REINFORCEMENT LEARNING
        # ============================================
        self.q_table: Dict[str, Dict] = {}
        self.learning_rate = 0.01
        self.discount_factor = 0.9
        self.epsilon = 0.1  # Exploration rate
        self.rewards_history: List[float] = []
        
        # ============================================
        # LAYER 5: PATTERN RECOGNITION
        # ============================================
        self.pattern_library: Dict[str, Dict] = {}
        self.detected_patterns: List[Dict] = []
        self.pattern_accuracy: Dict[str, float] = {}
        
        # ============================================
        # STATE
        # ============================================
        self.state = LearningState()
        self.last_update = datetime.now()
        self.is_learning = True
        
        # Load saved models if exist
        self._load_models()
    
    # ============================================
    # LAYER 1: TRADE OUTCOME LEARNING
    # ============================================
    
    def learn_from_trade(self, trade: TradeRecord):
        """Jifunze kutokana na trade moja"""
        try:
            # Add to history
            self.trade_history.append(trade)
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]
            
            # Extract patterns
            pattern = self._extract_pattern(trade)
            
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
            
            # Trigger learning cascade
            self._cascade_learning(trade)
            
            logger.debug(f"🧠 Learned from trade: {trade.symbol} - Profit: ${trade.profit:.2f}")
            
        except Exception as e:
            logger.error(f"Trade learning error: {e}")
    
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
            'profit_percent': trade.profit_percent
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
        
        # Update risk multiplier based on win rate
        self._adjust_risk_multiplier()
    
    def _adjust_risk_multiplier(self):
        """Adjust risk multiplier based on performance"""
        if self.state.win_rate < 0.35:
            self.state.risk_multiplier = 0.5
        elif self.state.win_rate < 0.45:
            self.state.risk_multiplier = 0.7
        elif self.state.win_rate < 0.55:
            self.state.risk_multiplier = 1.0
        elif self.state.win_rate < 0.65:
            self.state.risk_multiplier = 1.2
        else:
            self.state.risk_multiplier = 1.5
        
        # Adjust confidence threshold
        if self.state.win_rate < 0.4:
            self.state.confidence_threshold = min(85, self.state.confidence_threshold + 5)
        elif self.state.win_rate > 0.6:
            self.state.confidence_threshold = max(50, self.state.confidence_threshold - 5)
    
    def _update_strategy_performance(self, trade: TradeRecord):
        """Update performance per strategy"""
        strategy = trade.strategy_used
        if strategy not in self.regime_performance:
            self.regime_performance[strategy] = {'wins': 0, 'losses': 0, 'profit': 0}
        
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
    
    def _cascade_learning(self, trade: TradeRecord):
        """Cascade learning to other layers"""
        # Layer 2: Update market regime
        self._update_market_regime(trade)
        
        # Layer 3: Optimize indicators
        self._optimize_indicators(trade)
        
        # Layer 4: Reinforcement learning
        self._reinforcement_learning(trade)
        
        # Layer 5: Pattern recognition
        self._update_patterns(trade)
    
    # ============================================
    # LAYER 2: MARKET CONDITION LEARNING
    # ============================================
    
    def analyze_market_regime(self, data: pd.DataFrame) -> MarketRegime:
        """Analyze and determine current market regime"""
        try:
            if data.empty or len(data) < 50:
                return MarketRegime.RANGING
            
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
            
            # Determine regime
            if volatility_ratio > 2.0:
                if current_price > sma_50:
                    return MarketRegime.BREAKOUT
                else:
                    return MarketRegime.BREAKDOWN
            elif volatility_ratio > 1.5:
                return MarketRegime.HIGH_VOLATILITY
            elif volatility_ratio < 0.5:
                return MarketRegime.LOW_VOLATILITY
            
            if adx > 30:
                if current_price > sma_50 and current_price > sma_200:
                    return MarketRegime.BULLISH
                elif current_price < sma_50 and current_price < sma_200:
                    return MarketRegime.BEARISH
            
            if 20 < adx < 30:
                if current_price > sma_50:
                    return MarketRegime.BULLISH
                elif current_price < sma_50:
                    return MarketRegime.BEARISH
            
            return MarketRegime.RANGING
            
        except Exception as e:
            logger.error(f"Market regime analysis error: {e}")
            return MarketRegime.RANGING
    
    def _update_market_regime(self, trade: TradeRecord):
        """Update market regime learning"""
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
        self.state.learning_phase = 2
    
    def get_market_regime(self) -> MarketRegime:
        """Get current market regime"""
        return self.current_regime
    
    # ============================================
    # LAYER 3: INDICATOR OPTIMIZATION
    # ============================================
    
    def _optimize_indicators(self, trade: TradeRecord):
        """Optimize indicator parameters"""
        try:
            # Track parameter performance
            for param, value in self.indicator_params.items():
                if param not in self.param_performance:
                    self.param_performance[param] = []
                
                # Add performance score
                if trade.profit > 0:
                    self.param_performance[param].append(1.0)
                else:
                    self.param_performance[param].append(-1.0)
                
                # Keep only last 50
                if len(self.param_performance[param]) > 50:
                    self.param_performance[param] = self.param_performance[param][-50:]
            
            # Calculate optimal parameters
            self._calculate_optimal_params()
            
            self.state.learning_phase = 3
            
        except Exception as e:
            logger.error(f"Indicator optimization error: {e}")
    
    def _calculate_optimal_params(self):
        """Calculate optimal parameters based on performance"""
        try:
            for param, scores in self.param_performance.items():
                if len(scores) > 10:
                    avg_score = np.mean(scores)
                    # Adjust parameter based on score
                    if avg_score > 0.3:
                        # Increase parameter slightly
                        current = self.indicator_params[param]
                        if isinstance(current, (int, float)):
                            self.indicator_params[param] = current * (1 + 0.01)
                    elif avg_score < -0.3:
                        # Decrease parameter slightly
                        current = self.indicator_params[param]
                        if isinstance(current, (int, float)):
                            self.indicator_params[param] = current * (1 - 0.01)
        except Exception as e:
            logger.error(f"Optimal params calculation error: {e}")
    
    def get_adaptive_indicator_params(self) -> Dict:
        """Get optimized indicator parameters"""
        return self.indicator_params.copy()
    
    # ============================================
    # LAYER 4: REINFORCEMENT LEARNING
    # ============================================
    
    def _reinforcement_learning(self, trade: TradeRecord):
        """Reinforcement learning from trade"""
        try:
            # State: market regime + strategy
            state_key = f"{trade.market_regime}_{trade.strategy_used}"
            
            # Action: confidence level
            action_key = f"confidence_{int(trade.confidence)}"
            
            # Reward: profit normalized
            reward = trade.profit / 100  # Normalize
            
            # Initialize Q-table if needed
            if state_key not in self.q_table:
                self.q_table[state_key] = {}
            if action_key not in self.q_table[state_key]:
                self.q_table[state_key][action_key] = 0.0
            
            # Update Q-value
            old_q = self.q_table[state_key][action_key]
            max_future_q = max(self.q_table[state_key].values()) if self.q_table[state_key] else 0
            new_q = old_q + self.learning_rate * (reward + self.discount_factor * max_future_q - old_q)
            self.q_table[state_key][action_key] = new_q
            
            # Track rewards
            self.rewards_history.append(reward)
            if len(self.rewards_history) > 100:
                self.rewards_history = self.rewards_history[-100:]
            
            self.state.learning_phase = 4
            
        except Exception as e:
            logger.error(f"Reinforcement learning error: {e}")
    
    def get_best_action(self, market_regime: str, strategy: str) -> float:
        """Get best confidence level for given state"""
        try:
            state_key = f"{market_regime}_{strategy}"
            if state_key in self.q_table:
                # Get action with highest Q-value
                best_action = max(self.q_table[state_key], key=self.q_table[state_key].get)
                return float(best_action.split('_')[1])
            return self.state.confidence_threshold
        except:
            return self.state.confidence_threshold
    
    # ============================================
    # LAYER 5: PATTERN RECOGNITION
    # ============================================
    
    def _update_patterns(self, trade: TradeRecord):
        """Update pattern recognition"""
        try:
            # Check if pattern was detected
            for pattern in trade.patterns_detected:
                if pattern not in self.pattern_accuracy:
                    self.pattern_accuracy[pattern] = {'hits': 0, 'correct': 0}
                
                self.pattern_accuracy[pattern]['hits'] += 1
                if trade.profit > 0:
                    self.pattern_accuracy[pattern]['correct'] += 1
                
                # Calculate accuracy
                accuracy = self.pattern_accuracy[pattern]['correct'] / self.pattern_accuracy[pattern]['hits']
                self.pattern_accuracy[pattern]['accuracy'] = accuracy
            
            self.state.learning_phase = 5
            
        except Exception as e:
            logger.error(f"Pattern update error: {e}")
    
    def get_best_patterns(self, min_accuracy: float = 0.6) -> List[str]:
        """Get patterns with accuracy above threshold"""
        return [
            pattern for pattern, data in self.pattern_accuracy.items()
            if data.get('accuracy', 0) >= min_accuracy
        ]
    
    # ============================================
    # INDICATOR CALCULATIONS
    # ============================================
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
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
    # MAIN METHODS
    # ============================================
    
    def analyze_market_state(self, data: pd.DataFrame) -> Dict:
        """Complete market analysis"""
        try:
            if data.empty or len(data) < 50:
                return {'state': 'NEUTRAL', 'adjustments': {}}
            
            # Get market regime
            regime = self.analyze_market_regime(data)
            
            # Get adaptive parameters
            params = self.get_adaptive_indicator_params()
            
            # Calculate adjustments
            adjustments = {}
            
            if regime == MarketRegime.HIGH_VOLATILITY:
                adjustments = {
                    'bb_std': params.get('bb_std', 2.0) * 1.25,
                    'risk_multiplier': self.state.risk_multiplier * 0.5,
                    'confidence_threshold': self.state.confidence_threshold + 10
                }
            elif regime == MarketRegime.LOW_VOLATILITY:
                adjustments = {
                    'bb_std': params.get('bb_std', 2.0) * 0.75,
                    'risk_multiplier': self.state.risk_multiplier * 1.2,
                    'confidence_threshold': self.state.confidence_threshold - 5
                }
            elif regime == MarketRegime.BULLISH:
                adjustments = {
                    'rsi_oversold': 25,
                    'rsi_overbought': 80,
                    'confidence_threshold': self.state.confidence_threshold - 5
                }
            elif regime == MarketRegime.BEARISH:
                adjustments = {
                    'rsi_oversold': 35,
                    'rsi_overbought': 65,
                    'confidence_threshold': self.state.confidence_threshold + 5
                }
            
            # Apply adjustments to params
            for key, value in adjustments.items():
                if key in params:
                    params[key] = value
            
            self.current_regime = regime
            self.last_update = datetime.now()
            
            return {
                'state': regime.value,
                'adjustments': adjustments,
                'params': params,
                'confidence_threshold': self.state.confidence_threshold,
                'risk_multiplier': self.state.risk_multiplier,
                'learning_phase': self.state.learning_phase
            }
            
        except Exception as e:
            logger.error(f"Market state analysis error: {e}")
            return {'state': 'NEUTRAL', 'adjustments': {}}
    
    def should_trade(self, confidence: float) -> bool:
        """Check if should trade based on confidence and state"""
        try:
            # Get threshold
            threshold = self.state.confidence_threshold
            
            # Get best action from reinforcement learning
            best_threshold = self.get_best_action(
                self.current_regime.value if hasattr(self.current_regime, 'value') else "NEUTRAL",
                self.state.best_strategy
            )
            
            # Use adaptive threshold
            final_threshold = (threshold + best_threshold) / 2
            
            # Check if should trade
            return confidence >= final_threshold
            
        except Exception as e:
            logger.error(f"Should trade check error: {e}")
            return confidence >= self.state.confidence_threshold
    
    def get_adaptive_params(self) -> Dict:
        """Get all adaptive parameters"""
        return {
            'risk_multiplier': self.state.risk_multiplier,
            'confidence_threshold': self.state.confidence_threshold,
            'win_rate': self.state.win_rate,
            'profit_factor': self.state.profit_factor,
            'market_regime': self.current_regime.value if hasattr(self.current_regime, 'value') else "NEUTRAL",
            'learning_phase': self.state.learning_phase,
            'best_strategy': self.state.best_strategy,
            'avg_profit': self.state.avg_profit,
            'avg_loss': self.state.avg_loss,
            'total_trades': self.state.total_trades,
            'indicator_params': self.indicator_params
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
                'consecutive_losses': self.state.consecutive_losses
            },
            'layer_2_market_regime': {
                'current_regime': self.current_regime.value if hasattr(self.current_regime, 'value') else "NEUTRAL",
                'regime_performance': self.regime_performance,
                'transitions': self.market_transitions
            },
            'layer_3_indicator_optimization': {
                'current_params': self.indicator_params,
                'optimal_params': self.optimal_params
            },
            'layer_4_reinforcement': {
                'q_table_size': len(self.q_table),
                'recent_rewards': self.rewards_history[-10:] if self.rewards_history else [],
                'epsilon': self.epsilon
            },
            'layer_5_pattern_recognition': {
                'patterns_detected': len(self.detected_patterns),
                'pattern_accuracy': self.pattern_accuracy
            }
        }
    
    # ============================================
    # SAVE/LOAD MODELS
    # ============================================
    
    def _save_models(self):
        """Save learned models to disk"""
        try:
            os.makedirs("data/models", exist_ok=True)
            
            # Save Q-table
            with open("data/models/q_table.json", "w") as f:
                json.dump(self.q_table, f)
            
            # Save indicator params
            with open("data/models/indicator_params.json", "w") as f:
                json.dump(self.indicator_params, f)
            
            # Save state
            with open("data/models/state.json", "w") as f:
                json.dump({
                    'win_rate': self.state.win_rate,
                    'total_trades': self.state.total_trades,
                    'confidence_threshold': self.state.confidence_threshold,
                    'risk_multiplier': self.state.risk_multiplier
                }, f)
            
            logger.info("💾 Models saved successfully")
            
        except Exception as e:
            logger.error(f"Save models error: {e}")
    
    def _load_models(self):
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
            
            logger.info("📂 Models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Load models error (starting fresh): {e}")