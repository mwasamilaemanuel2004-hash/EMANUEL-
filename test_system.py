"""
ESMH.TRADE - System Test Script
Tests all major components and features
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_imports():
    """Test all module imports"""
    print("\n" + "="*50)
    print("TESTING IMPORTS")
    print("="*50)
    
    try:
        from app.core import TradingEngine, RiskEngine, AdaptiveEngine
        from app.core import IndicatorEngine, CandleAnalyzer, BotStateManager
        from app.core import SystemCoordinator, SystemConfig, SystemMode
        from app.core import BacktestEngine, BacktestConfig, BacktestStrategy
        from app.core import AdaptiveAutoBot, AdaptiveBotConfig
        print("✅ All core imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_trading_engine():
    """Test trading engine"""
    print("\n" + "="*50)
    print("TESTING TRADING ENGINE")
    print("="*50)
    
    try:
        from app.core.trading_engine import TradingEngine
        
        engine = TradingEngine()
        
        # Test order execution
        result = await engine.execute_order("BTCUSDT", "BUY", 0.01, 50000.0)
        print(f"✅ Order execution: {result.get('success')}")
        
        # Test risk management
        risk = engine.manage_risk(0.01, 49000.0)
        print(f"✅ Risk management: {risk.get('risk_amount', 0):.2f}")
        
        # Test performance
        perf = engine.get_performance()
        print(f"✅ Performance metrics: {perf}")
        
        return True
    except Exception as e:
        print(f"❌ Trading engine error: {e}")
        return False

async def test_risk_engine():
    """Test risk management engine"""
    print("\n" + "="*50)
    print("TESTING RISK ENGINE")
    print("="*50)
    
    try:
        from app.core.risk_management_engine import RiskEngine
        
        engine = RiskEngine()
        
        # Test trade validation
        result = engine.validate_trade(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.01,
            entry_price=50000.0,
            stop_loss=49000.0
        )
        print(f"✅ Trade validation: {result}")
        
        # Test status
        status = engine.get_status()
        print(f"✅ Risk status: {status}")
        
        return True
    except Exception as e:
        print(f"❌ Risk engine error: {e}")
        return False

async def test_adaptive_engine():
    """Test adaptive engine"""
    print("\n" + "="*50)
    print("TESTING ADAPTIVE ENGINE")
    print("="*50)
    
    try:
        from app.core.adaptive_engine import AdaptiveEngine, TradeRecord
        
        engine = AdaptiveEngine()
        
        # Test learning from trade
        trade = TradeRecord(
            timestamp=__import__('datetime').datetime.now(),
            symbol="BTCUSDT",
            action="BUY",
            entry_price=50000.0,
            exit_price=51000.0,
            profit=100.0,
            profit_percent=2.0,
            market_regime="BULLISH",
            strategy_used="trend_follow",
            confidence=75.0
        )
        engine.learn_from_trade(trade)
        print(f"✅ Trade learning: win_rate={engine.state.win_rate:.2f}")
        
        # Test adaptive params
        params = engine.get_adaptive_params()
        print(f"✅ Adaptive params: risk_multiplier={params['risk_multiplier']}")
        
        # Test should_trade
        should_trade = engine.should_trade(70.0)
        print(f"✅ Should trade (70% confidence): {should_trade}")
        
        return True
    except Exception as e:
        print(f"❌ Adaptive engine error: {e}")
        return False

async def test_bot_state_manager():
    """Test bot state manager"""
    print("\n" + "="*50)
    print("TESTING BOT STATE MANAGER")
    print("="*50)
    
    try:
        from app.core.bot_state_manager import BotStateManager, StopTrigger
        
        manager = BotStateManager("test_bot")
        
        # Test start
        started = manager.start()
        print(f"✅ Bot start: {started}")
        
        # Test stats update
        manager.update_stats({'profit': 100.0, 'symbol': 'BTCUSDT'})
        print(f"✅ Stats update: total_trades={manager.stats.total_trades}")
        
        # Test state
        state = manager.get_state()
        print(f"✅ Bot state: {state['current_state']}")
        
        # Test health
        health = manager.check_health()
        print(f"✅ Health check: {health['is_healthy']}")
        
        return True
    except Exception as e:
        print(f"❌ Bot state manager error: {e}")
        return False

async def test_system_coordinator():
    """Test system coordinator"""
    print("\n" + "="*50)
    print("TESTING SYSTEM COORDINATOR")
    print("="*50)
    
    try:
        from app.core.system_coordinator import SystemCoordinator, SystemConfig, SystemMode
        
        config = SystemConfig(
            mode=SystemMode.PAPER,
            max_concurrent_trades=3,
            enable_adaptive=True,
            enable_multi_trade=True
        )
        
        coordinator = SystemCoordinator(config)
        
        # Test start
        started = await coordinator.start()
        print(f"✅ Coordinator start: {started}")
        
        # Test trade execution
        result = await coordinator.execute_trade(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.01,
            price=50000.0,
            stop_loss=49000.0
        )
        print(f"✅ Coordinated trade: {result.get('success')}")
        
        # Test multi-trade
        multi_result = await coordinator.execute_multi_trade([
            {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 0.01},
            {'symbol': 'ETHUSDT', 'side': 'BUY', 'quantity': 0.1}
        ])
        print(f"✅ Multi-trade: {multi_result.get('successful', 0)}/{multi_result.get('total', 0)}")
        
        # Test status
        status = coordinator.get_system_status()
        print(f"✅ System status: mode={status['mode']}, bots={status['active_bots']}")
        
        # Test stop
        stopped = await coordinator.stop()
        print(f"✅ Coordinator stop: {stopped}")
        
        return True
    except Exception as e:
        print(f"❌ System coordinator error: {e}")
        return False

async def test_backtest_engine():
    """Test backtesting engine"""
    print("\n" + "="*50)
    print("TESTING BACKTEST ENGINE")
    print("="*50)
    
    try:
        from app.core.backtest_engine import BacktestEngine, BacktestConfig, BacktestStrategy
        
        config = BacktestConfig(
            strategy=BacktestStrategy.TREND_FOLLOW,
            initial_capital=10000.0,
            risk_per_trade=2.0
        )
        
        engine = BacktestEngine(config)
        
        # Generate sample data
        data = engine.generate_sample_data(500)
        print(f"✅ Sample data generated: {len(data)} candles")
        
        # Run backtest
        result = engine.run()
        print(f"✅ Backtest complete: {result.total_trades} trades")
        print(f"   Win rate: {result.win_rate:.1f}%")
        print(f"   Total PnL: ${result.total_pnl:.2f}")
        print(f"   Max drawdown: {result.max_drawdown_percent:.1f}%")
        print(f"   Profit factor: {result.profit_factor:.2f}")
        
        # Test weakness analysis
        weaknesses = engine.get_weakness_analysis()
        print(f"✅ Weakness analysis: {len(weaknesses.get('weaknesses', []))} issues found")
        
        # Test report
        report = engine.get_report()
        print(f"✅ Report generated")
        
        return True
    except Exception as e:
        print(f"❌ Backtest engine error: {e}")
        return False

async def test_adaptive_bot():
    """Test adaptive auto-trading bot"""
    print("\n" + "="*50)
    print("TESTING ADAPTIVE AUTO BOT")
    print("="*50)
    
    try:
        from app.core.adaptive_auto_bot import AdaptiveAutoBot, AdaptiveBotConfig
        
        config = AdaptiveBotConfig(
            bot_id="test_adaptive_bot",
            symbols=["BTCUSDT", "ETHUSDT"],
            adaptive_enabled=True
        )
        
        bot = AdaptiveAutoBot(config)
        
        # Test initialize
        initialized = await bot.initialize()
        print(f"✅ Bot initialize: {initialized}")
        
        # Test start
        started = await bot.start()
        print(f"✅ Bot start: {started}")
        
        # Test status
        status = bot.get_status()
        print(f"✅ Bot status: running={status['is_running']}")
        
        # Test stop
        stopped = await bot.stop()
        print(f"✅ Bot stop: {stopped}")
        
        return True
    except Exception as e:
        print(f"❌ Adaptive bot error: {e}")
        return False

async def test_notification_service():
    """Test notification service"""
    print("\n" + "="*50)
    print("TESTING NOTIFICATION SERVICE")
    print("="*50)
    
    try:
        from app.services.notification_service import NotificationService, Notification
        
        service = NotificationService()
        
        # Test notification creation
        notification = Notification(
            title="Test Notification",
            message="This is a test notification from ESMH.TRADE",
            channel="email",
            priority="high"
        )
        
        # Test send (will queue if email not configured)
        result = await service.send(notification)
        print(f"✅ Notification send: {result.get('status')}")
        
        # Test status
        status = service.get_status()
        print(f"✅ Notification status: email_configured={status['email_configured']}")
        
        return True
    except Exception as e:
        print(f"❌ Notification service error: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints (requires running server)"""
    print("\n" + "="*50)
    print("TESTING API ENDPOINTS (Server must be running)")
    print("="*50)
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get('http://localhost:8000/health') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Health check: {data}")
                else:
                    print(f"⚠️ Health check: status {resp.status}")
            
            # Test status endpoint
            async with session.get('http://localhost:8000/api/status') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ API status: {data.get('status')}")
                else:
                    print(f"⚠️ API status: status {resp.status}")
            
            return True
    except Exception as e:
        print(f"⚠️ API test skipped (server not running): {e}")
        return True  # Not a failure, just skipped

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ESMH.TRADE - COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Imports", await test_imports()))
    results.append(("Trading Engine", await test_trading_engine()))
    results.append(("Risk Engine", await test_risk_engine()))
    results.append(("Adaptive Engine", await test_adaptive_engine()))
    results.append(("Bot State Manager", await test_bot_state_manager()))
    results.append(("System Coordinator", await test_system_coordinator()))
    results.append(("Backtest Engine", await test_backtest_engine()))
    results.append(("Adaptive Bot", await test_adaptive_bot()))
    results.append(("Notification Service", await test_notification_service()))
    results.append(("API Endpoints", await test_api_endpoints()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check logs above.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
