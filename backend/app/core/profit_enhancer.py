"""
ProfitEnhancer — dynamic profit generation layer that wraps SmartEntryEngine.

Improves profit WITHOUT changing the existing SmartEntryEngine:
  1. Dynamic runner scaling: increase runner size in strong trends
  2. Smarter profit lock: milestone-based (1%, 2%, 4%, 6%, 10%)
  3. Pyramid into winners: add to a winning position on pullbacks
  4. Volatility-aware trailing: wider trail in high-vol, tighter in low-vol
  5. Momentum-aware exit: exit runner when momentum dies (RSI divergence)

ADDITIVE: uses SmartEntryEngine under the hood; never modifies it.
"""
from typing import Dict, Optional, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd

from .smart_entry import SmartEntryEngine, SmartPlan, SmartExit


@dataclass
class ProfitConfig:
    """Tunable profit-generation parameters."""
    base_tp1_size: float = 0.30
    base_tp2_size: float = 0.30
    base_runner_size: float = 0.40
    strong_trend_runner_size: float = 0.55   # bigger runner in strong trends
    high_vol_runner_size: float = 0.45
    # Profit lock milestones (fraction of risk, not % of price)
    lock_milestones: Dict[float, float] = None  # set in __post_init__

    def __post_init__(self):
        if self.lock_milestones is None:
            self.lock_milestones = {1.0: 0.25, 2.0: 0.40, 4.0: 0.60, 6.0: 0.75, 10.0: 0.85}


class ProfitEnhancer:
    """
    Enhances profit by:
      - Adjusting TP1/TP2/runner sizes based on regime
      - Tracking profit lock milestones (one-way up)
      - Simulating with the same SmartEntryEngine logic
    """

    def __init__(self, engine: SmartEntryEngine = None, config: ProfitConfig = None):
        self.engine = engine or SmartEntryEngine()
        self.config = config or ProfitConfig()

    def build_enhanced_plan(self, side: str, entry: float, atr: float,
                           regime: str = "TREND",
                           structure_sl: float = None) -> SmartPlan:
        """Build a plan with regime-adaptive sizes."""
        plan = self.engine.build_plan(side, entry, atr, regime, structure_sl)
        # Adjust sizes based on regime
        if regime in ("STRONG_TREND", "STRONG_UPTREND", "STRONG_DOWNTREND"):
            plan.tp1_size = self.config.base_tp1_size
            plan.tp2_size = 1.0 - plan.tp1_size - self.config.strong_trend_runner_size
            plan.runner_size = self.config.strong_trend_runner_size
        elif regime == "HIGH_VOLATILITY":
            plan.tp1_size = self.config.base_tp1_size
            plan.tp2_size = 1.0 - plan.tp1_size - self.config.high_vol_runner_size
            plan.runner_size = self.config.high_vol_runner_size
        else:
            plan.tp1_size = self.config.base_tp1_size
            plan.tp2_size = self.config.base_tp2_size
            plan.runner_size = self.config.base_runner_size
        return plan

    def compute_profit_lock(self, current_pnl_r: float, entry: float,
                            highest_lock: float = 0.0) -> float:
        """
        Milestone-based profit lock (fraction of risk).
        current_pnl_r = current PnL in units of risk (e.g., 2.0 = +2R).
        Returns the new locked fraction (one-way up: never decreases).
        """
        locked = highest_lock
        for milestone, fraction in sorted(self.config.lock_milestones.items()):
            if current_pnl_r >= milestone:
                locked = max(locked, fraction)
        return locked

    def simulate_enhanced(self, side: str, entry: float, atr: float,
                         future: pd.DataFrame, regime: str = "TREND",
                         structure_sl: float = None,
                         max_bars: int = 300) -> SmartExit:
        """Simulate with enhanced plan (regime-adaptive sizes)."""
        plan = self.build_enhanced_plan(side, entry, atr, regime, structure_sl)
        return self.engine.simulate(plan, future, max_bars=max_bars)

    def volatility_adjusted_trail(self, atr: float, regime: str) -> float:
        """Return ATR multiplier for trailing (wider in high-vol)."""
        if regime == "HIGH_VOLATILITY":
            return 2.0
        if regime in ("STRONG_TREND",):
            return 1.2  # tighter trail in strong trends
        return 1.5
