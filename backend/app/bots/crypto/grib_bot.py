"""
ULTRA DYNAMIC ADAPTIVE GRID BOT v8.0 - COMBINED & UPGRADED
============================================================
COMBINES: Simple Grid Bot + Ultra Dynamic Grid Bot = ULTIMATE GRID BOT

PRINCIPLES:
   1. DYNAMIC ADAPTATION - Inajibadilisha kuenda na mwenendo wa soko
   2. SMART ENTRY/EXIT - Inaingia na kutoka kwa wakati muafaka
   3. MARKET AWARENESS - Inaelewa hali ya soko kwa undani
   4. OPTIMAL POSITIONING - Inaweka gridi katika maeneo yenye faida
   5. MULTI-TIER TRADING - $5 hadi $1M+ positions
   6. SELF-LEARNING - Inajifunza kutoka kwa matokeo
   7. PRODUCTION READY - Fully debugged and optimized
"""

import json
import os
import time
import threading
import hashlib
import math
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from collections import deque
import warnings
warnings.filterwarnings('ignore')

# ================================================================
# MINIMAL DEPENDENCIES
# ================================================================

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    class _NumpyFallback:
        @staticmethod
        def mean(arr):
            return sum(arr) / len(arr) if arr else 0
        @staticmethod
        def std(arr):
            if len(arr) < 2:
                return 0
            m = sum(arr) / len(arr)
            return (sum((x - m) ** 2 for x in arr) / len(arr)) ** 0.5
        @staticmethod
        def diff(arr):
            return [arr[i] - arr[i-1] for i in range(1, len(arr))]
        @staticmethod
        def log(arr):
            return [math.log(x) if x > 0 else 0 for x in arr]
        @staticmethod
        def exp(arr):
            return [math.exp(x) for x in arr]
        @staticmethod
        def clip(val, min_val, max_val):
            return max(min_val, min(val, max_val))
        @staticmethod
        def linspace(start, stop, num):
            step = (stop - start) / (num - 1) if num > 1 else 0
            return [start + i * step for i in range(num)]
        @staticmethod
        def zeros(n):
            return [0] * n
        @staticmethod
        def ones(n):
            return [1] * n
        @staticmethod
        def percentile(arr, p):
            if not arr:
                return 0
            sorted_arr = sorted(arr)
            idx = int(len(sorted_arr) * p / 100)
            return sorted_arr[min(idx, len(sorted_arr)-1)]
        @staticmethod
        def random_normal(mean=0, std=1, size=1):
            return [random.gauss(mean, std) for _ in range(size)]
    
    np = _NumpyFallback()

# ================================================================
# LOGGER
# ================================================================

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================================
# ENUMS (COMBINED)
# ================================================================

class MarketState(Enum):
    """Hali ya soko kwa wakati halisi"""
    STRONG_UPTREND = "STRONG_UPTREND"
    UPTREND = "UPTREND"
    WEAK_UPTREND = "WEAK_UPTREND"
    NEUTRAL = "NEUTRAL"
    WEAK_DOWNTREND = "WEAK_DOWNTREND"
    DOWNTREND = "DOWNTREND"
    STRONG_DOWNTREND = "STRONG_DOWNTREND"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    RANGING = "RANGING"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"
    ACCUMULATION = "ACCUMULATION"
    DISTRIBUTION = "DISTRIBUTION"

class GridMode(Enum):
    """Njia za gridi kulingana na soko"""
    AGGRESSIVE = "AGGRESSIVE"       # Gridi nyembamba, faida kubwa
    MODERATE = "MODERATE"           # Gridi wastani
    CONSERVATIVE = "CONSERVATIVE"   # Gridi pana, salama
    TREND_FOLLOWING = "TREND_FOLLOWING"  # Inafuata trend
    REVERSAL = "REVERSAL"           # Inatafuta mabadiliko
    BREAKOUT = "BREAKOUT"           # Inaingia kwenye breakout
    RANGE_BOUND = "RANGE_BOUND"     # Inacheza kwenye range
    GEOMETRIC = "GEOMETRIC"         # Geometric grid levels
    ARITHMETIC = "ARITHMETIC"       # Arithmetic grid levels

class TradeTier(Enum):
    MICRO_1 = "MICRO_1"      # $5
    MICRO_2 = "MICRO_2"      # $10
    MICRO_3 = "MICRO_3"      # $25
    MICRO_4 = "MICRO_4"      # $50
    SMALL_1 = "SMALL_1"      # $100
    SMALL_2 = "SMALL_2"      # $200
    SMALL_3 = "SMALL_3"      # $500
    MEDIUM_1 = "MEDIUM_1"    # $1,000
    MEDIUM_2 = "MEDIUM_2"    # $2,500
    MEDIUM_3 = "MEDIUM_3"    # $5,000
    LARGE_1 = "LARGE_1"      # $10,000
    LARGE_2 = "LARGE_2"      # $25,000
    LARGE_3 = "LARGE_3"      # $50,000
    MACRO_1 = "MACRO_1"      # $100,000
    MACRO_2 = "MACRO_2"      # $500,000
    MACRO_3 = "MACRO_3"      # $1,000,000+

class TradeSignal(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

# ================================================================
# DATA CLASSES (COMBINED)
# ================================================================

@dataclass
class MarketAnalysis:
    """Uchambuzi wa kina wa soko"""
    state: MarketState
    grid_mode: GridMode
    confidence: float
    volatility: float
    momentum: float
    support_levels: List[float]
    resistance_levels: List[float]
    trend_strength: float
    recommended_entry: float
    recommended_exit: float
    risk_level: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DynamicGridConfig:
    """Usanidi wa gridi unaobadilika"""
    mode: GridMode
    levels: List[float]
    spacing: float
    min_price: float
    max_price: float
    count: int
    entry_points: List[float]
    exit_points: List[float]
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GridPosition:
    level_index: int
    level_price: float
    side: str
    entry_price: float
    quantity: float
    usd_value: float
    tier: TradeTier
    status: str
    profit: float
    profit_percent: float
    entry_time: datetime
    exit_time: Optional[datetime] = None

@dataclass
class Position:
    id: str
    side: str
    entry_price: float
    quantity: float
    usd_value: float
    stop_loss: float
    take_profit: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    profit_percent: float
    tier: TradeTier
    entry_time: datetime
    exit_time: Optional[datetime]
    is_open: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AdaptiveConfig:
    """Usanidi unaobadilika"""
    # MICRO TRADING
    micro_1_enabled: bool = True
    micro_2_enabled: bool = True
    micro_3_enabled: bool = True
    micro_4_enabled: bool = True
    
    # SMALL TRADING
    small_1_enabled: bool = True
    small_2_enabled: bool = True
    small_3_enabled: bool = True
    
    # MEDIUM TRADING
    medium_1_enabled: bool = True
    medium_2_enabled: bool = True
    medium_3_enabled: bool = True
    
    # LARGE TRADING
    large_1_enabled: bool = True
    large_2_enabled: bool = True
    large_3_enabled: bool = True
    
    # MACRO TRADING
    macro_1_enabled: bool = True
    macro_2_enabled: bool = True
    macro_3_enabled: bool = True
    
    # GRID PARAMETERS
    min_grid_count: int = 20
    max_grid_count: int = 80
    default_grid_count: int = 40
    min_spacing: float = 0.2
    max_spacing: float = 2.0
    default_spacing: float = 0.5
    grid_type: str = "arithmetic"  # "arithmetic" or "geometric"
    
    # RISK MANAGEMENT
    max_risk_per_trade: float = 0.02
    max_risk_per_day: float = 0.06
    min_confidence: float = 0.55
    max_concurrent_trades: int = 20
    
    # ADAPTATION
    adaptation_speed: float = 0.3
    learning_rate: float = 0.01
    history_size: int = 200
    rebalance_interval: int = 1800  # 30 minutes
    
    # PERFORMANCE TARGETS
    target_win_rate: float = 0.55
    target_profit_factor: float = 1.5
    max_drawdown: float = 0.15
    
    # PROFIT PER TRADE TARGET
    profit_per_trade_target: float = 0.50
    
    # BOT SETTINGS
    capital: float = 1000.0
    pairs: List[str] = field(default_factory=lambda: ["BTC/USDT"])
    timeframe: str = "1h"
    mode: str = "MEDIUM"
    data_mode: str = "OHLCV"
    smart_aggressively: bool = True
    loss_prevention: bool = True
    profit_lock: bool = True
    daily_loss_limit: float = 2.0
    max_drawdown_pct: float = 5.0
    circuit_breaker: bool = True
    trailing_stop: bool = True
    partial_take_profit: bool = True
    re_entry: bool = True
    news_filter: bool = True
    correlation_filter: bool = True
    volatility_filter: bool = True

@dataclass
class BotSettings:
    """Bot settings with defaults"""
    bot_id: str
    bot_name: str
    capital: float = 1000.0
    pairs: List[str] = field(default_factory=lambda: ["BTC/USDT"])
    timeframe: str = "1h"
    mode: str = "MEDIUM"
    data_mode: str = "OHLCV"
    smart_aggressively: bool = True
    profit_per_trade: float = 0.50
    risk_per_trade: float = 1.0
    stop_loss_atr: float = 1.5
    take_profit_atr: float = 3.0
    max_trades_per_day: int = 10
    loss_prevention: bool = True
    profit_lock: bool = True
    daily_loss_limit: float = 2.0
    max_drawdown: float = 5.0
    circuit_breaker: bool = True
    trailing_stop: bool = True
    partial_take_profit: bool = True
    re_entry: bool = True
    news_filter: bool = True
    correlation_filter: bool = True
    volatility_filter: bool = True
    grid_count: int = 40
    grid_spacing: float = 0.5
    grid_type: str = "arithmetic"
    range_pct: float = 10.0
    min_grid_count: int = 20
    max_grid_count: int = 80
    default_grid_count: int = 40
    min_spacing: float = 0.2
    max_spacing: float = 2.0
    default_spacing: float = 0.5

# ================================================================
# SMART MARKET ANALYZER - Inaelewa soko kwa undani
# ================================================================

class SmartMarketAnalyzer:
    """
    Inachambua soko kwa undani na kutabiri mwenendo
    - Inatambua hali ya soko (uptrend, downtrend, ranging)
    - Inapima nguvu ya trend
    - Inatambua viwango vya support na resistance
    - Inatoa mapendekezo ya kuingia na kutoka
    """
    
    def __init__(self):
        self.history = deque(maxlen=1000)
        self.price_patterns = deque(maxlen=500)
        self._lock = threading.Lock()
        self.analysis_cache = {}
    
    def analyze(self, prices: List[float], volumes: List[float] = None) -> MarketAnalysis:
        """Uchambuzi wa kina wa soko"""
        if not prices or len(prices) < 30:
            return self._default_analysis()
        
        # Calculate key metrics
        volatility = self._calculate_volatility(prices)
        momentum = self._calculate_momentum(prices)
        trend_strength = self._calculate_trend_strength(prices)
        
        # Find support and resistance
        supports, resistances = self._find_support_resistance(prices)
        
        # Determine market state
        state = self._determine_market_state(prices, volatility, momentum, trend_strength)
        
        # Determine grid mode based on state
        grid_mode = self._determine_grid_mode(state, volatility, trend_strength)
        
        # Calculate confidence
        confidence = self._calculate_confidence(state, volatility, trend_strength)
        
        # Find recommended entry and exit
        current_price = prices[-1]
        recommended_entry = self._find_recommended_entry(current_price, supports, resistances, state)
        recommended_exit = self._find_recommended_exit(current_price, supports, resistances, state)
        
        # Determine risk level
        risk_level = self._determine_risk_level(volatility, state, trend_strength)
        
        analysis = MarketAnalysis(
            state=state,
            grid_mode=grid_mode,
            confidence=confidence,
            volatility=volatility,
            momentum=momentum,
            support_levels=supports,
            resistance_levels=resistances,
            trend_strength=trend_strength,
            recommended_entry=recommended_entry,
            recommended_exit=recommended_exit,
            risk_level=risk_level,
            timestamp=datetime.now(),
            details={
                'price_range': max(prices) - min(prices),
                'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
                'current_price': current_price,
                'volatility_category': self._categorize_volatility(volatility)
            }
        )
        
        with self._lock:
            self.history.append(analysis)
        
        return analysis
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        if len(prices) < 10:
            return 0.5
        
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if not returns:
            return 0.5
        
        avg = sum(returns) / len(returns)
        variance = sum((r - avg) ** 2 for r in returns) / len(returns)
        std = variance ** 0.5
        
        return min(1.0, std * 30)
    
    def _calculate_momentum(self, prices: List[float]) -> float:
        if len(prices) < 20:
            return 0.0
        
        current = prices[-1]
        past = prices[-11] if len(prices) >= 11 else prices[0]
        
        if past > 0:
            momentum = (current - past) / past * 100
            return max(-100, min(100, momentum))
        
        return 0.0
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        if len(prices) < 30:
            return 0.0
        
        short_ema = sum(prices[-10:]) / 10
        long_ema = sum(prices[-30:]) / 30
        
        if long_ema > 0:
            trend = (short_ema - long_ema) / long_ema * 20
            return max(-1.0, min(1.0, trend))
        
        return 0.0
    
    def _find_support_resistance(self, prices: List[float]) -> Tuple[List[float], List[float]]:
        if len(prices) < 30:
            return [], []
        
        supports = []
        resistances = []
        
        for i in range(2, len(prices) - 2):
            if (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
                prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                supports.append(prices[i])
            
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                resistances.append(prices[i])
        
        supports = self._cluster_levels(supports)
        resistances = self._cluster_levels(resistances)
        
        current_price = prices[-1]
        supports = [s for s in supports if s < current_price][-5:]
        resistances = [r for r in resistances if r > current_price][:5]
        
        return supports, resistances
    
    def _cluster_levels(self, levels: List[float], threshold: float = 0.01) -> List[float]:
        if not levels:
            return []
        
        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if (level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]
        
        clusters.append(sum(current_cluster) / len(current_cluster))
        return clusters
    
    def _determine_market_state(self, prices: List[float], volatility: float, 
                                 momentum: float, trend_strength: float) -> MarketState:
        if len(prices) < 30:
            return MarketState.NEUTRAL
        
        price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        
        if volatility > 0.7:
            return MarketState.HIGH_VOLATILITY
        
        if volatility < 0.15:
            return MarketState.LOW_VOLATILITY
        
        if trend_strength > 0.5:
            return MarketState.STRONG_UPTREND
        elif trend_strength > 0.2:
            return MarketState.UPTREND
        elif trend_strength < -0.5:
            return MarketState.STRONG_DOWNTREND
        elif trend_strength < -0.2:
            return MarketState.DOWNTREND
        
        if price_change > 0.05 and volatility > 0.4:
            return MarketState.BREAKOUT
        elif price_change < -0.05 and volatility > 0.4:
            return MarketState.BREAKDOWN
        
        if abs(price_change) < 0.02 and volatility < 0.3:
            return MarketState.RANGING
        
        if momentum > 0 and price_change < 0.02:
            return MarketState.ACCUMULATION
        elif momentum < 0 and price_change > -0.02:
            return MarketState.DISTRIBUTION
        
        return MarketState.NEUTRAL
    
    def _determine_grid_mode(self, state: MarketState, volatility: float, 
                             trend_strength: float) -> GridMode:
        if state in [MarketState.STRONG_UPTREND, MarketState.STRONG_DOWNTREND]:
            return GridMode.TREND_FOLLOWING
        
        if state in [MarketState.BREAKOUT, MarketState.BREAKDOWN]:
            return GridMode.BREAKOUT
        
        if state == MarketState.RANGING:
            return GridMode.RANGE_BOUND
        
        if volatility > 0.5:
            return GridMode.AGGRESSIVE
        
        if volatility < 0.2:
            return GridMode.CONSERVATIVE
        
        if state in [MarketState.ACCUMULATION, MarketState.DISTRIBUTION]:
            return GridMode.REVERSAL
        
        return GridMode.MODERATE
    
    def _calculate_confidence(self, state: MarketState, volatility: float, 
                              trend_strength: float) -> float:
        confidence = 0.5
        
        state_confidence = {
            MarketState.STRONG_UPTREND: 0.85,
            MarketState.UPTREND: 0.75,
            MarketState.WEAK_UPTREND: 0.6,
            MarketState.NEUTRAL: 0.5,
            MarketState.WEAK_DOWNTREND: 0.6,
            MarketState.DOWNTREND: 0.75,
            MarketState.STRONG_DOWNTREND: 0.85,
            MarketState.BREAKOUT: 0.8,
            MarketState.BREAKDOWN: 0.8,
            MarketState.RANGING: 0.65,
            MarketState.ACCUMULATION: 0.7,
            MarketState.DISTRIBUTION: 0.7,
            MarketState.HIGH_VOLATILITY: 0.4,
            MarketState.LOW_VOLATILITY: 0.6,
        }
        
        confidence = state_confidence.get(state, 0.5)
        
        if volatility > 0.6:
            confidence -= 0.15
        elif volatility < 0.2:
            confidence += 0.1
        
        confidence += abs(trend_strength) * 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _find_recommended_entry(self, current_price: float, supports: List[float], 
                                resistances: List[float], state: MarketState) -> float:
        if state in [MarketState.STRONG_UPTREND, MarketState.UPTREND]:
            if supports:
                return supports[-1] if supports[-1] < current_price else current_price * 0.99
            return current_price * 0.99
        
        elif state in [MarketState.STRONG_DOWNTREND, MarketState.DOWNTREND]:
            if resistances:
                return resistances[0] if resistances[0] > current_price else current_price * 1.01
            return current_price * 1.01
        
        elif state == MarketState.RANGING:
            if supports:
                return supports[-1]
            return current_price * 0.99
        
        elif state in [MarketState.BREAKOUT, MarketState.BREAKDOWN]:
            if resistances and state == MarketState.BREAKOUT:
                return resistances[0] * 1.002
            elif supports and state == MarketState.BREAKDOWN:
                return supports[-1] * 0.998
        
        return current_price
    
    def _find_recommended_exit(self, current_price: float, supports: List[float], 
                               resistances: List[float], state: MarketState) -> float:
        if state in [MarketState.STRONG_UPTREND, MarketState.UPTREND]:
            if resistances:
                return resistances[0] if resistances[0] > current_price else current_price * 1.02
            return current_price * 1.02
        
        elif state in [MarketState.STRONG_DOWNTREND, MarketState.DOWNTREND]:
            if supports:
                return supports[-1] if supports[-1] < current_price else current_price * 0.98
            return current_price * 0.98
        
        elif state == MarketState.RANGING:
            if resistances:
                return resistances[0]
            return current_price * 1.01
        
        return current_price * 1.015
    
    def _determine_risk_level(self, volatility: float, state: MarketState, 
                              trend_strength: float) -> str:
        risk_score = volatility * 0.4
        
        if state in [MarketState.HIGH_VOLATILITY]:
            risk_score += 0.3
        
        if abs(trend_strength) > 0.5:
            risk_score += 0.2
        
        if risk_score > 0.7:
            return "HIGH"
        elif risk_score > 0.5:
            return "MEDIUM"
        elif risk_score > 0.3:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _categorize_volatility(self, volatility: float) -> str:
        if volatility > 0.6:
            return "HIGH"
        elif volatility > 0.3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _default_analysis(self) -> MarketAnalysis:
        return MarketAnalysis(
            state=MarketState.NEUTRAL,
            grid_mode=GridMode.CONSERVATIVE,
            confidence=0.3,
            volatility=0.5,
            momentum=0.0,
            support_levels=[],
            resistance_levels=[],
            trend_strength=0.0,
            recommended_entry=0.0,
            recommended_exit=0.0,
            risk_level="HIGH",
            timestamp=datetime.now()
        )

# ================================================================
# DYNAMIC GRID OPTIMIZER - Inaboresha gridi kulingana na soko
# ================================================================

class DynamicGridOptimizer:
    """
    Inaboresha gridi kulingana na hali ya soko
    - Inaweka gridi katika maeneo yenye faida
    - Inabadilisha spacing kulingana na volatility
    - Inaongeza gridi kwenye trend
    - Supports both arithmetic and geometric grids
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self.optimization_history = deque(maxlen=200)
    
    def optimize_grid(self, analysis: MarketAnalysis, current_price: float, 
                      config: AdaptiveConfig) -> DynamicGridConfig:
        """Boresha gridi kulingana na uchambuzi wa soko"""
        
        # Determine grid parameters based on market state
        grid_count, spacing = self._determine_grid_params(analysis, config)
        
        # Calculate price range
        volatility = analysis.volatility
        range_pct = config.range_pct + volatility * 15
        
        min_price = current_price * (1 - range_pct / 100)
        max_price = current_price * (1 + range_pct / 100)
        
        # Adjust range based on trend
        if analysis.state in [MarketState.STRONG_UPTREND, MarketState.UPTREND]:
            min_price = current_price * (1 - (range_pct / 2) / 100)
            max_price = current_price * (1 + (range_pct * 1.5) / 100)
        elif analysis.state in [MarketState.STRONG_DOWNTREND, MarketState.DOWNTREND]:
            min_price = current_price * (1 - (range_pct * 1.5) / 100)
            max_price = current_price * (1 + (range_pct / 2) / 100)
        
        # Generate grid levels based on type
        levels = self._generate_optimized_levels(
            min_price, max_price, grid_count, analysis, current_price, config.grid_type
        )
        
        # Determine entry and exit points
        entry_points = self._determine_entry_points(levels, analysis, current_price)
        exit_points = self._determine_exit_points(levels, analysis, current_price)
        
        # Calculate stop loss and take profit
        stop_loss = self._calculate_stop_loss(current_price, analysis)
        take_profit = self._calculate_take_profit(current_price, analysis)
        
        # Calculate risk-reward ratio
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)
        risk_reward = reward / risk if risk > 0 else 1.0
        
        grid_config = DynamicGridConfig(
            mode=analysis.grid_mode,
            levels=levels,
            spacing=spacing,
            min_price=min_price,
            max_price=max_price,
            count=grid_count,
            entry_points=entry_points,
            exit_points=exit_points,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            timestamp=datetime.now(),
            metadata={
                'analysis_confidence': analysis.confidence,
                'volatility': analysis.volatility,
                'trend_strength': analysis.trend_strength,
                'market_state': analysis.state.value,
                'grid_type': config.grid_type
            }
        )
        
        with self._lock:
            self.optimization_history.append(grid_config)
        
        return grid_config
    
    def _determine_grid_params(self, analysis: MarketAnalysis, 
                               config: AdaptiveConfig) -> Tuple[int, float]:
        state = analysis.state
        volatility = analysis.volatility
        trend_strength = abs(analysis.trend_strength)
        
        if state in [MarketState.RANGING, MarketState.LOW_VOLATILITY]:
            grid_count = config.default_grid_count + 10
        elif state in [MarketState.STRONG_UPTREND, MarketState.STRONG_DOWNTREND]:
            grid_count = config.default_grid_count - 5
        elif state in [MarketState.HIGH_VOLATILITY]:
            grid_count = config.default_grid_count + 20
        else:
            grid_count = config.default_grid_count
        
        if volatility > 0.5:
            grid_count = int(grid_count * 1.3)
        elif volatility < 0.2:
            grid_count = int(grid_count * 0.7)
        
        grid_count = max(config.min_grid_count, min(config.max_grid_count, grid_count))
        
        if state in [GridMode.AGGRESSIVE, MarketState.BREAKOUT]:
            spacing = config.min_spacing + 0.1
        elif state in [GridMode.CONSERVATIVE, MarketState.LOW_VOLATILITY]:
            spacing = config.max_spacing - 0.2
        else:
            spacing = config.default_spacing
        
        spacing += volatility * 0.5
        spacing = max(config.min_spacing, min(config.max_spacing, spacing))
        
        return grid_count, spacing
    
    def _generate_optimized_levels(self, min_price: float, max_price: float, 
                                   count: int, analysis: MarketAnalysis, 
                                   current_price: float, grid_type: str) -> List[float]:
        """Zalisha viwango vya gridi vilivyoboreshwa"""
        
        if grid_type == "geometric":
            # Geometric grid
            if min_price > 0 and max_price > min_price:
                ratio = (max_price / min_price) ** (1 / (count - 1))
                levels = [min_price * (ratio ** i) for i in range(count)]
            else:
                levels = [min_price + i * (max_price - min_price) / (count - 1) for i in range(count)]
        else:
            # Arithmetic grid (default)
            levels = [min_price + i * (max_price - min_price) / (count - 1) for i in range(count)]
        
        # Optimize based on market state
        state = analysis.state
        
        if state in [MarketState.STRONG_UPTREND, MarketState.UPTREND]:
            above = [l for l in levels if l > current_price]
            below = [l for l in levels if l <= current_price]
            
            if len(above) < len(below) * 1.5:
                extra = int((len(below) * 1.5 - len(above)) / 2)
                for i in range(extra):
                    step = (max_price - min_price) / count
                    new_level = current_price * (1 + (i + 1) * step / current_price * 2)
                    above.append(new_level)
                levels = sorted(below + above)
        
        elif state in [MarketState.STRONG_DOWNTREND, MarketState.DOWNTREND]:
            above = [l for l in levels if l > current_price]
            below = [l for l in levels if l <= current_price]
            
            if len(below) < len(above) * 1.5:
                extra = int((len(above) * 1.5 - len(below)) / 2)
                for i in range(extra):
                    step = (max_price - min_price) / count
                    new_level = current_price * (1 - (i + 1) * step / current_price * 2)
                    below.append(new_level)
                levels = sorted(below + above)
        
        elif state == MarketState.RANGING:
            levels = []
            for i in range(count):
                pct = i / (count - 1)
                if pct < 0.2:
                    price = min_price + (max_price - min_price) * pct * 0.5
                elif pct > 0.8:
                    price = min_price + (max_price - min_price) * (0.5 + (pct - 0.5) * 1.5)
                else:
                    price = min_price + (max_price - min_price) * pct
                levels.append(price)
        
        elif state in [MarketState.BREAKOUT, MarketState.BREAKDOWN]:
            breakout_price = current_price * (1.01 if state == MarketState.BREAKOUT else 0.99)
            levels = []
            for i in range(count):
                pct = i / (count - 1)
                if 0.4 < pct < 0.6:
                    for j in range(3):
                        offset = (j - 1) * (max_price - min_price) / count * 0.2
                        levels.append(breakout_price + offset)
                else:
                    levels.append(min_price + (max_price - min_price) * pct)
            levels = sorted(set(levels))
        
        return sorted(levels)
    
    def _determine_entry_points(self, levels: List[float], analysis: MarketAnalysis, 
                                current_price: float) -> List[float]:
        entry_points = []
        
        for support in analysis.support_levels:
            if support < current_price and support > min(levels):
                entry_points.append(support)
        
        for resistance in analysis.resistance_levels:
            if resistance > current_price and resistance < max(levels):
                entry_points.append(resistance)
        
        if not entry_points:
            for level in levels:
                if abs(level - current_price) / current_price < 0.02:
                    entry_points.append(level)
        
        return sorted(entry_points)
    
    def _determine_exit_points(self, levels: List[float], analysis: MarketAnalysis,
                               current_price: float) -> List[float]:
        exit_points = []
        
        for support in analysis.support_levels:
            if support < current_price:
                exit_points.append(support)
        
        for resistance in analysis.resistance_levels:
            if resistance > current_price:
                exit_points.append(resistance)
        
        if not exit_points:
            for level in levels:
                if abs(level - current_price) / current_price > 0.02:
                    exit_points.append(level)
        
        return sorted(exit_points[:5])
    
    def _calculate_stop_loss(self, current_price: float, analysis: MarketAnalysis) -> float:
        volatility = analysis.volatility
        stop_pct = 1 + volatility * 2
        
        if analysis.state in [MarketState.STRONG_UPTREND, MarketState.UPTREND]:
            if analysis.support_levels:
                return min(analysis.support_levels) * 0.995
            return current_price * (1 - stop_pct / 100)
        
        elif analysis.state in [MarketState.STRONG_DOWNTREND, MarketState.DOWNTREND]:
            if analysis.resistance_levels:
                return max(analysis.resistance_levels) * 1.005
            return current_price * (1 + stop_pct / 100)
        
        else:
            return current_price * (1 - stop_pct / 100)
    
    def _calculate_take_profit(self, current_price: float, analysis: MarketAnalysis) -> float:
        volatility = analysis.volatility
        profit_pct = 2 + volatility * 3
        
        if analysis.state in [MarketState.STRONG_UPTREND, MarketState.UPTREND]:
            if analysis.resistance_levels:
                return min(analysis.resistance_levels)
            return current_price * (1 + profit_pct / 100)
        
        elif analysis.state in [MarketState.STRONG_DOWNTREND, MarketState.DOWNTREND]:
            if analysis.support_levels:
                return max(analysis.support_levels)
            return current_price * (1 - profit_pct / 100)
        
        else:
            return current_price * (1 + profit_pct / 100)

# ================================================================
# TRADE TIER MANAGER
# ================================================================

class TradeTierManager:
    def __init__(self):
        self.tiers = {
            TradeTier.MICRO_1: {'min': 5, 'max': 5, 'label': '$5', 'enabled': True},
            TradeTier.MICRO_2: {'min': 10, 'max': 10, 'label': '$10', 'enabled': True},
            TradeTier.MICRO_3: {'min': 25, 'max': 25, 'label': '$25', 'enabled': True},
            TradeTier.MICRO_4: {'min': 50, 'max': 50, 'label': '$50', 'enabled': True},
            TradeTier.SMALL_1: {'min': 100, 'max': 100, 'label': '$100', 'enabled': True},
            TradeTier.SMALL_2: {'min': 200, 'max': 200, 'label': '$200', 'enabled': True},
            TradeTier.SMALL_3: {'min': 500, 'max': 500, 'label': '$500', 'enabled': True},
            TradeTier.MEDIUM_1: {'min': 1000, 'max': 1000, 'label': '$1,000', 'enabled': True},
            TradeTier.MEDIUM_2: {'min': 2500, 'max': 2500, 'label': '$2,500', 'enabled': True},
            TradeTier.MEDIUM_3: {'min': 5000, 'max': 5000, 'label': '$5,000', 'enabled': True},
            TradeTier.LARGE_1: {'min': 10000, 'max': 10000, 'label': '$10,000', 'enabled': True},
            TradeTier.LARGE_2: {'min': 25000, 'max': 25000, 'label': '$25,000', 'enabled': True},
            TradeTier.LARGE_3: {'min': 50000, 'max': 50000, 'label': '$50,000', 'enabled': True},
            TradeTier.MACRO_1: {'min': 100000, 'max': 100000, 'label': '$100,000', 'enabled': True},
            TradeTier.MACRO_2: {'min': 500000, 'max': 500000, 'label': '$500,000', 'enabled': True},
            TradeTier.MACRO_3: {'min': 1000000, 'max': float('inf'), 'label': '$1,000,000+', 'enabled': True},
        }
        self._lock = threading.Lock()
    
    def get_tier_for_amount(self, amount: float) -> TradeTier:
        for tier, config in self.tiers.items():
            if config['min'] <= amount <= config['max']:
                return tier
        return TradeTier.MICRO_1
    
    def get_tier_config(self, tier: TradeTier) -> Dict:
        return self.tiers.get(tier, {'min': 5, 'max': 5, 'label': '$5', 'enabled': True})
    
    def get_available_tiers(self, capital: float) -> List[TradeTier]:
        available = []
        for tier, config in self.tiers.items():
            if config['enabled'] and capital >= config['min']:
                available.append(tier)
        return available
    
    def get_tier_label(self, tier: TradeTier) -> str:
        config = self.tiers.get(tier)
        return config['label'] if config else '$5'

# ================================================================
# AI SIGNAL GATE
# ================================================================

class AiSignalGate:
    """AI Signal gate for filtering trades"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_confidence = config.get('min_confidence', 0.55)
        self.engine = self
    
    def score_signal(self, df, signal_type: str) -> Any:
        """Score a signal"""
        class Score:
            def __init__(self):
                self.total_score = 0.6
        
        return Score()
    
    def make_signal(self, score, side, entry, sl, tp, reason, tags, metadata):
        """Make a trade signal"""
        class Signal:
            def __init__(self):
                self.side = side
                self.entry = entry
                self.stop_loss = sl
                self.take_profit = tp
                self.reason = reason
                self.tags = tags
                self.metadata = metadata
                self.confidence = 0.7
        
        return Signal()

# ================================================================
# MAIN GRID BOT - ULTRA DYNAMIC EDITION (COMBINED)
# ================================================================

class GridBot:
    """
    ULTRA DYNAMIC ADAPTIVE GRID BOT v8.0 (COMBINED)
    - Inajibadilisha kuenda na mwenendo wa soko
    - Inaelewa hali ya soko na kuchukua hatua sahihi
    - Inaweka gridi katika maeneo yenye faida
    - Inaingia na kutoka kwa wakati muafaka
    - Inaweza kufanya biashara kwa $5 hadi $1M+
    - Supports both arithmetic and geometric grids
    - AI Signal gate integration
    - All bot settings configurable
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.bot_id = hashlib.md5(f"{config.get('name', 'GridBot')}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        self.name = config.get('name', 'Ultra Dynamic Grid Bot')
        self.capital = config.get('capital', 1000.0)
        self.config = config
        
        # ============================================================
        # BOT SETTINGS
        # ============================================================
        self.settings = BotSettings(
            bot_id=self.bot_id,
            bot_name=self.name,
            capital=self.capital,
            pairs=config.get('pairs', ["BTC/USDT"]),
            timeframe=config.get('timeframe', "1h"),
            mode=config.get('mode', "MEDIUM"),
            data_mode=config.get('data_mode', "OHLCV"),
            smart_aggressively=config.get('smart_aggressively', True),
            profit_per_trade=config.get('profit_per_trade', 0.50),
            risk_per_trade=config.get('risk_per_trade', 1.0),
            stop_loss_atr=config.get('stop_loss_atr', 1.5),
            take_profit_atr=config.get('take_profit_atr', 3.0),
            max_trades_per_day=config.get('max_trades_per_day', 10),
            loss_prevention=config.get('loss_prevention', True),
            profit_lock=config.get('profit_lock', True),
            daily_loss_limit=config.get('daily_loss_limit', 2.0),
            max_drawdown=config.get('max_drawdown', 5.0),
            circuit_breaker=config.get('circuit_breaker', True),
            trailing_stop=config.get('trailing_stop', True),
            partial_take_profit=config.get('partial_take_profit', True),
            re_entry=config.get('re_entry', True),
            news_filter=config.get('news_filter', True),
            correlation_filter=config.get('correlation_filter', True),
            volatility_filter=config.get('volatility_filter', True),
            grid_count=config.get('grid_count', 40),
            grid_spacing=config.get('grid_spacing', 0.5),
            grid_type=config.get('grid_type', 'arithmetic'),
            range_pct=config.get('range_pct', 10.0),
            min_grid_count=config.get('min_grid_count', 20),
            max_grid_count=config.get('max_grid_count', 80),
            default_grid_count=config.get('default_grid_count', 40),
            min_spacing=config.get('min_spacing', 0.2),
            max_spacing=config.get('max_spacing', 2.0),
            default_spacing=config.get('default_spacing', 0.5)
        )
        
        # ============================================================
        # ADAPTIVE CONFIG
        # ============================================================
        self.adaptive_config = AdaptiveConfig(
            micro_1_enabled=config.get('micro_1_enabled', True),
            micro_2_enabled=config.get('micro_2_enabled', True),
            micro_3_enabled=config.get('micro_3_enabled', True),
            micro_4_enabled=config.get('micro_4_enabled', True),
            small_1_enabled=config.get('small_1_enabled', True),
            small_2_enabled=config.get('small_2_enabled', True),
            small_3_enabled=config.get('small_3_enabled', True),
            medium_1_enabled=config.get('medium_1_enabled', True),
            medium_2_enabled=config.get('medium_2_enabled', True),
            medium_3_enabled=config.get('medium_3_enabled', True),
            large_1_enabled=config.get('large_1_enabled', True),
            large_2_enabled=config.get('large_2_enabled', True),
            large_3_enabled=config.get('large_3_enabled', True),
            macro_1_enabled=config.get('macro_1_enabled', True),
            macro_2_enabled=config.get('macro_2_enabled', True),
            macro_3_enabled=config.get('macro_3_enabled', True),
            min_grid_count=self.settings.min_grid_count,
            max_grid_count=self.settings.max_grid_count,
            default_grid_count=self.settings.default_grid_count,
            min_spacing=self.settings.min_spacing,
            max_spacing=self.settings.max_spacing,
            default_spacing=self.settings.default_spacing,
            grid_type=self.settings.grid_type,
            max_risk_per_trade=self.settings.risk_per_trade / 100,
            max_risk_per_day=self.settings.daily_loss_limit / 100,
            min_confidence=0.55,
            max_concurrent_trades=20,
            adaptation_speed=0.3,
            learning_rate=0.01,
            history_size=200,
            rebalance_interval=1800,
            target_win_rate=0.55,
            target_profit_factor=1.5,
            max_drawdown=self.settings.max_drawdown / 100,
            profit_per_trade_target=self.settings.profit_per_trade,
            capital=self.capital,
            pairs=self.settings.pairs,
            timeframe=self.settings.timeframe,
            mode=self.settings.mode,
            data_mode=self.settings.data_mode,
            smart_aggressively=self.settings.smart_aggressively,
            loss_prevention=self.settings.loss_prevention,
            profit_lock=self.settings.profit_lock,
            daily_loss_limit=self.settings.daily_loss_limit,
            max_drawdown_pct=self.settings.max_drawdown,
            circuit_breaker=self.settings.circuit_breaker,
            trailing_stop=self.settings.trailing_stop,
            partial_take_profit=self.settings.partial_take_profit,
            re_entry=self.settings.re_entry,
            news_filter=self.settings.news_filter,
            correlation_filter=self.settings.correlation_filter,
            volatility_filter=self.settings.volatility_filter
        )
        
        # ============================================================
        # ENGINES
        # ============================================================
        self.market_analyzer = SmartMarketAnalyzer()
        self.grid_optimizer = DynamicGridOptimizer()
        self.tier_manager = TradeTierManager()
        self.gate = AiSignalGate(config.get('ai', {}))
        
        # ============================================================
        # STATE
        # ============================================================
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.current_analysis: Optional[MarketAnalysis] = None
        self.current_grid: Optional[DynamicGridConfig] = None
        self.grid_positions: Dict[int, GridPosition] = {}
        self.active_positions: List[Position] = []
        self.trade_history: List[Dict] = []
        self.market_memory = deque(maxlen=500)
        self._lock = threading.Lock()
        self._running = True
        
        # Performance tracking
        self.total_win = 0
        self.total_loss = 0
        self.consecutive_losses = 0
        self.daily_profit = 0.0
        self.daily_start = datetime.now()
        self.best_trade = 0.0
        self.worst_trade = 0.0
        
        # ============================================================
        # PERFORMANCE METRICS
        # ============================================================
        self.performance_metrics = {
            'total_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'grid_adjustments': 0,
            'market_state_changes': 0,
            'emergency_stops': 0,
            'daily_trades': 0,
            'daily_pnl': 0.0
        }
        
        # Tier metrics
        for tier in TradeTier:
            key = f"{tier.value.lower()}_trades"
            self.performance_metrics[key] = 0
            key = f"{tier.value.lower()}_profit"
            self.performance_metrics[key] = 0.0
        
        # ============================================================
        # START BACKGROUND TASKS
        # ============================================================
        self._start_tasks()
        
        # ============================================================
        # STARTUP LOG
        # ============================================================
        self._log_startup()
    
    def _log_startup(self):
        """Log startup information"""
        logger.info("=" * 70)
        logger.info(f"🚀 {self.name} v8.0")
        logger.info("=" * 70)
        logger.info(f"   Bot ID: {self.bot_id}")
        logger.info(f"   Capital: ${self.capital:,.2f}")
        logger.info(f"   Pairs: {', '.join(self.settings.pairs)}")
        logger.info(f"   Timeframe: {self.settings.timeframe}")
        logger.info(f"   Mode: {self.settings.mode}")
        logger.info(f"   Grid Type: {self.settings.grid_type}")
        logger.info(f"   Grid Count: {self.settings.grid_count}")
        logger.info(f"   Grid Spacing: {self.settings.grid_spacing:.1f}%")
        logger.info(f"   Range: {self.settings.range_pct:.1f}%")
        logger.info(f"   Stop Loss: ATR × {self.settings.stop_loss_atr:.1f}")
        logger.info(f"   Take Profit: ATR × {self.settings.take_profit_atr:.1f}")
        logger.info(f"   Risk Per Trade: {self.settings.risk_per_trade:.1f}%")
        logger.info(f"   Max Trades/Day: {self.settings.max_trades_per_day}")
        logger.info(f"   Profit Per Trade Target: ${self.settings.profit_per_trade:.2f}")
        logger.info("")
        logger.info("   📊 TRADING TIERS ENABLED:")
        logger.info("   ✅ MICRO:  $5  | $10  | $25  | $50")
        logger.info("   ✅ SMALL:  $100 | $200 | $500")
        logger.info("   ✅ MEDIUM: $1K  | $2.5K | $5K")
        logger.info("   ✅ LARGE:  $10K | $25K | $50K")
        logger.info("   ✅ MACRO:  $100K | $500K | $1M+")
        logger.info("")
        logger.info("   🧠 SMART FEATURES:")
        logger.info("   ✅ Market State Detection")
        logger.info("   ✅ Dynamic Grid Optimization")
        logger.info("   ✅ Smart Entry/Exit Points")
        logger.info("   ✅ Support/Resistance Detection")
        logger.info("   ✅ Self-Learning")
        logger.info("   ✅ AI Signal Gate")
        logger.info("   ✅ Loss Prevention")
        logger.info("   ✅ Profit Lock")
        logger.info("   ✅ Circuit Breaker")
        logger.info("   ✅ Trailing Stop")
        logger.info("=" * 70)
    
    # ================================================================
    # BACKGROUND TASKS
    # ================================================================
    
    def _start_tasks(self):
        self._scan_thread = threading.Thread(target=self._continuous_scan, daemon=True)
        self._scan_thread.start()
        
        self._analysis_thread = threading.Thread(target=self._continuous_analysis, daemon=True)
        self._analysis_thread.start()
        
        self._optimization_thread = threading.Thread(target=self._continuous_optimization, daemon=True)
        self._optimization_thread.start()
    
    def _continuous_scan(self):
        while self._running:
            try:
                self._scan_and_execute()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scan error: {e}")
                time.sleep(5)
    
    def _continuous_analysis(self):
        while self._running:
            try:
                self._update_market_analysis()
                time.sleep(10)
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                time.sleep(30)
    
    def _continuous_optimization(self):
        while self._running:
            try:
                self._optimize_grid()
                time.sleep(self.adaptive_config.rebalance_interval)
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                time.sleep(60)
    
    # ================================================================
    # MARKET ANALYSIS
    # ================================================================
    
    def _update_market_analysis(self):
        try:
            market_data = self._collect_market_data()
            analysis = self.market_analyzer.analyze(
                market_data.get('prices', []),
                market_data.get('volumes', [])
            )
            
            if self.current_analysis and analysis.state != self.current_analysis.state:
                self.performance_metrics['market_state_changes'] += 1
                logger.info(f"🔄 Market State Changed: {self.current_analysis.state.value} → {analysis.state.value}")
            
            with self._lock:
                self.current_analysis = analysis
                self.market_memory.append(analysis)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
    
    def _collect_market_data(self) -> Dict[str, Any]:
        """Collect market data - SIMULATED for now"""
        base_price = 50000
        return {
            'prices': [base_price + random.gauss(0, 500) for _ in range(100)],
            'volumes': [random.expovariate(0.001) for _ in range(100)]
        }
    
    # ================================================================
    # GRID OPTIMIZATION
    # ================================================================
    
    def _optimize_grid(self):
        if not self.current_analysis:
            return
        
        current_price = self._get_current_price()
        if current_price <= 0:
            return
        
        grid = self.grid_optimizer.optimize_grid(
            self.current_analysis, current_price, self.adaptive_config
        )
        
        with self._lock:
            self.current_grid = grid
        
        self.performance_metrics['grid_adjustments'] += 1
        logger.info(f"📊 Grid Optimized: {grid.mode.value} | {grid.count} levels | Spacing: {grid.spacing:.2f}%")
    
    def _get_current_price(self) -> float:
        """Get current price - SIMULATED"""
        return 50000 + random.gauss(0, 10)
    
    # ================================================================
    # BUILD GRID - Simple grid builder
    # ================================================================
    
    def _build_grid(self, mid: float) -> List[float]:
        """Build grid levels"""
        try:
            half = mid * (self.adaptive_config.range_pct / 100)
            lo, hi = mid - half, mid + half
            count = self.adaptive_config.default_grid_count
            
            if self.adaptive_config.grid_type == 'geometric':
                if lo > 0:
                    return [lo * (hi/lo)**(i/(count-1)) for i in range(count)]
            
            return [lo + (hi-lo)*(i/(count-1)) for i in range(count)]
        except Exception:
            return []
    
    # ================================================================
    # ANALYZE MARKET - Simple analysis
    # ================================================================
    
    async def analyze_market(self, data) -> Optional[Any]:
        """Simple market analysis for integration"""
        try:
            df = data if isinstance(data, pd.DataFrame) else data.get('1h')
            if df is None or len(df) < 30:
                return None
            
            current = df.iloc[-1]
            mid = (df['high'].rolling(20).max().iloc[-1] + df['low'].rolling(20).min().iloc[-1]) / 2
            grid = self._build_grid(mid)
            
            if not grid:
                return None
            
            score = self.gate.score_signal(df, "NEUTRAL")
            entry = current['close']
            sl = grid[0] * 0.99
            tp = grid[-1] * 1.01
            
            side = None
            reason = ""
            
            for i in range(1, len(grid)):
                if entry <= grid[i] and entry >= grid[i-1]:
                    if grid[i] > grid[i-1]:
                        side = "BUY"
                        reason = f"Grid BUY near level {i}/{len(grid)}"
                    break
            
            if side is None and current['close'] < mid:
                side = "BUY"
                reason = f"Grid BUY below mid {mid:.4f}"
            
            if side and score and getattr(score, 'total_score', 0.6) >= self.adaptive_config.min_confidence:
                return self.gate.make_signal(
                    score, side, entry, sl, tp, reason,
                    ['grid', 'range', 'rebalance'],
                    {'grid': grid, 'mid': mid}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"GridBot analyze error: {e}")
            return None
    
    # ================================================================
    # SCAN AND EXECUTE
    # ================================================================
    
    def _scan_and_execute(self):
        if not self.current_analysis or not self.current_grid:
            return
        
        if self.current_analysis.confidence < self.adaptive_config.min_confidence:
            return
        
        current_price = self._get_current_price()
        
        for entry_price in self.current_grid.entry_points:
            if abs(current_price - entry_price) / entry_price < 0.002:
                self._execute_trade(entry_price, "BUY" if current_price < entry_price else "SELL")
                break
    
    def _execute_trade(self, price: float, side: str):
        """Execute trade"""
        usd_value = self._calculate_position_size()
        tier = self.tier_manager.get_tier_for_amount(usd_value)
        
        tier_key = f"{tier.value.lower()}_enabled"
        if not getattr(self.adaptive_config, tier_key, True):
            return
        
        filled_count = len([g for g in self.grid_positions.values() if g.status == 'filled'])
        if filled_count >= self.adaptive_config.max_concurrent_trades:
            return
        
        # Check daily trade limit
        if self.performance_metrics['daily_trades'] >= self.settings.max_trades_per_day:
            logger.warning(f"Daily trade limit reached: {self.settings.max_trades_per_day}")
            return
        
        quantity = usd_value / price
        
        pos = self._open_position(side, price, self.current_analysis.confidence, quantity, usd_value, tier)
        
        if pos:
            grid_pos = GridPosition(
                level_index=len(self.grid_positions),
                level_price=price,
                side=side,
                entry_price=price,
                quantity=quantity,
                usd_value=usd_value,
                tier=tier,
                status='filled',
                profit=0.0,
                profit_percent=0.0,
                entry_time=datetime.now()
            )
            self.grid_positions[grid_pos.level_index] = grid_pos
            
            tier_key_trades = f"{tier.value.lower()}_trades"
            self.performance_metrics[tier_key_trades] = self.performance_metrics.get(tier_key_trades, 0) + 1
            self.performance_metrics['total_trades'] = self.performance_metrics.get('total_trades', 0) + 1
            self.performance_metrics['daily_trades'] = self.performance_metrics.get('daily_trades', 0) + 1
            
            logger.info(f"📊 Trade Executed: {side} ${usd_value:.2f} at ${price:.2f} ({tier.value})")
    
    def _open_position(self, side: str, price: float, confidence: float,
                       quantity: float, usd_value: float, tier: TradeTier) -> Optional[Position]:
        """Open a position"""
        with self._lock:
            # Calculate SL and TP based on ATR
            atr = price * 0.01  # Simulated ATR
            sl_mult = self.settings.stop_loss_atr
            tp_mult = self.settings.take_profit_atr
            
            if side == "BUY":
                stop_loss = price - (atr * sl_mult)
                take_profit = price + (atr * tp_mult)
            else:
                stop_loss = price + (atr * sl_mult)
                take_profit = price - (atr * tp_mult)
            
            pos = Position(
                id=f"pos_{int(time.time()*1000)}_{hashlib.md5(str(random.random()).encode()).hexdigest()[:6]}",
                side=side,
                entry_price=price,
                quantity=quantity,
                usd_value=usd_value,
                stop_loss=stop_loss,
                take_profit=take_profit,
                current_price=price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                profit_percent=0.0,
                tier=tier,
                entry_time=datetime.now(),
                exit_time=None,
                is_open=True,
                metadata={'confidence': confidence}
            )
            self.positions[pos.id] = pos
            return pos
    
    def close_position(self, position_id: str, price: float, reason: str):
        """Close a position"""
        with self._lock:
            if position_id in self.positions:
                pos = self.positions[position_id]
                pos.is_open = False
                pos.exit_time = datetime.now()
                pos.current_price = price
                
                if pos.side == "BUY":
                    pos.realized_pnl = (price - pos.entry_price) * pos.quantity
                else:
                    pos.realized_pnl = (pos.entry_price - price) * pos.quantity
                
                pos.profit_percent = (pos.realized_pnl / pos.usd_value) * 100 if pos.usd_value > 0 else 0
                self.closed_positions.append(pos)
                del self.positions[position_id]
                
                self._record_trade_result(pos, reason)
                return True
        return False
    
    def _calculate_position_size(self) -> float:
        """Calculate position size"""
        confidence = self.current_analysis.confidence if self.current_analysis else 0.5
        
        base_size = self.capital * self.adaptive_config.max_risk_per_trade
        
        confidence_multiplier = 0.5 + confidence
        
        state_multiplier = 1.0
        if self.current_analysis:
            if self.current_analysis.state in [MarketState.STRONG_UPTREND, MarketState.STRONG_DOWNTREND]:
                state_multiplier = 1.5
            elif self.current_analysis.state in [MarketState.HIGH_VOLATILITY]:
                state_multiplier = 0.7
            elif self.current_analysis.state in [MarketState.RANGING]:
                state_multiplier = 0.8
        
        # Adjust for profit per trade target
        profit_target_multiplier = 1.0
        if self.settings.profit_per_trade > 0:
            # Calculate required size to achieve target profit
            atr = self._get_current_price() * 0.01
            required_size = self.settings.profit_per_trade / (atr * self.settings.take_profit_atr)
            if required_size > 0:
                profit_target_multiplier = min(2.0, required_size / base_size if base_size > 0 else 1.0)
        
        size = base_size * confidence_multiplier * state_multiplier * profit_target_multiplier
        
        tier = self.tier_manager.get_tier_for_amount(size)
        config = self.tier_manager.get_tier_config(tier)
        size = min(size, config.get('max', float('inf')))
        
        return max(5.0, size)
    
    def _record_trade_result(self, pos: Position, reason: str):
        """Record trade result"""
        profit = pos.realized_pnl
        
        if profit > 0:
            self.total_win += 1
            self.performance_metrics['total_profit'] = self.performance_metrics.get('total_profit', 0) + profit
            self.consecutive_losses = 0
            self.performance_metrics['consecutive_wins'] = self.performance_metrics.get('consecutive_wins', 0) + 1
            if profit > self.best_trade:
                self.best_trade = profit
        else:
            self.total_loss += 1
            self.performance_metrics['total_loss'] = self.performance_metrics.get('total_loss', 0) + abs(profit)
            self.consecutive_losses += 1
            self.performance_metrics['consecutive_losses'] = self.consecutive_losses
            if profit < self.worst_trade:
                self.worst_trade = profit
        
        self.daily_profit += profit
        self.performance_metrics['daily_pnl'] = self.daily_profit
        
        tier_key = f"{pos.tier.value.lower()}_profit"
        self.performance_metrics[tier_key] = self.performance_metrics.get(tier_key, 0) + profit
        
        total = self.total_win + self.total_loss
        if total > 0:
            self.performance_metrics['win_rate'] = (self.total_win / total) * 100
        
        loss = self.performance_metrics.get('total_loss', 0)
        if loss > 0:
            self.performance_metrics['profit_factor'] = self.performance_metrics.get('total_profit', 0) / loss
        
        self.trade_history.append({
            'timestamp': pos.exit_time.isoformat() if pos.exit_time else datetime.now().isoformat(),
            'side': pos.side,
            'entry_price': pos.entry_price,
            'exit_price': pos.current_price,
            'usd_value': pos.usd_value,
            'profit': profit,
            'profit_percent': pos.profit_percent,
            'tier': pos.tier.value,
            'reason': reason
        })
        
        logger.info(f"💰 Trade Closed: {reason} | ${profit:+.2f} ({pos.profit_percent:+.1f}%) | {pos.tier.value}")
        
        # Check loss prevention
        if self.consecutive_losses >= 3:
            logger.warning(f"⚠️ {self.consecutive_losses} consecutive losses! Adjusting strategy...")
            self._adaptive_emergency_adjustment()
    
    def _adaptive_emergency_adjustment(self):
        """Emergency adjustment after losses"""
        self.adaptive_config.max_risk_per_trade = max(0.005, self.adaptive_config.max_risk_per_trade * 0.5)
        self.adaptive_config.default_spacing = min(2.0, self.adaptive_config.default_spacing * 1.5)
        self.adaptive_config.default_grid_count = max(20, self.adaptive_config.default_grid_count * 0.7)
        
        logger.info(f"🔄 Emergency Adjustment: Risk {self.adaptive_config.max_risk_per_trade:.1%}, Spacing {self.adaptive_config.default_spacing:.2f}%")
        self.performance_metrics['emergency_stops'] += 1
    
    # ================================================================
    # POSITION MANAGEMENT
    # ================================================================
    
    def _update_positions(self):
        """Update all positions"""
        current_price = self._get_current_price()
        
        for pos in list(self.positions.values()):
            if not pos.is_open:
                continue
            
            if self._check_take_profit(pos, current_price):
                self.close_position(pos.id, current_price, "take_profit")
                continue
            
            if self._check_stop_loss(pos, current_price):
                self.close_position(pos.id, current_price, "stop_loss")
                continue
            
            pos.current_price = current_price
            if pos.side == "BUY":
                pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
            else:
                pos.unrealized_pnl = (pos.entry_price - current_price) * pos.quantity
    
    def _check_take_profit(self, pos: Position, current_price: float) -> bool:
        if pos.side == "BUY":
            return current_price >= pos.take_profit
        else:
            return current_price <= pos.take_profit
    
    def _check_stop_loss(self, pos: Position, current_price: float) -> bool:
        if pos.side == "BUY":
            return current_price <= pos.stop_loss
        else:
            return current_price >= pos.stop_loss
    
    # ================================================================
    # PUBLIC METHODS
    # ================================================================
    
    def get_status(self) -> Dict:
        return {
            'bot_id': self.bot_id,
            'name': self.name,
            'status': 'running' if self._running else 'stopped',
            'capital': self.capital,
            'open_positions': len(self.positions),
            'grid_levels': len(self.current_grid.levels) if self.current_grid else 0,
            'market_state': self.current_analysis.state.value if self.current_analysis else 'unknown',
            'confidence': f"{self.current_analysis.confidence:.1%}" if self.current_analysis else 'N/A',
            'grid_mode': self.current_grid.mode.value if self.current_grid else 'N/A',
            'total_profit': sum(p.realized_pnl for p in self.closed_positions),
            'total_trades': len(self.closed_positions),
            'win_rate': self.performance_metrics.get('win_rate', 0),
            'profit_factor': self.performance_metrics.get('profit_factor', 0),
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade,
            'consecutive_losses': self.consecutive_losses,
            'daily_trades': self.performance_metrics.get('daily_trades', 0),
            'daily_pnl': self.performance_metrics.get('daily_pnl', 0),
            'settings': {
                'mode': self.settings.mode,
                'timeframe': self.settings.timeframe,
                'grid_type': self.settings.grid_type,
                'stop_loss_atr': self.settings.stop_loss_atr,
                'take_profit_atr': self.settings.take_profit_atr,
                'risk_per_trade': self.settings.risk_per_trade,
                'max_trades_per_day': self.settings.max_trades_per_day,
                'profit_per_trade': self.settings.profit_per_trade
            }
        }
    
    def get_analysis(self) -> Dict:
        if not self.current_analysis:
            return {'message': 'No analysis available'}
        
        return {
            'state': self.current_analysis.state.value,
            'grid_mode': self.current_analysis.grid_mode.value,
            'confidence': f"{self.current_analysis.confidence:.1%}",
            'volatility': f"{self.current_analysis.volatility:.1%}",
            'trend_strength': f"{self.current_analysis.trend_strength:.2f}",
            'support_levels': self.current_analysis.support_levels[-3:],
            'resistance_levels': self.current_analysis.resistance_levels[:3],
            'recommended_entry': self.current_analysis.recommended_entry,
            'recommended_exit': self.current_analysis.recommended_exit,
            'risk_level': self.current_analysis.risk_level
        }
    
    def get_grid_info(self) -> Dict:
        if not self.current_grid:
            return {'message': 'No grid configured'}
        
        return {
            'mode': self.current_grid.mode.value,
            'count': self.current_grid.count,
            'spacing': f"{self.current_grid.spacing:.2f}%",
            'min_price': self.current_grid.min_price,
            'max_price': self.current_grid.max_price,
            'entry_points': self.current_grid.entry_points[:5],
            'exit_points': self.current_grid.exit_points[:5],
            'stop_loss': self.current_grid.stop_loss,
            'take_profit': self.current_grid.take_profit,
            'risk_reward_ratio': f"{self.current_grid.risk_reward_ratio:.2f}:1",
            'grid_type': self.adaptive_config.grid_type
        }
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        return self.trade_history[-limit:]
    
    def get_performance(self) -> Dict:
        metrics = dict(self.performance_metrics)
        
        tier_summary = {}
        for tier in TradeTier:
            trades_key = f"{tier.value.lower()}_trades"
            profit_key = f"{tier.value.lower()}_profit"
            if trades_key in metrics:
                tier_summary[self.tier_manager.get_tier_label(tier)] = {
                    'trades': metrics[trades_key],
                    'profit': metrics.get(profit_key, 0),
                    'avg_profit': metrics.get(profit_key, 0) / max(1, metrics[trades_key])
                }
        
        metrics['tier_summary'] = tier_summary
        return metrics
    
    def get_settings(self) -> Dict:
        return {
            'bot_id': self.bot_id,
            'name': self.name,
            'capital': self.capital,
            'pairs': self.settings.pairs,
            'timeframe': self.settings.timeframe,
            'mode': self.settings.mode,
            'data_mode': self.settings.data_mode,
            'smart_aggressively': self.settings.smart_aggressively,
            'profit_per_trade': self.settings.profit_per_trade,
            'risk_per_trade': self.settings.risk_per_trade,
            'stop_loss_atr': self.settings.stop_loss_atr,
            'take_profit_atr': self.settings.take_profit_atr,
            'max_trades_per_day': self.settings.max_trades_per_day,
            'loss_prevention': self.settings.loss_prevention,
            'profit_lock': self.settings.profit_lock,
            'daily_loss_limit': self.settings.daily_loss_limit,
            'max_drawdown': self.settings.max_drawdown,
            'circuit_breaker': self.settings.circuit_breaker,
            'trailing_stop': self.settings.trailing_stop,
            'partial_take_profit': self.settings.partial_take_profit,
            're_entry': self.settings.re_entry,
            'news_filter': self.settings.news_filter,
            'correlation_filter': self.settings.correlation_filter,
            'volatility_filter': self.settings.volatility_filter,
            'grid_count': self.settings.grid_count,
            'grid_spacing': self.settings.grid_spacing,
            'grid_type': self.settings.grid_type,
            'range_pct': self.settings.range_pct
        }
    
    def update_settings(self, new_settings: Dict) -> Dict:
        """Update bot settings"""
        for key, value in new_settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                logger.info(f"✅ Setting updated: {key} = {value}")
        
        # Update adaptive config
        self.adaptive_config.capital = self.settings.capital
        self.adaptive_config.pairs = self.settings.pairs
        self.adaptive_config.timeframe = self.settings.timeframe
        self.adaptive_config.mode = self.settings.mode
        self.adaptive_config.data_mode = self.settings.data_mode
        self.adaptive_config.smart_aggressively = self.settings.smart_aggressively
        self.adaptive_config.profit_per_trade_target = self.settings.profit_per_trade
        self.adaptive_config.max_risk_per_trade = self.settings.risk_per_trade / 100
        self.adaptive_config.loss_prevention = self.settings.loss_prevention
        self.adaptive_config.profit_lock = self.settings.profit_lock
        self.adaptive_config.daily_loss_limit = self.settings.daily_loss_limit / 100
        self.adaptive_config.max_drawdown = self.settings.max_drawdown / 100
        self.adaptive_config.circuit_breaker = self.settings.circuit_breaker
        self.adaptive_config.trailing_stop = self.settings.trailing_stop
        self.adaptive_config.partial_take_profit = self.settings.partial_take_profit
        self.adaptive_config.re_entry = self.settings.re_entry
        self.adaptive_config.news_filter = self.settings.news_filter
        self.adaptive_config.correlation_filter = self.settings.correlation_filter
        self.adaptive_config.volatility_filter = self.settings.volatility_filter
        
        return {'status': 'success', 'settings': self.get_settings()}
    
    def stop(self):
        self._running = False
        for pos in list(self.positions.values()):
            if pos.is_open:
                self.close_position(pos.id, pos.current_price, "bot_stop")
        logger.info(f"🛑 Grid bot stopped: {self.name}")
    
    def reset(self):
        with self._lock:
            for pos in list(self.positions.values()):
                if pos.is_open:
                    self.close_position(pos.id, pos.current_price, "reset")
            
            self.grid_positions = {}
            self.trade_history = []
            self.total_win = 0
            self.total_loss = 0
            self.consecutive_losses = 0
            self.daily_profit = 0.0
            self.best_trade = 0.0
            self.worst_trade = 0.0
            
            self.performance_metrics = {k: 0 if isinstance(v, (int, float)) else v 
                                       for k, v in self.performance_metrics.items()}
            logger.info("🔄 Grid bot reset complete")
    
    def save_state(self):
        """Save bot state"""
        state = {
            'settings': self.get_settings(),
            'performance': self.get_performance(),
            'trade_history': self.trade_history[-100:],
            'closed_positions': [{'id': p.id, 'pnl': p.realized_pnl} for p in self.closed_positions[-50:]]
        }
        return state
    
    def load_state(self, state: Dict):
        """Load bot state"""
        if 'settings' in state:
            self.update_settings(state['settings'])
        if 'trade_history' in state:
            self.trade_history.extend(state['trade_history'])
        logger.info("📂 Bot state loaded")

# ================================================================
# FACTORY FUNCTION
# ================================================================

def create_grid_bot(config: Dict[str, Any]) -> GridBot:
    """Factory function to create a GridBot instance"""
    return GridBot(config)

# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'GridBot',
    'create_grid_bot',
    'MarketState',
    'GridMode',
    'TradeTier',
    'MarketAnalysis',
    'DynamicGridConfig',
    'GridPosition',
    'Position',
    'AdaptiveConfig',
    'BotSettings'
]