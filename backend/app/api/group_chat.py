"""
Group Chat / Campus Lounge API for AI Campus Companion.
Provides endpoints for sending messages and fetching chat history.
"""
from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_active_user
from app.models import (
    GroupChatHistoryResponse,
    GroupChatSendRequest,
    GroupChatSendResponse,
    GroupMessageResponse,
    UserInDB,
)
from app.services.group_chat_service import GroupChatService

router = APIRouter(prefix="/group-chat", tags=["group-chat"])


@router.post("/messages", response_model=dict)
async def send_group_message(
    request: GroupChatSendRequest,
    user: UserInDB = Depends(get_current_active_user),
):
    """Send a message to the campus lounge (group chat)."""
    # Track quest progress for sending messages
    from app.services.quest_service import QuestService
    await QuestService.track_quest_progress(str(user.id), "send_message")
    
    response = await GroupChatService.send_group_message(
        user_id=str(user.id),
        content=request.content,
        reply_to=request.reply_to,
    )
    
    # Optimistically add all messages to the state
    return {
        "success": True,
        "user_message": response.user_message,
        "companion_replies": response.companion_replies,
    }


@router.get("/messages", response_model=dict)
async def get_group_chat_history(
    limit: int = Query(50, ge=10, le=200),
    before: str = Query(None),
    user: UserInDB = Depends(get_current_active_user),
):
    """Get campus lounge chat history."""
    history = await GroupChatService.get_group_history(
        user_id=str(user.id),
        limit=limit,
    )
    
    return {
        "success": True,
        "messages": history.messages,
        "participants": history.participants,
        "total": history.total,
    }
