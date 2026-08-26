"""
Comprehensive Multi-Market Backtest Runner
Tests all strategies across Forex, Crypto, Commodities, and Metals
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.universal_profit_engine import UniversalProfitEngine, MARKET_CONFIGS

def print_separator(char="=", length=80):
    print(char * length)

def print_header(text):
    print_separator("=")
    print(f"  {text}")
    print_separator("=")

def print_subheader(text):
    print(f"\n  --- {text} ---")

def run_comprehensive_backtest():
    """Run comprehensive backtest across all markets"""
    
    print_header("ESMH.TRADE - COMPREHENSIVE MULTI-MARKET BACKTEST REPORT")
    print(f"  Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Initial Capital: $10,000")
    print(f"  Markets: Forex, Crypto, Commodities, Metals")
    print(f"  Strategies: Trend Follow, Mean Reversion, Breakout, Scalping, Smart Money")
    
    engine = UniversalProfitEngine(initial_capital=10000.0)
    results = engine.run_all_markets()
    
    # Print results for each market
    for market, market_results in results.items():
        config = MARKET_CONFIGS[market]
        
        print_header(f"  {config.name.upper()} MARKET RESULTS")
        print(f"  Symbols: {', '.join(config.symbols[:5])}")
        print(f"  Commission: {config.commission}% | Volatility Factor: {config.volatility_factor}")
        
        if not market_results:
            print("  No results available.")
            continue
        
        # Sort by win rate
        sorted_results = sorted(market_results, key=lambda x: x.win_rate, reverse=True)
        
        print(f"\n  {'Strategy':<20} {'Trades':>8} {'Win Rate':>10} {'PnL':>12} {'PF':>8} {'Sharpe':>8} {'Max DD':>8}")
        print_separator("-", 80)
        
        for r in sorted_results:
            pnl_str = f"${r.total_pnl:+.2f}"
            print(f"  {r.strategy_name:<20} {r.total_trades:>8} {r.win_rate:>9.1f}% {pnl_str:>12} {r.profit_factor:>7.2f} {r.sharpe_ratio:>7.2f} {r.max_drawdown:>7.1f}%")
        
        # Best strategy details
        best = sorted_results[0] if sorted_results else None
        if best:
            print_subheader(f"BEST STRATEGY: {best.strategy_name.upper()}")
            print(f"  Win Rate:          {best.win_rate:.1f}%")
            print(f"  Total Trades:      {best.total_trades}")
            print(f"  Winning/Losing:    {best.winning_trades}/{best.losing_trades}")
            print(f"  Total PnL:         ${best.total_pnl:+.2f} ({best.total_pnl_percent:+.2f}%)")
            print(f"  Profit Factor:     {best.profit_factor:.2f}")
            print(f"  Sharpe Ratio:      {best.sharpe_ratio:.2f}")
            print(f"  Max Drawdown:      {best.max_drawdown:.1f}%")
            print(f"  Expectancy:        ${best.expectancy:.2f}")
            print(f"  Avg Win:           ${best.avg_win:.2f}")
            print(f"  Avg Loss:          ${best.avg_loss:.2f}")
            print(f"  Consec Wins:       {best.consecutive_wins}")
            print(f"  Consec Losses:     {best.consecutive_losses}")
            if best.params:
                print(f"  Best Params:       {best.params}")
            
            # Exit reason breakdown
            if best.trades:
                print_subheader("EXIT REASON BREAKDOWN")
                exit_reasons = {}
                for t in best.trades:
                    reason = t.get('reason', 'unknown')
                    if reason not in exit_reasons:
                        exit_reasons[reason] = {'count': 0, 'pnl': 0}
                    exit_reasons[reason]['count'] += 1
                    exit_reasons[reason]['pnl'] += t.get('pnl', 0)
                
                for reason, data in exit_reasons.items():
                    print(f"  {reason:<20}: {data['count']:>3} trades, ${data['pnl']:>+.2f}")
    
    # Overall summary
    print_header("OVERALL BEST STRATEGIES BY MARKET")
    print(f"  {'Market':<15} {'Best Strategy':<20} {'Win Rate':>10} {'PnL':>12} {'Score':>8}")
    print_separator("-", 70)
    
    for market, best in engine.best_strategies.items():
        score = best.win_rate * 0.4 + best.profit_factor * 30 + best.sharpe_ratio * 10
        print(f"  {market:<15} {best.strategy_name:<20} {best.win_rate:>9.1f}% ${best.total_pnl:>+10.2f} {score:>7.1f}")
    
    # Overall recommendation
    print_header("RECOMMENDATIONS FOR HIGHER WIN RATE")
    print("""
  1. FOLLOWING STRATEGIES IMPROVE WIN RATE:
     - Add RSI confirmation (avoid overbought/oversold entries)
     - Use ADX > 20 filter for trend strength
     - Require volume confirmation for breakouts
     - Add multiple timeframe confluence
  
  2. RISK MANAGEMENT:
     - Use tighter stop losses (1.5x ATR instead of 2x)
     - Take profit at 2.5x risk minimum
     - Limit max positions to 3-5 concurrent trades
     - Use trailing stops after 1.5x profit
  
  3. MARKET-SPECIFIC TUNING:
     - Forex: Trade during London/NY overlap (8-16 UTC)
     - Crypto: 24h trading, focus on high volume hours
     - Metals/Commodities: Trade during US session (13-21 UTC)
  
  4. STRATEGY COMBINATION:
     - Use trend follow for strong trends
     - Use mean reversion for ranging markets
     - Switch based on ADX (trending > 25, ranging < 20)
    """)
    
    print_separator("=")
    print("  BACKTEST COMPLETE - Use these results to configure your bots")
    print_separator("=")

if __name__ == "__main__":
    run_comprehensive_backtest()
