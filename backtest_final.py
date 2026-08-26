"""
Final Optimized Backtest - 55%+ Win Rate Target
"""
import sys, os, numpy as np, pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def gen_data(seed, periods=700):
    np.random.seed(seed)
    configs = {
        100: (1.1000, 0.003),   # forex
        200: (50000, 0.03),     # crypto
        300: (2000, 0.005),     # commodities
        400: (2000, 0.004),     # metals
    }
    base, vol = configs.get(seed, (100, 0.01))
    
    returns = np.random.normal(0.00015, vol/np.sqrt(24), periods)
    for i in range(5, len(returns)):
        returns[i] += 0.12 * returns[i-1] + 0.08 * returns[i-2]
    
    price = base * np.exp(np.cumsum(returns))
    idx = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
    return pd.DataFrame({
        'open': price*(1+np.random.uniform(-0.0003,0.0003,periods)),
        'high': price*(1+np.abs(np.random.normal(0,vol*0.4,periods))),
        'low': price*(1-np.abs(np.random.normal(0,vol*0.4,periods))),
        'close': price, 'volume': np.random.lognormal(10,0.7,periods)
    }, index=idx)

def atr(data, p=14):
    tr = pd.concat([data['high']-data['low'], abs(data['high']-data['close'].shift()), abs(data['low']-data['close'].shift())], axis=1).max(axis=1)
    return tr.rolling(p).mean().bfill()

def rsi(data, p=14):
    d = data['close'].diff()
    g = d.where(d>0,0).rolling(p).mean()
    l = (-d.where(d<0,0)).rolling(p).mean()
    return 100-(100/(1+g/(l+0.0001))).bfill()

def adx(data, p=14):
    pm = data['high'].diff()
    mm = -data['low'].diff()
    pm = pm.where((pm>0)&(pm>mm), 0)
    mm = mm.where((mm>0)&(mm>pm), 0)
    a = atr(data, p)
    pdi = 100*(pm.rolling(p).mean()/(a+0.0001))
    mdi = 100*(mm.rolling(p).mean()/(a+0.0001))
    dx = 100*abs(pdi-mdi)/(pdi+mdi+0.0001)
    return dx.rolling(p).mean().bfill()

def macd(data):
    ema12 = data['close'].ewm(span=12).mean()
    ema26 = data['close'].ewm(span=26).mean()
    line = ema12 - ema26
    sig = line.ewm(span=9).mean()
    return line, sig, line - sig

def bb(data, p=20):
    sma = data['close'].rolling(p).mean()
    std = data['close'].rolling(p).std()
    return sma + 2*std, sma - 2*std

# ============================================
# STRATEGY 1: TREND FOLLOW (Target: 55%+ WR)
# ============================================
def strat_trend_follow(data):
    data = data.copy()
    data['ema_f'] = data['close'].ewm(span=8).mean()
    data['ema_s'] = data['close'].ewm(span=21).mean()
    data['atr'] = atr(data)
    data['rsi'] = rsi(data)
    data['adx'] = adx(data)
    data['macd'], data['macd_sig'], data['macd_hist'] = macd(data)
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(30, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        
        if pos is None:
            # Strong trend + MACD + RSI confluence
            bull = (c['ema_f'] > c['ema_s'] and p['ema_f'] <= p['ema_s'] and
                    c['adx'] > 22 and 35 < c['rsi'] < 60 and c['macd_hist'] > 0)
            bear = (c['ema_f'] < c['ema_s'] and p['ema_f'] >= p['ema_s'] and
                    c['adx'] > 22 and 40 < c['rsi'] < 65 and c['macd_hist'] < 0)
            
            if bull or bear:
                side = 'B' if bull else 'S'
                sd = c['atr'] * 1.8
                q = (cap * 0.012) / sd if sd > 0 else 0
                if q > 0:
                    pos = {'s':side, 'e':c['close'], 'sl':c['close']-sd if bull else c['close']+sd,
                           'tp':c['close']+sd*3 if bull else c['close']-sd*3, 'q':q, 'trail':False}
        else:
            ep = None
            if pos['s'] == 'B':
                # Trailing stop logic
                if c['high'] > pos['e'] + (pos['tp']-pos['e'])*0.5:
                    pos['sl'] = max(pos['sl'], pos['e'])
                if c['high'] > pos['e'] + (pos['tp']-pos['e'])*0.75:
                    pos['sl'] = max(pos['sl'], pos['e'] + (pos['tp']-pos['e'])*0.3)
                
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0003, 'w':pos['sl']>pos['e']}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
            else:
                if c['low'] < pos['e'] - (pos['e']-pos['tp'])*0.5:
                    pos['sl'] = min(pos['sl'], pos['e'])
                if c['low'] < pos['e'] - (pos['e']-pos['tp'])*0.75:
                    pos['sl'] = min(pos['sl'], pos['e'] - (pos['e']-pos['tp'])*0.3)
                
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0003, 'w':pos['sl']<pos['e']}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
            
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

# ============================================
# STRATEGY 2: MEAN REVERSION (Target: 60%+ WR)
# ============================================
def strat_mean_reversion(data):
    data = data.copy()
    data['sma'] = data['close'].rolling(20).mean()
    data['std'] = data['close'].rolling(20).std()
    data['z'] = (data['close']-data['sma'])/(data['std']+0.0001)
    data['rsi'] = rsi(data, 9)
    data['bb_up'], data['bb_lo'] = bb(data)
    data['macd'], _, data['macd_hist'] = macd(data)
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(25, len(data)):
        c = data.iloc[i]
        
        if pos is None:
            # Extreme oversold with multiple confirmations
            buy = (c['z'] < -2.5 and c['rsi'] < 25 and c['close'] < c['bb_lo'] and
                   c['macd_hist'] > data.iloc[i-1].get('macd_hist', 0))
            sell = (c['z'] > 2.5 and c['rsi'] > 75 and c['close'] > c['bb_up'] and
                    c['macd_hist'] < data.iloc[i-1].get('macd_hist', 0))
            
            if buy:
                q = (cap * 0.012) / c['close']
                pos = {'s':'B', 'e':c['close'], 'sl':c['close']*0.985, 'tp':c['close']*1.025, 'q':q}
            elif sell:
                q = (cap * 0.012) / c['close']
                pos = {'s':'S', 'e':c['close'], 'sl':c['close']*1.015, 'tp':c['close']*0.975, 'q':q}
        else:
            ep = None
            if pos['s'] == 'B':
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0003, 'w':False}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
                elif c['z'] > -0.2:
                    ep = {'pnl':(c['close']-pos['e'])*pos['q']-cap*0.0003, 'w':c['close']>pos['e']}
                    pos = None
            else:
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0003, 'w':False}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
                elif c['z'] < 0.2:
                    ep = {'pnl':(pos['e']-c['close'])*pos['q']-cap*0.0003, 'w':c['close']<pos['e']}
                    pos = None
            
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

# ============================================
# STRATEGY 3: BREAKOUT (Target: 50%+ WR)
# ============================================
def strat_breakout(data):
    data = data.copy()
    data['atr'] = atr(data)
    data['hi'] = data['high'].rolling(20).max()
    data['lo'] = data['low'].rolling(20).min()
    data['vol_sma'] = data['volume'].rolling(20).mean()
    data['rsi'] = rsi(data)
    data['adx'] = adx(data)
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(25, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        
        if pos is None:
            # Breakout with volume + ADX confirmation
            vol_ok = c['volume'] > c['vol_sma'] * 1.3
            adx_ok = c['adx'] > 22
            
            if p['high'] <= data.iloc[i-2]['hi'] and c['high'] > c['hi'] and vol_ok and adx_ok and c['rsi'] < 60:
                sd = c['atr'] * 1.5
                q = (cap * 0.012) / sd if sd > 0 else 0
                if q > 0:
                    pos = {'s':'B', 'e':c['close'], 'sl':c['close']-sd, 'tp':c['close']+sd*4, 'q':q}
            elif p['low'] >= data.iloc[i-2]['lo'] and c['low'] < c['lo'] and vol_ok and adx_ok and c['rsi'] > 40:
                sd = c['atr'] * 1.5
                q = (cap * 0.012) / sd if sd > 0 else 0
                if q > 0:
                    pos = {'s':'S', 'e':c['close'], 'sl':c['close']+sd, 'tp':c['close']-sd*4, 'q':q}
        else:
            ep = None
            if pos['s'] == 'B':
                if c['high'] > pos['e'] * 1.008:
                    pos['sl'] = max(pos['sl'], pos['e'])
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0003, 'w':pos['sl']>pos['e']}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
            else:
                if c['low'] < pos['e'] * 0.992:
                    pos['sl'] = min(pos['sl'], pos['e'])
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0003, 'w':pos['sl']<pos['e']}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0003, 'w':True}
                    pos = None
            
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

# ============================================
# STRATEGY 4: SCALPING (Target: 65%+ WR)
# ============================================
def strat_scalping(data):
    data = data.copy()
    data['ema_f'] = data['close'].ewm(span=5).mean()
    data['ema_s'] = data['close'].ewm(span=13).mean()
    data['rsi'] = rsi(data, 7)
    data['atr'] = atr(data, 7)
    data['macd'], _, data['macd_hist'] = macd(data)
    
    cap, trades, eq = 10000, [], [10000]
    pos = None
    
    for i in range(20, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        
        if pos is None:
            # Quick scalping with tight TP
            buy = (c['ema_f'] > c['ema_s'] and p['rsi'] < 28 and c['rsi'] > 28 and c['macd_hist'] > 0)
            sell = (c['ema_f'] < c['ema_s'] and p['rsi'] > 72 and c['rsi'] < 72 and c['macd_hist'] < 0)
            
            if buy:
                q = (cap * 0.008) / c['close']
                pos = {'s':'B', 'e':c['close'], 'sl':c['close']-c['atr']*0.6, 'tp':c['close']+c['atr']*1.8, 'q':q}
            elif sell:
                q = (cap * 0.008) / c['close']
                pos = {'s':'S', 'e':c['close'], 'sl':c['close']+c['atr']*0.6, 'tp':c['close']-c['atr']*1.8, 'q':q}
        else:
            ep = None
            if pos['s'] == 'B':
                if c['low'] <= pos['sl']:
                    ep = {'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.0002, 'w':False}
                    pos = None
                elif c['high'] >= pos['tp']:
                    ep = {'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.0002, 'w':True}
                    pos = None
                elif c['high'] > pos['e'] + c['atr'] * 0.3:
                    pos['sl'] = max(pos['sl'], pos['e'] - c['atr']*0.1)
            else:
                if c['high'] >= pos['sl']:
                    ep = {'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.0002, 'w':False}
                    pos = None
                elif c['low'] <= pos['tp']:
                    ep = {'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.0002, 'w':True}
                    pos = None
                elif c['low'] < pos['e'] - c['atr'] * 0.3:
                    pos['sl'] = min(pos['sl'], pos['e'] + c['atr']*0.1)
            
            if ep:
                cap += ep['pnl']
                trades.append(ep)
        eq.append(cap)
    return trades, eq

def analyze(trades, eq):
    if not trades: return {'n':0,'wr':0,'pnl':0,'pf':0,'sh':0,'dd':0,'avg_w':0,'avg_l':0}
    wins = sum(1 for t in trades if t['w'])
    n = len(trades)
    wr = (wins/n)*100
    pnl = sum(t['pnl'] for t in trades)
    wins_pnl = [t['pnl'] for t in trades if t['w']]
    loss_pnl = [t['pnl'] for t in trades if not t['w']]
    avg_w = np.mean(wins_pnl) if wins_pnl else 0
    avg_l = np.mean(loss_pnl) if loss_pnl else 0
    profs = sum(wins_pnl) if wins_pnl else 0
    loss = sum(abs(x) for x in loss_pnl) if loss_pnl else 0.0001
    pf = profs/loss
    peak = eq[0]; mdd = 0
    for e in eq:
        if e>peak: peak=e
        dd=(peak-e)/peak*100
        if dd>mdd: mdd=dd
    rets = np.diff(eq)/(np.array(eq[:-1])+0.0001)
    sh = np.mean(rets)/(np.std(rets)+0.0001)*np.sqrt(252) if len(rets)>1 and np.std(rets)>0 else 0
    return {'n':n,'wr':wr,'pnl':pnl,'pf':pf,'sh':sh,'dd':mdd,'avg_w':avg_w,'avg_l':avg_l}

def main():
    print("\n"+"="*85)
    print("  ESMH.TRADE - FINAL OPTIMIZED BACKTEST (HIGH WIN RATE)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*85)
    
    markets = {"FOREX":100, "CRYPTO":200, "COMMODITIES":300, "METALS":400}
    strats = {"Trend Follow":strat_trend_follow, "Mean Reversion":strat_mean_reversion,
              "Breakout":strat_breakout, "Scalping":strat_scalping}
    
    best_by_market = {}
    
    for mname, seed in markets.items():
        print(f"\n  {mname} MARKET")
        print(f"  {'Strategy':<18} {'Trades':>6} {'Win%':>6} {'PnL':>9} {'PF':>6} {'Sharpe':>6} {'MaxDD':>6} {'AvgW':>7} {'AvgL':>7}")
        print("  "+"-"*72)
        data = gen_data(seed, 700)
        
        best_wr = 0
        best_strat = None
        
        for sname, sfunc in strats.items():
            try:
                trades, eq = sfunc(data)
                r = analyze(trades, eq)
                if r['n'] > 0:
                    print(f"  {sname:<18} {r['n']:>6} {r['wr']:>5.1f}% ${r['pnl']:>+7.2f} {r['pf']:>5.2f} {r['sh']:>5.2f} {r['dd']:>5.1f}% ${r['avg_w']:>+6.2f} ${r['avg_l']:>+6.2f}")
                    if r['wr'] > best_wr and r['n'] >= 3:
                        best_wr = r['wr']
                        best_strat = sname
                        best_by_market[mname] = {'strat': sname, 'wr': r['wr'], 'pnl': r['pnl'], 'pf': r['pf'], 'trades': r['n']}
                else:
                    print(f"  {sname:<18} {'No trades':>50}")
            except Exception as e:
                print(f"  {sname:<18} ERROR: {str(e)[:40]}")
    
    # Summary
    print("\n"+"="*85)
    print("  BEST STRATEGY PER MARKET")
    print("="*85)
    print(f"  {'Market':<15} {'Strategy':<18} {'Win Rate':>10} {'PnL':>10} {'PF':>8} {'Trades':>8}")
    print("-"*70)
    for m, b in best_by_market.items():
        print(f"  {m:<15} {b['strat']:<18} {b['wr']:>9.1f}% ${b['pnl']:>+8.2f} {b['pf']:>7.2f} {b['trades']:>8}")
    
    print("\n"+"="*85)
    print("  RECOMMENDATIONS:")
    print("  1. Use Trend Follow for trending markets (ADX > 22)")
    print("  2. Use Mean Reversion for ranging markets (z-score < -2.5)")
    print("  3. Use Breakout for high volatility breakouts")
    print("  4. Use Scalping for quick trades with tight stops")
    print("  5. Always use trailing stops to lock in profits")
    print("  6. Risk max 1.2% per trade for higher win rate")
    print("="*85)

if __name__ == "__main__":
    main()
