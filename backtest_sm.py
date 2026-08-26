"""
Comprehensive Smart Money + CRT + TBS backtest.
Uses: SmartEntryEngine (breakeven@1R), CRT setups, session filter.
Goal: prove the upgraded system achieves >=60% win rate.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
import numpy as np
import pandas as pd
from loguru import logger
logger.remove(); logger.add(lambda _: None, level="CRITICAL")

from app.core.smart_entry import SmartEntryEngine, SmartPlan
from app.core.crt_engine import detect_crt
from app.core.tbs_engine import session_multiplier


def make_mtf(periods=2400, seed=21):
    """Trending OHLCV with realistic swing structure (so CRT has setups)."""
    np.random.seed(seed)
    dates = pd.date_range(end='now', periods=periods, freq='1h', tz='UTC')
    seg = periods // 6
    drifts = [0.0006, -0.0006, 0.0005, -0.0005, 0.0007, -0.0007]
    rets = np.zeros(periods)
    for i in range(periods):
        s = min(i // seg, len(drifts)-1)
        rets[i] = drifts[s] + np.random.normal(0, 0.004)
    close = 100 * np.exp(np.cumsum(rets))
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.002, 0.002, periods)),
        'high': close * (1 + np.random.uniform(0, 0.006, periods)),
        'low':  close * (1 - np.random.uniform(0, 0.006, periods)),
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


def find_setups(mtf):
    """Find CRT setups with session timing and build candidate entries."""
    df_ltf = mtf['15m']
    df_htf = mtf['4h']
    setups = detect_crt(df_ltf, df_htf, lookback_htf=5)

    candidates = []
    for s in setups:
        # Map back to LTF index for the entry
        try:
            ltf_idx = df_ltf.index.get_loc(df_ltf.index[s.choch_index])
        except Exception:
            continue
        if ltf_idx + 60 >= len(df_ltf):
            continue
        ts = df_ltf.index[ltf_idx]
        # Skip if not in a good session
        mult = session_multiplier(ts)
        if mult < 0.5:
            continue
        candidates.append({
            'ltf_idx': ltf_idx,
            'side': s.direction,
            'entry': s.ltf_entry,
            'sl': s.invalidation,
            'tp1': s.midpoint,
            'rr': s.rr,
            'conf': s.confidence * mult,
            'reason': f"CRT {s.direction} sweep@{s.sweep_level:.2f} mid={s.midpoint:.2f}",
        })
    return df_ltf, candidates


def run():
    eng = SmartEntryEngine()
    mtf = make_mtf()
    df, candidates = find_setups(mtf)
    print(f"Found {len(candidates)} CRT setups in good session windows")

    wins = losses = 0
    pnls = []
    for c in candidates:
        entry = c['entry']
        side = c['side']
        # ATR for the plan
        hist = df.iloc[:c['ltf_idx']+1]
        atr = float(hist['close'].diff().abs().rolling(14).mean().iloc[-1])
        atr = max(atr, entry * 0.002)
        plan = eng.build_plan(side, entry, atr, regime='STRONG_TREND',
                              structure_sl=c['sl'])
        future = df.iloc[c['ltf_idx']+1: c['ltf_idx']+1+100]
        out = eng.simulate(plan, future)
        if out.won:
            wins += 1
        else:
            losses += 1
        pnls.append(out.pnl_pct)

    total = wins + losses
    wr = wins / total * 100 if total else 0
    gross_w = sum(p for p in pnls if p > 0)
    gross_l = abs(sum(p for p in pnls if p < 0))
    pf = gross_w / gross_l if gross_l else 0
    exp = np.mean(pnls) if pnls else 0
    print("=" * 65)
    print("  SMART MONEY + CRT + TBS BACKTEST")
    print("=" * 65)
    print(f"  Executed trades : {total}")
    print(f"  Win Rate        : {wr:.1f}%   (TARGET >= 60%)")
    print(f"  Profit Factor   : {pf:.2f}")
    print(f"  Expectancy      : {exp*100:.2f}% per trade")
    if pnls:
        aw = np.mean([p for p in pnls if p > 0]) * 100
        al = np.mean([p for p in pnls if p < 0]) * 100
        print(f"  Avg Win / Loss  : {aw:.2f}% / {al:.2f}%")
    print("=" * 65)
    print("  RESULT:", "ACHIEVED 60%+" if wr >= 60 else f"NEED TUNING")


if __name__ == "__main__":
    run()
