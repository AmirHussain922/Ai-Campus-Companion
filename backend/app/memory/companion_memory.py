"""
High-level companion memory operations for trainable companions.

Provides a simple interface for storing and retrieving memories,
managing feedback, and handling scenario/story memories.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.memory.companion_memory_store import (
    CompanionMemoryRecord,
    add_companion_memory,
    get_recent_memories,
    search_companion_memories,
)
from app.memory.embedding_client import embed_text
from app.services.openrouter_client import OpenRouterError

logger = logging.getLogger(__name__)


async def remember_fact(
    *,
    user_id: str,
    companion_id: str,
    content: str,
    source: str = "conversation",
) -> str:
    """Store an important fact about the user."""
    return await add_companion_memory(
        user_id=user_id,
        companion_id=companion_id,
        memory_type="fact",
        content=content,
        metadata={"source": source, "kind": "important_fact"},
        importance=2.0,
    )


async def remember_conversation_exchange(
    *,
    user_id: str,
    companion_id: str,
    user_message: str,
    companion_reply: str,
) -> None:
    """Store a conversation exchange as a memory."""
    combined = f"User: {user_message}\nCompanion: {companion_reply}"
    await add_companion_memory(
        user_id=user_id,
        companion_id=companion_id,
        memory_type="conversation",
        content=combined,
        metadata={"role": "exchange"},
        importance=1.0,
    )


async def store_feedback_memory(
    *,
    user_id: str,
    companion_id: str,
    rating: int,
    user_message: str | None = None,
    assistant_message: str | None = None,
) -> str:
    """Store user feedback as a memory for the trainable companion."""
    label = "GOOD" if rating == 1 else "BAD"
    parts = [f"User feedback: {label}"]
    if user_message:
        parts.append(f"User message: {user_message}")
    if assistant_message:
        parts.append(f"Assistant reply: {assistant_message}")

    return await add_companion_memory(
        user_id=user_id,
        companion_id=companion_id,
        memory_type="feedback",
        content="\n".join(parts),
        metadata={"kind": "feedback", "rating": rating},
        importance=3.0 if rating == -1 else 2.0,
    )


async def store_scenario_memory(
    *,
    user_id: str,
    companion_id: str,
    title: str,
    scenario: str,
    backstory: str,
    narration: str,
) -> str:
    """Store a scenario/story unlock as a memory."""
    content = (
        f"{title}\n\n"
        f"Scenario:\n{scenario}\n\n"
        f"Backstory:\n{backstory}\n\n"
        f"Narration:\n{narration}"
    )
    return await add_companion_memory(
        user_id=user_id,
        companion_id=companion_id,
        memory_type="story",
        content=content,
        metadata={"title": title, "kind": "scenario"},
        importance=3.0,
    )


async def get_relevant_memories(
    *,
    user_id: str,
    companion_id: str,
    query: str,
    k: int = 5,
) -> list[CompanionMemoryRecord]:
    """Semantic search for relevant memories."""
    try:
        query_vec = await embed_text(text=query)
        return await search_companion_memories(
            user_id=user_id,
            companion_id=companion_id,
            query_embedding=query_vec,
            k=k,
        )
    except OpenRouterError as e:
        logger.warning(f"Failed to embed query for memory search: {e}")
        return []


async def get_latest_scenario(
    *,
    user_id: str,
    companion_id: str,
) -> Optional[CompanionMemoryRecord]:
    """Get the most recent scenario/story memory."""
    memories = await get_recent_memories(
        user_id=user_id,
        companion_id=companion_id,
        memory_type="story",
        limit=1,
    )
    return memories[0] if memories else None


async def get_recent_feedback(
    *,
    user_id: str,
    companion_id: str,
    limit: int = 3,
) -> list[CompanionMemoryRecord]:
    """Get recent feedback memories."""
    return await get_recent_memories(
        user_id=user_id,
        companion_id=companion_id,
        memory_type="feedback",
        limit=limit,
    )
