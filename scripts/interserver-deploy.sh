#!/bin/bash
set -euo pipefail
echo "=== ESMH.TRADE - InterServer VPS Deployment ==="
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip postgresql redis-server apache2 curl
DB_PASS=$(openssl rand -hex 16)
sudo -u postgres psql -c "CREATE USER esmh WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE esmh_trade OWNER esmh;" 2>/dev/null || true
mkdir -p /home/esmhtrade/esmh-backend && cd /home/esmhtrade/esmh-backend
git clone https://github.com/mwasamilaemanuel2004-hash/EMANUEL- . 2>/dev/null || true
python3.11 -m venv venv && source venv/bin/activate
pip install --upgrade pip && pip install -r backend/requirements.txt
cp -r frontend/* /home/esmhtrade/public_html/ 2>/dev/null || true
cat > /etc/apache2/sites-available/esmh.conf << 'APCH'
<VirtualHost *:80>
    DocumentRoot /home/esmhtrade/public_html
    <Directory /home/esmhtrade/public_html>
        AllowOverride All
        Require all granted
    </Directory>
    ProxyPass /api http://127.0.0.1:8000/api
    ProxyPassReverse /api http://127.0.0.1:8000/api
</VirtualHost>
APCH
a2ensite esmh.conf && a2enmod proxy proxy_http rewrite
systemctl restart apache2
cat > /etc/systemd/system/esmh-trade.service << SVCEOF
[Unit]
Description=ESMH.TRADE Backend
After=network.target postgresql.service redis.service
[Service]
Type=simple
WorkingDirectory=/home/esmhtrade/esmh-backend
EnvironmentFile=/home/esmhtrade/esmh-backend/.env
ExecStart=/home/esmhtrade/esmh-backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SVCEOF
cat > /home/esmhtrade/esmh-backend/.env << ENVEOF
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
