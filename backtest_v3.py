"""
Combined Backtest v3 — PRESERVES v2 baseline exactly.
v3 adds BotContext, AgentDispatcher, ProfitEnhancer, Multi-Confluence as
TRACKING/METADATA modules (no filtering). v2 execution is unchanged.
Run multiple times to see variance; v3 should match v2 ± noise.
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


def find_candidates(mtf):
    """EXACT same as v2."""
    df = mtf['15m']
    sm_setups = detect_sm_setups(df, hold_bars=2)
    crt = detect_crt(df, mtf['4h'], lookback_htf=3)
    candidates = []
    for s in sm_setups:
        if s.ltf_idx + 60 >= len(df): continue
        ts = df.index[s.ltf_idx]
        if session_multiplier(ts) < 0.5: continue
        t4 = htf_soft_trend(mtf['4h'], ts)
        want = 1 if s.side == 'BUY' else -1
        if t4 != 0 and t4 != want: continue
        candidates.append({'ltf_idx': s.ltf_idx, 'side': s.side,
                           'entry': s.entry, 'sl': s.sl, 'reason': s.reason,
                           'sm_setup': s})
    for c in crt:
        if c.choch_index + 60 >= len(df): continue
        ts = df.index[c.choch_index]
        if session_multiplier(ts) < 0.5: continue
        t4 = htf_soft_trend(mtf['4h'], ts)
        want = 1 if c.direction == 'BUY' else -1
        if t4 != 0 and t4 != want: continue
        candidates.append({'ltf_idx': c.choch_index, 'side': c.direction,
                           'entry': c.ltf_entry, 'sl': c.invalidation,
                           'reason': f"CRT {c.direction}", 'sm_setup': None})
    seen = set(); uniq = []
    for c in candidates:
        k = (c['ltf_idx'], c['side'])
        if k in seen: continue
        seen.add(k); uniq.append(c)
    uniq.sort(key=lambda x: x['ltf_idx'])
    return df, uniq


def run():
    """v3: EXACT v2 execution. v3 modules are tracking/metadata only."""
    eng = SmartEntryEngine()
    dispatcher = AgentDispatcher()
    enhancer = ProfitEnhancer()
    print("seed  trades  WR%    PF    exp%")
    all_results = []
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
            # v3 modules: track best-fit agent + multi-confluence (no filter)
            ts = df.index[c['ltf_idx']]
            for agent_name in dispatcher.contexts:
                dispatcher.dispatch(agent_name, "STRONG_TREND", ts,
                                    "EURUSD", base_confidence=75.0)
            if c.get('sm_setup') is not None:
                _ = enhance_setup_confluence(c['sm_setup'], df)
            # EXACT v2 plan + simulate
            plan = eng.build_plan(c['side'], c['entry'], atr,
                                  'STRONG_TREND', structure_sl=c['sl'])
            future = df.iloc[c['ltf_idx']+1: c['ltf_idx']+81]
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
        elapsed = time.time() - t0
        all_results.append((seed, t, wr, pf, exp))
        print(f"{seed:4d}  {t:5d}  {wr:5.1f}  {pf:5.2f}  {exp:+6.3f}  ({elapsed:.1f}s)")
    wrs = [r[2] for r in all_results]
    print(f"\nAvg WR: {sum(wrs)/len(wrs):.1f}%, Seeds >=60%: {sum(1 for w in wrs if w>=60)}/{len(wrs)}")
    return all_results


if __name__ == "__main__":
    run()
