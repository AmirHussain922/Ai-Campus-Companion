"""
Study Room Messaging Service for AI Campus Companion.

Handles real-time messaging within study rooms.
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.models import (
    RoomMessageInDB,
    RoomMessageResponse,
    RoomMessageCreate,
    MessageType,
)
from app.core.database import get_database, get_study_rooms_collection, get_study_room_messages_collection, get_users_collection
import logging

logger = logging.getLogger(__name__)


class StudyRoomMessagingService:
    """Service for managing study room messages."""

    @staticmethod
    async def get_room_messages(room_id: str, page: int = 1, per_page: int = 50) -> dict:
        """
        Get messages for a study room.

        Args:
            room_id: Room ID
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with messages and pagination meta
        """
        db = await get_database()
        messages_col = await get_study_room_messages_collection()

        # Get messages sorted by creation time (oldest first)
        cursor = messages_col.find({
            "room_id": room_id
        }).sort("created_at", 1)

        total = await messages_col.count_documents({
            "room_id": room_id
        })

        skip = (page - 1) * per_page
        messages_cursor = cursor.skip(skip).limit(per_page)

        messages = []
        async for doc in messages_cursor:
            messages.append(RoomMessageResponse(
                id=str(doc["_id"]),
                room_id=doc["room_id"],
                sender_id=doc["sender_id"],
                content=doc["content"],
                message_type=MessageType(doc.get("message_type", "text")),
                is_read=doc["is_read"],
                read_at=doc.get("read_at"),
                created_at=doc["created_at"],
            ))

        total_pages = (total + per_page - 1) // per_page

        return {
            "messages": messages,
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    @staticmethod
    async def create_message(room_id: str, sender_id: str, content: str) -> RoomMessageResponse:
        """
        Create and save a room message.

        Args:
            room_id: Room ID
            sender_id: Sender user ID
            content: Message content

        Returns:
            RoomMessageResponse with the created message
        """
        db = await get_database()
        messages_col = await get_study_room_messages_collection()

        # Verify room exists
        rooms_col = await get_study_rooms_collection()
        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            raise ValueError("Room not found")

        # Verify room is active
        if room["status"] != "active":
            raise ValueError("Room is not active")

        # Verify sender is participant
        participant_ids = room.get("participant_ids", [])
        if sender_id not in participant_ids:
            raise ValueError("You are not a participant in this room")

        # Create message
        message = RoomMessageInDB(
            room_id=room_id,
            sender_id=sender_id,
            content=content,
            message_type=MessageType.TEXT,
            is_read=False,
        )
        result = await messages_col.insert_one(message.model_dump(exclude={"id"}))
        message.id = ObjectId(result.inserted_id)

        # Mark messages in room as read for the sender (but they are the sender, so this is informational)
        await messages_col.update_many(
            {"room_id": room_id, "sender_id": {"$ne": sender_id}, "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )

        # Get sender info
        users_col = await get_users_collection()
        sender = await users_col.find_one({"_id": ObjectId(sender_id)})

        return RoomMessageResponse(
            id=str(message.id),
            room_id=message.room_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            is_read=message.is_read,
            read_at=message.read_at,
            created_at=message.created_at,
        )

    @staticmethod
    async def mark_messages_as_read(room_id: str, user_id: str) -> int:
        """
        Mark all messages in a room as read for a user.

        Args:
            room_id: Room ID
            user_id: User ID

        Returns:
            Number of messages marked as read
        """
        db = await get_database()
        messages_col = await get_study_room_messages_collection()

        result = await messages_col.update_many(
            {
                "room_id": room_id,
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
    async def delete_room_messages(room_id: str, user_id: str) -> bool:
        """
        Delete all messages in a room (for room host).

        Args:
            room_id: Room ID
            user_id: User ID (must be host)

        Returns:
            True if successful, False if not found
        """
        db = await get_database()
        messages_col = await get_study_room_messages_collection()
        rooms_col = await get_study_rooms_collection()

        # Verify user is host
        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            return False

        if room["host_id"] != user_id:
            raise ValueError("Only host can delete room messages")

        # Delete all messages in room
        result = await messages_col.delete_many({"room_id": room_id})
        return result.deleted_count > 0
