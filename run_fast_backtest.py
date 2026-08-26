"""
Fast Multi-Market Backtest Runner
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def calc_atr(data, period=14):
    high_low = data['high'] - data['low']
    high_close = abs(data['high'] - data['close'].shift())
    low_close = abs(data['low'] - data['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def calc_rsi(data, period=14):
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_adx(data, period=14):
    plus_dm = data['high'].diff()
    minus_dm = -data['low'].diff()
    plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0)
    minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0)
    atr = calc_atr(data, period)
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
    return dx.rolling(period).mean()

def generate_data(market, periods=800):
    np.random.seed(hash(market) % 2**32)
    
    if market == "forex":
        base, vol = 1.1000, 0.004
    elif market == "crypto":
        base, vol = 50000, 0.04
    elif market in ["commodities", "metals"]:
        base, vol = 2000, 0.008
    else:
        base, vol = 100, 0.01
    
    returns = np.random.normal(0.0001, vol / np.sqrt(24), periods)
    for i in range(1, len(returns)):
        returns[i] += 0.1 * returns[i-1] * np.random.normal(0, 1)
    
    price = base * np.exp(np.cumsum(returns))
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
    
    return pd.DataFrame({
        'open': price * (1 + np.random.uniform(-0.001, 0.001, periods)),
        'high': price * (1 + np.abs(np.random.normal(0, vol, periods))),
        'low': price * (1 - np.abs(np.random.normal(0, vol, periods))),
        'close': price,
        'volume': np.random.lognormal(10, 1, periods)
    }, index=dates)

def run_strategy(name, data, params):
    """Run a single strategy backtest"""
    capital = 10000.0
    position = None
    trades = []
    equity = [capital]
    
    if name == "trend_follow":
        fast, slow, atr_m = params.get('fast', 15), params.get('slow', 40), params.get('atr', 2.0)
        data = data.copy()
        data['ema_f'] = data['close'].ewm(span=fast).mean()
        data['ema_s'] = data['close'].ewm(span=slow).mean()
        data['atr'] = calc_atr(data)
        data['rsi'] = calc_rsi(data)
        data['adx'] = calc_adx(data)
        
        for i in range(slow + 10, len(data)):
            c, p = data.iloc[i], data.iloc[i-1]
            if position is None:
                bull = (p['ema_f'] <= p['ema_s'] and c['ema_f'] > c['ema_s'] and c['adx'] > 18 and c['rsi'] < 68)
                bear = (p['ema_f'] >= p['ema_s'] and c['ema_f'] < c['ema_s'] and c['adx'] > 18 and c['rsi'] > 32)
                if bull or bear:
                    side = 'BUY' if bull else 'SELL'
                    sd = c['atr'] * atr_m
                    qty = (capital * 0.02) / sd if sd > 0 else 0
                    if qty > 0:
                        position = {'side': side, 'entry': c['close'],
                                   'stop': c['close'] - sd if bull else c['close'] + sd,
                                   'tp': c['close'] + sd * 2.5 if bull else c['close'] - sd * 2.5, 'qty': qty}
            else:
                ep = None
                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['high'] >= position['tp']: ep, reason = position['tp'], 'TP'
                    elif c['ema_f'] < c['ema_s']: ep, reason = c['close'], 'REV'
                else:
                    if c['high'] >= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['low'] <= position['tp']: ep, reason = position['tp'], 'TP'
                    elif c['ema_f'] > c['ema_s']: ep, reason = c['close'], 'REV'
                if ep:
                    pnl = (ep - position['entry']) * position['qty'] * (1 if position['side'] == 'BUY' else -1) - capital * 0.001
                    capital += pnl
                    trades.append({'pnl': pnl, 'win': pnl > 0, 'reason': reason})
                    position = None
            equity.append(capital)
    
    elif name == "mean_reversion":
        lb, z_t = params.get('lb', 20), params.get('z', 2.0)
        data = data.copy()
        data['sma'] = data['close'].rolling(lb).mean()
        data['std'] = data['close'].rolling(lb).std()
        data['z'] = (data['close'] - data['sma']) / data['std']
        data['rsi'] = calc_rsi(data)
        
        for i in range(lb + 5, len(data)):
            c = data.iloc[i]
            if position is None:
                if c['z'] < -z_t and c['rsi'] < 35:
                    qty = (capital * 0.02) / c['close']
                    position = {'side': 'BUY', 'entry': c['close'], 'stop': c['close'] * 0.975, 'tp': c['close'] * 1.035, 'qty': qty}
                elif c['z'] > z_t and c['rsi'] > 65:
                    qty = (capital * 0.02) / c['close']
                    position = {'side': 'SELL', 'entry': c['close'], 'stop': c['close'] * 1.025, 'tp': c['close'] * 0.965, 'qty': qty}
            else:
                ep = None
                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['high'] >= position['tp']: ep, reason = position['tp'], 'TP'
                    elif c['z'] > 0: ep, reason = c['close'], 'MR'
                else:
                    if c['high'] >= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['low'] <= position['tp']: ep, reason = position['tp'], 'TP'
                    elif c['z'] < 0: ep, reason = c['close'], 'MR'
                if ep:
                    pnl = (ep - position['entry']) * position['qty'] * (1 if position['side'] == 'BUY' else -1) - capital * 0.001
                    capital += pnl
                    trades.append({'pnl': pnl, 'win': pnl > 0, 'reason': reason})
                    position = None
            equity.append(capital)
    
    elif name == "breakout":
        lb, atr_m = params.get('lb', 25), params.get('atr', 1.2)
        data = data.copy()
        data['atr'] = calc_atr(data)
        data['hi_n'] = data['high'].rolling(lb).max()
        data['lo_n'] = data['low'].rolling(lb).min()
        data['vol_sma'] = data['volume'].rolling(lb).mean()
        
        for i in range(lb + 5, len(data)):
            c, p = data.iloc[i], data.iloc[i-1]
            if position is None:
                if p['high'] <= data.iloc[i-2]['hi_n'] and c['high'] > c['hi_n'] and c['volume'] > c['vol_sma'] * 1.2:
                    sd = c['atr'] * atr_m
                    qty = (capital * 0.02) / sd if sd > 0 else 0
                    if qty > 0:
                        position = {'side': 'BUY', 'entry': c['close'], 'stop': c['close'] - sd, 'tp': c['close'] + sd * 3, 'qty': qty}
                elif p['low'] >= data.iloc[i-2]['lo_n'] and c['low'] < c['lo_n'] and c['volume'] > c['vol_sma'] * 1.2:
                    sd = c['atr'] * atr_m
                    qty = (capital * 0.02) / sd if sd > 0 else 0
                    if qty > 0:
                        position = {'side': 'SELL', 'entry': c['close'], 'stop': c['close'] + sd, 'tp': c['close'] - sd * 3, 'qty': qty}
            else:
                ep = None
                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['high'] >= position['tp']: ep, reason = position['tp'], 'TP'
                else:
                    if c['high'] >= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['low'] <= position['tp']: ep, reason = position['tp'], 'TP'
                if ep:
                    pnl = (ep - position['entry']) * position['qty'] * (1 if position['side'] == 'BUY' else -1) - capital * 0.001
                    capital += pnl
                    trades.append({'pnl': pnl, 'win': pnl > 0, 'reason': reason})
                    position = None
            equity.append(capital)
    
    elif name == "scalping":
        data = data.copy()
        data['ema_f'] = data['close'].ewm(span=5).mean()
        data['ema_s'] = data['close'].ewm(span=15).mean()
        data['rsi'] = calc_rsi(data, 7)
        data['atr'] = calc_atr(data, 7)
        
        for i in range(20, len(data)):
            c, p = data.iloc[i], data.iloc[i-1]
            if position is None:
                if c['ema_f'] > c['ema_s'] and p['rsi'] < 30 and c['rsi'] > 30:
                    qty = (capital * 0.01) / c['close']
                    position = {'side': 'BUY', 'entry': c['close'], 'stop': c['close'] - c['atr'], 'tp': c['close'] + c['atr'] * 1.5, 'qty': qty}
                elif c['ema_f'] < c['ema_s'] and p['rsi'] > 70 and c['rsi'] < 70:
                    qty = (capital * 0.01) / c['close']
                    position = {'side': 'SELL', 'entry': c['close'], 'stop': c['close'] + c['atr'], 'tp': c['close'] - c['atr'] * 1.5, 'qty': qty}
            else:
                ep = None
                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['high'] >= position['tp']: ep, reason = position['tp'], 'TP'
                    elif c['ema_f'] < c['ema_s']: ep, reason = c['close'], 'CROSS'
                else:
                    if c['high'] >= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['low'] <= position['tp']: ep, reason = position['tp'], 'TP'
                    elif c['ema_f'] > c['ema_s']: ep, reason = c['close'], 'CROSS'
                if ep:
                    pnl = (ep - position['entry']) * position['qty'] * (1 if position['side'] == 'BUY' else -1) - capital * 0.001
                    capital += pnl
                    trades.append({'pnl': pnl, 'win': pnl > 0, 'reason': reason})
                    position = None
            equity.append(capital)
    
    elif name == "smart_money":
        data = data.copy()
        data['atr'] = calc_atr(data)
        data['rsi'] = calc_rsi(data)
        data['vol_sma'] = data['volume'].rolling(20).mean()
        
        for i in range(30, len(data)):
            c = data.iloc[i]
            if position is None:
                # Look for order block retests
                for j in range(max(0, i-20), i):
                    ob = data.iloc[j]
                    if (ob['close'] < ob['open'] and data.iloc[j+1]['close'] > data.iloc[j+1]['open'] and
                        data.iloc[j+1]['close'] > ob['high'] and c['low'] <= ob['high'] and c['low'] >= ob['low'] and c['rsi'] < 40):
                        qty = (capital * 0.02) / c['atr'] if c['atr'] > 0 else 0
                        if qty > 0:
                            position = {'side': 'BUY', 'entry': c['close'], 'stop': ob['low'] - c['atr'], 'tp': c['close'] + c['atr'] * 3, 'qty': qty}
                        break
                    elif (ob['close'] > ob['open'] and data.iloc[j+1]['close'] < data.iloc[j+1]['open'] and
                          data.iloc[j+1]['close'] < ob['low'] and c['high'] >= ob['low'] and c['high'] <= ob['high'] and c['rsi'] > 60):
                        qty = (capital * 0.02) / c['atr'] if c['atr'] > 0 else 0
                        if qty > 0:
                            position = {'side': 'SELL', 'entry': c['close'], 'stop': ob['high'] + c['atr'], 'tp': c['close'] - c['atr'] * 3, 'qty': qty}
                        break
            else:
                ep = None
                if position['side'] == 'BUY':
                    if c['low'] <= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['high'] >= position['tp']: ep, reason = position['tp'], 'TP'
                else:
                    if c['high'] >= position['stop']: ep, reason = position['stop'], 'SL'
                    elif c['low'] <= position['tp']: ep, reason = position['tp'], 'TP'
                if ep:
                    pnl = (ep - position['entry']) * position['qty'] * (1 if position['side'] == 'BUY' else -1) - capital * 0.001
                    capital += pnl
                    trades.append({'pnl': pnl, 'win': pnl > 0, 'reason': reason})
                    position = None
            equity.append(capital)
    
    # Calculate results
    if not trades:
        return {'name': name, 'trades': 0, 'win_rate': 0, 'pnl': 0, 'pf': 0, 'sharpe': 0, 'dd': 0, 'eq': equity}
    
    wins = sum(1 for t in trades if t['win'])
    losses = len(trades) - wins
    win_rate = (wins / len(trades)) * 100
    pnl = sum(t['pnl'] for t in trades)
    
    profits = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses_abs = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    pf = sum(profits) / sum(losses_abs) if losses_abs else 0
    
    peak = equity[0]
    max_dd = 0
    for e in equity:
        if e > peak: peak = e
        dd = (peak - e) / peak * 100
        if dd > max_dd: max_dd = dd
    
    returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else [0]
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
    
    return {
        'name': name, 'trades': len(trades), 'win_rate': win_rate,
        'pnl': pnl, 'pf': pf, 'sharpe': sharpe, 'dd': max_dd,
        'wins': wins, 'losses': losses, 'eq': equity
    }

def main():
    print("\n" + "="*80)
    print("  ESMH.TRADE - MULTI-MARKET BACKTEST RESULTS")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    markets = ["forex", "crypto", "commodities", "metals"]
    strategies = ["trend_follow", "mean_reversion", "breakout", "scalping", "smart_money"]
    
    all_results = {}
    
    for market in markets:
        print(f"\n{'='*80}")
        print(f"  {market.upper()} MARKET")
        print(f"{'='*80}")
        
        data = generate_data(market, 800)
        market_results = []
        
        for strategy in strategies:
            params = {}
            result = run_strategy(strategy, data, params)
            market_results.append(result)
            
            status = "OK" if result['trades'] > 0 else "NO TRADES"
            print(f"  {strategy:<20} | Trades: {result['trades']:>3} | Win%: {result['win_rate']:>5.1f} | "
                  f"PnL: ${result['pnl']:>+8.2f} | PF: {result['pf']:>5.2f} | Sharpe: {result['sharpe']:>5.2f} | "
                  f"MaxDD: {result['dd']:>5.1f}% | {status}")
        
        all_results[market] = market_results
    
    # Summary
    print(f"\n{'='*80}")
    print("  BEST STRATEGY PER MARKET")
    print(f"{'='*80}")
    print(f"  {'Market':<15} {'Best Strategy':<20} {'Win Rate':>10} {'PnL':>12} {'PF':>8}")
    print("-" * 70)
    
    for market, results in all_results.items():
        best = max(results, key=lambda x: x['win_rate'] if x['trades'] >= 3 else 0)
        if best['trades'] >= 3:
            print(f"  {market:<15} {best['name']:<20} {best['win_rate']:>9.1f}% ${best['pnl']:>+10.2f} {best['pf']:>7.2f}")
        else:
            print(f"  {market:<15} {'N/A':<20} {'N/A':>10} {'N/A':>12} {'N/A':>8}")
    
    print(f"\n{'='*80}")
    print("  BACKTEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
