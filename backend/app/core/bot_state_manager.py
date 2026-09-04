"""
Bot State Manager — tracks bot lifecycle, stops, recovery, and re-entry.
Reconstructed to restore the deleted module (BOT_STATE_MANAGER.PY).
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

from loguru import logger


class BotState(Enum):
    ERROR = "ERROR"
    INITIALIZING = "INITIALIZING"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    REENTRY = "REENTRY"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    STOPPING = "STOPPING"


class StopTrigger(Enum):
    CAPITAL_PROTECTION = "CAPITAL_PROTECTION"
    CONSECUTIVE_LOSSES = "CONSECUTIVE_LOSSES"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    DRAWDOWN_LIMIT = "DRAWDOWN_LIMIT"
    EXCHANGE_ERROR = "EXCHANGE_ERROR"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    INDICATOR_FAILURE = "INDICATOR_FAILURE"
    MARKET_CRASH = "MARKET_CRASH"
    STRATEGY_FAILURE = "STRATEGY_FAILURE"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    USER_PAUSE = "USER_PAUSE"
    WEEKLY_LOSS_LIMIT = "WEEKLY_LOSS_LIMIT"


class RecoveryPhase(Enum):
    NONE = "NONE"
    DIAGNOSE = "DIAGNOSE"
    STABILIZE = "STABILIZE"
    VALIDATE = "VALIDATE"
    RESUME = "RESUME"


class RecoveryState(Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ReentryCondition(Enum):
    MARKET_CALM = "MARKET_CALM"
    BALANCE_RESTORED = "BALANCE_RESTORED"
    MANUAL_APPROVAL = "MANUAL_APPROVAL"
    TIME_ELAPSED = "TIME_ELAPSED"


@dataclass
class BotStats:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    consecutive_losses: int = 0
    daily_loss: float = 0.0
    weekly_loss: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class StopRecord:
    trigger: StopTrigger
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BotStateManager:
    """Manages bot operational state, stop triggers, recovery, and re-entry."""

    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.state = BotState.INITIALIZING
        self.stats = BotStats()
        self.stop_history: List[StopRecord] = []
        self.recovery_phase = RecoveryPhase.NONE
        self.recovery_state = RecoveryState.IDLE
        self.reentry_conditions: List[ReentryCondition] = []
        self.stop_conditions: Dict[str, Any] = {}
        self.last_heartbeat = datetime.now()
        self.user_resume_confirmed = False
        self.events: List[Dict[str, Any]] = []
        self._load_state()

    # ============================================================
    # STATE PERSISTENCE
    # ============================================================
    def _load_state(self) -> None:
        try:
            state_path = f"data/bots/{self.bot_id}_state.json"
            if os.path.exists(state_path):
                with open(state_path, "r") as f:
                    data = json.load(f)
                    s = data.get('stats', {})
                    self.stats = BotStats(**{k: v for k, v in s.items() if k in BotStats.__dataclass_fields__})
                    self.state = BotState(data.get('state', BotState.STOPPED.value))
        except Exception as e:
            logger.warning(f"Load state error: {e}")

    def _save_state(self) -> None:
        try:
            os.makedirs("data/bots", exist_ok=True)
            data = {
                'bot_id': self.bot_id,
                'state': self.state.value,
                'stats': self.stats.__dict__,
            }
            with open(f"data/bots/{self.bot_id}_state.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Save state error: {e}")

    def _log_event(self, event: str, **kwargs) -> None:
        self.events.append({'event': event, 'ts': datetime.now(), **kwargs})
        if len(self.events) > 200:
            self.events = self.events[-200:]

    # ============================================================
    # LIFECYCLE
    # ============================================================
    def start(self) -> None:
        self.state = BotState.RUNNING
        self.user_resume_confirmed = False
        self._log_event("start")
        self._save_state()

    def stop(self, trigger: StopTrigger = StopTrigger.USER_PAUSE, reason: str = "user/manual stop") -> None:
        self.state = BotState.STOPPED
        self.stop_history.append(StopRecord(trigger=trigger, reason=reason))
        self._log_event("stop", trigger=trigger.value)
        self._save_state()

    def pause(self, trigger: StopTrigger = StopTrigger.USER_PAUSE) -> None:
        self.state = BotState.PAUSED
        self._log_event("pause", trigger=trigger.value)

    def resume(self) -> None:
        if self.state in (BotState.PAUSED, BotState.STOPPED):
            self.state = BotState.RUNNING
            self._log_event("resume")
            self._save_state()

    def reset(self) -> None:
        self.state = BotState.INITIALIZING
        self.stats = BotStats()
        self.stop_history = []
        self.recovery_phase = RecoveryPhase.NONE
        self.recovery_state = RecoveryState.IDLE
        self._log_event("reset")
        self._save_state()

    def confirm_user_resume(self) -> None:
        self.user_resume_confirmed = True
        self._log_event("user_resume_confirmed")

    # ============================================================
    # HEALTH / HEARTBEAT
    # ============================================================
    def heartbeat(self) -> None:
        self.last_heartbeat = datetime.now()

    def check_health(self) -> Dict[str, Any]:
        heartbeat_age = datetime.now() - self.last_heartbeat
        return {
            "is_healthy": heartbeat_age < timedelta(seconds=60),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "heartbeat_age_seconds": heartbeat_age.total_seconds(),
        }

    # ============================================================
    # STATS / STOPS
    # ============================================================
    def update_stats(self, stats: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        updates = {**(stats or {}), **kwargs}
        for k, v in updates.items():
            if hasattr(self.stats, k):
                setattr(self.stats, k, v)
        self.stats.last_update = datetime.now()

    def update_stop_conditions(self, conditions: Dict[str, Any]) -> None:
        self.stop_conditions.update(conditions)

    def update_reentry_conditions(self, conditions: List[ReentryCondition]) -> None:
        self.reentry_conditions = conditions

    def check_stop_conditions(self) -> Optional[StopTrigger]:
        s = self.stats
        if s.daily_loss >= self.stop_conditions.get('daily_loss_limit', 5.0):
            return StopTrigger.DAILY_LOSS_LIMIT
        if s.weekly_loss >= self.stop_conditions.get('weekly_loss_limit', 10.0):
            return StopTrigger.WEEKLY_LOSS_LIMIT
        if s.consecutive_losses >= self.stop_conditions.get('max_consecutive_losses', 3):
            return StopTrigger.CONSECUTIVE_LOSSES
        if s.max_drawdown >= self.stop_conditions.get('max_drawdown', 15.0):
            return StopTrigger.DRAWDOWN_LIMIT
        return None

    def handle_stop(self, trigger: StopTrigger, reason: str = "") -> None:
        self.state = BotState.STOPPED
        self.stop_history.append(StopRecord(trigger=trigger, reason=reason))
        self._log_event("handle_stop", trigger=trigger.value, reason=reason)
        self._save_state()

    def record_error(self, error: str) -> None:
        self._log_event("error", error=error)
        if self.state == BotState.RUNNING:
            self.state = BotState.ERROR

    # ============================================================
    # RECOVERY
    # ============================================================
    def _should_start(self) -> bool:
        return self.state in (BotState.STOPPED, BotState.ERROR)

    def _start_recovery(self) -> None:
        self.recovery_state = RecoveryState.ACTIVE
        self.recovery_phase = RecoveryPhase.DIAGNOSE
        self._log_event("recovery_start")

    def _advance_recovery_phase(self) -> None:
        order = [RecoveryPhase.DIAGNOSE, RecoveryPhase.STABILIZE, RecoveryPhase.VALIDATE, RecoveryPhase.RESUME, RecoveryPhase.NONE]
        idx = order.index(self.recovery_phase)
        if idx < len(order) - 1:
            self.recovery_phase = order[idx + 1]

    def _is_phase_complete(self, phase: RecoveryPhase) -> bool:
        return phase in (RecoveryPhase.NONE, RecoveryPhase.RESUME)

    def _is_recovery_complete(self) -> bool:
        return self.recovery_state == RecoveryState.COMPLETE

    def _update_phase_progress(self, progress: float) -> None:
        self._log_event("phase_progress", phase=self.recovery_phase.value, progress=progress)

    def _update_stop_check(self) -> None:
        trigger = self.check_stop_conditions()
        if trigger:
            self.handle_stop(trigger)

    def _check_analysis_conditions(self) -> bool:
        return self.recovery_phase in (RecoveryPhase.VALIDATE, RecoveryPhase.RESUME)

    def _check_reentry_conditions(self) -> bool:
        if ReentryCondition.MANUAL_APPROVAL in self.reentry_conditions and not self.user_resume_confirmed:
            return False
        return self.recovery_state == RecoveryState.COMPLETE or not self.reentry_conditions

    def update_recovery(self, phase: Optional[RecoveryPhase] = None, progress: float = 0.0) -> None:
        if phase:
            self.recovery_phase = phase
        self._update_phase_progress(progress)
        if self._is_phase_complete(self.recovery_phase):
            self.recovery_state = RecoveryState.COMPLETE

    # ============================================================
    # READ API
    # ============================================================
    def get_state(self) -> Dict[str, Any]:
        return {
            "current_state": self.state.value,
            "bot_id": self.bot_id,
            "is_running": self.state == BotState.RUNNING,
        }

    def get_stats(self) -> BotStats:
        return self.stats

    def get_stop_history(self) -> List[StopRecord]:
        return self.stop_history

    def _get_stats_dict(self) -> Dict[str, Any]:
        return self.stats.__dict__

    def _get_stop_reason(self, trigger: StopTrigger) -> str:
        return f"Stop triggered: {trigger.value}"
