"""
Study Buddy Service for AI Campus Companion.

Handles study buddy profiles, matching engine, and connection management.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from bson import ObjectId
from app.models import (
    StudyBuddyProfileInDB,
    StudyBuddyProfileResponse,
    StudyBuddyProfileCreate,
    StudyBuddyProfileUpdate,
    StudyBuddyMatchRequest,
    StudyBuddyMatchResponse,
    MatchReason,
    MatchReasonResponse,
    StudyBuddyMatchResult,
    ConnectionRequestInDB,
    ConnectionRequestCreate,
    ConnectionRequestResponse,
    ConnectionResponse,
    ConnectionRequestStatus,
)
from app.core.database import get_database
import logging

logger = logging.getLogger(__name__)


class StudyBuddyService:
    """Service for managing study buddy profiles and matching."""

    @staticmethod
    async def get_or_create_profile(user_id: str) -> StudyBuddyProfileResponse:
        """
        Get user's study buddy profile or create it if it doesn't exist.

        Args:
            user_id: User ID

        Returns:
            StudyBuddyProfileResponse
        """
        db = await get_database()

        # Check if profile exists
        profile = await db.study_buddy_profiles.find_one({"user_id": user_id})

        if profile:
            # Convert _id ObjectId to string for Pydantic
            profile["_id"] = str(profile["_id"])
            return StudyBuddyProfileResponse(**profile)
        else:
            # Create default profile
            profile = StudyBuddyProfileInDB(
                user_id=user_id,
                country="",
                city="",
                campus_university="",
                major="",
                academic_year="",
                strong_subjects=[],
                weak_subjects=[],
                bio=None,
                avatar_id=None,
            )
            result = await db.study_buddy_profiles.insert_one(profile.model_dump(exclude={"id"}))
            profile.id = ObjectId(result.inserted_id)
            return StudyBuddyProfileResponse(
                id=str(profile.id),
                user_id=profile.user_id,
                country=profile.country,
                city=profile.city,
                campus_university=profile.campus_university,
                major=profile.major,
                academic_year=profile.academic_year,
                strong_subjects=profile.strong_subjects,
                weak_subjects=profile.weak_subjects,
                bio=profile.bio,
                avatar_id=profile.avatar_id,
                is_online=False,
                last_active=None,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )

    @staticmethod
    async def update_profile(user_id: str, profile_data: StudyBuddyProfileUpdate) -> StudyBuddyProfileResponse:
        """
        Update user's study buddy profile.

        Creates the profile if it doesn't exist yet.

        Args:
            user_id: User ID
            profile_data: Profile update data

        Returns:
            Updated StudyBuddyProfileResponse
        """
        db = await get_database()

        # Build update document - exclude unset fields, None values, and empty strings
        update_data = {
            k: v for k, v in profile_data.model_dump(exclude_unset=True).items()
            if v is not None and v != ""
        }

        if not update_data:
            raise ValueError("No valid fields to update")

        # Add last_active timestamp
        update_data["last_active"] = datetime.utcnow()

        # Check if profile exists
        existing = await db.study_buddy_profiles.find_one({"user_id": user_id})

        if existing:
            # Update existing profile
            await db.study_buddy_profiles.update_one(
                {"user_id": user_id},
                {
                    "$set": update_data,
                    "$currentDate": {"updated_at": True}
                }
            )
        else:
            # Create new profile
            profile = StudyBuddyProfileInDB(
                user_id=user_id,
                country=update_data.get("country", ""),
                city=update_data.get("city", ""),
                campus_university=update_data.get("campus_university", ""),
                major=update_data.get("major", ""),
                academic_year=update_data.get("academic_year", ""),
                strong_subjects=update_data.get("strong_subjects", []),
                weak_subjects=update_data.get("weak_subjects", []),
                bio=update_data.get("bio"),
                avatar_id=update_data.get("avatar_id"),
                is_online=False,
                last_active=update_data.get("last_active"),
            )
            result = await db.study_buddy_profiles.insert_one(profile.model_dump(exclude={"id"}))
            profile.id = ObjectId(result.inserted_id)

        # Return updated profile
        updated_profile = await db.study_buddy_profiles.find_one({"user_id": user_id})
        if updated_profile:
            # Convert _id ObjectId to string for Pydantic
            updated_profile["_id"] = str(updated_profile["_id"])
        return StudyBuddyProfileResponse(**updated_profile)

    @staticmethod
    async def get_match_reasons(user_profile: dict, other_profile: dict) -> List[MatchReasonResponse]:
        """
        Calculate match reasons between two users.

        Args:
            user_profile: User's profile data
            other_profile: Other user's profile data

        Returns:
            List of match reasons
        """
        reasons = []
        user_strong = set(user_profile.get("strong_subjects", []))
        user_weak = set(user_profile.get("weak_subjects", []))
        other_strong = set(other_profile.get("strong_subjects", []))
        other_weak = set(other_profile.get("weak_subjects", []))
        overlap = user_strong & other_strong

        # Same campus match
        if user_profile.get("campus_university") and other_profile.get("campus_university"):
            if user_profile["campus_university"].lower() == other_profile["campus_university"].lower():
                reasons.append(MatchReasonResponse(
                    reason=MatchReason.SAME_CAMPUS,
                    description="We go to the same campus!"
                ))

        # Same major match
        if user_profile.get("major") and other_profile.get("major"):
            if user_profile["major"].lower() == other_profile["major"].lower():
                reasons.append(MatchReasonResponse(
                    reason=MatchReason.SAME_MAJOR,
                    description="We're in the same major!"
                ))

        # Same year match
        if user_profile.get("academic_year") and other_profile.get("academic_year"):
            if user_profile["academic_year"] == other_profile["academic_year"]:
                reasons.append(MatchReasonResponse(
                    reason=MatchReason.SAME_YEAR,
                    description="We're in the same year!"
                ))

        # Same city match
        if user_profile.get("city") and other_profile.get("city"):
            if user_profile["city"].lower() == other_profile["city"].lower():
                reasons.append(MatchReasonResponse(
                    reason=MatchReason.SAME_LOCATION,
                    description="We're in the same city!"
                ))

        # Strong/weak subject compatibility
        if overlap:
            reasons.append(MatchReasonResponse(
                reason=MatchReason.RELATED_SUBJECTS,
                description=f"We both love: {', '.join(list(overlap)[:3])}"
            ))

        # You help them with weak subjects
        for subject in other_weak:
            if subject in user_strong:
                reasons.append(MatchReasonResponse(
                    reason=MatchReason.STRONG_WEAK,
                    description=f"You can help them with {subject}"
                ))

        # They help you with weak subjects
        for subject in user_weak:
            if subject in other_strong:
                reasons.append(MatchReasonResponse(
                    reason=MatchReason.STRONG_WEAK,
                    description=f"They can help you with {subject}"
                ))

        # Fallback reason if no matches
        if not reasons:
            reasons.append(MatchReasonResponse(
                reason=MatchReason.RELATED_SUBJECTS,
                description="Maybe your subjects overlap in unexpected ways"
            ))

        return reasons

    @staticmethod
    async def calculate_compatibility_score(user_profile: dict, other_profile: dict, match_reasons: List[MatchReasonResponse]) -> int:
        """
        Calculate compatibility score (0-100) between two users.

        Args:
            user_profile: User's profile data
            other_profile: Other user's profile data
            match_reasons: List of match reasons

        Returns:
            Compatibility score (0-100)
        """
        score = 0

        # Campus match (20 points)
        if user_profile.get("campus_university") and other_profile.get("campus_university"):
            if user_profile["campus_university"].lower() == other_profile["campus_university"].lower():
                score += 20

        # Major match (15 points)
        if user_profile.get("major") and other_profile.get("major"):
            if user_profile["major"].lower() == other_profile["major"].lower():
                score += 15

        # Same year (10 points)
        if user_profile.get("academic_year") and other_profile.get("academic_year"):
            if user_profile["academic_year"] == other_profile["academic_year"]:
                score += 10

        # Same city (5 points)
        if user_profile.get("city") and other_profile.get("city"):
            if user_profile["city"].lower() == other_profile["city"].lower():
                score += 5

        # Strong/weak subject compatibility (40 points total)
        user_strong = set(user_profile.get("strong_subjects", []))
        user_weak = set(user_profile.get("weak_subjects", []))
        other_strong = set(other_profile.get("strong_subjects", []))
        other_weak = set(other_profile.get("weak_subjects", []))

        # Both strong in same subjects
        overlap = user_strong & other_strong
        score += len(overlap) * 8

        # You help them with weak subjects
        user_helps_other = len(user_weak & other_strong)
        score += user_helps_other * 7

        # They help you with weak subjects
        other_helps_you = len(user_strong & other_weak)
        score += other_helps_you * 7

        # Max 100
        return min(score, 100)

    @staticmethod
    async def find_matches(user_id: str, limit: int = 20) -> StudyBuddyMatchResponse:
        """
        Find study buddy matches for a user.

        Args:
            user_id: User ID
            limit: Maximum number of matches to return

        Returns:
            StudyBuddyMatchResponse with matches
        """
        db = await get_database()

        # Get user's profile
        user_profile = await db.study_buddy_profiles.find_one({"user_id": user_id})
        if not user_profile:
            raise ValueError("Profile not found")

        # Get all profiles (exclude self)
        cursor = db.study_buddy_profiles.find(
            {
                "user_id": {"$ne": user_id},
            }
        )

        matches: List[StudyBuddyMatchResult] = []

        async for other_profile in cursor:
            # Calculate compatibility score
            match_reasons = await StudyBuddyService.get_match_reasons(user_profile, other_profile)
            score = await StudyBuddyService.calculate_compatibility_score(user_profile, other_profile, match_reasons)

            # Get user details for overlap subjects
            other_user = await db.users.find_one({"_id": ObjectId(other_profile["user_id"])})
            user_details = await db.users.find_one({"_id": ObjectId(user_profile["user_id"])})

            strong_overlap = list(set(user_profile.get("strong_subjects", [])) & set(other_profile.get("strong_subjects", [])))
            weak_help = []
            for subject in other_profile.get("weak_subjects", []):
                if subject in user_profile.get("strong_subjects", []):
                    weak_help.append(subject)

            matches.append(StudyBuddyMatchResult(
                user_id=other_profile["user_id"],
                full_name=other_user.get("full_name", "Anonymous") if other_user else "Anonymous",
                email=other_user.get("email", "") if other_user else "",
                avatar_url=None,  # Would require media service integration
                compatibility_score=score,
                match_reasons=match_reasons,
                strong_subjects_overlap=strong_overlap[:3],  # Top 3 overlaps
                weak_subjects_help=weak_help[:3],  # Top 3 ways they can help
            ))

        # Sort by score and limit
        matches.sort(key=lambda m: m.compatibility_score, reverse=True)
        matches = matches[:limit]

        return StudyBuddyMatchResponse(
            matches=matches,
            total_matches=len(matches)
        )

    @staticmethod
    async def send_connection_request(sender_id: str, recipient_id: str, message: Optional[str] = None) -> ConnectionRequestResponse:
        """
        Send a connection request to another user.

        Args:
            sender_id: Sender user ID
            recipient_id: Recipient user ID
            message: Optional message

        Returns:
            ConnectionRequestResponse
        """
        db = await get_database()

        # Check if sender has a profile
        sender_profile = await db.study_buddy_profiles.find_one({"user_id": sender_id})
        if not sender_profile:
            raise ValueError("Sender must complete their profile first")

        # Check if recipient has a profile
        recipient_profile = await db.study_buddy_profiles.find_one({"user_id": recipient_id})
        if not recipient_profile:
            raise ValueError("Recipient must complete their profile first")

        # Check if self-request
        if sender_id == recipient_id:
            raise ValueError("Cannot send request to yourself")

        # Check if request already exists
        existing = await db.buddy_requests.find_one({
            "sender_id": sender_id,
            "recipient_id": recipient_id,
        })
        if existing:
            raise ValueError("Connection request already exists")

        # Check if already connected
        existing_connection = await db.buddy_requests.find_one({
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "status": ConnectionRequestStatus.ACCEPTED.value
        })
        if existing_connection:
            raise ValueError("Already connected")

        # Create request
        request = ConnectionRequestInDB(
            sender_id=sender_id,
            recipient_id=recipient_id,
            status=ConnectionRequestStatus.PENDING,
            message=message,
        )
        result = await db.buddy_requests.insert_one(request.model_dump(exclude={"id"}))
        request.id = ObjectId(result.inserted_id)

        # Get sender details
        sender_user = await db.users.find_one({"_id": ObjectId(sender_id)})

        return ConnectionRequestResponse(
            id=str(request.id),
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            status=request.status,
            message=request.message,
            sender_full_name=sender_user.get("full_name", "Anonymous") if sender_user else "Anonymous",
            sender_avatar_url=None,
            created_at=request.created_at,
        )

    @staticmethod
    async def get_pending_requests(user_id: str) -> List[ConnectionRequestResponse]:
        """
        Get all pending connection requests for a user.

        Args:
            user_id: User ID

        Returns:
            List of ConnectionRequestResponse
        """
        db = await get_database()

        # Get incoming requests
        cursor = db.buddy_requests.find({
            "recipient_id": user_id,
            "status": ConnectionRequestStatus.PENDING.value,
        }).sort("created_at", -1)

        requests = []
        async for doc in cursor:
            # Get sender details
            sender_user = await db.users.find_one({"_id": ObjectId(doc["sender_id"])})
            requests.append(ConnectionRequestResponse(
                id=str(doc["_id"]),
                sender_id=doc["sender_id"],
                recipient_id=doc["recipient_id"],
                status=ConnectionRequestStatus.PENDING,
                message=doc.get("message"),
                sender_full_name=sender_user.get("full_name", "Anonymous") if sender_user else "Anonymous",
                sender_avatar_url=None,
                created_at=doc["created_at"],
            ))

        return requests

    @staticmethod
    async def respond_to_request(request_id: str, user_id: str, action: str) -> ConnectionRequestResponse:
        """
        Respond to a connection request (accept or reject).

        Args:
            request_id: Request ID
            user_id: User ID responding
            action: "accept" or "reject"

        Returns:
            Updated ConnectionRequestResponse
        """
        db = await get_database()

        # Get request
        request = await db.buddy_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise ValueError("Request not found")

        # Verify ownership
        if request["recipient_id"] != user_id:
            raise ValueError("Not authorized to respond to this request")

        # Check status
        if request["status"] != ConnectionRequestStatus.PENDING.value:
            raise ValueError("Request has already been processed")

        # Update status
        if action == "accept":
            new_status = ConnectionRequestStatus.ACCEPTED.value
        elif action == "reject":
            new_status = ConnectionRequestStatus.REJECTED.value
        else:
            raise ValueError("Invalid action. Use 'accept' or 'reject'")

        await db.buddy_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
        )

        # Get updated request
        updated_request = await db.buddy_requests.find_one({"_id": ObjectId(request_id)})
        sender_user = await db.users.find_one({"_id": ObjectId(updated_request["sender_id"])})

        return ConnectionRequestResponse(
            id=str(updated_request["_id"]),
            sender_id=updated_request["sender_id"],
            recipient_id=updated_request["recipient_id"],
            status=ConnectionRequestStatus(new_status) if new_status else ConnectionRequestStatus.PENDING,
            message=updated_request.get("message"),
            sender_full_name=sender_user.get("full_name", "Anonymous") if sender_user else "Anonymous",
            sender_avatar_url=None,
            created_at=updated_request["created_at"],
        )

    @staticmethod
    async def get_connections(user_id: str) -> List[ConnectionResponse]:
        """
        Get all accepted connections for a user.

        Args:
            user_id: User ID

        Returns:
            List of ConnectionResponse
        """
        db = await get_database()

        # Find both incoming and outgoing accepted connections
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"sender_id": user_id, "status": ConnectionRequestStatus.ACCEPTED.value},
                        {"recipient_id": user_id, "status": ConnectionRequestStatus.ACCEPTED.value}
                    ]
                }
            },
            {
                "$group": {
                    "_id": None,
                    "connections": {"$push": "$$ROOT"}
                }
            }
        ]

        result = await db.buddy_requests.aggregate(pipeline).to_list(length=1)

        connections = []
        if result and result[0].get("connections"):
            for doc in result[0]["connections"]:
                # Get connection details
                other_id = doc["sender_id"] if doc["recipient_id"] == user_id else doc["recipient_id"]
                connection_profile = await db.study_buddy_profiles.find_one({"user_id": other_id})

                other_user = await db.users.find_one({"_id": ObjectId(other_id)})

                connections.append(ConnectionResponse(
                    id=other_id,
                    user_id=other_id,
                    full_name=other_user.get("full_name", "Anonymous") if other_user else "Anonymous",
                    avatar_url=None,
                    country=connection_profile.get("country", "") if connection_profile else "",
                    city=connection_profile.get("city", "") if connection_profile else "",
                    campus_university=connection_profile.get("campus_university", "") if connection_profile else "",
                    major=connection_profile.get("major", "") if connection_profile else "",
                    academic_year=connection_profile.get("academic_year", "") if connection_profile else "",
                    is_online=connection_profile.get("is_online", False) if connection_profile else False,
                ))

        return connections
