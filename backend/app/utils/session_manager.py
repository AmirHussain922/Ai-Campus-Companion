"""
Conversation session manager for AI Campus Companion.

Manages creation, retrieval, and closing of conversation sessions.
Each session tracks messages, XP earned, relationship changes, and RL actions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database

logger = logging.getLogger(__name__)


async def get_or_create_session(
    *,
    user_id: str,
    companion_id: str,
    episode_id: str | None = None,
) -> dict:
    """Get the current active session or create a new one.

    Returns the session document as a dict.
    """
    db = await get_database()
    col = db.conversation_sessions

    # Try to find an active session for this user + companion
    existing = await col.find_one(
        {
            "user_id": user_id,
            "companion_id": companion_id,
            "is_active": True,
        },
        sort=[("started_at", -1)],
    )
    if existing is not None:
        return existing

    # Create new session
    doc = {
        "user_id": user_id,
        "companion_id": companion_id,
        "messages": [],
        "xp_earned": 0,
        "relationship_delta": 0,
        "rl_actions_taken": [],
        "episode_id": episode_id,
        "started_at": datetime.now(timezone.utc),
        "ended_at": None,
        "is_active": True,
    }
    result = await col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def append_message_to_session(
    *,
    session_id: str,
    role: str,
    content: str,
) -> None:
    """Append a message to an existing session."""
    db = await get_database()
    msg = {"role": role, "content": content, "timestamp": datetime.now(timezone.utc).isoformat()}
    await db.conversation_sessions.update_one(
        {"_id": session_id},
        {"$push": {"messages": msg}},
    )


async def append_rl_action(
    *,
    session_id: str,
    action_dict: dict,
) -> None:
    """Record an RL action taken during the session."""
    db = await get_database()
    await db.conversation_sessions.update_one(
        {"_id": session_id},
        {"$push": {"rl_actions_taken": action_dict}},
    )


async def update_session_xp(
    *,
    session_id: str,
    xp_delta: int,
    relationship_delta: int,
) -> None:
    """Increment XP and relationship deltas on a session."""
    db = await get_database()
    await db.conversation_sessions.update_one(
        {"_id": session_id},
        {
            "$inc": {
                "xp_earned": xp_delta,
                "relationship_delta": relationship_delta,
            }
        },
    )


async def close_session(*, session_id: str) -> None:
    """Mark a session as ended."""
    db = await get_database()
    await db.conversation_sessions.update_one(
        {"_id": session_id},
        {
            "$set": {
                "is_active": False,
                "ended_at": datetime.now(timezone.utc),
            }
        },
    )


async def get_session_messages(
    *,
    user_id: str,
    companion_id: str,
    limit: int = 20,
) -> list[dict]:
    """Get recent messages from the latest active session."""
    db = await get_database()
    session = await db.conversation_sessions.find_one(
        {
            "user_id": user_id,
            "companion_id": companion_id,
            "is_active": True,
        },
        sort=[("started_at", -1)],
    )
    if not session:
        return []
    messages = session.get("messages", [])
    return messages[-limit:]


async def get_user_sessions(
    *,
    user_id: str,
    companion_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Get session history for a user, optionally filtered by companion."""
    db = await get_database()
    query: dict = {"user_id": user_id}
    if companion_id:
        query["companion_id"] = companion_id
    cursor = db.conversation_sessions.find(query).sort("started_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
