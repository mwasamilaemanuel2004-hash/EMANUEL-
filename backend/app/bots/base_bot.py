import json
import os
from dataclasses import dataclass, field
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
