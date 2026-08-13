"""
Study Buddy Messaging Service for AI Campus Companion.

Handles conversations, messages, and real-time messaging operations.
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.models import (
    ConversationInDB,
    ConversationResponse,
    ConversationCreate,
    MessageInDB,
    MessageResponse,
    MessageCreate,
    MessageType,
)
from app.core.validation import PaginationParams
from app.core.database import (
    get_database,
    get_study_buddy_conversations_collection,
    get_study_buddy_messages_collection,
    get_users_collection,
)
import logging

logger = logging.getLogger(__name__)


class StudyBuddyMessagingService:
    """Service for managing Study Buddy conversations and messages."""

    @staticmethod
    async def get_or_create_conversation(user_id: str, other_user_id: str) -> ConversationResponse:
        """
        Get or create a conversation between two users.

        Args:
            user_id: First user ID
            other_user_id: Second user ID

        Returns:
            ConversationResponse
        """
        db = await get_database()
        conversations_col = await get_study_buddy_conversations_collection()

        # Normalize user IDs (ensure user_a_id comes first alphabetically)
        user_a, user_b = sorted([user_id, other_user_id])

        # Try to get existing conversation
        conversation = await conversations_col.find_one({
            "user_a_id": user_a,
            "user_b_id": user_b
        })

        if conversation:
            return ConversationResponse(
                id=str(conversation["_id"]),
                user_a_id=conversation["user_a_id"],
                user_b_id=conversation["user_b_id"],
                created_at=conversation["created_at"],
            )

        # Create new conversation
        conversation = ConversationInDB(
            user_a_id=user_a,
            user_b_id=user_b,
        )
        result = await conversations_col.insert_one(conversation.model_dump(exclude={"id"}))
        conversation.id = ObjectId(result.inserted_id)

        return ConversationResponse(
            id=str(conversation.id),
            user_a_id=conversation.user_a_id,
            user_b_id=conversation.user_b_id,
            created_at=conversation.created_at,
        )

    @staticmethod
    async def get_conversations(user_id: str, pagination: Optional[PaginationParams] = None) -> dict:
        """
        Get all conversations for a user.

        Args:
            user_id: User ID
            pagination: Pagination parameters

        Returns:
            Dictionary with conversations list and pagination meta
        """
        db = await get_database()
        conversations_col = await get_study_buddy_conversations_collection()
        users_col = await get_users_collection()

        # PaginationParams uses limit/offset (consistent with the rest of the codebase)
        per_page = pagination.limit if pagination else 50
        offset = pagination.offset if pagination else 0
        page = offset // per_page + 1 if per_page > 0 else 1

        # Find all conversations where user is either user_a_id or user_b_id
        cursor = conversations_col.find({
            "$or": [
                {"user_a_id": user_id},
                {"user_b_id": user_id}
            ]
        }).sort("updated_at", -1)

        # Get total count
        total = await conversations_col.count_documents({
            "$or": [
                {"user_a_id": user_id},
                {"user_b_id": user_id}
            ]
        })

        conversations_cursor = cursor.skip(offset).limit(per_page)

        conversations = []
        async for doc in conversations_cursor:
            # Get other user info
            other_id = doc["user_b_id"] if doc["user_a_id"] == user_id else doc["user_a_id"]
            other_user = await users_col.find_one({"_id": ObjectId(other_id)})

            conversations.append({
                "conversation_id": str(doc["_id"]),
                "other_user_id": other_id,
                "other_user_name": other_user.get("full_name", "Anonymous") if other_user else "Anonymous",
                "other_user_email": other_user.get("email", "") if other_user else "",
                "created_at": doc["created_at"],
                "updated_at": doc["updated_at"],
            })

        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return {
            "conversations": conversations,
            "meta": {
                "page": page,
                "per_page": per_page,
                "limit": per_page,
                "offset": offset,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    @staticmethod
    async def get_conversation_by_ids(conversation_id: str, user_id: str) -> Optional[dict]:
        """
        Get conversation by ID and verify user is a participant.

        Args:
            conversation_id: Conversation ID
            user_id: User ID

        Returns:
            Conversation dict or None if not found/not participant
        """
        db = await get_database()
        conversations_col = await get_study_buddy_conversations_collection()

        conversation = await conversations_col.find_one({"_id": ObjectId(conversation_id)})

        if not conversation:
            return None

        # Verify user is participant
        if conversation["user_a_id"] != user_id and conversation["user_b_id"] != user_id:
            return None

        return {
            "conversation_id": str(conversation["_id"]),
            "user_a_id": conversation["user_a_id"],
            "user_b_id": conversation["user_b_id"],
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"],
        }

    @staticmethod
    async def get_messages(
        conversation_id: str,
        user_id: str,
        pagination: Optional[PaginationParams] = None
    ) -> dict:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for verification)
            pagination: Pagination parameters

        Returns:
            Dictionary with messages list and pagination meta
        """
        # Verify conversation exists and user is participant
        conversation = await StudyBuddyMessagingService.get_conversation_by_ids(conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found or you are not a participant")

        db = await get_database()
        messages_col = await get_study_buddy_messages_collection()

        # PaginationParams uses limit/offset (consistent with the rest of the codebase)
        per_page = pagination.limit if pagination else 50
        offset = pagination.offset if pagination else 0
        page = offset // per_page + 1 if per_page > 0 else 1

        # Get messages sorted by creation time (oldest first)
        cursor = messages_col.find({
            "conversation_id": conversation_id
        }).sort("created_at", 1)

        total = await messages_col.count_documents({
            "conversation_id": conversation_id
        })

        messages_cursor = cursor.skip(offset).limit(per_page)

        messages = []
        async for doc in messages_cursor:
            messages.append(MessageResponse(
                id=str(doc["_id"]),
                conversation_id=doc["conversation_id"],
                sender_id=doc["sender_id"],
                content=doc["content"],
                message_type=MessageType(doc.get("message_type", "text")),
                is_read=doc["is_read"],
                read_at=doc.get("read_at"),
                created_at=doc["created_at"],
            ))

        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return {
            "messages": messages,
            "meta": {
                "page": page,
                "per_page": per_page,
                "limit": per_page,
                "offset": offset,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    @staticmethod
    async def create_message(conversation_id: str, sender_id: str, content: str) -> MessageResponse:
        """
        Create and save a message.

        Args:
            conversation_id: Conversation ID
            sender_id: Sender user ID
            content: Message content

        Returns:
            MessageResponse with the created message
        """
        db = await get_database()
        messages_col = await get_study_buddy_messages_collection()

        # Verify conversation exists and user is participant
        conversation = await StudyBuddyMessagingService.get_conversation_by_ids(conversation_id, sender_id)
        if not conversation:
            raise ValueError("Conversation not found or you are not a participant")

        # Verify connection exists (Study Buddy requirement)
        from app.services.study_buddy_service import StudyBuddyService
        try:
            # Check if users are connected
            connections = await StudyBuddyService.get_connections(sender_id)
            other_user_id = conversation["user_b_id"] if conversation["user_a_id"] == sender_id else conversation["user_a_id"]
            is_connected = any(c.id == other_user_id for c in connections)
            if not is_connected:
                raise ValueError("You can only message connected Study Buddies")
        except Exception:
            raise ValueError("You can only message connected Study Buddies")

        # Create message
        message = MessageInDB(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=MessageType.TEXT,
            is_read=False,
        )
        result = await messages_col.insert_one(message.model_dump(exclude={"id"}))
        message.id = ObjectId(result.inserted_id)

        # Update conversation's updated_at
        conversations_col = await get_study_buddy_conversations_collection()
        await conversations_col.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"updated_at": datetime.utcnow()}}
        )

        # Mark messages in conversation as read for the sender (but they are the sender, so this is informational)
        await messages_col.update_many(
            {"conversation_id": conversation_id, "sender_id": {"$ne": sender_id}, "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )

        # Convert datetime objects to ISO strings for JSON serialization
        created_at = message.created_at.isoformat() if message.created_at else None
        read_at = message.read_at.isoformat() if message.read_at else None

        return MessageResponse(
            id=str(message.id),
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            is_read=message.is_read,
            read_at=read_at,
            created_at=created_at,
        )

    @staticmethod
    async def mark_messages_as_read(conversation_id: str, user_id: str) -> int:
        """
        Mark all messages in a conversation as read for a user.

        Args:
            conversation_id: Conversation ID
            user_id: User ID

        Returns:
            Number of messages marked as read
        """
        db = await get_database()
        messages_col = await get_study_buddy_messages_collection()

        result = await messages_col.update_many(
            {
                "conversation_id": conversation_id,
                "sender_id": {"$ne": user_id},  # Messages from this user
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count

    @staticmethod
    async def delete_conversation(conversation_id: str, user_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (must be participant)

        Returns:
            True if deleted, False if not found
        """
        # Verify conversation exists and user is participant
        conversation = await StudyBuddyMessagingService.get_conversation_by_ids(conversation_id, user_id)
        if not conversation:
            return False

        db = await get_database()
        conversations_col = await get_study_buddy_conversations_collection()
        messages_col = await get_study_buddy_messages_collection()

        # Delete conversation and messages
        await conversations_col.delete_one({"_id": ObjectId(conversation_id)})
        await messages_col.delete_many({"conversation_id": conversation_id})

        return True
