"""Per-bot backtest — runs entirely inside an event loop for bots that need it."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd
import asyncio
from loguru import logger
logger.remove(); logger.add(lambda _: None, level="CRITICAL")

from app.core.smart_entry import SmartEntryEngine
from app.core.news_filter import NewsFilter, is_near_known_event
from app.core.market_microstructure import premium_discount_zone


def make_data(periods=1000, seed=21, mode='trend'):
    np.random.seed(seed)
    dates = pd.date_range(end='now', periods=periods, freq='1h', tz='UTC')
    if mode == 'trend':
        seg = periods // 6
        drifts = [0.0006, -0.0006, 0.0005, -0.0005, 0.0007, -0.0007]
        rets = np.zeros(periods)
        for i in range(periods):
            s = min(i // seg, len(drifts) - 1)
            rets[i] = drifts[s] + np.random.normal(0, 0.0025)
        close = 100 * np.exp(np.cumsum(rets))
    elif mode == 'range':
        t = np.arange(periods)
        close = 100 + 14 * np.sin(t / 30) + 7 * np.sin(t / 9) + np.random.normal(0, 0.8, periods)
    else:
        close = 100 * np.exp(np.cumsum(np.random.normal(0, 0.02, periods)))
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


async def _analyze(bot, df_window):
    """Safely call bot.analyze_market inside the running loop."""
    try:
        result = bot.analyze_market(df_window)
        if hasattr(result, '__await__'):
            result = await result
        return result
    except Exception:
        return None


async def backtest_bot_async(bot, df, bot_name, market="forex", horizon=40, step=10):
    eng = SmartEntryEngine()
    nf = NewsFilter()
    wins = losses = 0
    pnls = []
    rejects = 0
    for i in range(100, len(df) - horizon, step):
        window = df.iloc[:i + 1]
        ts = df.index[i]
        allowed, _, _ = nf.check(ts, market=market)
        if not allowed:
            rejects += 1; continue
        near, _ = is_near_known_event(ts)
        if near:
            rejects += 1; continue
        sig = await _analyze(bot, window)
        if sig is None:
            continue
        entry = float(sig.entry_price); sl = float(sig.stop_loss); tp = float(sig.take_profit)
        if not entry or not sl or sl == entry or entry <= 0:
            continue
        side = sig.action if sig.action in ("BUY", "SELL") else "BUY"
        atr = float(window['close'].diff().abs().rolling(14).mean().iloc[-1])
        atr = max(atr, entry * 0.002)
        zone = premium_discount_zone(window, lookback=50, current_idx=i)
        risk_pct = 1.0
        if side == "BUY" and zone == "PREMIUM": risk_pct = 0.5
        if side == "SELL" and zone == "DISCOUNT": risk_pct = 0.5
        plan = eng.build_plan(side, entry, atr, regime="STRONG_TREND", structure_sl=sl)
        future = df.iloc[i + 1: i + 1 + horizon]
        out = eng.simulate(plan, future)
        out.pnl_pct *= risk_pct
        if out.won: wins += 1
        else: losses += 1
        pnls.append(out.pnl_pct)
    total = wins + losses
    if total == 0:
        return {'bot': bot_name, 'trades': 0, 'wr': 0.0, 'pf': 0.0,
                'exp': 0.0, 'aw': 0.0, 'al': 0.0, 'rejects': rejects}
    wr = wins / total * 100
    gw = sum(x for x in pnls if x > 0)
    gl = abs(sum(x for x in pnls if x < 0))
    pf = gw / gl if gl else 0.0
    aw = np.mean([x for x in pnls if x > 0]) * 100 if wins else 0.0
    al = np.mean([x for x in pnls if x < 0]) * 100 if losses else 0.0
    exp = np.mean(pnls) * 100
    return {'bot': bot_name, 'trades': total, 'wr': wr, 'pf': pf,
            'exp': exp, 'aw': aw, 'al': al, 'rejects': rejects}


async def count_signals_async(bot, df, step=10):
    n = 0
    for i in range(100, len(df) - 40, step):
        window = df.iloc[:i + 1]
        sig = await _analyze(bot, window)
        if sig is not None and getattr(sig, 'entry_price', None):
            n += 1
    return n


def main():
    from app.bots import (
        TrendFollowerBot, ForexScalperBot, SmartMoneyBot, BreakoutBot, NewsBot,
        ArbitrageBot, CryptoScalperBot, DcaBot, GridBot, WhaleBot,
        AIStockAnalyzerBot, MetalsBot, CommoditiesBot,
    )
    bots = [
        ("TrendFollowerBot",    TrendFollowerBot,   "trend"),
        ("ForexScalperBot",     ForexScalperBot,    "volatile"),
        ("SmartMoneyBot",       SmartMoneyBot,      "trend"),
        ("BreakoutBot",         BreakoutBot,        "volatile"),
        ("NewsBot",             NewsBot,            "trend"),
        ("ArbitrageBot",        ArbitrageBot,       "volatile"),
        ("CryptoScalperBot",    CryptoScalperBot,   "volatile"),
        ("DcaBot",              DcaBot,             "trend"),
        ("GridBot",             GridBot,            "range"),
        ("WhaleBot",            WhaleBot,           "trend"),
        ("AIStockAnalyzerBot",  AIStockAnalyzerBot, "trend"),
        ("MetalsBot",           MetalsBot,          "trend"),
        ("CommoditiesBot",      CommoditiesBot,     "trend"),
    ]

    async def run_all():
        results = []
        for name, cls, mode in bots:
            try:
                df = make_data(periods=1000, seed=21, mode=mode)
                bot = cls({'bot_id': name, 'parameters': {}})
                n = await count_signals_async(bot, df, step=8)
                r = await backtest_bot_async(bot, df, name, market="forex")
                results.append((name, mode, n, r))
            except Exception as e:
                results.append((name, mode, 0, {'bot':name,'trades':0,'wr':0,'pf':0,'exp':0,'aw':0,'al':0,'rejects':0,'error':str(e)[:40]}))
        return results

    results = asyncio.run(run_all())

    print("=" * 78)
    print("  PER-BOT BACKTEST (all 13 bots, one by one)")
    print("  Shared: SmartEntryEngine (mandatory SL, breakeven@1R, UNLIMITED runner)")
    print("  Filters: News (NFP/FOMC/CPI), Premium/Discount zones, ATR-based risk")
    print("=" * 78)
    print(f"  {'Bot':22s} {'Mode':>10s} {'Sig':>5s} {'Trd':>5s} {'WR%':>6s} {'PF':>6s} {'Exp%':>7s}")
    print("-" * 78)
    for name, mode, n, r in results:
        err = r.get('error','')
        if err:
            print(f"  {name:22s} {mode:>10s} {n:5d} {r['trades']:5d}  ERR: {err}")
        else:
            print(f"  {name:22s} {mode:>10s} {n:5d} {r['trades']:5d} {r['wr']:6.1f} {r['pf']:6.2f} {r['exp']:+7.3f}")
        sys.stdout.flush()
    print("=" * 78)


if __name__ == "__main__":
    main()
