"""
Custom exception hierarchy for AI Campus Companion.

Provides standardized error handling with error codes and appropriate status codes.
"""

from __future__ import annotations

from typing import Any, Optional


class AppException(Exception):
    """
    Base application exception class.

    All custom exceptions inherit from this class to ensure consistent error handling.
    """

    def __init__(
        self,
        message: str = "An error occurred",
        error_code: str = "UNKNOWN",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize exception with error details.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., AUTH_001, VAL_001)
            status_code: HTTP status code for this error
            details: Additional error details for debugging
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthError(AppException):
    """
    Authentication-related errors (401 Unauthorized).

    Raised when authentication fails or tokens are invalid.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTH_001",
        status_code: int = 401,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class ValidationError(AppException):
    """
    Validation errors (422 Unprocessable Entity).

    Raised when input validation fails.
    """

    def __init__(
        self,
        message: str = "Invalid input data",
        error_code: str = "VAL_001",
        status_code: int = 422,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class NotFoundError(AppException):
    """
    Resource not found errors (404 Not Found).

    Raised when requested resource doesn't exist.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_001",
        status_code: int = 404,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class RateLimitError(AppException):
    """
    Rate limit exceeded errors (429 Too Many Requests).

    Raised when request rate limit is exceeded.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = "RATE_001",
        status_code: int = 429,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class ExternalServiceError(AppException):
    """
    External service errors (502 Bad Gateway).

    Raised when external services (OpenRouter, email, etc.) fail.
    """

    def __init__(
        self,
        message: str = "External service unavailable",
        error_code: str = "EXT_001",
        status_code: int = 502,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class DatabaseError(AppException):
    """
    Database errors (500 Internal Server Error).

    Raised when database operations fail.
    """

    def __init__(
        self,
        message: str = "Database error occurred",
        error_code: str = "DB_001",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )


class UnauthorizedError(AppException):
    """
    Unauthorized access errors (403 Forbidden).

    Raised when user lacks permissions.
    """

    def __init__(
        self,
        message: str = "Access denied",
        error_code: str = "AUTH_002",
        status_code: int = 403,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )