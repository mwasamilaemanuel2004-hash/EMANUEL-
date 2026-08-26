p = 'backend/app/core/smart_entry.py'
s = open(p, encoding='utf-8').read()
s = s.replace('risk = max(atr * 1.2, entry * 0.002)', 'risk = max(atr, entry * 0.002)')

old = (
    '        rr = {  # multiplier of risk for each target, by regime\n'
    '            "STRONG_TREND": (2.0, 3.5, 6.0),\n'
    '            "WEAK_TREND":   (1.8, 2.8, 4.5),\n'
    '            "RANGE":        (1.5, 2.2, 3.0),\n'
    '            "HIGH_VOLATILITY": (2.5, 4.0, 7.0),\n'
    '            "LOW_VOLATILITY": (1.5, 2.0, 3.0),\n'
    '            "UNSAFE": (1.0, 1.0, 1.0),\n'
    '        }.get(regime, (2.0, 3.0, 4.0))'
)
new = (
    '        rr = {  # (m1=breakeven trigger @1R, m2=trade R:R target, mr=runner) by regime\n'
    '            "STRONG_TREND":   (1.0, 2.5, 4.5),\n'
    '            "WEAK_TREND":     (1.0, 2.2, 3.5),\n'
    '            "RANGE":          (1.0, 2.0, 3.0),\n'
    '            "HIGH_VOLATILITY":(1.0, 3.0, 5.0),\n'
    '            "LOW_VOLATILITY": (1.0, 2.0, 3.0),\n'
    '            "UNSAFE":         (1.0, 1.0, 1.0),\n'
    '        }.get(regime, (1.0, 2.5, 4.0))'
)
assert old in s, 'rr dict block not found'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('FIXED risk=atr:', 'risk = max(atr, entry * 0.002)' in s, '| m1=1.0:', '(1.0, 2.5, 4.5)' in s)
