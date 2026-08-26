p = 'backend/app/core/profit_optimizer.py'
s = open(p).read()

old1 = '    regime = "STRONG_TREND" if c.token_score > 70 else "WEAK_TREND"\n    session = "LONDON"  # placeholder; in production use real session'
new1 = '    regime = "STRONG_TREND" if c.token_score > 70 else "WEAK_TREND"\n    session = "LONDON"'
assert old1 in s, 'old1 not found'
s = s.replace(old1, new1)

old2 = (
    '    for agent_name in dispatcher.contexts:\n'
    '        res = dispatcher.dispatch(agent_name, regime, session, c.symbol,\n'
    '                                  base_confidence=70.0)\n'
    '        if res.accepted and res.adjusted_confidence > best_conf:\n'
    '            best_bot = agent_name; best_conf = res.adjusted_confidence\n'
    '    if best_bot is None:\n'
    '        return None\n'
    '    # Determine side from trend\n'
    '    side = "BUY" if c.trend_30d > 0 else "SELL"'
)
new2 = (
    '    import pandas as pd\n'
    '    fake_ts = pd.Timestamp.now(tz="UTC")\n'
    '    for agent_name in dispatcher.contexts:\n'
    '        res = dispatcher.dispatch(agent_name, regime, fake_ts, c.symbol,\n'
    '                                  base_confidence=70.0)\n'
    '        if res.accepted and res.adjusted_confidence > best_conf:\n'
    '            best_bot = agent_name; best_conf = res.adjusted_confidence\n'
    '    if best_bot is None:\n'
    '        return None\n'
    '    side = "BUY" if c.trend_30d > 0 else "SELL"'
)
assert old2 in s, 'old2 not found'
s = s.replace(old2, new2)

old3 = (
    '    for agent_name in dispatcher.contexts:\n'
    '        res = dispatcher.dispatch(agent_name, regime, session, m.symbol,\n'
    '                                  base_confidence=70.0)'
)
new3 = (
    '    import pandas as pd\n'
    '    fake_ts = pd.Timestamp.now(tz="UTC")\n'
    '    for agent_name in dispatcher.contexts:\n'
    '        res = dispatcher.dispatch(agent_name, regime, fake_ts, m.symbol,\n'
    '                                  base_confidence=70.0)'
)
assert old3 in s, 'old3 not found'
s = s.replace(old3, new3)

open(p, 'w').write(s)
print('profit_optimizer fixed')
