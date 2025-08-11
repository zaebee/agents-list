#!/usr/bin/env python3
"""
Security middleware and utilities for AI-CRM system.
"""

from typing import Dict, Optional, Any, List
from fastapi import Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re
import logging
import hashlib
import json
from collections import defaultdict
import time

# Configure logging
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with sliding window algorithm."""

    def __init__(self, app, default_rate_limit: int = 100):
        super().__init__(app)
        self.default_rate_limit = default_rate_limit
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()

    def _cleanup_old_requests(self):
        """Clean up old request records."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - 3600  # 1 hour ago
        for key in list(self.requests.keys()):
            self.requests[key] = [
                timestamp for timestamp in self.requests[key] if timestamp > cutoff_time
            ]
            if not self.requests[key]:
                del self.requests[key]

        self.last_cleanup = current_time

    def _get_rate_limit(self, request: Request) -> int:
        """Get rate limit for request based on user/endpoint."""
        # TODO: Implement database lookup for user-specific rate limits
        # For now, return default
        return self.default_rate_limit

    def _get_client_key(self, request: Request) -> str:
        """Generate unique key for client identification."""
        # Use IP address as fallback, but prefer authenticated user
        client_ip = request.client.host if request.client else "unknown"

        # Try to get user from authorization header
        auth_header = request.headers.get("authorization")
        if auth_header:
            # Create hash of auth header for privacy
            auth_hash = hashlib.sha256(auth_header.encode()).hexdigest()[:16]
            return f"user:{auth_hash}"

        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Clean up old records periodically
        self._cleanup_old_requests()

        # Get client identifier and rate limit
        client_key = self._get_client_key(request)
        rate_limit = self._get_rate_limit(request)

        # Check current request count in the last hour
        current_time = time.time()
        hour_ago = current_time - 3600

        # Filter requests from the last hour
        recent_requests = [
            timestamp for timestamp in self.requests[client_key] if timestamp > hour_ago
        ]

        # Check if rate limit exceeded
        if len(recent_requests) >= rate_limit:
            logger.warning(
                f"Rate limit exceeded for {client_key}: {len(recent_requests)}/{rate_limit}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": 3600,
                    "limit": rate_limit,
                    "remaining": 0,
                },
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + 3600)),
                },
            )

        # Record this request
        self.requests[client_key].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = rate_limit - len(recent_requests) - 1
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 3600))

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests for security monitoring."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Generate request ID for tracking
        request_id = hashlib.md5(
            f"{time.time()}{request.client.host if request.client else 'unknown'}".encode()
        ).hexdigest()[:16]

        # Log request start
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")

        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request completion
            logger.info(
                f"Request {request_id} completed: "
                f"status={response.status_code} "
                f"time={process_time:.3f}s"
            )

            return response

        except Exception as e:
            # Log request error
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed: error={str(e)} time={process_time:.3f}s"
            )
            raise


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP address whitelisting for admin endpoints."""

    def __init__(self, app, admin_whitelist: Optional[List[str]] = None):
        super().__init__(app)
        self.admin_whitelist = admin_whitelist or []
        self.admin_patterns = [re.compile(r"/admin.*"), re.compile(r"/users/admin.*")]

    def _is_admin_endpoint(self, path: str) -> bool:
        """Check if path is an admin endpoint."""
        return any(pattern.match(path) for pattern in self.admin_patterns)

    def _is_whitelisted_ip(self, ip: str) -> bool:
        """Check if IP is in whitelist."""
        if not self.admin_whitelist:
            return True  # No whitelist configured

        return ip in self.admin_whitelist

    async def dispatch(self, request: Request, call_next):
        # Check admin endpoints
        if self._is_admin_endpoint(request.url.path):
            client_ip = request.client.host if request.client else "unknown"

            if not self._is_whitelisted_ip(client_ip):
                logger.warning(
                    f"Unauthorized admin access attempt from IP: {client_ip}"
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Access denied"},
                )

        return await call_next(request)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            re.compile(r"<script[^>]*>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"union\s+select", re.IGNORECASE),
            re.compile(r"drop\s+table", re.IGNORECASE),
            re.compile(r"insert\s+into", re.IGNORECASE),
            re.compile(r"delete\s+from", re.IGNORECASE),
        ]

    def _scan_for_malicious_content(self, text: str) -> bool:
        """Scan text for potentially malicious patterns."""
        if not isinstance(text, str):
            return False

        return any(pattern.search(text) for pattern in self.suspicious_patterns)

    def _scan_dict(self, data: Dict[str, Any]) -> bool:
        """Recursively scan dictionary for malicious content."""
        for key, value in data.items():
            if isinstance(value, str):
                if self._scan_for_malicious_content(value):
                    return True
            elif isinstance(value, dict):
                if self._scan_dict(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and self._scan_for_malicious_content(item):
                        return True
                    elif isinstance(item, dict) and self._scan_dict(item):
                        return True
        return False

    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Check query parameters
        for param, value in request.query_params.items():
            if self._scan_for_malicious_content(value):
                logger.warning(
                    f"Malicious content detected in query param '{param}': {value}"
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid input detected"},
                )

        # For POST/PUT requests, check request body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body
                body = await request.body()
                if body:
                    # Try to parse as JSON
                    try:
                        json_data = json.loads(body.decode())
                        if isinstance(json_data, dict) and self._scan_dict(json_data):
                            logger.warning("Malicious content detected in request body")
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "Invalid input detected"},
                            )
                    except json.JSONDecodeError:
                        # Not JSON, check as string
                        body_str = body.decode("utf-8", errors="ignore")
                        if self._scan_for_malicious_content(body_str):
                            logger.warning("Malicious content detected in request body")
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "Invalid input detected"},
                            )

                # Reconstruct request with body
                async def receive():
                    return {"type": "http.request", "body": body}

                request._receive = receive

            except Exception as e:
                logger.error(f"Error processing request body: {e}")

        return await call_next(request)


def get_cors_params() -> Dict[str, Any]:
    """Get CORS middleware parameters."""
    return {
        "allow_origins": [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://zae.life:8000",
            "http://zae.life:8888",
            "http://zae.life:3000",
            "https://crm.zae.life",
        ],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Mx-ReqToken",
            "Keep-Alive",
            "X-Requested-With",
            "If-Modified-Since",
        ],
        "expose_headers": [
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
    }


def setup_security_middleware(app):
    """Setup all security middleware for the FastAPI app."""

    # Add security middleware in order
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(
        RateLimitMiddleware, default_rate_limit=1000
    )  # 1000 requests per hour default

    # IP whitelist for admin endpoints (if configured)
    admin_whitelist = []  # Add admin IPs here if needed
    if admin_whitelist:
        app.add_middleware(IPWhitelistMiddleware, admin_whitelist=admin_whitelist)

    # CORS middleware (should be last)
    app.add_middleware(CORSMiddleware, **get_cors_params())


class SecurityConfig:
    """Security configuration settings."""

    # Rate limiting
    DEFAULT_RATE_LIMIT = 1000  # requests per hour
    BURST_RATE_LIMIT = 50  # requests per minute

    # Session settings
    SESSION_TIMEOUT_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    MAX_FAILED_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_MINUTES = 15

    # Password policy
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True

    # Security headers
    HSTS_MAX_AGE = 31536000  # 1 year
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # Admin security
    ADMIN_IP_WHITELIST = []  # Add specific IPs if needed
    ADMIN_SESSION_TIMEOUT = 15  # minutes

    # Audit logging
    LOG_ALL_REQUESTS = True
    LOG_FAILED_AUTH_ATTEMPTS = True
    LOG_ADMIN_ACTIONS = True

    # Feature flags
    ENABLE_RATE_LIMITING = True
    ENABLE_IP_WHITELISTING = False
    ENABLE_INPUT_VALIDATION = True
    ENABLE_SECURITY_HEADERS = True


def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    return SecurityConfig()
