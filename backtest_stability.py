import sys, time
sys.path.insert(0, 'backend')
import numpy as np
from backtest_v2 import make_mtf, find_candidates
from app.core.smart_entry import SmartEntryEngine

eng = SmartEntryEngine()
print("seed  trades  WR%    PF   exp%")
results = []
for seed in [7, 13, 21, 42, 99, 123, 200]:
    t0 = time.time()
    np.random.seed(seed)
    mtf = make_mtf(seed=seed)
    df, cands = find_candidates(mtf)
    w = l = 0; cd = 0; pnls = []
    for c in cands:
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
        pnls.append(o.pnl_pct)
    t = w + l
    wr = w / t * 100 if t else 0
    pf_w = sum(x for x in pnls if x > 0)
    pf_l = abs(sum(x for x in pnls if x < 0))
    pf = pf_w / pf_l if pf_l else 0
    exp = np.mean(pnls) * 100 if pnls else 0
    elapsed = time.time() - t0
    results.append((seed, t, wr, pf, exp))
    print(f"{seed:4d}  {t:5d}  {wr:5.1f}  {pf:4.2f}  {exp:+.3f}  ({elapsed:.1f}s)")

wrs = [r[2] for r in results]
print(f"\nAvg WR: {sum(wrs)/len(wrs):.1f}%, Seeds >=60%: {sum(1 for w in wrs if w>=60)}/7")
print("DONE")
