"""
Rate limiting implementation using MongoDB.

Provides sliding window rate limiting for API endpoints with configurable
limits per action type (login, registration, OTP resend, etc.).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from cachetools import TTLCache
from fastapi import HTTPException, Request, status

from app.core.database import get_database
from app.core.utils import is_database_available, set_database_available

logger = logging.getLogger(__name__)


# Set of sensitive endpoints that should fail closed when rate limiter is unavailable
SENSITIVE_ENDPOINTS = {
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/reset-password",
}

# Flag to track database availability
_database_available: bool = True


# In-memory cache for rate limiting in emergency mode (only when database is unavailable)
_fallback_cache = TTLCache(maxsize=10000, ttl=300)


class RateLimitAction(str, Enum):
    """Rate limit action types."""
    LOGIN = "login"
    REGISTER = "register"
    OTP_RESEND = "otp_resend"
    OTP_VERIFY = "otp_verify"
    PASSWORD_RESET = "password_reset"
    CHAT = "chat"
    GENERAL = "general"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int
    window_seconds: int
    block_duration_seconds: Optional[int] = None


# Default rate limit configurations
DEFAULT_RATE_LIMITS: dict[RateLimitAction, RateLimitConfig] = {
    RateLimitAction.LOGIN: RateLimitConfig(
        max_requests=10,
        window_seconds=120,  # 2 minutes
        block_duration_seconds=120  # 2 minutes reset
    ),
    RateLimitAction.REGISTER: RateLimitConfig(
        max_requests=3,
        window_seconds=3600,  # 1 hour
        block_duration_seconds=3600
    ),
    RateLimitAction.OTP_RESEND: RateLimitConfig(
        max_requests=3,
        window_seconds=3600,  # 1 hour
        block_duration_seconds=3600
    ),
    RateLimitAction.OTP_VERIFY: RateLimitConfig(
        max_requests=10,
        window_seconds=600,  # 10 minutes
        block_duration_seconds=600
    ),
    RateLimitAction.PASSWORD_RESET: RateLimitConfig(
        max_requests=3,
        window_seconds=3600,  # 1 hour
        block_duration_seconds=3600
    ),
    RateLimitAction.CHAT: RateLimitConfig(
        max_requests=30,
        window_seconds=3600,  # 1 hour - stricter limit to control API costs
        block_duration_seconds=300  # 5 minutes
    ),
    RateLimitAction.GENERAL: RateLimitConfig(
        max_requests=100,
        window_seconds=60  # 1 minute
    )
}


class RateLimiter:
    """
    Rate limiter using MongoDB for distributed rate limiting.

    Features:
    - Sliding window rate limiting
    - Per-action and per-identifier rate limits
    - Automatic cleanup of expired entries via TTL
    - Configurable block durations for repeated violations
    """

    def __init__(
        self,
        rate_limits: Optional[dict[RateLimitAction, RateLimitConfig]] = None
    ):
        """
        Initialize rate limiter.

        Args:
            rate_limits: Custom rate limit configurations (optional)
        """
        self._rate_limits = rate_limits or DEFAULT_RATE_LIMITS

    def _get_limit_key(
        self,
        identifier: str,
        action: RateLimitAction
    ) -> str:
        """Generate rate limit key for identifier and action."""
        return f"{action.value}:{identifier.lower()}"

    async def is_allowed(
        self,
        identifier: str,
        action: RateLimitAction
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.

        Args:
            identifier: Rate limit identifier (email, IP, etc.)
            action: Rate limit action type

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        config = self._rate_limits.get(action, self._rate_limits[RateLimitAction.GENERAL])
        key = self._get_limit_key(identifier, action)

        # First, try database-based rate limiting
        try:
            db = await get_database()
        except Exception:
            db = None

        # If database is not available, use fallback cache
        if db is None:
            # Emergency mode: use in-memory cache
            now = datetime.now(timezone.utc)
            
            # Check if currently blocked in cache
            block_key = f"block:{key}"
            if block_key in _fallback_cache:
                reset_time = _fallback_cache[block_key]
                return False, {
                    "limit": config.max_requests,
                    "remaining": 0,
                    "reset_timestamp": int(reset_time.timestamp()),
                    "blocked": True,
                    "emergency_mode": True
                }

            # Get current count from cache
            current_count = _fallback_cache.get(key, 0)

            # If limit exceeded, block the request
            if current_count >= config.max_requests:
                block_duration = config.block_duration_seconds or config.window_seconds
                block_until = now + timedelta(seconds=block_duration)
                _fallback_cache[block_key] = block_until

                logger.critical(f"Rate limiter in emergency mode: blocked {key} for identifier {identifier}")
                return False, {
                    "limit": config.max_requests,
                    "remaining": 0,
                    "reset_timestamp": int(block_until.timestamp()),
                    "blocked": True,
                    "emergency_mode": True
                }

            # Increment count in cache
            _fallback_cache[key] = current_count + 1
            
            reset_time = now + timedelta(seconds=config.window_seconds)
            return True, {
                "limit": config.max_requests,
                "remaining": config.max_requests - current_count - 1,
                "reset_timestamp": int(reset_time.timestamp()),
                "blocked": False,
                "emergency_mode": True
            }

        # Database-based rate limiting (normal case)
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=config.window_seconds)

        # Check if currently blocked
        block_key = f"block:{key}"
        block_record = await db.rate_limits.find_one({
            "key": block_key,
            "expires_at": {"$gt": now}
        })

        if block_record:
            reset_time = block_record["expires_at"]
            # Ensure reset_time is timezone-aware
            if reset_time.tzinfo is None:
                reset_time = reset_time.replace(tzinfo=timezone.utc)
            return False, {
                "limit": config.max_requests,
                "remaining": 0,
                "reset_timestamp": int(reset_time.timestamp()),
                "blocked": True
            }

        # Get or create rate limit record
        rate_limit = await db.rate_limits.find_one({"key": key})

        if not rate_limit:
            # First request
            expires_at = now + timedelta(seconds=config.window_seconds)
            await db.rate_limits.insert_one({
                "key": key,
                "count": 1,
                "window_start": now,
                "expires_at": expires_at
            })
            return True, {
                "limit": config.max_requests,
                "remaining": config.max_requests - 1,
                "reset_timestamp": int(expires_at.timestamp()),
                "blocked": False
            }

        # Check if window has expired
        window_start_time = rate_limit.get("window_start", now)
        # Ensure window_start_time is timezone-aware
        if window_start_time.tzinfo is None:
            window_start_time = window_start_time.replace(tzinfo=timezone.utc)
            
        if window_start_time < window_start:
            # Reset window
            expires_at = now + timedelta(seconds=config.window_seconds)
            await db.rate_limits.update_one(
                {"key": key},
                {
                    "$set": {
                        "count": 1,
                        "window_start": now,
                        "expires_at": expires_at
                    }
                }
            )
            return True, {
                "limit": config.max_requests,
                "remaining": config.max_requests - 1,
                "reset_timestamp": int(expires_at.timestamp()),
                "blocked": False
            }

        # Check if limit exceeded
        current_count = rate_limit.get("count", 0)
        if current_count >= config.max_requests:
            # Block the identifier
            expires_at = rate_limit.get("expires_at", now + timedelta(seconds=config.window_seconds))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
                
            if config.block_duration_seconds:
                block_until = now + timedelta(seconds=config.block_duration_seconds)
                await db.rate_limits.insert_one({
                    "key": block_key,
                    "count": 0,
                    "window_start": now,
                    "expires_at": block_until
                })
                expires_at = block_until

            return False, {
                "limit": config.max_requests,
                "remaining": 0,
                "reset_timestamp": int(expires_at.timestamp()),
                "blocked": True
            }

        # Increment count
        await db.rate_limits.update_one(
            {"key": key},
            {
                "$inc": {"count": 1},
                "$set": {"updated_at": now}
            }
        )

        expires_at = rate_limit.get("expires_at", now + timedelta(seconds=config.window_seconds))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        remaining = config.max_requests - current_count - 1
        return True, {
            "limit": config.max_requests,
            "remaining": max(0, remaining),
            "reset_timestamp": int(expires_at.timestamp()),
            "blocked": False
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def check_rate_limit(
    request: Request,
    action: RateLimitAction,
    identifier: Optional[str] = None
) -> tuple[bool, dict]:
    """
    FastAPI dependency for rate limiting.

    Args:
        request: FastAPI request object
        action: Rate limit action type
        identifier: Custom identifier (defaults to client IP)

    Returns:
        Tuple of (is_allowed, rate_limit_info)

    Raises:
        HTTPException: If rate limit exceeded
    """
    # Get identifier (email, IP, or custom)
    if identifier is None:
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            identifier = forwarded.split(",")[0].strip()
        else:
            identifier = request.client.host if request.client else "unknown"

    limiter = await get_rate_limiter()
    is_allowed, rate_info = await limiter.is_allowed(identifier, action)

    if not is_allowed:
        from fastapi import HTTPException, status

        reset_timestamp = rate_info.get("reset_timestamp", 0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Rate limit exceeded. Please try again later.",
                "reset_at": reset_timestamp,
                "error_code": "AUTH_008"
            },
            headers={
                "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_timestamp),
                "Retry-After": str(max(0, reset_timestamp - int(__import__('time').time())))
            }
        )

    # Add rate limit headers to request state for later use
    request.state.rate_limit_info = rate_info

    return is_allowed, rate_info


def get_rate_limit_headers(rate_info: dict) -> dict[str, str]:
    """
    Get rate limit headers for response.

    Args:
        rate_info: Rate limit information from check_rate_limit

    Returns:
        Dictionary of rate limit headers
    """
    return {
        "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
        "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
        "X-RateLimit-Reset": str(rate_info.get("reset_timestamp", 0))
    }
