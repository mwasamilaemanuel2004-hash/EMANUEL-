p = 'backtest_unified.py'
s = open(p).read()
old = """    wins = losses = 0
    pnls = []
    rejects = {}
    sym = "TREND"
    for idx, side, price in signals:
        # use available history only (no look-ahead)
        hist = {k: mtf[k].loc[:df.index[idx]].iloc[-300:] for k in mtf if len(mtf[k].loc[:df.index[idx]]) > 50}
        res = bm.prepare_trade('TrendFollowerBot', side, price, hist, symbol=sym,
                               risk_pct=1.0, spread_pct=0.02, liquidity_ok=True)
        if res is None or res.get('decision') != 'EXECUTE':
            reason = res.get('reason', 'none') if res else 'none'
            rejects[reason] = rejects.get(reason, 0) + 1
            continue
        plan = res['plan']
        future = df.iloc[idx+1: idx+1+200]
        out = bm.entry.simulate(plan, future)
        bm.record_outcome(sym, out.pnl_pct)
        if out.won:
            wins += 1
        else:
            losses += 1
        pnls.append(out.pnl_pct)"""

new = """    wins = losses = 0
    pnls = []
    rejects = {}
    sym = "TREND"
    cooldown = 0
    for idx, side, price in signals:
        if cooldown > 0:
            cooldown -= 1
            if cooldown == 0:
                bm.filter.consecutive_losses = 0
                bm.filter.daily_loss_pct = 0.0
            rejects['cooldown-wait'] = rejects.get('cooldown-wait', 0) + 1
            continue
        # use available history only (no look-ahead)
        hist = {k: mtf[k].loc[:df.index[idx]].iloc[-300:] for k in mtf if len(mtf[k].loc[:df.index[idx]]) > 50}
        res = bm.prepare_trade('TrendFollowerBot', side, price, hist, symbol=sym,
                               risk_pct=1.0, spread_pct=0.02, liquidity_ok=True)
        if res is None or res.get('decision') != 'EXECUTE':
            reason = res.get('reason', 'none') if res else 'none'
            rejects[reason] = rejects.get(reason, 0) + 1
            if 'consecutive-loss' in reason:
                cooldown = 30
            continue
        plan = res['plan']
        future = df.iloc[idx+1: idx+1+200]
        out = bm.entry.simulate(plan, future)
        bm.record_outcome(sym, out.pnl_pct)
        if out.won:
            wins += 1
        else:
            losses += 1
        pnls.append(out.pnl_pct)"""

assert old in s, "loop block not found"
s = s.replace(old, new)
open(p, 'w').write(s)
print("cooldown fix applied:", s.count("cooldown = 30"))
