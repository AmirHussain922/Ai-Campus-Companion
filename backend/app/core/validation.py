"""
Input validation and sanitization for AI Campus Companion.

Provides comprehensive input validation, request size limits, file upload validation,
and HTML sanitization to prevent XSS and injection attacks.
"""

from __future__ import annotations

import html
import re
import secrets
from typing import Optional, Set

from fastapi import HTTPException, Request, Response, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware


# ============================================================================
# Dangerous content patterns
# ============================================================================

# Patterns for detecting potentially dangerous content
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript:',  # JavaScript protocol
    r'on\w+\s*=',  # Event handlers (onerror, onload, etc.)
    r'data:text/html',  # Data URLs with HTML
    r'<iframe[^>]*>.*?</iframe>',  # Iframes
    r'<embed[^>]*>',  # Embed tags
    r'<object[^>]*>.*?</object>',  # Object tags
]

DANGEROUS_PATTERN_REGEX = re.compile(
    '|'.join(DANGEROUS_PATTERNS),
    re.IGNORECASE | re.DOTALL
)


# ============================================================================
# Pagination Models
# ============================================================================

class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.

    Attributes:
        limit: Maximum number of items to return (1-100, default 20)
        offset: Number of items to skip (default 0)
    """
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of items to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip"
    )


# ============================================================================
# Request Size Middleware
# ============================================================================

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to reject requests with Content-Length exceeding limit.

    Prevents DoS attacks via large payload submissions.
    """

    def __init__(self, app, max_size: int = 1_048_576):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            max_size: Maximum request body size in bytes (default: 1MB)
        """
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        """
        Process request and check Content-Length.

        Args:
            request: FastAPI request
            call_next: Next middleware or route handler

        Returns:
            FastAPI response

        Raises:
            HTTPException: If request body exceeds maximum size
        """
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length_int = int(content_length)
                if content_length_int > self.max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "message": f"Request body too large. Maximum size is {self.max_size // 1024}KB",
                            "error_code": "VAL_004"
                        }
                    )
            except ValueError:
                # Invalid Content-Length header, reject
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Invalid Content-Length header", "error_code": "VAL_003"}
                )

        response = await call_next(request)
        return response


# ============================================================================
# HTML Sanitization
# ============================================================================

def sanitize_html(raw: str) -> str:
    """
    Sanitize HTML input to prevent XSS attacks.

    Args:
        raw: Raw input string

    Returns:
        Sanitized string with dangerous content removed

    Raises:
        ValueError: If dangerous content is detected
    """
    if not raw or not isinstance(raw, str):
        return ""

    # Check for dangerous patterns
    if DANGEROUS_PATTERN_REGEX.search(raw):
        raise ValueError("Potentially malicious content detected. HTML scripts, iframes, and event handlers are not allowed.")

    # Strip all HTML tags
    stripped = re.sub(r'<[^>]+>', '', raw)

    # HTML encode any remaining special characters
    encoded = html.escape(stripped)

    return encoded.strip()


def strip_html_tags(text: str) -> str:
    """
    Remove HTML tags from text without encoding special characters.

    Args:
        text: The input text to process.

    Returns:
        Text with HTML tags removed.
    """
    if not text or not isinstance(text, str):
        return ""

    return re.sub(r'<[^>]+>', '', text).strip()


# ============================================================================
# JavaScript Scheme Validation
# ============================================================================

def validate_no_javascript(text: str) -> bool:
    """
    Check if text contains javascript: scheme which could be used for XSS.

    Args:
        text: The input text to validate.

    Returns:
        True if no javascript scheme found, False otherwise.
    """
    if not text or not isinstance(text, str):
        return True

    # Case-insensitive check for javascript: protocol
    return "javascript:" not in text.lower()


# ============================================================================
# File Upload Validation
# ============================================================================

async def validate_file_upload(
    file: UploadFile,
    allowed_types: Set[str],
    max_bytes: int,
    allowed_extensions: Optional[Set[str]] = None
) -> None:
    """
    Validate uploaded file.

    Args:
        file: UploadFile object from FastAPI
        allowed_types: Set of allowed MIME types (e.g., {"image/jpeg", "image/png"})
        max_bytes: Maximum file size in bytes
        allowed_extensions: Optional set of allowed file extensions (e.g., {".jpg", ".png"})

    Raises:
        ValueError: If file validation fails
        HTTPException: If file size exceeds maximum
    """
    if not file:
        raise ValueError("No file provided")

    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Seek back to start

    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "message": f"File too large. Maximum size is {max_bytes // 1024}KB",
                "error_code": "VAL_005"
            }
        )

    # Check content type
    if file.content_type and file.content_type not in allowed_types:
        raise ValueError(
            f"File type '{file.content_type}' not allowed. "
            f"Allowed types: {', '.join(sorted(allowed_types))}"
        )

    # Check file extension if provided
    if allowed_extensions and file.filename:
        # Extract file extension (case-insensitive)
        import os
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in allowed_extensions:
            raise ValueError(
                f"File extension '{ext}' not allowed. "
                f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
            )

    # Check for potential malicious file patterns
    if file.filename:
        lower_filename = file.filename.lower()
        dangerous_patterns = ['..', '.php', '.jsp', '.asp', '.exe', '.sh', '.bat', '.cmd']
        if any(pattern in lower_filename for pattern in dangerous_patterns):
            raise ValueError("File name contains potentially dangerous patterns")


# ============================================================================
# Content-Type Validation
# ============================================================================

def validate_content_type(
    content_type: str,
    allowed_types: Set[str]
) -> None:
    """
    Validate request Content-Type header.

    Args:
        content_type: Content-Type header value
        allowed_types: Set of allowed content types

    Raises:
        ValueError: If content type is not allowed
    """
    if not content_type:
        raise ValueError("Content-Type header is required")

    # Handle charset parameter (e.g., "application/json; charset=utf-8")
    content_type_base = content_type.split(';')[0].strip()

    if content_type_base not in allowed_types:
        raise ValueError(
            f"Content-Type '{content_type_base}' not allowed. "
            f"Allowed types: {', '.join(sorted(allowed_types))}"
        )


# ============================================================================
# General Input Validation
# ============================================================================

def validate_string_length(
    value: str,
    field_name: str,
    min_length: int = 0,
    max_length: int = 10_000
) -> str:
    """
    Validate string length.

    Args:
        value: String to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        Validated string

    Raises:
        ValueError: If length validation fails
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters long")

    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")

    return value.strip() if min_length > 0 else value


def validate_boolean(value: str, field_name: str) -> bool:
    """
    Validate and convert string to boolean.

    Args:
        value: String to validate
        field_name: Name of the field (for error messages)

    Returns:
        Boolean value

    Raises:
        ValueError: If value cannot be converted to boolean
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lower_value = value.lower().strip()
        if lower_value in ('true', '1', 'yes', 'on'):
            return True
        elif lower_value in ('false', '0', 'no', 'off'):
            return False

    raise ValueError(
        f"{field_name} must be a boolean (true/false, yes/no, 1/0)"
    )


def validate_integer_range(
    value: int,
    field_name: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None
) -> int:
    """
    Validate integer value is within range.

    Args:
        value: Integer to validate
        field_name: Name of the field (for error messages)
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Returns:
        Validated integer

    Raises:
        ValueError: If value is not within range
    """
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if min_value is not None and value < min_value:
        raise ValueError(f"{field_name} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValueError(f"{field_name} must not exceed {max_value}")

    return value


# ============================================================================
# Email Validation
# ============================================================================

EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex pattern.

    Args:
        email: The email address to validate.

    Returns:
        True if email format is valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False

    return bool(EMAIL_PATTERN.match(email))


# ============================================================================
# Null Byte Check
# ============================================================================

def validate_no_null_bytes(text: str) -> None:
    """
    Basic sanity check for null bytes which can cause issues in database operations.

    This is not injection prevention - MongoDB injection is prevented via
    proper parameterized queries and BSON encoding. This is simply to catch
    malformed input that could cause unexpected behavior.

    Args:
        text: The input text to validate.

    Raises:
        ValueError: If null bytes are found in the input.
    """
    if not text or not isinstance(text, str):
        return

    if '\x00' in text:
        raise ValueError("Input contains null bytes which are not allowed")