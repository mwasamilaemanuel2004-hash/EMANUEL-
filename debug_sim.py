import sys
sys.path.insert(0, 'backend')
import numpy as np, pandas as pd
from app.core.smart_entry import SmartEntryEngine

np.random.seed(1)
price = 100*np.exp(np.cumsum(np.random.normal(0.0005, 0.01, 300)))
df = pd.DataFrame({'high': price*1.01, 'low': price*0.99, 'close': price, 'open': price, 'volume': 5000})
eng = SmartEntryEngine()
entry = df['close'].iloc[50]
atr = 1.0
plan = eng.build_plan('BUY', entry, atr, 'STRONG_TREND')
print('entry', round(entry,2), 'sl', round(plan.sl,2), 'tp1', round(plan.tp1,2), 'tp2', round(plan.tp2,2), 'runner', round(plan.runner,2))
print('risk', round(abs(entry-plan.sl),3))

res = eng.simulate(plan, df.iloc[51:151])
print('won', res.won, 'pnl%', round(res.pnl_pct,4), 'reason', res.exit_reason, 'tp1', res.tp1_hit, 'tp2', res.tp2_hit)
print('MFE', round(res.max_favorable,2), 'MAE', round(res.max_adverse,2))
