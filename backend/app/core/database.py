"""
Database module for AI Campus Companion.

Provides MongoDB connection management, database access, and index creation
for all collections including users, OTPs, token blacklist, and rate limits.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create the MongoDB client."""
    global _client
    if _client is None:
        settings = get_settings()
        try:
            _client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
            )
            # Verify connection
            await _client.admin.command('ping')
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}. Running without database.")
            _client = None
    return _client


async def get_database() -> AsyncIOMotorDatabase:
    """Get or create the database."""
    global _database
    if _database is None:
        settings = get_settings()
        client = await get_mongo_client()
        if client is None:
            raise RuntimeError("MongoDB client is not available. Please ensure MongoDB is running and MONGODB_URI is correctly configured.")
        _database = client[settings.mongodb_db]
        logger.info(f"Database '{settings.mongodb_db}' initialized")
    return _database


async def is_database_available() -> bool:
    """Check if database connection is available."""
    try:
        client = await get_mongo_client()
        if client is None:
            return False
        await client.admin.command('ping')
        return True
    except Exception:
        return False


async def setup_database_indexes() -> None:
    """
    Set up all required database indexes.

    Creates indexes for:
    - users: unique email index
    - otps: TTL index for automatic expiration, compound index on email+purpose
    - token_blacklist: TTL index for automatic cleanup, unique token_jti index
    - rate_limits: TTL index for automatic cleanup, key index
    """
    db = await get_database()

    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True, background=True)
        await db.users.create_index("created_at", background=True)
        await db.users.create_index([("is_verified", 1), ("is_active", 1)], background=True)
        logger.info("Users collection indexes created")

        # OTPs collection indexes
        # TTL index for automatic expiration
        await db.otps.create_index(
            "expires_at",
            expireAfterSeconds=0,
            background=True
        )
        # Compound index for efficient lookups
        await db.otps.create_index(
            [("email", 1), ("purpose", 1)],
            background=True
        )
        logger.info("OTPs collection indexes created")

        # Token blacklist collection indexes
        # TTL index for automatic cleanup
        await db.token_blacklist.create_index(
            "expires_at",
            expireAfterSeconds=0,
            background=True
        )
        # Unique index on token JTI
        await db.token_blacklist.create_index(
            "token_jti",
            unique=True,
            background=True
        )
        logger.info("Token blacklist collection indexes created")

        # Rate limits collection indexes
        # TTL index for automatic cleanup
        await db.rate_limits.create_index(
            "expires_at",
            expireAfterSeconds=0,
            background=True
        )
        # Index for key lookups
        await db.rate_limits.create_index(
            "key",
            background=True
        )
        logger.info("Rate limits collection indexes created")

        # Conversation sessions collection indexes
        await db.conversation_sessions.create_index(
            [("user_id", 1), ("companion_id", 1), ("started_at", -1)],
            background=True,
        )
        await db.conversation_sessions.create_index(
            [("user_id", 1), ("companion_id", 1), ("is_active", 1)],
            background=True,
        )
        logger.info("Conversation sessions collection indexes created")

        # RL transitions collection indexes
        await db.rl_transitions.create_index(
            [("companion_id", 1), ("created_at", -1)],
            background=True,
        )
        await db.rl_transitions.create_index(
            [("user_id", 1), ("companion_id", 1)],
            background=True,
        )
        logger.info("RL transitions collection indexes created")

        # Companion memories collection indexes
        await db.companion_memories.create_index(
            [("user_id", 1), ("companion_id", 1), ("created_at", -1)],
            background=True,
        )
        await db.companion_memories.create_index(
            [("user_id", 1), ("companion_id", 1), ("memory_type", 1)],
            background=True,
        )
        logger.info("Companion memories collection indexes created")

        # Episodes collection indexes
        await db.episodes.create_index(
            [("companion_id", 1), ("required_relationship_stage", 1)],
            background=True,
        )
        logger.info("Episodes collection indexes created")

        # Episode progress collection indexes
        await db.episode_progress.create_index(
            [("user_id", 1), ("companion_id", 1)],
            background=True,
        )
        await db.episode_progress.create_index(
            [("user_id", 1), ("episode_id", 1)],
            unique=True,
            background=True,
        )
        logger.info("Episode progress collection indexes created")

        # Companion journals collection indexes
        await db.companion_journals.create_index(
            [("user_id", 1), ("companion_id", 1), ("stage", 1)],
            unique=True,
            background=True,
        )
        await db.companion_journals.create_index(
            [("user_id", 1), ("companion_id", 1)],
            background=True,
        )
        logger.info("Companion journals collection indexes created")

        # Proactive triggers collection indexes
        await db.proactive_triggers.create_index(
            [("user_id", 1), ("companion_id", 1), ("trigger_type", 1)],
            background=True,
        )
        await db.proactive_triggers.create_index(
            [("is_processed", 1), ("scheduled_at", 1)],
            background=True,
        )
        await db.proactive_triggers.create_index(
            "created_at",
            expireAfterSeconds=2592000,  # 30 days TTL
            background=True,
        )
        logger.info("Proactive triggers collection indexes created")

        # Companion initiated messages collection indexes
        await db.companion_initiated_messages.create_index(
            [("user_id", 1), ("companion_id", 1), ("is_read", 1)],
            background=True,
        )
        await db.companion_initiated_messages.create_index(
            [("user_id", 1), ("created_at", -1)],
            background=True,
        )
        await db.companion_initiated_messages.create_index(
            "created_at",
            expireAfterSeconds=7776000,  # 90 days TTL
            background=True,
        )
        logger.info("Companion initiated messages collection indexes created")

        # Proactive email logs collection indexes
        await db.proactive_email_logs.create_index(
            [("user_id", 1), ("sent_at", -1)],
            background=True,
        )
        await db.proactive_email_logs.create_index(
            "sent_at",
            expireAfterSeconds=2592000,  # 30 days TTL
            background=True,
        )
        logger.info("Proactive email logs collection indexes created")

        logger.info("All database indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        raise


async def close_mongo_connection() -> None:
    """Close the MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("MongoDB connection closed")


@asynccontextmanager
async def get_db_context():
    """Context manager for database operations."""
    db = await get_database()
    try:
        yield db
    except Exception:
        raise


# Collection helper functions for type hints
async def get_users_collection():
    """Get users collection."""
    db = await get_database()
    return db.users


async def get_otps_collection():
    """Get OTPs collection."""
    db = await get_database()
    return db.otps


async def get_token_blacklist_collection():
    """Get token blacklist collection."""
    db = await get_database()
    return db.token_blacklist


async def get_rate_limits_collection():
    """Get rate limits collection."""
    db = await get_database()
    return db.rate_limits


async def get_conversation_sessions_collection():
    """Get conversation sessions collection."""
    db = await get_database()
    return db.conversation_sessions


async def get_rl_transitions_collection():
    """Get RL transitions collection."""
    db = await get_database()
    return db.rl_transitions


async def get_companion_memories_collection():
    """Get companion memories collection."""
    db = await get_database()
    return db.companion_memories


async def get_episodes_collection():
    """Get episodes collection."""
    db = await get_database()
    return db.episodes


async def get_episode_progress_collection():
    """Get episode progress collection."""
    db = await get_database()
    return db.episode_progress


async def get_companion_journals_collection():
    """Get companion journals collection."""
    db = await get_database()
    return db.companion_journals


async def get_proactive_triggers_collection():
    """Get proactive triggers collection."""
    db = await get_database()
    return db.proactive_triggers


async def get_companion_initiated_messages_collection():
    """Get companion initiated messages collection."""
    db = await get_database()
    return db.companion_initiated_messages


async def get_proactive_email_logs_collection():
    """Get proactive email logs collection."""
    db = await get_database()
    return db.proactive_email_logs
