"""
TokenizationBot backtest — verifies the tokenization analysis + smart entry
produces signals on sample data and that the smart entry generates positive
expectancy.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
import numpy as np
import pandas as pd
import asyncio
from loguru import logger
logger.remove(); logger.add(lambda _: None, level="CRITICAL")

from app.bots.crypto.tokenization_bot import TokenizationBot
from app.core.smart_entry import SmartEntryEngine


def make_data(periods=1000, seed=21):
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
    return df


async def get_signal(bot, df_window):
    try:
        result = bot.analyze_market(df_window)
        if hasattr(result, '__await__'):
            result = await result
        return result
    except Exception:
        return None


def main():
    eng = SmartEntryEngine()
    print("seed  signals  trades  WR%    PF    exp%   notes")
    for seed in [7, 21, 42, 99, 200, 300, 500]:
        t0 = time.time()
        np.random.seed(seed)
        df = make_data(seed=seed)
        bot = TokenizationBot({'bot_id': 'BTC', 'parameters': {}})
        # Run async
        async def collect():
            sigs = 0
            for i in range(50, len(df) - 40, 20):
                window = df.iloc[:i + 1]
                sig = await get_signal(bot, window)
                if sig is not None and getattr(sig, 'entry_price', None):
                    sigs += 1
            return sigs
        signals = asyncio.run(collect())

        # Simulate: for each signal-like point, run smart entry
        w = l = 0; cd = 0; pnls = []
        async def simulate():
            nonlocal w, l, cd, pnls
            for i in range(50, len(df) - 40, 20):
                window = df.iloc[:i + 1]
                sig = await get_signal(bot, window)
                if sig is None: continue
                entry = float(sig.entry_price); sl = float(sig.stop_loss)
                if not entry or not sl or sl == entry: continue
                side = sig.action if sig.action in ('BUY','SELL') else 'BUY'
                atr = float(window['close'].diff().abs().rolling(14).mean().iloc[-1])
                atr = max(atr, entry * 0.002)
                plan = eng.build_plan(side, entry, atr, 'STRONG_TREND', structure_sl=sl)
                future = df.iloc[i+1: i+1+60]
                if len(future) < 5: continue
                out = eng.simulate(plan, future)
                if out.won: w += 1; cd = 2
                else: l += 1; cd = 4
                pnls.append(out.pnl_pct)
        asyncio.run(simulate())
        t = w + l
        wr = w / t * 100 if t else 0
        pf_w = sum(x for x in pnls if x > 0)
        pf_l = abs(sum(x for x in pnls if x < 0))
        pf = pf_w / pf_l if pf_l else 0
        exp = np.mean(pnls) * 100 if pnls else 0
        elapsed = time.time() - t0
        print(f"{seed:4d}  {signals:6d}  {t:5d}  {wr:5.1f}  {pf:5.2f}  {exp:+6.3f}  ({elapsed:.1f}s)")
    print("DONE")


if __name__ == "__main__":
    main()
