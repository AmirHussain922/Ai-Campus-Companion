"""
Study Mode / War Room API for AI Campus Companion.
Provides endpoints for managing study sessions.
"""
from fastapi import APIRouter, Depends
from app.core.auth import get_current_active_user
from app.models import (
    StudySessionCreate,
    StudySessionResponse,
    StudyCompleteResponse,
    StudyLeaderboardResponse,
    UserInDB,
)
from app.services.study_service import StudyService

router = APIRouter(prefix="/study", tags=["study"])


@router.post("/sessions", response_model=dict)
async def create_study_session(
    request: StudySessionCreate,
    user: UserInDB = Depends(get_current_active_user),
):
    """Create a new study session."""
    # Track quest progress for starting a study session
    from app.services.quest_service import QuestService
    await QuestService.track_study_session_start(str(user.id))
    
    session = await StudyService.create_study_session(
        user_id=str(user.id),
        request=request,
    )
    
    return {
        "success": True,
        "session": session,
    }


@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """Get a study session by ID."""
    session = await StudyService.get_session(
        session_id=session_id,
        user_id=str(user.id),
    )
    
    if not session:
        return {"success": False, "message": "Session not found"}
    
    return {
        "success": True,
        "session": session,
    }


@router.post("/sessions/{session_id}/complete", response_model=dict)
async def complete_session(
    session_id: str,
    user: UserInDB = Depends(get_current_active_user),
):
    """Mark a study session as completed."""
    result = await StudyService.complete_session(
        session_id=session_id,
        user_id=str(user.id),
    )
    
    if not result:
        return {"success": False, "message": "Session not found"}
    
    return {
        "success": True,
        "session": result,
    }


@router.get("/leaderboard", response_model=dict)
async def get_study_leaderboard(
    user: UserInDB = Depends(get_current_active_user),
):
    """Get study leaderboard."""
    leaderboard = await StudyService.get_leaderboard(str(user.id))
    return {
        "success": True,
        "leaderboard": leaderboard.entries,
    }
