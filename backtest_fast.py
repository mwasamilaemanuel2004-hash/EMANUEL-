"""
Ultra-Fast Multi-Market Backtest
"""
import sys, os, numpy as np, pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def gen_data(seed, periods=500):
    np.random.seed(seed)
    base, vol = 100, 0.02
    returns = np.random.normal(0, vol/np.sqrt(24), periods)
    price = base * np.exp(np.cumsum(returns))
    idx = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
    return pd.DataFrame({
        'open': price*(1+np.random.uniform(-0.001,0.001,periods)),
        'high': price*(1+np.abs(np.random.normal(0,vol,periods))),
        'low': price*(1-np.abs(np.random.normal(0,vol,periods))),
        'close': price, 'volume': np.random.lognormal(10,1,periods)
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

def run_tf(data):
    data = data.copy()
    data['ef'] = data['close'].ewm(span=12).mean()
    data['es'] = data['close'].ewm(span=26).mean()
    data['atr'] = atr(data)
    data['rsi'] = rsi(data)
    data['adx'] = adx(data)
    cap, trades, eq = 10000, [], [10000]
    pos = None
    for i in range(30, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        if pos is None:
            if p['ef']<=p['es'] and c['ef']>c['es'] and c['adx']>15 and c['rsi']<65:
                sd=c['atr']*2; q=(cap*0.02)/sd if sd>0 else 0
                if q>0: pos={'s':'B','e':c['close'],'sl':c['close']-sd,'tp':c['close']+sd*2.5,'q':q}
            elif p['ef']>=p['es'] and c['ef']<c['es'] and c['adx']>15 and c['rsi']>35:
                sd=c['atr']*2; q=(cap*0.02)/sd if sd>0 else 0
                if q>0: pos={'s':'S','e':c['close'],'sl':c['close']+sd,'tp':c['close']-sd*2.5,'q':q}
        else:
            ep=None
            if pos['s']=='B':
                if c['low']<=pos['sl']: ep,pos={'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.001,'w':False},None
                elif c['high']>=pos['tp']: ep,pos={'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.001,'w':True},None
                elif c['ef']<c['es']: ep,pos={'pnl':(c['close']-pos['e'])*pos['q']-cap*0.001,'w':(c['close']>pos['e'])},None
            else:
                if c['high']>=pos['sl']: ep,pos={'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.001,'w':False},None
                elif c['low']<=pos['tp']: ep,pos={'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.001,'w':True},None
                elif c['ef']>c['es']: ep,pos={'pnl':(pos['e']-c['close'])*pos['q']-cap*0.001,'w':(c['close']<pos['e'])},None
            if ep: cap+=ep['pnl']; trades.append(ep)
        eq.append(cap)
    return trades, eq

def run_mr(data):
    data = data.copy()
    data['sma'] = data['close'].rolling(20).mean()
    data['std'] = data['close'].rolling(20).std()
    data['z'] = (data['close']-data['sma'])/(data['std']+0.0001)
    data['rsi'] = rsi(data)
    cap, trades, eq = 10000, [], [10000]
    pos = None
    for i in range(25, len(data)):
        c = data.iloc[i]
        if pos is None:
            if c['z']<-2 and c['rsi']<35:
                q=(cap*0.02)/c['close']; pos={'s':'B','e':c['close'],'sl':c['close']*0.975,'tp':c['close']*1.035,'q':q}
            elif c['z']>2 and c['rsi']>65:
                q=(cap*0.02)/c['close']; pos={'s':'S','e':c['close'],'sl':c['close']*1.025,'tp':c['close']*0.965,'q':q}
        else:
            ep=None
            if pos['s']=='B':
                if c['low']<=pos['sl']: ep={'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['high']>=pos['tp']: ep={'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.001,'w':True}; pos=None
                elif c['z']>0: ep={'pnl':(c['close']-pos['e'])*pos['q']-cap*0.001,'w':c['close']>pos['e']}; pos=None
            else:
                if c['high']>=pos['sl']: ep={'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['low']<=pos['tp']: ep={'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.001,'w':True}; pos=None
                elif c['z']<0: ep={'pnl':(pos['e']-c['close'])*pos['q']-cap*0.001,'w':c['close']<pos['e']}; pos=None
            if ep: cap+=ep['pnl']; trades.append(ep)
        eq.append(cap)
    return trades, eq

def run_bo(data):
    data = data.copy()
    data['atr'] = atr(data)
    data['hi'] = data['high'].rolling(20).max()
    data['lo'] = data['low'].rolling(20).min()
    cap, trades, eq = 10000, [], [10000]
    pos = None
    for i in range(25, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        if pos is None:
            if p['high']<=data.iloc[i-2]['hi'] and c['high']>c['hi']:
                sd=c['atr']*1.2; q=(cap*0.02)/sd if sd>0 else 0
                if q>0: pos={'s':'B','e':c['close'],'sl':c['close']-sd,'tp':c['close']+sd*3,'q':q}
            elif p['low']>=data.iloc[i-2]['lo'] and c['low']<c['lo']:
                sd=c['atr']*1.2; q=(cap*0.02)/sd if sd>0 else 0
                if q>0: pos={'s':'S','e':c['close'],'sl':c['close']+sd,'tp':c['close']-sd*3,'q':q}
        else:
            ep=None
            if pos['s']=='B':
                if c['low']<=pos['sl']: ep={'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['high']>=pos['tp']: ep={'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.001,'w':True}; pos=None
            else:
                if c['high']>=pos['sl']: ep={'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['low']<=pos['tp']: ep={'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.001,'w':True}; pos=None
            if ep: cap+=ep['pnl']; trades.append(ep)
        eq.append(cap)
    return trades, eq

def run_scalp(data):
    data = data.copy()
    data['ef'] = data['close'].ewm(span=5).mean()
    data['es'] = data['close'].ewm(span=15).mean()
    data['rsi'] = rsi(data, 7)
    data['atr'] = atr(data, 7)
    cap, trades, eq = 10000, [], [10000]
    pos = None
    for i in range(20, len(data)):
        c, p = data.iloc[i], data.iloc[i-1]
        if pos is None:
            if c['ef']>c['es'] and p['rsi']<30 and c['rsi']>30:
                q=(cap*0.01)/c['close']; pos={'s':'B','e':c['close'],'sl':c['close']-c['atr'],'tp':c['close']+c['atr']*1.5,'q':q}
            elif c['ef']<c['es'] and p['rsi']>70 and c['rsi']<70:
                q=(cap*0.01)/c['close']; pos={'s':'S','e':c['close'],'sl':c['close']+c['atr'],'tp':c['close']-c['atr']*1.5,'q':q}
        else:
            ep=None
            if pos['s']=='B':
                if c['low']<=pos['sl']: ep={'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['high']>=pos['tp']: ep={'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.001,'w':True}; pos=None
                elif c['ef']<c['es']: ep={'pnl':(c['close']-pos['e'])*pos['q']-cap*0.001,'w':c['close']>pos['e']}; pos=None
            else:
                if c['high']>=pos['sl']: ep={'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['low']<=pos['tp']: ep={'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.001,'w':True}; pos=None
                elif c['ef']>c['es']: ep={'pnl':(pos['e']-c['close'])*pos['q']-cap*0.001,'w':c['close']<pos['e']}; pos=None
            if ep: cap+=ep['pnl']; trades.append(ep)
        eq.append(cap)
    return trades, eq

def run_smart(data):
    data = data.copy()
    data['atr'] = atr(data)
    data['rsi'] = rsi(data)
    cap, trades, eq = 10000, [], [10000]
    pos = None
    for i in range(30, len(data)):
        c = data.iloc[i]
        if pos is None:
            for j in range(max(0,i-15), i):
                ob = data.iloc[j]
                if ob['close']<ob['open'] and data.iloc[j+1]['close']>data.iloc[j+1]['open'] and c['low']<=ob['high'] and c['low']>=ob['low'] and c['rsi']<40:
                    q=(cap*0.02)/c['atr'] if c['atr']>0 else 0
                    if q>0: pos={'s':'B','e':c['close'],'sl':ob['low']-c['atr'],'tp':c['close']+c['atr']*3,'q':q}
                    break
                elif ob['close']>ob['open'] and data.iloc[j+1]['close']<data.iloc[j+1]['open'] and c['high']>=ob['low'] and c['high']<=ob['high'] and c['rsi']>60:
                    q=(cap*0.02)/c['atr'] if c['atr']>0 else 0
                    if q>0: pos={'s':'S','e':c['close'],'sl':ob['high']+c['atr'],'tp':c['close']-c['atr']*3,'q':q}
                    break
        else:
            ep=None
            if pos['s']=='B':
                if c['low']<=pos['sl']: ep={'pnl':(pos['sl']-pos['e'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['high']>=pos['tp']: ep={'pnl':(pos['tp']-pos['e'])*pos['q']-cap*0.001,'w':True}; pos=None
            else:
                if c['high']>=pos['sl']: ep={'pnl':(pos['e']-pos['sl'])*pos['q']-cap*0.001,'w':False}; pos=None
                elif c['low']<=pos['tp']: ep={'pnl':(pos['e']-pos['tp'])*pos['q']-cap*0.001,'w':True}; pos=None
            if ep: cap+=ep['pnl']; trades.append(ep)
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
    print("  ESMH.TRADE - MULTI-MARKET BACKTEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    markets = {"forex":100, "crypto":200, "commodities":300, "metals":400}
    strats = {"trend_follow":run_tf, "mean_reversion":run_mr, "breakout":run_bo, "scalping":run_scalp, "smart_money":run_smart}
    
    for mname, seed in markets.items():
        print(f"\n  {mname.upper()} MARKET")
        print(f"  {'Strategy':<20} {'Trades':>7} {'Win%':>7} {'PnL':>10} {'PF':>7} {'Sharpe':>7} {'MaxDD':>7}")
        print("  "+"-"*65)
        data = gen_data(seed, 500)
        for sname, sfunc in strats.items():
            try:
                trades, eq = sfunc(data)
                r = analyze(trades, eq)
                print(f"  {sname:<20} {r['n']:>7} {r['wr']:>6.1f}% ${r['pnl']:>+8.2f} {r['pf']:>6.2f} {r['sh']:>6.2f} {r['dd']:>6.1f}%")
            except Exception as e:
                print(f"  {sname:<20} ERROR: {e}")
    
    print("\n"+"="*80)
    print("  DONE")
    print("="*80)

if __name__ == "__main__":
    main()
