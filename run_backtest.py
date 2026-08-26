"""
Backtest Runner - Run and display comprehensive backtest results
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.backtest_engine import BacktestEngine, BacktestConfig, BacktestStrategy

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_subheader(text):
    print(f"\n--- {text} ---")

def run_backtest():
    """Run comprehensive backtest and display results"""
    
    print_header("ESMH.TRADE - BACKTEST RESULTS")
    
    # Run multiple strategies
    strategies = [
        (BacktestStrategy.TREND_FOLLOW, "Trend Following"),
        (BacktestStrategy.MEAN_REVERSION, "Mean Reversion"),
    ]
    
    all_results = {}
    
    for strategy, name in strategies:
        print(f"\n{'='*70}")
        print(f"  Running: {name}")
        print(f"{'='*70}")
        
        is_mr = (strategy == BacktestStrategy.MEAN_REVERSION)
        config = BacktestConfig(
            strategy=strategy,
            initial_capital=10000.0,
            risk_per_trade=2.0,
            max_positions=3,
            commission=0.1,
            slippage=0.05,
            stop_loss_pct=1.5 if is_mr else 2.0,
            take_profit_pct=3.0 if is_mr else 4.0
        )
        
        engine = BacktestEngine(config)
        data = engine.generate_sample_data(1000, mean_reverting=(strategy == BacktestStrategy.MEAN_REVERSION))
        result = engine.run()
        
        if result:
            all_results[name] = (engine, result)
            
            # Print results
            print_subheader("Performance Summary")
            print(f"  Total Trades:        {result.total_trades}")
            print(f"  Winning Trades:      {result.winning_trades}")
            print(f"  Losing Trades:       {result.losing_trades}")
            print(f"  Win Rate:            {result.win_rate:.1f}%")
            print(f"  Total PnL:           ${result.total_pnl:+.2f}")
            print(f"  Total PnL %:         {result.total_pnl_percent:+.2f}%")
            print(f"  Profit Factor:       {result.profit_factor:.2f}")
            print(f"  Sharpe Ratio:        {result.sharpe_ratio:.2f}")
            print(f"  Max Drawdown:        {result.max_drawdown_percent:.1f}%")
            print(f"  Expectancy:          ${result.expectancy:.2f}")
            
            print_subheader("Trade Details")
            print(f"  Avg Profit:          ${result.avg_profit:.2f}")
            print(f"  Avg Loss:            ${result.avg_loss:.2f}")
            print(f"  Best Trade:          ${result.best_trade:.2f}")
            print(f"  Worst Trade:         ${result.worst_trade:.2f}")
            print(f"  Consecutive Wins:    {result.consecutive_wins}")
            print(f"  Consecutive Losses:  {result.consecutive_losses}")
            print(f"  Avg Trade Duration:  {result.avg_trade_duration:.1f} hours")
            
            # Weakness analysis
            print_subheader("Weakness Analysis")
            weaknesses = engine.get_weakness_analysis()
            
            if weaknesses['strengths']:
                print("  Strengths:")
                for s in weaknesses['strengths']:
                    print(f"    + {s}")
            
            if weaknesses['weaknesses']:
                print("  Weaknesses:")
                for w in weaknesses['weaknesses']:
                    print(f"    - {w}")
            
            print(f"  Risk Level:          {weaknesses['risk_level']}")
            print(f"  Recommendation:      {weaknesses['recommendation']}")
            
            # Trade breakdown
            print_subheader("Trade Breakdown by Exit Reason")
            exit_reasons = {}
            for trade in result.trades:
                reason = trade.exit_reason
                if reason not in exit_reasons:
                    exit_reasons[reason] = {'count': 0, 'pnl': 0}
                exit_reasons[reason]['count'] += 1
                exit_reasons[reason]['pnl'] += trade.pnl
            
            for reason, data in exit_reasons.items():
                print(f"  {reason:20s}: {data['count']:3d} trades, ${data['pnl']:+.2f}")
    
    # Comparison
    if len(all_results) > 1:
        print_header("STRATEGY COMPARISON")
        print(f"{'Strategy':<25} {'Win Rate':>10} {'PnL':>12} {'Max DD':>10} {'PF':>8} {'Sharpe':>8}")
        print("-" * 75)
        for name, (engine, result) in all_results.items():
            print(f"{name:<25} {result.win_rate:>9.1f}% ${result.total_pnl:>+10.2f} {result.max_drawdown_percent:>9.1f}% {result.profit_factor:>7.2f} {result.sharpe_ratio:>7.2f}")
        
        # Best strategy
        best = max(all_results.items(), key=lambda x: x[1][1].total_pnl)
        print(f"\n  Best Strategy: {best[0]} (${best[1][1].total_pnl:+.2f})")
    
    print_header("BACKTEST COMPLETE")
    print("  All strategies tested successfully.")
    print("  Use these results to optimize your trading parameters.")
    print("="*70)

if __name__ == "__main__":
    run_backtest()
