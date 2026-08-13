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
from app.core.utils import set_database_available

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
            set_database_available(True)
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            set_database_available(False)
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
        # Lowercase all existing emails to ensure consistency
        # This is a one-time migration step
        users_coll = db.users
        cursor = users_coll.find({"email": {"$regex": "[A-Z]"}})
        async for user in cursor:
            old_email = user["email"]
            new_email = old_email.lower()
            logger.info(f"Normalizing email: {old_email} -> {new_email}")
            await users_coll.update_one({"_id": user["_id"]}, {"$set": {"email": new_email}})

        # Users collection indexes
        # Use collation for case-insensitive unique index
        from pymongo.collation import Collation
        email_collation = Collation(locale="en", strength=2)
        
        # Drop old index if it exists without collation to update it
        try:
            await db.users.drop_index("email_1")
        except Exception:
            pass

        await db.users.create_index(
            "email", 
            unique=True, 
            background=True,
            collation=email_collation
        )
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

        # Additional database indexes for performance and security
        # User progression index for efficient queries
        await db.users.create_index(
            [("companion_progression.companion_id", 1), ("_id", 1)],
            background=True
        )
        logger.info("User companion progression index created")

        # Quest indexes for efficient querying
        await db.user_quests.create_index(
            [("status", 1), ("created_at", -1)],
            background=True
        )
        logger.info("User quests status index created")

        # Session indexes for performance
        await db.conversation_sessions.create_index(
            [("user_id", 1), ("is_active", 1), ("started_at", -1)],
            background=True
        )
        logger.info("Conversation sessions index created")

        # Study buddy profile indexes
        await db.study_buddy_profiles.create_index(
            [("user_id", 1)],
            unique=True,
            background=True
        )
        await db.study_buddy_profiles.create_index(
            [("is_online", 1), ("last_active", -1)],
            background=True
        )
        logger.info("Study buddy profiles indexes created")

        # Buddy requests indexes
        await db.buddy_requests.create_index(
            [("user_id", 1), ("status", 1)],
            background=True
        )
        await db.buddy_requests.create_index(
            [("requested_at", -1)],
            background=True
        )
        logger.info("Buddy requests indexes created")

        # Study buddy conversations indexes (one-to-one per user pair)
        await db.study_buddy_conversations.create_index(
            [("user_a_id", 1), ("user_b_id", 1)],
            unique=True,
            background=True
        )
        await db.study_buddy_conversations.create_index(
            [("user_b_id", 1), ("user_a_id", 1)],
            unique=True,
            background=True
        )
        logger.info("Study buddy conversations indexes created")

        # Study buddy messages indexes
        await db.study_buddy_messages.create_index(
            [("conversation_id", 1), ("created_at", -1)],
            background=True
        )
        await db.study_buddy_messages.create_index(
            [("conversation_id", 1), ("is_read", 1)],
            background=True
        )
        await db.study_buddy_messages.create_index(
            ["created_at"],
            expireAfterSeconds=7776000,  # 90 days TTL for messages
            background=True
        )
        logger.info("Study buddy messages indexes created")

        # Q&A questions indexes
        await db.qa_questions.create_index(
            [("subject", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_questions.create_index(
            [("author_id", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_questions.create_index(
            ["created_at"],
            expireAfterSeconds=7776000,  # 90 days TTL
            background=True
        )
        logger.info("Q&A questions indexes created")

        # Q&A answers indexes
        await db.qa_answers.create_index(
            [("question_id", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_answers.create_index(
            [("author_id", 1), ("created_at", -1)],
            background=True
        )
        logger.info("Q&A answers indexes created")

        # Q&A comments indexes
        await db.qa_comments.create_index(
            [("question_id", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_comments.create_index(
            [("author_id", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_comments.create_index(
            [("parent_id", 1)],
            background=True
        )
        logger.info("Q&A comments indexes created")

        # Study rooms indexes
        await db.study_rooms.create_index(
            [("host_id", 1), ("status", 1)],
            background=True
        )
        await db.study_rooms.create_index(
            [("status", 1), ("created_at", -1)],
            background=True
        )
        logger.info("Study rooms indexes created")

        # Study room messages indexes
        await db.study_room_messages.create_index(
            [("room_id", 1), ("created_at", -1)],
            background=True
        )
        await db.study_room_messages.create_index(
            [("room_id", 1), ("is_read", 1)],
            background=True
        )
        await db.study_room_messages.create_index(
            "created_at",
            expireAfterSeconds=7776000,  # 90 days TTL for messages
            background=True
        )
        logger.info("Study room messages indexes created")

        # Q&A posts indexes
        await db.qa_posts.create_index(
            [("subject", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_posts.create_index(
            [("user_id", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_posts.create_index(
            [("question_type", 1), ("created_at", -1)],
            background=True
        )
        await db.qa_posts.create_index(
            [("tags", 1)],
            background=True
        )
        logger.info("Q&A posts indexes created")

        # Ensure OTP TTL index (already created but re-verify)
        await db.otps.create_index(
            "expires_at",
            expireAfterSeconds=0,
            background=True
        )
        logger.info("OTPs TTL index verified")

        # Revoked tokens collection (for refresh token rotation)
        await db.revoked_tokens.create_index("expires_at", expireAfterSeconds=0, background=True)
        await db.revoked_tokens.create_index("family", background=True)  # For revoking entire token families
        await db.revoked_tokens.create_index([("user_id", 1), ("family", 1)], background=True)  # Compound index
        logger.info("Revoked tokens collection indexes created")

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


async def get_revoked_tokens_collection():
    """Get revoked tokens collection."""
    db = await get_database()
    return db.revoked_tokens


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


async def get_study_buddy_conversations_collection():
    """Get study buddy conversations collection."""
    db = await get_database()
    return db.study_buddy_conversations


async def get_study_buddy_messages_collection():
    """Get study buddy messages collection."""
    db = await get_database()
    return db.study_buddy_messages


async def get_qa_questions_collection():
    """Get Q&A questions collection."""
    db = await get_database()
    return db.qa_questions


async def get_qa_answers_collection():
    """Get Q&A answers collection."""
    db = await get_database()
    return db.qa_answers


async def get_qa_comments_collection():
    """Get Q&A comments collection."""
    db = await get_database()
    return db.qa_comments


async def get_study_rooms_collection():
    """Get study rooms collection."""
    db = await get_database()
    return db.study_rooms


async def get_study_room_messages_collection():
    """Get study room messages collection."""
    db = await get_database()
    return db.study_room_messages
