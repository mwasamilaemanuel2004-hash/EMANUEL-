#!/usr/bin/env python3
"""ESMH.TRADE - Part 3a: docker-compose.prod.yml + .env.example"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def write(path, content):
    fp = ROOT / path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    print(f"  OK: {path}")

def main():
    write("docker-compose.prod.yml", """\
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: esmh-backend-prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://esmh:esmh_pass@postgres:5432/esmh_trade
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
    restart: always
    networks: [esmh-prod]

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: esmh-frontend-prod
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
    networks: [esmh-prod]

  postgres:
    image: postgres:16-alpine
    container_name: esmh-postgres-prod
    environment:
      - POSTGRES_USER=esmh
      - POSTGRES_PASSWORD=esmh_pass
      - POSTGRES_DB=esmh_trade
    volumes: [pgdata_prod:/var/lib/postgresql/data]
    restart: always
    networks: [esmh-prod]

  redis:
    image: redis:7-alpine
    container_name: esmh-redis-prod
    command: redis-server --appendonly yes
    volumes: [redisdata_prod:/data]
    restart: always
    networks: [esmh-prod]

volumes:
  pgdata_prod:
  redisdata_prod:

networks:
  esmh-prod:
    driver: bridge
""")

    write(".env.example", """\
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

    print("Part 3a done")

if __name__ == "__main__":
    main()
