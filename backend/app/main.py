"""
Main FastAPI Application Entry Point
ESMH.TRADE - AI-Powered Trading Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from loguru import logger

# Configure Logging
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    level="INFO"
)

# Initialize FastAPI App
app = FastAPI(
    title="ESMH.TRADE API",
    description="AI-Powered Trading Platform API",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.esmh.trade"]
)

# Include API Routers
from .api import auth, trading, debug

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
app.include_router(debug.router, prefix="/api/debug", tags=["Debug"])


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": "ESMH.TRADE API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/api/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/status", tags=["Status"])
async def api_status():
    """API status and version info"""
    return {
        "api_version": "2.0.0",
        "status": "operational",
        "modules": {
            "auth": "active",
            "trading": "active",
            "debug": "active",
            "risk_management": "active",
            "adaptive_engine": "active",
            "indicator_engine": "active",
            "candle_analyzer": "active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
