import sys, os
sys.path.insert(0, 'backend')
import numpy as np, pandas as pd
from app.core.smart_entry import SmartEntryEngine
from app.core.master_trade_filter import MasterTradeFilter, Decision

np.random.seed(1)
price = 100*np.exp(np.cumsum(np.random.normal(0.0005, 0.01, 300)))
df = pd.DataFrame({'high': price*1.01, 'low': price*0.99, 'close': price, 'open': price, 'volume': 5000})

eng = SmartEntryEngine()
plan = eng.build_plan('BUY', df['close'].iloc[50], 1.0, 'STRONG_TREND')
r = eng.simulate(plan, df.iloc[51:151])
print('simulate won:', r.won, 'pnl%:', round(r.pnl_pct, 3), 'reason:', r.exit_reason)

# master filter quick test
mf = MasterTradeFilter()
mtf = {'1h': df, '1d': df, '4h': df, '15m': df}
fr = mf.evaluate(mtf, 'BUY', df['close'].iloc[50], plan.sl, plan.tp1, symbol='BTC', risk_pct=1.0)
print('filter decision:', fr.decision.value, 'score:', round(fr.score,1), 'reason:', fr.reason)
