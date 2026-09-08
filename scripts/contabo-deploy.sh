#!/bin/bash
set -euo pipefail
echo "=== ESMH.TRADE - Contabo VPS Deployment ==="
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip postgresql redis-server nginx curl
DB_PASS=$(openssl rand -hex 16)
sudo -u postgres psql -c "CREATE USER esmh WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE esmh_trade OWNER esmh;" 2>/dev/null || true
mkdir -p /opt/esmh-trade && cd /opt/esmh-trade
git clone https://github.com/mwasamilaemanuel2004-hash/EMANUEL- . 2>/dev/null || true
python3.11 -m venv venv && source venv/bin/activate
pip install --upgrade pip && pip install -r backend/requirements.txt
cat > /etc/nginx/sites-available/esmh << 'NGX'
server {
    listen 80;
    server_name _;
    location / { root /opt/esmh-trade/frontend; try_files $uri $uri/ /index.html; }
    location /api/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; }
}
NGX
ln -sf /etc/nginx/sites-available/esmh /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
cat > /etc/systemd/system/esmh-trade.service << SVCEOF
[Unit]
Description=ESMH.TRADE Backend
After=network.target postgresql.service redis.service
[Service]
Type=simple
WorkingDirectory=/opt/esmh-trade
EnvironmentFile=/opt/esmh-trade/.env
ExecStart=/opt/esmh-trade/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SVCEOF
cat > /opt/esmh-trade/.env << ENVEOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://esmh:${DB_PASS}@localhost:5432/esmh_trade
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
LOG_LEVEL=info
ENVEOF
systemctl daemon-reload && systemctl enable --now esmh-trade
echo "=== Deployment Complete! DB password: $DB_PASS ==="
