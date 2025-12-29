"""Middleware for API authentication, rate limiting, and security."""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from utils.logging_config import get_logger
from utils.audit import get_audit_logger, AuditEventType
from api.auth import get_current_user, decode_token

logger = get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: Client identifier (IP or user ID)
        
        Returns:
            True if request is allowed
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.requests_per_minute:
            return False
        
        # Record request
        self.requests[identifier].append(now)
        return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        response = await call_next(request)
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware."""
    
    async def dispatch(self, request: Request, call_next):
        audit_logger = get_audit_logger()
        start_time = datetime.utcnow()
        
        # Extract user info if authenticated
        user_id = None
        username = None
        try:
            if "authorization" in request.headers:
                token = request.headers["authorization"].replace("Bearer ", "")
                payload = decode_token(token)
                user_id = payload.get("sub")
                username = payload.get("username")
        except:
            pass
        
        # Process request
        response = await call_next(request)
        
        # Log audit event
        audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action=f"{request.method} {request.url.path}",
            user_id=user_id,
            username=username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="success" if response.status_code < 400 else "failure",
            details={
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        )
        
        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelisting middleware."""
    
    def __init__(self, app, allowed_ips: Optional[list] = None):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips or [])
        self.enabled = len(self.allowed_ips) > 0
    
    async def dispatch(self, request: Request, call_next):
        if self.enabled:
            client_ip = request.client.host if request.client else None
            if client_ip and client_ip not in self.allowed_ips:
                logger.warning(f"IP {client_ip} not in whitelist")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address not allowed"
                )
        
        response = await call_next(request)
        return response

