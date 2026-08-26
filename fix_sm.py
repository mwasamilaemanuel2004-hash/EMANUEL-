p = 'backend/app/core/sm_engine.py'
s = open(p).read()
old = "if abs(oi - eb) > 20 and ob['side'] == side:"
new = "if abs(oi - eb) <= 20 and ob['side'] == side:"
assert old in s, 'pattern not found'
s = s.replace(old, new)
open(p, 'w').write(s)
print('fixed:', s.count('abs(oi - eb) <= 20'))
