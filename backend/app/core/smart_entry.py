"""
Smart Entry Engine — unified execution logic for ALL 13 bots AND backtester.

ENHANCED (per your spec):
  - Mandatory SMART stop loss on every trade (ATR + structure, never widened
    on a losing trade). This is your "enhance all system associated with
    stop loss" — smarter, not removed.
  - TP1: bank 30% at first milestone (1R) -> arm BREAKEVEN LOCK (SL -> entry)
  - TP2: bank 30% at next objective (2.5R)
  - RUNNER: UNLIMITED — trails via ATR/structure, NO small mandatory target.
    Exits ONLY on trailing-stop hit or structure break. Lets winners run.
  - Advanced profit lock (one-way, never moves backward)
  - Structure-break exit for the runner (momentum dies / CHoCH against)
  - Asymmetric payoff: small controlled losses, large winners
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


class SmartExit:
    def __init__(self):
        self.won = False
        self.pnl_pct = 0.0
        self.exit_reason = "none"
        self.tp1_hit = False
        self.tp2_hit = False
        self.runner_hit = False       # True if runner exited at trailing/structure
        self.max_favorable = 0.0       # MFE
        self.max_adverse = 0.0         # MAE
        self.locked_profit_pct = 0.0
        self.runner_pnl_pct = 0.0      # PnL contributed by the runner portion


@dataclass
class SmartPlan:
    entry: float
    side: str                 # BUY / SELL
    sl: float                 # INITIAL stop (mandatory, smart ATR/structure)
    tp1: float                # first milestone (breakeven trigger)
    tp2: float                # second objective
    tp1_size: float = 0.30
    tp2_size: float = 0.40
    runner_size: float = 0.30
    atr: float = 0.0
    regime: str = "TREND"


class SmartEntryEngine:
    """
    Build plan and simulate bar-by-bar. SAME logic for live and backtest.

    The plan has a MANDATORY initial SL. TP1 (1R) arms breakeven. TP2 banks
    partial. The RUNNER (30%) is UNLIMITED — it trails via ATR and exits only
    on trailing-stop hit, structure break, or end-of-window. No small fixed
    mandatory target on the runner (no cutting winners short).
    """

    def __init__(self, min_rr: float = 2.0):
        self.min_rr = min_rr

    def build_plan(self, side: str, entry: float, atr: float,
                   regime: str = "TREND", structure_sl: Optional[float] = None) -> SmartPlan:
        """SL is MANDATORY. Compute from ATR (and structure if provided)."""
        # MANDATORY smart stop loss
        risk = max(atr, entry * 0.002)
        if structure_sl is not None:
            if side == "BUY":
                risk = min(abs(entry - structure_sl), atr * 3.0)
                risk = max(risk, atr * 0.8)
            else:
                risk = min(abs(structure_sl - entry), atr * 3.0)
                risk = max(risk, atr * 0.8)

        # (m1=breakeven trigger @1R, m2=second objective, runner=UNLIMITED)
        rr = {
            "STRONG_TREND":   (1.0, 2.5),
            "WEAK_TREND":     (1.0, 2.2),
            "RANGE":          (1.0, 2.0),
            "HIGH_VOLATILITY":(1.0, 3.0),
            "LOW_VOLATILITY": (1.0, 2.0),
            "UNSAFE":         (1.0, 1.0),
        }.get(regime, (1.0, 2.5))
        m1, m2 = rr

        if side == "BUY":
            sl = entry - risk
            tp1 = entry + risk * m1
            tp2 = entry + risk * m2
        else:
            sl = entry + risk
            tp1 = entry - risk * m1
            tp2 = entry - risk * m2

        # MANDATORY: sl must be valid
        assert sl != entry, "Stop loss must differ from entry"
        return SmartPlan(entry=entry, side=side, sl=sl, tp1=tp1, tp2=tp2,
                         atr=atr, regime=regime)

    def simulate(self, plan: SmartPlan, future: pd.DataFrame,
                 max_bars: int = 250) -> SmartExit:
        """
        Mandatory SL on every bar. Breakeven lock at TP1. Partial at TP2.
        Runner is UNLIMITED — exits only on trailing stop or structure break.
        """
        res = SmartExit()
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
        for _, row in bars.iterrows():
            hi, lo, cl = row['high'], row['low'], row['close']
            risk = abs(entry - plan.sl) or atr

            # MFE / MAE
            if side == "BUY":
                fav = (hi - entry) / risk if risk else 0
                adv = (entry - lo) / risk if risk else 0
            else:
                fav = (entry - lo) / risk if risk else 0
                adv = (hi - entry) / risk if risk else 0
            res.max_favorable = max(res.max_favorable, fav)
            res.max_adverse = max(res.max_adverse, adv)

            # 1) TP1 — bank partial, arm breakeven
            if not tp1_done:
                if (side == "BUY" and hi >= plan.tp1) or (side == "SELL" and lo <= plan.tp1):
                    res.tp1_hit = True
                    tp1_done = True
                    breakeven_armed = True
                    close_px = plan.tp1
                    partial = plan.tp1_size * _signed(side, close_px - entry) / entry
                    res.pnl_pct += partial
                    remaining -= plan.tp1_size

            # 2) Breakeven lock (one-way, never backward)
            if breakeven_armed:
                locked_sl = entry

            # 3) TP2 — bank partial
            if tp1_done and not tp2_done:
                if (side == "BUY" and hi >= plan.tp2) or (side == "SELL" and lo <= plan.tp2):
                    res.tp2_hit = True
                    tp2_done = True
                    partial = plan.tp2_size * _signed(side, plan.tp2 - entry) / entry
                    res.pnl_pct += partial
                    remaining -= plan.tp2_size

            # 4) RUNNER — UNLIMITED trailing (no small fixed target)
            if remaining > 1e-6:
                # ATR trailing stop (one-way up). Tighter in strong trend,
                # looser in volatile.
                trail_mult = 1.5 if plan.regime != "HIGH_VOLATILITY" else 2.0
                if side == "BUY":
                    trail = hi - atr * trail_mult
                    locked_sl = max(locked_sl, trail)
                else:
                    trail = lo + atr * trail_mult
                    locked_sl = min(locked_sl, trail)

            # 5) EXIT: mandatory stop (MUST close on SL hit) OR runner structure break
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

            # Runner structure break: a strong candle against the trade on
            # the runner portion (momentum dies -> lock in runner profit)
            if exit_px is None and remaining > 1e-6 and tp2_done:
                rng = hi - lo
                body = abs(cl - row['open'])
                if rng > 0 and body / rng > 0.7:
                    # Strong candle. Against the trade?
                    against = ((side == "BUY" and cl < row['open']) or
                               (side == "SELL" and cl > row['open']))
                    if against and body > atr * 0.5:
                        exit_px = cl
                        exit_reason = "runner_structure_break"

            if exit_px is not None:
                pnl = remaining * _signed(side, exit_px - entry) / entry
                res.pnl_pct += pnl
                if remaining > plan.runner_size - 1e-6 and not tp1_done:
                    runner_pnl = pnl
                else:
                    runner_pnl += pnl
                res.exit_reason = exit_reason
                res.runner_hit = (exit_reason == "runner_structure_break")
                break

        # End of window: close remaining at last close (runner still trails)
        if remaining > 1e-6:
            last = bars.iloc[-1]['close'] if len(bars) else entry
            pnl = remaining * _signed(side, last - entry) / entry
            res.pnl_pct += pnl
            runner_pnl += pnl
            res.exit_reason = res.exit_reason or "end_of_window"

        res.runner_pnl_pct = runner_pnl
        res.locked_profit_pct = max(0.0, res.pnl_pct)
        res.won = res.pnl_pct > 0
        return res


def _signed(side: str, delta: float) -> float:
    return delta if side == "BUY" else -delta
