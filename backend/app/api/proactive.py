"""
Proactive messaging routes for AI Campus Companion.

Provides endpoints for retrieving and managing companion-initiated messages.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_active_user
from app.models import (
    ProactiveHistoryResponse,
    ProactiveMessageResponse,
    UnreadProactiveMessagesResponse,
    UserInDB,
)
from app.services.proactive_service import ProactiveService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proactive", tags=["proactive"])


@router.get("/unread", response_model=list[UnreadProactiveMessagesResponse])
async def get_unread_proactive_messages(
    user: UserInDB = Depends(get_current_active_user),
) -> list[UnreadProactiveMessagesResponse]:
    """
    Get all unread proactive messages grouped by companion.
    
    Returns a list of companions with their unread message counts and message details.
    """
    user_id = str(user.id)
    return await ProactiveService.get_unread_proactive_messages(user_id)


@router.post("/read/{message_id}", response_model=dict)
async def mark_proactive_message_as_read(
    message_id: str,
    user: UserInDB = Depends(get_current_active_user),
) -> dict:
    """
    Mark a proactive message as read.
    
    Args:
        message_id: The ID of the message to mark as read
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If message not found or doesn't belong to user
    """
    user_id = str(user.id)
    success = await ProactiveService.mark_as_read(message_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Message not found or already read"
        )
    
    return {
        "success": True,
        "message": "Message marked as read"
    }


@router.get("/history/{companion_id}", response_model=ProactiveHistoryResponse)
async def get_proactive_history(
    companion_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user: UserInDB = Depends(get_current_active_user),
) -> ProactiveHistoryResponse:
    """
    Get proactive message history with a specific companion.
    
    Args:
        companion_id: The ID of the companion
        page: Page number (1-indexed)
        per_page: Number of messages per page
        
    Returns:
        Paginated list of proactive messages with the companion
    """
    user_id = str(user.id)
    history = await ProactiveService.get_proactive_history(
        user_id=user_id,
        companion_id=companion_id,
        page=page,
        per_page=per_page,
    )
    
    return ProactiveHistoryResponse(
        messages=history["messages"],
        total=history["total"],
        page=history["page"],
        per_page=history["per_page"],
    )


@router.get("/messages/{message_id}", response_model=ProactiveMessageResponse)
async def get_proactive_message(
    message_id: str,
    user: UserInDB = Depends(get_current_active_user),
) -> ProactiveMessageResponse:
    """
    Get a specific proactive message by ID.
    
    Args:
        message_id: The ID of the message
        
    Returns:
        The proactive message details
        
    Raises:
        HTTPException: If message not found or doesn't belong to user
    """
    from app.core.database import get_database
    from bson import ObjectId
    
    db = await get_database()
    user_id = str(user.id)
    
    message = await db.companion_initiated_messages.find_one({
        "_id": ObjectId(message_id),
        "user_id": user_id,
    })
    
    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )
    
    return ProactiveMessageResponse(
        id=str(message["_id"]),
        companion_id=message["companion_id"],
        trigger_type=message["trigger_type"],
        content=message["content"],
        sent_at=message["created_at"],
        is_read=message.get("is_read", False),
    )