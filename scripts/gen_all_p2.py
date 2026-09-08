#!/usr/bin/env python3
"""Create deployment files - Part 2"""
import pathlib

ROOT = pathlib.Path(r"C:\Users\DELL YOUR\Desktop\ESMH.TRADE")

def w(path, content):
    fp = ROOT / path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    print(f"OK: {path}")

# Dockerfile.frontend
w("Dockerfile.frontend", """\
FROM nginx:alpine
COPY scripts/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/ /usr/share/nginx/html/
RUN echo 'server_tokens off;' > /etc/nginx/conf.d/security.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
""")

# .do/deploy.yaml
w(".do/deploy.yaml", """\
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

# scripts/nginx.conf
w("scripts/nginx.conf", """\
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

# scripts/prometheus.yml
w("scripts/prometheus.yml", """\
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: "esmh-backend"
    static_configs:
      - targets: ["backend:8000"]
    metrics_path: /metrics
""")

# .env.example
w(".env.example", """\
ENVIRONMENT=development
DEBUG=true
APP_NAME=ESMH.TRADE
LOG_LEVEL=debug
DATABASE_URL=sqlite:///./data/estrade.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
""")

print("Part 2 done!")
