# backend/app/bots/forex/enhanced_forex_bot.py
# ============================================
# ENHANCED FOREX BOT - Smart Multi-Pair Forex Trader
# ============================================
# Features: SmartEntryEngine (min_rr=2.5), ADX trend filter (>=18),
#           Volume confirmation, EMA100 trend filter,
#           Session killzone filter (London 7-10 UTC, NY 13-16 UTC),
#           7 major pairs, full TradeSignal output with metadata.
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from loguru import logger

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality
from ...core.smart_entry import SmartEntryEngine


class EnhancedForexBot(BaseBot):
    """
    Enhanced Forex Bot.
    Scans 7 major pairs, applies a layered filter stack (session killzone,
    ADX, EMA100 trend, volume) and routes surviving setups through the
    SmartEntryEngine to produce asymmetric, high-RR trade plans.
    """

    PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]

    def __init__(self, config: Dict[str, Any]):
        super().__init__("Enhanced Forex", config)
        self.pairs = config.get('pairs', self.PAIRS)
        self.adx_threshold = config.get('adx_threshold', 18)
        self.ema_slow = config.get('ema_slow', 100)
        self.volume_mult = config.get('volume_mult', 1.2)
        self.min_rr = config.get('min_rr', 2.5)
        self.engine = SmartEntryEngine(min_rr=self.min_rr)
        self.entry_tf = config.get('entry_tf', '15m')
        self.risk_pct = config.get('risk_pct', 1.0)
        self.max_signals = config.get('max_signals', 3)
        self.performance_metrics.update({
            'scanned_pairs': 0,
            'signals_generated': 0,
            'filtered_session': 0,
            'filtered_adx': 0,
            'filtered_trend': 0,
            'filtered_volume': 0,
        })
        logger.info(f"Enhanced Forex Bot initialized for {len(self.pairs)} pairs "
                    f"(ADX>={self.adx_threshold}, EMA{self.ema_slow}, RR>={self.min_rr})")

    # ============ SESSION KILLZONE ============

    @staticmethod
    def _in_killzone(dt: Optional[datetime] = None) -> bool:
        """London 7-10 UTC, New York 13-16 UTC."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        h = dt.hour
        return (7 <= h < 10) or (13 <= h < 16)

    # ============ INDICATORS ============

    @staticmethod
    def _ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        try:
            high, low, close = df['high'], df['low'], df['close']
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()
            up = high.diff()
            dn = -low.diff()
            plus_dm = up.where((up > 0) & (up > dn.abs()), 0.0)
            minus_dm = dn.where((dn > 0) & (dn > up.abs()), 0.0)
            plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
            dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
            return dx.rolling(period).mean().fillna(0.0)
        except Exception:
            return pd.Series([0.0] * len(df))

    @staticmethod
    def _atr(df: pd.DataFrame, period: int = 14) -> float:
        try:
            tr = pd.concat([
                df['high'] - df['low'],
                (df['high'] - df['close'].shift()).abs(),
                (df['low'] - df['close'].shift()).abs()
            ], axis=1).max(axis=1)
            return float(tr.rolling(period).mean().iloc[-1])
        except Exception:
            return 0.0

    # ============ FILTERS ============

    def _passes_filters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run the layered filter stack. Returns verdict + diagnostics."""
        res = {'ok': False, 'direction': None, 'adx': 0.0, 'ema100': 0.0,
               'volume_ok': False, 'price': 0.0, 'atr': 0.0}
        try:
            if len(df) < 110:
                return res
            price = float(df['close'].iloc[-1])
            ema100 = float(self._ema(df['close'], self.ema_slow).iloc[-1])
            adx = float(self._adx(df).iloc[-1])
            atr = self._atr(df)
            res.update({'price': price, 'adx': adx, 'ema100': ema100, 'atr': atr})

            # 1) EMA100 trend filter
            if price > ema100:
                direction = "BUY"
            elif price < ema100:
                direction = "SELL"
            else:
                self.performance_metrics['filtered_trend'] += 1
                return res
            res['direction'] = direction

            # 2) ADX trend strength filter
            if adx < self.adx_threshold:
                self.performance_metrics['filtered_adx'] += 1
                return res

            # 3) Volume confirmation
            if 'volume' in df.columns:
                vol = df['volume']
                avg = vol.rolling(20).mean().iloc[-1]
                vol_ok = float(vol.iloc[-1]) > float(avg) * self.volume_mult
            else:
                vol_ok = True
            res['volume_ok'] = vol_ok
            if not vol_ok:
                self.performance_metrics['filtered_volume'] += 1
                return res

            res['ok'] = True
            return res
        except Exception as e:
            logger.error(f"Filter error: {e}")
            return res

    # ============ SIGNAL GENERATION ============

    def generate_signal(self, data: pd.DataFrame, pair: str) -> Optional[TradeSignal]:
        """
        Generate a single trade signal for `pair` given its OHLCV `data`.
        Returns None when filters reject the setup.
        """
        try:
            if not self._in_killzone():
                self.performance_metrics['filtered_session'] += 1
                return None

            f = self._passes_filters(data)
            if not f['ok']:
                return None

            direction = f['direction']
            entry = f['price']
            atr = f['atr']
            if atr <= 0:
                atr = entry * 0.0008

            plan = self.engine.build_plan(direction, entry, atr, regime="STRONG_TREND")
            rr = abs(plan.tp2 - entry) / abs(entry - plan.sl) if plan.sl != entry else 0.0
            if rr < self.min_rr:
                return None

            confidence = min(95.0, 55 + f['adx'] + (20 if f['volume_ok'] else 0))
            strength = (SignalStrength.VERY_STRONG if confidence >= 85
                        else SignalStrength.STRONG if confidence >= 75
                        else SignalStrength.MODERATE)
            quality = (TradeQuality.EXCELLENT if confidence >= 80
                       else TradeQuality.GOOD if confidence >= 65
                       else TradeQuality.AVERAGE)
            pips = entry * 100 if pair.endswith('JPY') else entry * 10000

            signal = TradeSignal(
                action=direction,
                confidence=round(confidence, 1),
                strength=strength,
                quality=quality,
                entry_price=round(entry, 5),
                stop_loss=round(plan.sl, 5),
                take_profit=round(plan.tp2, 5),
                position_size=round(100000 * (self.risk_pct / 100.0), 2),
                reason=f"{direction} {pair} EMA100+ADX({f['adx']:.0f}) killzone",
                supporting_indicators=['EMA100', 'ADX', 'Volume', 'SmartEntry'],
                ai_reasoning=(f"trend={direction} adx={f['adx']:.1f} "
                              f"ema100={f['ema100']:.5f} vol={f['volume_ok']} rr={rr:.2f}"),
                risk_score=round(100 - confidence, 1),
                expected_return=round(abs(plan.tp2 - entry) / entry * 100, 3),
                time_horizon="INTRADAY",
                metadata={
                    'pair': pair,
                    'session': 'London/NY killzone',
                    'adx': round(f['adx'], 2),
                    'ema100': round(f['ema100'], 5),
                    'volume_confirmed': f['volume_ok'],
                    'atr': round(atr, 5),
                    'tp1': round(plan.tp1, 5),
                    'tp2': round(plan.tp2, 5),
                    'runner_target': round(plan.tp2, 5),
                    'risk_reward': round(rr, 2),
                    'pip_value': round(pips, 1),
                    'entry_time_utc': datetime.now(timezone.utc).isoformat(),
                },
            )
            self.performance_metrics['signals_generated'] += 1
            return signal
        except Exception as e:
            logger.error(f"generate_signal error {pair}: {e}")
            return None

    # ============ SCAN ALL PAIRS ============

    def scan_all_pairs(self, data_dict: Dict[str, pd.DataFrame]) -> List[TradeSignal]:
        """
        Scan a dict {pair: ohlcv_df}, returning up to `max_signals`
        ranked TradeSignals (best R:R first).
        """
        self.performance_metrics['scanned_pairs'] = len(data_dict)
        signals: List[TradeSignal] = []
        try:
            for pair, df in data_dict.items():
                if pair not in self.pairs:
                    continue
                sig = self.generate_signal(df, pair)
                if sig is not None:
                    signals.append(sig)
            signals.sort(key=lambda s: s.metadata.get('risk_reward', 0.0), reverse=True)
            return signals[: self.max_signals]
        except Exception as e:
            logger.error(f"scan_all_pairs error: {e}")
            return signals

    # ============ CONVENIENCE ============

    def get_strategies(self) -> List[str]:
        return ['killzone_trend', 'adx_momentum', 'smart_entry_rr']

    def get_indicators(self) -> List[str]:
        return ['EMA100', 'ADX(18)', 'Volume', 'ATR', 'SmartEntryEngine']
