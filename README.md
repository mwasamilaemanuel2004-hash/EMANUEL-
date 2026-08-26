# ESMH.TRADE - AI-Powered Trading Platform

A comprehensive AI-powered automated trading platform supporting Forex, Crypto, and Stock trading with advanced risk management, adaptive learning, and multi-trade capabilities.

## Features

### Core Trading Engines
- **Trading Engine** - Order execution, position management, portfolio tracking
- **Risk Management Engine** - Advanced risk management with adaptive multipliers, drawdown protection
- **Adaptive Engine** - AI self-learning system with 5 layers of learning
- **Indicator Engine** - 20+ technical indicators including Smart Money concepts
- **Candle Analyzer** - 30+ candlestick pattern detection
- **Bot State Manager** - Complete bot lifecycle management with stop/re-entry system

### Advanced Features
- **System Coordinator** - Central orchestration of all trading engines
- **Backtesting Engine** - Strategy testing with comprehensive analytics
- **Adaptive Auto-Bot** - Self-learning multi-strategy trading bot
- **Multi-Trade Support** - Trade multiple pairs simultaneously with permission
- **Notification System** - Email, Telegram, and push notifications

### Trading Bots
- Trend Follower Bot
- Scalper Bot
- Arbitrage Bot
- Smart Money Bot
- News Trader Bot
- Grid Bot
- Breakout Bot
- Mean Reversion Bot

### Frontend
- Modern dark-themed dashboard
- Real-time trading terminal
- Multi-trade interface
- Backtesting interface
- Bot management panel
- Mobile-responsive with bottom navigation
- PWA support

## Installation

1. **Install Python 3.11+**
2. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the system:**
   ```bash
   cd backend
   python -m app.main
   ```

5. **Run tests:**
   ```bash
   python test_system.py
   ```

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/verify-2fa` - Verify 2FA code
- `POST /api/auth/refresh-token` - Refresh JWT token
- `POST /api/trading/order/place` - Place a new order
- `POST /api/trading/order/place-multi` - Place multiple orders
- `GET /api/trading/positions` - Get open positions
- `GET /api/trading/history` - Get trade history
- `POST /api/trading/position/close` - Close a position
- `GET /api/trading/performance` - Get trading performance
- `GET /api/debug/status` - Debug system status
- `POST /api/debug/entry` - Debug trade entry
- `POST /api/debug/close` - Debug trade close

## Project Structure

```
ESMH.TRADE/
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI entry point
│       ├── config.py               # Configuration management
│       ├── database.py             # Database session management
│       ├── core/                   # Core trading engines
│       │   ├── trading_engine.py
│       │   ├── risk_management_engine.py
│       │   ├── adaptive_engine.py
│       │   ├── indicator_engine.py
│       │   ├── candle_analyzer.py
│       │   ├── bot_state_manager.py
│       │   ├── system_coordinator.py
│       │   ├── backtest_engine.py
│       │   └── adaptive_auto_bot.py
│       ├── api/                    # API routes
│       │   ├── auth.py
│       │   ├── trading.py
│       │   └── debug.py
│       ├── models/                 # SQLAlchemy ORM models
│       ├── bots/                   # Trading bot implementations
│       ├── exchanges/              # Exchange API integrations
│       ├── services/               # Business logic services
│       ├── admin/                  # Admin panel
│       ├── ai_chatbot/             # AI chatbot system
│       └── security/               # Security module
├── frontend/
│   ├── index.html                  # Main HTML entry
│   ├── stye/style.css              # Stylesheet
│   ├── script/app.js               # JavaScript application
│   └── pwa/manifest.json           # PWA manifest
├── data/                           # Data directory
├── config/                         # Configuration files
├── scripts/                        # Utility scripts
├── .env                            # Environment variables
├── test_system.py                  # System test script
└── README.md                       # This file
```

## Configuration

Edit `.env` file with your settings:

```env
# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Email (Gmail App Password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Exchange API Keys
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret
```

## Gmail App Password Setup

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Generate a 16-character app password
4. Use this password in your `.env` file

## Security Notes

- Change default secrets in production
- Use strong, random keys
- Enable 2FA for all accounts
- Never commit `.env` to version control
- Use environment-specific configurations

## License

Proprietary - All rights reserved

## Support

For issues and support, please open an issue on GitHub.
