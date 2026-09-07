"""
Universal Profit Engine - Multi-Market Trading Optimization
Tests and optimizes strategies across Forex, Crypto, Commodities, and Metals
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
from .cs_indicator_library import analyze_strategy_profile


@dataclass
class MarketConfig:
    """Market-specific configuration"""
    name: str
    symbols: List[str]
    spread: float
    commission: float
    volatility_factor: float
    trading_hours: str
    session_peaks: List[int]


# Market configurations
MARKET_CONFIGS = {
    "forex": MarketConfig(
        name="Forex",
        symbols=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"],
        spread=0.0001,
        commission=0.02,
        volatility_factor=0.8,
        trading_hours="24h",
        session_peaks=[8, 13, 16]
    ),
    "crypto": MarketConfig(
        name="Crypto",
        symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"],
        spread=0.0005,
        commission=0.1,
        volatility_factor=2.5,
        trading_hours="24h",
        session_peaks=[0, 8, 13]
    ),
    "commodities": MarketConfig(
        name="Commodities",
        symbols=["XAUUSD", "XAGUSD", "WTI", "BRENT", "NG", "COPPER"],
        spread=0.001,
        commission=0.05,
        volatility_factor=1.2,
        trading_hours="22h",
        session_peaks=[8, 13]
    ),
    "metals": MarketConfig(
        name="Metals",
        symbols=["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "COPPER", "IRON"],
        spread=0.001,
        commission=0.05,
        volatility_factor=1.0,
        trading_hours="22h",
        session_peaks=[8, 13]
    ),
    "stocks": MarketConfig(
        name="Stocks",
        symbols=["AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "META", "GOOGL"],
        spread=0.0005,
        commission=0.01,
        volatility_factor=1.1,
        trading_hours="market",
        session_peaks=[14, 16]
    ),
    "deriv": MarketConfig(
        name="Deriv Indices",
        symbols=["R_10", "R_25", "R_50", "R_75", "R_100", "VOLATILITY_75"],
        spread=0.0008,
        commission=0.0,
        volatility_factor=1.8,
        trading_hours="24h",
        session_peaks=[0, 8, 16]
    )
}


@dataclass
class StrategyResult:
    """Strategy backtest result"""
    strategy_name: str
    market: str
    symbol: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    expectancy: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    params: Dict = field(default_factory=dict)
    trades: List = field(default_factory=list)
    profile: Dict = field(default_factory=dict)


class UniversalProfitEngine:
    """
    Universal Profit Engine
    - Multi-market strategy testing
    - Adaptive parameter optimization
    - Market-specific tuning
    - Comprehensive performance reporting
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.results: Dict[str, List[StrategyResult]] = {}
        self.best_strategies: Dict[str, StrategyResult] = {}

    def generate_market_data(self, market: str, periods: int = 1000) -> pd.DataFrame:
        """Generate realistic market-specific data"""
        config = MARKET_CONFIGS.get(market)
        if not config:
            config = MARKET_CONFIGS["crypto"]

        np.random.seed(hash(market) % 2**32)

        if market == "forex":
            base_price = 1.1000
            daily_vol = 0.005 * config.volatility_factor
        elif market == "crypto":
            base_price = 50000
            daily_vol = 0.03 * config.volatility_factor
        elif market in ["commodities", "metals"]:
            base_price = 2000
            daily_vol = 0.01 * config.volatility_factor
        else:
            base_price = 100
            daily_vol = 0.01

        returns = np.random.normal(0.0001, daily_vol / np.sqrt(24), periods)

        for i in range(1, len(returns)):
            returns[i] += 0.1 * returns[i-1] * np.random.normal(0, 1)

        if market == "forex":
            price = base_price * np.exp(np.cumsum(returns))
            mean_reversion = base_price * (1 + 0.001 * np.sin(np.arange(periods) / 100))
            price = price * 0.7 + mean_reversion * 0.3
        else:
            price = base_price * np.exp(np.cumsum(returns))

        dates = pd.date_range(end=datetime.now(), periods=periods, freq='1h')

        data = pd.DataFrame({
            'timestamp': dates,
            'open': price * (1 + np.random.uniform(-0.001, 0.001, periods)),
            'high': price * (1 + np.abs(np.random.normal(0, daily_vol, periods))),
            'low': price * (1 - np.abs(np.random.normal(0, daily_vol, periods))),
            'close': price,
            'volume': np.random.lognormal(10, 1, periods)
        })

        data.set_index('timestamp', inplace=True)
        return data

    def run_all_markets(self) -> Dict[str, List[StrategyResult]]:
        """Run backtests for all markets and strategies"""
        strategies = ["trend_follow", "mean_reversion", "breakout", "scalping", "smart_money"]
        markets = ["forex", "crypto", "commodities", "metals", "stocks", "deriv"]

        for market in markets:
            self.results[market] = []
            data = self.generate_market_data(market, 1500)

            for strategy in strategies:
                result = self.optimize_strategy(market, strategy, data)
                if result:
                    self.results[market].append(result)

                    # Track best strategy per market
                    if market not in self.best_strategies or self._score_result(result) > self._score_result(self.best_strategies[market]):
                        if result.total_trades >= 10 and result.expectancy > 0:
                            self.best_strategies[market] = result

        return self.results

    def optimize_strategy(self, market: str, strategy: str, data: pd.DataFrame) -> Optional[StrategyResult]:
        """Find optimal parameters for a strategy"""
        best_result = None
        best_score = -999999

        param_ranges = self._get_param_ranges(strategy)

        from itertools import product
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())

        split = max(30, int(len(data) * 0.7))
        train_data = data.iloc[:split]
        validation_data = data.iloc[split:]

        for combo in product(*param_values):
            params = dict(zip(param_names, combo))
            result = self._run_single_backtest(market, strategy, train_data, params)

            if result and result.total_trades >= 10 and result.expectancy > 0:
                validation = self._run_single_backtest(market, strategy, validation_data, params)
                if not validation or validation.total_trades < 5:
                    continue
                score = self._score_result(validation)

                if score > best_score:
                    best_score = score
                    best_result = validation
                    best_result.params = dict(params)
                    best_result.params['train_score'] = round(self._score_result(result), 4)
                    best_result.params['validation_score'] = round(score, 4)
                    try:
                        best_result.profile = analyze_strategy_profile(validation_data).as_dict()
                    except (ValueError, KeyError):
                        best_result.profile = {}

        return best_result

    @staticmethod
    def _score_result(result: StrategyResult) -> float:
        """Score risk-adjusted out-of-sample performance, not win rate alone."""
        if result.total_trades < 5 or result.expectancy <= 0 or result.profit_factor < 1.0:
            return -1e9
        return (
            result.profit_factor * 40.0
            + result.expectancy / max(1.0, abs(result.avg_loss)) * 30.0
            + result.sharpe_ratio * 10.0
            - result.max_drawdown * 0.75
        )

    def _get_param_ranges(self, strategy: str) -> Dict:
        """Get parameter ranges for strategy optimization"""
        if strategy == "trend_follow":
            return {
                'ema_fast': [5, 10, 15, 20],
                'ema_slow': [30, 40, 50, 60],
                'atr_mult': [1.5, 2.0, 2.5]
            }
        elif strategy == "mean_reversion":
            return {
                'lookback': [10, 15, 20, 25],
                'z_threshold': [1.5, 2.0, 2.5],
                'exit_z': [0.0, 0.5]
            }
        elif strategy == "breakout":
            return {
                'lookback': [15, 20, 30, 40],
                'atr_mult': [0.8, 1.0, 1.5]
            }
        elif strategy == "scalping":
            return {
                'ema_fast': [3, 5, 7],
                'ema_slow': [10, 15, 20],
                'rsi_ob': [70, 75],
                'rsi_os': [25, 30]
            }
        elif strategy == "smart_money":
            return {
                'order_block_lookback': [10, 20, 30],
                'fvg_threshold': [0.001, 0.002],
                'liquidity_threshold': [0.005, 0.01]
            }
        return {}

    def _run_single_backtest(self, market: str, strategy: str, data: pd.DataFrame, params: Dict) -> Optional[StrategyResult]:
        """Run a single backtest"""
        try:
            config = MARKET_CONFIGS[market]
            capital = self.initial_capital

            if strategy == "trend_follow":
                return self._trend_follow(data, config, params, capital)
            elif strategy == "mean_reversion":
                return self._mean_reversion(data, config, params, capital)
            elif strategy == "breakout":
                return self._breakout(data, config, params, capital)
            elif strategy == "scalping":
                return self._scalping(data, config, params, capital)
            elif strategy == "smart_money":
                return self._smart_money(data, config, params, capital)
            else:
                return self._trend_follow(data, config, params, capital)
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return None

    def _trend_follow(self, data: pd.DataFrame, config: MarketConfig, params: Dict, capital: float) -> StrategyResult:
        """Enhanced trend following strategy"""
        result = StrategyResult(strategy_name="trend_follow", market=config.name, symbol=config.symbols[0])

        ema_fast_p = params.get('ema_fast', 20)
        ema_slow_p = params.get('ema_slow', 50)
        atr_mult = params.get('atr_mult', 2.0)

        data = data.copy()
        data['ema_fast'] = data['close'].ewm(span=ema_fast_p).mean()
        data['ema_slow'] = data['close'].ewm(span=ema_slow_p).mean()
        data['atr'] = self._calc_atr(data)
        data['rsi'] = self._calc_rsi(data)
        data['adx'] = self._calc_adx(data)
        data['trend_str'] = abs(data['ema_fast'] - data['ema_slow']) / data['ema_slow'] * 100

        position = None
        trades = []
        equity = [capital]

        for i in range(ema_slow_p + 10, len(data)):
            c = data.iloc[i]
            p = data.iloc[i-1]

            if position is None:
                # Entry with multiple confirmations
                bullish = (p['ema_fast'] <= p['ema_slow'] and c['ema_fast'] > c['ema_slow'] and
                          c['adx'] > 20 and c['rsi'] < 70 and c['trend_str'] > 0.1)
                bearish = (p['ema_fast'] >= p['ema_slow'] and c['ema_fast'] < c['ema_slow'] and
                          c['adx'] > 20 and c['rsi'] > 30 and c['trend_str'] > 0.1)

                if bullish or bearish:
                    side = 'BUY' if bullish else 'SELL'
                    stop_dist = c['atr'] * atr_mult
                    risk_amt = capital * 0.02
                    qty = risk_amt / stop_dist if stop_dist > 0 else 0

                    if qty > 0:
                        position = {
                            'side': side, 'entry': c['close'],
                            'stop': c['close'] - stop_dist if bullish else c['close'] + stop_dist,
                            'tp': c['close'] + stop_dist * 2.5 if bullish else c['close'] - stop_dist * 2.5,
                            'qty': qty
                        }
            else:
                exit_price = None
                reason = None

                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['high'] >= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                    elif c['ema_fast'] < c['ema_slow']:
                        exit_price = c['close']
                        reason = 'trend_reversal'
                else:
                    if c['high'] >= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['low'] <= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                    elif c['ema_fast'] > c['ema_slow']:
                        exit_price = c['close']
                        reason = 'trend_reversal'

                if exit_price:
                    pnl = (exit_price - position['entry']) * position['qty'] if position['side'] == 'BUY' else (position['entry'] - exit_price) * position['qty']
                    pnl -= capital * (config.commission / 100)
                    capital += pnl

                    trades.append({
                        'side': position['side'], 'entry': position['entry'],
                        'exit': exit_price, 'pnl': pnl, 'reason': reason,
                        'is_win': pnl > 0
                    })
                    position = None

            equity.append(capital)

        return self._calc_result(result, trades, equity)

    def _mean_reversion(self, data: pd.DataFrame, config: MarketConfig, params: Dict, capital: float) -> StrategyResult:
        """Enhanced mean reversion strategy"""
        result = StrategyResult(strategy_name="mean_reversion", market=config.name, symbol=config.symbols[0])

        lookback = params.get('lookback', 20)
        z_thresh = params.get('z_threshold', 2.0)
        exit_z = params.get('exit_z', 0.0)

        data = data.copy()
        data['sma'] = data['close'].rolling(lookback).mean()
        data['std'] = data['close'].rolling(lookback).std()
        data['z_score'] = (data['close'] - data['sma']) / data['std']
        data['rsi'] = self._calc_rsi(data)
        data['bb_upper'] = data['sma'] + 2 * data['std']
        data['bb_lower'] = data['sma'] - 2 * data['std']

        position = None
        trades = []
        equity = [capital]

        for i in range(lookback + 5, len(data)):
            c = data.iloc[i]

            if position is None:
                # Mean reversion entry with RSI confirmation
                buy_signal = c['z_score'] < -z_thresh and c['rsi'] < 35 and c['close'] < c['bb_lower']
                sell_signal = c['z_score'] > z_thresh and c['rsi'] > 65 and c['close'] > c['bb_upper']

                if buy_signal or sell_signal:
                    side = 'BUY' if buy_signal else 'SELL'
                    risk_amt = capital * 0.02
                    qty = risk_amt / c['close'] if c['close'] > 0 else 0

                    if qty > 0:
                        position = {
                            'side': side, 'entry': c['close'],
                            'stop': c['close'] * 0.97 if buy_signal else c['close'] * 1.03,
                            'tp': c['close'] * 1.04 if buy_signal else c['close'] * 0.96,
                            'qty': qty
                        }
            else:
                exit_price = None
                reason = None

                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['high'] >= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                    elif c['z_score'] > -exit_z:
                        exit_price = c['close']
                        reason = 'mean_reverted'
                else:
                    if c['high'] >= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['low'] <= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                    elif c['z_score'] < exit_z:
                        exit_price = c['close']
                        reason = 'mean_reverted'

                if exit_price:
                    pnl = (exit_price - position['entry']) * position['qty'] if position['side'] == 'BUY' else (position['entry'] - exit_price) * position['qty']
                    pnl -= capital * (config.commission / 100)
                    capital += pnl

                    trades.append({
                        'side': position['side'], 'entry': position['entry'],
                        'exit': exit_price, 'pnl': pnl, 'reason': reason,
                        'is_win': pnl > 0
                    })
                    position = None

            equity.append(capital)

        return self._calc_result(result, trades, equity)

    def _breakout(self, data: pd.DataFrame, config: MarketConfig, params: Dict, capital: float) -> StrategyResult:
        """Enhanced breakout strategy"""
        result = StrategyResult(strategy_name="breakout", market=config.name, symbol=config.symbols[0])

        lookback = params.get('lookback', 20)
        atr_mult = params.get('atr_mult', 1.0)

        data = data.copy()
        data['atr'] = self._calc_atr(data)
        data['high_n'] = data['high'].rolling(lookback).max()
        data['low_n'] = data['low'].rolling(lookback).min()
        data['volume_sma'] = data['volume'].rolling(lookback).mean()

        position = None
        trades = []
        equity = [capital]

        for i in range(lookback + 5, len(data)):
            c = data.iloc[i]
            p = data.iloc[i-1]

            if position is None:
                # Breakout with volume confirmation
                vol_confirm = c['volume'] > c['volume_sma'] * 1.2

                if p['high'] <= data.iloc[i-2]['high_n'] and c['high'] > c['high_n'] and vol_confirm:
                    risk_amt = capital * 0.02
                    qty = risk_amt / (c['atr'] * atr_mult) if c['atr'] > 0 else 0
                    if qty > 0:
                        position = {
                            'side': 'BUY', 'entry': c['close'],
                            'stop': c['close'] - c['atr'] * atr_mult,
                            'tp': c['close'] + c['atr'] * atr_mult * 3,
                            'qty': qty
                        }
                elif p['low'] >= data.iloc[i-2]['low_n'] and c['low'] < c['low_n'] and vol_confirm:
                    risk_amt = capital * 0.02
                    qty = risk_amt / (c['atr'] * atr_mult) if c['atr'] > 0 else 0
                    if qty > 0:
                        position = {
                            'side': 'SELL', 'entry': c['close'],
                            'stop': c['close'] + c['atr'] * atr_mult,
                            'tp': c['close'] - c['atr'] * atr_mult * 3,
                            'qty': qty
                        }
            else:
                exit_price = None
                reason = None

                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['high'] >= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                else:
                    if c['high'] >= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['low'] <= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'

                if exit_price:
                    pnl = (exit_price - position['entry']) * position['qty'] if position['side'] == 'BUY' else (position['entry'] - exit_price) * position['qty']
                    pnl -= capital * (config.commission / 100)
                    capital += pnl

                    trades.append({
                        'side': position['side'], 'entry': position['entry'],
                        'exit': exit_price, 'pnl': pnl, 'reason': reason,
                        'is_win': pnl > 0
                    })
                    position = None

            equity.append(capital)

        return self._calc_result(result, trades, equity)

    def _scalping(self, data: pd.DataFrame, config: MarketConfig, params: Dict, capital: float) -> StrategyResult:
        """Enhanced scalping strategy"""
        result = StrategyResult(strategy_name="scalping", market=config.name, symbol=config.symbols[0])

        ema_fast_p = params.get('ema_fast', 5)
        ema_slow_p = params.get('ema_slow', 15)
        rsi_ob = params.get('rsi_ob', 70)
        rsi_os = params.get('rsi_os', 30)

        data = data.copy()
        data['ema_fast'] = data['close'].ewm(span=ema_fast_p).mean()
        data['ema_slow'] = data['close'].ewm(span=ema_slow_p).mean()
        data['rsi'] = self._calc_rsi(data, period=7)
        data['atr'] = self._calc_atr(data, period=7)

        position = None
        trades = []
        equity = [capital]

        for i in range(ema_slow_p + 5, len(data)):
            c = data.iloc[i]
            p = data.iloc[i-1]

            if position is None:
                # Quick scalping entries
                if c['ema_fast'] > c['ema_slow'] and p['rsi'] < rsi_os and c['rsi'] > rsi_os:
                    risk_amt = capital * 0.01
                    qty = risk_amt / c['close'] if c['close'] > 0 else 0
                    if qty > 0:
                        position = {
                            'side': 'BUY', 'entry': c['close'],
                            'stop': c['close'] - c['atr'],
                            'tp': c['close'] + c['atr'] * 1.5,
                            'qty': qty
                        }
                elif c['ema_fast'] < c['ema_slow'] and p['rsi'] > rsi_ob and c['rsi'] < rsi_ob:
                    risk_amt = capital * 0.01
                    qty = risk_amt / c['close'] if c['close'] > 0 else 0
                    if qty > 0:
                        position = {
                            'side': 'SELL', 'entry': c['close'],
                            'stop': c['close'] + c['atr'],
                            'tp': c['close'] - c['atr'] * 1.5,
                            'qty': qty
                        }
            else:
                exit_price = None
                reason = None

                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['high'] >= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                    elif c['ema_fast'] < c['ema_slow']:
                        exit_price = c['close']
                        reason = 'ema_cross'
                else:
                    if c['high'] >= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['low'] <= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                    elif c['ema_fast'] > c['ema_slow']:
                        exit_price = c['close']
                        reason = 'ema_cross'

                if exit_price:
                    pnl = (exit_price - position['entry']) * position['qty'] if position['side'] == 'BUY' else (position['entry'] - exit_price) * position['qty']
                    pnl -= capital * (config.commission / 100)
                    capital += pnl

                    trades.append({
                        'side': position['side'], 'entry': position['entry'],
                        'exit': exit_price, 'pnl': pnl, 'reason': reason,
                        'is_win': pnl > 0
                    })
                    position = None

            equity.append(capital)

        return self._calc_result(result, trades, equity)

    def _smart_money(self, data: pd.DataFrame, config: MarketConfig, params: Dict, capital: float) -> StrategyResult:
        """Smart money concepts strategy"""
        result = StrategyResult(strategy_name="smart_money", market=config.name, symbol=config.symbols[0])

        ob_lookback = params.get('order_block_lookback', 20)
        fvg_thresh = params.get('fvg_threshold', 0.001)

        data = data.copy()
        data['atr'] = self._calc_atr(data)
        data['rsi'] = self._calc_rsi(data)
        data['volume_sma'] = data['volume'].rolling(20).mean()

        # Detect order blocks
        data['ob_bull'] = False
        data['ob_bear'] = False

        for i in range(ob_lookback, len(data)):
            # Bullish order block: last bearish candle before strong bullish move
            if (data.iloc[i-1]['close'] < data.iloc[i-1]['open'] and
                data.iloc[i]['close'] > data.iloc[i]['open'] and
                data.iloc[i]['close'] > data.iloc[i-1]['high'] and
                data.iloc[i]['volume'] > data.iloc[i]['volume_sma'] * 1.5):
                data.iloc[i-1, data.columns.get_loc('ob_bull')] = True

            # Bearish order block
            if (data.iloc[i-1]['close'] > data.iloc[i-1]['open'] and
                data.iloc[i]['close'] < data.iloc[i]['open'] and
                data.iloc[i]['close'] < data.iloc[i-1]['low'] and
                data.iloc[i]['volume'] > data.iloc[i]['volume_sma'] * 1.5):
                data.iloc[i-1, data.columns.get_loc('ob_bear')] = True

        position = None
        trades = []
        equity = [capital]

        for i in range(ob_lookback + 10, len(data)):
            c = data.iloc[i]

            if position is None:
                # Look for price returning to order blocks
                for j in range(max(0, i-ob_lookback), i):
                    ob = data.iloc[j]
                    if ob['ob_bull'] and c['low'] <= ob['high'] and c['low'] >= ob['low'] and c['rsi'] < 40:
                        risk_amt = capital * 0.02
                        qty = risk_amt / c['atr'] if c['atr'] > 0 else 0
                        if qty > 0:
                            position = {
                                'side': 'BUY', 'entry': c['close'],
                                'stop': ob['low'] - c['atr'],
                                'tp': c['close'] + c['atr'] * 3,
                                'qty': qty
                            }
                        break
                    elif ob['ob_bear'] and c['high'] >= ob['low'] and c['high'] <= ob['high'] and c['rsi'] > 60:
                        risk_amt = capital * 0.02
                        qty = risk_amt / c['atr'] if c['atr'] > 0 else 0
                        if qty > 0:
                            position = {
                                'side': 'SELL', 'entry': c['close'],
                                'stop': ob['high'] + c['atr'],
                                'tp': c['close'] - c['atr'] * 3,
                                'qty': qty
                            }
                        break
            else:
                exit_price = None
                reason = None

                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['high'] >= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'
                else:
                    if c['high'] >= position['stop']:
                        exit_price = position['stop']
                        reason = 'stop_loss'
                    elif c['low'] <= position['tp']:
                        exit_price = position['tp']
                        reason = 'take_profit'

                if exit_price:
                    pnl = (exit_price - position['entry']) * position['qty'] if position['side'] == 'BUY' else (position['entry'] - exit_price) * position['qty']
                    pnl -= capital * (config.commission / 100)
                    capital += pnl

                    trades.append({
                        'side': position['side'], 'entry': position['entry'],
                        'exit': exit_price, 'pnl': pnl, 'reason': reason,
                        'is_win': pnl > 0
                    })
                    position = None

            equity.append(capital)

        return self._calc_result(result, trades, equity)

    def _calc_result(self, result: StrategyResult, trades: List, equity: List[float]) -> StrategyResult:
        """Calculate final results"""
        if not trades:
            return result

        result.total_trades = len(trades)
        result.winning_trades = sum(1 for t in trades if t['is_win'])
        result.losing_trades = result.total_trades - result.winning_trades
        result.win_rate = (result.winning_trades / result.total_trades) * 100 if result.total_trades > 0 else 0

        profits = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] < 0]

        result.total_pnl = sum(t['pnl'] for t in trades)
        result.total_pnl_percent = (result.total_pnl / self.initial_capital) * 100
        result.avg_win = np.mean(profits) if profits else 0
        result.avg_loss = np.mean(losses) if losses else 0

        total_profit = sum(profits) if profits else 0
        total_loss = abs(sum(losses)) if losses else 1
        result.profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Drawdown
        peak = equity[0]
        max_dd = 0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak * 100
            if dd > max_dd:
                max_dd = dd
        result.max_drawdown = max_dd

        # Sharpe
        returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else [0]
        result.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0

        # Expectancy
        result.expectancy = (result.win_rate / 100 * result.avg_win) + ((1 - result.win_rate / 100) * result.avg_loss)

        # Consecutive
        max_wins = max_losses = cur_wins = cur_losses = 0
        for t in trades:
            if t['is_win']:
                cur_wins += 1
                cur_losses = 0
                max_wins = max(max_wins, cur_wins)
            else:
                cur_losses += 1
                cur_wins = 0
                max_losses = max(max_losses, cur_losses)
        result.consecutive_wins = max_wins
        result.consecutive_losses = max_losses

        result.trades = trades
        return result

    def _calc_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def _calc_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calc_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX"""
        plus_dm = data['high'].diff()
        minus_dm = -data['low'].diff()
        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0)
        minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0)

        atr = self._calc_atr(data, period)
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        return dx.rolling(period).mean()
