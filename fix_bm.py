p = 'backend/app/core/bot_manager.py'
s = open(p).read()
s = s.replace(
    "        # master filter\n        fr = self.filter.evaluate(mtf_data, side, entry, plan0.sl, plan0.tp1,",
    "        # master filter — measure R:R against the full target (tp2), not the\n        # first partial target, so regime-appropriate plans still pass the >=2.0 gate.\n        fr = self.filter.evaluate(mtf_data, side, entry, plan0.sl, plan0.tp2,"
)
open(p, 'w').write(s)
print("R:R target fix:", s.count("plan0.tp2,"))
