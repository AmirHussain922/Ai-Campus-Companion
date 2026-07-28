"""
Services package for AI Campus Companion.

Contains external service integrations like email, file storage, etc.
"""

from .email_service import EmailService, get_email_service

__all__ = ["EmailService", "get_email_service"]
