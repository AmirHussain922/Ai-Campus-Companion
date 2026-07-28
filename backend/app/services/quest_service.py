"""
Campus Quests Service for AI Campus Companion.

Manages daily quest generation, completion verification, and XP rewards.
Uses APScheduler for daily quest generation at 6:00 AM.
Integrates with XP evaluator and RL transitions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from bson import ObjectId

from app.companions.companions import companions
from app.core.database import get_database
from app.models import (
    QuestCompletionResponse,
    QuestHistoryResponse,
    QuestStatus,
    QuestType,
    UserQuestInDB,
    UserQuestResponse,
)
from app.services.openrouter_client import generate_reply

logger = logging.getLogger(__name__)

# Quest templates for daily generation
DAILY_QUEST_TEMPLATES = [
    {
        "quest_id": "daily_study_oliver_pomodoro",
        "title": "Focus Session Challenge",
        "description": "Start a 25-minute focused study session in the Study Room with Oliver.",
        "companion_giver": "study_buddy",
        "quest_type": QuestType.STUDY,
        "xp_reward": 50,
        "verification_method": "auto",
        "trigger_event": "start_study_session",
        "target_count": 1
    },
    {
        "quest_id": "daily_social_chatty",
        "title": "Campus Chat",
        "description": "Send 5 messages in the Campus Lounge or to your companions.",
        "companion_giver": "party_friend",
        "quest_type": QuestType.SOCIAL,
        "xp_reward": 40,
        "verification_method": "auto",
        "trigger_event": "send_message",
        "target_count": 5
    },
    {
        "quest_id": "daily_rivalry_victoria_logic",
        "title": "Logic Duel",
        "description": "Solve this logic puzzle: 'If all Bloops are Razzies, and all Razzies are Lazzies, are all Bloops definitely Lazzies?' Explain your reasoning to Victoria.",
        "companion_giver": "rival",
        "quest_type": QuestType.RIVALRY,
        "xp_reward": 60,
        "verification_method": "openrouter"
    },
    {
        "quest_id": "daily_wellness_julian_walk",
        "title": "Campus Walk & Reflect",
        "description": "Take a 15-minute walk around campus. Notice three things you've never seen before. Mark this quest complete manually when done!",
        "companion_giver": "philosopher",
        "quest_type": QuestType.WELLNESS,
        "xp_reward": 45,
        "verification_method": "manual"
    },
    {
        "quest_id": "daily_study_oliver_notes",
        "title": "Study Helper",
        "description": "Have a 3-message conversation about a study topic in the Study Room's chat.",
        "companion_giver": "study_buddy",
        "quest_type": QuestType.STUDY,
        "xp_reward": 55,
        "verification_method": "auto",
        "trigger_event": "send_study_message",
        "target_count": 3
    },
    {
        "quest_id": "daily_social_chloe_event",
        "title": "Event Explorer",
        "description": "Chat about an event you attended with Chloe. Mark this complete manually!",
        "companion_giver": "party_friend",
        "quest_type": QuestType.SOCIAL,
        "xp_reward": 50,
        "verification_method": "manual"
    },
    {
        "quest_id": "daily_rivalry_victoria_quiz",
        "title": "Knowledge Showdown",
        "description": "Teach Victoria one fact you learned recently. Then ask her to quiz you on something you think she knows well!",
        "companion_giver": "rival",
        "quest_type": QuestType.RIVALRY,
        "xp_reward": 65,
        "verification_method": "openrouter"
    },
    {
        "quest_id": "daily_wellness_julian_breath",
        "title": "Mindful Moment",
        "description": "Try a 5-minute mindfulness exercise and mark this complete manually!",
        "companion_giver": "philosopher",
        "quest_type": QuestType.WELLNESS,
        "xp_reward": 35,
        "verification_method": "manual"
    },
]


class QuestService:
    """Service for managing campus quests."""

    @staticmethod
    async def generate_daily_quests(user_id: str) -> list[UserQuestInDB]:
        """
        Generate daily quests for a user.
        Called daily at 6:00 AM via APScheduler.
        """
        logger.info(f"Generating daily quests for user {user_id}")

        try:
            db = await get_database()
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Check if user already has active quests for today
            existing_count = await db.user_quests.count_documents({
                "user_id": user_id,
                "status": QuestStatus.ACTIVE,
                "started_at": {"$gte": today_start},
            })

            if existing_count > 0:
                logger.info(f"User {user_id} already has active quests for today")
                return []

            # Generate new quests
            created_quests: list[UserQuestInDB] = []

            for template in DAILY_QUEST_TEMPLATES:
                quest = UserQuestInDB(
                    user_id=user_id,
                    quest_id=template["quest_id"],
                    title=template["title"],
                    description=template["description"],
                    companion_giver=template["companion_giver"],
                    quest_type=template["quest_type"],
                    xp_reward=template["xp_reward"],
                    verification_method=template.get("verification_method", "openrouter"),
                    target_count=template.get("target_count"),
                    trigger_event=template.get("trigger_event"),
                    progress_count=0,
                    status=QuestStatus.ACTIVE,
                    started_at=now,
                )

                result = await db.user_quests.insert_one(quest.model_dump(exclude={"id"}))
                quest.id = ObjectId(result.inserted_id)
                created_quests.append(quest)

            logger.info(f"Created {len(created_quests)} daily quests for user {user_id}")
            return created_quests

        except Exception as e:
            logger.error(f"Error generating daily quests for user {user_id}: {e}", exc_info=True)
            return []

    @staticmethod
    async def generate_all_daily_quests() -> None:
        """
        Generate daily quests for all active users.
        Called daily at 6:00 AM via APScheduler.
        """
        logger.info("Starting daily quest generation for all users")

        try:
            db = await get_database()
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Get all active users
            users_cursor = db.users.find({"is_active": True})

            count = 0
            async for user in users_cursor:
                user_id = str(user["_id"])

                # Check if user already has quests for today
                existing = await db.user_quests.find_one({
                    "user_id": user_id,
                    "started_at": {"$gte": today_start},
                })

                if not existing:
                    await QuestService.generate_daily_quests(user_id)
                    count += 1

            logger.info(f"Generated daily quests for {count} users")

        except Exception as e:
            logger.error(f"Error in daily quest generation: {e}", exc_info=True)

    @staticmethod
    async def submit_quest_completion(
        user_id: str,
        quest_id: str,
        report_text: str,
    ) -> QuestCompletionResponse:
        """
        Submit a quest completion report.
        Verifies the report using OpenRouter and awards XP if verified.
        """
        logger.info(f"Quest completion attempt: user={user_id}, quest={quest_id}")

        try:
            db = await get_database()

            # Find the quest
            quest_doc = await db.user_quests.find_one({
                "user_id": user_id,
                "quest_id": quest_id,
                "status": QuestStatus.ACTIVE,
            })

            if not quest_doc:
                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message="Quest not found or not active",
                    can_retry=False,
                )

            quest = UserQuestInDB(**quest_doc)

            # Check retry count
            if quest.retry_count >= 1:
                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message="Maximum retry attempts reached",
                    can_retry=False,
                )

            # Get companion info for verification
            companion = companions.get(quest.companion_giver)
            if not companion:
                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message="Companion not found",
                    can_retry=False,
                )

            # Verify the report using OpenRouter
            is_verified = await QuestService._verify_quest_report(
                companion=companion,
                quest=quest,
                report_text=report_text,
            )

            if is_verified:
                # Mark quest as completed
                now = datetime.now(timezone.utc)
                await db.user_quests.update_one(
                    {"_id": ObjectId(quest.id)},
                    {
                        "$set": {
                            "status": QuestStatus.COMPLETED,
                            "completed_at": now,
                            "user_report_text": report_text,
                            "verification_result": True,
                        }
                    },
                )

                # Award XP via XP evaluator
                from app.ml.xp_evaluator import xp_evaluator
                xp_data = await xp_evaluator.add_quest_completion_xp(
                    user_id=user_id,
                    companion_id=quest.companion_giver,
                    quest_type=quest.quest_type.value,
                    xp_reward=quest.xp_reward,
                )

                # Add RL transition for positive quest completion
                await QuestService._add_quest_rl_transition(
                    user_id=user_id,
                    companion_id=quest.companion_giver,
                    reward=5.0,
                )

                return QuestCompletionResponse(
                    success=True,
                    verified=True,
                    xp_earned=quest.xp_reward,
                    message=f"Quest completed! {companion.get('name', 'Your companion')} is impressed with your effort.",
                    can_retry=False,
                )
            else:
                # Verification failed - allow one retry
                await db.user_quests.update_one(
                    {"_id": ObjectId(quest.id)},
                    {
                        "$inc": {"retry_count": 1},
                        "$set": {
                            "user_report_text": report_text,
                            "verification_result": False,
                        },
                    },
                )

                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message=f"{companion.get('name', 'Your companion')} isn't quite convinced. Please try again with more detail.",
                    can_retry=quest.retry_count == 0,
                )

        except Exception as e:
            logger.error(f"Error submitting quest completion: {e}", exc_info=True)
            return QuestCompletionResponse(
                success=False,
                verified=False,
                xp_earned=0,
                message="An error occurred while processing your quest submission",
                can_retry=True,
            )

    @staticmethod
    async def _verify_quest_report(
        companion: dict,
        quest: UserQuestInDB,
        report_text: str,
    ) -> bool:
        """
        Verify a quest completion report using OpenRouter.
        Returns True if the report is coherent and on-topic.
        """
        try:
            companion_name = companion.get("name", "Companion")
            personality = companion.get("system_prompt", "")

            # Build verification prompt
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"{personality}\n\n"
                        f"You are {companion_name}. You assigned a quest to the user: '{quest.title}'.\n"
                        f"Quest description: {quest.description}\n\n"
                        f"Your task is to verify if the user's completion report is genuine, coherent, and on-topic.\n"
                        f"Be fair but discerning. Short or vague answers should be rejected.\n\n"
                        f"Respond with ONLY a JSON object: {{\"verified\": true/false, \"reason\": \"brief explanation\"}}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"The user submitted this completion report:\n\n{report_text}\n\nPlease verify if this is a genuine completion of the quest.",
                },
            ]

            response = await generate_reply(messages=messages, model="meta-llama/llama-3.1-8b-instruct")

            # Parse JSON response
            try:
                # Extract JSON from response (handle potential markdown code blocks)
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()

                result = json.loads(json_str)
                verified = result.get("verified", False)
                reason = result.get("reason", "No reason provided")

                logger.info(f"Quest verification result: verified={verified}, reason={reason}")
                return verified
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse verification response as JSON: {e}")
                # Fallback: check if response contains positive indicators
                positive_indicators = ["verified", "genuine", "complete", "valid", "true"]
                negative_indicators = ["not verified", "incomplete", "invalid", "false", "rejected"]

                response_lower = response.lower()
                positive_count = sum(1 for indicator in positive_indicators if indicator in response_lower)
                negative_count = sum(1 for indicator in negative_indicators if indicator in response_lower)

                return positive_count > negative_count

        except Exception as e:
            logger.error(f"Error verifying quest report: {e}", exc_info=True)
            return False  # Fail-safe: reject on error

    @staticmethod
    async def _add_quest_rl_transition(
        user_id: str,
        companion_id: str,
        reward: float,
    ) -> None:
        """Add an RL transition for quest completion."""
        try:
            db = await get_database()

            transition = {
                "user_id": user_id,
                "companion_id": companion_id,
                "state": {"quest_completion": True},
                "action": {"type": "complete_quest"},
                "reward": reward,
                "next_state": {"quest_completion": False},
                "done": True,
                "created_at": datetime.now(timezone.utc),
            }

            await db.rl_transitions.insert_one(transition)
            logger.info(f"Added RL transition for quest completion: user={user_id}, reward={reward}")

        except Exception as e:
            logger.error(f"Error adding quest RL transition: {e}", exc_info=True)

    @staticmethod
    async def get_active_quests(user_id: str) -> list[UserQuestResponse]:
        """Get user's active quests for today. Generates quests if none exist."""
        try:
            db = await get_database()
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            cursor = db.user_quests.find({
                "user_id": user_id,
                "status": QuestStatus.ACTIVE,
                "started_at": {"$gte": today_start},
            }).sort("started_at", -1)

            quests = []
            async for doc in cursor:
                quests.append(UserQuestResponse(**doc))

            # If no active quests, generate them
            if not quests:
                await QuestService.generate_daily_quests(user_id)
                # Fetch again
                cursor = db.user_quests.find({
                    "user_id": user_id,
                    "status": QuestStatus.ACTIVE,
                    "started_at": {"$gte": today_start},
                }).sort("started_at", -1)
                quests = []
                async for doc in cursor:
                    quests.append(UserQuestResponse(**doc))

            return quests

        except Exception as e:
            logger.error(f"Error getting active quests: {e}", exc_info=True)
            return []

    @staticmethod
    async def track_quest_progress(user_id: str, event_type: str) -> None:
        """Track quest progress for auto-completion quests triggered by events."""
        logger.info(f"Tracking quest progress for user {user_id}, event: {event_type}")
        
        try:
            db = await get_database()
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Find all active auto quests with matching trigger event
            cursor = db.user_quests.find({
                "user_id": user_id,
                "status": QuestStatus.ACTIVE,
                "verification_method": "auto",
                "trigger_event": event_type,
                "started_at": {"$gte": today_start}
            })
            
            async for doc in cursor:
                quest = UserQuestInDB(**doc)
                quest.progress_count += 1
                
                # Check if target reached
                target_met = quest.target_count is None or quest.progress_count >= quest.target_count
                
                if target_met:
                    # Auto complete
                    quest.status = QuestStatus.COMPLETED
                    quest.completed_at = now
                    
                    # Award XP
                    from app.ml.xp_evaluator import xp_evaluator
                    await xp_evaluator.add_quest_completion_xp(
                        user_id=user_id,
                        companion_id=quest.companion_giver,
                        quest_type=quest.quest_type.value,
                        xp_reward=quest.xp_reward
                    )
                    
                    logger.info(f"Auto completed quest {quest.quest_id} for user {user_id}")
                
                # Update database
                await db.user_quests.update_one(
                    {"_id": ObjectId(quest.id)},
                    {"$set": quest.model_dump(exclude={"id"})}
                )
                
        except Exception as e:
            logger.error(f"Error tracking quest progress: {e}", exc_info=True)

    @staticmethod
    async def submit_quest_completion(
        user_id: str,
        quest_id: str,
        report_text: str,
    ) -> QuestCompletionResponse:
        """
        Submit a quest completion report.
        Verifies the report using OpenRouter and awards XP if verified.
        Handles manual and openrouter verification methods.
        """
        logger.info(f"Quest completion attempt: user={user_id}, quest={quest_id}")

        try:
            db = await get_database()

            # Find the quest
            quest_doc = await db.user_quests.find_one({
                "user_id": user_id,
                "quest_id": quest_id,
                "status": QuestStatus.ACTIVE,
            })

            if not quest_doc:
                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message="Quest not found or not active",
                    can_retry=False,
                )

            quest = UserQuestInDB(**quest_doc)

            # If manual verification, just mark complete
            if quest.verification_method == "manual":
                now = datetime.now(timezone.utc)
                await db.user_quests.update_one(
                    {"_id": ObjectId(quest.id)},
                    {
                        "$set": {
                            "status": QuestStatus.COMPLETED,
                            "completed_at": now,
                            "user_report_text": report_text,
                            "verification_result": True,
                        }
                    },
                )

                # Award XP
                from app.ml.xp_evaluator import xp_evaluator
                await xp_evaluator.add_quest_completion_xp(
                    user_id=user_id,
                    companion_id=quest.companion_giver,
                    quest_type=quest.quest_type.value,
                    xp_reward=quest.xp_reward,
                )

                return QuestCompletionResponse(
                    success=True,
                    verified=True,
                    xp_earned=quest.xp_reward,
                    message="Quest marked complete! Great job!",
                    can_retry=False,
                )

            # Check retry count
            if quest.retry_count >= 1:
                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message="Maximum retry attempts reached",
                    can_retry=False,
                )

            # Get companion info for verification
            companion = companions.get(quest.companion_giver)
            if not companion:
                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message="Companion not found",
                    can_retry=False,
                )

            # Verify the report using OpenRouter
            is_verified = await QuestService._verify_quest_report(
                companion=companion,
                quest=quest,
                report_text=report_text,
            )

            if is_verified:
                # Mark quest as completed
                now = datetime.now(timezone.utc)
                await db.user_quests.update_one(
                    {"_id": ObjectId(quest.id)},
                    {
                        "$set": {
                            "status": QuestStatus.COMPLETED,
                            "completed_at": now,
                            "user_report_text": report_text,
                            "verification_result": True,
                        }
                    },
                )

                # Award XP via XP evaluator
                from app.ml.xp_evaluator import xp_evaluator
                xp_data = await xp_evaluator.add_quest_completion_xp(
                    user_id=user_id,
                    companion_id=quest.companion_giver,
                    quest_type=quest.quest_type.value,
                    xp_reward=quest.xp_reward,
                )

                # Add RL transition for positive quest completion
                await QuestService._add_quest_rl_transition(
                    user_id=user_id,
                    companion_id=quest.companion_giver,
                    reward=5.0,
                )

                return QuestCompletionResponse(
                    success=True,
                    verified=True,
                    xp_earned=quest.xp_reward,
                    message=f"Quest completed! {companion.get('name', 'Your companion')} is impressed with your effort.",
                    can_retry=False,
                )
            else:
                # Verification failed - allow one retry
                await db.user_quests.update_one(
                    {"_id": ObjectId(quest.id)},
                    {
                        "$inc": {"retry_count": 1},
                        "$set": {
                            "user_report_text": report_text,
                            "verification_result": False,
                        },
                    },
                )

                return QuestCompletionResponse(
                    success=False,
                    verified=False,
                    xp_earned=0,
                    message=f"{companion.get('name', 'Your companion')} isn't quite convinced. Please try again with more detail.",
                    can_retry=quest.retry_count == 0,
                )

        except Exception as e:
            logger.error(f"Error submitting quest completion: {e}", exc_info=True)
            return QuestCompletionResponse(
                success=False,
                verified=False,
                xp_earned=0,
                message="An error occurred while processing your quest submission",
                can_retry=True,
            )

    @staticmethod
    async def get_quest_history(user_id: str) -> QuestHistoryResponse:
        """Get user's quest history."""
        try:
            db = await get_database()

            # Get all quests for user
            cursor = db.user_quests.find({"user_id": user_id}).sort("started_at", -1)

            active = []
            completed = []
            failed = []

            async for doc in cursor:
                quest = UserQuestResponse(**doc)
                if quest.status == QuestStatus.ACTIVE:
                    active.append(quest)
                elif quest.status == QuestStatus.COMPLETED:
                    completed.append(quest)
                elif quest.status == QuestStatus.FAILED:
                    failed.append(quest)

            return QuestHistoryResponse(
                active=active,
                completed=completed,
                failed=failed,
            )

        except Exception as e:
            logger.error(f"Error getting quest history: {e}", exc_info=True)
            return QuestHistoryResponse(active=[], completed=[], failed=[])