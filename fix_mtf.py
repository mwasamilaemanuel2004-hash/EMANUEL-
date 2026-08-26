# Patch master_trade_filter.py
p = 'backend/app/core/master_trade_filter.py'
s = open(p).read()
s = s.replace(
    "            # Use the finest timeframe available for scoring\n            score_data = mtf_data.get('1h') or mtf_data.get('15m') or next(iter(mtf_data.values()))",
    "            # Use the finest timeframe available for scoring\n            score_data = mtf_data.get('1h')\n            if score_data is None:\n                score_data = mtf_data.get('15m')\n            if score_data is None:\n                score_data = next(iter(mtf_data.values()))"
)
s = s.replace(
    "            atr = self.ai._calc_atr(\n                mtf_data.get('1h') or next(iter(mtf_data.values()))).iloc[-1]",
    "            _sd = mtf_data.get('1h')\n            if _sd is None:\n                _sd = next(iter(mtf_data.values()))\n            atr = self.ai._calc_atr(_sd).iloc[-1]"
)
open(p, 'w').write(s)

# Patch bot_manager.py
p2 = 'backend/app/core/bot_manager.py'
t = open(p2).read()
t = t.replace(
    "            atr = self.filter.ai._calc_atr(\n                mtf_data.get('1h') or next(iter(mtf_data.values()))).iloc[-1]",
    "            _sd = mtf_data.get('1h')\n            if _sd is None:\n                _sd = next(iter(mtf_data.values()))\n            atr = self.filter.ai._calc_atr(_sd).iloc[-1]"
)
open(p2, 'w').write(t)
print('patched mtf:', s.count("score_data is None"), '| bot_manager:', t.count("_sd = mtf_data.get('1h')"))
