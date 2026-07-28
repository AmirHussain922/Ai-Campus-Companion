"""
Campus Quests Router for AI Campus Companion.

Provides endpoints for managing daily quests, completion submissions, and quest history.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path

from app.core.auth import get_current_active_user
from app.models import (
    QuestCompletionRequest,
    QuestCompletionResponse,
    QuestHistoryResponse,
    UserInDB,
    UserQuestResponse,
)
from app.services.quest_service import QuestService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quests", tags=["quests"])


@router.get("/active", response_model=list[UserQuestResponse])
async def get_active_quests(
    user: UserInDB = Depends(get_current_active_user),
) -> list[UserQuestResponse]:
    """
    Get user's active quests for today.
    
    Returns a list of quests that are currently active and can be completed.
    """
    user_id = str(user.id)
    quests = await QuestService.get_active_quests(user_id)
    return quests


@router.post("/complete/{quest_id}", response_model=QuestCompletionResponse)
async def complete_quest(
    quest_id: str = Path(..., description="The ID of the quest to complete"),
    request: QuestCompletionRequest = ...,
    user: UserInDB = Depends(get_current_active_user),
) -> QuestCompletionResponse:
    """
    Submit a quest completion report.
    
    The report will be verified by the companion who assigned the quest.
    If verified, XP will be awarded and the quest will be marked as completed.
    If rejected, you may retry once with a more detailed report.
    """
    user_id = str(user.id)
    
    result = await QuestService.submit_quest_completion(
        user_id=user_id,
        quest_id=quest_id,
        report_text=request.report_text,
    )
    
    if not result.success and result.verified is None:
        # Internal error
        raise HTTPException(status_code=500, detail=result.message)
    
    return result


@router.get("/history", response_model=QuestHistoryResponse)
async def get_quest_history(
    user: UserInDB = Depends(get_current_active_user),
) -> QuestHistoryResponse:
    """
    Get user's complete quest history.
    
    Returns all quests organized by status: active, completed, and failed.
    """
    user_id = str(user.id)
    history = await QuestService.get_quest_history(user_id)
    return history


@router.get("/{quest_id}", response_model=UserQuestResponse)
async def get_quest_details(
    quest_id: str = Path(..., description="The ID of the quest"),
    user: UserInDB = Depends(get_current_active_user),
) -> UserQuestResponse:
    """
    Get details of a specific quest.
    """
    from app.core.database import get_database
    from bson import ObjectId
    
    db = await get_database()
    user_id = str(user.id)
    
    quest_doc = await db.user_quests.find_one({
        "user_id": user_id,
        "quest_id": quest_id,
    })
    
    if not quest_doc:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    return UserQuestResponse(**quest_doc)