import sys
sys.path.insert(0, 'backend')
import numpy as np
from backtest_v2 import make_mtf, find_candidates
from app.core.sm_engine import detect_sm_setups
for s in [7, 21, 42, 99]:
    np.random.seed(s)
    mtf = make_mtf(seed=s)
    df, c = find_candidates(mtf)
    sm = detect_sm_setups(df, hold_bars=2)
    sm_killzone = sum(1 for x in sm if any(x.ltf_idx == y['ltf_idx'] for y in c))
    print(f"seed={s}  sm_total={len(sm)}  candidates_after_filter={len(c)}")
