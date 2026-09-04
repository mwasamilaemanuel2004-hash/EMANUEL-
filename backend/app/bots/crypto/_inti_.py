# ================================================================
# 1. BASIC USAGE
# ================================================================

from backend.app.bots.crypto import (
    create_bot, start_bot, stop_bot, 
    get_bot, get_all_bots, get_summary,
    list_bots, print_summary, start_all_bots, stop_all_bots
)

# List available bots
list_bots()

# Create bots
scalper = create_bot('scalper', symbol='BTCUSDT', initial_capital=1000)
dca = create_bot('dca', symbol='ETHUSDT', initial_capital=500)
grid = create_bot('grid', symbol='BTCUSDT', initial_capital=1000)
whale = create_bot('whale', symbol='BTCUSDT', initial_capital=5000)
arbitrage = create_bot('arbitrage', symbol='BTCUSDT', initial_capital=10000)

# Start all bots
start_all_bots()

# Get summary
print_summary()

# Get metrics
metrics = get_all_metrics()

# Stop all bots
stop_all_bots()

# ================================================================
# 2. INDIVIDUAL BOT CONTROL
# ================================================================

# Register a bot
from backend.app.bots.crypto import register_bot

scalper = create_bot('scalper', symbol='ETHUSDT', initial_capital=500)
register_bot('scalper', 'scalper_eth', scalper)

# Start specific bot
start_bot('scalper_eth')

# Get specific bot metrics
metrics = get_bot_metrics('scalper_eth')

# Stop specific bot
stop_bot('scalper_eth')

# ================================================================
# 3. GETTING BOT STATUS
# ================================================================

# Get single bot
bot = get_bot('scalper_eth')
if bot:
    status = bot.get_status()
    print(f"Bot: {status}")

# Get all bots
all_bots = get_all_bots()
for bot_id, bot_info in all_bots.items():
    print(f"{bot_id}: {bot_info.get('status')}")