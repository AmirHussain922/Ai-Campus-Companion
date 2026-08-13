"""
Logging configuration with sensitive data redaction.

Provides a filter that automatically redacts sensitive information from log messages.
"""

from __future__ import annotations

import logging
import re
from typing import Pattern

# Patterns to redact from log messages
SENSITIVE_PATTERNS: dict[str, Pattern] = {
    "password": re.compile(r'("(password|pwd)\s*:\s*)"[^"]*"', re.IGNORECASE),
    "token": re.compile(r'("(token|bearer|access|refresh)\s*:\s*)"[^"]*"', re.IGNORECASE),
    "secret": re.compile(r'("(secret|api_key|apikey|sk-|sk_test\-[a-z]+)"\s*:\s*)"[^"]*"', re.IGNORECASE),
    "otp": re.compile(r'("(otp|verification_code|code)"\s*:\s*)"[^"]*"', re.IGNORECASE),
    "authorization": re.compile(r'("Authorization:\s*)[^"]+"', re.IGNORECASE),
    "authorization_header": re.compile(r'(Authorization:\s*Bearer\s+)[^"]+'),
    "api_key": re.compile(r'(api[_-]?key)\s*:\s*"[^"]*"', re.IGNORECASE),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
}


class RedactingFilter(logging.Filter):
    """
    Logging filter that automatically redacts sensitive data.

    Automatically redacts passwords, tokens, API keys, and other sensitive information
    from log messages before they are processed.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records and redact sensitive data.

        Args:
            record: Log record to filter

        Returns:
            True to include the record, False to exclude
        """
        if isinstance(record.msg, str):
            original_msg = record.msg
            for key, pattern in SENSITIVE_PATTERNS.items():
                record.msg = pattern.sub(r'[REDACTED]', record.msg)
            # Only update if something was redacted
            if record.msg != original_msg:
                record.msg = f"[REDACTED] {record.msg}"

        return True


def configure_redacting_filter(handler: logging.Handler) -> None:
    """
    Configure a logging handler with the redacting filter.

    Args:
        handler: Logging handler to configure
    """
    redacting_filter = RedactingFilter()
    handler.addFilter(redacting_filter)


def mask_sensitive_in_message(message: str) -> str:
    """
    Mask sensitive data in a log message string.

    Args:
        message: Message to mask

    Returns:
        Message with sensitive data redacted
    """
    if not isinstance(message, str):
        return message

    for key, pattern in SENSITIVE_PATTERNS.items():
        message = pattern.sub(r'\1"[REDACTED]"', message, flags=re.IGNORECASE)

    return message if "[REDACTED]" in message else message


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging with redaction for the application.

    Args:
        log_level: Log level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    import sys

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create console handler with redaction
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add redacting filter
    console_handler.addFilter(RedactingFilter())

    root_logger.addHandler(console_handler)

    # Configure root logger
    logging.getLogger('motor').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level} and sensitive data redaction enabled")