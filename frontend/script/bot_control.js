// ESMH.TRADE - Bot Control & Upgrade Layer (v12.1)
// ================================================================
// Adds per-bot user controls: On/Off, Advanced, Smart Risk Management,
// Profit / Take Profit, Dynamic & Adaptive mechanisms, plus live tick feed.
(function () {
    'use strict';

    const API = window.ESMH_API_BASE || (window.location.origin.indexOf('localhost') !== -1
        ? 'http://localhost:8000'
        : window.location.origin);

    const DEFAULT_BOTS = [
        { bot_id: 'crypto_scalper', bot_type: 'crypto_scalper', name: 'Scalper Bot', pairs: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'], timeframe: '1m', risk_per_trade_pct: 1.0, capital: 1000, enabled: true },
        { bot_id: 'forex_scalper', bot_type: 'scalper', name: 'Forex Scalper', pairs: ['EURUSD'], timeframe: '1m', risk_per_trade_pct: 1.0, capital: 1000, enabled: true },
        { bot_id: 'grid_bot', bot_type: 'grid', name: 'Grid Bot', pairs: ['BTCUSDT'], timeframe: '15m', risk_per_trade_pct: 1.0, capital: 1000, enabled: true },
        { bot_id: 'news_bot', bot_type: 'news', name: 'News Bot', pairs: ['EURUSD'], timeframe: '1h', risk_per_trade_pct: 1.0, capital: 1000, enabled: true },
        { bot_id: 'smart_money', bot_type: 'smart_money', name: 'Smart Money', pairs: ['XAUUSD'], timeframe: '15m', risk_per_trade_pct: 1.0, capital: 1000, enabled: true },
        { bot_id: 'metals_bot', bot_type: 'metals', name: 'Metals Bot', pairs: ['XAUUSD', 'XAGUSD'], timeframe: '1h', risk_per_trade_pct: 1.0, capital: 1000, enabled: true },
        { bot_id: 'commodities_bot', bot_type: 'commodities', name: 'Commodities Bot', pairs: ['OILUSD', 'NATGASUSD'], timeframe: '1h', risk_per_trade_pct: 1.0, capital: 1000, enabled: true },
        { bot_id: 'deriv_bot', bot_type: 'deriv', name: 'Deriv Bot', pairs: ['R_75'], timeframe: '1m', risk_per_trade_pct: 1.0, capital: 1000, enabled: true }
    ];

    const state = { bots: [], settings: {}, ws: null, wsConnected: false };

    // ---------- Helpers ----------
    function getId(id) { return document.getElementById(id); }

    function esc(v) {
        return String(v == null ? '' : v)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function fetchJson(url, options) {
        options = options || {};
        options.headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
        return fetch(API + url, options).then(function (r) {
            return r.json().then(function (data) { return { status: r.status, data: data }; });
        });
    }

    // ---------- Persistence ----------
    function saveLocal(botId, cfg) {
        try {
            const key = 'esh_bot_settings_' + botId;
            const existing = JSON.parse(localStorage.getItem(key) || '{}');
            localStorage.setItem(key, JSON.stringify(Object.assign({}, existing, cfg)));
        } catch (e) { /* ignore */ }
    }

    function loadLocal(botId) {
        try { return JSON.parse(localStorage.getItem('esh_bot_settings_' + botId) || '{}'); }
        catch (e) { return {}; }
    }
// ---------- API calls ----------
    async function registerBot(cfg) {
        const res = await fetchJson('/api/trading/bots/register', { method: 'POST', body: JSON.stringify(cfg) });
        return res.data;
    }
    async function toggleBot(botId, enabled) {
        const res = await fetchJson('/api/trading/bots/' + encodeURIComponent(botId) + '/toggle', { method: 'POST', body: JSON.stringify({ enabled: enabled }) });
        return res.data;
    }
    async function updateBotConfig(botId, cfg) {
        const res = await fetchJson('/api/trading/bots/' + encodeURIComponent(botId) + '/config', { method: 'POST', body: JSON.stringify(cfg) });
        return res.data;
    }
    async function listBots() {
        const res = await fetchJson('/api/trading/bots');
        return res.data && res.data.bots ? res.data.bots : [];
    }

    // ---------- Rendering ----------
    function mergeRemainingDefaults() {
        const map = {};
        DEFAULT_BOTS.forEach(function (b) { map[b.bot_id] = Object.assign({}, b); });
        Object.keys(state.settings).forEach(function (k) {
            if (map[k]) map[k] = Object.assign({}, map[k], state.settings[k]);
        });
        return Object.keys(map).map(function (k) { return map[k]; });
    }

    function renderBotsIntoGrid(gridEl) {
        if (!gridEl) return;
        const all = mergeRemainingDefaults();
        gridEl.innerHTML = all.map(function (bot) {
            const saved = loadLocal(bot.bot_id);
            const cfg = Object.assign({}, bot, saved);
            const on = cfg.enabled !== false;
            return '' +
                '<div class="bot-card" data-bot-id="' + esc(cfg.bot_id) + '">' +
                '  <div class="bot-card-header">' +
                '    <span class="bot-name">' + esc(cfg.name || cfg.bot_id) + '</span>' +
                '    <span class="bot-status ' + (on ? 'running' : 'stopped') + '">' + (on ? '● Running' : '● Stopped') + '</span>' +
                '  </div>' +
                '  <div class="bot-info">' + esc(cfg.bot_type) + (cfg.pairs ? ' · ' + cfg.pairs.join(', ') : '') + '</div>' +
                '  <div class="bot-metrics"><div>Risk: <strong>' + esc(cfg.risk_per_trade_pct) + '%</strong></div>' +
                '    <div>Smart Risk: <strong>' + (cfg.smart_risk_enabled !== false ? 'ON' : 'OFF') + '</strong></div></div>' +
                '  <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">' +
                '    <button class="btn btn-sm ' + (on ? 'btn-secondary' : 'btn-primary') + '" onclick="window.__esmhToggleBot(\'' + esc(cfg.bot_id) + '\', ' + (on ? 'false' : 'true') + ')">' + (on ? 'Pause' : 'Start') + '</button>' +
                '    <button class="btn btn-sm btn-secondary" onclick="window.__esmhConfigBot(\'' + esc(cfg.bot_id) + '\')">Advanced</button>' +
                '    <button class="btn btn-sm btn-secondary" onclick="window.__esmhDetails(\'' + esc(cfg.bot_id) + '\')">Details</button>' +
                '  </div>' + '</div>';
        }).join('');
    }

    function showToast(title, msg, type) {
        if (window.showToast) { window.showToast(title, msg, type === 'error' ? 'error' : 'success'); }
        else { alert(title + ': ' + msg); }
    }
// ---------- Bot actions ----------
    async function __esmhToggleBot(botId, enabled) {
        try {
            const res = await toggleBot(botId, enabled);
            if (res && res.success) {
                const local = loadLocal(botId);
                local.enabled = enabled;
                saveLocal(botId, local);
                showToast((enabled ? '✅ ' : '⏸ ') + botId, enabled ? 'Bot started' : 'Bot paused', 'success');
            } else {
                showToast('⚠️ Failed', (res && res.detail) || 'Toggle failed', 'error');
            }
            refresh();
        } catch (e) { showToast('⚠️ API Error', String(e), 'error'); }
    }

    function toggleRow(id, label, desc, on) {
        return '<div class="toggle-row"><div><div class="toggle-label">' + label + '</div>' +
            '<div class="toggle-desc">' + desc + '</div></div>' +
            '<button class="toggle ' + (on ? 'active' : '') + '" id="' + id + '" onclick="this.classList.toggle(\'active\')"></button></div>';
    }

    function configFormHtml(botId) {
        const saved = loadLocal(botId);
        const base = DEFAULT_BOTS.find(function (b) { return b.bot_id === botId; }) || {};
        const cfg = Object.assign({}, base, saved);
        return '' +
            '<div class="modal-form-group"><label>Capital ($)</label>' +
            '<input id="esmhCapital" type="number" value="' + (cfg.capital || 1000) + '" min="5" /></div>' +
            '<div class="modal-form-group"><label>Risk Per Trade (%)</label>' +
            '<input id="esmhRisk" type="number" value="' + (cfg.risk_per_trade_pct || 1) + '" min="0.8" max="5" step="0.1" /></div>' +
            '<div class="modal-form-group"><label>Pairs (comma separated)</label>' +
            '<input id="esmhPairs" value="' + esc((cfg.pairs && cfg.pairs.join ? cfg.pairs.join(',') : cfg.pairs) || 'BTCUSDT') + '" /></div>' +
            '<div class="modal-form-group"><label>Timeframe</label>' +
            '<select id="esmhTimeframe"><option ' + (cfg.timeframe === '1m' ? 'selected' : '') + '>1m</option>' +
            '<option ' + (cfg.timeframe === '5m' ? 'selected' : '') + '>5m</option>' +
            '<option ' + (cfg.timeframe === '15m' ? 'selected' : '') + '>15m</option>' +
            '<option ' + (cfg.timeframe === '1h' ? 'selected' : '') + '>1h</option></select></div>' +
            '<div class="modal-form-group"><label>Take Profit % (optional)</label>' +
            '<input id="esmhTP" type="number" value="' + (cfg.take_profit_pct ? (cfg.take_profit_pct * 100).toFixed(2) : '') + '" min="0.1" step="0.1" placeholder="auto" /></div>' +
            '<div class="modal-form-group"><label>Stop Loss % (optional)</label>' +
            '<input id="esmhSL" type="number" value="' + (cfg.stop_loss_pct ? (cfg.stop_loss_pct * 100).toFixed(2) : '') + '" min="0.05" step="0.05" placeholder="auto" /></div>' +
            toggleRow('esmhSmart', 'Smart Risk Management', 'Win-rate/streak aware sizing', cfg.smart_risk_enabled !== false) +
            toggleRow('esmhAdaptive', 'Adaptive Mechanism', 'Auto-adapt to market regime', cfg.adaptive_enabled !== false) +
            toggleRow('esmhDynamicTP', 'Dynamic Take Profit', 'Scale TP with recent results', cfg.dynamic_take_profit !== false) +
            toggleRow('esmhTrailing', 'Trailing Take Profit', 'Ratchet TP up as price moves', !!cfg.trailing_take_profit_enabled) +
            toggleRow('esmhAdvanced', 'Advanced Mode', 'Expose extra parameters', !!cfg.advanced_mode) +
            '<button class="btn" style="width:100%; justify-content:center; margin-top:0.5rem;" onclick="window.__esmhSaveConfig(\'' + botId + '\')"><i class="fas fa-save"></i> Save Configuration</button>';
    }

    function __esmhConfigBot(botId) {
        if (window.showModal) { window.showModal('⚙️ Configure ' + botId, configFormHtml(botId)); return; }
        const holder = getId('esmhConfigPanel');
        if (holder) { holder.style.display = 'block'; holder.innerHTML = configFormHtml(botId); }
        else { alert('Modal not available'); }
    }
async function __esmhSaveConfig(botId) {
        const getVal = function (id, fallback) {
            const el = getId(id);
            return el ? el.value : fallback;
        };
        const capital = Number(getVal('esmhCapital', 1000));
        const risk = Number(getVal('esmhRisk', 1));
        const pairs = getVal('esmhPairs', 'BTCUSDT').split(',').map(function (s) { return s.trim().toUpperCase(); }).filter(Boolean);
        const timeframe = getVal('esmhTimeframe', '1m');
        const tpPct = Number(getVal('esmhTP', 0)) / 100;
        const slPct = Number(getVal('esmhSL', 0)) / 100;
        const smart = document.getElementById('esmhSmart') ? getId('esmhSmart').classList.contains('active') : true;
        const adaptive = document.getElementById('esmhAdaptive') ? getId('esmhAdaptive').classList.contains('active') : true;
        const dynamicTP = document.getElementById('esmhDynamicTP') ? getId('esmhDynamicTP').classList.contains('active') : true;
        const trailing = document.getElementById('esmhTrailing') ? getId('esmhTrailing').classList.contains('active') : false;
        const advanced = document.getElementById('esmhAdvanced') ? getId('esmhAdvanced').classList.contains('active') : false;

        const cfg = {
            bot_id: botId,
            bot_type: (DEFAULT_BOTS.find(function (b) { return b.bot_id === botId; }) || {}).bot_type || 'crypto_scalper',
            capital: capital,
            risk_per_trade_pct: risk,
            pairs: pairs,
            timeframe: timeframe,
            take_profit_pct: tpPct > 0 ? tpPct : null,
            stop_loss_pct: slPct > 0 ? slPct : null,
            smart_risk_enabled: smart,
            adaptive_enabled: adaptive,
            dynamic_take_profit: dynamicTP,
            trailing_take_profit_enabled: trailing,
            advanced_mode: advanced,
            enabled: loadLocal(botId).enabled !== false
        };
        try {
            await updateBotConfig(botId, cfg);
            saveLocal(botId, cfg);
            if (window.closeModal) window.closeModal();
            const panel = getId('esmhConfigPanel');
            if (panel) panel.style.display = 'none';
            showToast('✅ ' + botId, 'Configuration saved', 'success');
        } catch (e) { showToast('⚠️ Save error', String(e), 'error'); }
        refresh();
    }

    async function __esmhDetails(botId) {
        try {
            const bots = await listBots();
            const bot = bots.find(function (b) { return b.bot_id === botId; });
            if (window.showModal && bot) {
                window.showModal('📊 ' + botId + ' Details',
                    '<div style="font-size:.8rem; font-family:monospace; white-space:pre-wrap; text-align:left;">' + esc(JSON.stringify(bot, null, 2)) + '</div>');
            } else if (bot) { alert(JSON.stringify(bot, null, 2)); }
            else { alert('No recorded status for ' + botId + '. Register it first.'); }
        } catch (e) { alert('API error: ' + e); }
    }

    // ---------- WebSocket tick bridge ----------
    function connectWs() {
        try {
            const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
            const host = window.location.host || 'localhost:8000';
            const socket = new WebSocket(proto + host + '/api/trading/ws/ticks');
            socket.onopen = function () { state.wsConnected = true; socket.send(JSON.stringify({ type: 'ping' })); };
            socket.onmessage = function () { /* ack/pong only */ };
            socket.onclose = function () { state.wsConnected = false; setTimeout(connectWs, 5000); };
            state.ws = socket;
        } catch (e) { /* no ws */ }
    }

    function pushTick(symbol, price) {
        if (!state.ws || state.ws.readyState !== WebSocket.OPEN) return;
        state.ws.send(JSON.stringify({ type: 'tick', symbol: symbol, price: price, source: 'frontend' }));
    }

    // ---------- Lifecycle ----------
    function init() {
        DEFAULT_BOTS.forEach(function (b) {
            if (!state.settings[b.bot_id]) state.settings[b.bot_id] = loadLocal(b.bot_id);
        });
        refresh();
        connectWs();
        DEFAULT_BOTS.forEach(function (b) {
            try {
                const local = Object.assign({}, b, loadLocal(b.bot_id));
                registerBot(local);
            } catch (e) { /* not yet registered */ }
        });
    }

    function refresh() {
        const grid = getId('botsGrid') || document.querySelector('.bot-grid');
        if (grid) renderBotsIntoGrid(grid);
    }

    window.__esmhToggleBot = __esmhToggleBot;
    window.__esmhConfigBot = __esmhConfigBot;
    window.__esmhSaveConfig = __esmhSaveConfig;
    window.__esmhDetails = __esmhDetails;
    window.__esmhPushTick = pushTick;
    window.ESMH_BotControl = {
        init: init,
        refresh: refresh,
        registerBot: registerBot,
        toggleBot: toggleBot,
        updateBotConfig: updateBotConfig,
        listBots: listBots,
        pushTick: pushTick
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();