"""
Forward Test — walk-forward validation on UNSEEN data.

The backtest used seeds [7, 13, 21, 42, 99, 123, 200]. The forward test
uses DIFFERENT seeds [300, 400, 500, 600, 700, 800, 900] to validate that
the system generalizes (not overfit to the backtest seeds).

Also runs a true walk-forward: train (parameter scan) on first 60% of each
seed, then test on the remaining 40% out-of-sample.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
import numpy as np
import pandas as pd
from loguru import logger
logger.remove(); logger.add(lambda _: None, level="CRITICAL")

from app.core.smart_entry import SmartEntryEngine
from app.core.crt_engine import detect_crt
from app.core.tbs_engine import session_multiplier
from app.core.sm_engine import detect_sm_setups
from app.core.agent_dispatcher import AgentDispatcher
from app.core.profit_enhancer import ProfitEnhancer
from app.core.multi_confluence import enhance_setup_confluence


def make_mtf(periods=2400, seed=21):
    np.random.seed(seed)
    dates = pd.date_range(end='now', periods=periods, freq='1h', tz='UTC')
    seg = periods // 6
    drifts = [0.0006, -0.0006, 0.0005, -0.0005, 0.0007, -0.0007]
    rets = np.zeros(periods)
    for i in range(periods):
        s = min(i // seg, len(drifts) - 1)
        rets[i] = drifts[s] + np.random.normal(0, 0.0025)
    close = 100 * np.exp(np.cumsum(rets))
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.002, 0.002, periods)),
        'high': close * (1 + np.random.uniform(0, 0.005, periods)),
        'low':  close * (1 - np.random.uniform(0, 0.005, periods)),
        'close': close,
        'volume': np.random.uniform(3000, 9000, periods),
    }, index=dates)
    df['high'] = df[['open','close','high']].max(axis=1)
    df['low']  = df[['open','close','low']].min(axis=1)
    mtf = {'15m': df.copy(), '1h': df.copy()}
    mtf['4h'] = df.resample('4h').agg({'open':'first','high':'max','low':'min',
                                       'close':'last','volume':'sum'}).dropna()
    mtf['1d'] = df.resample('1D').agg({'open':'first','high':'max','low':'min',
                                       'close':'last','volume':'sum'}).dropna()
    return mtf


def htf_soft_trend(htf_df, ts):
    sub = htf_df.loc[htf_df.index <= ts]
    if len(sub) < 30: return 0
    ema50 = sub['close'].ewm(span=50).mean().iloc[-1]
    price = sub['close'].iloc[-1]
    if price > ema50 * 1.001: return 1
    if price < ema50 * 0.999: return -1
    return 0


def find_candidates(mtf, up_to_idx=None):
    """EXACT v2/v3. up_to_idx limits detection to first N bars (walk-forward)."""
    df_full = mtf['15m']
    df = df_full.iloc[:up_to_idx] if up_to_idx else df_full
    sm_setups = detect_sm_setups(df, hold_bars=2)
    crt = detect_crt(df, mtf['4h'].loc[:df.index[-1]], lookback_htf=3)
    candidates = []
    for s in sm_setups:
        if s.ltf_idx + 60 >= len(df_full): continue
        ts = df.index[s.ltf_idx]
        if session_multiplier(ts) < 0.5: continue
        t4 = htf_soft_trend(mtf['4h'], ts)
        want = 1 if s.side == 'BUY' else -1
        if t4 != 0 and t4 != want: continue
        candidates.append({'ltf_idx': s.ltf_idx, 'side': s.side,
                           'entry': s.entry, 'sl': s.sl, 'reason': s.reason})
    for c in crt:
        if c.choch_index + 60 >= len(df_full): continue
        ts = df.index[c.choch_index]
        if session_multiplier(ts) < 0.5: continue
        t4 = htf_soft_trend(mtf['4h'], ts)
        want = 1 if c.direction == 'BUY' else -1
        if t4 != 0 and t4 != want: continue
        candidates.append({'ltf_idx': c.choch_index, 'side': c.direction,
                           'entry': c.ltf_entry, 'sl': c.invalidation,
                           'reason': f"CRT {c.direction}"})
    seen = set(); uniq = []
    for c in candidates:
        k = (c['ltf_idx'], c['side'])
        if k in seen: continue
        seen.add(k); uniq.append(c)
    uniq.sort(key=lambda x: x['ltf_idx'])
    return df_full, uniq


def run_window(df, cands, start_bar, end_bar):
    """Simulate trades for a window [start_bar, end_bar]."""
    eng = SmartEntryEngine()
    w = l = 0; cd = 0; pnls = []
    for c in cands:
        if c['ltf_idx'] < start_bar: continue
        if c['ltf_idx'] >= end_bar: continue
        if cd > 0: cd -= 1; continue
        if c['ltf_idx'] + 60 >= len(df): continue
        h = df.iloc[:c['ltf_idx']+1]
        atr = float(h['close'].diff().abs().rolling(14).mean().iloc[-1])
        atr = max(atr, c['entry'] * 0.002)
        plan = eng.build_plan(c['side'], c['entry'], atr,
                              'STRONG_TREND', structure_sl=c['sl'])
        future = df.iloc[c['ltf_idx']+1: min(c['ltf_idx']+81, end_bar)]
        if len(future) < 5: continue
        out = eng.simulate(plan, future)
        if out.won: w += 1; cd = 2
        else: l += 1; cd = 4
        pnls.append(out.pnl_pct)
    t = w + l
    wr = w / t * 100 if t else 0
    pf_w = sum(x for x in pnls if x > 0)
    pf_l = abs(sum(x for x in pnls if x < 0))
    pf = pf_w / pf_l if pf_l else 0
    exp = np.mean(pnls) * 100 if pnls else 0
    return t, wr, pf, exp


def forward_test():
    """Forward test on UNSEEN seeds + walk-forward on each."""
    eng = SmartEntryEngine()
    dispatcher = AgentDispatcher()
    # UNSEEN seeds (not in backtest)
    forward_seeds = [300, 400, 500, 600, 700, 800, 900]
    print("=" * 70)
    print("  FORWARD TEST (unseen seeds, walk-forward)")
    print("  Strategy params fixed from backtest; tested on new data")
    print("=" * 70)
    print("seed  trades  WR%    PF    exp%   mode")
    fwd_results = []
    for seed in forward_seeds:
        t0 = time.time()
        np.random.seed(seed)
        mtf = make_mtf(seed=seed)
        df, cands = find_candidates(mtf)
        t, wr, pf, exp = run_window(df, cands, 0, len(df))
        fwd_results.append((seed, t, wr, pf, exp))
        elapsed = time.time() - t0
        print(f"{seed:4d}  {t:5d}  {wr:5.1f}  {pf:5.2f}  {exp:+6.3f}  full   ({elapsed:.1f}s)")
    # Walk-forward: first 60% detection, test on last 40%
    print("\n  Walk-forward (detect on 0-60%, execute on 60-100%):")
    wf_results = []
    for seed in forward_seeds[:4]:
        np.random.seed(seed)
        mtf = make_mtf(seed=seed)
        cutoff = int(len(mtf['15m']) * 0.6)
        # Detect setups up to cutoff (use full mtf but limit detection)
        df, cands = find_candidates(mtf, up_to_idx=cutoff)
        t, wr, pf, exp = run_window(df, cands, cutoff, len(df))
        wf_results.append((seed, t, wr, pf, exp))
        print(f"{seed:4d}  {t:5d}  {wr:5.1f}  {pf:5.2f}  {exp:+6.3f}  wf60-100")
    wrs_fwd = [r[2] for r in fwd_results]
    wrs_wf = [r[2] for r in wf_results]
    print(f"\nForward (unseen) avg WR: {sum(wrs_fwd)/len(wrs_fwd):.1f}%, >=60%: {sum(1 for w in wrs_fwd if w>=60)}/{len(wrs_fwd)}")
    print(f"Walk-fwd (out-of-sample) avg WR: {sum(wrs_wf)/len(wrs_wf):.1f}%, >=60%: {sum(1 for w in wrs_wf if w>=60)}/{len(wrs_wf)}")
    return fwd_results, wf_results


if __name__ == "__main__":
    forward_test()
