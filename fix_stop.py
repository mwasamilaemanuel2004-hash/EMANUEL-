p = 'backend/app/core/backtest_engine.py'
s = open(p).read()
count = s.count('stop_distance = current["atr"] * 1.5')
s = s.replace('stop_distance = current["atr"] * 1.5', 'stop_distance = current["atr"] * 1.0')
open(p, 'w').write(s)
print('replaced', count, 'occurrences -> ATR*1.0')
