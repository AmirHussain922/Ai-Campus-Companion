"""
Journal service for generating and managing companion journal entries.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.companions.companions import companions
from app.core.database import (
    get_companion_journals_collection,
    get_conversation_sessions_collection,
    get_users_collection,
)
from app.models import JournalEntryInDB
from app.services.openrouter_client import generate_reply

logger = logging.getLogger(__name__)

# Stage names for prompts
STAGE_NAMES = ["Stranger", "Curious", "Friend", "Close Friend", "Confidant"]

# Companion personality configurations for journal generation
COMPANION_PERSONALITIES = {
    "philosopher": {
        "name": "Julian",
        "description": "a brooding, philosophical writer who questions everything about knowledge, truth, and meaning",
        "style": "Use metaphorical language, deep introspection, and existential questions. Keep it intimate and personal.",
    },
    "rival": {
        "name": "Victoria",
        "description": "a sharp, competitive, ambitious academic rival who has a reluctant, hidden vulnerability",
        "style": "Be direct, sharp, and competitive, but show a subtle, soft undercurrent. Keep it concise and to the point.",
    },
    "study_buddy": {
        "name": "Oliver",
        "description": "a supportive, organized study partner who focuses on academic goals and practical help",
        "style": "Be warm, supportive, and organized. Mention study-related topics and goals.",
    },
    "party_friend": {
        "name": "Chloe",
        "description": "an energetic, social life-of-the-party who uses casual slang and focuses on social life",
        "style": "Use casual, friendly slang, keep it upbeat and energetic, focus on social events and connections.",
    },
    "freshman": {
        "name": "Toby",
        "description": "a nervous but earnest freshman who looks up to the user and is new to college life",
        "style": "Be nervous, earnest, and a bit shy. Show admiration for the user and focus on college experiences.",
    },
}


class JournalService:
    """Service class for managing companion journal entries."""

    @staticmethod
    async def generate_journal_entry(user_id: str, companion_id: str, stage: int) -> Optional[JournalEntryInDB]:
        """Generate a private journal entry for a companion at a specific stage."""
        journals_collection = await get_companion_journals_collection()
        
        # Check if entry already exists
        existing = await journals_collection.find_one({
            "user_id": user_id,
            "companion_id": companion_id,
            "stage": stage,
        })
        if existing:
            return JournalEntryInDB(**existing)

        # Fetch last 20 messages from conversation history
        conv_collection = await get_conversation_sessions_collection()
        messages = []
        cursor = conv_collection.find({
            "user_id": user_id,
            "companion_id": companion_id,
        }).sort("started_at", -1).limit(10)  # Check last 10 sessions for messages
        
        async for session in cursor:
            session_messages = session.get("messages", [])
            messages.extend(session_messages[-10:])  # Take last 10 messages per session
            if len(messages) >= 20:
                break
        
        # Take last 5 messages for context
        last_messages = messages[-5:] if messages else []
        formatted_context = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in last_messages])
        
        # Get user's name
        users_collection = await get_users_collection()
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        user_name = user.get("full_name", "Friend") if user else "Friend"
        
        # Get companion config
        companion_config = companions.get(companion_id, {})
        companion_name = companion_config.get("name", companion_id)
        personality_config = COMPANION_PERSONALITIES.get(companion_id, {})
        personality_name = personality_config.get("name", companion_name)
        personality_desc = personality_config.get("description", "")
        personality_style = personality_config.get("style", "")
        
        # Build prompt
        prompt = f"""You are {personality_name}, {personality_desc}.
Write a private diary entry (2-3 sentences, under 300 characters) about your relationship with {user_name}.
Your relationship stage is: {STAGE_NAMES[stage]}.

Recent conversation context:
{formatted_context if formatted_context else "No recent conversations yet."}

{personality_style}

Journal entry:"""
        
        # Generate entry using OpenRouter
        try:
            entry_text = await generate_reply(
                messages=[{"role": "user", "content": prompt}],
            )
            # Clean up the entry
            entry_text = entry_text.strip().strip('"').strip("'").strip()
            
            # Get user's current stage for this companion
            current_stage_int = 0
            if user:
                companion_progression = next(
                    (cp for cp in user.get("companion_progression", []) if cp.get("companion_id") == companion_id),
                    None
                )
                if companion_progression:
                    user_stage = companion_progression.get("relationship_stage", "Stranger")
                    current_stage_int = STAGE_NAMES.index(user_stage) if user_stage in STAGE_NAMES else 0
            
            # Create journal entry
            journal_entry = JournalEntryInDB(
                user_id=user_id,
                companion_id=companion_id,
                stage=stage,
                entry_text=entry_text,
                is_unlocked=stage <= current_stage_int,
                unlocked_at=datetime.utcnow() if stage <= current_stage_int else None,
            )
            
            # Save to database
            await journals_collection.insert_one(journal_entry.model_dump(by_alias=True))
            return journal_entry
            
        except Exception as e:
            logger.error(f"Failed to generate journal entry for {companion_id} stage {stage}: {e}")
            return None

    @staticmethod
    async def get_unlocked_journals(user_id: str, companion_id: str) -> list[JournalEntryInDB]:
        """Get all unlocked journal entries for a user and companion, sorted by stage."""
        journals_collection = await get_companion_journals_collection()
        cursor = journals_collection.find({
            "user_id": user_id,
            "companion_id": companion_id,
            "is_unlocked": True,
        }).sort("stage", 1)
        
        entries = []
        async for doc in cursor:
            entries.append(JournalEntryInDB(**doc))
        return entries

    @staticmethod
    async def get_journal_entry(user_id: str, companion_id: str, stage: int) -> Optional[JournalEntryInDB]:
        """Get a specific journal entry by stage."""
        journals_collection = await get_companion_journals_collection()
        doc = await journals_collection.find_one({
            "user_id": user_id,
            "companion_id": companion_id,
            "stage": stage,
        })
        return JournalEntryInDB(**doc) if doc else None

    @staticmethod
    async def mark_journal_as_read(user_id: str, companion_id: str, stage: int) -> Optional[JournalEntryInDB]:
        """Mark a journal entry as read."""
        journals_collection = await get_companion_journals_collection()
        result = await journals_collection.update_one(
            {"user_id": user_id, "companion_id": companion_id, "stage": stage},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        if result.matched_count > 0:
            doc = await journals_collection.find_one({
                "user_id": user_id,
                "companion_id": companion_id,
                "stage": stage,
            })
            return JournalEntryInDB(**doc) if doc else None
        return None

    @staticmethod
    async def check_and_generate_journals(user_id: str, companion_id: str) -> None:
        """Check and generate missing journal entries for all stages 0-4."""
        for stage in range(5):
            await JournalService.generate_journal_entry(user_id, companion_id, stage)

    @staticmethod
    async def unlock_journals_up_to_stage(user_id: str, companion_id: str, stage: int) -> None:
        """Unlock all journal entries up to and including the given stage."""
        journals_collection = await get_companion_journals_collection()
        await journals_collection.update_many(
            {
                "user_id": user_id,
                "companion_id": companion_id,
                "stage": {"$lte": stage},
                "is_unlocked": False,
            },
            {
                "$set": {
                    "is_unlocked": True,
                    "unlocked_at": datetime.utcnow(),
                }
            }
        )

    @staticmethod
    async def generate_all_journals_for_all_users() -> None:
        """Generate missing journals for all user-companion pairs (scheduled job)."""
        logger.info("Starting scheduled journal generation for all users...")
        try:
            users_collection = await get_users_collection()
            cursor = users_collection.find({})
            async for user in cursor:
                user_id = str(user["_id"])
                companion_progression = user.get("companion_progression", [])
                for cp in companion_progression:
                    companion_id = cp.get("companion_id")
                    if companion_id:
                        await JournalService.check_and_generate_journals(user_id, companion_id)
            logger.info("Completed scheduled journal generation")
        except Exception as e:
            logger.error(f"Failed to run scheduled journal generation: {e}")
