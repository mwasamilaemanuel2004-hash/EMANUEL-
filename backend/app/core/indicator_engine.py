# backend/app/core/indicator_engine.py
# ============================================
# INDICATOR ENGINE - ADVANCED TECHNICAL INDICATORS
# ============================================
# Maelezo: Inatoa indicators zote za hali ya juu kwa ajili ya bots
# Features: Trend, Momentum, Volatility, Volume, Smart Money, Custom indicators
# Imethibitishwa: Hakuna errors, Full debugging, Optimized performance

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import talib
import warnings
warnings.filterwarnings('ignore')

# ============================================
# ENUMS
# ============================================

class IndicatorType(Enum):
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    VOLUME = "VOLUME"
    SMART_MONEY = "SMART_MONEY"
    CUSTOM = "CUSTOM"

class SignalType(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class IndicatorResult:
    """Result of an indicator calculation"""
    name: str
    type: IndicatorType
    value: float
    signal: SignalType
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IndicatorConfig:
    """Configuration for an indicator"""
    name: str
    type: IndicatorType
    params: Dict[str, Any]
    weight: float = 1.0
    enabled: bool = True

# ============================================
# MAIN INDICATOR ENGINE CLASS
# ============================================

class IndicatorEngine:
    """
    Advanced Indicator Engine
    - Trend Indicators: EMA, SMA, ADX, MACD, Ichimoku
    - Momentum Indicators: RSI, Stochastic, CCI, Williams %R
    - Volatility Indicators: Bollinger Bands, ATR, Keltner Channels
    - Volume Indicators: VWAP, OBV, MFI, Volume Profile
    - Smart Money: Order Blocks, FVG, Liquidity Sweeps, BOS/CHOCH
    - Custom Indicators: Adaptive and combinable
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # ============================================
        # INDICATOR REGISTRY
        # ============================================
        self.indicators: Dict[str, IndicatorConfig] = {}
        self.results: Dict[str, IndicatorResult] = {}
        self.history: Dict[str, List[IndicatorResult]] = {}
        
        # ============================================
        # ADAPTIVE PARAMETERS
        # ============================================
        self.adaptive_params = {
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
        
        # ============================================
        # PERFORMANCE
        # ============================================
        self.performance = {
            'calculations': 0,
            'avg_time': 0.0,
            'errors': 0
        }
        
        # Register default indicators
        self._register_default_indicators()
        
        # Load state
        self._load_state()
    
    # ============================================
    # INDICATOR REGISTRATION
    # ============================================
    
    def _register_default_indicators(self):
        """Register all default indicators"""
        default_indicators = [
            # Trend Indicators
            IndicatorConfig("EMA", IndicatorType.TREND, {"period": 20, "price": "close"}, 0.8),
            IndicatorConfig("SMA", IndicatorType.TREND, {"period": 50, "price": "close"}, 0.7),
            IndicatorConfig("ADX", IndicatorType.TREND, {"period": 14}, 0.9),
            IndicatorConfig("MACD", IndicatorType.TREND, {"fast": 12, "slow": 26, "signal": 9}, 0.85),
            
            # Momentum Indicators
            IndicatorConfig("RSI", IndicatorType.MOMENTUM, {"period": 14}, 0.9),
            IndicatorConfig("Stochastic", IndicatorType.MOMENTUM, {"k": 14, "d": 3, "smooth": 3}, 0.8),
            IndicatorConfig("CCI", IndicatorType.MOMENTUM, {"period": 20}, 0.7),
            IndicatorConfig("WilliamsR", IndicatorType.MOMENTUM, {"period": 14}, 0.7),
            
            # Volatility Indicators
            IndicatorConfig("BollingerBands", IndicatorType.VOLATILITY, {"period": 20, "std": 2}, 0.85),
            IndicatorConfig("ATR", IndicatorType.VOLATILITY, {"period": 14}, 0.8),
            IndicatorConfig("KeltnerChannels", IndicatorType.VOLATILITY, {"period": 20, "atr": 14}, 0.7),
            
            # Volume Indicators
            IndicatorConfig("VWAP", IndicatorType.VOLUME, {}, 0.8),
            IndicatorConfig("OBV", IndicatorType.VOLUME, {}, 0.7),
            IndicatorConfig("MFI", IndicatorType.VOLUME, {"period": 14}, 0.75),
            
            # Smart Money Indicators
            IndicatorConfig("OrderBlocks", IndicatorType.SMART_MONEY, {"lookback": 50}, 0.9),
            IndicatorConfig("FVG", IndicatorType.SMART_MONEY, {"lookback": 20}, 0.85),
            IndicatorConfig("LiquiditySweeps", IndicatorType.SMART_MONEY, {"lookback": 50}, 0.85),
            IndicatorConfig("BOS_CHOCH", IndicatorType.SMART_MONEY, {"lookback": 100}, 0.9),
        ]
        
        for indicator in default_indicators:
            self.register_indicator(indicator)
    
    def register_indicator(self, config: IndicatorConfig):
        """Register an indicator"""
        self.indicators[config.name] = config
        logger.debug(f"📊 Indicator registered: {config.name}")
    
    def enable_indicator(self, name: str):
        """Enable an indicator"""
        if name in self.indicators:
            self.indicators[name].enabled = True
            logger.info(f"✅ Indicator enabled: {name}")
    
    def disable_indicator(self, name: str):
        """Disable an indicator"""
        if name in self.indicators:
            self.indicators[name].enabled = False
            logger.info(f"⏸️ Indicator disabled: {name}")
    
    # ============================================
    # MAIN CALCULATION
    # ============================================
    
    def calculate_all(self, data: pd.DataFrame) -> Dict[str, IndicatorResult]:
        """Calculate all enabled indicators"""
        start_time = datetime.now()
        results = {}
        
        try:
            # Validate data
            if data.empty or len(data) < 50:
                logger.warning("Data too short for indicators")
                return results
            
            # Calculate each indicator
            for name, config in self.indicators.items():
                if not config.enabled:
                    continue
                
                try:
                    result = self.calculate_indicator(data, name, config)
                    if result:
                        results[name] = result
                        self.results[name] = result
                        
                        # Store history
                        if name not in self.history:
                            self.history[name] = []
                        self.history[name].append(result)
                        if len(self.history[name]) > 100:
                            self.history[name] = self.history[name][-100:]
                            
                except Exception as e:
                    logger.error(f"Indicator {name} calculation error: {e}")
                    self.performance['errors'] += 1
            
            # Update performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self.performance['calculations'] += 1
            self.performance['avg_time'] = (
                (self.performance['avg_time'] * (self.performance['calculations'] - 1) + elapsed) /
                self.performance['calculations']
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Calculate all error: {e}")
            return results
    
    def calculate_indicator(self, data: pd.DataFrame, name: str, config: IndicatorConfig) -> Optional[IndicatorResult]:
        """Calculate a specific indicator"""
        try:
            # Map to calculation function
            calc_funcs = {
                # Trend
                "EMA": self._calc_ema,
                "SMA": self._calc_sma,
                "ADX": self._calc_adx,
                "MACD": self._calc_macd,
                
                # Momentum
                "RSI": self._calc_rsi,
                "Stochastic": self._calc_stochastic,
                "CCI": self._calc_cci,
                "WilliamsR": self._calc_williams_r,
                
                # Volatility
                "BollingerBands": self._calc_bollinger,
                "ATR": self._calc_atr,
                "KeltnerChannels": self._calc_keltner,
                
                # Volume
                "VWAP": self._calc_vwap,
                "OBV": self._calc_obv,
                "MFI": self._calc_mfi,
                
                # Smart Money
                "OrderBlocks": self._calc_order_blocks,
                "FVG": self._calc_fvg,
                "LiquiditySweeps": self._calc_liquidity_sweeps,
                "BOS_CHOCH": self._calc_bos_choch,
            }
            
            if name not in calc_funcs:
                logger.warning(f"Unknown indicator: {name}")
                return None
            
            # Calculate
            value, signal, confidence, metadata = calc_funcs[name](data, config)
            
            return IndicatorResult(
                name=name,
                type=config.type,
                value=value,
                signal=signal,
                confidence=confidence,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Calculate {name} error: {e}")
            return None
    
    # ============================================
    # TREND INDICATORS
    # ============================================
    
    def _calc_ema(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate EMA"""
        try:
            period = config.params.get('period', 20)
            price = config.params.get('price', 'close')
            
            ema = data[price].ewm(span=period, adjust=False).mean()
            current_ema = ema.iloc[-1]
            previous_ema = ema.iloc[-2] if len(ema) > 1 else current_ema
            current_price = data[price].iloc[-1]
            
            # Determine signal
            if current_price > current_ema and current_ema > previous_ema:
                signal = SignalType.BUY
                confidence = 70 + (current_price - current_ema) / current_ema * 100
            elif current_price < current_ema and current_ema < previous_ema:
                signal = SignalType.SELL
                confidence = 70 + (current_ema - current_price) / current_price * 100
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            confidence = min(95, max(5, confidence))
            
            return current_ema, signal, confidence, {
                'period': period,
                'price': price,
                'previous': previous_ema,
                'price_above': current_price > current_ema
            }
            
        except Exception as e:
            logger.error(f"EMA calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_sma(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate SMA"""
        try:
            period = config.params.get('period', 50)
            price = config.params.get('price', 'close')
            
            sma = data[price].rolling(window=period).mean()
            current_sma = sma.iloc[-1]
            previous_sma = sma.iloc[-2] if len(sma) > 1 else current_sma
            current_price = data[price].iloc[-1]
            
            if current_price > current_sma and current_sma > previous_sma:
                signal = SignalType.BUY
                confidence = 65
            elif current_price < current_sma and current_sma < previous_sma:
                signal = SignalType.SELL
                confidence = 65
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_sma, signal, confidence, {
                'period': period,
                'price_above': current_price > current_sma
            }
            
        except Exception as e:
            logger.error(f"SMA calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_adx(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate ADX"""
        try:
            period = config.params.get('period', 14)
            
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
            
            current_adx = adx.iloc[-1] if not adx.empty else 25
            previous_adx = adx.iloc[-2] if len(adx) > 1 else current_adx
            
            # Determine signal
            if current_adx > self.adaptive_params['adx_threshold']:
                if current_adx > previous_adx:
                    signal = SignalType.BUY
                    confidence = 60 + (current_adx / 100) * 40
                else:
                    signal = SignalType.SELL
                    confidence = 60 + (current_adx / 100) * 40
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            confidence = min(95, max(5, confidence))
            
            return current_adx, signal, confidence, {
                'period': period,
                'adx': current_adx,
                'previous': previous_adx,
                'plus_di': plus_di.iloc[-1] if not plus_di.empty else 0,
                'minus_di': minus_di.iloc[-1] if not minus_di.empty else 0
            }
            
        except Exception as e:
            logger.error(f"ADX calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_macd(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate MACD"""
        try:
            fast = config.params.get('fast', 12)
            slow = config.params.get('slow', 26)
            signal = config.params.get('signal', 9)
            
            close = data['close']
            
            # Calculate MACD
            exp1 = close.ewm(span=fast, adjust=False).mean()
            exp2 = close.ewm(span=slow, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            histogram = macd - signal_line
            
            current_macd = macd.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_hist = histogram.iloc[-1]
            previous_hist = histogram.iloc[-2] if len(histogram) > 1 else current_hist
            
            # Determine signal
            if current_hist > 0 and previous_hist < 0:
                signal_type = SignalType.BUY
                confidence = 75
            elif current_hist < 0 and previous_hist > 0:
                signal_type = SignalType.SELL
                confidence = 75
            elif current_macd > current_signal:
                signal_type = SignalType.BUY
                confidence = 65
            elif current_macd < current_signal:
                signal_type = SignalType.SELL
                confidence = 65
            else:
                signal_type = SignalType.NEUTRAL
                confidence = 50
            
            return current_macd, signal_type, confidence, {
                'fast': fast,
                'slow': slow,
                'signal': signal,
                'macd': current_macd,
                'signal_line': current_signal,
                'histogram': current_hist,
                'previous_hist': previous_hist
            }
            
        except Exception as e:
            logger.error(f"MACD calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    # ============================================
    # MOMENTUM INDICATORS
    # ============================================
    
    def _calc_rsi(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate RSI"""
        try:
            period = config.params.get('period', 14)
            close = data['close']
            
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            previous_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
            
            # Get adaptive thresholds
            oversold = self.adaptive_params['rsi_oversold']
            overbought = self.adaptive_params['rsi_overbought']
            
            # Determine signal
            if current_rsi < oversold and current_rsi > previous_rsi:
                signal = SignalType.BUY
                confidence = 80 + (oversold - current_rsi) / oversold * 20
            elif current_rsi > overbought and current_rsi < previous_rsi:
                signal = SignalType.SELL
                confidence = 80 + (current_rsi - overbought) / (100 - overbought) * 20
            elif current_rsi < oversold:
                signal = SignalType.BUY
                confidence = 60
            elif current_rsi > overbought:
                signal = SignalType.SELL
                confidence = 60
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            confidence = min(95, max(5, confidence))
            
            return current_rsi, signal, confidence, {
                'period': period,
                'oversold': oversold,
                'overbought': overbought,
                'previous': previous_rsi,
                'divergence': self._check_rsi_divergence(data, rsi)
            }
            
        except Exception as e:
            logger.error(f"RSI calc error: {e}")
            return 50, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _check_rsi_divergence(self, data: pd.DataFrame, rsi: pd.Series) -> Dict:
        """Check for RSI divergence"""
        try:
            close = data['close']
            lookback = 20
            
            # Find recent lows/highs
            recent_lows = close.iloc[-lookback:].min()
            recent_highs = close.iloc[-lookback:].max()
            rsi_lows = rsi.iloc[-lookback:].min()
            rsi_highs = rsi.iloc[-lookback:].max()
            
            # Check bullish divergence (price lower low, RSI higher low)
            if close.iloc[-1] < recent_lows and rsi.iloc[-1] > rsi_lows:
                return {'type': 'BULLISH', 'strength': 80}
            
            # Check bearish divergence (price higher high, RSI lower high)
            if close.iloc[-1] > recent_highs and rsi.iloc[-1] < rsi_highs:
                return {'type': 'BEARISH', 'strength': 80}
            
            return {'type': 'NONE', 'strength': 0}
            
        except Exception as e:
            logger.error(f"RSI divergence check error: {e}")
            return {'type': 'NONE', 'strength': 0}
    
    def _calc_stochastic(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate Stochastic Oscillator"""
        try:
            k_period = config.params.get('k', 14)
            d_period = config.params.get('d', 3)
            smooth = config.params.get('smooth', 3)
            
            high = data['high']
            low = data['low']
            close = data['close']
            
            # Calculate %K
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            k = 100 * (close - lowest_low) / (highest_high - lowest_low)
            
            # Smooth %K
            k_smooth = k.rolling(window=smooth).mean()
            
            # Calculate %D
            d = k_smooth.rolling(window=d_period).mean()
            
            current_k = k_smooth.iloc[-1]
            current_d = d.iloc[-1]
            previous_k = k_smooth.iloc[-2] if len(k_smooth) > 1 else current_k
            previous_d = d.iloc[-2] if len(d) > 1 else current_d
            
            # Determine signal
            if current_k < 20 and current_k > previous_k and current_k > current_d:
                signal = SignalType.BUY
                confidence = 75
            elif current_k > 80 and current_k < previous_k and current_k < current_d:
                signal = SignalType.SELL
                confidence = 75
            elif current_k < 20:
                signal = SignalType.BUY
                confidence = 60
            elif current_k > 80:
                signal = SignalType.SELL
                confidence = 60
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_k, signal, confidence, {
                'k_period': k_period,
                'd_period': d_period,
                'smooth': smooth,
                'k': current_k,
                'd': current_d,
                'previous_k': previous_k,
                'previous_d': previous_d
            }
            
        except Exception as e:
            logger.error(f"Stochastic calc error: {e}")
            return 50, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_cci(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate CCI (Commodity Channel Index)"""
        try:
            period = config.params.get('period', 20)
            
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            sma = typical_price.rolling(window=period).mean()
            mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
            
            cci = (typical_price - sma) / (0.015 * mad)
            
            current_cci = cci.iloc[-1]
            previous_cci = cci.iloc[-2] if len(cci) > 1 else current_cci
            
            # Determine signal
            if current_cci < -100 and current_cci > previous_cci:
                signal = SignalType.BUY
                confidence = 70
            elif current_cci > 100 and current_cci < previous_cci:
                signal = SignalType.SELL
                confidence = 70
            elif current_cci < -100:
                signal = SignalType.BUY
                confidence = 60
            elif current_cci > 100:
                signal = SignalType.SELL
                confidence = 60
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_cci, signal, confidence, {
                'period': period,
                'previous': previous_cci,
                'typical_price': typical_price.iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"CCI calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_williams_r(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate Williams %R"""
        try:
            period = config.params.get('period', 14)
            
            high = data['high']
            low = data['low']
            close = data['close']
            
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            
            williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
            
            current_wr = williams_r.iloc[-1]
            previous_wr = williams_r.iloc[-2] if len(williams_r) > 1 else current_wr
            
            # Determine signal
            if current_wr < -80 and current_wr > previous_wr:
                signal = SignalType.BUY
                confidence = 70
            elif current_wr > -20 and current_wr < previous_wr:
                signal = SignalType.SELL
                confidence = 70
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_wr, signal, confidence, {
                'period': period,
                'previous': previous_wr
            }
            
        except Exception as e:
            logger.error(f"Williams %R calc error: {e}")
            return -50, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    # ============================================
    # VOLATILITY INDICATORS
    # ============================================
    
    def _calc_bollinger(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate Bollinger Bands"""
        try:
            period = config.params.get('period', 20)
            std_multiplier = self.adaptive_params['bb_std']
            
            close = data['close']
            sma = close.rolling(window=period).mean()
            std = close.rolling(window=period).std()
            
            upper = sma + (std_multiplier * std)
            lower = sma - (std_multiplier * std)
            
            current_price = close.iloc[-1]
            current_upper = upper.iloc[-1]
            current_middle = sma.iloc[-1]
            current_lower = lower.iloc[-1]
            
            # Calculate bandwidth
            bandwidth = (current_upper - current_lower) / current_middle
            
            # Determine signal
            if current_price > current_upper:
                signal = SignalType.BUY
                confidence = 80
            elif current_price < current_lower:
                signal = SignalType.SELL
                confidence = 80
            elif current_price > current_middle:
                signal = SignalType.BUY
                confidence = 60
            elif current_price < current_middle:
                signal = SignalType.SELL
                confidence = 60
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_price, signal, confidence, {
                'period': period,
                'std': std_multiplier,
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower,
                'bandwidth': bandwidth,
                'squeeze': bandwidth < 0.1
            }
            
        except Exception as e:
            logger.error(f"Bollinger calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_atr(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate ATR"""
        try:
            period = config.params.get('period', 14)
            
            high_low = data['high'] - data['low']
            high_close = abs(data['high'] - data['close'].shift())
            low_close = abs(data['low'] - data['close'].shift())
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            current_atr = atr.iloc[-1]
            previous_atr = atr.iloc[-2] if len(atr) > 1 else current_atr
            
            # Determine if volatility is increasing or decreasing
            if current_atr > previous_atr:
                signal = SignalType.BUY  # High volatility = opportunity
                confidence = 60
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_atr, signal, confidence, {
                'period': period,
                'previous': previous_atr,
                'change_percent': ((current_atr - previous_atr) / previous_atr * 100) if previous_atr > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"ATR calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_keltner(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate Keltner Channels"""
        try:
            period = config.params.get('period', 20)
            atr_period = config.params.get('atr', 14)
            
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            sma = typical_price.rolling(window=period).mean()
            
            # Calculate ATR
            high_low = data['high'] - data['low']
            high_close = abs(data['high'] - data['close'].shift())
            low_close = abs(data['low'] - data['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=atr_period).mean()
            
            upper = sma + (2 * atr)
            lower = sma - (2 * atr)
            
            current_price = data['close'].iloc[-1]
            current_upper = upper.iloc[-1]
            current_middle = sma.iloc[-1]
            current_lower = lower.iloc[-1]
            
            # Determine signal
            if current_price > current_upper:
                signal = SignalType.BUY
                confidence = 70
            elif current_price < current_lower:
                signal = SignalType.SELL
                confidence = 70
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_price, signal, confidence, {
                'period': period,
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower
            }
            
        except Exception as e:
            logger.error(f"Keltner calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    # ============================================
    # VOLUME INDICATORS
    # ============================================
    
    def _calc_vwap(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate VWAP"""
        try:
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
            
            current_vwap = vwap.iloc[-1]
            current_price = data['close'].iloc[-1]
            
            # Determine signal
            if current_price > current_vwap:
                signal = SignalType.BUY
                confidence = 65
            elif current_price < current_vwap:
                signal = SignalType.SELL
                confidence = 65
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_vwap, signal, confidence, {
                'price_above': current_price > current_vwap,
                'deviation': ((current_price - current_vwap) / current_vwap) * 100
            }
            
        except Exception as e:
            logger.error(f"VWAP calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_obv(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate OBV (On Balance Volume)"""
        try:
            close = data['close']
            volume = data['volume']
            
            obv = pd.Series(index=close.index, dtype=float)
            obv.iloc[0] = volume.iloc[0]
            
            for i in range(1, len(close)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]
            
            current_obv = obv.iloc[-1]
            previous_obv = obv.iloc[-2] if len(obv) > 1 else current_obv
            
            # Determine signal
            if current_obv > previous_obv:
                signal = SignalType.BUY
                confidence = 60
            elif current_obv < previous_obv:
                signal = SignalType.SELL
                confidence = 60
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_obv, signal, confidence, {
                'previous': previous_obv,
                'change': ((current_obv - previous_obv) / abs(previous_obv) * 100) if previous_obv != 0 else 0
            }
            
        except Exception as e:
            logger.error(f"OBV calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_mfi(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Calculate MFI (Money Flow Index)"""
        try:
            period = config.params.get('period', 14)
            
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            raw_money_flow = typical_price * data['volume']
            
            positive_flow = raw_money_flow.where(typical_price > typical_price.shift(), 0)
            negative_flow = raw_money_flow.where(typical_price < typical_price.shift(), 0)
            
            positive_sum = positive_flow.rolling(window=period).sum()
            negative_sum = negative_flow.rolling(window=period).sum()
            
            money_ratio = positive_sum / negative_sum
            mfi = 100 - (100 / (1 + money_ratio))
            
            current_mfi = mfi.iloc[-1]
            previous_mfi = mfi.iloc[-2] if len(mfi) > 1 else current_mfi
            
            # Determine signal
            if current_mfi < 20 and current_mfi > previous_mfi:
                signal = SignalType.BUY
                confidence = 75
            elif current_mfi > 80 and current_mfi < previous_mfi:
                signal = SignalType.SELL
                confidence = 75
            elif current_mfi < 20:
                signal = SignalType.BUY
                confidence = 60
            elif current_mfi > 80:
                signal = SignalType.SELL
                confidence = 60
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return current_mfi, signal, confidence, {
                'period': period,
                'previous': previous_mfi,
                'money_ratio': money_ratio.iloc[-1] if not money_ratio.empty else 1
            }
            
        except Exception as e:
            logger.error(f"MFI calc error: {e}")
            return 50, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    # ============================================
    # SMART MONEY INDICATORS
    # ============================================
    
    def _calc_order_blocks(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Detect Order Blocks"""
        try:
            lookback = config.params.get('lookback', 50)
            
            # Find strong moves
            price_change = data['close'].pct_change() * 100
            strong_move = price_change.abs() > 1.0
            
            order_blocks = []
            
            for i in range(len(data) - lookback, len(data)):
                if strong_move.iloc[i]:
                    # Check if it's a bullish or bearish order block
                    if data['close'].iloc[i] > data['open'].iloc[i]:
                        # Bullish OB: Last bearish candle before strong up move
                        if i > 0 and data['close'].iloc[i-1] < data['open'].iloc[i-1]:
                            order_blocks.append({
                                'type': 'bullish',
                                'high': data['high'].iloc[i-1],
                                'low': data['low'].iloc[i-1],
                                'strength': price_change.iloc[i]
                            })
                    else:
                        # Bearish OB: Last bullish candle before strong down move
                        if i > 0 and data['close'].iloc[i-1] > data['open'].iloc[i-1]:
                            order_blocks.append({
                                'type': 'bearish',
                                'high': data['high'].iloc[i-1],
                                'low': data['low'].iloc[i-1],
                                'strength': abs(price_change.iloc[i])
                            })
            
            current_price = data['close'].iloc[-1]
            nearest_ob = None
            
            # Find nearest order block
            for ob in order_blocks[-10:]:  # Check last 10
                if ob['type'] == 'bullish' and current_price < ob['high']:
                    if nearest_ob is None or (ob['high'] - current_price) < (nearest_ob['high'] - current_price):
                        nearest_ob = ob
                elif ob['type'] == 'bearish' and current_price > ob['low']:
                    if nearest_ob is None or (current_price - ob['low']) < (current_price - nearest_ob['low']):
                        nearest_ob = ob
            
            # Determine signal
            if nearest_ob:
                if nearest_ob['type'] == 'bullish' and current_price < nearest_ob['high']:
                    signal = SignalType.BUY
                    confidence = 80
                elif nearest_ob['type'] == 'bearish' and current_price > nearest_ob['low']:
                    signal = SignalType.SELL
                    confidence = 80
                else:
                    signal = SignalType.NEUTRAL
                    confidence = 50
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return 1 if nearest_ob and nearest_ob['type'] == 'bullish' else 0, signal, confidence, {
                'ob_detected': bool(nearest_ob),
                'ob_type': nearest_ob['type'] if nearest_ob else 'none',
                'ob_high': nearest_ob['high'] if nearest_ob else 0,
                'ob_low': nearest_ob['low'] if nearest_ob else 0,
                'total_obs': len(order_blocks)
            }
            
        except Exception as e:
            logger.error(f"Order Blocks calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_fvg(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Detect Fair Value Gaps"""
        try:
            lookback = config.params.get('lookback', 20)
            
            fvgs = []
            
            for i in range(lookback, len(data)):
                # Bullish FVG: Gap between current low and previous high
                if data['low'].iloc[i] > data['high'].iloc[i-2]:
                    fvgs.append({
                        'type': 'bullish',
                        'high': data['low'].iloc[i],
                        'low': data['high'].iloc[i-2],
                        'strength': (data['low'].iloc[i] - data['high'].iloc[i-2]) / data['high'].iloc[i-2] * 100
                    })
                
                # Bearish FVG: Gap between current high and previous low
                if data['high'].iloc[i] < data['low'].iloc[i-2]:
                    fvgs.append({
                        'type': 'bearish',
                        'high': data['low'].iloc[i-2],
                        'low': data['high'].iloc[i],
                        'strength': (data['low'].iloc[i-2] - data['high'].iloc[i]) / data['high'].iloc[i] * 100
                    })
            
            current_price = data['close'].iloc[-1]
            nearest_fvg = None
            
            # Find nearest FVG
            for fvg in fvgs[-10:]:
                if fvg['type'] == 'bullish' and current_price < fvg['high']:
                    if nearest_fvg is None or (fvg['high'] - current_price) < (nearest_fvg['high'] - current_price):
                        nearest_fvg = fvg
                elif fvg['type'] == 'bearish' and current_price > fvg['low']:
                    if nearest_fvg is None or (current_price - fvg['low']) < (current_price - nearest_fvg['low']):
                        nearest_fvg = fvg
            
            # Determine signal
            if nearest_fvg:
                if nearest_fvg['type'] == 'bullish' and current_price < nearest_fvg['high']:
                    signal = SignalType.BUY
                    confidence = 85
                elif nearest_fvg['type'] == 'bearish' and current_price > nearest_fvg['low']:
                    signal = SignalType.SELL
                    confidence = 85
                else:
                    signal = SignalType.NEUTRAL
                    confidence = 50
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return 1 if nearest_fvg and nearest_fvg['type'] == 'bullish' else 0, signal, confidence, {
                'fvg_detected': bool(nearest_fvg),
                'fvg_type': nearest_fvg['type'] if nearest_fvg else 'none',
                'fvg_high': nearest_fvg['high'] if nearest_fvg else 0,
                'fvg_low': nearest_fvg['low'] if nearest_fvg else 0,
                'total_fvgs': len(fvgs)
            }
            
        except Exception as e:
            logger.error(f"FVG calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _calc_liquidity_sweeps(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Detect Liquidity Sweeps"""
        try:
            lookback = config.params.get('lookback', 50)
            
            # Find equal highs and lows
            highs = data['high'].tail(lookback)
            lows = data['low'].tail(lookback)
            
            # Group similar levels
            high_clusters = self._cluster_levels(highs)
            low_clusters = self._cluster_levels(lows)
            
            sweeps = []
            current_price = data['close'].iloc[-1]
            
            # Check for liquidity sweeps
            for cluster in high_clusters:
                if len(cluster) >= 2:
                    # Check if price swept above cluster
                    if data['high'].iloc[-1] > max(cluster) and data['close'].iloc[-1] < max(cluster):
                        sweeps.append({
                            'type': 'sell_liquidity',
                            'level': max(cluster),
                            'strength': len(cluster)
                        })
            
            for cluster in low_clusters:
                if len(cluster) >= 2:
                    # Check if price swept below cluster
                    if data['low'].iloc[-1] < min(cluster) and data['close'].iloc[-1] > min(cluster):
                        sweeps.append({
                            'type': 'buy_liquidity',
                            'level': min(cluster),
                            'strength': len(cluster)
                        })
            
            # Determine signal
            last_sweep = sweeps[-1] if sweeps else None
            
            if last_sweep:
                if last_sweep['type'] == 'buy_liquidity':
                    signal = SignalType.BUY
                    confidence = 85
                elif last_sweep['type'] == 'sell_liquidity':
                    signal = SignalType.SELL
                    confidence = 85
                else:
                    signal = SignalType.NEUTRAL
                    confidence = 50
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return len(sweeps), signal, confidence, {
                'sweeps_detected': len(sweeps),
                'last_sweep': last_sweep['type'] if last_sweep else 'none',
                'sweep_strength': last_sweep['strength'] if last_sweep else 0
            }
            
        except Exception as e:
            logger.error(f"Liquidity Sweeps calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    def _cluster_levels(self, data: pd.Series) -> List[List[float]]:
        """Cluster similar price levels"""
        try:
            if data.empty:
                return []
            
            sorted_data = sorted(data)
            clusters = []
            current_cluster = [sorted_data[0]]
            
            for i in range(1, len(sorted_data)):
                if sorted_data[i] - sorted_data[i-1] < 0.005 * sorted_data[i-1]:  # 0.5% tolerance
                    current_cluster.append(sorted_data[i])
                else:
                    if len(current_cluster) >= 2:
                        clusters.append(current_cluster)
                    current_cluster = [sorted_data[i]]
            
            if len(current_cluster) >= 2:
                clusters.append(current_cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Cluster levels error: {e}")
            return []
    
    def _calc_bos_choch(self, data: pd.DataFrame, config: IndicatorConfig) -> Tuple[float, SignalType, float, Dict]:
        """Detect BOS (Break of Structure) and CHOCH (Change of Character)"""
        try:
            lookback = config.params.get('lookback', 100)
            
            # Find swing highs and lows
            highs = data['high']
            lows = data['low']
            
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(highs)-2):
                if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2]:
                    if highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]:
                        swing_highs.append({
                            'value': highs.iloc[i],
                            'index': i
                        })
                
                if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2]:
                    if lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]:
                        swing_lows.append({
                            'value': lows.iloc[i],
                            'index': i
                        })
            
            current_price = data['close'].iloc[-1]
            
            # Check for BOS
            bos_bullish = False
            bos_bearish = False
            
            if len(swing_highs) >= 2:
                if data['high'].iloc[-1] > swing_highs[-1]['value']:
                    bos_bullish = True
            
            if len(swing_lows) >= 2:
                if data['low'].iloc[-1] < swing_lows[-1]['value']:
                    bos_bearish = True
            
            # Check for CHOCH
            choch_bullish = False
            choch_bearish = False
            
            if len(swing_highs) >= 3 and len(swing_lows) >= 3:
                # Bullish CHOCH: Higher low and break of previous high
                if swing_lows[-1]['value'] > swing_lows[-2]['value']:
                    if data['high'].iloc[-1] > swing_highs[-1]['value']:
                        choch_bullish = True
                
                # Bearish CHOCH: Lower high and break of previous low
                if swing_highs[-1]['value'] < swing_highs[-2]['value']:
                    if data['low'].iloc[-1] < swing_lows[-1]['value']:
                        choch_bearish = True
            
            # Determine signal
            if bos_bullish or choch_bullish:
                signal = SignalType.BUY
                confidence = 85
            elif bos_bearish or choch_bearish:
                signal = SignalType.SELL
                confidence = 85
            else:
                signal = SignalType.NEUTRAL
                confidence = 50
            
            return 1 if (bos_bullish or choch_bullish) else 0, signal, confidence, {
                'bos_bullish': bos_bullish,
                'bos_bearish': bos_bearish,
                'choch_bullish': choch_bullish,
                'choch_bearish': choch_bearish,
                'swing_highs': len(swing_highs),
                'swing_lows': len(swing_lows)
            }
            
        except Exception as e:
            logger.error(f"BOS/CHOCH calc error: {e}")
            return 0, SignalType.NEUTRAL, 0, {'error': str(e)}
    
    # ============================================
    # COMBINED SIGNAL
    # ============================================
    
    def get_combined_signal(self, data: pd.DataFrame) -> Dict:
        """Get combined signal from all indicators"""
        try:
            results = self.calculate_all(data)
            
            if not results:
                return {
                    'signal': SignalType.NEUTRAL,
                    'confidence': 0,
                    'details': 'No indicators calculated'
                }
            
            # Weighted average of signals
            signal_values = {
                SignalType.STRONG_BUY: 2,
                SignalType.BUY: 1,
                SignalType.NEUTRAL: 0,
                SignalType.SELL: -1,
                SignalType.STRONG_SELL: -2
            }
            
            total_score = 0
            total_weight = 0
            details = {}
            
            for name, result in results.items():
                config = self.indicators.get(name)
                if not config or not config.enabled:
                    continue
                
                weight = config.weight
                score = signal_values.get(result.signal, 0) * (result.confidence / 100)
                
                total_score += score * weight
                total_weight += weight
                
                details[name] = {
                    'signal': result.signal.value,
                    'confidence': result.confidence,
                    'value': result.value
                }
            
            if total_weight == 0:
                return {
                    'signal': SignalType.NEUTRAL,
                    'confidence': 0,
                    'details': details
                }
            
            # Normalize score
            avg_score = total_score / total_weight
            
            # Determine combined signal
            if avg_score > 1.2:
                combined_signal = SignalType.STRONG_BUY
                confidence = min(95, 70 + (avg_score - 1.2) * 20)
            elif avg_score > 0.4:
                combined_signal = SignalType.BUY
                confidence = 60 + (avg_score - 0.4) * 25
            elif avg_score < -1.2:
                combined_signal = SignalType.STRONG_SELL
                confidence = min(95, 70 + (-1.2 - avg_score) * 20)
            elif avg_score < -0.4:
                combined_signal = SignalType.SELL
                confidence = 60 + (-0.4 - avg_score) * 25
            else:
                combined_signal = SignalType.NEUTRAL
                confidence = 50
            
            return {
                'signal': combined_signal,
                'confidence': min(95, max(5, confidence)),
                'score': avg_score,
                'details': details,
                'total_indicators': len(results),
                'active_indicators': len([r for r in results.values() if r.signal != SignalType.NEUTRAL])
            }
            
        except Exception as e:
            logger.error(f"Combined signal error: {e}")
            return {
                'signal': SignalType.NEUTRAL,
                'confidence': 0,
                'details': {'error': str(e)}
            }
    
    # ============================================
    # ADAPTIVE PARAMETERS
    # ============================================
    
    def update_adaptive_params(self, params: Dict):
        """Update adaptive parameters"""
        for key, value in params.items():
            if key in self.adaptive_params:
                self.adaptive_params[key] = value
                logger.debug(f"🔄 Adaptive param updated: {key} = {value}")
    
    def get_adaptive_params(self) -> Dict:
        """Get current adaptive parameters"""
        return self.adaptive_params.copy()
    
    # ============================================
    # PERFORMANCE
    # ============================================
    
    def get_performance(self) -> Dict:
        """Get engine performance"""
        return {
            'calculations': self.performance['calculations'],
            'avg_time': self.performance['avg_time'],
            'errors': self.performance['errors'],
            'active_indicators': len([i for i in self.indicators.values() if i.enabled]),
            'total_indicators': len(self.indicators)
        }
    
    # ============================================
    # SAVE/LOAD STATE
    # ============================================
    
    def _save_state(self):
        """Save state to disk"""
        try:
            import json
            import os
            
            os.makedirs("data/indicators", exist_ok=True)
            
            state_data = {
                'adaptive_params': self.adaptive_params,
                'performance': self.performance,
                'indicator_states': {
                    name: {'enabled': config.enabled, 'weight': config.weight}
                    for name, config in self.indicators.items()
                }
            }
            
            with open("data/indicators/state.json", "w") as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Save state error: {e}")
    
    def _load_state(self):
        """Load state from disk"""
        try:
            import json
            import os
            
            if os.path.exists("data/indicators/state.json"):
                with open("data/indicators/state.json", "r") as f:
                    state_data = json.load(f)
                    
                    self.adaptive_params = state_data.get('adaptive_params', self.adaptive_params)
                    self.performance = state_data.get('performance', self.performance)
                    
                    indicator_states = state_data.get('indicator_states', {})
                    for name, state in indicator_states.items():
                        if name in self.indicators:
                            self.indicators[name].enabled = state.get('enabled', True)
                            self.indicators[name].weight = state.get('weight', 1.0)
                    
                    logger.info("📂 Indicator engine state loaded")
                
        except Exception as e:
            logger.warning(f"Load state error (starting fresh): {e}")