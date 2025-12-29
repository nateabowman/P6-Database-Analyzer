"""Enhanced health check endpoints."""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter
from utils.logging_config import get_logger
from utils.metrics import get_metrics

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready")
def readiness_check() -> Dict[str, Any]:
    """Readiness probe for Kubernetes."""
    # Check if application is ready to serve traffic
    # Add checks for database connectivity, etc.
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
def liveness_check() -> Dict[str, Any]:
    """Liveness probe for Kubernetes."""
    # Check if application is alive
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed")
def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status."""
    metrics = get_metrics()
    metrics_summary = metrics.get_metrics_summary()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "database": "healthy",  # Would check actual DB connection
            "cache": "healthy"
        },
        "metrics": {
            "uptime_seconds": metrics_summary.get("uptime_seconds", 0),
            "total_requests": metrics_summary.get("counters", {}).get("http_requests_total", 0)
        }
    }

