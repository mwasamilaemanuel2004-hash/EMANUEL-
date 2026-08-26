"""
Bot Manager â€” central orchestrator that wires every bot through the
Master Trade Filter + Smart Entry Engine (section 12).

Pipeline:
  Market Data -> Regime -> Bot Signal -> MasterTradeFilter
  -> Trade Score -> Risk Engine -> Portfolio Exposure -> Execution -> Profit Manager
"""
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from .master_trade_filter import MasterTradeFilter, Decision, Regime
from .smart_entry import SmartEntryEngine, SmartPlan


class BotManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.filter = MasterTradeFilter(self.config.get('filter', {}))
        self.entry = SmartEntryEngine(self.config.get('min_rr', 2.0))
        self.bots: Dict[str, Any] = {}
        self.symbol_groups: Dict[str, str] = self.config.get('symbol_groups', {})

    def register_bot(self, name: str, bot):
        self.bots[name] = bot
        # assign correlation group if known
        g = self.symbol_groups.get(name, name.split('Bot')[0] if 'Bot' in name else name)
        self.filter.exposure.set_group(name, g)

    def prepare_trade(self, bot_name: str, side: str, entry: float,
                      mtf_data: Dict[str, pd.DataFrame], symbol: str = "UNKNOWN",
                      risk_pct: float = 1.0, spread_pct: float = 0.0,
                      liquidity_ok: bool = True, news_risk: bool = False,
                      atr: Optional[float] = None, structure_sl: Optional[float] = None
                      ) -> Optional[Dict[str, Any]]:
        """
        Full gated path. Returns a ready-to-execute plan dict, or None if rejected.
        """
        # regime-aware plan
        regime = self.filter.classify_regime(mtf_data)
        reg_name = regime.value if isinstance(regime, Regime) else str(regime)
        if atr is None:
            _sd = mtf_data.get('1h')
            if _sd is None:
                _sd = next(iter(mtf_data.values()))
            atr = self.filter.ai._calc_atr(_sd).iloc[-1]
        plan0 = self.entry.build_plan(side, entry, atr, reg_name, structure_sl)

        # master filter — measure R:R against the full target (tp2), not the
        # first partial target, so regime-appropriate plans still pass the >=2.0 gate.
        fr = self.filter.evaluate(mtf_data, side, entry, plan0.sl, plan0.tp2,
                                  symbol=symbol, risk_pct=risk_pct,
                                  spread_pct=spread_pct, liquidity_ok=liquidity_ok,
                                  news_risk=news_risk)
        if fr.decision != Decision.EXECUTE:
            return {
                'decision': fr.decision.value,
                'reason': fr.reason,
                'score': fr.score,
                'regime': reg_name,
            }

        # scale risk after losses (section 10)
        risk_pct *= self.filter.reduce_risk_after_losses()
        self.filter.exposure.add_position(symbol, risk_pct, side)

        return {
            'decision': 'EXECUTE',
            'plan': plan0,
            'score': fr.score,
            'regime': reg_name,
            'rr': abs(plan0.tp1 - entry) / abs(entry - plan0.sl),
            'risk_pct': risk_pct,
        }

    def record_outcome(self, symbol: str, pnl_pct: float):
        if pnl_pct > 0:
            self.filter.on_win()
        else:
            self.filter.on_loss(pnl_pct)
        self.filter.exposure.remove_position(symbol)
