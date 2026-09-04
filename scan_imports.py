import os, re, sys

roots = ["backend/app", "backend/core", "backend/layerz", "data/models"]
heavy = ["tensorflow","torch","transformers","sentence_transformers","xgboost","lightgbm",
         "numba","ta","talib","sklearn","scikit","celery","redis","elasticsearch","MetaTrader5",
         "mt5","ccxt","yfinance","websockets","aiosmtplib","passlib","jose","jwt","cryptography",
         "pyotp","qrcode","supabase","google","openai","anthropic","pandas","numpy","scipy",
         "asyncpg","psycopg2","aiosqlite","sqlalchemy","boto3"]

found = {}
for r in roots:
    if not os.path.isdir(r):
        continue
    for dirpath, _, files in os.walk(r):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        m = re.match(r"\s*(?:import|from)\s+([A-Za-z0-9_\.]+)", line)
                        if m:
                            mod = m.group(1).split(".")[0]
                            if mod in heavy:
                                found.setdefault(mod, set()).add(p)
            except Exception:
                continue

for mod in sorted(found):
    files = sorted(found[mod])
    print(f"{mod}: {len(files)} file(s)")
