# ============================================
# ESH.TRADE - EXCHANGE MANAGER (REAL + DEMO)
# ============================================
# backend/app/exchanges/exchange_manager.py
# Version: 5.0.0 - Micro Trading Enabled

import asyncio
from typing import Dict, Optional, Any, List, Tuple
from enum import Enum
from loguru import logger
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_DOWN
import uuid

from .binance import BinanceExchange, create_binance_exchange, TradingConfig
from .base_exchange import ExchangeConfig


class TradingEnvironment(str, Enum):
    """Trading environment types"""
    REAL = "real"
    DEMO = "demo"
    TESTNET = "testnet"
    PAPER = "paper"


class TradingLevel(str, Enum):
    """Trading levels based on capital"""
    MICRO = "micro"  # $5 - $50
    MINI = "mini"    # $50 - $500
    STANDARD = "standard"  # $500 - $5000
    PRO = "pro"      # $5000 - $50000
    VIP = "vip"      # $50000+


class MicroTradingConfig:
    """Configuration for micro trading with $5 minimum"""
    
    def __init__(self, initial_capital: float = 5.0):
        self.initial_capital = initial_capital
        self.min_trade_amount = 5.0  # Minimum trade amount
        self.max_trade_amount = initial_capital * 0.2  # 20% per trade
        self.min_position_size = 0.0001  # Minimum position size
        self.max_position_size = initial_capital * 0.5  # 50% max position
        self.risk_per_trade = 1.0  # 1% risk per trade
        self.max_daily_loss = 5.0  # 5% daily loss limit
        self.max_open_positions = 2  # Maximum concurrent positions
        self.compounding_enabled = True  # Enable profit compounding
        self.smart_position_sizing = True  # Automatic position sizing
        self.use_all_balance = False  # Don't use all balance
        self.reserve_balance = 0.5  # Keep $0.50 reserve
        self.fee_percentage = 0.1  # 0.1% trading fee
        self.slippage_percentage = 0.05  # 0.05% slippage
        self.profit_reinvest_percentage = 80  # Reinvest 80% of profits
        self.stop_loss_percentage = 2.0  # 2% stop loss
        self.take_profit_percentage = 4.0  # 4% take profit
        self.trailing_stop_percentage = 1.5  # 1.5% trailing stop
        
        # Supported symbols for micro trading
        self.micro_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT',
            'ADAUSDT', 'DOGEUSDT', 'SOLUSDT', 'MATICUSDT',
            'LTCUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT'
        ]
        
        # Minimum quantities for micro trading
        self.min_quantities = {
            'BTCUSDT': 0.00001,  # ~$0.50
            'ETHUSDT': 0.0001,   # ~$0.30
            'BNBUSDT': 0.001,    # ~$0.30
            'XRPUSDT': 0.1,      # ~$0.05
            'ADAUSDT': 0.1,      # ~$0.03
            'DOGEUSDT': 1.0,     # ~$0.08
            'SOLUSDT': 0.01,     # ~$0.20
            'MATICUSDT': 0.1,    # ~$0.08
            'LTCUSDT': 0.001,    # ~$0.08
            'DOTUSDT': 0.01,     # ~$0.06
            'AVAXUSDT': 0.01,    # ~$0.15
            'LINKUSDT': 0.01,    # ~$0.14
        }


class ExchangeManager:
    """Manages both real and demo exchange instances"""
    
    def __init__(self):
        self.exchanges: Dict[str, Dict[str, Any]] = {}
        self.active_exchange: Optional[str] = None
        self.default_environment = TradingEnvironment.DEMO
        self.micro_trading_enabled = True
        self.micro_configs: Dict[str, MicroTradingConfig] = {}
        
        logger.info("🔄 Exchange Manager initialized")
        logger.info("💵 Micro trading enabled - minimum $5 USD")
    
    def create_real_exchange(
        self,
        api_key: str,
        secret_key: str,
        name: str = "real_binance",
        initial_capital: float = 5.0,
        trading_config: Optional[TradingConfig] = None,
        micro_config: Optional[MicroTradingConfig] = None
    ) -> BinanceExchange:
        """Create real trading exchange with micro trading support"""
        
        # Determine trading level based on capital
        trading_level = self._determine_trading_level(initial_capital)
        
        # Create micro trading config if not provided
        if micro_config is None:
            micro_config = MicroTradingConfig(initial_capital=initial_capital)
        
        # Adjust trading config for micro trading
        if trading_config is None:
            trading_config = self._create_micro_trading_config(trading_level, micro_config)
        
        exchange = create_binance_exchange(
            api_key=api_key,
            secret_key=secret_key,
            testnet=False,
            trading_config=trading_config
        )
        
        self.exchanges[name] = {
            'exchange': exchange,
            'environment': TradingEnvironment.REAL,
            'config': trading_config,
            'micro_config': micro_config,
            'trading_level': trading_level,
            'initial_capital': initial_capital,
            'current_capital': initial_capital,
            'created_at': datetime.now(timezone.utc),
            'is_active': False
        }
        
        self.micro_configs[name] = micro_config
        
        logger.warning(f"🚀 REAL trading exchange created: {name}")
        logger.warning(f"   💰 Initial capital: ${initial_capital}")
        logger.warning(f"   📊 Trading level: {trading_level.value.upper()}")
        logger.warning(f"   ⚠️  This will trade with REAL money!")
        
        return exchange
    
    def create_demo_exchange(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        name: str = "demo_binance",
        initial_capital: float = 10000.0,
        trading_config: Optional[TradingConfig] = None
    ) -> BinanceExchange:
        """Create demo/testnet exchange"""
        
        demo_config = trading_config or TradingConfig(
            max_retries=3,
            retry_delay=1.0,
            max_orders_per_second=20,
            max_orders_per_day=200000,
            min_order_value=5.0,
            max_order_value=1000000.0,
            enable_risk_management=True,
            max_position_size=200000.0,
            max_leverage=5.0,
            stop_loss_percentage=5.0,
            take_profit_percentage=10.0,
        )
        
        exchange = create_binance_exchange(
            api_key=api_key or "demo_api_key",
            secret_key=secret_key or "demo_secret_key",
            testnet=True,
            trading_config=demo_config
        )
        
        self.exchanges[name] = {
            'exchange': exchange,
            'environment': TradingEnvironment.DEMO,
            'config': demo_config,
            'trading_level': TradingLevel.STANDARD,
            'initial_capital': initial_capital,
            'current_capital': initial_capital,
            'created_at': datetime.now(timezone.utc),
            'is_active': False
        }
        
        logger.info(f"🎮 DEMO exchange created: {name}")
        
        return exchange
    
    def create_paper_exchange(
        self,
        name: str = "paper_binance",
        initial_balance: float = 5.0,
        trading_config: Optional[TradingConfig] = None
    ) -> 'PaperTradingExchange':
        """Create paper trading exchange with $5 minimum"""
        
        from .paper_exchange import PaperTradingExchange
        
        paper_config = trading_config or TradingConfig(
            max_orders_per_second=100,
            max_orders_per_day=1000000,
            min_order_value=5.0,
            enable_risk_management=True,
            max_position_size=initial_balance * 2,
        )
        
        exchange = PaperTradingExchange(
            initial_balance=initial_balance,
            trading_config=paper_config
        )
        
        self.exchanges[name] = {
            'exchange': exchange,
            'environment': TradingEnvironment.PAPER,
            'config': paper_config,
            'trading_level': self._determine_trading_level(initial_balance),
            'initial_capital': initial_balance,
            'current_capital': initial_balance,
            'created_at': datetime.now(timezone.utc),
            'is_active': False
        }
        
        logger.info(f"📊 PAPER trading exchange created: {name}")
        logger.info(f"   💰 Initial balance: ${initial_balance}")
        
        return exchange
    
    def _determine_trading_level(self, capital: float) -> TradingLevel:
        """Determine trading level based on capital"""
        if capital < 50:
            return TradingLevel.MICRO
        elif capital < 500:
            return TradingLevel.MINI
        elif capital < 5000:
            return TradingLevel.STANDARD
        elif capital < 50000:
            return TradingLevel.PRO
        else:
            return TradingLevel.VIP
    
    def _create_micro_trading_config(
        self, 
        trading_level: TradingLevel, 
        micro_config: MicroTradingConfig
    ) -> TradingConfig:
        """Create trading config for micro trading"""
        
        if trading_level == TradingLevel.MICRO:
            # Ultra conservative for $5-$50
            return TradingConfig(
                max_retries=3,
                retry_delay=1.0,
                max_orders_per_second=2,
                max_orders_per_day=50,
                min_order_value=micro_config.min_trade_amount,
                max_order_value=micro_config.max_trade_amount,
                enable_risk_management=True,
                max_position_size=micro_config.max_position_size,
                max_leverage=1.0,
                stop_loss_percentage=micro_config.stop_loss_percentage,
                take_profit_percentage=micro_config.take_profit_percentage,
                trailing_stop_percentage=micro_config.trailing_stop_percentage,
                max_slippage_percentage=micro_config.slippage_percentage,
            )
        elif trading_level == TradingLevel.MINI:
            # Conservative for $50-$500
            return TradingConfig(
                max_retries=3,
                retry_delay=1.0,
                max_orders_per_second=5,
                max_orders_per_day=200,
                min_order_value=10.0,
                max_order_value=100.0,
                enable_risk_management=True,
                max_position_size=micro_config.max_position_size,
                max_leverage=1.0,
                stop_loss_percentage=3.0,
                take_profit_percentage=6.0,
                trailing_stop_percentage=2.0,
                max_slippage_percentage=0.3,
            )
        else:
            # Standard for $500+
            return TradingConfig(
                max_retries=3,
                retry_delay=1.0,
                max_orders_per_second=10,
                max_orders_per_day=1000,
                min_order_value=50.0,
                max_order_value=500.0,
                enable_risk_management=True,
                max_position_size=micro_config.max_position_size,
                max_leverage=2.0,
                stop_loss_percentage=2.0,
                take_profit_percentage=4.0,
                trailing_stop_percentage=1.5,
                max_slippage_percentage=0.2,
            )
    
    async def place_micro_trade(
        self,
        exchange_name: str,
        symbol: str,
        side: str,
        amount_usd: Optional[float] = None,
        use_smart_sizing: bool = True
    ) -> Optional[Dict]:
        """Place micro trade with smart position sizing"""
        
        exchange_info = self.exchanges.get(exchange_name)
        if not exchange_info:
            logger.error(f"Exchange not found: {exchange_name}")
            return None
        
        exchange = exchange_info['exchange']
        micro_config = exchange_info.get('micro_config')
        current_capital = exchange_info.get('current_capital', 0)
        
        # Validate minimum capital
        if current_capital < 5.0:
            logger.error(f"Insufficient capital: ${current_capital:.2f} (minimum $5.00)")
            return None
        
        # Determine trade amount
        if amount_usd is None:
            if use_smart_sizing and micro_config:
                amount_usd = self._calculate_smart_position_size(
                    current_capital, 
                    micro_config
                )
            else:
                amount_usd = min(
                    micro_config.min_trade_amount if micro_config else 5.0,
                    current_capital * 0.2
                )
        
        # Validate amount
        if amount_usd < 5.0:
            logger.error(f"Minimum trade amount is $5.00, got ${amount_usd:.2f}")
            return None
        
        if amount_usd > current_capital:
            logger.error(f"Trade amount ${amount_usd:.2f} exceeds capital ${current_capital:.2f}")
            return None
        
        # Get current price
        ticker = await exchange.get_ticker(symbol)
        if not ticker or ticker.last <= 0:
            logger.error(f"Unable to get price for {symbol}")
            return None
        
        # Calculate quantity
        quantity = amount_usd / ticker.last
        
        # Round to minimum quantity
        if micro_config and symbol in micro_config.min_quantities:
            min_qty = micro_config.min_quantities[symbol]
            quantity = max(quantity, min_qty)
        
        # Apply fees and slippage
        if micro_config:
            fee_amount = amount_usd * (micro_config.fee_percentage / 100)
            slippage_amount = amount_usd * (micro_config.slippage_percentage / 100)
            total_cost = amount_usd + fee_amount + slippage_amount
            
            if total_cost > current_capital:
                logger.warning(f"Total cost ${total_cost:.2f} exceeds capital ${current_capital:.2f}")
                # Adjust quantity
                adjusted_amount = amount_usd - fee_amount - slippage_amount
                quantity = adjusted_amount / ticker.last
        
        # Place order
        order_result = await exchange.place_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type='market'
        )
        
        if order_result:
            # Update capital
            if side.upper() == 'BUY':
                exchange_info['current_capital'] -= amount_usd
            else:
                exchange_info['current_capital'] += amount_usd
            
            logger.info(f"✅ Micro trade placed: {side} {quantity} {symbol} @ ${ticker.last:.2f}")
            logger.info(f"   💰 Trade amount: ${amount_usd:.2f}")
            logger.info(f"   📊 Remaining capital: ${exchange_info['current_capital']:.2f}")
            
            return {
                'order': order_result,
                'amount_usd': amount_usd,
                'quantity': quantity,
                'price': ticker.last,
                'remaining_capital': exchange_info['current_capital']
            }
        
        return None
    
    def _calculate_smart_position_size(
        self, 
        capital: float, 
        micro_config: MicroTradingConfig
    ) -> float:
        """Calculate smart position size based on capital"""
        
        if not micro_config.smart_position_sizing:
            return micro_config.min_trade_amount
        
        # Base position size
        base_size = capital * 0.1  # 10% of capital
        
        # Adjust based on risk
        risk_adjusted = base_size * (micro_config.risk_per_trade / 100)
        
        # Ensure within limits
        position_size = max(
            micro_config.min_trade_amount,
            min(risk_adjusted, micro_config.max_trade_amount)
        )
        
        # Keep reserve balance
        if micro_config.reserve_balance > 0:
            available = capital - micro_config.reserve_balance
            position_size = min(position_size, available)
        
        return round(position_size, 2)
    
    async def get_micro_trading_summary(self, exchange_name: str) -> Dict:
        """Get micro trading summary"""
        
        exchange_info = self.exchanges.get(exchange_name)
        if not exchange_info:
            return {}
        
        return {
            'environment': exchange_info['environment'].value,
            'trading_level': exchange_info['trading_level'].value,
            'initial_capital': exchange_info['initial_capital'],
            'current_capital': exchange_info['current_capital'],
            'profit_loss': exchange_info['current_capital'] - exchange_info['initial_capital'],
            'profit_loss_percentage': ((exchange_info['current_capital'] - exchange_info['initial_capital']) / exchange_info['initial_capital']) * 100,
            'micro_trading_enabled': self.micro_trading_enabled,
            'minimum_trade': 5.0,
            'can_trade': exchange_info['current_capital'] >= 5.0
        }
    
    def get_exchange(self, name: Optional[str] = None) -> Optional[Any]:
        """Get exchange by name or active exchange"""
        if name:
            return self.exchanges.get(name, {}).get('exchange')
        return self.get_active_exchange()
    
    def get_active_exchange(self) -> Optional[Any]:
        """Get currently active exchange"""
        for name, info in self.exchanges.items():
            if info.get('is_active'):
                return info['exchange']
        return None
    
    def set_active_exchange(self, name: str) -> bool:
        """Set active exchange"""
        if name not in self.exchanges:
            logger.error(f"Exchange not found: {name}")
            return False
        
        for info in self.exchanges.values():
            info['is_active'] = False
        
        self.exchanges[name]['is_active'] = True
        self.active_exchange = name
        
        env = self.exchanges[name]['environment']
        logger.info(f"✅ Active exchange set to: {name} ({env.value.upper()})")
        
        if env == TradingEnvironment.REAL:
            logger.warning("⚠️  REAL trading active - be careful!")
        
        return True
    
    def list_exchanges(self) -> List[Dict]:
        """List all exchanges"""
        return [
            {
                'name': name,
                'environment': info['environment'].value,
                'trading_level': info.get('trading_level', TradingLevel.STANDARD).value,
                'initial_capital': info.get('initial_capital', 0),
                'current_capital': info.get('current_capital', 0),
                'is_active': info['is_active'],
                'created_at': info['created_at'].isoformat()
            }
            for name, info in self.exchanges.items()
        ]
    
    async def close_all(self):
        """Close all exchange connections"""
        for name, info in self.exchanges.items():
            exchange = info['exchange']
            if hasattr(exchange, 'close'):
                await exchange.close()
                logger.info(f"Closed exchange: {name}")
    
    async def health_check_all(self) -> Dict:
        """Health check all exchanges"""
        results = {}
        
        for name, info in self.exchanges.items():
            exchange = info['exchange']
            env = info['environment'].value
            
            try:
                is_healthy = await exchange.ping()
                results[name] = {
                    'environment': env,
                    'healthy': is_healthy,
                    'status': '✅ Online' if is_healthy else '❌ Offline',
                    'can_trade_micro': info.get('current_capital', 0) >= 5.0
                }
            except Exception as e:
                results[name] = {
                    'environment': env,
                    'healthy': False,
                    'status': f'❌ Error: {str(e)}',
                    'can_trade_micro': False
                }
        
        return results


# ============================================
# PAPER TRADING EXCHANGE (SIMULATED)
# ============================================

class PaperTradingExchange:
    """Simulated exchange for paper trading with $5 minimum"""
    
    def __init__(self, initial_balance: float = 5.0, trading_config: Optional[TradingConfig] = None):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trading_config = trading_config or TradingConfig()
        
        self.positions: Dict[str, Dict] = {}
        self.orders: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.market_prices: Dict[str, float] = {}
        
        # Micro trading support
        self.min_trade_amount = 5.0
        self.fee_percentage = 0.1
        self.compounding_enabled = True
        self.profit_reinvest_percentage = 80
        
        logger.info(f"📊 Paper Trading initialized with ${initial_balance}")
        logger.info(f"   💵 Minimum trade: ${self.min_trade_amount}")
    
    async def ping(self) -> bool:
        return True
    
    async def get_ticker(self, symbol: str):
        from .base_exchange import Ticker
        
        price = self.market_prices.get(symbol, 100.0)
        
        return Ticker(
            symbol=symbol,
            bid=price * 0.999,
            ask=price * 1.001,
            last=price,
            high=price * 1.01,
            low=price * 0.99,
            volume=1000,
            change=price * 0.001,
            change_percent=0.1
        )
    
    async def place_order(self, symbol, side, quantity, order_type='market', price=None):
        from .base_exchange import OrderResult, OrderStatus
        
        current_price = self.market_prices.get(symbol, price or 100.0)
        execution_price = price or current_price
        
        cost = execution_price * quantity
        
        # Check minimum trade amount
        if cost < self.min_trade_amount:
            logger.error(f"Minimum trade amount is ${self.min_trade_amount}, got ${cost:.2f}")
            return None
        
        # Check balance
        if side.upper() == 'BUY' and cost > self.balance:
            logger.error(f"Insufficient balance: ${self.balance:.2f} < ${cost:.2f}")
            return None
        
        # Apply fees
        fee = cost * (self.fee_percentage / 100)
        total_cost = cost + fee
        
        # Update balance
        if side.upper() == 'BUY':
            if total_cost > self.balance:
                logger.error(f"Insufficient balance with fees: ${self.balance:.2f} < ${total_cost:.2f}")
                return None
            self.balance -= total_cost
        else:
            self.balance += cost - fee
        
        # Create order result
        order = OrderResult(
            order_id=f"PAPER_{uuid.uuid4().hex[:8]}",
            symbol=symbol,
            side=side.lower(),
            order_type=order_type,
            price=execution_price,
            quantity=quantity,
            filled_quantity=quantity,
            filled_price=execution_price,
            status=OrderStatus.FILLED.value
        )
        
        # Track order
        self.orders.append(order.__dict__)
        self.trade_history.append({
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': execution_price,
            'cost': cost,
            'fee': fee,
            'timestamp': datetime.now(timezone.utc)
        })
        
        # Update position
        self._update_position(symbol, side, quantity, execution_price)
        
        # Apply compounding
        if self.compounding_enabled and side.upper() == 'SELL':
            profit = self._calculate_position_profit(symbol)
            if profit > 0:
                reinvest = profit * (self.profit_reinvest_percentage / 100)
                self.balance += reinvest
                logger.info(f"   📈 Profit compounded: ${reinvest:.2f}")
        
        return order
    
    def _update_position(self, symbol: str, side: str, quantity: float, price: float):
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'realized_pnl': 0,
                'total_fees': 0
            }
        
        position = self.positions[symbol]
        
        if side.upper() == 'BUY':
            total_cost = position['avg_price'] * position['quantity'] + price * quantity
            position['quantity'] += quantity
            position['avg_price'] = total_cost / position['quantity'] if position['quantity'] > 0 else 0
        else:
            if position['quantity'] >= quantity:
                pnl = (price - position['avg_price']) * quantity
                position['realized_pnl'] += pnl
                position['quantity'] -= quantity
    
    def _calculate_position_profit(self, symbol: str) -> float:
        position = self.positions.get(symbol, {})
        return position.get('realized_pnl', 0)
    
    async def get_balance(self, asset: str = "USDT"):
        from .base_exchange import Balance
        
        return Balance(
            asset=asset,
            free=self.balance,
            used=0,
            total=self.balance
        )
    
    async def set_market_price(self, symbol: str, price: float):
        self.market_prices[symbol] = price
    
    async def get_trading_summary(self) -> Dict:
        """Get trading summary"""
        total_pnl = sum(p.get('realized_pnl', 0) for p in self.positions.values())
        total_fees = sum(t.get('fee', 0) for t in self.trade_history)
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_pnl': total_pnl,
            'total_fees': total_fees,
            'total_trades': len(self.trade_history),
            'win_rate': self._calculate_win_rate(),
            'compounding_enabled': self.compounding_enabled
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        if not self.trade_history:
            return 0.0
        
        profitable_trades = sum(1 for t in self.trade_history if t.get('side') == 'SELL')
        total_trades = len(self.trade_history)
        return (profitable_trades / total_trades) * 100 if total_trades > 0 else 0.0
    
    async def close(self):
        summary = await self.get_trading_summary()
        logger.info(f"📊 Paper trading closed")
        logger.info(f"   💰 Final balance: ${summary['current_balance']:.2f}")
        logger.info(f"   📈 Total PnL: ${summary['total_pnl']:.2f}")
        logger.info(f"   🏆 Win rate: {summary['win_rate']:.1f}%")


# ============================================
# USAGE EXAMPLE
# ============================================

async def main():
    """Example usage with micro trading"""
    
    manager = ExchangeManager()
    
    # Create paper trading with $5
    paper = manager.create_paper_exchange(
        name="paper_micro",
        initial_balance=5.0
    )
    
    # Set simulated prices
    await paper.set_market_price("BTCUSDT", 50000)
    await paper.set_market_price("ETHUSDT", 3000)
    await paper.set_market_price("DOGEUSDT", 0.08)
    
    # Test micro trades
    print("\n📊 Micro Trading Test ($5.00 starting)")
    print("=" * 50)
    
    # Trade 1: Buy DOGE with $1
    order1 = await paper.place_order("DOGEUSDT", "BUY", 12.5, price=0.08)
    if order1:
        print(f"\n✅ Trade 1: Bought 12.5 DOGE @ $0.08 = $1.00")
    
    # Update price (profit)
    await paper.set_market_price("DOGEUSDT", 0.10)
    
    # Trade 2: Sell DOGE at profit
    order2 = await paper.place_order("DOGEUSDT", "SELL", 12.5, price=0.10)
    if order2:
        print(f"✅ Trade 2: Sold 12.5 DOGE @ $0.10 = $1.25")
        print(f"   📈 Profit: $0.25 (25% return!)")
    
    # Get summary
    summary = await paper.get_trading_summary()
    balance = await paper.get_balance()
    
    print(f"\n📊 Trading Summary")
    print(f"   💰 Current balance: ${balance.total:.2f}")
    print(f"   📈 Total PnL: ${summary['total_pnl']:.2f}")
    print(f"   🏆 Win rate: {summary['win_rate']:.1f}%")
    print(f"   📊 Total trades: {summary['total_trades']}")
    
    # Show capital growth
    growth = ((balance.total - 5.0) / 5.0) * 100
    print(f"\n💎 Capital Growth: {growth:.1f}%")
    print(f"   Started with: $5.00")
    print(f"   Now have: ${balance.total:.2f}")
    
    await manager.close_all()


if __name__ == "__main__":
    asyncio.run(main())


# ============================================
# EXPORTS
# ============================================

__all__ = [
    'ExchangeManager',
    'TradingEnvironment',
    'TradingLevel',
    'MicroTradingConfig',
    'PaperTradingExchange',
    'create_binance_exchange',
]