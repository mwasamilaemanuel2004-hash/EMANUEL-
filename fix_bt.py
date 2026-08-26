p = 'backtest_unified.py'
s = open(p).read()
s = s.replace(
    "        entry_mtf = {k: mtf[k].loc[:df.index[idx]] for k in mtf if mtf[k].index[-1] <= df.index[idx]}\n        # use available history only (no look-ahead)\n        hist = {k: v.iloc[-300:] for k, v in entry_mtf.items()}",
    "        # use available history only (no look-ahead)\n        hist = {k: mtf[k].loc[:df.index[idx]].iloc[-300:] for k in mtf if len(mtf[k].loc[:df.index[idx]]) > 50}"
)
open(p, 'w').write(s)
print("backtest history fix:", s.count("mtf[k].loc[:df.index[idx]].iloc[-300:]"))
