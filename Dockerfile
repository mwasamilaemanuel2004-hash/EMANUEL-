# ============================================
# ESH.TRADE - ULTIMATE DOCKERFILE (OPTIMIZED)
# ============================================
# Multi-stage build | Security hardened | Production ready

# ============================================
# STAGE 1: BUILDER
# ============================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev libffi-dev libssl-dev curl git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (requirements live in backend/)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy app code
COPY backend/ .

# Ensure runtime data dir exists in the image (data/ is not tracked in git)
RUN mkdir -p /build/data

# ============================================
# STAGE 2: FINAL (Slim)
# ============================================
FROM python:3.12-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC \
    PYTHONPATH=/app

WORKDIR /app

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder (installed to /usr/local so non-root appuser can read them)
COPY --from=builder /install /usr/local
COPY --from=builder /build/app /app/app
COPY --from=builder /build/data /app/data

# NOTE: Do NOT COPY .env into the image - it is not committed to git (by design).
# Set environment variables in the Render/DigitalOcean dashboard instead.

# Create non-root user
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --gid 1001 appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]