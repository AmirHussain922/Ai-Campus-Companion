"""
Security utilities for input sanitization and validation.

Provides functions for sanitizing user input, validating data formats,
and preventing common security vulnerabilities like XSS and injection attacks.
"""

from __future__ import annotations

import html
import re
from typing import Pattern

from pydantic import EmailStr, ValidationError


# Regular expression patterns
HTML_TAG_PATTERN: Pattern = re.compile(r"<[^>]+>")
JAVASCRIPT_SCHEME_PATTERN: Pattern = re.compile(r"javascript:", re.IGNORECASE)
SQL_INJECTION_PATTERN: Pattern = re.compile(
    r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)|"
    r"(--|#|/\*|\*/)",
    re.IGNORECASE
)
EMAIL_PATTERN: Pattern = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
SPECIAL_CHARS_PATTERN: Pattern = re.compile(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]")


def sanitize_html(text: str) -> str:
    """
    Remove HTML tags and encode special characters to prevent XSS attacks.

    Args:
        text: The input text to sanitize.

    Returns:
        Sanitized text with HTML tags removed and special characters escaped.
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove HTML tags
    text = HTML_TAG_PATTERN.sub("", text)

    # HTML encode special characters
    text = html.escape(text)

    return text.strip()


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

    return HTML_TAG_PATTERN.sub("", text).strip()


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

    return not JAVASCRIPT_SCHEME_PATTERN.search(text)


def validate_no_sql_injection(text: str) -> bool:
    """
    Basic check for common SQL injection patterns.

    Note: This is a basic check. Use parameterized queries for proper protection.

    Args:
        text: The input text to validate.

    Returns:
        True if no SQL injection patterns found, False otherwise.
    """
    if not text or not isinstance(text, str):
        return True

    return not SQL_INJECTION_PATTERN.search(text)


def sanitize_input(
    text: str,
    max_length: int = 10000,
    allow_html: bool = False,
    check_sql: bool = True,
    check_javascript: bool = True
) -> str:
    """
    Comprehensive input sanitization function.

    Args:
        text: The input text to sanitize.
        max_length: Maximum allowed length.
        allow_html: Whether to allow HTML tags (default: False).
        check_sql: Whether to check for SQL injection patterns.
        check_javascript: Whether to check for javascript: schemes.

    Returns:
        Sanitized text.

    Raises:
        ValueError: If input fails validation checks.
    """
    if not text or not isinstance(text, str):
        return ""

    # Check length
    if len(text) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length} characters")

    # Check for JavaScript schemes
    if check_javascript and not validate_no_javascript(text):
        raise ValueError("Input contains potentially dangerous content (javascript: scheme)")

    # Check for SQL injection
    if check_sql and not validate_no_sql_injection(text):
        raise ValueError("Input contains potentially dangerous content (SQL injection patterns)")

    # Handle HTML
    if not allow_html:
        text = sanitize_html(text)
    else:
        # Even with HTML allowed, encode special chars
        text = html.escape(text)

    return text.strip()


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


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength according to security requirements.

    Args:
        password: The password to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must not exceed 128 characters"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    if not SPECIAL_CHARS_PATTERN.search(password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"

    # Check for common patterns
    common_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
    if password.lower() in common_passwords:
        return False, "Password is too common, please choose a more unique password"

    return True, ""


def mask_email(email: str) -> str:
    """
    Mask email address for privacy in logs.

    Args:
        email: The email address to mask.

    Returns:
        Masked email address (e.g., j***@example.com).
    """
    if not email or "@" not in email:
        return "***"

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1) if local else ""
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: The length of the token in bytes (result will be hex encoded, so 2x length).

    Returns:
        Hex-encoded random token.
    """
    import secrets

    return secrets.token_hex(length)


def constant_time_compare(val1: str, val2: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.

    Args:
        val1: First string to compare.
        val2: Second string to compare.

    Returns:
        True if strings are equal, False otherwise.
    """
    import hmac

    return hmac.compare_digest(val1.encode(), val2.encode())
