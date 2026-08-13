"""
Study Service for AI Campus Companion.
Handles study session creation, completion, and leaderboard.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from bson import ObjectId
from app.models import (
    StudySessionCreate,
    StudySessionInDB,
    StudySessionResponse,
    StudyCompleteResponse,
    StudyLeaderboardResponse,
    StudyLeaderboardEntry,
)
from app.core.database import get_database
from app.companions.companions import companions
import logging

logger = logging.getLogger(__name__)


class StudyService:
    """Service for managing study sessions."""

    @staticmethod
    async def create_study_session(
        user_id: str,
        request: StudySessionCreate,
    ) -> StudySessionResponse:
        """Create a new study session."""
        db = await get_database()
        now = datetime.now(timezone.utc)
        
        session = StudySessionInDB(
            user_id=user_id,
            companion_id=request.companion_id,
            duration_minutes=request.duration_minutes,
            focus_topic=request.focus_topic,
            expected_end_at=now + timedelta(minutes=request.duration_minutes),
        )
        
        result = await db.study_sessions.insert_one(
            session.model_dump(exclude={"id"})
        )
        session.id = ObjectId(result.inserted_id)
        
        return StudySessionResponse(
            _id=str(session.id),
            companion_id=session.companion_id,
            duration_minutes=session.duration_minutes,
            focus_topic=session.focus_topic,
            status=session.status,
            started_at=session.started_at,
            expected_end_at=session.expected_end_at,
            interruptions=0,
            xp_earned=0,
            time_remaining_seconds=session.duration_minutes * 60,
        )

    @staticmethod
    async def get_session(
        session_id: str,
        user_id: str,
    ) -> Optional[StudySessionResponse]:
        """Get a study session by ID."""
        db = await get_database()
        
        doc = await db.study_sessions.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id,
        })
        
        if not doc:
            return None
        
        session = StudySessionInDB(**doc)
        now = datetime.now(timezone.utc)
        time_remaining = max(
            0,
            int((session.expected_end_at - now).total_seconds()),
        )
        
        return StudySessionResponse(
            _id=str(session.id),
            companion_id=session.companion_id,
            duration_minutes=session.duration_minutes,
            focus_topic=session.focus_topic,
            status=session.status,
            started_at=session.started_at,
            expected_end_at=session.expected_end_at,
            interruptions=session.interruptions,
            xp_earned=session.xp_earned,
            time_remaining_seconds=time_remaining,
        )

    @staticmethod
    async def complete_session(
        session_id: str,
        user_id: str,
    ) -> Optional[StudyCompleteResponse]:
        """Mark a study session as completed."""
        db = await get_database()
        now = datetime.now(timezone.utc)
        
        doc = await db.study_sessions.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id,
        })
        
        if not doc:
            return None
        
        session = StudySessionInDB(**doc)
        
        # Calculate XP
        base_xp = 10
        duration_bonus = session.duration_minutes
        interruption_penalty = session.interruptions * 5
        xp_earned = max(5, base_xp + duration_bonus - interruption_penalty)
        
        # Generate congratulations message
        congrats = StudyService._get_congratulations_message(
            companion_id=session.companion_id,
            xp=xp_earned,
            topic=session.focus_topic,
        )
        
        # Update session
        await db.study_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": now,
                    "xp_earned": xp_earned,
                }
            }
        )
        
        return StudyCompleteResponse(
            session_id=str(session.id),
            status="completed",
            xp_earned=xp_earned,
            completed_at=now,
            companion_congratulations=congrats,
        )
        
    @staticmethod
    def _get_congratulations_message(companion_id: str, xp: int, topic: Optional[str]):
        companion = companions.get(companion_id, {})
        name = companion.get("name", "Study Buddy")

        if companion_id == "rival":
            return f"Not bad. You earned {xp} XP. Let's see if you can do better next time."
        elif companion_id == "party_friend":
            return f"YAYYY!!! You did it! {xp} XP! You totally deserve a break! 🎉"
        else:
            return f"Great job! You earned {xp} XP! {f'Seems like {topic} is going well!' if topic else 'Keep going!'}"

    @staticmethod
    async def get_leaderboard(user_id: str) -> StudyLeaderboardResponse:
        """Get study leaderboard."""
        db = await get_database()
        
        pipeline = [
            {
                "$match": {
                    "status": "completed"
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "total_focus_minutes": {"$sum": "$duration_minutes"},
                    "completed_sessions": {"$sum": 1}
                }
            },
            {
                "$sort": {"total_focus_minutes": -1}
            },
            {
                "$limit": 10
            }
        ]
        
        entries_cursor = db.study_sessions.aggregate(pipeline)
        entries: list[StudyLeaderboardEntry] = []
        
        user_rank: Optional[int] = None
        user_total: Optional[int] = None
        
        rank = 1
        async for doc in entries_cursor:
            user_doc = await db.users.find_one({"_id": ObjectId(doc["_id"])})
            name = user_doc.get("full_name", "Anonymous") if user_doc else "Anonymous"
            
            entry = StudyLeaderboardEntry(
                rank=rank,
                user_name=name,
                total_focus_minutes=doc["total_focus_minutes"],
                completed_sessions=doc["completed_sessions"]
            )
            
            entries.append(entry)
            
            if doc["_id"] == user_id:
                user_rank = rank
                user_total = doc["total_focus_minutes"]
                
            rank +=1
            
        return StudyLeaderboardResponse(
            entries=entries,
            user_rank=user_rank,
            user_total_minutes=user_total,
        )
