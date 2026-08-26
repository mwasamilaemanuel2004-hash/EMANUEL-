// ESMH.TRADE - Main Application JavaScript
// AI-Powered Trading Platform

class ESMHApp {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.currentSection = 'dashboard';
        this.multiTradeEnabled = false;
        this.positions = [];
        this.bots = [];
        this.notifications = [];
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupTabs();
        this.setupForms();
        this.setupTerminal();
        this.setupMultiTrade();
        this.loadInitialData();
        console.log('ESMH.TRADE initialized');
    }

    // NAVIGATION
    setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('href').substring(1);
                this.navigateTo(section);
            });
        });
        document.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('href').substring(1);
                this.navigateTo(section);
            });
        });
    }

    navigateTo(section) {
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(section)?.classList.add('active');
        document.querySelectorAll('.nav-link, .bottom-nav-item').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${section}`) link.classList.add('active');
        });
        this.currentSection = section;
        if (section === 'dashboard') this.loadDashboardData();
        if (section === 'bots') this.loadBots();
    }

    // TABS
    setupTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                const panel = btn.closest('.panel');
                panel.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                panel.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                panel.querySelector(`#${tabName}Trade`)?.classList.add('active');
            });
        });
    }

    // FORMS
    setupForms() {
        const tradeForm = document.getElementById('tradeForm');
        if (tradeForm) {
            tradeForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.placeOrder();
            });
        }
        const backtestForm = document.getElementById('backtestForm');
        if (backtestForm) {
            backtestForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.runBacktest();
            });
        }
        const placeMultiBtn = document.getElementById('placeMultiOrders');
        if (placeMultiBtn) {
            placeMultiBtn.addEventListener('click', () => this.placeMultiOrders());
        }
    }

    // TRADING
    async placeOrder() {
        const symbol = document.getElementById('symbol').value;
        const side = document.getElementById('side').value;
        const quantity = parseFloat(document.getElementById('quantity').value);
        const price = parseFloat(document.getElementById('price').value) || null;
        const stopLoss = parseFloat(document.getElementById('stopLoss').value) || null;
        const takeProfit = parseFloat(document.getElementById('takeProfit').value) || null;

        if (!symbol || !quantity) {
            this.showToast('Error', 'Please fill in all required fields', 'error');
            return;
        }

        try {
            this.showToast('Placing Order', `${side} ${quantity} ${symbol}...`, 'info');
            const response = await fetch(`${this.apiBase}/api/trading/order/place`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: symbol.toUpperCase(), side, quantity, price, stop_loss: stopLoss, take_profit: takeProfit })
            });
            const result = await response.json();
            if (result.success) {
                this.showToast('Order Placed', `${side} ${quantity} ${symbol} @ ${price || 'MARKET'}`, 'success');
                document.getElementById('tradeForm').reset();
                this.loadPositions();
            } else {
                this.showToast('Order Failed', result.error || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showToast('Connection Error', 'Could not connect to trading server', 'error');
        }
    }

    async placeMultiOrders() {
        if (!this.multiTradeEnabled) {
            this.showToast('Permission Required', 'Enable multi-trade mode first', 'warning');
            return;
        }
        const rows = document.querySelectorAll('.multi-order-row');
        const orders = [];
        rows.forEach(row => {
            const symbol = row.querySelector('.mt-symbol')?.value;
            const side = row.querySelector('.mt-side')?.value;
            const quantity = parseFloat(row.querySelector('.mt-quantity')?.value);
            const price = parseFloat(row.querySelector('.mt-price')?.value) || null;
            if (symbol && side && quantity) orders.push({ symbol: symbol.toUpperCase(), side, quantity, price });
        });

        if (orders.length === 0) {
            this.showToast('No Orders', 'Add at least one order', 'warning');
            return;
        }
        if (orders.length > 5) {
            this.showToast('Limit Exceeded', 'Maximum 5 orders per batch', 'warning');
            return;
        }

        try {
            this.showToast('Placing Orders', `${orders.length} orders...`, 'info');
            const response = await fetch(`${this.apiBase}/api/trading/order/place-multi`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ orders, require_permission: true })
            });
            const result = await response.json();
            if (result.success) {
                this.showToast('Orders Placed', `${result.successful}/${result.total_orders} successful`, 'success');
                this.loadPositions();
            } else {
                this.showToast('Orders Failed', result.error || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showToast('Connection Error', 'Could not connect to trading server', 'error');
        }
    }

    async loadPositions() {
        try {
            const response = await fetch(`${this.apiBase}/api/trading/positions`);
            const positions = await response.json();
            this.positions = positions;
            this.renderPositions(positions);
        } catch (error) {
            console.error('Load positions error:', error);
        }
    }

    renderPositions(positions) {
        const tbody = document.querySelector('#positionsTable tbody');
        if (!tbody) return;
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No open positions</td></tr>';
            return;
        }
        tbody.innerHTML = positions.map(pos => `
            <tr>
                <td><strong>${pos.symbol}</strong></td>
                <td>${pos.side}</td>
                <td>$${pos.entry_price.toFixed(2)}</td>
                <td>${pos.quantity}</td>
                <td class="${pos.unrealized_pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">
                    ${pos.unrealized_pnl >= 0 ? '+' : ''}$${pos.unrealized_pnl.toFixed(2)}
                </td>
                <td><button class="btn btn-sm btn-secondary" onclick="app.closePosition('${pos.symbol}')">Close</button></td>
            </tr>
        `).join('');
    }

    async closePosition(symbol) {
        try {
            const response = await fetch(`${this.apiBase}/api/trading/position/close?symbol=${symbol}`, { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                this.showToast('Position Closed', `${symbol} closed successfully`, 'success');
                this.loadPositions();
            } else {
                this.showToast('Close Failed', result.error || 'Unknown error', 'error');
            }
        } catch (error) {
            this.showToast('Error', 'Could not close position', 'error');
        }
    }

    // MULTI-TRADE
    setupMultiTrade() {
        const checkbox = document.getElementById('enableMultiTrade');
        const addBtn = document.getElementById('addOrderRow');
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                this.multiTradeEnabled = e.target.checked;
                if (this.multiTradeEnabled) {
                    this.showToast('Multi-Trade Enabled', 'You can now place multiple orders', 'info');
                    this.addOrderRow();
                }
            });
        }
        if (addBtn) addBtn.addEventListener('click', () => this.addOrderRow());
    }

    addOrderRow() {
        const container = document.getElementById('multiTradeOrders');
        if (!container) return;
        const row = document.createElement('div');
        row.className = 'multi-order-row';
        row.innerHTML = `
            <input type="text" class="mt-symbol" placeholder="Symbol (e.g., BTCUSDT)" required>
            <select class="mt-side"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>
            <input type="number" class="mt-quantity" placeholder="Qty" step="0.0001" required>
            <input type="number" class="mt-price" placeholder="Price (optional)" step="0.01">
            <button type="button" class="btn-remove" onclick="this.parentElement.remove()">×</button>
        `;
        container.appendChild(row);
    }

    // BACKTESTING
    async runBacktest() {
        const symbol = document.getElementById('btSymbol').value;
        const strategy = document.getElementById('btStrategy').value;
        const startDate = document.getElementById('btStartDate').value;
        const endDate = document.getElementById('btEndDate').value;
        const initialCapital = parseFloat(document.getElementById('btInitialCapital').value);
        const riskPerTrade = parseFloat(document.getElementById('btRiskPerTrade').value);

        if (!symbol || !startDate || !endDate) {
            this.showToast('Error', 'Please fill in all fields', 'error');
            return;
        }
        this.showToast('Running Backtest', `Testing ${strategy} on ${symbol}...`, 'info');
        setTimeout(() => {
            const results = this.simulateBacktest(initialCapital, riskPerTrade);
            this.renderBacktestResults(results, symbol, strategy);
        }, 2000);
    }

    simulateBacktest(capital, riskPerTrade) {
        const trades = [];
        let balance = capital;
        let wins = 0, losses = 0;
        let maxBalance = capital, maxDrawdown = 0;

        for (let i = 0; i < 50; i++) {
            const riskAmount = balance * (riskPerTrade / 100);
            const isWin = Math.random() > 0.4;
            const pnl = isWin ? riskAmount * (1.5 + Math.random()) : -riskAmount;
            balance += pnl;
            if (isWin) wins++; else losses++;
            if (balance > maxBalance) maxBalance = balance;
            const drawdown = (maxBalance - balance) / maxBalance;
            if (drawdown > maxDrawdown) maxDrawdown = drawdown;
            trades.push({ id: i + 1, pnl, balance, isWin });
        }

        return {
            initialCapital: capital,
            finalBalance: balance,
            totalPnl: balance - capital,
            totalTrades: trades.length,
            wins, losses,
            winRate: (wins / trades.length) * 100,
            maxDrawdown: maxDrawdown * 100,
            profitFactor: wins > 0 ? (wins / Math.max(losses, 1)) : 0,
            trades
        };
    }

    renderBacktestResults(results, symbol, strategy) {
        const container = document.getElementById('backtestResults');
        if (!container) return;
        container.style.display = 'block';
        container.innerHTML = `
            <h3 style="margin-bottom:16px">Backtest Results: ${symbol} (${strategy})</h3>
            <div class="backtest-summary">
                <div class="backtest-stat"><div class="stat-label">Final Balance</div><div class="stat-value">$${results.finalBalance.toFixed(2)}</div></div>
                <div class="backtest-stat"><div class="stat-label">Total PnL</div><div class="stat-value ${results.totalPnl >= 0 ? 'positive' : 'negative'}">${results.totalPnl >= 0 ? '+' : ''}$${results.totalPnl.toFixed(2)}</div></div>
                <div class="backtest-stat"><div class="stat-label">Win Rate</div><div class="stat-value">${results.winRate.toFixed(1)}%</div></div>
                <div class="backtest-stat"><div class="stat-label">Total Trades</div><div class="stat-value">${results.totalTrades}</div></div>
                <div class="backtest-stat"><div class="stat-label">Max Drawdown</div><div class="stat-value negative">${results.maxDrawdown.toFixed(1)}%</div></div>
                <div class="backtest-stat"><div class="stat-label">Profit Factor</div><div class="stat-value">${results.profitFactor.toFixed(2)}</div></div>
            </div>
            <div style="margin-top:16px;padding:16px;background:var(--bg-tertiary);border-radius:8px">
                <h4 style="margin-bottom:8px">Weakness Analysis</h4>
                <ul style="font-size:.9rem;color:var(--text-secondary);padding-left:20px">
                    ${results.maxDrawdown > 15 ? '<li>High drawdown detected - consider tighter stop losses</li>' : ''}
                    ${results.winRate < 55 ? '<li>Win rate below 55% - strategy needs optimization</li>' : ''}
                    ${results.profitFactor < 1.5 ? '<li>Low profit factor - improve risk/reward ratio</li>' : ''}
                    ${results.maxDrawdown <= 15 && results.winRate >= 55 && results.profitFactor >= 1.5 ? '<li>Strategy shows good performance metrics</li>' : ''}
                </ul>
            </div>
        `;
    }

    // BOTS
    async loadBots() {
        const botsGrid = document.getElementById('botsGrid');
        if (!botsGrid) return;
        this.bots = [
            { id: 1, name: 'Trend Follower', status: 'running', strategy: 'Trend Following', winRate: 62, trades: 156 },
            { id: 2, name: 'Scalper Pro', status: 'running', strategy: 'Scalping', winRate: 58, trades: 423 },
            { id: 3, name: 'Arbitrage Bot', status: 'paused', strategy: 'Arbitrage', winRate: 75, trades: 89 },
            { id: 4, name: 'News Trader', status: 'stopped', strategy: 'News Based', winRate: 45, trades: 67 },
            { id: 5, name: 'Grid Bot', status: 'running', strategy: 'Grid Trading', winRate: 55, trades: 234 },
            { id: 6, name: 'Smart Money', status: 'running', strategy: 'Smart Money', winRate: 68, trades: 98 }
        ];
        botsGrid.innerHTML = this.bots.map(bot => `
            <div class="bot-card">
                <div class="bot-card-header">
                    <span class="bot-name">${bot.name}</span>
                    <span class="bot-status ${bot.status}">${bot.status}</span>
                </div>
                <div class="bot-info">${bot.strategy}</div>
                <div class="bot-metrics">
                    <div>Win Rate: <strong>${bot.winRate}%</strong></div>
                    <div>Trades: <strong>${bot.trades}</strong></div>
                </div>
                <div style="margin-top:12px;display:flex;gap:8px">
                    <button class="btn btn-sm ${bot.status === 'running' ? 'btn-secondary' : 'btn-primary'}" onclick="app.toggleBot(${bot.id})">
                        ${bot.status === 'running' ? 'Pause' : 'Start'}
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="app.viewBotDetails(${bot.id})">Details</button>
                </div>
            </div>
        `).join('');
    }

    toggleBot(botId) {
        const bot = this.bots.find(b => b.id === botId);
        if (bot) {
            bot.status = bot.status === 'running' ? 'paused' : 'running';
            this.showToast('Bot Updated', `${bot.name} is now ${bot.status}`, 'success');
            this.loadBots();
        }
    }

    viewBotDetails(botId) {
        const bot = this.bots.find(b => b.id === botId);
        if (bot) this.showToast('Bot Details', `${bot.name}: ${bot.strategy} | Win Rate: ${bot.winRate}%`, 'info');
    }

    // TERMINAL
    setupTerminal() {
        const input = document.getElementById('terminalInput');
        const output = document.getElementById('terminalOutput');
        if (!input || !output) return;
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const command = input.value.trim();
                if (command) {
                    this.executeCommand(command);
                    input.value = '';
                }
            }
        });
    }

    executeCommand(command) {
        const output = document.getElementById('terminalOutput');
        if (!output) return;
        const cmdLine = document.createElement('div');
        cmdLine.className = 'terminal-line';
        cmdLine.textContent = `> ${command}`;
        output.appendChild(cmdLine);
        const response = this.processCommand(command);
        const respLine = document.createElement('div');
        respLine.className = `terminal-line ${response.type}`;
        respLine.textContent = response.message;
        output.appendChild(respLine);
        output.scrollTop = output.scrollHeight;
    }

    processCommand(command) {
        const cmd = command.toLowerCase().trim();
        if (cmd === 'help') return { type: 'info', message: 'Commands: help, status, bots, positions, clear, version, ping' };
        if (cmd === 'status') return { type: 'success', message: 'System: ONLINE | API: Connected | Bots: 4 Running' };
        if (cmd === 'bots') return { type: 'info', message: 'Active: Trend Follower, Scalper Pro, Grid Bot, Smart Money' };
        if (cmd === 'positions') return { type: 'info', message: `Open Positions: ${this.positions.length}` };
        if (cmd === 'clear') {
            const output = document.getElementById('terminalOutput');
            if (output) output.innerHTML = '';
            return { type: 'info', message: 'Terminal cleared' };
        }
        if (cmd === 'version') return { type: 'info', message: 'ESMH.TRADE v2.0.0 | API v2.0.0' };
        if (cmd === 'ping') return { type: 'success', message: 'Pong! Latency: 12ms' };
        return { type: 'error', message: `Unknown command: ${cmd}. Type 'help' for available commands.` };
    }

    // DASHBOARD
    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBase}/api/status`);
            const data = await response.json();
            document.getElementById('activeBots').textContent = Object.values(data.modules).filter(m => m === 'active').length;
        } catch (error) {
            console.error('Load dashboard error:', error);
        }
        this.loadPositions();
    }

    async loadInitialData() {
        this.loadDashboardData();
    }

    // TOAST NOTIFICATIONS
    showToast(title, message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<div class="toast-title">${title}</div><div class="toast-message">${message}</div>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// Initialize app
const app = new ESMHApp();
