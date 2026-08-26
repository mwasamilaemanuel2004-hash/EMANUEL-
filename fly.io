# ============ DEPLOY TO DIFFERENT ENVIRONMENTS ============

# Development
fly deploy --config fly.dev.toml --app eshtrade-dev

# Staging
fly deploy --config fly.staging.toml --app eshtrade-staging

# Production
fly deploy --config fly.toml --app eshtrade

# ============ SCALING COMMANDS ============

# Scale up (Production)
fly scale count 5
fly scale memory 8192
fly scale vm performance-4x

# Scale down (Development)
fly scale count 1
fly scale memory 512
fly scale vm shared-cpu-1x

# ============ MONITORING ============

# Check metrics
fly metrics --app eshtrade

# Check status
fly status --app eshtrade

# Check checks
fly checks list --app eshtrade

# View logs
fly logs --app eshtrade -f

# ============ DATABASE ============

# Create PostgreSQL
fly postgres create --name eshtrade-postgres \
  --region iad \
  --vm-size performance-2x \
  --volume-size 50

# Attach
fly postgres attach eshtrade-postgres --app eshtrade

# Create Redis
fly redis create --name eshtrade-redis \
  --region iad \
  --vm-size shared-cpu-1x

# Attach Redis
fly redis attach eshtrade-redis --app eshtrade

# ============ SECRETS ============

# Set all secrets
fly secrets set \
  GMAIL_APP_PASSWORD=your_password \
  JWT_SECRET=your_jwt_secret \
  SECURITY_MASTER_KEY=your_master_key \
  --app eshtrade

# List secrets
fly secrets list --app eshtrade

# ============ VOLUMES ============

# Create data volume
fly volumes create eshtrade_data \
  --size 50 \
  --region iad \
  --app eshtrade

# Create backup volume
fly volumes create eshtrade_backups \
  --size 100 \
  --region iad \
  --app eshtrade

# ============ CERTIFICATES ============

# Create certificate
fly certs create eshtrade.com --app eshtrade
fly certs create app.eshtrade.com --app eshtrade
fly certs create api.eshtrade.com --app eshtrade

# ============ DESTROY ============

# Destroy production
fly destroy eshtrade --yes

# Destroy development
fly destroy eshtrade-dev --yes