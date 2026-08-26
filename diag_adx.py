import numpy as np, pandas as pd
np.random.seed(42)
dates = pd.date_range(end='now', periods=1000, freq='1h')
returns = np.random.normal(0.0001, 0.02, 1000)
price = 100*np.exp(np.cumsum(returns))
data = pd.DataFrame({'close':price})
data['ema_fast']=data['close'].ewm(span=20).mean()
data['ema_slow']=data['close'].ewm(span=50).mean()
data['adx']=data['close'].pct_change().rolling(14).std()*100
data['vol']=np.random.uniform(1000,10000,1000)
data['vol_avg']=data['vol'].rolling(20).mean()
cross_bull=0; cross_bear=0; pass_bull=0; pass_bear=0
for i in range(50,len(data)):
    c=data.iloc[i]; p=data.iloc[i-1]
    bull = p['ema_fast']<=p['ema_slow'] and c['ema_fast']>c['ema_slow']
    bear = p['ema_fast']>=p['ema_slow'] and c['ema_fast']<c['ema_slow']
    adx_ok = c['adx']>15
    vol_ok = c['vol']>c['vol_avg']
    if bull: cross_bull+=1; pass_bull+=1 if (adx_ok and vol_ok) else 0
    if bear: cross_bear+=1; pass_bear+=1 if (adx_ok and vol_ok) else 0
print(f'Crossovers: bull={cross_bull} bear={cross_bear}')
print(f'Passing ADX>15+vol: bull={pass_bull} bear={pass_bear}')
print(f'ADX>15 count: {(data["adx"]>15).sum()}')
print(f'ADX mean: {data["adx"].mean():.2f} max: {data["adx"].max():.2f}')
