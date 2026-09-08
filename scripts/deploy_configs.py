#!/usr/bin/env python3
"""ESMH.TRADE - Generate all deployment configuration files."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def write(path, content):
    fp = ROOT / path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    print(f"  OK: {path}")

def main():
    print("Generating ESMH.TRADE deployment files...")

    # === pyproject.toml ===
    write("pyproject.toml", """\
[project]
name = "esmh-trade"
version = "4.0.0"
description = "ESMH.TRADE - AI-Powered Trading Platform"
authors = ["ESMH Team"]
license = "MIT"
readme = "README.md"
requires-python = ">=3.11"
keywords = ["trading", "ai", "crypto", "forex", "fastapi"]

[project.urls]
Homepage = "https://eshtrade.com"
Documentation = "https://docs.eshtrade.com"
Repository = "https://github.com/mwasamilaemanuel2004-hash/EMANUEL-"

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["backend"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=backend --cov-report=html"

[tool.coverage.run]
source = ["backend"]
omit = ["tests/*", "*/migrations/*"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]
""")

    # === render.yaml ===
    write("render.yaml", """\
services:
  - type: web
    name: esmh-trade-api
    runtime: python
    plan: standard
    region: oregon
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000"
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: "false"
      - key: PORT
        value: "8000"
      - key: DATABASE_URL
        fromDatabase:
          name: esmh-trade-db
          property: connectionString
      - key: REDIS_URL
        fromRedis:
          name: esmh-trade-redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET
        generateValue: true

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

    # === Procfile ===
    write("Procfile", """\
web: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000}
worker: celery -A app.tasks worker --loglevel=info --concurrency=4
beat: celery -A app.tasks beat --loglevel=info
release: echo "Deployment complete"
""")

    print("Part 1 done: pyproject.toml, render.yaml, Procfile")

if __name__ == "__main__":
    main()
