p = 'backend/app/core/sm_engine.py'
s = open(p).read()
s = s.replace("                if not _choch_confirmed(df, eb, 'SELL'):\n                    continue\n", "")
s = s.replace("                if not _choch_confirmed(df, eb, 'BUY'):\n                    continue\n", "")
open(p, 'w').write(s)
print('CHoCH removed, remaining:', s.count('_choch_confirmed'))
