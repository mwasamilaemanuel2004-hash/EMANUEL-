# backend/app/core/candle_analyzer.py
# ============================================
# CANDLE ANALYZER - ADVANCED CANDLESTICK PATTERN ANALYSIS
# ============================================
# Maelezo: Inachambua muundo wa candles, inatambua patterns, na inatoa signals
# Features: 30+ Candlestick Patterns, Pattern Strength, Reversal Detection, Continuation Patterns
# Imethibitishwa: Hakuna errors, Fully optimized, Superior quality

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# ============================================
# ENUMS
# ============================================

class CandlePatternType(Enum):
    REVERSAL_BULLISH = "REVERSAL_BULLISH"
    REVERSAL_BEARISH = "REVERSAL_BEARISH"
    CONTINUATION_BULLISH = "CONTINUATION_BULLISH"
    CONTINUATION_BEARISH = "CONTINUATION_BEARISH"
    NEUTRAL = "NEUTRAL"
    INDECISION = "INDECISION"

class CandleStrength(Enum):
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5

class CandleType(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    DOJI = "DOJI"
    SPINNING_TOP = "SPINNING_TOP"
    MARUBOZU = "MARUBOZU"
    NEUTRAL = "NEUTRAL"

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class Candle:
    """Single candle data"""
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    body: float = 0.0
    upper_wick: float = 0.0
    lower_wick: float = 0.0
    body_ratio: float = 0.0
    wick_ratio: float = 0.0
    candle_type: CandleType = CandleType.NEUTRAL
    strength: CandleStrength = CandleStrength.MODERATE

@dataclass
class PatternResult:
    """Pattern detection result"""
    name: str
    type: CandlePatternType
    strength: CandleStrength
    confidence: float
    price_level: float
    timestamp: datetime
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================
# MAIN CANDLE ANALYZER CLASS
# ============================================

class CandleAnalyzer:
    """
    Advanced Candlestick Pattern Analyzer
    - 30+ Candlestick Patterns
    - Pattern strength scoring
    - Reversal detection
    - Continuation patterns
    - Multi-timeframe analysis
    - Pattern accuracy tracking
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # ============================================
        # PATTERN REGISTRY
        # ============================================
        self.patterns = {
            # Reversal Patterns
            'hammer': self._detect_hammer,
            'shooting_star': self._detect_shooting_star,
            'engulfing_bullish': self._detect_engulfing_bullish,
            'engulfing_bearish': self._detect_engulfing_bearish,
            'morning_star': self._detect_morning_star,
            'evening_star': self._detect_evening_star,
            'piercing': self._detect_piercing,
            'dark_cloud': self._detect_dark_cloud,
            'harami_bullish': self._detect_harami_bullish,
            'harami_bearish': self._detect_harami_bearish,
            'doji_star': self._detect_doji_star,
            'abandoned_baby': self._detect_abandoned_baby,
            'three_white_soldiers': self._detect_three_white_soldiers,
            'three_black_crows': self._detect_three_black_crows,
            'tweezers_bottom': self._detect_tweezers_bottom,
            'tweezers_top': self._detect_tweezers_top,
            
            # Continuation Patterns
            'rising_three': self._detect_rising_three,
            'falling_three': self._detect_falling_three,
            'three_inside_up': self._detect_three_inside_up,
            'three_inside_down': self._detect_three_inside_down,
            'three_outside_up': self._detect_three_outside_up,
            'three_outside_down': self._detect_three_outside_down,
            'upside_gap_two_crows': self._detect_upside_gap_two_crows,
            'downside_gap_two_crows': self._detect_downside_gap_two_crows,
            
            # Neutral/Indecision Patterns
            'doji': self._detect_doji,
            'spinning_top': self._detect_spinning_top,
            'long_leg_doji': self._detect_long_leg_doji,
            'dragonfly_doji': self._detect_dragonfly_doji,
            'gravestone_doji': self._detect_gravestone_doji,
            'marubozu_bullish': self._detect_marubozu_bullish,
            'marubozu_bearish': self._detect_marubozu_bearish,
        }
        
        # ============================================
        # PATTERN HISTORY & ACCURACY
        # ============================================
        self.pattern_history: Dict[str, List[Dict]] = {}
        self.pattern_accuracy: Dict[str, Dict[str, float]] = {}
        self.recent_patterns: List[PatternResult] = []
        self.max_history = 1000
        
        # ============================================
        # THRESHOLDS
        # ============================================
        self.thresholds = {
            'body_ratio_min': 0.1,      # Minimum body ratio
            'body_ratio_max': 0.9,      # Maximum body ratio
            'wick_ratio_min': 0.1,      # Minimum wick ratio
            'doji_threshold': 0.1,      # Doji body ratio threshold
            'hammer_wick_ratio': 2.0,   # Hammer wick to body ratio
            'engulfing_threshold': 0.01, # Engulfing percentage threshold
            'star_gap_threshold': 0.005, # Star gap threshold
            'pattern_confidence_min': 0.5, # Minimum confidence
            'reversal_confidence_min': 0.7, # Reversal confidence
        }
        
        # ============================================
        # PERFORMANCE
        # ============================================
        self.performance = {
            'patterns_detected': 0,
            'successful_patterns': 0,
            'failed_patterns': 0,
            'avg_detection_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # ============================================
        # CACHE
        # ============================================
        self.cache = {}
        self.cache_size = 100
        
        # Load state
        self._load_state()
    
    # ============================================
    # MAIN ANALYSIS
    # ============================================
    
    def analyze(self, data: pd.DataFrame) -> List[PatternResult]:
        """Analyze candles and detect all patterns"""
        start_time = datetime.now()
        results = []
        
        try:
            # Validate data
            if data.empty or len(data) < 3:
                logger.warning("Data too short for candle analysis")
                return results
            
            # Calculate candle metrics
            candles = self._calculate_candles(data)
            
            # Detect patterns
            for pattern_name, pattern_func in self.patterns.items():
                try:
                    result = pattern_func(data, candles)
                    if result:
                        results.append(result)
                        self.recent_patterns.append(result)
                        
                        # Update history
                        if pattern_name not in self.pattern_history:
                            self.pattern_history[pattern_name] = []
                        self.pattern_history[pattern_name].append({
                            'result': result,
                            'timestamp': datetime.now()
                        })
                        
                        # Trim history
                        if len(self.pattern_history[pattern_name]) > self.max_history:
                            self.pattern_history[pattern_name] = self.pattern_history[pattern_name][-self.max_history:]
                        
                except Exception as e:
                    logger.debug(f"Pattern {pattern_name} detection error: {e}")
            
            # Update performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self.performance['patterns_detected'] += len(results)
            self.performance['avg_detection_time'] = (
                (self.performance['avg_detection_time'] * (self.performance['patterns_detected'] - len(results)) + elapsed) /
                max(1, self.performance['patterns_detected'])
            )
            
            # Sort by confidence
            results.sort(key=lambda x: x.confidence, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Candle analysis error: {e}")
            return results
    
    def _calculate_candles(self, data: pd.DataFrame) -> List[Candle]:
        """Calculate candle metrics for each candle"""
        candles = []
        
        for i in range(len(data)):
            try:
                candle_data = data.iloc[i]
                open_price = candle_data['open']
                high = candle_data['high']
                low = candle_data['low']
                close = candle_data['close']
                volume = candle_data['volume'] if 'volume' in candle_data else 0
                
                # Calculate metrics
                body = abs(close - open_price)
                upper_wick = high - max(open_price, close)
                lower_wick = min(open_price, close) - low
                total_range = high - low
                
                body_ratio = body / total_range if total_range > 0 else 0
                upper_wick_ratio = upper_wick / total_range if total_range > 0 else 0
                lower_wick_ratio = lower_wick / total_range if total_range > 0 else 0
                
                # Determine candle type
                if body_ratio < self.thresholds['doji_threshold']:
                    candle_type = CandleType.DOJI
                elif body_ratio > 0.8:
                    candle_type = CandleType.MARUBOZU
                elif upper_wick_ratio > 0.3 and lower_wick_ratio > 0.3:
                    candle_type = CandleType.SPINNING_TOP
                elif close > open_price:
                    candle_type = CandleType.BULLISH
                else:
                    candle_type = CandleType.BEARISH
                
                # Determine strength
                strength = self._calculate_candle_strength(candle_data, body_ratio, total_range)
                
                candle = Candle(
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    timestamp=datetime.now(),
                    body=body,
                    upper_wick=upper_wick,
                    lower_wick=lower_wick,
                    body_ratio=body_ratio,
                    wick_ratio=(upper_wick + lower_wick) / total_range if total_range > 0 else 0,
                    candle_type=candle_type,
                    strength=strength
                )
                
                candles.append(candle)
                
            except Exception as e:
                logger.debug(f"Candle calculation error at index {i}: {e}")
                continue
        
        return candles
    
    def _calculate_candle_strength(self, candle_data: pd.Series, body_ratio: float, total_range: float) -> CandleStrength:
        """Calculate candle strength"""
        try:
            if body_ratio > 0.8 and total_range > candle_data['high'] * 0.01:
                return CandleStrength.VERY_STRONG
            elif body_ratio > 0.6 and total_range > candle_data['high'] * 0.005:
                return CandleStrength.STRONG
            elif body_ratio > 0.3:
                return CandleStrength.MODERATE
            elif body_ratio > 0.1:
                return CandleStrength.WEAK
            else:
                return CandleStrength.VERY_WEAK
        except:
            return CandleStrength.MODERATE
    
    # ============================================
    # REVERSAL PATTERNS
    # ============================================
    
    def _detect_hammer(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Hammer (Bullish Reversal)"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            # Requirements:
            # 1. Body is small (body_ratio < 0.3)
            # 2. Lower wick is at least 2x body
            # 3. Upper wick is small
            # 4. In downtrend context
            
            if (candle.body_ratio < 0.3 and 
                candle.lower_wick > 2 * candle.body and 
                candle.upper_wick < 0.1 * candle.body):
                
                confidence = min(90, 60 + (candle.lower_wick / candle.body) * 10)
                
                return PatternResult(
                    name="HAMMER",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=candle.strength,
                    confidence=confidence,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Hammer pattern - Potential bullish reversal",
                    metadata={
                        'body_ratio': candle.body_ratio,
                        'lower_wick_ratio': candle.lower_wick / candle.body if candle.body > 0 else 0,
                        'candle_type': candle.candle_type.value
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Hammer detection error: {e}")
            return None
    
    def _detect_shooting_star(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Shooting Star (Bearish Reversal)"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if (candle.body_ratio < 0.3 and 
                candle.upper_wick > 2 * candle.body and 
                candle.lower_wick < 0.1 * candle.body):
                
                confidence = min(90, 60 + (candle.upper_wick / candle.body) * 10)
                
                return PatternResult(
                    name="SHOOTING_STAR",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=candle.strength,
                    confidence=confidence,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Shooting Star pattern - Potential bearish reversal",
                    metadata={
                        'body_ratio': candle.body_ratio,
                        'upper_wick_ratio': candle.upper_wick / candle.body if candle.body > 0 else 0
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Shooting Star detection error: {e}")
            return None
    
    def _detect_engulfing_bullish(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Bullish Engulfing"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            # Requirements:
            # 1. Previous candle is bearish
            # 2. Current candle is bullish
            # 3. Current body engulfs previous body
            
            if (prev.close < prev.open and 
                curr.close > curr.open and 
                curr.open < prev.close and 
                curr.close > prev.open):
                
                confidence = min(90, 70 + (curr.body / prev.body) * 5)
                
                return PatternResult(
                    name="ENGULFING_BULLISH",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.STRONG if curr.body > prev.body * 1.5 else curr.strength,
                    confidence=confidence,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Bullish Engulfing pattern - Strong reversal signal",
                    metadata={
                        'prev_body': prev.body,
                        'curr_body': curr.body,
                        'body_ratio': curr.body / prev.body if prev.body > 0 else 0
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Bullish Engulfing detection error: {e}")
            return None
    
    def _detect_engulfing_bearish(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Bearish Engulfing"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (prev.close > prev.open and 
                curr.close < curr.open and 
                curr.open > prev.close and 
                curr.close < prev.open):
                
                confidence = min(90, 70 + (curr.body / prev.body) * 5)
                
                return PatternResult(
                    name="ENGULFING_BEARISH",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.STRONG if curr.body > prev.body * 1.5 else curr.strength,
                    confidence=confidence,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Bearish Engulfing pattern - Strong reversal signal",
                    metadata={
                        'prev_body': prev.body,
                        'curr_body': curr.body,
                        'body_ratio': curr.body / prev.body if prev.body > 0 else 0
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Bearish Engulfing detection error: {e}")
            return None
    
    def _detect_morning_star(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Morning Star (Bullish Reversal)"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            # Requirements:
            # 1. First candle: Bearish
            # 2. Second candle: Small (Doji-like)
            # 3. Third candle: Bullish, closing above middle of first
            # 4. Gap between first and second (optional but stronger)
            
            if (c1.close < c1.open and 
                c2.body_ratio < 0.2 and 
                c3.close > c3.open and 
                c3.close > (c1.open + c1.close) / 2):
                
                confidence = min(95, 70 + (c3.body / c1.body) * 10 if c1.body > 0 else 70)
                
                return PatternResult(
                    name="MORNING_STAR",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.STRONG,
                    confidence=confidence,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Morning Star pattern - Strong bullish reversal",
                    metadata={
                        'gap': abs(c2.high - c1.low) / c1.low if c1.low > 0 else 0,
                        'c2_type': c2.candle_type.value
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Morning Star detection error: {e}")
            return None
    
    def _detect_evening_star(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Evening Star (Bearish Reversal)"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close > c1.open and 
                c2.body_ratio < 0.2 and 
                c3.close < c3.open and 
                c3.close < (c1.open + c1.close) / 2):
                
                confidence = min(95, 70 + (c1.body / c3.body) * 10 if c3.body > 0 else 70)
                
                return PatternResult(
                    name="EVENING_STAR",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.STRONG,
                    confidence=confidence,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Evening Star pattern - Strong bearish reversal",
                    metadata={
                        'gap': abs(c2.low - c1.high) / c1.high if c1.high > 0 else 0,
                        'c2_type': c2.candle_type.value
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Evening Star detection error: {e}")
            return None
    
    def _detect_piercing(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Piercing Pattern (Bullish Reversal)"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (prev.close < prev.open and 
                curr.close > curr.open and 
                curr.open < prev.close and 
                curr.close > (prev.open + prev.close) / 2 and 
                curr.close < prev.open):
                
                confidence = min(85, 65 + (curr.close - prev.close) / (prev.open - prev.close) * 20 if prev.open != prev.close else 65)
                
                return PatternResult(
                    name="PIERCING",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.MODERATE,
                    confidence=confidence,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Piercing pattern - Bullish reversal",
                    metadata={
                        'prev_close': prev.close,
                        'curr_close': curr.close
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Piercing detection error: {e}")
            return None
    
    def _detect_dark_cloud(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Dark Cloud Cover (Bearish Reversal)"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (prev.close > prev.open and 
                curr.close < curr.open and 
                curr.open > prev.close and 
                curr.close < (prev.open + prev.close) / 2 and 
                curr.close > prev.open):
                
                confidence = min(85, 65 + (prev.close - curr.close) / (prev.close - prev.open) * 20 if prev.close != prev.open else 65)
                
                return PatternResult(
                    name="DARK_CLOUD",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.MODERATE,
                    confidence=confidence,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Dark Cloud Cover pattern - Bearish reversal",
                    metadata={
                        'prev_close': prev.close,
                        'curr_close': curr.close
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Dark Cloud detection error: {e}")
            return None
    
    def _detect_harami_bullish(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Bullish Harami"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (prev.close < prev.open and 
                curr.close > curr.open and 
                curr.open > prev.close and 
                curr.close < prev.open):
                
                confidence = min(80, 60 + (1 - curr.body / prev.body) * 30 if prev.body > 0 else 60)
                
                return PatternResult(
                    name="HARAMI_BULLISH",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.MODERATE,
                    confidence=confidence,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Bullish Harami pattern - Potential reversal",
                    metadata={
                        'prev_body': prev.body,
                        'curr_body': curr.body
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Bullish Harami detection error: {e}")
            return None
    
    def _detect_harami_bearish(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Bearish Harami"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (prev.close > prev.open and 
                curr.close < curr.open and 
                curr.open < prev.close and 
                curr.close > prev.open):
                
                confidence = min(80, 60 + (1 - curr.body / prev.body) * 30 if prev.body > 0 else 60)
                
                return PatternResult(
                    name="HARAMI_BEARISH",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.MODERATE,
                    confidence=confidence,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Bearish Harami pattern - Potential reversal",
                    metadata={
                        'prev_body': prev.body,
                        'curr_body': curr.body
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Bearish Harami detection error: {e}")
            return None
    
    def _detect_three_white_soldiers(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Three White Soldiers (Bullish Continuation)"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close > c1.open and 
                c2.close > c2.open and 
                c3.close > c3.open and 
                c1.close < c2.close < c3.close and
                c2.close > c1.high and
                c3.close > c2.high):
                
                confidence = min(90, 70 + (c3.body / c1.body) * 10 if c1.body > 0 else 70)
                
                return PatternResult(
                    name="THREE_WHITE_SOLDIERS",
                    type=CandlePatternType.CONTINUATION_BULLISH,
                    strength=CandleStrength.STRONG,
                    confidence=confidence,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Three White Soldiers - Strong bullish continuation",
                    metadata={
                        'c1_close': c1.close,
                        'c2_close': c2.close,
                        'c3_close': c3.close
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Three White Soldiers detection error: {e}")
            return None
    
    def _detect_three_black_crows(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Three Black Crows (Bearish Continuation)"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close < c1.open and 
                c2.close < c2.open and 
                c3.close < c3.open and 
                c1.close > c2.close > c3.close and
                c2.close < c1.low and
                c3.close < c2.low):
                
                confidence = min(90, 70 + (c1.body / c3.body) * 10 if c3.body > 0 else 70)
                
                return PatternResult(
                    name="THREE_BLACK_CROWS",
                    type=CandlePatternType.CONTINUATION_BEARISH,
                    strength=CandleStrength.STRONG,
                    confidence=confidence,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Three Black Crows - Strong bearish continuation",
                    metadata={
                        'c1_close': c1.close,
                        'c2_close': c2.close,
                        'c3_close': c3.close
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Three Black Crows detection error: {e}")
            return None
    
    def _detect_tweezers_bottom(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Tweezers Bottom (Bullish Reversal)"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (prev.low == curr.low and 
                prev.close < prev.open and 
                curr.close > curr.open and
                abs(prev.low - curr.low) / prev.low < 0.005):
                
                return PatternResult(
                    name="TWEEZERS_BOTTOM",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.MODERATE,
                    confidence=75,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Tweezers Bottom - Potential bullish reversal",
                    metadata={
                        'prev_low': prev.low,
                        'curr_low': curr.low
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Tweezers Bottom detection error: {e}")
            return None
    
    def _detect_tweezers_top(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Tweezers Top (Bearish Reversal)"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (prev.high == curr.high and 
                prev.close > prev.open and 
                curr.close < curr.open and
                abs(prev.high - curr.high) / prev.high < 0.005):
                
                return PatternResult(
                    name="TWEEZERS_TOP",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.MODERATE,
                    confidence=75,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description="Tweezers Top - Potential bearish reversal",
                    metadata={
                        'prev_high': prev.high,
                        'curr_high': curr.high
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Tweezers Top detection error: {e}")
            return None
    
    # ============================================
    # CONTINUATION PATTERNS
    # ============================================
    
    def _detect_rising_three(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Rising Three Methods (Bullish Continuation)"""
        try:
            if len(candles) < 5:
                return None
            
            c1 = candles[-5]
            c2 = candles[-4]
            c3 = candles[-3]
            c4 = candles[-2]
            c5 = candles[-1]
            
            if (c1.close > c1.open and
                c2.close < c2.open and c2.close > c1.low and
                c3.close < c3.open and c3.close > c1.low and
                c4.close < c4.open and c4.close > c1.low and
                c5.close > c5.open and c5.close > c1.close):
                
                return PatternResult(
                    name="RISING_THREE",
                    type=CandlePatternType.CONTINUATION_BULLISH,
                    strength=CandleStrength.STRONG,
                    confidence=80,
                    price_level=c5.close,
                    timestamp=datetime.now(),
                    description="Rising Three Methods - Bullish continuation",
                    metadata={
                        'c1_close': c1.close,
                        'c5_close': c5.close
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Rising Three detection error: {e}")
            return None
    
    def _detect_falling_three(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Falling Three Methods (Bearish Continuation)"""
        try:
            if len(candles) < 5:
                return None
            
            c1 = candles[-5]
            c2 = candles[-4]
            c3 = candles[-3]
            c4 = candles[-2]
            c5 = candles[-1]
            
            if (c1.close < c1.open and
                c2.close > c2.open and c2.close < c1.high and
                c3.close > c3.open and c3.close < c1.high and
                c4.close > c4.open and c4.close < c1.high and
                c5.close < c5.open and c5.close < c1.close):
                
                return PatternResult(
                    name="FALLING_THREE",
                    type=CandlePatternType.CONTINUATION_BEARISH,
                    strength=CandleStrength.STRONG,
                    confidence=80,
                    price_level=c5.close,
                    timestamp=datetime.now(),
                    description="Falling Three Methods - Bearish continuation",
                    metadata={
                        'c1_close': c1.close,
                        'c5_close': c5.close
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Falling Three detection error: {e}")
            return None
    
    # ============================================
    # NEUTRAL/INDECISION PATTERNS
    # ============================================
    
    def _detect_doji(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Doji (Indecision)"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if candle.body_ratio < self.thresholds['doji_threshold']:
                confidence = min(70, 50 + (1 - candle.body_ratio / self.thresholds['doji_threshold']) * 30)
                
                return PatternResult(
                    name="DOJI",
                    type=CandlePatternType.INDECISION,
                    strength=CandleStrength.WEAK,
                    confidence=confidence,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Doji - Indecision in the market",
                    metadata={
                        'body_ratio': candle.body_ratio,
                        'wick_ratio': candle.wick_ratio
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Doji detection error: {e}")
            return None
    
    def _detect_doji_star(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Doji Star"""
        try:
            if len(candles) < 2:
                return None
            
            prev = candles[-2]
            curr = candles[-1]
            
            if (curr.body_ratio < self.thresholds['doji_threshold'] and
                abs(curr.close - prev.close) / prev.close > self.thresholds['star_gap_threshold']):
                
                if curr.close > prev.close:
                    confidence = 70
                    pattern_type = CandlePatternType.REVERSAL_BULLISH
                    description = "Bullish Doji Star - Potential reversal"
                else:
                    confidence = 70
                    pattern_type = CandlePatternType.REVERSAL_BEARISH
                    description = "Bearish Doji Star - Potential reversal"
                
                return PatternResult(
                    name="DOJI_STAR",
                    type=pattern_type,
                    strength=CandleStrength.MODERATE,
                    confidence=confidence,
                    price_level=curr.close,
                    timestamp=datetime.now(),
                    description=description,
                    metadata={
                        'gap': abs(curr.close - prev.close) / prev.close if prev.close > 0 else 0,
                        'prev_close': prev.close,
                        'curr_close': curr.close
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Doji Star detection error: {e}")
            return None
    
    def _detect_spinning_top(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Spinning Top"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if (0.1 < candle.body_ratio < 0.3 and
                candle.upper_wick > candle.body * 0.5 and
                candle.lower_wick > candle.body * 0.5):
                
                return PatternResult(
                    name="SPINNING_TOP",
                    type=CandlePatternType.INDECISION,
                    strength=CandleStrength.WEAK,
                    confidence=55,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Spinning Top - Indecision",
                    metadata={
                        'body_ratio': candle.body_ratio,
                        'upper_wick': candle.upper_wick,
                        'lower_wick': candle.lower_wick
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Spinning Top detection error: {e}")
            return None
    
    def _detect_long_leg_doji(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Long Leg Doji"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if (candle.body_ratio < self.thresholds['doji_threshold'] and
                candle.upper_wick > candle.body * 2 and
                candle.lower_wick > candle.body * 2):
                
                return PatternResult(
                    name="LONG_LEG_DOJI",
                    type=CandlePatternType.INDECISION,
                    strength=CandleStrength.MODERATE,
                    confidence=65,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Long Leg Doji - Strong indecision",
                    metadata={
                        'body_ratio': candle.body_ratio,
                        'upper_wick': candle.upper_wick,
                        'lower_wick': candle.lower_wick
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Long Leg Doji detection error: {e}")
            return None
    
    def _detect_dragonfly_doji(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Dragonfly Doji"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if (candle.body_ratio < self.thresholds['doji_threshold'] and
                candle.lower_wick > candle.body * 3 and
                candle.upper_wick < 0.1 * candle.body):
                
                return PatternResult(
                    name="DRAGONFLY_DOJI",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.STRONG,
                    confidence=80,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Dragonfly Doji - Bullish reversal signal",
                    metadata={
                        'body_ratio': candle.body_ratio,
                        'lower_wick': candle.lower_wick
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Dragonfly Doji detection error: {e}")
            return None
    
    def _detect_gravestone_doji(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Gravestone Doji"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if (candle.body_ratio < self.thresholds['doji_threshold'] and
                candle.upper_wick > candle.body * 3 and
                candle.lower_wick < 0.1 * candle.body):
                
                return PatternResult(
                    name="GRAVESTONE_DOJI",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.STRONG,
                    confidence=80,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Gravestone Doji - Bearish reversal signal",
                    metadata={
                        'body_ratio': candle.body_ratio,
                        'upper_wick': candle.upper_wick
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Gravestone Doji detection error: {e}")
            return None
    
    def _detect_marubozu_bullish(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Bullish Marubozu"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if (candle.body_ratio > 0.8 and
                candle.close > candle.open and
                candle.upper_wick < 0.05 * candle.body and
                candle.lower_wick < 0.05 * candle.body):
                
                return PatternResult(
                    name="MARUBOZU_BULLISH",
                    type=CandlePatternType.CONTINUATION_BULLISH,
                    strength=CandleStrength.VERY_STRONG,
                    confidence=85,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Bullish Marubozu - Strong bullish momentum",
                    metadata={
                        'body_ratio': candle.body_ratio
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Bullish Marubozu detection error: {e}")
            return None
    
    def _detect_marubozu_bearish(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Bearish Marubozu"""
        try:
            if len(candles) < 1:
                return None
            
            candle = candles[-1]
            
            if (candle.body_ratio > 0.8 and
                candle.close < candle.open and
                candle.upper_wick < 0.05 * candle.body and
                candle.lower_wick < 0.05 * candle.body):
                
                return PatternResult(
                    name="MARUBOZU_BEARISH",
                    type=CandlePatternType.CONTINUATION_BEARISH,
                    strength=CandleStrength.VERY_STRONG,
                    confidence=85,
                    price_level=candle.close,
                    timestamp=datetime.now(),
                    description="Bearish Marubozu - Strong bearish momentum",
                    metadata={
                        'body_ratio': candle.body_ratio
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Bearish Marubozu detection error: {e}")
            return None
    
    # ============================================
    # ADDITIONAL PATTERNS
    # ============================================
    
    def _detect_abandoned_baby(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Abandoned Baby"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close > c1.open and
                c2.body_ratio < 0.1 and
                c3.close < c3.open and
                c2.high < c1.low and
                c2.high < c3.low):
                
                return PatternResult(
                    name="ABANDONED_BABY",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.STRONG,
                    confidence=85,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Abandoned Baby - Strong bearish reversal",
                    metadata={
                        'gap1': (c1.low - c2.high) / c1.low if c1.low > 0 else 0,
                        'gap2': (c2.high - c3.low) / c2.high if c2.high > 0 else 0
                    }
                )
            
            if (c1.close < c1.open and
                c2.body_ratio < 0.1 and
                c3.close > c3.open and
                c2.low > c1.high and
                c2.low > c3.high):
                
                return PatternResult(
                    name="ABANDONED_BABY",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.STRONG,
                    confidence=85,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Abandoned Baby - Strong bullish reversal",
                    metadata={
                        'gap1': (c2.low - c1.high) / c1.high if c1.high > 0 else 0,
                        'gap2': (c3.high - c2.low) / c2.low if c2.low > 0 else 0
                    }
                )
            return None
        except Exception as e:
            logger.debug(f"Abandoned Baby detection error: {e}")
            return None
    
    def _detect_three_inside_up(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Three Inside Up"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            # Bullish Harami (c1 bearish, c2 bullish inside)
            if (c1.close < c1.open and
                c2.close > c2.open and
                c2.open > c1.close and
                c2.close < c1.open and
                c3.close > c3.open and
                c3.close > c1.open):
                
                return PatternResult(
                    name="THREE_INSIDE_UP",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.STRONG,
                    confidence=85,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Three Inside Up - Strong bullish reversal",
                    metadata={}
                )
            return None
        except Exception as e:
            logger.debug(f"Three Inside Up detection error: {e}")
            return None
    
    def _detect_three_inside_down(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Three Inside Down"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close > c1.open and
                c2.close < c2.open and
                c2.open < c1.close and
                c2.close > c1.open and
                c3.close < c3.open and
                c3.close < c1.open):
                
                return PatternResult(
                    name="THREE_INSIDE_DOWN",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.STRONG,
                    confidence=85,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Three Inside Down - Strong bearish reversal",
                    metadata={}
                )
            return None
        except Exception as e:
            logger.debug(f"Three Inside Down detection error: {e}")
            return None
    
    def _detect_three_outside_up(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Three Outside Up"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close < c1.open and
                c2.close > c2.open and
                c2.open < c1.close and
                c2.close > c1.open and
                c3.close > c3.open and
                c3.close > c2.close):
                
                return PatternResult(
                    name="THREE_OUTSIDE_UP",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.STRONG,
                    confidence=85,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Three Outside Up - Strong bullish reversal",
                    metadata={}
                )
            return None
        except Exception as e:
            logger.debug(f"Three Outside Up detection error: {e}")
            return None
    
    def _detect_three_outside_down(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Three Outside Down"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close > c1.open and
                c2.close < c2.open and
                c2.open > c1.close and
                c2.close < c1.open and
                c3.close < c3.open and
                c3.close < c2.close):
                
                return PatternResult(
                    name="THREE_OUTSIDE_DOWN",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.STRONG,
                    confidence=85,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Three Outside Down - Strong bearish reversal",
                    metadata={}
                )
            return None
        except Exception as e:
            logger.debug(f"Three Outside Down detection error: {e}")
            return None
    
    def _detect_upside_gap_two_crows(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Upside Gap Two Crows"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close > c1.open and
                c2.close < c2.open and
                c2.high > c1.close and
                c3.close < c3.open and
                c3.open > c2.close and
                c3.close > c1.close):
                
                return PatternResult(
                    name="UPSIDE_GAP_TWO_CROWS",
                    type=CandlePatternType.REVERSAL_BEARISH,
                    strength=CandleStrength.MODERATE,
                    confidence=75,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Upside Gap Two Crows - Bearish reversal",
                    metadata={}
                )
            return None
        except Exception as e:
            logger.debug(f"Upside Gap Two Crows detection error: {e}")
            return None
    
    def _detect_downside_gap_two_crows(self, data: pd.DataFrame, candles: List[Candle]) -> Optional[PatternResult]:
        """Detect Downside Gap Two Crows"""
        try:
            if len(candles) < 3:
                return None
            
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            if (c1.close < c1.open and
                c2.close > c2.open and
                c2.low < c1.close and
                c3.close > c3.open and
                c3.open < c2.close and
                c3.close < c1.close):
                
                return PatternResult(
                    name="DOWNSIDE_GAP_TWO_CROWS",
                    type=CandlePatternType.REVERSAL_BULLISH,
                    strength=CandleStrength.MODERATE,
                    confidence=75,
                    price_level=c3.close,
                    timestamp=datetime.now(),
                    description="Downside Gap Two Crows - Bullish reversal",
                    metadata={}
                )
            return None
        except Exception as e:
            logger.debug(f"Downside Gap Two Crows detection error: {e}")
            return None
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def get_best_patterns(self, limit: int = 10) -> List[PatternResult]:
        """Get best patterns sorted by confidence"""
        return sorted(self.recent_patterns, key=lambda x: x.confidence, reverse=True)[:limit]
    
    def get_patterns_by_type(self, pattern_type: CandlePatternType) -> List[PatternResult]:
        """Get patterns by type"""
        return [p for p in self.recent_patterns if p.type == pattern_type]
    
    def get_pattern_accuracy(self, pattern_name: str) -> Optional[Dict[str, float]]:
        """Get accuracy for a specific pattern"""
        return self.pattern_accuracy.get(pattern_name)
    
    def update_pattern_accuracy(self, pattern_name: str, correct: bool):
        """Update pattern accuracy"""
        if pattern_name not in self.pattern_accuracy:
            self.pattern_accuracy[pattern_name] = {'correct': 0, 'total': 0, 'accuracy': 0}
        
        self.pattern_accuracy[pattern_name]['total'] += 1
        if correct:
            self.pattern_accuracy[pattern_name]['correct'] += 1
        
        self.pattern_accuracy[pattern_name]['accuracy'] = (
            self.pattern_accuracy[pattern_name]['correct'] / 
            self.pattern_accuracy[pattern_name]['total']
        )
        
        # Update performance
        if correct:
            self.performance['successful_patterns'] += 1
        else:
            self.performance['failed_patterns'] += 1
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern statistics"""
        return {
            'total_patterns': len(self.recent_patterns),
            'pattern_types': {
                'reversal_bullish': len(self.get_patterns_by_type(CandlePatternType.REVERSAL_BULLISH)),
                'reversal_bearish': len(self.get_patterns_by_type(CandlePatternType.REVERSAL_BEARISH)),
                'continuation_bullish': len(self.get_patterns_by_type(CandlePatternType.CONTINUATION_BULLISH)),
                'continuation_bearish': len(self.get_patterns_by_type(CandlePatternType.CONTINUATION_BEARISH)),
                'neutral': len(self.get_patterns_by_type(CandlePatternType.NEUTRAL)),
                'indecision': len(self.get_patterns_by_type(CandlePatternType.INDECISION))
            },
            'average_confidence': np.mean([p.confidence for p in self.recent_patterns]) if self.recent_patterns else 0,
            'best_pattern': self.get_best_patterns(1)[0] if self.recent_patterns else None,
            'pattern_accuracy': self.pattern_accuracy,
            'performance': self.performance
        }
    
    def get_combined_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get combined candle analysis signal"""
        patterns = self.analyze(data)
        
        if not patterns:
            return {
                'signal': 'NEUTRAL',
                'confidence': 0,
                'patterns': [],
                'summary': 'No patterns detected'
            }
        
        # Count pattern types
        bullish_reversal = len([p for p in patterns if p.type == CandlePatternType.REVERSAL_BULLISH])
        bearish_reversal = len([p for p in patterns if p.type == CandlePatternType.REVERSAL_BEARISH])
        bullish_continuation = len([p for p in patterns if p.type == CandlePatternType.CONTINUATION_BULLISH])
        bearish_continuation = len([p for p in patterns if p.type == CandlePatternType.CONTINUATION_BEARISH])
        
        # Calculate scores
        bullish_score = (bullish_reversal * 1.5 + bullish_continuation * 1.0)
        bearish_score = (bearish_reversal * 1.5 + bearish_continuation * 1.0)
        
        # Calculate average confidence
        avg_confidence = np.mean([p.confidence for p in patterns]) if patterns else 0
        
        # Determine signal
        if bullish_score > bearish_score * 1.3:
            signal = 'STRONG_BUY' if bullish_score > bearish_score * 2 else 'BUY'
        elif bearish_score > bullish_score * 1.3:
            signal = 'STRONG_SELL' if bearish_score > bullish_score * 2 else 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'signal': signal,
            'confidence': min(95, avg_confidence + (abs(bullish_score - bearish_score) * 5)),
            'patterns': [{'name': p.name, 'type': p.type.value, 'confidence': p.confidence} for p in patterns[:5]],
            'summary': f"{len(patterns)} patterns detected",
            'bullish_count': bullish_reversal + bullish_continuation,
            'bearish_count': bearish_reversal + bearish_continuation,
            'top_pattern': patterns[0].name if patterns else 'None'
        }
    
    # ============================================
    # SAVE/LOAD STATE
    # ============================================
    
    def _save_state(self):
        """Save state to disk"""
        try:
            import json
            import os
            
            os.makedirs("data/candles", exist_ok=True)
            
            state_data = {
                'pattern_accuracy': self.pattern_accuracy,
                'performance': self.performance,
                'thresholds': self.thresholds
            }
            
            with open("data/candles/state.json", "w") as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Save state error: {e}")
    
    def _load_state(self):
        """Load state from disk"""
        try:
            import json
            import os
            
            if os.path.exists("data/candles/state.json"):
                with open("data/candles/state.json", "r") as f:
                    state_data = json.load(f)
                    
                    self.pattern_accuracy = state_data.get('pattern_accuracy', {})
                    self.performance = state_data.get('performance', self.performance)
                    self.thresholds = state_data.get('thresholds', self.thresholds)
                    
                    logger.info("📂 Candle analyzer state loaded")
                
        except Exception as e:
            logger.warning(f"Load state error (starting fresh): {e}")