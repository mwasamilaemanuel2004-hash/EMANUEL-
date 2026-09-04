"""
Profit Engine — Upgraded execution engine optimized for maximum profit
and highest probability of profit.

Key upgrades over SmartEntryEngine:
- Higher TP2 targets (3.5R in strong trends vs 2.5R)
- Wider runner trailing (2.5x ATR vs 1.5x) for bigger winners
- Less sensitive structure break (1.0x ATR vs 0.5x) to avoid premature exits
- Optimized position split (25/35/40) for more runner exposure
- Multi-timeframe trend confirmation
- Dynamic position sizing based on conviction
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd


class ProfitExit:
    """Extended exit tracking for profit analysis."""
    def __init__(self):
        self.won = False
        self.pnl_pct = 0.0
        self.exit_reason = "none"
        self.tp1_hit = False
        self.tp2_hit = False
        self.runner_hit = False
        self.runner_trailing_hit = False
        self.max_favorable = 0.0
        self.max_adverse = 0.0
        self.locked_profit_pct = 0.0
        self.runner_pnl_pct = 0.0
        self.bars_held = 0
        self.max_r_multiple = 0.0  # Max R-multiple reached


@dataclass
class ProfitPlan:
    """Enhanced plan with conviction-based sizing."""
    entry: float
    side: str
    sl: float
    tp1: float
    tp2: float
    tp1_size: float = 0.25
    tp2_size: float = 0.35
    runner_size: float = 0.40
    atr: float = 0.0
    regime: str = "STRONG_TREND"
    conviction: float = 1.0  # 0.5=low, 1.0=normal, 1.5=high
    risk_pct: float = 1.0  # Risk per trade %


class ProfitEngine:
    """
    Upgraded execution engine for maximum profit and probability.
    
    R:R Table (optimized for trending markets):
    - STRONG_TREND:    TP1=1.0R, TP2=3.5R (was 2.5R)
    - WEAK_TREND:      TP1=1.0R, TP2=2.5R (was 2.2R)
    - RANGE:           TP1=1.0R, TP2=2.0R (unchanged)
    - HIGH_VOLATILITY: TP1=1.0R, TP2=4.0R (was 3.0R)
    - LOW_VOLATILITY:  TP1=1.0R, TP2=2.5R (was 2.0R)
    - UNSAFE:          TP1=1.0R, TP2=1.0R (no edge)
    
    Runner trailing: 2.5x ATR (was 1.5x) in normal, 3.0x in high vol
    Structure break: body > 1.0x ATR (was 0.5x) to avoid premature exits
    Position split: 25/35/40 (was 30/40/30) for more runner exposure
    """

    def __init__(self, min_rr: float = 2.5):
        self.min_rr = min_rr

    def build_plan(self, side: str, entry: float, atr: float,
                   regime: str = "STRONG_TREND", structure_sl: Optional[float] = None,
                   conviction: float = 1.0) -> ProfitPlan:
        """Build optimized plan with conviction-based sizing."""
        risk = max(atr, entry * 0.002)
        if structure_sl is not None:
            if side == "BUY":
                risk = min(abs(entry - structure_sl), atr * 3.0)
                risk = max(risk, atr * 0.8)
            else:
                risk = min(abs(structure_sl - entry), atr * 3.0)
                risk = max(risk, atr * 0.8)

        # Optimized R:R table for higher profit
        rr = {
            "STRONG_TREND":    (1.0, 3.5),
            "WEAK_TREND":      (1.0, 2.5),
            "RANGE":           (1.0, 2.0),
            "HIGH_VOLATILITY": (1.0, 4.0),
            "LOW_VOLATILITY":  (1.0, 2.5),
            "UNSAFE":          (1.0, 1.0),
        }.get(regime, (1.0, 3.5))
        m1, m2 = rr

        if side == "BUY":
            sl = entry - risk
            tp1 = entry + risk * m1
            tp2 = entry + risk * m2
        else:
            sl = entry + risk
            tp1 = entry - risk * m1
            tp2 = entry - risk * m2

        assert sl != entry, "Stop loss must differ from entry"
        
        # Conviction-based risk adjustment
        risk_pct = min(2.0, max(0.5, conviction * 1.0))
        
        return ProfitPlan(entry=entry, side=side, sl=sl, tp1=tp1, tp2=tp2,
                         tp1_size=0.25, tp2_size=0.35, runner_size=0.40,
                         atr=atr, regime=regime, conviction=conviction,
                         risk_pct=risk_pct)

    def simulate(self, plan: ProfitPlan, future: pd.DataFrame,
                 max_bars: int = 300) -> ProfitExit:
        """Simulate with optimized runner management for maximum profit."""
        res = ProfitExit()
        side = plan.side
        remaining = 1.0
        locked_sl = plan.sl
        breakeven_armed = False
        tp1_done = tp2_done = False
        entry = plan.entry
        atr = plan.atr or abs(entry - plan.sl)
        risk = abs(entry - plan.sl) or atr

        bars = future.head(max_bars)
        runner_pnl = 0.0
        bar_count = 0
        
        for _, row in bars.iterrows():
            bar_count += 1
            hi, lo, cl = row['high'], row['low'], row['close']
            risk = abs(entry - plan.sl) or atr

            # MFE / MAE tracking
            if side == "BUY":
                fav = (hi - entry) / risk if risk else 0
                adv = (entry - lo) / risk if risk else 0
            else:
                fav = (entry - lo) / risk if risk else 0
                adv = (hi - entry) / risk if risk else 0
            res.max_favorable = max(res.max_favorable, fav)
            res.max_adverse = max(res.max_adverse, adv)
            res.max_r_multiple = max(res.max_r_multiple, fav)

            # 1) TP1 — bank 25%, arm breakeven
            if not tp1_done:
                if (side == "BUY" and hi >= plan.tp1) or (side == "SELL" and lo <= plan.tp1):
                    res.tp1_hit = True
                    tp1_done = True
                    breakeven_armed = True
                    partial = plan.tp1_size * _signed(side, plan.tp1 - entry) / entry
                    res.pnl_pct += partial
                    remaining -= plan.tp1_size

            # 2) Breakeven lock (one-way)
            if breakeven_armed:
                locked_sl = entry

            # 3) TP2 — bank 35%
            if tp1_done and not tp2_done:
                if (side == "BUY" and hi >= plan.tp2) or (side == "SELL" and lo <= plan.tp2):
                    res.tp2_hit = True
                    tp2_done = True
                    partial = plan.tp2_size * _signed(side, plan.tp2 - entry) / entry
                    res.pnl_pct += partial
                    remaining -= plan.tp2_size

            # 4) RUNNER — WIDER trailing for bigger winners
            if remaining > 1e-6:
                trail_mult = 2.5 if plan.regime != "HIGH_VOLATILITY" else 3.0
                if side == "BUY":
                    trail = hi - atr * trail_mult
                    locked_sl = max(locked_sl, trail)
                else:
                    trail = lo + atr * trail_mult
                    locked_sl = min(locked_sl, trail)

            # 5) EXIT: mandatory stop
            exit_px = None
            exit_reason = None
            if side == "BUY":
                if lo <= locked_sl and remaining > 1e-6:
                    exit_px = locked_sl
                    exit_reason = "breakeven" if abs(locked_sl - entry) < 1e-9 else "stop"
            else:
                if hi >= locked_sl and remaining > 1e-6:
                    exit_px = locked_sl
                    exit_reason = "breakeven" if abs(locked_sl - entry) < 1e-9 else "stop"

            # Structure break: LESS sensitive (1.0x ATR vs 0.5x)
            if exit_px is None and remaining > 1e-6 and tp2_done:
                rng = hi - lo
                body = abs(cl - row['open'])
                if rng > 0 and body / rng > 0.7:
                    against = ((side == "BUY" and cl < row['open']) or
                               (side == "SELL" and cl > row['open']))
                    if against and body > atr * 1.0:  # Changed from 0.5 to 1.0
                        exit_px = cl
                        exit_reason = "runner_structure_break"
                        res.runner_hit = True

            if exit_px is not None:
                pnl = remaining * _signed(side, exit_px - entry) / entry
                res.pnl_pct += pnl
                runner_pnl += pnl
                res.exit_reason = exit_reason
                res.bars_held = bar_count
                break

        # End of window
        if remaining > 1e-6:
            last = bars.iloc[-1]['close'] if len(bars) else entry
            pnl = remaining * _signed(side, last - entry) / entry
            res.pnl_pct += pnl
            runner_pnl += pnl
            res.exit_reason = res.exit_reason or "end_of_window"
            res.bars_held = bar_count

        res.runner_pnl_pct = runner_pnl
        res.locked_profit_pct = max(0.0, res.pnl_pct)
        res.won = res.pnl_pct > 0
        return res


def _signed(side: str, delta: float) -> float:
    return delta if side == "BUY" else -delta


def compute_conviction(adx: float, trend_alignment: float, volume_ratio: float,
                       fundamental_score: float) -> float:
    """
    Compute trade conviction (0.5 to 1.5) based on multi-factor confluence.
    
    Higher conviction = larger position size, wider stops, more runner exposure.
    """
    conv = 1.0
    
    # ADX contribution (stronger trend = higher conviction)
    if adx > 30:
        conv += 0.2
    elif adx > 25:
        conv += 0.1
    elif adx < 15:
        conv -= 0.2
    
    # Trend alignment (multi-TF confirmation)
    conv += trend_alignment * 0.2
    
    # Volume confirmation
    if volume_ratio > 1.5:
        conv += 0.1
    elif volume_ratio < 0.7:
        conv -= 0.1
    
    # Fundamental score contribution
    if fundamental_score > 75:
        conv += 0.1
    elif fundamental_score < 50:
        conv -= 0.1
    
    return min(1.5, max(0.5, conv))
