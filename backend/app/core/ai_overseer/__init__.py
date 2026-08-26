"""
AI Overseer - Trade Quality Filter and Market Analysis
Evaluates trade quality using multi-factor scoring
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import pandas as pd
import numpy as np


class MarketCondition(Enum):
    STRONG_TREND = "STRONG_TREND"
    WEAK_TREND = "WEAK_TREND"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"


class _Grade:
    def __init__(self, mn, mx, lbl):
        self.min_score = mn
        self.max_score = mx
        self.label = lbl


class TradeGrade:
    NO_TRADE = _Grade(0, 59, "NO_TRADE")
    WATCH = _Grade(60, 69, "WATCH")
    NORMAL = _Grade(70, 79, "NORMAL_ENTRY")
    HIGH_CONFIDENCE = _Grade(80, 89, "HIGH_CONFIDENCE")
    PREMIUM = _Grade(90, 100, "PREMIUM_SNIPER")

    @classmethod
    def from_score(cls, score: float):
        for g in [cls.PREMIUM, cls.HIGH_CONFIDENCE, cls.NORMAL, cls.WATCH, cls.NO_TRADE]:
            if g.min_score <= score <= g.max_score:
                return g
        return cls.NO_TRADE


@dataclass
class TradeScore:
    """Complete trade quality score"""
    total_score: float
    trend_score: float
    structure_score: float
    momentum_score: float
    volume_score: float
    volatility_score: float
    liquidity_score: float
    risk_reward_score: float
    grade: str
    should_trade: bool
    reasons: Dict[str, float]


class AIOverseer:
    """
    AI Trade Quality Filter
    Scores trades before execution to ensure only high-quality setups
    """

    def __init__(self, min_confidence: float = 70.0, min_risk_reward: float = 2.0):
        self.min_confidence = min_confidence
        self.min_risk_reward = min_risk_reward
        self.daily_loss_limit = 0.03  # 3% daily loss limit
        self.max_consecutive_losses = 3
        self.max_open_positions = 5
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.open_positions = 0
        self.is_trading_enabled = True

    def analyze_market(self, data: pd.DataFrame) -> Dict:
        """Complete market analysis"""
        if data is None or len(data) < 50:
            return {'condition': MarketCondition.LOW_LIQUIDITY, 'trend_strength': 0}

        # Calculate indicators
        atr = self._calc_atr(data)
        adx = self._calc_adx(data)
        rsi = self._calc_rsi(data)
        volume_sma = data['volume'].rolling(20).mean()

        # Trend strength
        ema_fast = data['close'].ewm(span=20).mean()
        ema_slow = data['close'].ewm(span=50).mean()
        trend_direction = 1 if ema_fast.iloc[-1] > ema_slow.iloc[-1] else -1
        trend_strength = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0

        # Volatility
        current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
        avg_atr = atr.mean()
        volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1

        # Liquidity
        current_volume = data['volume'].iloc[-1]
        avg_volume = volume_sma.iloc[-1] if not pd.isna(volume_sma.iloc[-1]) else current_volume
        liquidity_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # Market condition classification
        condition = self._classify_market(trend_strength, volatility_ratio, adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0)

        return {
            'condition': condition,
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'atr': current_atr,
            'volatility_ratio': volatility_ratio,
            'liquidity_ratio': liquidity_ratio,
            'rsi': rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50,
            'ema_fast': ema_fast.iloc[-1],
            'ema_slow': ema_slow.iloc[-1]
        }

    def score_trade(self, data: pd.DataFrame, side: str, entry_price: float,
                   stop_loss: float, take_profit: float) -> TradeScore:
        """Score a potential trade"""
        market = self.analyze_market(data)
        reasons = {}

        # 1. Trend Score (0-20 points)
        trend_score = self._score_trend(market, side)
        reasons['trend'] = trend_score

        # 2. Structure Score (0-15 points)
        structure_score = self._score_structure(data, side, entry_price)
        reasons['structure'] = structure_score

        # 3. Momentum Score (0-15 points)
        momentum_score = self._score_momentum(data, side)
        reasons['momentum'] = momentum_score

        # 4. Volume Score (0-10 points)
        volume_score = self._score_volume(data)
        reasons['volume'] = volume_score

        # 5. Volatility Score (0-10 points)
        volatility_score = self._score_volatility(market)
        reasons['volatility'] = volatility_score

        # 6. Liquidity Score (0-10 points)
        liquidity_score = self._score_liquidity(market)
        reasons['liquidity'] = liquidity_score

        # 7. Risk/Reward Score (0-20 points)
        risk_reward_score = self._score_risk_reward(entry_price, stop_loss, take_profit, side)
        reasons['risk_reward'] = risk_reward_score

        total_score = (trend_score + structure_score + momentum_score +
                      volume_score + volatility_score + liquidity_score + risk_reward_score)

        grade = TradeGrade.from_score(total_score)
        should_trade = (total_score >= self.min_confidence and
                       risk_reward_score >= 12 and  # At least 12/20 on R:R
                       self.is_trading_enabled and
                       self.open_positions < self.max_open_positions)

        return TradeScore(
            total_score=total_score,
            trend_score=trend_score,
            structure_score=structure_score,
            momentum_score=momentum_score,
            volume_score=volume_score,
            volatility_score=volatility_score,
            liquidity_score=liquidity_score,
            risk_reward_score=risk_reward_score,
            grade=grade.label,
            should_trade=should_trade,
            reasons=reasons
        )

    def calculate_adaptive_stop_loss(self, data: pd.DataFrame, side: str,
                                    entry_price: float, atr: float) -> float:
        """Calculate adaptive stop loss based on ATR and market structure"""
        if side == 'BUY':
            # Find recent swing low
            recent_lows = data['low'].rolling(10, center=True).min()
            structure_low = recent_lows.iloc[-10:].min()
            
            # ATR-based stop
            atr_stop = entry_price - (atr * 1.5)
            
            # Use the higher of structure-based or ATR-based stop
            stop = max(structure_low, atr_stop)
            
            # Ensure stop is not too far (max 3% for most markets)
            max_stop_distance = entry_price * 0.03
            stop = max(stop, entry_price - max_stop_distance)
        else:
            recent_highs = data['high'].rolling(10, center=True).max()
            structure_high = recent_highs.iloc[-10:].max()
            
            atr_stop = entry_price + (atr * 1.5)
            stop = min(structure_high, atr_stop)
            
            max_stop_distance = entry_price * 0.03
            stop = min(stop, entry_price + max_stop_distance)
        
        return stop

    def calculate_smart_take_profit(self, data: pd.DataFrame, side: str,
                                   entry_price: float, stop_loss: float,
                                   market_condition: MarketCondition) -> Dict:
        """Calculate multi-stage take profit"""
        risk = abs(entry_price - stop_loss)
        
        # Adjust targets based on market condition
        if market_condition == MarketCondition.STRONG_TREND:
            tp1_mult = 2.0
            tp2_mult = 3.5
            runner_mult = 5.0
        elif market_condition == MarketCondition.WEAK_TREND:
            tp1_mult = 1.5
            tp2_mult = 2.5
            runner_mult = 3.5
        elif market_condition == MarketCondition.RANGING:
            tp1_mult = 1.5
            tp2_mult = 2.0
            runner_mult = 2.5
        elif market_condition == MarketCondition.HIGH_VOLATILITY:
            tp1_mult = 2.5
            tp2_mult = 4.0
            runner_mult = 6.0
        else:
            tp1_mult = 2.0
            tp2_mult = 3.0
            runner_mult = 4.0
        
        if side == 'BUY':
            tp1 = entry_price + (risk * tp1_mult)
            tp2 = entry_price + (risk * tp2_mult)
            runner = entry_price + (risk * runner_mult)
        else:
            tp1 = entry_price - (risk * tp1_mult)
            tp2 = entry_price - (risk * tp2_mult)
            runner = entry_price - (risk * runner_mult)
        
        return {
            'tp1': tp1,  # Take 25% here
            'tp2': tp2,  # Take 25% here
            'runner': runner,  # Let 50% run
            'tp1_size': 0.25,
            'tp2_size': 0.25,
            'runner_size': 0.50
        }

    def calculate_profit_lock(self, current_price: float, entry_price: float,
                             highest_profit: float, atr: float, side: str) -> Dict:
        """Calculate dynamic profit lock levels"""
        if side == 'BUY':
            current_profit_pct = (current_price - entry_price) / entry_price * 100
        else:
            current_profit_pct = (entry_price - current_price) / entry_price * 100
        
        # Milestones for profit locking
        milestones = {
            1.0: 0.25,   # At 1% profit, lock 25% of position
            2.0: 0.40,   # At 2% profit, lock 40% of position
            4.0: 0.60,   # At 4% profit, lock 60% of position
            6.0: 0.75,   # At 6% profit, lock 75% of position
            10.0: 0.85   # At 10% profit, lock 85% of position
        }
        
        locked_pct = 0
        for milestone_pct, lock_pct in milestones.items():
            if current_profit_pct >= milestone_pct:
                locked_pct = lock_pct
        
        # Trailing lock based on ATR
        if current_profit_pct > 0:
            trailing_distance = atr * 1.5
            if side == 'BUY':
                lock_price = current_price - trailing_distance
            else:
                lock_price = current_price + trailing_distance
        else:
            lock_price = entry_price
        
        # Lock price can only move up (never backward)
        lock_price = max(lock_price, entry_price)
        
        return {
            'locked_percentage': locked_pct,
            'lock_price': lock_price,
            'current_profit_pct': current_profit_pct,
            'should_lock': locked_pct > 0
        }

    def _score_trend(self, market: Dict, side: str) -> float:
        """Score trend alignment (0-20 points)"""
        score = 0
        trend_direction = market.get('trend_direction', 0)
        trend_strength = market.get('trend_strength', 0)
        
        # Trade with trend
        if (side == 'BUY' and trend_direction > 0) or (side == 'SELL' and trend_direction < 0):
            score += 10
            
            # Bonus for strong trend
            if trend_strength > 30:
                score += 10
            elif trend_strength > 25:
                score += 7
            elif trend_strength > 20:
                score += 5
        else:
            # Counter-trend trade - reduced score
            if trend_strength < 20:
                score += 5  # OK if no clear trend
            else:
                score += 2  # Penalty for strong counter-trend
        
        return min(20, score)

    def _score_structure(self, data: pd.DataFrame, side: str, entry: float) -> float:
        """Score market structure (0-15 points)"""
        score = 0
        recent_high = data['high'].iloc[-20:].max()
        recent_low = data['low'].iloc[-20:].min()
        
        if side == 'BUY':
            # Buying near support
            distance_from_low = (entry - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5
            if distance_from_low < 0.3:
                score = 15  # Near strong support
            elif distance_from_low < 0.4:
                score = 12
            elif distance_from_low < 0.5:
                score = 8
            else:
                score = 4
        else:
            # Selling near resistance
            distance_from_high = (recent_high - entry) / (recent_high - recent_low) if recent_high > recent_low else 0.5
            if distance_from_high < 0.3:
                score = 15  # Near strong resistance
            elif distance_from_high < 0.4:
                score = 12
            elif distance_from_high < 0.5:
                score = 8
            else:
                score = 4
        
        return score

    def _score_momentum(self, data: pd.DataFrame, side: str) -> float:
        """Score momentum (0-15 points)"""
        score = 0
        rsi = self._calc_rsi(data)
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        if side == 'BUY':
            if 40 < current_rsi < 60:
                score = 15  # Fresh momentum
            elif 30 < current_rsi < 70:
                score = 10
            elif current_rsi < 30:
                score = 12  # Oversold - potential reversal
            else:
                score = 5   # Overbought - avoid
        else:
            if 40 < current_rsi < 60:
                score = 15
            elif 30 < current_rsi < 70:
                score = 10
            elif current_rsi > 70:
                score = 12  # Overbought - potential reversal
            else:
                score = 5
        
        return score

    def _score_volume(self, data: pd.DataFrame) -> float:
        """Score volume confirmation (0-10 points)"""
        score = 5  # Neutral default
        vol_sma = data['volume'].rolling(20).mean()
        current_vol = data['volume'].iloc[-1]
        avg_vol = vol_sma.iloc[-1]
        
        if avg_vol > 0:
            vol_ratio = current_vol / avg_vol
            if vol_ratio > 1.5:
                score = 10  # Strong volume
            elif vol_ratio > 1.2:
                score = 8
            elif vol_ratio > 0.8:
                score = 6
            else:
                score = 3  # Low volume
        
        return score

    def _score_volatility(self, market: Dict) -> float:
        """Score volatility conditions (0-10 points)"""
        vol_ratio = market.get('volatility_ratio', 1)
        
        if 0.8 < vol_ratio < 1.5:
            return 10  # Normal volatility
        elif 0.5 < vol_ratio < 2.0:
            return 7
        elif vol_ratio >= 2.0:
            return 4  # Too volatile
        else:
            return 3  # Too flat

    def _score_liquidity(self, market: Dict) -> float:
        """Score liquidity (0-10 points)"""
        liq_ratio = market.get('liquidity_ratio', 1)
        
        if liq_ratio > 1.2:
            return 10  # High liquidity
        elif liq_ratio > 0.8:
            return 7
        elif liq_ratio > 0.5:
            return 4
        else:
            return 1  # Low liquidity - avoid

    def _score_risk_reward(self, entry: float, sl: float, tp: float, side: str) -> float:
        """Score risk/reward ratio (0-20 points)"""
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        
        if risk <= 0:
            return 0
        
        rr_ratio = reward / risk
        
        if rr_ratio >= 4.0:
            return 20
        elif rr_ratio >= 3.0:
            return 18
        elif rr_ratio >= 2.5:
            return 15
        elif rr_ratio >= 2.0:
            return 12
        elif rr_ratio >= 1.5:
            return 8
        elif rr_ratio >= 1.0:
            return 4
        else:
            return 0

    def _classify_market(self, trend_strength: float, volatility: float, adx: float) -> MarketCondition:
        """Classify current market condition"""
        if adx > 30:
            return MarketCondition.STRONG_TREND
        elif adx > 20:
            return MarketCondition.WEAK_TREND
        elif volatility > 2.0:
            return MarketCondition.HIGH_VOLATILITY
        elif volatility < 0.5:
            return MarketCondition.LOW_VOLATILITY
        else:
            return MarketCondition.RANGING

    def _calc_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        tr = pd.concat([
            data['high'] - data['low'],
            abs(data['high'] - data['close'].shift()),
            abs(data['low'] - data['close'].shift())
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def _calc_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / (loss + 0.0001)
        return 100 - (100 / (1 + rs))

    def _calc_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        plus_dm = data['high'].diff()
        minus_dm = -data['low'].diff()
        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0)
        minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0)
        atr = self._calc_atr(data, period)
        plus_di = 100 * (plus_dm.rolling(period).mean() / (atr + 0.0001))
        minus_di = 100 * (minus_dm.rolling(period).mean() / (atr + 0.0001))
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
        return dx.rolling(period).mean()
