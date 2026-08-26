"""
Backtesting Engine - Strategy Testing and Optimization
Tests trading strategies on historical data with comprehensive analytics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from ..core.advanced_engine import AdvancedEngine, AdvancedTradeConfig


class BacktestStrategy(Enum):
    TREND_FOLLOW = "trend_follow"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    ARBITRAGE = "arbitrage"
    SCALPING = "scalping"
    GRID_TRADING = "grid_trading"


@dataclass
class BacktestConfig:
    """Backtest configuration"""
    strategy: BacktestStrategy = BacktestStrategy.TREND_FOLLOW
    initial_capital: float = 10000.0
    risk_per_trade: float = 2.0  # percentage
    max_positions: int = 5
    commission: float = 0.1  # percentage
    slippage: float = 0.05  # percentage
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    timeframe: str = "1h"
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0
    trailing_stop: bool = False
    trailing_stop_pct: float = 1.5


@dataclass
class BacktestTrade:
    """Individual backtest trade"""
    trade_id: int
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    commission: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_reason: str = "signal"
    is_win: bool = False


@dataclass
class BacktestResult:
    """Complete backtest results"""
    config: BacktestConfig
    trades: List[BacktestTrade]
    equity_curve: List[float]
    drawdown_curve: List[float]
    timestamps: List[datetime]
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    avg_trade_duration: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    expectancy: float = 0.0
    recovery_factor: float = 0.0
    calmar_ratio: float = 0.0


class BacktestEngine:
    """
    Advanced Backtesting Engine
    - Multiple strategy support
    - Realistic simulation (commission, slippage)
    - Comprehensive performance metrics
    - Drawdown analysis
    - Weakness detection
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        self.data: Optional[pd.DataFrame] = None
        self.results: Optional[BacktestResult] = None
        self.is_running = False
        self.advanced = AdvancedEngine()

    def load_data(self, data: pd.DataFrame) -> bool:
        """Load historical data for backtesting"""
        try:
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_columns):
                logger.error(f"Data missing required columns: {required_columns}")
                return False

            self.data = data.copy()
            logger.info(f"Loaded {len(data)} candles for backtesting")
            return True

        except Exception as e:
            logger.error(f"Data load error: {e}")
            return False

    def generate_sample_data(self, periods: int = 1000, mean_reverting: bool = False) -> pd.DataFrame:
        """Generate sample OHLCV data for testing.

        mean_reverting=True produces oscillating (range-bound) data so the
        mean-reversion strategy is evaluated under realistic conditions.
        """
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='1h')

        if mean_reverting:
            # Oscillating price around a fixed mean (no cumulative drift)
            t = np.arange(periods)
            wave = 14 * np.sin(t / 30.0) + 7 * np.sin(t / 9.0)
            noise = np.random.normal(0, 0.8, periods)
            price = 100 + wave + noise
        else:
            # Random-walk with slight upward drift (trending)
            returns = np.random.normal(0.0001, 0.02, periods)
            price = 100 * np.exp(np.cumsum(returns))

        # Generate OHLCV
        data = pd.DataFrame({
            'timestamp': dates,
            'open': price * (1 + np.random.uniform(-0.005, 0.005, periods)),
            'high': price * (1 + np.random.uniform(0, 0.02, periods)),
            'low': price * (1 - np.random.uniform(0, 0.02, periods)),
            'close': price,
            'volume': np.random.uniform(1000, 10000, periods)
        })

        data.set_index('timestamp', inplace=True)
        self.data = data
        logger.info(f"Generated {periods} sample candles (mean_reverting={mean_reverting})")
        return data

    def run(self, data: Optional[pd.DataFrame] = None) -> BacktestResult:
        """Run backtest"""
        try:
            if data is not None:
                self.load_data(data)
            
            if self.data is None:
                logger.error("No data loaded for backtest")
                return None

            self.is_running = True
            logger.info(f"Running backtest: {self.config.strategy.value}")

            # Run strategy
            if self.config.strategy == BacktestStrategy.TREND_FOLLOW:
                result = self._run_trend_follow()
            elif self.config.strategy == BacktestStrategy.MEAN_REVERSION:
                result = self._run_mean_reversion()
            elif self.config.strategy == BacktestStrategy.BREAKOUT:
                result = self._run_breakout()
            elif self.config.strategy == BacktestStrategy.SCALPING:
                result = self._run_scalping()
            else:
                result = self._run_trend_follow()

            self.results = result
            self.is_running = False

            logger.info(f"Backtest complete: {result.total_trades} trades, {result.win_rate:.1f}% win rate")
            return result

        except Exception as e:
            logger.error(f"Backtest error: {e}")
            self.is_running = False
            return None

    def _run_trend_follow(self) -> BacktestResult:
        """Trend following strategy backtest"""
        trades = []
        equity = [self.config.initial_capital]
        drawdown = [0.0]
        capital = self.config.initial_capital
        position = None
        trade_id = 0
        cooldown_bars = 0  # backtest cooldown so trading resumes after a loss streak

        # Calculate indicators
        data = self.data.copy()
        data['ema_fast'] = data['close'].ewm(span=12).mean()
        data['ema_slow'] = data['close'].ewm(span=26).mean()
        data['atr'] = self._calculate_atr(data)
        # ENHANCED: multi-factor confirmation — ADX trend strength + volume filter
        delta_high = data['high'].diff()
        delta_low = data['low'].diff()
        tr = pd.concat([delta_high, delta_low], axis=1).abs().max(axis=1)
        data['tr'] = tr
        data['atr_smoothed'] = data['atr']
        up_move = data['high'].diff()
        dn_move = -data['low'].diff()
        data['+dm'] = np.where((up_move > dn_move) & (up_move > 0), up_move, 0.0)
        data['-dm'] = np.where((dn_move > up_move) & (dn_move > 0), dn_move, 0.0)
        data['_pos'] = data['+dm'].rolling(14).sum()
        data['_neg'] = data['-dm'].rolling(14).sum()
        data['adx'] = 100 * (data['_pos'] - data['_neg']).abs() / (data['_pos'] + data['_neg']).replace(0, np.nan)
        data['adx'] = data['adx'].rolling(14).mean()
        data['vol_avg'] = data['volume'].rolling(20).mean()

        for i in range(50, len(data)):
            current = data.iloc[i]
            prev = data.iloc[i-1]

            # Entry signals
            if position is None:
                # ENHANCED: confirmation gate — require ADX>20 (trending) and volume confirmation
                adx_ok = pd.notna(current['adx']) and current['adx'] > 15
                vol_ok = current['volume'] > current['vol_avg'] if pd.notna(current['vol_avg']) and current['vol_avg'] > 0 else True
                if not (adx_ok and vol_ok):
                    pass  # skip unconfirmed entry
                elif prev['ema_fast'] <= prev['ema_slow'] and current['ema_fast'] > current['ema_slow']:
                    # ENHANCED: loss-control gate — skip entry after consecutive losses or daily loss limit.
                    # Backtest uses a cooldown so trading resumes after the streak cools down.
                    if cooldown_bars > 0:
                        cooldown_bars -= 1
                        if cooldown_bars == 0:
                            self.advanced.consecutive_losses = 0
                            self.advanced.daily_loss = 0.0
                        continue
                    if not self.advanced.check_loss_controls():
                        cooldown_bars = 20
                        continue
                    risk_amount = capital * (self.config.risk_per_trade / 100)
                    stop_distance = current['atr'] * 1.0
                    quantity = risk_amount / stop_distance if stop_distance > 0 else 0

                    if quantity > 0 and len([t for t in trades if t.exit_price == 0]) < self.config.max_positions:
                        trade_id += 1
                        position = BacktestTrade(
                            trade_id=trade_id,
                            symbol='BACKTEST',
                            side='BUY',
                            entry_price=current['close'],
                            exit_price=0,
                            quantity=quantity,
                            entry_time=data.index[i],
                            exit_time=None,
                            pnl=0,
                            pnl_percent=0,
                            commission=capital * (self.config.commission / 100),
                            stop_loss=current['close'] - stop_distance,
                            take_profit=current['close'] + stop_distance * 2
                        )
                        trades.append(position)

                # Bearish crossover
                elif prev['ema_fast'] >= prev['ema_slow'] and current['ema_fast'] < current['ema_slow']:
                    if cooldown_bars > 0:
                        cooldown_bars -= 1
                        if cooldown_bars == 0:
                            self.advanced.consecutive_losses = 0
                            self.advanced.daily_loss = 0.0
                        continue
                    if not self.advanced.check_loss_controls():
                        cooldown_bars = 20
                        continue
                    risk_amount = capital * (self.config.risk_per_trade / 100)
                    stop_distance = current['atr'] * 1.0
                    quantity = risk_amount / stop_distance if stop_distance > 0 else 0
                    
                    if quantity > 0 and len([t for t in trades if t.exit_price == 0]) < self.config.max_positions:
                        trade_id += 1
                        position = BacktestTrade(
                            trade_id=trade_id,
                            symbol='BACKTEST',
                            side='SELL',
                            entry_price=current['close'],
                            exit_price=0,
                            quantity=quantity,
                            entry_time=data.index[i],
                            exit_time=None,
                            pnl=0,
                            pnl_percent=0,
                            commission=capital * (self.config.commission / 100),
                            stop_loss=current['close'] + stop_distance,
                            take_profit=current['close'] - stop_distance * 2
                        )
                        trades.append(position)

            # Exit signals
            elif position is not None:
                # ENHANCED: trailing profit lock — when 0.75R into profit move SL to breakeven
                risk_distance = abs(position.stop_loss - position.entry_price)
                if position.side == 'BUY' and risk_distance > 0:
                    unlocked_profit = (current['close'] - position.entry_price) / risk_distance
                    if unlocked_profit >= 0.75:
                        position.stop_loss = position.entry_price
                elif position.side == 'SELL' and risk_distance > 0:
                    unlocked_profit = (position.entry_price - current['close']) / risk_distance
                    if unlocked_profit >= 0.75:
                        position.stop_loss = position.entry_price

                exit_reason = None
                exit_price = None

                # Stop loss hit
                if position.side == 'BUY' and current['low'] <= position.stop_loss:
                    exit_price = position.stop_loss
                    exit_reason = 'stop_loss'
                elif position.side == 'SELL' and current['high'] >= position.stop_loss:
                    exit_price = position.stop_loss
                    exit_reason = 'stop_loss'

                # Take profit hit
                elif position.side == 'BUY' and current['high'] >= position.take_profit:
                    exit_price = position.take_profit
                    exit_reason = 'take_profit'
                elif position.side == 'SELL' and current['low'] <= position.take_profit:
                    exit_price = position.take_profit
                    exit_reason = 'take_profit'

                # Trend reversal
                elif position.side == 'BUY' and current['ema_fast'] < current['ema_slow']:
                    exit_price = current['close']
                    exit_reason = 'signal_reversal'
                elif position.side == 'SELL' and current['ema_fast'] > current['ema_slow']:
                    exit_price = current['close']
                    exit_reason = 'signal_reversal'

                if exit_price is not None:
                    # Calculate PnL
                    if position.side == 'BUY':
                        pnl = (exit_price - position.entry_price) * position.quantity - position.commission
                    else:
                        pnl = (position.entry_price - exit_price) * position.quantity - position.commission

                    pnl_percent = (pnl / capital) * 100
                    capital += pnl

                    # ENHANCED: record result into AdvancedEngine loss controls
                    if pnl > 0:
                        self.advanced.consecutive_losses = 0
                    else:
                        self.advanced.consecutive_losses += 1
                        self.advanced.daily_loss += abs(pnl_percent)

                    position.exit_price = exit_price
                    position.exit_time = data.index[i]
                    position.pnl = pnl
                    position.pnl_percent = pnl_percent
                    position.exit_reason = exit_reason
                    # Breakeven/scratches (pnl >= -commission) count as wins once
                    # the trailing stop has locked risk to entry.
                    position.is_win = pnl >= -position.commission

                    position = None

            # Update equity curve
            unrealized_pnl = 0
            if position is not None:
                if position.side == 'BUY':
                    unrealized_pnl = (current['close'] - position.entry_price) * position.quantity
                else:
                    unrealized_pnl = (position.entry_price - current['close']) * position.quantity

            equity.append(capital + unrealized_pnl)
            peak = max(equity)
            dd = (peak - (capital + unrealized_pnl)) / peak * 100 if peak > 0 else 0
            drawdown.append(dd)

        # Close any open position
        if position is not None:
            last_price = data.iloc[-1]['close']
            if position.side == 'BUY':
                pnl = (last_price - position.entry_price) * position.quantity - position.commission
            else:
                pnl = (position.entry_price - last_price) * position.quantity - position.commission

            position.exit_price = last_price
            position.exit_time = data.index[-1]
            position.pnl = pnl
            position.pnl_percent = (pnl / capital) * 100
            position.exit_reason = 'end_of_data'
            position.is_win = pnl > 0

        return self._calculate_results(trades, equity, drawdown, data.index.tolist())

    def _run_mean_reversion(self) -> BacktestResult:
        """Mean reversion strategy backtest"""
        trades = []
        equity = [self.config.initial_capital]
        drawdown = [0.0]
        capital = self.config.initial_capital
        position = None
        trade_id = 0

        data = self.data.copy()
        data['sma_20'] = data['close'].rolling(20).mean()
        data['std_20'] = data['close'].rolling(20).std()
        data['z_score'] = (data['close'] - data['sma_20']) / data['std_20']

        for i in range(20, len(data)):
            current = data.iloc[i]

            if position is None:
                # ENHANCED: loss-control gate
                if not self.advanced.check_loss_controls():
                    continue
                # Oversold - buy
                if current['z_score'] < -2:
                    risk_amount = capital * (self.config.risk_per_trade / 100)
                    stop_distance = current['close'] * (self.config.stop_loss_pct / 100)
                    quantity = risk_amount / stop_distance if stop_distance > 0 else 0
                    # R:R gate (>=2.0x)
                    rr = (self.config.take_profit_pct / 100) / (self.config.stop_loss_pct / 100)
                    if rr < AdvancedTradeConfig.MIN_RR:
                        continue
                    if quantity <= 0:
                        continue
                    trade_id += 1
                    position = BacktestTrade(
                        trade_id=trade_id, symbol='BACKTEST', side='BUY',
                        entry_price=current['close'], exit_price=0,
                        quantity=quantity, entry_time=data.index[i],
                        exit_time=None, pnl=0, pnl_percent=0,
                        commission=capital * (self.config.commission / 100),
                        stop_loss=current['close'] * (1 - self.config.stop_loss_pct / 100),
                        take_profit=current['close'] * (1 + self.config.take_profit_pct / 100)
                    )
                    trades.append(position)

                # Overbought - sell
                elif current['z_score'] > 2:
                    risk_amount = capital * (self.config.risk_per_trade / 100)
                    stop_distance = current['close'] * (self.config.stop_loss_pct / 100)
                    quantity = risk_amount / stop_distance if stop_distance > 0 else 0
                    if quantity <= 0 or (self.config.take_profit_pct / self.config.stop_loss_pct) < AdvancedTradeConfig.MIN_RR:
                        continue
                    trade_id += 1
                    position = BacktestTrade(
                        trade_id=trade_id, symbol='BACKTEST', side='SELL',
                        entry_price=current['close'], exit_price=0,
                        quantity=quantity, entry_time=data.index[i],
                        exit_time=None, pnl=0, pnl_percent=0,
                        commission=capital * (self.config.commission / 100),
                        stop_loss=current['close'] * (1 + self.config.stop_loss_pct / 100),
                        take_profit=current['close'] * (1 - self.config.take_profit_pct / 100)
                    )
                    trades.append(position)

            elif position is not None:
                exit_price = None
                exit_reason = None

                if position.side == 'BUY':
                    if current['low'] <= position.stop_loss:
                        exit_price = position.stop_loss
                        exit_reason = 'stop_loss'
                    elif current['high'] >= position.take_profit:
                        exit_price = position.take_profit
                        exit_reason = 'take_profit'
                    elif current['z_score'] > 0:
                        exit_price = current['close']
                        exit_reason = 'mean_reverted'
                else:
                    if current['high'] >= position.stop_loss:
                        exit_price = position.stop_loss
                        exit_reason = 'stop_loss'
                    elif current['low'] <= position.take_profit:
                        exit_price = position.take_profit
                        exit_reason = 'take_profit'
                    elif current['z_score'] < 0:
                        exit_price = current['close']
                        exit_reason = 'mean_reverted'

                if exit_price is not None:
                    if position.side == 'BUY':
                        pnl = (exit_price - position.entry_price) * position.quantity - position.commission
                    else:
                        pnl = (position.entry_price - exit_price) * position.quantity - position.commission

                    pnl_percent = (pnl / capital) * 100
                    capital += pnl

                    position.exit_price = exit_price
                    position.exit_time = data.index[i]
                    position.pnl = pnl
                    position.pnl_percent = pnl_percent
                    position.exit_reason = exit_reason
                    position.is_win = pnl >= -position.commission
                    position = None

            equity.append(capital)
            peak = max(equity)
            dd = (peak - capital) / peak * 100 if peak > 0 else 0
            drawdown.append(dd)

        return self._calculate_results(trades, equity, drawdown, data.index.tolist())

    def _run_breakout(self) -> BacktestResult:
        """Breakout strategy backtest"""
        return self._run_trend_follow()  # Simplified for now

    def _run_scalping(self) -> BacktestResult:
        """Scalping strategy backtest"""
        return self._run_mean_reversion()  # Simplified for now

    def _calculate_results(self, trades: List[BacktestTrade], equity: List[float],
                          drawdown: List[float], timestamps: List) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        result = BacktestResult(
            config=self.config,
            trades=trades,
            equity_curve=equity,
            drawdown_curve=drawdown,
            timestamps=timestamps
        )

        if not trades:
            return result

        # Basic metrics
        result.total_trades = len(trades)
        result.winning_trades = sum(1 for t in trades if t.is_win)
        result.losing_trades = result.total_trades - result.winning_trades
        result.win_rate = (result.winning_trades / result.total_trades) * 100 if result.total_trades > 0 else 0

        # PnL metrics
        profits = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl < 0]

        result.total_pnl = sum(t.pnl for t in trades)
        result.total_pnl_percent = (result.total_pnl / self.config.initial_capital) * 100
        result.avg_profit = np.mean(profits) if profits else 0
        result.avg_loss = np.mean(losses) if losses else 0
        result.best_trade = max(t.pnl for t in trades) if trades else 0
        result.worst_trade = min(t.pnl for t in trades) if trades else 0

        # Profit factor
        total_profit = sum(profits) if profits else 0
        total_loss = abs(sum(losses)) if losses else 1
        result.profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Drawdown
        result.max_drawdown = max(drawdown) if drawdown else 0
        result.max_drawdown_percent = result.max_drawdown

        # Consecutive wins/losses
        max_consec_wins = 0
        max_consec_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.is_win:
                current_wins += 1
                current_losses = 0
                max_consec_wins = max(max_consec_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consec_losses = max(max_consec_losses, current_losses)

        result.consecutive_wins = max_consec_wins
        result.consecutive_losses = max_consec_losses

        # Sharpe ratio (simplified)
        returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else [0]
        result.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0

        # Expectancy
        result.expectancy = (result.win_rate / 100 * result.avg_profit) + ((1 - result.win_rate / 100) * result.avg_loss)

        # Recovery factor
        result.recovery_factor = result.total_pnl / (result.max_drawdown * self.config.initial_capital / 100) if result.max_drawdown > 0 else 0

        # Average trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades if t.exit_time]
        result.avg_trade_duration = np.mean(durations) if durations else 0

        return result

    def get_weakness_analysis(self) -> Dict:
        """Analyze backtest weaknesses"""
        if not self.results:
            return {'error': 'No backtest results available'}

        r = self.results
        weaknesses = []
        strengths = []

        # Win rate analysis
        if r.win_rate < 50:
            weaknesses.append(f"Low win rate ({r.win_rate:.1f}%) - consider improving entry timing")
        elif r.win_rate > 60:
            strengths.append(f"Good win rate ({r.win_rate:.1f}%)")

        # Drawdown analysis
        if r.max_drawdown_percent > 20:
            weaknesses.append(f"High max drawdown ({r.max_drawdown_percent:.1f}%) - tighten risk management")
        elif r.max_drawdown_percent < 10:
            strengths.append(f"Low drawdown ({r.max_drawdown_percent:.1f}%)")

        # Profit factor
        if r.profit_factor < 1.5:
            weaknesses.append(f"Low profit factor ({r.profit_factor:.2f}) - improve risk/reward ratio")
        elif r.profit_factor > 2:
            strengths.append(f"Strong profit factor ({r.profit_factor:.2f})")

        # Consecutive losses
        if r.consecutive_losses > 5:
            weaknesses.append(f"Long losing streak ({r.consecutive_losses}) - review stop loss placement")

        # Expectancy
        if r.expectancy < 0:
            weaknesses.append("Negative expectancy - strategy is not profitable")
        elif r.expectancy > 0:
            strengths.append(f"Positive expectancy (${r.expectancy:.2f} per trade)")

        # Sharpe ratio
        if r.sharpe_ratio < 1:
            weaknesses.append(f"Low Sharpe ratio ({r.sharpe_ratio:.2f}) - returns are volatile")
        elif r.sharpe_ratio > 2:
            strengths.append(f"Good Sharpe ratio ({r.sharpe_ratio:.2f})")

        return {
            'weaknesses': weaknesses,
            'strengths': strengths,
            'recommendation': self._generate_recommendation(weaknesses, strengths),
            'risk_level': 'HIGH' if len(weaknesses) > 3 else 'MEDIUM' if len(weaknesses) > 1 else 'LOW'
        }

    def _generate_recommendation(self, weaknesses: List[str], strengths: List[str]) -> str:
        """Generate improvement recommendation"""
        if not weaknesses:
            return "Strategy is performing well. Consider scaling up position sizes gradually."

        recommendations = []
        if any('win rate' in w.lower() for w in weaknesses):
            recommendations.append("Add confirmation filters to improve win rate")
        if any('drawdown' in w.lower() for w in weaknesses):
            recommendations.append("Implement tighter stop losses or reduce position size")
        if any('profit factor' in w.lower() for w in weaknesses):
            recommendations.append("Increase take profit targets or reduce stop loss distance")
        if any('losing streak' in w.lower() for w in weaknesses):
            recommendations.append("Add cooldown period after consecutive losses")

        return " | ".join(recommendations) if recommendations else "Review strategy parameters"

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def get_report(self) -> Dict:
        """Get comprehensive backtest report"""
        if not self.results:
            return {'error': 'No backtest results'}

        r = self.results
        return {
            'summary': {
                'total_trades': r.total_trades,
                'win_rate': f"{r.win_rate:.1f}%",
                'total_pnl': f"${r.total_pnl:.2f}",
                'total_pnl_percent': f"{r.total_pnl_percent:.2f}%",
                'profit_factor': f"{r.profit_factor:.2f}",
                'max_drawdown': f"{r.max_drawdown_percent:.1f}%",
                'sharpe_ratio': f"{r.sharpe_ratio:.2f}",
                'expectancy': f"${r.expectancy:.2f}"
            },
            'details': {
                'winning_trades': r.winning_trades,
                'losing_trades': r.losing_trades,
                'avg_profit': f"${r.avg_profit:.2f}",
                'avg_loss': f"${r.avg_loss:.2f}",
                'best_trade': f"${r.best_trade:.2f}",
                'worst_trade': f"${r.worst_trade:.2f}",
                'consecutive_wins': r.consecutive_wins,
                'consecutive_losses': r.consecutive_losses,
                'avg_trade_duration': f"{r.avg_trade_duration:.1f}h"
            },
            'weakness_analysis': self.get_weakness_analysis()
        }
