"""
Shared AI Signal Gate — single entry point used by ALL 13 bots.

Routes every candidate trade through:
  MasterTradeFilter -> SmartEntryEngine (TP1/TP2/runner plan)
and only returns a TradeSignal when the master filter says EXECUTE.
This guarantees every bot shares the same professional risk core.
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from ..core.master_trade_filter import MasterTradeFilter, Decision
from ..core.smart_entry import SmartEntryEngine, SmartPlan
from ..core.ai_overseer import MarketCondition
from .base_bot import TradeSignal, TradeQuality, SignalStrength


class AiSignalGate:
    """Reusable master-filter gate for strategy bots."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.cfg = config or {}
        self.filter = MasterTradeFilter(self.cfg.get('filter', {}))
        self.entry = SmartEntryEngine(self.cfg.get('min_rr', 2.0))

    def price_array(self, df) -> np.ndarray:
        try:
            return np.asarray(df['close'].values, dtype=float)
        except Exception:
            return np.array([])

    def volume_array(self, df) -> np.ndarray:
        try:
            return np.asarray(df['volume'].values, dtype=float)
        except Exception:
            return np.array([])

    def score_signal(self, df, direction: str = "NEUTRAL"):
        if df is None or len(df) < 15:
            return None
        entry = float(df['close'].iloc[-1])
        atr_series = self.filter.ai._calc_atr(df)
        atr = float(atr_series.iloc[-1]) if not pd.isna(atr_series.iloc[-1]) else entry * 0.01
        atr = max(atr, entry * 0.0001)
        side = direction if direction in {"BUY", "SELL"} else ("BUY" if df['close'].iloc[-1] >= df['close'].iloc[-2] else "SELL")
        stop_loss = entry - atr * 1.5 if side == "BUY" else entry + atr * 1.5
        take_profit = entry + atr * 3.0 if side == "BUY" else entry - atr * 3.0
        return self.filter.ai.score_trade(df, side, entry, stop_loss, take_profit)

    def regime_of(self, mtf_data: Dict[str, pd.DataFrame]):
        return self.filter.classify_regime(mtf_data)

    def make_signal(self, mtf_data: Dict[str, pd.DataFrame], side: str,
                   entry_price: float, reason: str,
                   indicators=None, metadata=None,
                   symbol: str = "UNKNOWN", risk_pct: float = 1.0,
                   spread_pct: float = 0.0, liquidity_ok: bool = True,
                   news_risk: bool = False, atr: Optional[float] = None,
                   structure_sl: Optional[float] = None) -> Optional[TradeSignal]:
        """Run the full gated path. Returns None if rejected."""
        regime = self.filter.classify_regime(mtf_data)
        reg_name = regime.value if hasattr(regime, 'value') else str(regime)
        if atr is None:
            score_df = mtf_data.get('1h') or mtf_data.get('15m') or next(iter(mtf_data.values()))
            atr = self.filter.ai._calc_atr(score_df).iloc[-1]
        plan: SmartPlan = self.entry.build_plan(side, entry_price, atr, reg_name, structure_sl)

        fr = self.filter.evaluate(mtf_data, side, entry_price, plan.sl, plan.tp1,
                                  symbol=symbol, risk_pct=risk_pct,
                                  spread_pct=spread_pct, liquidity_ok=liquidity_ok,
                                  news_risk=news_risk)
        if fr.decision != Decision.EXECUTE:
            return None

        score = fr.score
        quality = (TradeQuality.PERFECT if score >= 85
                   else TradeQuality.EXCELLENT if score >= 75
                   else TradeQuality.GOOD if score >= 65
                   else TradeQuality.AVERAGE)
        strength = (SignalStrength.VERY_STRONG if score >= 85
                    else SignalStrength.STRONG if score >= 75
                    else SignalStrength.MODERATE)
        meta = dict(metadata or {})
        meta.update({'tp1': plan.tp1, 'tp2': plan.tp2, 'runner': plan.runner,
                     'score': score, 'regime': reg_name, 'rr': fr.rr})
        return TradeSignal(
            action=side,
            confidence=score,
            strength=strength,
            quality=quality,
            entry_price=entry_price,
            stop_loss=plan.sl,
            take_profit=plan.tp2,   # runner target documented in metadata
            position_size=self.cfg.get('position_size', 100),
            reason=reason,
            supporting_indicators=indicators or [],
            ai_reasoning=f"score={score:.0f} regime={reg_name} rr={fr.rr:.2f}",
            risk_score=100 - score,
            expected_return=abs(plan.tp2 - entry_price) / entry_price * 100,
            time_horizon=self.cfg.get('time_horizon', 'MEDIUM'),
            metadata=meta,
        )
