"""
Utility functions shared across modules.

Contains functions like database availability tracking
that shouldn't cause circular imports.
"""

from typing import Optional


# Database availability tracking
_database_available: bool = True


def set_database_available(available: bool) -> None:
    """
    Set the database availability status.

    Args:
        available: Whether the database is available
    """
    global _database_available
    _database_available = available


def is_database_available() -> bool:
    """
    Check if database is available for rate limiting.

    Returns:
        Whether the database is currently available
    """
    return _database_available
