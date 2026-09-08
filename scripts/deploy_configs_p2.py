#!/usr/bin/env python3
"""ESMH.TRADE - Generate all deployment configuration files - Part 2."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def write(path, content):
    fp = ROOT / path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    print(f"  OK: {path}")

def main():
    print("Generating ESMH.TRADE deployment files (Part 2)...")

    # === app.yaml (Google App Engine) ===
    write("app.yaml", """\
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

    # === Dockerfile.frontend ===
    write("Dockerfile.frontend", """\
FROM nginx:alpine

COPY scripts/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/ /usr/share/nginx/html/

RUN echo 'server_tokens off;' > /etc/nginx/conf.d/security.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
""")

    # === .do/deploy.yaml (DigitalOcean) ===
    write(".do/deploy.yaml", """\
name: esmh-trade
region: nyc

services:
  - name: backend
    source_dir: /
    github:
      repo: mwasamilaemanuel2004-hash/EMANUEL-
      branch: main
      deploy_on_push: true
    run_command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080
    environment_slug: python
    instance_count: 2
    instance_size_slug: professional-xs
    health_check:
      http_path: /health
      port: 8080
    http_port: 8080
    envs:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
      - key: SECRET_KEY
        generate: true

databases:
  - name: db
    engine: PG
    version: "16"
""")

    # === scripts/nginx.conf ===
    write("scripts/nginx.conf", """\
server {
    listen 80;
    server_name localhost;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://backend:8000/health;
    }
}
""")

    # === scripts/prometheus.yml ===
    write("scripts/prometheus.yml", """\
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "esmh-backend"
    static_configs:
      - targets: ["backend:8000"]
    metrics_path: /metrics
""")

    print("Part 2 done: app.yaml, Dockerfile.frontend, .do/deploy.yaml, nginx.conf, prometheus.yml")

if __name__ == "__main__":
    main()
