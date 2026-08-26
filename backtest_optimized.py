"""
Optimized Backtest - Higher Win Rate Strategies
"""
import sys, os, numpy as np, pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def gen_data(seed, periods=600):
    np.random.seed(seed)
    if seed == 100:  # forex
        base, vol = 1.1000, 0.003
    elif seed == 200:  # crypto
        base, vol = 50000, 0.035
    elif seed == 300:  # commodities
        base, vol = 2000, 0.006
    else:  # metals
        base, vol = 2000, 0.005
    
    returns = np.random.normal(0.0002, vol/np.sqrt(24), periods)
    # Add momentum
    for i in range(10, len(returns)):
        returns[i] += 0.15 * returns[i-1] + 0.1 * returns[i-2] + 0.05 * returns[i-3]
    
    price = base * np.exp(np.cumsum(returns))
    idx = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
    return pd.DataFrame({
        'open': price*(1+np.random.uniform(-0.0005,0.0005,periods)),
        'high': price*(1+np.abs(np.random.normal(0,vol*0.5,periods))),
        'low': price*(1-np.abs(np.random.normal(0,vol*0.5,periods))),
        'close': price, 'volume': np.random.lognormal(10,0.8,periods)
    }, index=idx)

def atr(data, p=14):
    tr = pd.concat([data['high']-data['low'], abs(data['high']-data['close'].shift()), abs(data['low']-data['close'].shift())], axis=1).max(axis=1)
    return tr.rolling(p).mean()

def rsi(data, p=14):
    d = data['close'].diff()
    g = d.where(d>0,0).rolling(p).mean()
    l = (-d.where(d<0,0)).rolling(p).mean()
    return 100-(100/(1+g/(l+0.0001)))

def adx(data, p=14):
    pm = data['high'].diff()
    mm = -data['low'].diff()
    pm = pm.where((pm>0)&(pm>mm),0)
    mm = mm.where((mm>0)&(mm>pm),0)
    a = atr(data,p)
    pdi = 100*(pm.rolling(p).mean()/(a+0.0001))
    mdi = 100*(mm.rolling(p).mean()/(a+0.0001))
    dx = 100*abs(pdi-mdi)/(pdi+mdi+0.0001)
    return dx.rolling(p).mean()

def macd(data):
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()
    return macd_line, signal, macd_line - signal

def bb(data, p=20):
    sma = data['close'].rolling(p).mean()
    std = data['close'].rolling(p).std()
    return sma + 2*std, sma - 2*std

# ============================================
# OPTIMIZED STRATEGIES FOR HIGHER WIN RATE
# ============================================

def run_optimized_tf(data):
    """Optimized Trend Follow with multiple confirmations"""
    data = data.copy()
    data['ef'] = data['close'].ewm(span=10).mean()
    data['es'] = data['close'].ewm(span=21).mean()
    data['atr'] = atr(data)
    data['rsi'] = rsi(data)
    data['adx'] = adx(data)
    data['macd'], data['macd_sig'], data['macd_hist'] = macd(data)
    data['bb_up'], data['bb_lo'] = bb(data)
    data['vol_sma'] = data['volume'].rolling(20).mean()
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(30, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        
        if pos is None:
            # Multiple confirmations for higher win rate
            ema_cross_bull = p['ef'] <= p['es'] and c['ef'] > c['es']
            ema_cross_bear = p['ef'] >= p['es'] and c['ef'] < c['es']
            trend_strong = c['adx'] > 20
            macd_confirm_bull = c['macd_hist'] > 0 and p['macd_hist'] <= 0
            macd_confirm_bear = c['macd_hist'] < 0 and p['macd_hist'] >= 0
            rsi_ok_bull = 30 < c['rsi'] < 65
            rsi_ok_bear = 35 < c['rsi'] < 70
            vol_ok = c['volume'] > c['vol_sma'] * 0.8
            
            if (ema_cross_bull or macd_confirm_bull) and trend_strong and rsi_ok_bull and vol_ok:
                sd = c['atr'] * 1.5
                q = (cap * 0.015) / sd if sd > 0 else 0
                if q > 0:
                    pos = {'s':'B', 'e':c['close'], 'sl':c['close']-sd, 'tp':c['close']+sd*3, 'q':q}
            elif (ema_cross_bear or macd_confirm_bear) and trend_strong and rsi_ok_bear and vol_ok:
                sd = c['atr'] * 1.5
                q = (cap * 0.015) / sd if sd > 0 else 0
                if q > 0:
                    pos = {'s':'S', 'e':c['close'], 'sl':c['close']+sd, 'tp':c['close']-sd*3, 'q':q}
        else:
            ep = None
            # Trailing stop for better win rate
            if pos['s'] == 'B':
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0005, 'w':False}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0005, 'w':True}
                    pos = None
                elif c['high'] > pos['e'] + (pos['tp']-pos['e'])*0.6:
                    # Move stop to breakeven + small profit
                    pos['sl'] = max(pos['sl'], pos['e'] + c['atr']*0.1)
                elif c['ef'] < c['es'] and c['macd_hist'] < 0:
                    ep = {'pnl':(c['close']-pos['e'])*pos['q']-cap*0.0005, 'w':c['close']>pos['e']}
                    pos = None
            else:
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0005, 'w':False}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0005, 'w':True}
                    pos = None
                elif c['low'] < pos['e'] - (pos['e']-pos['tp'])*0.6:
                    pos['sl'] = min(pos['sl'], pos['e'] - c['atr']*0.1)
                elif c['ef'] > c['es'] and c['macd_hist'] > 0:
                    ep = {'pnl':(pos['e']-c['close'])*pos['q']-cap*0.0005, 'w':c['close']<pos['e']}
                    pos = None
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

def run_optimized_mr(data):
    """Optimized Mean Reversion with strict entry filters"""
    data = data.copy()
    data['sma'] = data['close'].rolling(20).mean()
    data['std'] = data['close'].rolling(20).std()
    data['z'] = (data['close']-data['sma'])/(data['std']+0.0001)
    data['rsi'] = rsi(data, 10)
    data['atr'] = atr(data)
    data['bb_up'], data['bb_lo'] = bb(data)
    data['macd'], data['macd_sig'], data['macd_hist'] = macd(data)
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(25, len(data)):
        c = data.iloc[i]
        
        if pos is None:
            # Strict oversold conditions for buying
            buy = (c['z'] < -2.2 and c['rsi'] < 28 and c['close'] < c['bb_lo'] and
                   c['macd_hist'] > p['macd_hist'] if 'p' in dir() else c['macd_hist'] > -999)
            # Actually use current z and rsi conditions
            buy = c['z'] < -2.2 and c['rsi'] < 30 and c['close'] < c['bb_lo']
            sell = c['z'] > 2.2 and c['rsi'] > 70 and c['close'] > c['bb_up']
            
            if buy:
                q = (cap * 0.015) / c['close']
                pos = {'s':'B', 'e':c['close'], 'sl':c['close']*0.98, 'tp':c['close']*1.03, 'q':q}
            elif sell:
                q = (cap * 0.015) / c['close']
                pos = {'s':'S', 'e':c['close'], 'sl':c['close']*1.02, 'tp':c['close']*0.97, 'q':q}
        else:
            ep = None
            if pos['s'] == 'B':
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0005, 'w':False}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0005, 'w':True}
                    pos = None
                elif c['z'] > -0.3:
                    ep = {'pnl':(c['close']-pos['e'])*pos['q']-cap*0.0005, 'w':c['close']>pos['e']}
                    pos = None
            else:
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0005, 'w':False}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0005, 'w':True}
                    pos = None
                elif c['z'] < 0.3:
                    ep = {'pnl':(pos['e']-c['close'])*pos['q']-cap*0.0005, 'w':c['close']<pos['e']}
                    pos = None
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

def run_optimized_breakout(data):
    """Optimized Breakout with volume and momentum confirmation"""
    data = data.copy()
    data['atr'] = atr(data)
    data['hi'] = data['high'].rolling(25).max()
    data['lo'] = data['low'].rolling(25).min()
    data['vol_sma'] = data['volume'].rolling(25).mean()
    data['rsi'] = rsi(data)
    data['adx'] = adx(data)
    data['macd'], _, data['macd_hist'] = macd(data)
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(30, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        
        if pos is None:
            # Breakout with volume and momentum
            vol_surge = c['volume'] > c['vol_sma'] * 1.5
            adx_ok = c['adx'] > 20
            
            if (p['high'] <= data.iloc[i-2]['hi'] and c['high'] > c['hi'] and 
                vol_surge and adx_ok and c['rsi'] < 65 and c['macd_hist'] > 0):
                sd = c['atr'] * 1.5
                q = (cap * 0.015) / sd if sd > 0 else 0
                if q > 0:
                    pos = {'s':'B', 'e':c['close'], 'sl':c['close']-sd, 'tp':c['close']+sd*3.5, 'q':q}
            elif (p['low'] >= data.iloc[i-2]['lo'] and c['low'] < c['lo'] and
                  vol_surge and adx_ok and c['rsi'] > 35 and c['macd_hist'] < 0):
                sd = c['atr'] * 1.5
                q = (cap * 0.015) / sd if sd > 0 else 0
                if q > 0:
                    pos = {'s':'S', 'e':c['close'], 'sl':c['close']+sd, 'tp':c['close']-sd*3.5, 'q':q}
        else:
            ep = None
            if pos['s'] == 'B':
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0005, 'w':False}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0005, 'w':True}
                    pos = None
                elif c['high'] > pos['e'] * 1.01:
                    pos['sl'] = max(pos['sl'], pos['e'] * 0.998)
            else:
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0005, 'w':False}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0005, 'w':True}
                    pos = None
                elif c['low'] < pos['e'] * 0.99:
                    pos['sl'] = min(pos['sl'], pos['e'] * 1.002)
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

def run_optimized_scalp(data):
    """Optimized Scalping with EMA + RSI + MACD confluence"""
    data = data.copy()
    data['ef'] = data['close'].ewm(span=5).mean()
    data['es'] = data['close'].ewm(span=13).mean()
    data['rsi'] = rsi(data, 7)
    data['atr'] = atr(data, 7)
    data['macd'], _, data['macd_hist'] = macd(data)
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(20, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        
        if pos is None:
            # Scalping with confluence
            buy = (c['ef'] > c['es'] and c['rsi'] > 30 and p['rsi'] <= 30 and
                   c['macd_hist'] > 0 and c['rsi'] < 60)
            sell = (c['ef'] < c['es'] and c['rsi'] < 70 and p['rsi'] >= 70 and
                    c['macd_hist'] < 0 and c['rsi'] > 40)
            
            if buy:
                q = (cap * 0.01) / c['close']
                pos = {'s':'B', 'e':c['close'], 'sl':c['close']-c['atr']*0.8, 'tp':c['close']+c['atr']*2, 'q':q}
            elif sell:
                q = (cap * 0.01) / c['close']
                pos = {'s':'S', 'e':c['close'], 'sl':c['close']+c['atr']*0.8, 'tp':c['close']-c['atr']*2, 'q':q}
        else:
            ep = None
            if pos['s'] == 'B':
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0003, 'w':False}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
                elif c['high'] > pos['e'] + c['atr'] * 0.5:
                    pos['sl'] = max(pos['sl'], pos['e'])
                elif c['ef'] < c['es']:
                    ep = {'pnl':(c['close']-pos['e'])*pos['q']-cap*0.0003, 'w':c['close']>pos['e']}
                    pos = None
            else:
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0003, 'w':False}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
                elif c['low'] < pos['e'] - c['atr'] * 0.5:
                    pos['sl'] = min(pos['sl'], pos['e'])
                elif c['ef'] > c['es']:
                    ep = {'pnl':(pos['e']-c['close'])*pos['q']-cap*0.0003, 'w':c['close']<pos['e']}
                    pos = None
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

def analyze(trades, eq):
    if not trades: return {'n':0,'wr':0,'pnl':0,'pf':0,'sh':0,'dd':0}
    wins = sum(1 for t in trades if t['w'])
    n = len(trades)
    wr = (wins/n)*100
    pnl = sum(t['pnl'] for t in trades)
    profs = sum(t['pnl'] for t in trades if t['pnl']>0)
    loss = sum(abs(t['pnl']) for t in trades if t['pnl']<0)
    pf = profs/(loss+0.0001)
    peak = eq[0]; mdd = 0
    for e in eq:
        if e>peak: peak=e
        dd=(peak-e)/peak*100
        if dd>mdd: mdd=dd
    rets = np.diff(eq)/(np.array(eq[:-1])+0.0001)
    sh = np.mean(rets)/(np.std(rets)+0.0001)*np.sqrt(252) if len(rets)>1 and np.std(rets)>0 else 0
    return {'n':n,'wr':wr,'pnl':pnl,'pf':pf,'sh':sh,'dd':mdd}

def main():
    print("\n"+"="*80)
    print("  ESMH.TRADE - OPTIMIZED STRATEGIES (HIGHER WIN RATE)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    markets = {"forex":100, "crypto":200, "commodities":300, "metals":400}
    strats = {
        "trend_follow": run_optimized_tf,
        "mean_reversion": run_optimized_mr,
        "breakout": run_optimized_breakout,
        "scalping": run_optimized_scalp,
    }
    
    for mname, seed in markets.items():
        print(f"\n  {mname.upper()} MARKET")
        print(f"  {'Strategy':<20} {'Trades':>7} {'Win%':>7} {'PnL':>10} {'PF':>7} {'Sharpe':>7} {'MaxDD':>7}")
        print("  "+"-"*65)
        data = gen_data(seed, 600)
        for sname, sfunc in strats.items():
            try:
                trades, eq = sfunc(data)
                r = analyze(trades, eq)
                print(f"  {sname:<20} {r['n']:>7} {r['wr']:>6.1f}% ${r['pnl']:>+8.2f} {r['pf']:>6.2f} {r['sh']:>6.2f} {r['dd']:>6.1f}%")
            except Exception as e:
                print(f"  {sname:<20} ERROR: {str(e)[:40]}")
    
    print("\n"+"="*80)
    print("  OPTIMIZATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
