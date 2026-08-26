"""
Advanced Trading Engine — Multi-Factor Confirmed, Adaptive SL/TP, Profit Lock, Loss Control
Integrates ai_overseer TradeScore + MarketCondition for 12-point spec.
NOT GUARANTEEING 98% WIN RATE — uses honest risk/reward filtering.
"""
from typing import Optional, Dict, Any
import numpy as np
from backend.app.core.ai_overseer import TradeScore, TradeGrade, AIOverseer, MarketCondition

class AdvancedTradeConfig:
    MIN_CONFIDENCE = 70          # 60-69 WATCH, 70+ NORMAL, 80+ HIGH
    MIN_RR = 2.0                 # 1:2 minimum; prefer 2.5-4
    MAX_DAILY_LOSS_PCT = 5.0     # stop if down 5% daily
    MAX_CONSECUTIVE_LOSSES = 3   # cooldown after 3 losses
    USE_DEMO = True              # default demo mode
    ATR_MULT_SL = 1.5            # adaptive SL = entry - ATR*1.5
    TP_STAGES = [1.5, 2.5, 4.0] # TP1 1.5R, TP2 2.5R, Runner 4R+
    PROFIT_LOCK_PCT = 0.5        # lock 50% profit at TP1; SL to entry

class AdvancedEngine:
    def __init__(self, config: Optional[AdvancedTradeConfig] = None):
        self.cfg = config or AdvancedTradeConfig()
        self.ai = AIOverseer()
        self.daily_loss = 0.0
        self.consecutive_losses = 0
        self.trades_today = 0
        self.demo = self.cfg.USE_DEMO
        self.active_positions: Dict[str, Any] = {}

    def score_trade(self, price_data: np.ndarray, volume: np.ndarray,
                    trend_context: str = "neutral") -> TradeScore:
        """Multi-factor score from ai_overseer."""
        return self.ai.evaluate(price_data, volume, trend_context)

    def should_enter(self, score: TradeScore) -> bool:
        if score.grade == "NO_TRADE" or score.total_score < self.cfg.MIN_CONFIDENCE:
            return False
        if score.risk_reward_score < self.cfg.MIN_RR:
            return False  # R:R gate
        return True

    def adaptive_sl(self, entry: float, atr: float, structure: str = "support") -> float:
        if self.demo:
            return entry - atr * self.cfg.ATR_MULT_SL
        return max(entry - atr * 1.5, entry - atr * 2.0)  # conservative

    def smart_tp(self, entry: float, risk: float, stage: int = 1) -> float:
        mult = self.cfg.TP_STAGES[min(stage-1, len(self.cfg.TP_STAGES)-1)]
        return entry + risk * mult

    def profit_lock(self, pos: Dict) -> None:
        if pos.get("tp1_hit") and not pos.get("sl_trailed"):
            pos["sl"] = pos.get("entry", pos["entry"])  # lock to breakeven
            pos["sl_trailed"] = True

    def check_loss_controls(self) -> bool:
        if self.daily_loss >= self.cfg.MAX_DAILY_LOSS_PCT:
            return False
        if self.consecutive_losses >= self.cfg.MAX_CONSECUTIVE_LOSSES:
            return False
        return True

    def classify_market(self, price_data: np.ndarray) -> MarketCondition:
        # simplified: use ai_overseer market analysis
        return self.ai.classify_market(price_data)

    def execute_order(self, symbol: str, direction: str, entry: float,
                      risk: float, score: TradeScore) -> Dict:
        if not self.should_enter(score):
            return {"status": "REJECTED", "reason": "score/RR", "demo": self.demo}
        if not self.check_loss_controls():
            return {"status": "REJECTED", "reason": "loss_control", "demo": self.demo}
        sl = self.adaptive_sl(entry, risk * 0.5)  # ATR proxy
        tp1 = self.smart_tp(entry, risk, 1)
        tp2 = self.smart_tp(entry, risk, 2)
        pos = {
            "symbol": symbol, "direction": direction,
            "entry": entry, "sl": sl, "tp1": tp1, "tp2": tp2,
            "risk": risk, "score": score.total_score,
            "sl_trailed": False, "tp1_hit": False,
            "grade": score.grade, "demo": self.demo
        }
        self.active_positions[symbol] = pos
        self.trades_today += 1
        return {"status": "EXECUTED", "position": pos}
