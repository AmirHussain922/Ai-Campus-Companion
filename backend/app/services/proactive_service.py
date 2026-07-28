"""
Proactive messaging service for AI Campus Companion.

Manages companion-initiated messages through scheduled triggers and message generation.
Uses APScheduler for background job execution and OpenRouter for AI-generated content.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from bson import ObjectId

from app.companions.companions import companions
from app.core.database import get_database
from app.models import (
    CompanionInitiatedMessageInDB,
    ProactiveMessageResponse,
    ProactiveTriggerInDB,
    ProactiveTriggerType,
    UnreadProactiveMessagesResponse,
)
from app.services.email_service import EmailMessage, EmailService
from app.services.openrouter_client import generate_reply

logger = logging.getLogger(__name__)


# Rate limit constants
MAX_PROACTIVE_MESSAGES_PER_DAY = 3  # Per companion per user per day
MAX_EMAILS_PER_WEEK = 1  # Per user per week


class ProactiveService:
    """Service for managing proactive companion messaging."""

    @staticmethod
    async def schedule_triggers() -> None:
        """
        Run every 6 hours via APScheduler.
        For each user-companion pair, check various conditions and schedule triggers.
        """
        logger.info("Starting proactive trigger scheduling...")

        try:
            db = await get_database()
            now = datetime.now(timezone.utc)

            # Get all users with their companion progression
            users_cursor = db.users.find({"is_active": True})

            async for user in users_cursor:
                user_id = str(user["_id"])
                companion_progression = user.get("companion_progression", [])

                for prog in companion_progression:
                    companion_id = prog.get("companion_id")
                    if not companion_id:
                        continue

                    await ProactiveService._check_and_schedule_triggers(
                        db=db,
                        user_id=user_id,
                        companion_id=companion_id,
                        user=user,
                        progression=prog,
                        now=now,
                    )

            logger.info("Proactive trigger scheduling completed")

        except Exception as e:
            logger.error(f"Error scheduling proactive triggers: {e}", exc_info=True)

    @staticmethod
    async def _check_and_schedule_triggers(
        db: Any,
        user_id: str,
        companion_id: str,
        user: dict,
        progression: dict,
        now: datetime,
    ) -> None:
        """Check all trigger conditions and schedule appropriate triggers."""

        # Check good_morning trigger (8 AM if user mentioned morning class)
        await ProactiveService._check_good_morning_trigger(
            db, user_id, companion_id, user, now
        )

        # Check miss_you trigger (no message in 48+ hours)
        await ProactiveService._check_miss_you_trigger(
            db, user_id, companion_id, now
        )

        # Check milestone_congrats trigger (new level in last 6 hours)
        await ProactiveService._check_milestone_trigger(
            db, user_id, companion_id, progression, now
        )

        # Check story_nudge trigger (in-progress episode, no choice in 24 hours)
        await ProactiveService._check_story_nudge_trigger(
            db, user_id, companion_id, now
        )

    @staticmethod
    async def _check_good_morning_trigger(
        db: Any,
        user_id: str,
        companion_id: str,
        user: dict,
        now: datetime,
    ) -> None:
        """Check and schedule good morning trigger."""
        # Check if already scheduled for today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        existing = await db.proactive_triggers.find_one({
            "user_id": user_id,
            "companion_id": companion_id,
            "trigger_type": ProactiveTriggerType.GOOD_MORNING.value,
            "scheduled_at": {"$gte": today_start},
        })

        if existing:
            return

        # Schedule for 8 AM today (or tomorrow if past 8 AM)
        scheduled_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now.hour >= 8:
            scheduled_time += timedelta(days=1)

        trigger = ProactiveTriggerInDB(
            user_id=user_id,
            companion_id=companion_id,
            trigger_type=ProactiveTriggerType.GOOD_MORNING,
            scheduled_at=scheduled_time,
        )

        await db.proactive_triggers.insert_one(trigger.model_dump(exclude={"id"}))
        logger.info(f"Scheduled good_morning trigger for user {user_id}, companion {companion_id}")

    @staticmethod
    async def _check_miss_you_trigger(
        db: Any,
        user_id: str,
        companion_id: str,
        now: datetime,
    ) -> None:
        """Check and schedule miss_you trigger if no message in 48+ hours."""
        # Find last conversation session
        last_session = await db.conversation_sessions.find_one(
            {"user_id": user_id, "companion_id": companion_id},
            sort=[("ended_at", -1)],
        )

        if not last_session:
            # No conversation yet, skip
            return

        last_interaction = last_session.get("ended_at") or last_session.get("started_at")
        if not last_interaction:
            return

        # Check if 48+ hours have passed
        hours_since_last = (now - last_interaction).total_seconds() / 3600
        if hours_since_last < 48:
            return

        # Check if already scheduled
        existing = await db.proactive_triggers.find_one({
            "user_id": user_id,
            "companion_id": companion_id,
            "trigger_type": ProactiveTriggerType.MISS_YOU.value,
            "is_processed": False,
        })

        if existing:
            return

        trigger = ProactiveTriggerInDB(
            user_id=user_id,
            companion_id=companion_id,
            trigger_type=ProactiveTriggerType.MISS_YOU,
            scheduled_at=now,  # Schedule immediately
            context={"hours_since_last": hours_since_last},
        )

        await db.proactive_triggers.insert_one(trigger.model_dump(exclude={"id"}))
        logger.info(f"Scheduled miss_you trigger for user {user_id}, companion {companion_id}")

    @staticmethod
    async def _check_milestone_trigger(
        db: Any,
        user_id: str,
        companion_id: str,
        progression: dict,
        now: datetime,
    ) -> None:
        """Check and schedule milestone_congrats trigger for new level."""
        # Check if there was a recent level up (in last 6 hours)
        last_level_up = progression.get("last_level_up_at")
        if not last_level_up:
            return

        hours_since_level_up = (now - last_level_up).total_seconds() / 3600
        if hours_since_level_up > 6:
            return

        level = progression.get("level", 1)

        # Check if already scheduled
        existing = await db.proactive_triggers.find_one({
            "user_id": user_id,
            "companion_id": companion_id,
            "trigger_type": ProactiveTriggerType.MILESTONE_CONGRATS.value,
            "is_processed": False,
        })

        if existing:
            return

        trigger = ProactiveTriggerInDB(
            user_id=user_id,
            companion_id=companion_id,
            trigger_type=ProactiveTriggerType.MILESTONE_CONGRATS,
            scheduled_at=now,
            context={"level": level, "level_up_at": last_level_up.isoformat()},
        )

        await db.proactive_triggers.insert_one(trigger.model_dump(exclude={"id"}))
        logger.info(f"Scheduled milestone_congrats trigger for user {user_id}, companion {companion_id}")

    @staticmethod
    async def _check_story_nudge_trigger(
        db: Any,
        user_id: str,
        companion_id: str,
        now: datetime,
    ) -> None:
        """Check and schedule story_nudge trigger for in-progress episode with no choice in 24+ hours."""
        # Find in-progress episode for this companion
        progress = await db.episode_progress.find_one({
            "user_id": user_id,
            "companion_id": companion_id,
            "status": "in_progress",
        })

        if not progress:
            return

        last_choice_at = progress.get("last_choice_at")
        if not last_choice_at:
            return

        hours_since_choice = (now - last_choice_at).total_seconds() / 3600
        if hours_since_choice < 24:
            return

        # Check if already scheduled
        existing = await db.proactive_triggers.find_one({
            "user_id": user_id,
            "companion_id": companion_id,
            "trigger_type": ProactiveTriggerType.STORY_NUDGE.value,
            "is_processed": False,
        })

        if existing:
            return

        episode_id = progress.get("episode_id")
        trigger = ProactiveTriggerInDB(
            user_id=user_id,
            companion_id=companion_id,
            trigger_type=ProactiveTriggerType.STORY_NUDGE,
            scheduled_at=now,
            context={
                "episode_id": episode_id,
                "hours_since_choice": hours_since_choice,
            },
        )

        await db.proactive_triggers.insert_one(trigger.model_dump(exclude={"id"}))
        logger.info(f"Scheduled story_nudge trigger for user {user_id}, companion {companion_id}")

    @staticmethod
    async def process_triggers() -> None:
        """
        Run every 30 minutes via APScheduler.
        Find due unprocessed triggers, generate messages, and mark as processed.
        """
        logger.info("Starting proactive trigger processing...")

        try:
            db = await get_database()
            now = datetime.now(timezone.utc)

            # Find due unprocessed triggers
            due_triggers = db.proactive_triggers.find({
                "is_processed": False,
                "scheduled_at": {"$lte": now},
            })

            processed_count = 0
            async for trigger_doc in due_triggers:
                try:
                    await ProactiveService._process_single_trigger(db, trigger_doc, now)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing trigger {trigger_doc.get('_id')}: {e}")

            logger.info(f"Processed {processed_count} proactive triggers")

        except Exception as e:
            logger.error(f"Error processing proactive triggers: {e}", exc_info=True)

    @staticmethod
    async def _process_single_trigger(
        db: Any,
        trigger_doc: dict,
        now: datetime,
    ) -> None:
        """Process a single trigger and generate message."""
        trigger_id = str(trigger_doc["_id"])
        user_id = trigger_doc["user_id"]
        companion_id = trigger_doc["companion_id"]
        trigger_type = trigger_doc["trigger_type"]
        context = trigger_doc.get("context", {})

        # Check rate limits
        if not await ProactiveService._check_rate_limits(db, user_id, companion_id):
            logger.info(f"Rate limit exceeded for user {user_id}, companion {companion_id}")
            # Mark as processed to avoid retrying
            await db.proactive_triggers.update_one(
                {"_id": ObjectId(trigger_id)},
                {"$set": {"is_processed": True, "processed_at": now, "skipped_reason": "rate_limit"}},
            )
            return

        # Get companion info
        companion = companions.get(companion_id)
        if not companion:
            logger.warning(f"Companion {companion_id} not found")
            return

        # Get user info for email
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            logger.warning(f"User {user_id} not found")
            return

        # Generate message content
        content = await ProactiveService._generate_message_content(
            companion=companion,
            companion_id=companion_id,
            trigger_type=trigger_type,
            context=context,
            user=user,
        )

        # Create conversation session for this proactive message
        from app.models import ConversationSessionInDB
        session = ConversationSessionInDB(
            user_id=user_id,
            companion_id=companion_id,
            messages=[
                {
                    "role": "companion",
                    "content": content,
                    "timestamp": now.isoformat(),
                    "is_proactive": True,
                }
            ],
            is_active=True,
            started_at=now,
        )
        session_result = await db.conversation_sessions.insert_one(
            session.model_dump(exclude={"id"})
        )
        session_id = str(session_result.inserted_id)

        # Store the proactive message
        message = CompanionInitiatedMessageInDB(
            user_id=user_id,
            companion_id=companion_id,
            trigger_type=ProactiveTriggerType(trigger_type),
            content=content,
            conversation_session_id=session_id,
        )
        message_result = await db.companion_initiated_messages.insert_one(
            message.model_dump(exclude={"id"})
        )
        message_id = str(message_result.inserted_id)

        # Send email for miss_you trigger if user inactive 24+ hours
        if trigger_type == ProactiveTriggerType.MISS_YOU.value:
            hours_inactive = context.get("hours_since_last", 0)
            if hours_inactive >= 24:
                await ProactiveService._send_miss_you_email(
                    user=user,
                    companion=companion,
                    companion_id=companion_id,
                    content=content,
                )

        # Mark trigger as processed
        await db.proactive_triggers.update_one(
            {"_id": ObjectId(trigger_id)},
            {"$set": {"is_processed": True, "processed_at": now}},
        )

        logger.info(
            f"Processed trigger {trigger_id}: {trigger_type} message for user {user_id}, "
            f"companion {companion_id}, message_id {message_id}"
        )

    @staticmethod
    async def _check_rate_limits(
        db: Any,
        user_id: str,
        companion_id: str,
    ) -> bool:
        """Check if rate limits allow sending another proactive message."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Count messages sent today for this user-companion pair
        count_today = await db.companion_initiated_messages.count_documents({
            "user_id": user_id,
            "companion_id": companion_id,
            "created_at": {"$gte": today_start},
        })

        return count_today < MAX_PROACTIVE_MESSAGES_PER_DAY

    @staticmethod
    async def _generate_message_content(
        companion: dict,
        companion_id: str,
        trigger_type: str,
        context: dict,
        user: dict,
    ) -> str:
        """Generate message content using OpenRouter."""

        companion_name = companion.get("name", "Companion")
        personality = companion.get("system_prompt", "")

        # Build prompt based on trigger type
        trigger_prompts = {
            ProactiveTriggerType.GOOD_MORNING.value: (
                f"Send a warm good morning message to the user. "
                f"Be encouraging and help them start their day positively. "
                f"Keep it brief (2-3 sentences)."
            ),
            ProactiveTriggerType.MISS_YOU.value: (
                f"The user hasn't chatted in a while. Send a thoughtful message "
                f"checking in on them. Be warm but not pushy. Express that you "
                f"miss talking with them. Keep it to 2-3 sentences."
            ),
            ProactiveTriggerType.MILESTONE_CONGRATS.value: (
                f"The user just reached a new milestone! Send a heartfelt "
                f"congratulations message. Be specific about their achievement "
                f"and encourage them to keep going. 2-3 sentences."
            ),
            ProactiveTriggerType.QUEST_REMINDER.value: (
                f"Gently remind the user about an ongoing quest or task. "
                f"Be encouraging and offer to help if they need it. "
                f"Keep it friendly and brief. 2-3 sentences."
            ),
            ProactiveTriggerType.STORY_NUDGE.value: (
                f"The user has an in-progress story episode. Send a gentle nudge "
                f"to continue their adventure. Build some anticipation about "
                f"what might happen next. 2-3 sentences."
            ),
        }

        prompt_instruction = trigger_prompts.get(
            trigger_type,
            "Send a friendly message to the user. Keep it brief."
        )

        # Build messages for OpenRouter
        messages = [
            {
                "role": "system",
                "content": (
                    f"{personality}\n\n"
                    f"You are {companion_name}, the user's AI companion. "
                    f"You are initiating a conversation with the user. "
                    f"Be authentic to your personality. Be warm, natural, and engaging. "
                    f"Do not use the user's name unless you know it."
                ),
            },
            {
                "role": "user",
                "content": prompt_instruction,
            },
        ]

        try:
            content = await generate_reply(messages=messages)
            return content.strip()
        except Exception as e:
            logger.error(f"Failed to generate message content: {e}")
            # Fallback messages
            fallbacks = {
                ProactiveTriggerType.GOOD_MORNING.value: f"Good morning! I hope you have a wonderful day ahead. Remember, I'm here if you need anything!",
                ProactiveTriggerType.MISS_YOU.value: f"Hey there! I haven't heard from you in a while. How have you been? I'd love to catch up when you have a moment.",
                ProactiveTriggerType.MILESTONE_CONGRATS.value: f"Congratulations on your achievement! I'm so proud of you and all the progress you've made. Keep up the amazing work!",
                ProactiveTriggerType.QUEST_REMINDER.value: f"Just a gentle reminder about your ongoing quest. You're doing great! Let me know if you need any help.",
                ProactiveTriggerType.STORY_NUDGE.value: f"I was just thinking about the story we were exploring together. I'm curious to see what happens next! Want to continue?",
            }
            return fallbacks.get(
                trigger_type,
                f"Hey! Just wanted to check in with you. How are things going?"
            )

    @staticmethod
    async def _send_miss_you_email(
        user: dict,
        companion: dict,
        companion_id: str,
        content: str,
    ) -> None:
        """Send email notification for miss_you trigger."""
        try:
            user_email = user.get("email")
            if not user_email:
                return

            companion_name = companion.get("name", "Your Companion")

            # Check weekly email rate limit
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            db = await get_database()
            recent_emails = await db.proactive_email_logs.count_documents({
                "user_id": str(user["_id"]),
                "sent_at": {"$gte": week_ago},
            })

            if recent_emails >= MAX_EMAILS_PER_WEEK:
                logger.info(f"Weekly email limit reached for user {user['_id']}")
                return

            # Send email
            email_service = EmailService()
            email = EmailMessage(
                to_email=user_email,
                subject=f"{companion_name} misses you!",
                body_text=f"""Hi there,

{content}

Come say hi when you have a moment!

Best,
AI Campus Companion
""",
                body_html=f"""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Hi there,</p>
    <p>{content}</p>
    <p>Come say hi when you have a moment!</p>
    <p>Best,<br>AI Campus Companion</p>
</body>
</html>""",
            )

            await email_service.send_email(email)

            # Log email sent
            await db.proactive_email_logs.insert_one({
                "user_id": str(user["_id"]),
                "companion_id": companion_id,
                "sent_at": datetime.now(timezone.utc),
            })

            logger.info(f"Sent miss_you email to {user_email}")

        except Exception as e:
            logger.error(f"Failed to send miss_you email: {e}")

    # ============================================================================
    # Public API Methods
    # ============================================================================

    @staticmethod
    async def get_unread_proactive_messages(
        user_id: str,
    ) -> list[UnreadProactiveMessagesResponse]:
        """Get unread proactive messages grouped by companion."""
        db = await get_database()

        # Aggregate unread messages by companion
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "is_read": False,
                }
            },
            {
                "$group": {
                    "_id": "$companion_id",
                    "messages": {
                        "$push": {
                            "_id": {"$toString": "$_id"},
                            "companion_id": "$companion_id",
                            "trigger_type": "$trigger_type",
                            "content": "$content",
                            "sent_at": "$created_at",
                            "is_read": "$is_read",
                        }
                    },
                    "unread_count": {"$sum": 1},
                }
            },
        ]

        results = []
        async for doc in db.companion_initiated_messages.aggregate(pipeline):
            companion_id = doc["_id"]
            companion = companions.get(companion_id, {})
            companion_name = companion.get("name", "Unknown Companion")

            messages = [
                ProactiveMessageResponse(**msg)
                for msg in doc["messages"]
            ]

            results.append(
                UnreadProactiveMessagesResponse(
                    companion_id=companion_id,
                    companion_name=companion_name,
                    unread_count=doc["unread_count"],
                    messages=messages,
                )
            )

        return results

    @staticmethod
    async def mark_as_read(message_id: str, user_id: str) -> bool:
        """Mark a proactive message as read."""
        db = await get_database()

        result = await db.companion_initiated_messages.update_one(
            {
                "_id": ObjectId(message_id),
                "user_id": user_id,
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.now(timezone.utc),
                }
            },
        )

        return result.modified_count > 0

    @staticmethod
    async def get_proactive_history(
        user_id: str,
        companion_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Get proactive message history with a companion."""
        db = await get_database()

        skip = (page - 1) * per_page

        # Get total count
        total = await db.companion_initiated_messages.count_documents({
            "user_id": user_id,
            "companion_id": companion_id,
        })

        # Get messages
        messages_cursor = db.companion_initiated_messages.find({
            "user_id": user_id,
            "companion_id": companion_id,
        }).sort("created_at", -1).skip(skip).limit(per_page)

        messages = []
        async for doc in messages_cursor:
            messages.append(
                ProactiveMessageResponse(
                    id=str(doc["_id"]),
                    companion_id=doc["companion_id"],
                    trigger_type=doc["trigger_type"],
                    content=doc["content"],
                    sent_at=doc["created_at"],
                    is_read=doc.get("is_read", False),
                )
            )

        return {
            "messages": messages,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }