import sys, signal
sys.path.insert(0, 'backend')
import numpy as np
from backtest_v2 import make_mtf, find_candidates
from app.core.sm_engine import detect_sm_setups
from app.core.smart_entry import SmartEntryEngine

eng = SmartEntryEngine()
np.random.seed(21)
mtf = make_mtf(seed=21)
df, cands = find_candidates(mtf)
print(f"candidates: {len(cands)}")
w = l = 0; cd = 0
for i, c in enumerate(cands):
    if cd > 0: cd -= 1; continue
    if c['ltf_idx'] + 60 >= len(df): continue
    h = df.iloc[:c['ltf_idx']+1]
    atr = float(h['close'].diff().abs().rolling(14).mean().iloc[-1])
    atr = max(atr, c['entry'] * 0.002)
    p = eng.build_plan(c['side'], c['entry'], atr, 'STRONG_TREND', structure_sl=c['sl'])
    f = df.iloc[c['ltf_idx']+1: c['ltf_idx']+81]
    o = eng.simulate(p, f)
    if o.won: w += 1; cd = 2
    else: l += 1; cd = 4
    if i % 10 == 0:
        print(f"  {i}/{len(cands)} done, wins={w} losses={l}")
t = w + l
print(f"FINAL: {t} trades, WR={w/t*100:.1f}%" if t else "no trades")
