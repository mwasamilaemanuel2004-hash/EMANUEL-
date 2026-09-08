import os
import sys
import importlib.util

# Ensure the backend directory is on the path so 'app' package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Load ultra.py with proper package context so relative imports resolve
    # without triggering app/api/__init__.py (which pulls in auth/trading/debug
    # and the legacy models package that has pre-existing import gaps).
    spec = importlib.util.spec_from_file_location(
        'app.api.ultra',
        os.path.join('app', 'api', 'ultra.py'),
    )
    m = importlib.util.module_from_spec(spec)
    m.__package__ = 'app.api'       # enable relative imports (..core, ..security)
    sys.modules['app.api.ultra'] = m
    spec.loader.exec_module(m)
    print('ULTRA_API_IMPORT_OK')
except Exception as e:
    print('IMPORT_ERR:', type(e).__name__, e)