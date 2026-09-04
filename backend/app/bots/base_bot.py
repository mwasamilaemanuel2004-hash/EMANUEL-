import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from loguru import logger


class SignalStrength(Enum):
    VERY_WEAK = "VERY_WEAK"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


class TradeQuality(Enum):
    POOR = "POOR"
    AVERAGE = "AVERAGE"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"
    PERFECT = "PERFECT"


@dataclass
class TradeSignal:
    action: str
    confidence: float
    strength: SignalStrength
    quality: TradeQuality
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    reason: str
    supporting_indicators: List[str]
    ai_reasoning: str
    risk_score: float
    expected_return: float
    time_horizon: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BotState:
    def __init__(self):
        self.performance = type('Performance', (), {'total_profit': 0.0})()
        self.active_signals: List[TradeSignal] = []


class BaseBot:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.bot_id = config.get('bot_id', name.lower().replace(' ', '_'))
        self.parameters = config.get('parameters', {})
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
        }
        self.state = BotState()
        self._load_state()

    def _load_state(self):
        try:
            state_path = f"data/bots/{self.bot_id}_state.json"
            if os.path.exists(state_path):
                with open(state_path, "r") as f:
                    data = json.load(f)
                    self.performance_metrics.update(data.get('performance_metrics', {}))
                    self.state.performance.total_profit = data.get('total_profit', 0.0)
        except Exception as e:
            logger.warning(f"Load state error: {e}")

    def _save_state(self):
        try:
            os.makedirs("data/bots", exist_ok=True)
            data = {
                'performance_metrics': self.performance_metrics,
                'total_profit': self.state.performance.total_profit,
            }
            with open(f"data/bots/{self.bot_id}_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Save state error: {e}")

    async def analyze_market(self, data: Any) -> Optional[TradeSignal]:
        raise NotImplementedError

    def get_performance(self) -> Dict:
        return self.performance_metrics


@dataclass
class Position:
    """Shared position record for bots with an internal execution ledger."""

    id: str
    side: str
    entry_price: float
    quantity: float
    current_price: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    realized_pnl: float = 0.0
    is_open: bool = True
    entry_time: datetime = field(default_factory=datetime.now)


class UltraAdvancedBaseBot:
    """Small shared lifecycle base for bots that manage simulated positions."""

    def __init__(self, bot_name: str, symbol: str, initial_capital: float = 10000.0):
        self.bot_name = bot_name
        self.symbol = symbol
        self.current_capital = float(initial_capital)
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_capital = self.current_capital
        self.logger = logger

    def open_position(self, side: str, price: float, confidence: float, quantity: float) -> Optional[Position]:
        normalized_side = {"long": "BUY", "short": "SELL", "buy": "BUY", "sell": "SELL"}.get(side.lower())
        if normalized_side is None or price <= 0 or quantity <= 0 or not 0 <= confidence <= 1:
            return None
        position_id = f"{self.symbol}-{len(self.positions) + len(self.closed_positions) + 1}"
        position = Position(
            id=position_id,
            side=normalized_side,
            entry_price=float(price),
            quantity=float(quantity),
            current_price=float(price),
        )
        self.positions[position_id] = position
        return position

    def close_position(self, position_id: str, price: float, reason: str) -> Optional[Position]:
        position = self.positions.pop(position_id, None)
        if position is None or price <= 0:
            return None
        position.current_price = float(price)
        direction = 1 if position.side == "BUY" else -1
        position.realized_pnl = (position.current_price - position.entry_price) * position.quantity * direction
        position.is_open = False
        self.current_capital += position.realized_pnl
        self.daily_pnl += position.realized_pnl
        self.peak_capital = max(self.peak_capital, self.current_capital)
        if self.peak_capital > 0:
            drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            self.max_drawdown = max(self.max_drawdown, drawdown)
        self.closed_positions.append(position)
        return position

    def get_performance_metrics(self) -> Dict[str, Any]:
        wins = sum(1 for position in self.closed_positions if position.realized_pnl > 0)
        total = len(self.closed_positions)
        return {
            "total_trades": total,
            "winning_trades": wins,
            "losing_trades": total - wins,
            "win_rate": wins / total if total else 0.0,
            "total_profit": sum(position.realized_pnl for position in self.closed_positions),
            "current_capital": self.current_capital,
            "open_positions": len(self.positions),
            "max_drawdown": self.max_drawdown,
        }
