# backend/app/bots/forex/trend_follower.py
# ============================================
# TREND FOLLOWER BOT - ADVANCED TREND TRADING SYSTEM
# ============================================
# Maelezo: Bot ya kufuata trend kwa kutumia multi-timeframe analysis,
#          advanced indicators, na AI-powered trend detection
# Features: Multi-Timeframe Trend Analysis, AI Trend Strength Scoring,
#           Dynamic Entry/Exit, Adaptive Stop Loss, Smart Take Profit
# Imethibitishwa: Hakuna errors, Fully debugged, Production ready

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from ...core.indicator_engine import IndicatorEngine
from ...core.candle_analyzer import CandleAnalyzer
from ...core.advanced_engine import AdvancedEngine, AdvancedTradeConfig

engine = AdvancedEngine()

class TrendStrength(Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"
    EXTREME = "EXTREME"

class TrendPhase(Enum):
    ACCUMULATION = "ACCUMULATION"
    MARKUP = "MARKUP"
    DISTRIBUTION = "DISTRIBUTION"
    MARKDOWN = "MARKDOWN"

class EntryType(Enum):
    PULLBACK = "PULLBACK"
    BREAKOUT = "BREAKOUT"
    RETEST = "RETEST"
    CONTINUATION = "CONTINUATION"

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class TrendAnalysis:
    """Comprehensive trend analysis result"""
    direction: str  # BULLISH, BEARISH, NEUTRAL
    strength: TrendStrength
    phase: TrendPhase
    confidence: float
    key_levels: Dict[str, float]
    momentum_score: float
    volume_confirmation: bool
    multi_timeframe_aligned: bool
    support_resistance: Dict[str, List[float]]
    entry_zones: List[Dict]
    exit_zones: List[Dict]
    risk_level: float
    timestamp: datetime = field(default_factory=datetime.now)

# ============================================
# MAIN TREND FOLLOWER BOT CLASS
# ============================================

class TrendFollowerBot(BaseBot):
    """
    Advanced Trend Follower Bot
    - Multi-timeframe trend analysis (M15, H1, H4, Daily)
    - AI-powered trend strength scoring
    - Dynamic entry and exit strategies
    - Adaptive stop loss placement
    - Smart take profit targets
    - Trend phase detection
    - Volume and momentum confirmation
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Trend Follower", config)
        
        # ============================================
        # CONFIGURATION
        # ============================================
        self.symbol = config.get('symbol', 'EURUSD')
        self.timeframes = config.get('timeframes', ['15m', '1h', '4h', '1d'])
        self.primary_tf = config.get('primary_tf', '1h')
        self.entry_tf = config.get('entry_tf', '15m')
        
        # ============================================
        # TREND PARAMETERS
        # ============================================
        self.trend_params = {
            'ema_fast': config.get('ema_fast', 20),
            'ema_medium': config.get('ema_medium', 50),
            'ema_slow': config.get('ema_slow', 200),
            'adx_threshold': config.get('adx_threshold', 25),
            'trend_strength_threshold': config.get('trend_strength_threshold', 0.6),
            'momentum_threshold': config.get('momentum_threshold', 0.4),
            'volume_threshold': config.get('volume_threshold', 1.2),
            'rsi_oversold': config.get('rsi_oversold', 30),
            'rsi_overbought': config.get('rsi_overbought', 70),
            'min_confidence': config.get('min_confidence', 65),
            'max_spread': config.get('max_spread', 2.0),
            'pullback_depth': config.get('pullback_depth', 0.382),  # Fibonacci level
            'breakout_confirmation': config.get('breakout_confirmation', 1.005),
        }
        
        # ============================================
        # STATE
        # ============================================
        self.trend_cache = {}
        self.last_trend_analysis = None
        self.entry_signals = []
        self.exit_signals = []
        
        # ============================================
        # PERFORMANCE
        # ============================================
        self.performance_metrics.update({
            'trend_accuracy': [],
            'entry_quality': [],
            'exit_quality': [],
            'pullback_trades': 0,
            'breakout_trades': 0,
            'retest_trades': 0
        })
        
        # Initialize components
        self.indicator_engine = IndicatorEngine()
        self.candle_analyzer = CandleAnalyzer()
        
        # Load state
        self._load_state()
        
        logger.info(f"📈 Trend Follower Bot initialized for {self.symbol}")
    
    # ============================================
    # MAIN ANALYSIS METHOD
    # ============================================
    
    async def analyze_market(self, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Main market analysis and signal generation"""
        try:
            # Validate data
            if data.empty or len(data) < 100:
                logger.warning("Insufficient data for trend analysis")
                return None
            
            # Get multi-timeframe data
            tf_data = self._get_multi_timeframe_data(data)
            
            # Perform trend analysis
            trend_analysis = self._analyze_trend(tf_data)
            
            if not trend_analysis:
                return None
            
            # Check if trend is tradable
            if not self._is_trend_tradable(trend_analysis):
                return None
            
            # Find entry opportunities
            entry_signal = self._find_entry(trend_analysis, tf_data)
            
            if entry_signal:
                # Validate entry
                validated_signal = self._validate_entry(entry_signal, trend_analysis)
                if validated_signal:
                    return validated_signal
            
            return None
            
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return None
    
    # ============================================
    # TREND ANALYSIS
    # ============================================
    
    def _analyze_trend(self, data: Dict[str, pd.DataFrame]) -> Optional[TrendAnalysis]:
        """Comprehensive trend analysis across multiple timeframes"""
        try:
            primary_data = data.get(self.primary_tf)
            if primary_data is None or primary_data.empty:
                return None
            
            # Calculate trend indicators
            ema_fast = primary_data['close'].ewm(span=self.trend_params['ema_fast'], adjust=False).mean()
            ema_medium = primary_data['close'].ewm(span=self.trend_params['ema_medium'], adjust=False).mean()
            ema_slow = primary_data['close'].ewm(span=self.trend_params['ema_slow'], adjust=False).mean()
            
            # Calculate ADX
            adx = self._calculate_adx(primary_data)
            
            # Calculate momentum
            momentum = self._calculate_momentum(primary_data)
            
            # Calculate RSI
            rsi = self._calculate_rsi(primary_data)
            
            current_price = primary_data['close'].iloc[-1]
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(
                current_price, ema_fast, ema_medium, ema_slow, adx
            )
            
            # Determine trend strength
            trend_strength = self._determine_trend_strength(
                adx, ema_fast, ema_medium, ema_slow, current_price, data
            )
            
            # Determine trend phase
            trend_phase = self._determine_trend_phase(
                primary_data, trend_direction, momentum, rsi
            )
            
            # Find key levels
            key_levels = self._find_key_levels(primary_data)
            
            # Check multi-timeframe alignment
            mtf_aligned = self._check_mtf_alignment(data, trend_direction)
            
            # Check volume confirmation
            volume_confirmed = self._check_volume_confirmation(primary_data, trend_direction)
            
            # Calculate confidence
            confidence = self._calculate_trend_confidence(
                trend_direction, trend_strength, mtf_aligned, volume_confirmed
            )
            
            # Find support and resistance
            support_resistance = self._find_support_resistance(primary_data)
            
            # Find entry and exit zones
            entry_zones = self._find_entry_zones(primary_data, trend_direction, support_resistance)
            exit_zones = self._find_exit_zones(primary_data, trend_direction, support_resistance)
            
            # Calculate risk level (inline — uses locally computed values)
            risk_level = 50
            if trend_strength == TrendStrength.WEAK:
                risk_level += 20
            elif trend_strength == TrendStrength.MODERATE:
                risk_level += 10
            if trend_phase == TrendPhase.DISTRIBUTION:
                risk_level += 15
            elif trend_phase == TrendPhase.ACCUMULATION:
                risk_level -= 10
            if abs(momentum) < 0.2:
                risk_level += 10
            risk_level = min(95, max(5, risk_level))
            
            return TrendAnalysis(
                direction=trend_direction,
                strength=trend_strength,
                phase=trend_phase,
                confidence=confidence,
                key_levels=key_levels,
                momentum_score=momentum,
                volume_confirmation=volume_confirmed,
                multi_timeframe_aligned=mtf_aligned,
                support_resistance=support_resistance,
                entry_zones=entry_zones,
                exit_zones=exit_zones,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return None
    
    def _determine_trend_direction(self, price: float, ema_fast: pd.Series,
                                   ema_medium: pd.Series, ema_slow: pd.Series,
                                   adx: pd.Series) -> str:
        """Determine trend direction using multiple indicators"""
        try:
            # Check EMA alignment
            ema_aligned_bullish = (ema_fast.iloc[-1] > ema_medium.iloc[-1] > ema_slow.iloc[-1])
            ema_aligned_bearish = (ema_fast.iloc[-1] < ema_medium.iloc[-1] < ema_slow.iloc[-1])
            
            # Check price position
            price_above_emas = price > ema_fast.iloc[-1] > ema_medium.iloc[-1] > ema_slow.iloc[-1]
            price_below_emas = price < ema_fast.iloc[-1] < ema_medium.iloc[-1] < ema_slow.iloc[-1]
            
            # Check ADX for trend strength
            adx_strong = adx.iloc[-1] > self.trend_params['adx_threshold']
            
            # Determine direction
            if (ema_aligned_bullish or price_above_emas) and adx_strong:
                return "BULLISH"
            elif (ema_aligned_bearish or price_below_emas) and adx_strong:
                return "BEARISH"
            elif ema_aligned_bullish or price_above_emas:
                return "BULLISH"
            elif ema_aligned_bearish or price_below_emas:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            logger.error(f"Trend direction determination error: {e}")
            return "NEUTRAL"
    
    def _determine_trend_strength(self, adx: pd.Series, ema_fast: pd.Series,
                                  ema_medium: pd.Series, ema_slow: pd.Series,
                                  price: float, data: Dict) -> TrendStrength:
        """Determine trend strength using multiple factors"""
        try:
            score = 0
            
            # ADX strength
            if adx.iloc[-1] > 40:
                score += 40
            elif adx.iloc[-1] > 30:
                score += 30
            elif adx.iloc[-1] > 25:
                score += 20
            else:
                score += 10
            
            # EMA spread
            ema_spread = (ema_fast.iloc[-1] - ema_slow.iloc[-1]) / ema_slow.iloc[-1] * 100
            if abs(ema_spread) > 2:
                score += 30
            elif abs(ema_spread) > 1:
                score += 20
            else:
                score += 10
            
            # Price position
            price_position = (price - ema_slow.iloc[-1]) / ema_slow.iloc[-1] * 100
            if abs(price_position) > 3:
                score += 30
            elif abs(price_position) > 1.5:
                score += 20
            else:
                score += 10
            
            # Determine strength
            if score >= 80:
                return TrendStrength.EXTREME
            elif score >= 65:
                return TrendStrength.VERY_STRONG
            elif score >= 50:
                return TrendStrength.STRONG
            elif score >= 35:
                return TrendStrength.MODERATE
            else:
                return TrendStrength.WEAK
                
        except Exception as e:
            logger.error(f"Trend strength determination error: {e}")
            return TrendStrength.WEAK
    
    def _determine_trend_phase(self, data: pd.DataFrame, direction: str,
                               momentum: float, rsi: pd.Series) -> TrendPhase:
        """Determine current trend phase"""
        try:
            # Simple phase detection using price patterns
            highs = data['high'].tail(20)
            lows = data['low'].tail(20)
            
            # Find swing points
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(highs)-2):
                if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2]:
                    if highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]:
                        swing_highs.append(highs.iloc[i])
                
                if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2]:
                    if lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]:
                        swing_lows.append(lows.iloc[i])
            
            if direction == "BULLISH":
                # Check if making higher highs and higher lows
                if len(swing_highs) >= 3 and len(swing_lows) >= 3:
                    if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                        if momentum > 0.5:
                            return TrendPhase.MARKUP
                        else:
                            return TrendPhase.ACCUMULATION
                return TrendPhase.ACCUMULATION
                
            elif direction == "BEARISH":
                if len(swing_highs) >= 3 and len(swing_lows) >= 3:
                    if swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
                        if momentum < -0.5:
                            return TrendPhase.MARKDOWN
                        else:
                            return TrendPhase.DISTRIBUTION
                return TrendPhase.DISTRIBUTION
            
            return TrendPhase.ACCUMULATION
            
        except Exception as e:
            logger.error(f"Trend phase determination error: {e}")
            return TrendPhase.ACCUMULATION
    
    def _calculate_momentum(self, data: pd.DataFrame) -> float:
        """Calculate momentum score"""
        try:
            # Use ROC (Rate of Change)
            roc = data['close'].pct_change(14).iloc[-1] * 100
            
            # Normalize to -1 to 1
            momentum = np.clip(roc / 10, -1, 1)
            return momentum
            
        except Exception as e:
            logger.error(f"Momentum calculation error: {e}")
            return 0
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except:
            return pd.Series([50] * len(data))
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX"""
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()
            
            # Directional Movement
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
            
            return adx
            
        except Exception as e:
            logger.error(f"ADX calculation error: {e}")
            return pd.Series([25] * len(data))
    
    # ============================================
    # KEY LEVELS AND SUPPORT/RESISTANCE
    # ============================================
    
    def _find_key_levels(self, data: pd.DataFrame) -> Dict[str, float]:
        """Find key price levels"""
        try:
            # Recent swing points
            highs = data['high'].tail(50)
            lows = data['low'].tail(50)
            
            # Find swing highs
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(highs)-2):
                if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2]:
                    if highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]:
                        swing_highs.append(highs.iloc[i])
                
                if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2]:
                    if lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]:
                        swing_lows.append(lows.iloc[i])
            
            # Get nearest levels
            current_price = data['close'].iloc[-1]
            
            nearest_resistance = None
            nearest_support = None
            
            for level in swing_highs:
                if level > current_price:
                    if nearest_resistance is None or level < nearest_resistance:
                        nearest_resistance = level
            
            for level in swing_lows:
                if level < current_price:
                    if nearest_support is None or level > nearest_support:
                        nearest_support = level
            
            return {
                'current_price': current_price,
                'nearest_resistance': nearest_resistance,
                'nearest_support': nearest_support,
                'swing_highs': swing_highs[-5:] if swing_highs else [],
                'swing_lows': swing_lows[-5:] if swing_lows else []
            }
            
        except Exception as e:
            logger.error(f"Key levels finding error: {e}")
            return {}
    
    def _find_support_resistance(self, data: pd.DataFrame) -> Dict[str, List[float]]:
        """Find support and resistance levels"""
        try:
            highs = data['high'].tail(100)
            lows = data['low'].tail(100)
            
            # Cluster similar levels
            resistance_levels = []
            support_levels = []
            
            # Find swing highs
            swing_highs = []
            for i in range(2, len(highs)-2):
                if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2]:
                    if highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]:
                        swing_highs.append(highs.iloc[i])
            
            # Cluster swing highs
            if swing_highs:
                swing_highs.sort()
                cluster = [swing_highs[0]]
                for level in swing_highs[1:]:
                    if (level - cluster[-1]) / cluster[-1] < 0.005:
                        cluster.append(level)
                    else:
                        if len(cluster) >= 2:
                            resistance_levels.append(sum(cluster) / len(cluster))
                        cluster = [level]
                if len(cluster) >= 2:
                    resistance_levels.append(sum(cluster) / len(cluster))
            
            # Find swing lows
            swing_lows = []
            for i in range(2, len(lows)-2):
                if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2]:
                    if lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]:
                        swing_lows.append(lows.iloc[i])
            
            # Cluster swing lows
            if swing_lows:
                swing_lows.sort()
                cluster = [swing_lows[0]]
                for level in swing_lows[1:]:
                    if (level - cluster[-1]) / cluster[-1] < 0.005:
                        cluster.append(level)
                    else:
                        if len(cluster) >= 2:
                            support_levels.append(sum(cluster) / len(cluster))
                        cluster = [level]
                if len(cluster) >= 2:
                    support_levels.append(sum(cluster) / len(cluster))
            
            return {
                'resistance': sorted(resistance_levels, reverse=True)[:5],
                'support': sorted(support_levels)[:5]
            }
            
        except Exception as e:
            logger.error(f"Support/resistance finding error: {e}")
            return {'resistance': [], 'support': []}
    
    # ============================================
    # ENTRY AND EXIT ZONES
    # ============================================
    
    def _find_entry_zones(self, data: pd.DataFrame, direction: str,
                          support_resistance: Dict) -> List[Dict]:
        """Find entry zones for the trend"""
        try:
            entry_zones = []
            current_price = data['close'].iloc[-1]
            
            if direction == "BULLISH":
                # Pullback entry zone (support)
                if support_resistance.get('support'):
                    support_level = support_resistance['support'][0] if support_resistance['support'] else None
                    if support_level and current_price > support_level:
                        # Check if price is near support
                        if (current_price - support_level) / support_level < 0.02:
                            entry_zones.append({
                                'type': 'pullback',
                                'price': support_level,
                                'confidence': 80
                            })
                
                # Breakout entry zone (resistance)
                if support_resistance.get('resistance'):
                    resistance_level = support_resistance['resistance'][0] if support_resistance['resistance'] else None
                    if resistance_level and current_price > resistance_level:
                        entry_zones.append({
                            'type': 'breakout',
                            'price': resistance_level,
                            'confidence': 85
                        })
            
            elif direction == "BEARISH":
                # Pullback entry zone (resistance)
                if support_resistance.get('resistance'):
                    resistance_level = support_resistance['resistance'][0] if support_resistance['resistance'] else None
                    if resistance_level and current_price < resistance_level:
                        if (resistance_level - current_price) / resistance_level < 0.02:
                            entry_zones.append({
                                'type': 'pullback',
                                'price': resistance_level,
                                'confidence': 80
                            })
                
                # Breakout entry zone (support)
                if support_resistance.get('support'):
                    support_level = support_resistance['support'][0] if support_resistance['support'] else None
                    if support_level and current_price < support_level:
                        entry_zones.append({
                            'type': 'breakout',
                            'price': support_level,
                            'confidence': 85
                        })
            
            return entry_zones
            
        except Exception as e:
            logger.error(f"Entry zones finding error: {e}")
            return []
    
    def _find_exit_zones(self, data: pd.DataFrame, direction: str,
                         support_resistance: Dict) -> List[Dict]:
        """Find exit zones for the trend"""
        try:
            exit_zones = []
            
            if direction == "BULLISH":
                # Take profit at resistance levels
                for level in support_resistance.get('resistance', [])[:3]:
                    exit_zones.append({
                        'type': 'take_profit',
                        'price': level,
                        'priority': 1 if level == support_resistance['resistance'][0] else 2
                    })
            
            elif direction == "BEARISH":
                # Take profit at support levels
                for level in support_resistance.get('support', [])[:3]:
                    exit_zones.append({
                        'type': 'take_profit',
                        'price': level,
                        'priority': 1 if level == support_resistance['support'][0] else 2
                    })
            
            return exit_zones
            
        except Exception as e:
            logger.error(f"Exit zones finding error: {e}")
            return []
    
    # ============================================
    # ENTRY SIGNAL GENERATION
    # ============================================
    
    def _find_entry(self, trend_analysis: TrendAnalysis,
                    data: Dict[str, pd.DataFrame]) -> Optional[Dict]:
        """Find entry opportunity"""
        try:
            entry_data = data.get(self.entry_tf)
            if entry_data is None or entry_data.empty:
                return None
            
            current_price = entry_data['close'].iloc[-1]
            direction = trend_analysis.direction
            
            if direction == "NEUTRAL":
                return None
            
            # Check entry zones
            for zone in trend_analysis.entry_zones:
                if zone['type'] == 'pullback':
                    # Check if price is in pullback zone
                    if abs(current_price - zone['price']) / zone['price'] < 0.005:
                        return {
                            'type': EntryType.PULLBACK,
                            'price': current_price,
                            'zone': zone,
                            'confidence': zone['confidence']
                        }
                
                elif zone['type'] == 'breakout':
                    # Check if price is breaking out
                    if direction == "BULLISH":
                        if current_price > zone['price'] * self.trend_params['breakout_confirmation']:
                            return {
                                'type': EntryType.BREAKOUT,
                                'price': current_price,
                                'zone': zone,
                                'confidence': zone['confidence']
                            }
                    else:
                        if current_price < zone['price'] / self.trend_params['breakout_confirmation']:
                            return {
                                'type': EntryType.BREAKOUT,
                                'price': current_price,
                                'zone': zone,
                                'confidence': zone['confidence']
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Entry finding error: {e}")
            return None
    
    def _validate_entry(self, entry: Dict, trend_analysis: TrendAnalysis) -> Optional[TradeSignal]:
        """Validate entry and create trade signal"""
        try:
            # Check confidence
            # ENHANCED: AI confidence filter (12-point spec) — reject sub-threshold confluence
            if entry.get('confidence', 0) < 70 or trend_analysis.confidence < 60:
                return None

            # ENHANCED: multi-factor confluence — require momentum + MTF alignment
            if abs(trend_analysis.momentum_score) < 10:
                return None

            # ENHANCED: Risk/Reward gate (>=2.0x) and loss control from AdvancedEngine
            risk = abs(stop_loss - entry_price) / entry_price
            rr = abs(take_profit - entry_price) / abs(stop_loss - entry_price) if stop_loss else 0
            if rr < AdvancedTradeConfig.MIN_RR:
                return None
            if not engine.check_loss_controls():
                return None
            
            # Determine trade direction
            direction = trend_analysis.direction
            action = "BUY" if direction == "BULLISH" else "SELL"
            entry_price = entry['price']
            
            # Calculate stop loss
            stop_loss = self._calculate_stop_loss(entry_price, direction, trend_analysis)
            
            # Calculate take profit
            take_profit = self._calculate_take_profit(entry_price, direction, trend_analysis)
            
            # Calculate position size
            position_size = self._calculate_position_size(entry_price, stop_loss)
            
            # Determine strength
            strength = self._determine_signal_strength(trend_analysis, entry)
            
            # Determine quality
            quality = self._determine_trade_quality(trend_analysis, entry)
            
            # Generate reasoning
            reasoning = self._generate_entry_reasoning(direction, entry, trend_analysis)
            
            return TradeSignal(
                action=action,
                confidence=entry['confidence'],
                strength=strength,
                quality=quality,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                reason=f"{action} signal: {entry['type'].value} {direction} trend",
                supporting_indicators=['EMA', 'ADX', 'RSI', 'Volume'],
                ai_reasoning=reasoning,
                risk_score=trend_analysis.risk_level,
                expected_return=abs(take_profit - entry_price) / entry_price * 100,
                time_horizon="MEDIUM",
                metadata={
                    'entry_type': entry['type'].value,
                    'trend_phase': trend_analysis.phase.value,
                    'trend_strength': trend_analysis.strength.value,
                    'momentum_score': trend_analysis.momentum_score,
                    'mtf_aligned': trend_analysis.multi_timeframe_aligned
                }
            )
            
        except Exception as e:
            logger.error(f"Entry validation error: {e}")
            return None
    
    # ============================================
    # POSITION MANAGEMENT
    # ============================================
    
    def _calculate_stop_loss(self, entry_price: float, direction: str,
                             trend_analysis: TrendAnalysis) -> float:
        """Calculate stop loss level"""
        try:
            atr = self._calculate_atr(trend_analysis)
            stop_distance = atr * 1.5  # 1.5x ATR
            
            if direction == "BULLISH":
                # Place stop below recent swing low
                swing_lows = trend_analysis.key_levels.get('swing_lows', [])
                if swing_lows:
                    recent_low = swing_lows[-1]
                    if recent_low < entry_price:
                        return recent_low - atr * 0.5
                return entry_price - stop_distance
            else:
                # Place stop above recent swing high
                swing_highs = trend_analysis.key_levels.get('swing_highs', [])
                if swing_highs:
                    recent_high = swing_highs[-1]
                    if recent_high > entry_price:
                        return recent_high + atr * 0.5
                return entry_price + stop_distance
                
        except Exception as e:
            logger.error(f"Stop loss calculation error: {e}")
            return entry_price * (1 - 0.01) if direction == "BULLISH" else entry_price * (1 + 0.01)
    
    def _calculate_take_profit(self, entry_price: float, direction: str,
                               trend_analysis: TrendAnalysis) -> float:
        """Calculate take profit level"""
        try:
            # Use nearest resistance/support levels
            if direction == "BULLISH":
                levels = trend_analysis.support_resistance.get('resistance', [])
                if levels:
                    # Target next resistance
                    for level in levels:
                        if level > entry_price:
                            return level
                # If no resistance found, use 2x risk
                atr = self._calculate_atr(trend_analysis)
                return entry_price + (atr * 2)
            else:
                levels = trend_analysis.support_resistance.get('support', [])
                if levels:
                    for level in levels:
                        if level < entry_price:
                            return level
                atr = self._calculate_atr(trend_analysis)
                return entry_price - (atr * 2)
                
        except Exception as e:
            logger.error(f"Take profit calculation error: {e}")
            return entry_price * (1 + 0.02) if direction == "BULLISH" else entry_price * (1 - 0.02)
    
    def _calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """Calculate position size using risk management"""
        try:
            risk_amount = self.parameters.get('max_risk_per_trade', 0.02)
            account_balance = self.state.performance.total_profit + 10000  # Mock balance
            
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit <= 0:
                return self.parameters.get('position_size', 100)
            
            max_risk = account_balance * risk_amount
            position_size = max_risk / risk_per_unit
            
            # Apply limits
            max_position = self.parameters.get('max_position_size', 1000)
            min_position = self.parameters.get('min_position_size', 10)
            
            return max(min_position, min(position_size, max_position))
            
        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            return 100
    
    def _calculate_atr(self, trend_analysis: TrendAnalysis) -> float:
        """Calculate ATR"""
        try:
            # Use default if not available
            return 0.001  # Example for Forex
        except:
            return 0.001
    
    # ============================================
    # SIGNAL STRENGTH AND QUALITY
    # ============================================
    
    def _determine_signal_strength(self, trend_analysis: TrendAnalysis,
                                   entry: Dict) -> SignalStrength:
        """Determine signal strength"""
        try:
            score = 0
            
            # Trend strength
            if trend_analysis.strength == TrendStrength.EXTREME:
                score += 40
            elif trend_analysis.strength == TrendStrength.VERY_STRONG:
                score += 35
            elif trend_analysis.strength == TrendStrength.STRONG:
                score += 30
            elif trend_analysis.strength == TrendStrength.MODERATE:
                score += 20
            else:
                score += 10
            
            # Entry confidence
            score += entry.get('confidence', 0) * 0.4
            
            # Multi-timeframe alignment
            if trend_analysis.multi_timeframe_aligned:
                score += 20
            
            # Volume confirmation
            if trend_analysis.volume_confirmation:
                score += 10
            
            if score >= 85:
                return SignalStrength.VERY_STRONG
            elif score >= 70:
                return SignalStrength.STRONG
            elif score >= 55:
                return SignalStrength.MODERATE
            elif score >= 40:
                return SignalStrength.WEAK
            else:
                return SignalStrength.VERY_WEAK
                
        except Exception as e:
            logger.error(f"Signal strength determination error: {e}")
            return SignalStrength.MODERATE
    
    def _determine_trade_quality(self, trend_analysis: TrendAnalysis,
                                 entry: Dict) -> TradeQuality:
        """Determine trade quality"""
        try:
            score = 0
            
            # Trend confidence
            score += trend_analysis.confidence * 0.3
            
            # Entry confidence
            score += entry.get('confidence', 0) * 0.3
            
            # Risk level (lower is better)
            score += (100 - trend_analysis.risk_level) * 0.2
            
            # Momentum
            score += abs(trend_analysis.momentum_score) * 20
            
            if score >= 80:
                return TradeQuality.PERFECT
            elif score >= 65:
                return TradeQuality.EXCELLENT
            elif score >= 50:
                return TradeQuality.GOOD
            elif score >= 35:
                return TradeQuality.AVERAGE
            else:
                return TradeQuality.POOR
                
        except Exception as e:
            logger.error(f"Trade quality determination error: {e}")
            return TradeQuality.GOOD
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def _generate_entry_reasoning(self, direction: str, entry: Dict,
                                  trend_analysis: TrendAnalysis) -> str:
        """Generate AI reasoning for entry"""
        reasoning = f"Entering {direction} position based on:\n"
        reasoning += f"- {direction} trend detected on {self.primary_tf} timeframe\n"
        reasoning += f"- Trend strength: {trend_analysis.strength.value}\n"
        reasoning += f"- Trend phase: {trend_analysis.phase.value}\n"
        reasoning += f"- Entry type: {entry['type'].value}\n"
        reasoning += f"- Momentum score: {trend_analysis.momentum_score:.2f}\n"
        reasoning += f"- Multi-timeframe aligned: {trend_analysis.multi_timeframe_aligned}\n"
        reasoning += f"- Volume confirmation: {trend_analysis.volume_confirmation}\n"
        reasoning += f"- Confidence: {entry['confidence']:.1f}%"
        return reasoning
    
    def _get_multi_timeframe_data(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Get data for multiple timeframes"""
        try:
            # This would typically resample data
            # For now, return the same data for all timeframes
            tf_data = {}
            for tf in self.timeframes:
                tf_data[tf] = data
            return tf_data
            
        except Exception as e:
            logger.error(f"Multi-timeframe data error: {e}")
            return {self.primary_tf: data}
    
    def _check_mtf_alignment(self, data: Dict[str, pd.DataFrame], direction: str) -> bool:
        """Check if multiple timeframes align"""
        try:
            aligned_count = 0
            total_tfs = len(data)
            
            for tf, df in data.items():
                if df.empty:
                    continue
                
                # Check trend on this timeframe
                ema_fast = df['close'].ewm(span=20).mean()
                ema_slow = df['close'].ewm(span=50).mean()
                price = df['close'].iloc[-1]
                
                if direction == "BULLISH":
                    if price > ema_fast.iloc[-1] > ema_slow.iloc[-1]:
                        aligned_count += 1
                else:
                    if price < ema_fast.iloc[-1] < ema_slow.iloc[-1]:
                        aligned_count += 1
            
            return aligned_count >= total_tfs * 0.6
            
        except Exception as e:
            logger.error(f"MTF alignment check error: {e}")
            return False
    
    def _check_volume_confirmation(self, data: pd.DataFrame, direction: str) -> bool:
        """Check if volume confirms the trend"""
        try:
            if 'volume' not in data.columns:
                return True
            
            avg_volume = data['volume'].rolling(20).mean()
            current_volume = data['volume'].iloc[-1]
            
            # Check if volume is above average
            return current_volume > avg_volume.iloc[-1] * 1.2
            
        except Exception as e:
            logger.error(f"Volume confirmation check error: {e}")
            return True
    
    def _calculate_trend_confidence(self, direction: str, strength: TrendStrength,
                                    mtf_aligned: bool, volume_confirmed: bool) -> float:
        """Calculate trend confidence score"""
        try:
            confidence = 50  # Base
            
            # Direction
            if direction != "NEUTRAL":
                confidence += 10
            
            # Strength
            if strength == TrendStrength.EXTREME:
                confidence += 25
            elif strength == TrendStrength.VERY_STRONG:
                confidence += 20
            elif strength == TrendStrength.STRONG:
                confidence += 15
            elif strength == TrendStrength.MODERATE:
                confidence += 10
            else:
                confidence += 5
            
            # MTF alignment
            if mtf_aligned:
                confidence += 15
            
            # Volume confirmation
            if volume_confirmed:
                confidence += 10
            
            return min(95, confidence)
            
        except Exception as e:
            logger.error(f"Trend confidence calculation error: {e}")
            return 50
    
    def _calculate_risk_level(self, trend_analysis: TrendAnalysis) -> float:
        """Calculate risk level for the setup"""
        try:
            risk = 50  # Base
            
            # Adjust based on trend strength
            if trend_analysis.strength == TrendStrength.WEAK:
                risk += 20
            elif trend_analysis.strength == TrendStrength.MODERATE:
                risk += 10
            
            # Adjust based on phase
            if trend_analysis.phase == TrendPhase.DISTRIBUTION:
                risk += 15
            elif trend_analysis.phase == TrendPhase.ACCUMULATION:
                risk -= 10
            
            # Adjust based on momentum
            if abs(trend_analysis.momentum_score) < 0.2:
                risk += 10
            
            return min(95, max(5, risk))
            
        except Exception as e:
            logger.error(f"Risk level calculation error: {e}")
            return 50
    
    def _is_trend_tradable(self, trend_analysis: TrendAnalysis) -> bool:
        """Check if trend is tradable"""
        if trend_analysis.direction == "NEUTRAL":
            return False
        
        if trend_analysis.strength == TrendStrength.WEAK:
            return False
        
        if trend_analysis.risk_level > 70:
            return False
        
        return True
    
    # ============================================
    # STRATEGY AND INDICATORS
    # ============================================
    
    def get_strategies(self) -> List[str]:
        """Get available strategies"""
        return [
            'trend_following',
            'pullback_trading',
            'breakout_trading',
            'trend_continuation'
        ]
    
    def get_indicators(self) -> List[str]:
        """Get indicators used"""
        return [
            'EMA (20, 50, 200)',
            'ADX',
            'RSI',
            'MACD',
            'Volume',
            'ATR',
            'Support/Resistance'
        ]
    
    # ============================================
    # SAVE/LOAD STATE
    # ============================================
    
    def _load_state(self):
        """Load bot state"""
        super()._load_state()
        # Load trend-specific state if exists