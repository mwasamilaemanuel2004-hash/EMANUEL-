"""
Optimized Backtest using the production backtest engine
"""
import sys, os
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.backtest_engine import BacktestEngine, BacktestConfig, BacktestStrategy

def generate_realistic_data(market, periods=1000):
    """Generate realistic market data"""
    np.random.seed(hash(market) % 2**32)
    
    configs = {
        "forex": {"base": 1.1000, "vol": 0.004, "trend": 0.0001},
        "crypto": {"base": 50000, "vol": 0.035, "trend": 0.0002},
        "commodities": {"base": 2000, "vol": 0.006, "trend": 0.00005},
        "metals": {"base": 2000, "vol": 0.005, "trend": 0.00008},
    }
    
    cfg = configs.get(market, configs["crypto"])
    base, vol, trend = cfg["base"], cfg["vol"], cfg["trend"]
    
    # Generate returns with momentum and mean reversion
    returns = np.random.normal(trend, vol / np.sqrt(24), periods)
    
    # Add momentum clustering
    for i in range(5, len(returns)):
        returns[i] += 0.15 * returns[i-1] + 0.08 * returns[i-2]
    
    # Add mean reversion for forex
    if market == "forex":
        price = base * np.exp(np.cumsum(returns))
        mean_rev = base * (1 + 0.0005 * np.sin(np.arange(periods) / 80))
        price = price * 0.6 + mean_rev * 0.4
    else:
        price = base * np.exp(np.cumsum(returns))
    
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': price * (1 + np.random.uniform(-0.0005, 0.0005, periods)),
        'high': price * (1 + np.abs(np.random.normal(0, vol * 0.5, periods))),
        'low': price * (1 - np.abs(np.random.normal(0, vol * 0.5, periods))),
        'close': price,
        'volume': np.random.lognormal(10, 0.8, periods)
    }).set_index('timestamp')

def run_optimized_backtest():
    """Run optimized backtest for all markets"""
    
    print("\n" + "="*90)
    print("  ESMH.TRADE - OPTIMIZED MULTI-MARKET BACKTEST")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*90)
    
    markets = ["forex", "crypto", "commodities", "metals"]
    strategies = [BacktestStrategy.TREND_FOLLOW, BacktestStrategy.MEAN_REVERSION]
    
    all_results = {}
    
    for market in markets:
        print(f"\n  {market.upper()} MARKET")
        print(f"  {'Strategy':<20} {'Trades':>7} {'Win%':>7} {'PnL':>10} {'PF':>7} {'Sharpe':>7} {'MaxDD':>7}")
        print("  " + "-"*65)
        
        data = generate_realistic_data(market, 1000)
        market_results = []
        
        for strategy in strategies:
            # Optimized config for higher win rate
            config = BacktestConfig(
                strategy=strategy,
                initial_capital=10000.0,
                risk_per_trade=1.5,  # Lower risk for higher win rate
                max_positions=3,
                commission=0.05,
                slippage=0.02,
                stop_loss_pct=1.5,  # Tighter stop
                take_profit_pct=3.0,  # Higher reward
                trailing_stop=True,
                trailing_stop_pct=1.0
            )
            
            engine = BacktestEngine(config)
            result = engine.run(data)
            
            if result and result.total_trades > 0:
                print(f"  {strategy.value:<20} {result.total_trades:>7} {result.win_rate:>6.1f}% ${result.total_pnl:>+8.2f} {result.profit_factor:>6.2f} {result.sharpe_ratio:>6.2f} {result.max_drawdown_percent:>6.1f}%")
                market_results.append({
                    'strategy': strategy.value,
                    'trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'pnl': result.total_pnl,
                    'pf': result.profit_factor,
                    'sharpe': result.sharpe_ratio,
                    'max_dd': result.max_drawdown_percent
                })
            else:
                print(f"  {strategy.value:<20} {'No trades':>50}")
        
        if market_results:
            best = max(market_results, key=lambda x: x['win_rate'] if x['trades'] >= 3 else 0)
            all_results[market] = best
    
    # Summary
    print("\n" + "="*90)
    print("  BEST STRATEGY PER MARKET (Optimized for Win Rate)")
    print("="*90)
    print(f"  {'Market':<15} {'Strategy':<20} {'Win Rate':>10} {'PnL':>10} {'PF':>8} {'Trades':>8}")
    print("-"*75)
    
    for market, best in all_results.items():
        print(f"  {market:<15} {best['strategy']:<20} {best['win_rate']:>9.1f}% ${best['pnl']:>+8.2f} {best['pf']:>7.2f} {best['trades']:>8}")
    
    print("\n" + "="*90)
    print("  OPTIMIZATION NOTES:")
    print("  - Risk per trade reduced to 1.5% for higher win rate")
    print("  - Stop loss tightened to 1.5%")
    print("  - Take profit set to 3% (2:1 reward/risk ratio)")
    print("  - Trailing stops enabled to lock in profits")
    print("="*90)

if __name__ == "__main__":
    run_optimized_backtest()
