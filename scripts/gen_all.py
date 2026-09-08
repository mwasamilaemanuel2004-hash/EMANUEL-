#!/usr/bin/env python3
"""Create all deployment files for ESMH.TRADE"""
import pathlib

ROOT = pathlib.Path(r"C:\Users\DELL YOUR\Desktop\ESMH.TRADE")

def w(path, content):
    fp = ROOT / path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    print(f"OK: {path}")

# render.yaml
w("render.yaml", """\
services:
  - type: web
    name: esmh-trade-api
    runtime: python
    plan: standard
    region: oregon
    buildCommand: pip install -r backend/requirements.txt
    startCommand: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: "false"
      - key: PORT
        value: "8000"
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET
        generateValue: true
      - key: LOG_LEVEL
        value: info
  - type: static
    name: esmh-trade-frontend
    plan: free
    staticPublishPath: ./frontend
    routes:
      - type: rewrite
        source: /api/*
        destination: https://esmh-trade-api.onrender.com/*
databases:
  - name: esmh-trade-db
    plan: standard
    postgresMajorVersion: "16"
  - name: esmh-trade-redis
    plan: standard
""")

# Procfile
w("Procfile", """\
web: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000}
worker: celery -A app.tasks worker --loglevel=info --concurrency=4
beat: celery -A app.tasks beat --loglevel=info
release: echo "Deployment complete"
""")

# app.yaml
w("app.yaml", """\
runtime: python311
entrypoint: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
instance_class: F4_1G
automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.7
env_variables:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "info"
handlers:
  - url: /static
    static_dir: frontend/
    secure: always
  - url: /.*
    script: auto
    secure: always
""")

print("Part 1 done!")
