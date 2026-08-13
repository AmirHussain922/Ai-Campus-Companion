"""
Health check and monitoring endpoints.

Provides database availability status and system health information.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.utils import is_database_available
from app.core.database import get_database

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Check overall system health.

    Returns:
        System health status including database availability
    """
    from app.core.database import is_database_available as check_db

    db_available = await check_db()

    return {
        "status": "healthy" if db_available else "degraded",
        "database": {
            "available": db_available,
            "service": "MongoDB"
        },
        "rate_limiter": {
            "mode": "emergency" if not db_available else "normal"
        }
    }


@router.get("/health/database")
async def health_database() -> dict:
    """
    Check database connectivity.

    Returns:
        Database connection status
    """
    try:
        db = await get_database()
        if db is None:
            from app.core.utils import set_database_available
            set_database_available(False)
            return {
                "status": "unavailable",
                "message": "Database connection failed"
            }
        from app.core.utils import set_database_available
        set_database_available(True)
        return {
            "status": "healthy",
            "database": "MongoDB"
        }
    except Exception as e:
        from app.core.utils import set_database_available
        set_database_available(False)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unavailable",
                "error": str(e),
                "message": "Database connection failed"
            }
        )


@router.get("/health/ready")
async def readiness_check() -> dict:
    """
    Readiness probe for Kubernetes/Docker.

    Returns:
        True if system is ready to accept traffic
    """
    from app.core.utils import is_database_available as check_db

    if not await check_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    return {
        "status": "ready",
        "database": "available"
    }
