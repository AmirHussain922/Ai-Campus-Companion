"""
Study Room Service for AI Campus Companion.

Handles collaborative study rooms with max 5 participants.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from bson import ObjectId
from app.models import (
    StudyRoomInDB,
    StudyRoomCreate,
    StudyRoomResponse,
    StudyRoomUpdate,
    StudyRoomParticipant,
    StudyRoomStatus,
)
from app.core.database import get_database, get_study_rooms_collection, get_users_collection
import logging

logger = logging.getLogger(__name__)


class StudyRoomService:
    """Service for managing study rooms."""

    MAX_PARTICIPANTS = 5

    @staticmethod
    async def create_room(
        host_id: str,
        major: str,
        subject: str,
        title: str,
        description: Optional[str] = None
    ) -> StudyRoomResponse:
        """
        Create a new study room.

        Args:
            host_id: Host user ID
            major: Major
            subject: Subject
            title: Room title
            description: Optional description

        Returns:
            StudyRoomResponse
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        # Validate inputs
        if not title or len(title.strip()) == 0:
            raise ValueError("Title is required")

        # Limit lengths
        title = title.strip()
        if len(title) > 200:
            title = title[:200]

        major = major.strip()
        if len(major) > 100:
            major = major[:100]

        subject = subject.strip()
        if len(subject) > 100:
            subject = subject[:100]

        # Create room
        try:
            room = StudyRoomInDB(
                host_id=host_id,
                major=major,
                subject=subject,
                title=title,
                description=description,
                participant_ids=[host_id], # Initialize with host
                started_at=datetime.now(timezone.utc)
            )
            
            room_dict = room.model_dump(exclude={"id"})
            
            result = await rooms_col.insert_one(room_dict)
            room.id = ObjectId(result.inserted_id)
        except Exception as e:
            raise

        # Get host info
        users_col = await get_users_collection()
        host = await users_col.find_one({"_id": ObjectId(host_id)})

        return StudyRoomResponse(
            id=str(room.id),
            host_id=room.host_id,
            host_full_name=host.get("full_name", "Anonymous") if host else "Anonymous",
            major=room.major,
            subject=room.subject,
            title=room.title,
            description=room.description,
            status=room.status,
            participant_ids=[room.host_id],  # Host is always first participant
            participant_count=1,
            max_participants=StudyRoomService.MAX_PARTICIPANTS,
            created_at=room.created_at,
            started_at=datetime.now(timezone.utc),
            ended_at=None,
        )

    @staticmethod
    async def get_room(room_id: str) -> Optional[StudyRoomResponse]:
        """
        Get a room by ID.

        Args:
            room_id: Room ID

        Returns:
            StudyRoomResponse or None
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            return None

        # Get host info
        users_col = await get_users_collection()
        host = await users_col.find_one({"_id": ObjectId(room["host_id"])})

        return StudyRoomResponse(
            id=str(room["_id"]),
            host_id=room["host_id"],
            host_full_name=host.get("full_name", "Anonymous") if host else "Anonymous",
            major=room["major"],
            subject=room["subject"],
            title=room["title"],
            description=room.get("description"),
            status=StudyRoomStatus(room["status"]),
            participant_ids=room.get("participant_ids", []),
            participant_count=len(room.get("participant_ids", [])),
            max_participants=StudyRoomService.MAX_PARTICIPANTS,
            created_at=room["created_at"],
            started_at=room.get("started_at"),
            ended_at=room.get("ended_at"),
        )

    @staticmethod
    async def get_active_rooms(page: int = 1, per_page: int = 50) -> dict:
        """
        Get all active study rooms.

        Args:
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with rooms and pagination meta
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        # Get total count of active rooms
        total = await rooms_col.count_documents({"status": StudyRoomStatus.ACTIVE.value})

        # Get active rooms with pagination
        skip = (page - 1) * per_page
        cursor = rooms_col.find({"status": StudyRoomStatus.ACTIVE.value}).sort("created_at", -1).skip(skip).limit(per_page)

        rooms = []
        async for doc in cursor:
            users_col = await get_users_collection()
            host = await users_col.find_one({"_id": ObjectId(doc["host_id"])})
            rooms.append({
                "id": str(doc["_id"]),
                "host_id": doc["host_id"],
                "host_full_name": host.get("full_name", "Anonymous") if host else "Anonymous",
                "major": doc["major"],
                "subject": doc["subject"],
                "title": doc["title"],
                "description": doc.get("description"),
                "status": doc["status"],
                "participant_ids": doc.get("participant_ids", []),
                "participant_count": len(doc.get("participant_ids", [])),
                "max_participants": StudyRoomService.MAX_PARTICIPANTS,
                "created_at": doc["created_at"],
                "started_at": doc.get("started_at"),
                "ended_at": doc.get("ended_at"),
            })

        total_pages = (total + per_page - 1) // per_page

        return {
            "rooms": rooms,
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
    async def join_room(room_id: str, user_id: str) -> StudyRoomParticipant:
        """
        Join a study room with atomic concurrency protection.

        Args:
            room_id: Room ID
            user_id: User ID attempting to join

        Returns:
            StudyRoomParticipant

        Raises:
            ValueError: If room is full or not active
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        # Get room
        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            raise ValueError("Room not found")

        # Check status
        if room["status"] != StudyRoomStatus.ACTIVE.value:
            raise ValueError("Room is not active")

        # Check if already participant
        if user_id in room.get("participant_ids", []):
            raise ValueError("Already a participant in this room")

        # Check capacity with ATOMIC operation (prevents race conditions)
        # This ensures we only increase participant count if we're adding a new participant
        result = await rooms_col.update_one(
            {
                "_id": ObjectId(room_id),
                "status": StudyRoomStatus.ACTIVE.value,
                "participant_ids": {"$ne": user_id},  # User not already participant
                "$expr": {"$lt": [{"$size": "$participant_ids"}, StudyRoomService.MAX_PARTICIPANTS]}
            },
            {
                "$push": {"participant_ids": user_id}
            }
        )

        if result.matched_count == 0:
            raise ValueError("Room is full or not available")

        # Get updated room
        room = await rooms_col.find_one({"_id": ObjectId(room_id)})

        # Get user info
        users_col = await get_users_collection()
        user = await users_col.find_one({"_id": ObjectId(user_id)})

        return StudyRoomParticipant(
            id=str(room["_id"]),
            user_id=room["participant_ids"][-1],  # Last added is the one we just joined
            full_name=user.get("full_name", "Anonymous") if user else "Anonymous",
            joined_at=datetime.now(timezone.utc),
        )

    @staticmethod
    async def leave_room(room_id: str, user_id: str) -> bool:
        """
        Leave a study room.

        Args:
            room_id: Room ID
            user_id: User ID leaving

        Returns:
            True if successful
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        # Get room
        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            raise ValueError("Room not found")

        # Verify user is participant
        participant_ids = room.get("participant_ids", [])
        if user_id not in participant_ids:
            raise ValueError("Not a participant in this room")

        # Remove user from participants
        await rooms_col.update_one(
            {"_id": ObjectId(room_id)},
            {"$pull": {"participant_ids": user_id}}
        )

        # If host leaves, end the room
        if room["host_id"] == user_id:
            await StudyRoomService.end_room(room_id)

        return True

    @staticmethod
    async def end_room(room_id: str, host_id: str) -> bool:
        """
        End a study room (only by host).

        Args:
            room_id: Room ID
            host_id: Host user ID (must be room host)

        Returns:
            True if successful
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        # Verify host
        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            raise ValueError("Room not found")

        if room["host_id"] != host_id:
            raise ValueError("Only host can end room")

        # Update room status
        now = datetime.now(timezone.utc)
        await rooms_col.update_one(
            {"_id": ObjectId(room_id)},
            {
                "$set": {
                    "status": StudyRoomStatus.ENDED.value,
                    "ended_at": now
                }
            }
        )

        return True

    @staticmethod
    async def update_room(
        room_id: str,
        host_id: str,
        update_data: StudyRoomUpdate
    ) -> Optional[StudyRoomResponse]:
        """
        Update room details (only by host).

        Args:
            room_id: Room ID
            host_id: Host user ID (must be room host)
            update_data: Update data

        Returns:
            Updated StudyRoomResponse or None
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        # Verify host
        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            return None

        if room["host_id"] != host_id:
            raise ValueError("Only host can update room")

        # Build update document
        update_data_dict = update_data.model_dump(exclude_unset=True)

        if update_data_dict:
            update_data_dict["updated_at"] = datetime.utcnow()
            await rooms_col.update_one(
                {"_id": ObjectId(room_id)},
                {"$set": update_data_dict}
            )

            # Get updated room
            room = await rooms_col.find_one({"_id": ObjectId(room_id)})

        # Get host info
        users_col = await get_users_collection()
        host = await users_col.find_one({"_id": ObjectId(host_id)})

        return StudyRoomResponse(
            id=str(room["_id"]),
            host_id=room["host_id"],
            host_full_name=host.get("full_name", "Anonymous") if host else "Anonymous",
            major=room["major"],
            subject=room["subject"],
            title=room["title"],
            description=room.get("description"),
            status=StudyRoomStatus(room["status"]),
            participant_ids=room.get("participant_ids", []),
            participant_count=len(room.get("participant_ids", [])),
            max_participants=StudyRoomService.MAX_PARTICIPANTS,
            created_at=room["created_at"],
            started_at=room.get("started_at"),
            ended_at=room.get("ended_at"),
        )

    @staticmethod
    async def is_user_participant(room_id: str, user_id: str) -> bool:
        """
        Check if a user is a participant of a room.

        Args:
            room_id: Room ID
            user_id: User ID

        Returns:
            True if participant
        """
        db = await get_database()
        rooms_col = await get_study_rooms_collection()

        room = await rooms_col.find_one({"_id": ObjectId(room_id)})
        if not room:
            return False

        participant_ids = room.get("participant_ids", [])
        return user_id in participant_ids
