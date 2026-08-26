import sys, os
sys.path.insert(0, 'backend')
from app.core.backtest_engine import BacktestEngine, BacktestConfig, BacktestStrategy

cfg = BacktestConfig(strategy=BacktestStrategy.TREND_FOLLOW, max_positions=3)
eng = BacktestEngine(cfg)
data = eng.generate_sample_data(1000)
# monkey-patch to count
orig_run = eng._run_trend_follow
entries=0; exits=0
import pandas as pd, numpy as np
d = data.copy()
d['ema_fast']=d['close'].ewm(span=12).mean()
d['ema_slow']=d['close'].ewm(span=26).mean()
cross=0
for i in range(50,len(d)):
    p=d.iloc[i-1]; c=d.iloc[i]
    if p['ema_fast']<=p['ema_slow'] and c['ema_fast']>c['ema_slow']: cross+=1
    elif p['ema_fast']>=p['ema_slow'] and c['ema_fast']<c['ema_slow']: cross+=1
print('EMA12/26 crossovers:', cross)
r = eng.run()
print('Total trades:', r.total_trades, 'Wins:', r.winning_trades)
print('Win rate:', r.win_rate)
