"""
Transaction decorators for AI Campus Companion.

Provides database transaction support using MongoDB sessions.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Coroutine

from motor.motor_asyncio import AsyncIOMotorClientSession
from starlette.concurrency import run_in_threadpool

from app.core.database import get_mongo_client, get_database

logger = logging.getLogger(__name__)


async def get_session() -> AsyncIOMotorClientSession:
    """
    Get or create a MongoDB session for transactional operations.

    Returns:
        MongoDB client session

    Raises:
        RuntimeError: If database connection is unavailable
    """
    client = await get_mongo_client()
    if client is None:
        raise RuntimeError("MongoDB client is not available")

    return client.start_session()


async def _run_in_session(
    func: Callable[..., Coroutine[Any, Any, Any]],
    session: AsyncIOMotorClientSession,
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Run a function within a transaction session.

    Args:
        func: Async function to execute
        session: MongoDB session
        args: Positional arguments for func
        kwargs: Keyword arguments for func

    Returns:
        Result of the function

    Raises:
        Exception: Propagates any exception that occurs
    """
    try:
        return await func(*args, session=session, **kwargs)
    except Exception as e:
        # Abort transaction on error
        await session.abort_transaction()
        logger.error(f"Transaction aborted: {e}")
        raise


def transactional(
    retry_on_conflict: int = 1,
    max_retry_delay: float = 0.5
) -> Callable:
    """
    Decorator for transactional database operations.

    Wraps an async function in a MongoDB transaction with automatic retry
    on optimistic concurrency conflicts.

    Args:
        retry_on_conflict: Maximum number of retry attempts for conflicts
        max_retry_delay: Maximum delay between retries (seconds)

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a session if not already provided
            session = kwargs.pop('session', None)

            if session is None:
                # Get new session
                session = await get_session()

            attempt = 0
            last_error = None

            while attempt <= retry_on_conflict:
                try:
                    # Start transaction
                    async with session.start_transaction():
                        # Execute function within transaction
                        result = await _run_in_session(func, session, *args, **kwargs)

                        # Commit transaction
                        await session.commit_transaction()

                        return result

                except Exception as e:
                    # Check if this is an optimistic concurrency conflict
                    from bson.errors import OperationFailure
                    is_conflict = (
                        isinstance(e, OperationFailure) and
                        "Transaction interrupted" in str(e)
                    )

                    if not is_conflict or attempt >= retry_on_conflict:
                        # Either not a conflict or we've exhausted retries
                        raise

                    # Increment attempt counter
                    attempt += 1

                    # Log conflict
                    logger.warning(
                        f"Optimistic concurrency conflict in transactional function "
                        f"{func.__name__}, attempt {attempt}/{retry_on_conflict}: {e}"
                    )

                    # Optional: wait before retrying
                    # await asyncio.sleep(min(attempt * 0.1, max_retry_delay))

                    # Continue loop to retry
                    continue

            # Should not reach here
            if last_error:
                raise last_error
            raise RuntimeError("Transaction failed after maximum retries")

        return wrapper

    return decorator