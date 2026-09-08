"""
TICK OPTION ENGINE - ULTRA PROFIT EXOTIC OPTIONS
Inatuma Tick Options za Profit Ultra
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger(__name__)


class OptionType(Enum):
    BINARY_ONE_TOUCH = "binary_one_touch"
    BINARY_NO_TOUCH = "binary_no_touch"
    DIGITAL_CALL = "digital_call"
    DIGITAL_PUT = "digital_put"
    RANGE_INSIDE = "range_inside"
    RANGE_OUTSIDE = "range_outside"
    TICK_SPEED = "tick_speed"
    LADDER = "ladder"


class OptionStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SETTLED = "settled"


@dataclass
class TickOption:
    """A single tick option contract"""
    id: str
    option_type: OptionType
    symbol: str
    strike: float
    barrier: float
    barrier2: float = 0.0
    premium: float = 0.0
    payout: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    status: OptionStatus = OptionStatus.ACTIVE
    current_price: float = 0.0
    entry_price: float = 0.0
    high_watermark: float = -999999.0
    low_watermark: float = 999999.0
    ticks_triggered: int = 0
    profit: float = 0.0
    strategy: str = "ultra"

    @property
    def remaining_time(self) -> float:
        return max(0.0, (self.expires_at - datetime.now()).total_seconds())

    @property
    def is_expired(self) -> bool:
        return self.remaining_time <= 0


class TickOptionEngine:
    """ULTRA PROFIT Tick Option Engine"""
    def __init__(self):
        self.options: Dict[str, TickOption] = {}
        self.closed_options: List[TickOption] = []
        self.tick_buffer: Dict[str, deque] = {}
        self._counter = 0
        self.stats = {
            'total_options': 0, 'triggered': 0, 'expired': 0,
            'total_profit': 0.0, 'total_premium': 0.0,
        }
        logger.info("TICK OPTION ENGINE initialized - ULTRA PROFIT MODE")

    def _next_id(self) -> str:
        self._counter += 1
        return f"TICKOPT_{int(time.time() * 1000)}_{self._counter}"

    def create_option(self, option_type: OptionType, symbol: str, current_price: float,
                      barrier: float = 0.0, barrier2: float = 0.0,
                      premium: float = 100.0, payout_multiple: float = 2.5,
                      duration_seconds: int = 3600) -> TickOption:
        """Create a new tick option contract"""
        entry = current_price
        opt = TickOption(
            id=self._next_id(), option_type=option_type, symbol=symbol,
            strike=entry,
            barrier=barrier if barrier > 0 else entry,
            barrier2=barrier2, premium=premium, payout=premium * payout_multiple,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=duration_seconds),
            status=OptionStatus.ACTIVE, current_price=entry, entry_price=entry,
            strategy="ultra_profit"
        )
        self.options[opt.id] = opt
        self.stats['total_options'] += 1
        self.stats['total_premium'] += premium
        logger.info(f"Option created [{option_type.value}] {symbol} barrier={barrier}")
        return opt

    def process_tick(self, symbol: str, price: float, timestamp: float = None) -> List[TickOption]:
        """Process a price tick and check all active options"""
        if symbol not in self.tick_buffer:
            self.tick_buffer[symbol] = deque(maxlen=20)
        self.tick_buffer[symbol].append((timestamp or time.time(), price))

        triggered = []
        for option in list(self.options.values()):
            if option.symbol != symbol or option.status != OptionStatus.ACTIVE:
                continue
            option.current_price = price
            option.high_watermark = max(option.high_watermark, price)
            option.low_watermark = min(option.low_watermark, price)

            if self._check_trigger(option, price):
                triggered.append(self._settle_triggered(option))
            elif option.is_expired:
                option.status = OptionStatus.EXPIRED
                option.profit = -option.premium
                self.stats['expired'] += 1
                self.stats['total_profit'] -= option.premium
        return triggered

    def _check_trigger(self, option: TickOption, price: float) -> bool:
        """Check trigger conditions"""
        t = option.option_type
        if t == OptionType.BINARY_ONE_TOUCH:
            return (price >= option.barrier and option.entry_price <= option.barrier) or \
                   (price <= option.barrier and option.entry_price >= option.barrier)
        if t == OptionType.BINARY_NO_TOUCH:
            if option.is_expired:
                touched = (price >= option.barrier and option.entry_price <= option.barrier) or \
                          (price <= option.barrier and option.entry_price >= option.barrier)
                if not touched:
                    option.status = OptionStatus.TRIGGERED
                    return True
            return False
        if t == OptionType.DIGITAL_CALL:
            return price >= option.barrier and option.entry_price < option.barrier
        if t == OptionType.DIGITAL_PUT:
            return price <= option.barrier and option.entry_price > option.barrier
        if t == OptionType.RANGE_INSIDE:
            return (option.entry_price < option.barrier and price >= option.barrier) or \
                   (option.entry_price > option.barrier2 and price <= option.barrier2)
        if t == OptionType.RANGE_OUTSIDE:
            return (option.barrier <= option.entry_price <= option.barrier2) and \
                   (price < option.barrier or price > option.barrier2)
        if t == OptionType.TICK_SPEED:
            return abs(price - option.entry_price) >= option.barrier
        if t == OptionType.LADDER:
            return price >= option.barrier and option.entry_price < option.barrier
        return False

    def _settle_triggered(self, option: TickOption) -> TickOption:
        """Settle triggered option with profit"""
        option.status = OptionStatus.SETTLED
        option.profit = option.payout - option.premium
        option.ticks_triggered += 1
        self.stats['triggered'] += 1
        self.stats['total_profit'] += option.profit
        logger.info(f"OPTION TRIGGERED: {option.option_type.value} profit=${option.profit:,.2f}")
        return option

    def close_option(self, option_id: str) -> Optional[Dict]:
        """Manually close an option"""
        option = self.options.pop(option_id, None)
        if not option:
            return None
        if option.status == OptionStatus.ACTIVE:
            option.status = OptionStatus.CANCELLED
            option.profit = -option.premium
            self.stats['total_profit'] -= option.premium
        self.closed_options.append(option)
        return self._serialize(option)

    def get_active_options(self) -> List[Dict]:
        return [self._serialize(o) for o in self.options.values() if o.status == OptionStatus.ACTIVE]

    def _serialize(self, option: TickOption) -> Dict:
        return {
            'id': option.id, 'type': option.option_type.value, 'symbol': option.symbol,
            'strike': option.strike, 'barrier': option.barrier, 'barrier2': option.barrier2,
            'entry_price': option.entry_price, 'current_price': option.current_price,
            'premium': option.premium, 'payout': option.payout, 'profit': round(option.profit, 2),
            'status': option.status.value, 'expires_at': option.expires_at.isoformat(),
            'remaining_seconds': option.remaining_time,
            'high_watermark': option.high_watermark, 'low_watermark': option.low_watermark,
        }

    def get_stats(self) -> Dict:
        active = len([o for o in self.options.values() if o.status == OptionStatus.ACTIVE])
        return {
            **self.stats, 'active_options': active,
            'win_rate': round((self.stats['triggered'] / max(1, self.stats['triggered'] + self.stats['expired'])) * 100, 1),
            'roi': round((self.stats['total_profit'] / max(1, self.stats['total_premium'])) * 100, 1),
        }


tick_option_engine = TickOptionEngine()

__all__ = ['TickOptionEngine', 'TickOption', 'OptionType', 'OptionStatus', 'tick_option_engine']
