"""
Security middleware for AI Campus Companion.

Provides middleware for security headers, request logging, and CORS configuration.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Adds headers for XSS protection, content type sniffing prevention,
    clickjacking protection, and other security features.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # HSTS (HTTPS Strict Transport Security) - only in production
        settings = get_settings()
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.

    Logs request method, path, client IP, response time, and status code.
    """

    def __init__(
        self,
        app,
        skip_paths: Optional[list[str]] = None,
        log_body: bool = False
    ):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            skip_paths: List of path prefixes to skip logging
            log_body: Whether to log request body (use with caution - may contain sensitive data)
        """
        super().__init__(app)
        self.skip_paths = set(skip_paths or ["/health", "/docs", "/openapi.json", "/redoc"])
        self.log_body = log_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Check if path should be skipped
        path = request.url.path
        if any(path.startswith(skip) for skip in self.skip_paths):
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Get client info
        client_ip = self._get_client_ip(request)
        method = request.method

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request
            logger.info(
                f"{method} {path} {status_code} - {duration_ms:.2f}ms - {client_ip}"
            )

            # Add custom headers for debugging
            response.headers["X-Request-ID"] = str(int(start_time * 1000))
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"{method} {path} ERROR - {duration_ms:.2f}ms - {client_ip} - {str(e)}"
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


class CORSMiddlewareConfig:
    """CORS middleware configuration helper."""

    @staticmethod
    def configure(app: FastAPI, settings) -> None:
        """
        Configure CORS middleware for the application.

        Args:
            app: FastAPI application
            settings: Application settings with CORS configuration
        """
        # Use settings.cors_allow_origins directly
        # For development with empty setting, default to localhost
        origins = settings.cors_allow_origins
        if not origins:
            if settings.app_env == "development":
                origins = ["http://localhost:3000", "http://localhost:5173"]
                logger.warning("CORS_ORIGINS not set. Defaulting to localhost for development.")
            else:
                logger.error("CORS_ORIGINS is empty. This will prevent requests from all origins!")
                origins = ["http://localhost:3000"]  # Fallback to localhost

        # Log CORS configuration
        logger.info(f"Configuring CORS with origins: {origins}")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
            expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Limit",
                          "X-RateLimit-Remaining", "X-RateLimit-Reset"],
            max_age=600  # 10 minutes
        )


def setup_security_middleware(app: FastAPI) -> None:
    """
    Set up all security middleware for the application.

    Args:
        app: FastAPI application
    """
    from app.config import get_settings

    settings = get_settings()

    # 1. Trusted Host Middleware (in production)
    logger.info(f"Configuring TrustedHostMiddleware - app_env: {settings.app_env}, cors_allow_origins: {settings.cors_allow_origins}")

    if settings.app_env == "production":
        allowed_hosts = ["localhost", "127.0.0.1"]
        # Add origins from CORS settings
        for origin in settings.cors_allow_origins:
            host = origin.replace("http://", "").replace("https://", "").split(":")[0]
            allowed_hosts.append(host)

        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
        logger.info(f"✅ TrustedHostMiddleware configured with hosts: {allowed_hosts}")
    else:
        logger.info("⚠️  TrustedHostMiddleware not enabled (development mode)")

    # 2. Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("SecurityHeadersMiddleware configured")

    # 3. Request Logging Middleware
    app.add_middleware(
        RequestLoggingMiddleware,
        skip_paths=["/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"],
        log_body=False
    )
    logger.info("RequestLoggingMiddleware configured")

    # 4. CORS Middleware (MUST be last - executes first to handle OPTIONS preflight)
    CORSMiddlewareConfig.configure(app, settings)

    logger.info("All security middleware configured successfully")
