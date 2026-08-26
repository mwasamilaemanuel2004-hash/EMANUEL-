p = 'backend/app/core/smart_entry.py'
s = open(p).read()

# Fix BUY exit reason label
s = s.replace(
    '                    res.exit_reason = "stop" if locked_sl > entry else "breakeven"',
    '                    res.exit_reason = "breakeven" if abs(locked_sl - entry) < 1e-9 else "stop"'
)
# Fix SELL exit reason label
s = s.replace(
    '                    res.exit_reason = "stop" if locked_sl < entry else "breakeven"',
    '                    res.exit_reason = "breakeven" if abs(locked_sl - entry) < 1e-9 else "stop"'
)
open(p, 'w').write(s)
print("label fixes applied:", s.count('abs(locked_sl - entry) < 1e-9'))
