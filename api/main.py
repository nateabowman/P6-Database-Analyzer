"""FastAPI application for P6 Database Analyzer."""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from utils.logging_config import setup_logging, get_logger
from api.middleware import SecurityHeadersMiddleware, RateLimitMiddleware, AuditMiddleware
from api.auth import get_current_user
from monitoring.metrics_exporter import get_metrics_exporter
from monitoring.health import router as health_router
from api.routes import analysis, profiles, webhooks

logger = setup_logging()
app = FastAPI(title="P6 Database Analyzer API", version="1.0.0")

# Include routes
app.include_router(health_router)
app.include_router(analysis.router)
app.include_router(profiles.router)
app.include_router(webhooks.router)

# Security headers middleware (first)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Audit logging middleware
app.add_middleware(AuditMiddleware)

security = HTTPBearer()


@app.get("/")
def root():
    """API root endpoint."""
    return {"message": "P6 Database Analyzer API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    exporter = get_metrics_exporter()
    return exporter.export_metrics()


@app.get("/api/v1/analysis/schema")
async def analyze_schema(current_user: dict = Depends(get_current_user)):
    """Run schema health analysis."""
    # Placeholder - implement with actual analysis
    return {"status": "not_implemented", "user": current_user.get("username")}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

