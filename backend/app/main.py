"""
Main application module for AI Campus Companion.

Provides FastAPI application factory with security middleware,
database initialization, route registration, and background worker management.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    _scheduler_available = True
except ImportError:
    _scheduler_available = False
    logging.warning("APScheduler not available - skipping scheduled jobs")

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.database import close_mongo_connection, setup_database_indexes, is_database_available
from app.memory.memory import get_memory_store
from app.core.middleware import setup_security_middleware
from app.core.validation import MaxBodySizeMiddleware
from app.core.error_responses import AppException
from app.core.logging import configure_redacting_filter
from app.core.error_responses import (
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
    create_error_response,
    create_success_response
)

# Import routers
from app.api.auth_routes import router as auth_router
from app.api.chat_routes import router as chat_router
from app.api.health_routes import router as health_router
from app.api.memory_routes import router as memory_router
from app.api.episodes import router as episodes_router
from app.api.journals import router as journals_router
from app.api.proactive import router as proactive_router
from app.api.media import router as media_router
from app.api.study import router as study_router
from app.api.study_buddy import router as study_buddy_router

# Try importing RL routes optionally - SKIP COMPLETELY FOR NOW
rl_router = None
# try:
#     from app.api.rl_routes import router as rl_router
# except Exception:
#     logging.warning("RL routes not available: torch or dependencies not installed")

# Background RL training worker - SKIP COMPLETELY FOR NOW
# try:
#     from app.ml.rl_worker import start_training_worker, stop_training_worker
#     _rl_worker_available = True
# except Exception:
_rl_worker_available = False
logging.warning("RL worker not available - skipping torch imports")

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    # Configure logging with redaction
    from app.core.logging import setup_logging
    setup_logging(log_level="INFO" if settings.debug else "WARNING")

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered campus companion with secure authentication and RL-driven companions",
        version="2.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Initialize scheduler if available
    scheduler = None
    if _scheduler_available:
        scheduler = AsyncIOScheduler()

    # Generate unique request ID for every request
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add request ID to every request for tracking."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Register AppException handler
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle application-specific exceptions."""
        logger.warning(
            f"AppException [{exc.status_code}]: {exc.message}",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "exception_type": exc.__class__.__name__,
                "error_code": exc.error_code
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code or f"HTTP_{exc.status_code}",
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unhandled exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"Unhandled exception: {exc}",
            extra={
                "request_id": request_id,
                "exception_type": type(exc).__name__
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_001",
                "message": "Internal server error",
                "details": {},
                "request_id": request_id
            }
        )

    # Add max body size middleware before security middleware
    app.add_middleware(MaxBodySizeMiddleware, max_size=1_048_576)  # 1MB

    setup_security_middleware(app)

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins + ["http://localhost:5179"],
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers + ["*"],
    )

    # Register routes
    app.include_router(auth_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(memory_router, prefix="/api")
    app.include_router(episodes_router, prefix="/api")
    app.include_router(journals_router, prefix="/api")
    app.include_router(proactive_router, prefix="/api")
    app.include_router(media_router, prefix="/api")
    app.include_router(study_router, prefix="/api")
    app.include_router(study_buddy_router, prefix="/api")

    if rl_router is not None:
        app.include_router(rl_router, prefix="/api")

    @app.get("/")
    async def root():
        return {
            "message": f"{settings.app_name} API is running!",
            "docs": "/docs" if settings.debug else None,
            "version": "2.0.0",
            "status": "healthy",
        }

    @app.get("/health")
    async def health_check():
        db_status = "connected"
        try:
            if await is_database_available():
                db_status = "connected"
            else:
                db_status = "disconnected"
        except Exception:
            db_status = "error"
        
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": settings.app_name,
            "database": db_status,
        }

    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name} v2.0...")

        # Validate CORS origins in development only
        if settings.app_env == "development":
            from app.core.error_responses import AppException
            if settings.cors_allow_origins:
                # Check for localhost
                localhost_origins = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]
                invalid_origins = []

                for origin in settings.cors_allow_origins:
                    origin_lower = origin.lower()
                    for localhost in localhost_origins:
                        if localhost in origin_lower:
                            logger.critical(f"CRITICAL: Localhost origin detected in development CORS: {origin}")
                            logger.critical("Development applications should not use localhost in production.")
                            invalid_origins.append(origin)

                # Reject localhost origins in development
                if invalid_origins:
                    raise AppException(
                        message=f"Development CORS configuration contains invalid origins: {', '.join(invalid_origins)}. "
                               f"Localhost origins ('localhost', '127.0.0.1', '0.0.0.0', '[::1]') should only be used in development.",
                        error_code="CORS_INVALID_ORIGINS",
                        status_code=400
                    )

        try:
            await setup_database_indexes()
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Database setup failed: {e}. Continuing without database.")

        try:
            from app.services.episode_service import EpisodeService
            await EpisodeService.seed_episodes()
            logger.info("Episodes seeded successfully")
        except Exception as e:
            logger.warning(f"Failed to seed episodes: {e}")

        try:
            store = get_memory_store()
            await store.ensure_indexes()
            logger.info("Legacy memory store initialized")
        except Exception as e:
            logger.warning(f"Memory store initialization failed: {e}")

        # Start background RL training worker
        if _rl_worker_available:
            try:
                start_training_worker()
                logger.info("RL training worker started")
            except Exception as e:
                logger.warning(f"RL training worker failed to start: {e}")

        # Start scheduled jobs
        if scheduler is not None:
            try:
                from app.services.journal_service import JournalService
                from app.services.proactive_service import ProactiveService

                # Add daily job at 2 AM for journal generation
                scheduler.add_job(
                    JournalService.generate_all_journals_for_all_users,
                    'cron',
                    hour=2,
                    minute=0,
                    id='daily_journal_generation',
                    replace_existing=True,
                )

                # Add proactive trigger scheduling job (every 6 hours)
                scheduler.add_job(
                    ProactiveService.schedule_triggers,
                    'interval',
                    hours=6,
                    id='proactive_schedule_triggers',
                    replace_existing=True,
                    next_run_time=datetime.now(timezone.utc) + timedelta(minutes=5),  # First run after 5 minutes
                )

                # Add proactive trigger processing job (every 30 minutes)
                scheduler.add_job(
                    ProactiveService.process_triggers,
                    'interval',
                    minutes=30,
                    id='proactive_process_triggers',
                    replace_existing=True,
                    next_run_time=datetime.now(timezone.utc) + timedelta(minutes=10),  # First run after 10 minutes
                )

                # Add daily quest generation job (at 6:00 AM)
                scheduler.add_job(
                    lambda: QuestService.generate_all_daily_quests(),
                    'cron',
                    hour=6,
                    minute=0,
                    id='daily_quest_generation',
                    replace_existing=True,
                )

                scheduler.start()
                logger.info("Scheduled jobs started including proactive messaging and daily quest generation")
            except Exception as e:
                logger.warning(f"Failed to start scheduled jobs: {e}")

        logger.info(
            f"{settings.app_name} started — "
            f"trainable: {settings.trainable_companions}, "
            f"demo: {settings.demo_companions}"
        )

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info(f"Shutting down {settings.app_name}...")

        # Shutdown scheduler
        if scheduler is not None:
            try:
                scheduler.shutdown()
                logger.info("Scheduler stopped")
            except Exception as e:
                logger.warning(f"Failed to stop scheduler: {e}")

        if _rl_worker_available:
            try:
                stop_training_worker()
            except Exception:
                pass

        try:
            await close_mongo_connection()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    return app


app = create_app()
