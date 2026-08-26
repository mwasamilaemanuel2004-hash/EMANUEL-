# 1. IMPORT
from backend.app.bots.crypto import (
    create_bot, start_bot, stop_bot, 
    get_bot, get_all_bots, get_summary,
    list_bots, print_summary, bot_manager
)

# 2. LIST AVAILABLE BOTS
list_bots()

# 3. CREATE BOTS
scalper = create_bot('scalper', symbol='BTCUSDT', initial_capital=1000)
dca = create_bot('dca', symbol='ETHUSDT', initial_capital=500)
grid = create_bot('grid', symbol='BTCUSDT', initial_capital=1000)
whale = create_bot('whale', symbol='BTCUSDT', initial_capital=5000)
arbitrage = create_bot('arbitrage', symbol='BTCUSDT', initial_capital=10000)

# 4. START BOTS
start_all_bots()

# 5. GET SUMMARY
print_summary()

# 6. GET METRICS
metrics = get_all_metrics()

# 7. STOP BOTS
stop_all_bots()