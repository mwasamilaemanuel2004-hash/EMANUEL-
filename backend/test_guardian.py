import sys
sys.path.insert(0, 'backend')
from app.security.ai_guardian import ai_guardian

# Test normal request
r1 = ai_guardian.protect_request({'ip': '1.2.3.4', 'endpoint': '/api/prices', 'query': 'BTC'})
print('NORMAL:', r1['allowed'], r1['action'])

# Test SQL injection
r2 = ai_guardian.protect_request({'ip': '1.2.3.5', 'endpoint': '/api/login', 'query': "' OR '1'='1"})
print('SQL_INJECT:', r2['allowed'], r2['action'], r2['reason'])

# Test XSS
r3 = ai_guardian.protect_request({'ip': '1.2.3.6', 'endpoint': '/api/search', 'query': '<script>alert(1)</script>'})
print('XSS:', r3['allowed'], r3['action'], r3['reason'])

# Test rate limit
ok = True
for i in range(10):
    ok = ai_guardian.protect_request({'ip': '4.4.4.4', 'endpoint': '/api/login'})['allowed']
print('RATE_LIMIT after 10 logins:', ok)

print('STATUS:', ai_guardian.get_status())
print('GUARDIAN TEST PASSED')