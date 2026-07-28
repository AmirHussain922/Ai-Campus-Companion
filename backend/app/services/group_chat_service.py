"""
Campus Lounge / Group Chat Service for AI Campus Companion.

Manages group chat simulations with all companions responding to user messages.
Uses OpenRouter to generate contextually appropriate responses from each companion
based on their personality, relationships with other companions, and chat history.
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId

from app.companions.companions import companions
from app.core.database import get_database
from app.models import (
    GroupChatHistoryResponse,
    GroupChatSendResponse,
    GroupMessageInDB,
    GroupMessageResponse,
    GroupMessageSenderType,
)
from app.services.openrouter_client import generate_reply

logger = logging.getLogger(__name__)

# Companion configurations for group chat
COMPANION_CONFIGS = {
    "study_buddy": {
        "name": "Oliver",
        "opinions": {
            "party_friend": "Chloe means well, but she can be distracting.",
            "philosopher": "Julian thinks too much. Sometimes you just need to do the work.",
            "rival": "Victoria is intense, but her competitive drive pushes me to be better.",
            "freshman": "Poor Toby is overwhelmed. I should help him get organized.",
        },
        "speech_patterns": "Calm, helpful, uses study metaphors, occasionally nerdy references.",
    },
    "party_friend": {
        "name": "Chloe",
        "opinions": {
            "study_buddy": "Oliver is sweet but needs to lighten up! Life isn't all about grades.",
            "philosopher": "Julian gets me. We have deep talks at 2 AM.",
            "rival": "Victoria terrifies me. Why is she always competing?",
            "freshman": "Toby is ADORABLE. I'm adopting him as my little freshman.",
        },
        "speech_patterns": "Energetic, uses ALL CAPS for emphasis, lots of exclamation points!!!",
    },
    "philosopher": {
        "name": "Julian",
        "opinions": {
            "study_buddy": "Oliver has wisdom in his diligence. I respect his focus.",
            "party_friend": "Chloe's exuberance is... tiring, but her heart is genuine.",
            "rival": "Victoria's competitiveness stems from insecurity. I pity her.",
            "freshman": "Toby reminds me of myself. Lost, searching for meaning.",
        },
        "speech_patterns": "Thoughtful, poetic, references literature and philosophy, speaks in metaphors.",
    },
    "rival": {
        "name": "Victoria",
        "opinions": {
            "study_buddy": "Oliver is competent. A worthy rival, if he'd stop helping everyone.",
            "party_friend": "Chloe is frivolous. I don't have time for her nonsense.",
            "philosopher": "Julian thinks he's above competition. He's just afraid to lose.",
            "freshman": "Toby is pathetic. How did he even get into this school?",
        },
        "speech_patterns": "Sharp, challenging, uses competitive language, occasionally mocking.",
    },
    "freshman": {
        "name": "Toby",
        "opinions": {
            "study_buddy": "Oliver is so nice! He helped me organize my schedule.",
            "party_friend": "Chloe invited me to a party! I've never been to one before...",
            "philosopher": "Julian is kinda scary. He asked me what the meaning of life is.",
            "rival": "Victoria terrifies me. She told me I don't belong here.",
        },
        "speech_patterns": "Nervous, uses lots of question marks, apologetic, excited about small things.",
    },
}


class GroupChatService:
    """Service for managing group chat simulations."""

    @staticmethod
    async def send_group_message(
        user_id: str,
        content: str,
        reply_to: Optional[str] = None,
    ) -> GroupChatSendResponse:
        """
        Send a message to the group chat.
        
        Saves the user message and generates companion replies based on:
        - Companion personalities
        - Relationships with other companions
        - Chat history context
        """
        logger.info(f"Group chat message from user {user_id}: {content[:50]}...")

        try:
            db = await get_database()
            now = datetime.now(timezone.utc)

            # Save user message
            user_message = GroupMessageInDB(
                sender_type=GroupMessageSenderType.USER,
                sender_id=user_id,
                sender_name="You",
                content=content,
                timestamp=now,
                reply_to=reply_to,
            )

            result = await db.group_conversations.insert_one(
                user_message.model_dump(exclude={"id"})
            )
            user_message.id = ObjectId(result.inserted_id)

            # Get recent chat history for context
            history = await GroupChatService._get_recent_history(db)

            # Generate companion replies
            companion_replies = await GroupChatService._generate_companion_replies(
                user_id=user_id,
                user_message=content,
                history=history,
            )

            # Save companion replies
            reply_messages = []
            for reply in companion_replies:
                companion_msg = GroupMessageInDB(
                    sender_type=GroupMessageSenderType.COMPANION,
                    sender_id=reply["companion_id"],
                    sender_name=COMPANION_CONFIGS[reply["companion_id"]]["name"],
                    content=reply["content"],
                    timestamp=datetime.now(timezone.utc),
                    reply_to=str(user_message.id),
                )

                result = await db.group_conversations.insert_one(
                    companion_msg.model_dump(exclude={"id"})
                )
                companion_msg.id = ObjectId(result.inserted_id)
                reply_messages.append(companion_msg)

            # Helper function to get color and avatar for a sender
            def get_sender_metadata(sender_id: str, sender_type: GroupMessageSenderType):
                if sender_type == GroupMessageSenderType.USER:
                    return {"sender_color": "zinc", "sender_avatar": ""}
                if sender_id in COMPANION_CONFIGS:
                    companion_data = companions.get(sender_id, {})
                    color_map = {
                        "study_buddy": "emerald",
                        "party_friend": "pink",
                        "philosopher": "purple",
                        "rival": "red",
                        "freshman": "amber",
                    }
                    return {
                        "sender_color": color_map.get(sender_id, "purple"),
                        "sender_avatar": companion_data.get("avatarUrl", "")
                    }
                return {"sender_color": "purple", "sender_avatar": ""}
            
            user_meta = get_sender_metadata(user_message.sender_id, user_message.sender_type)
            
            return GroupChatSendResponse(
                user_message=GroupMessageResponse(
                    id=str(user_message.id),
                    sender_type=user_message.sender_type,
                    sender_id=user_message.sender_id,
                    sender_name=user_message.sender_name,
                    content=user_message.content,
                    timestamp=user_message.timestamp,
                    reply_to=user_message.reply_to,
                    **user_meta
                ),
                companion_replies=[
                    GroupMessageResponse(
                        id=str(msg.id),
                        sender_type=msg.sender_type,
                        sender_id=msg.sender_id,
                        sender_name=msg.sender_name,
                        content=msg.content,
                        timestamp=msg.timestamp,
                        reply_to=msg.reply_to,
                        **get_sender_metadata(msg.sender_id, msg.sender_type)
                    )
                    for msg in reply_messages
                ],
            )

        except Exception as e:
            logger.error(f"Error sending group message: {e}", exc_info=True)
            raise

    @staticmethod
    async def _get_recent_history(db: Any, limit: int = 10) -> list[dict]:
        """Get recent chat history for context."""
        cursor = db.group_conversations.find().sort("timestamp", -1).limit(limit)
        history = []
        async for doc in cursor:
            history.append({
                "sender": COMPANION_CONFIGS.get(doc["sender_id"], {}).get("name", doc.get("sender_name", "Unknown")),
                "content": doc["content"],
            })
        return list(reversed(history))

    @staticmethod
    async def _generate_companion_replies(
        user_id: str,
        user_message: str,
        history: list[dict],
    ) -> list[dict]:
        """
        Generate companion replies using OpenRouter.
        Returns list of {companion_id, content} dicts.
        """
        try:
            # Build system prompt
            system_prompt = GroupChatService._build_group_chat_system_prompt()

            # Build user prompt with history and message
            history_text = ""
            for h in history[-5:]:  # Last 5 messages for context
                history_text += f"{h['sender']}: {h['content']}\n"

            user_prompt = f"""Recent chat history:
{history_text}

User just said: "{user_message}"

Generate replies from 2-3 companions who would most naturally respond. Return ONLY a JSON array."""

            # Call OpenRouter
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = await generate_reply(
                messages=messages,
                model="meta-llama/llama-3.1-8b-instruct",
            )

            # Parse JSON response
            try:
                # Clean up response
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()

                replies = json.loads(json_str)

                if not isinstance(replies, list):
                    logger.warning(f"Expected list of replies, got {type(replies)}")
                    return GroupChatService._get_fallback_replies(user_message)

                # Validate and format replies
                formatted_replies = []
                for reply in replies:
                    if isinstance(reply, dict) and "companion_id" in reply and "content" in reply:
                        companion_id = reply["companion_id"]
                        # Normalize companion_id
                        if companion_id in COMPANION_CONFIGS:
                            formatted_replies.append({
                                "companion_id": companion_id,
                                "content": reply["content"],
                            })

                if not formatted_replies:
                    return GroupChatService._get_fallback_replies(user_message)

                return formatted_replies[:3]  # Max 3 replies

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse companion replies as JSON: {e}")
                return GroupChatService._get_fallback_replies(user_message)

        except Exception as e:
            logger.error(f"Error generating companion replies: {e}", exc_info=True)
            return GroupChatService._get_fallback_replies(user_message)

    @staticmethod
    def _build_group_chat_system_prompt() -> str:
        """Build the system prompt for group chat."""
        prompt = """You are simulating a group chat with 5 AI companions who are friends but have distinct personalities and occasional conflicts:

"""
        for companion_id, config in COMPANION_CONFIGS.items():
            name = config["name"]
            personality = companions.get(companion_id, {}).get("system_prompt", "")
            opinions = config["opinions"]
            speech = config["speech_patterns"]

            prompt += f"\n{name} ({companion_id}):\n"
            prompt += f"- Personality: {personality[:100]}...\n"
            prompt += f"- Speech: {speech}\n"
            prompt += f"- Opinions: {opinions}\n"

        prompt += """
Rules:
1. Choose 2-3 companions who would naturally respond to the user's message
2. Each response should reflect their personality, speech patterns, and opinions
3. Companions can agree, disagree, or build on each other's points
4. Keep responses conversational and in character
5. Victoria often disagrees with Chloe. Julian mediates. Oliver stays on topic. Toby gets confused.

Return ONLY a JSON array in this exact format:
[
  {"companion_id": "study_buddy", "content": "Oliver's response here"},
  {"companion_id": "party_friend", "content": "Chloe's response here"}
]"""

        return prompt

    @staticmethod
    def _get_fallback_replies(user_message: str) -> list[dict]:
        """Generate fallback replies when OpenRouter fails."""
        fallbacks = [
            {"companion_id": "study_buddy", "content": "That's interesting. I think we should consider the practical implications of what you're saying."},
            {"companion_id": "party_friend", "content": "OMG yes!!! This is exactly what I've been talking about!!! 🎉"},
            {"companion_id": "philosopher", "content": "Your words carry a certain weight. I find myself contemplating the deeper meaning behind them."},
            {"companion_id": "rival", "content": "Hmm. Not bad. But I think there's a more efficient way to look at this."},
            {"companion_id": "freshman", "content": "Wait, I'm confused... can someone explain what we're talking about again? 😅"},
        ]

        # Select 2-3 random companions to respond
        num_replies = random.randint(2, 3)
        selected = random.sample(fallbacks, min(num_replies, len(fallbacks)))

        return selected

    @staticmethod
    async def get_group_history(user_id: str, limit: int = 50) -> GroupChatHistoryResponse:
        """Get group chat history."""
        try:
            db = await get_database()

            # Helper function to get color and avatar for a sender
            def get_sender_metadata(sender_id: str, sender_type: GroupMessageSenderType):
                if sender_type == GroupMessageSenderType.USER:
                    return {"sender_color": "zinc", "sender_avatar": ""}
                if sender_id in COMPANION_CONFIGS:
                    companion_data = companions.get(sender_id, {})
                    color_map = {
                        "study_buddy": "emerald",
                        "party_friend": "pink",
                        "philosopher": "purple",
                        "rival": "red",
                        "freshman": "amber",
                    }
                    return {
                        "sender_color": color_map.get(sender_id, "purple"),
                        "sender_avatar": companion_data.get("avatarUrl", "")
                    }
                return {"sender_color": "purple", "sender_avatar": ""}
            
            # Get messages
            cursor = db.group_conversations.find().sort("timestamp", -1).limit(limit)
            messages = []
            async for doc in cursor:
                meta = get_sender_metadata(doc["sender_id"], GroupMessageSenderType(doc["sender_type"]))
                doc.update(meta)
                messages.append(GroupMessageResponse(**doc))

            messages.reverse()  # Oldest first

            # Build participants list
            participants = []
            for companion_id, config in COMPANION_CONFIGS.items():
                companion_data = companions.get(companion_id, {})
                participants.append({
                    "id": companion_id,
                    "name": config["name"],
                    "color": companion_data.get("color", "blue"),
                    "avatar": companion_data.get("avatarUrl", ""),
                })

            # Add user
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                participants.append({
                    "id": user_id,
                    "name": user_doc.get("full_name", "You"),
                    "color": "zinc",
                    "avatar": "",
                })

            return GroupChatHistoryResponse(
                messages=messages,
                participants=participants,
                total=len(messages),
            )

        except Exception as e:
            logger.error(f"Error getting group history: {e}", exc_info=True)
            raise