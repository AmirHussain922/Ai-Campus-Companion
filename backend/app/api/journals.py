"""
Journal routes for companion diary entries.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models import JournalEntryResponse, JournalReadRequest, UserInDB
from app.services.journal_service import JournalService
from app.companions.companions import resolve_backend_id

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/journals/{companion_id}", response_model=list[JournalEntryResponse])
async def get_journals(
    companion_id: str,
    user: UserInDB = Depends(get_current_active_user),
) -> list[JournalEntryResponse]:
    """Get all unlocked journal entries for a specific companion."""
    try:
        backend_id = resolve_backend_id(companion_id)
        journals = await JournalService.get_unlocked_journals(str(user.id), backend_id)
        return [
            JournalEntryResponse(
                id=str(j.id),
                user_id=j.user_id,
                companion_id=j.companion_id,
                stage=j.stage,
                entry_text=j.entry_text,
                is_unlocked=j.is_unlocked,
                unlocked_at=j.unlocked_at,
                is_read=j.is_read,
                generated_at=j.generated_at,
            )
            for j in journals
        ]
    except Exception as e:
        logger.error(f"Error getting journals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get journals",
        )


@router.get("/journals/{companion_id}/{stage}", response_model=Optional[JournalEntryResponse])
async def get_journal_entry(
    companion_id: str,
    stage: int,
    user: UserInDB = Depends(get_current_active_user),
) -> Optional[JournalEntryResponse]:
    """Get a specific journal entry by stage."""
    try:
        backend_id = resolve_backend_id(companion_id)
        journal = await JournalService.get_journal_entry(str(user.id), backend_id, stage)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found",
            )
        if not journal.is_unlocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Journal entry not unlocked yet",
            )
        return JournalEntryResponse(
            id=str(journal.id),
            user_id=journal.user_id,
            companion_id=journal.companion_id,
            stage=journal.stage,
            entry_text=journal.entry_text,
            is_unlocked=journal.is_unlocked,
            unlocked_at=journal.unlocked_at,
            is_read=journal.is_read,
            generated_at=journal.generated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting journal entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get journal entry",
        )


@router.post("/journals/{companion_id}/{stage}/read", response_model=Optional[JournalEntryResponse])
async def mark_journal_read(
    companion_id: str,
    stage: int,
    user: UserInDB = Depends(get_current_active_user),
) -> Optional[JournalEntryResponse]:
    """Mark a journal entry as read."""
    try:
        backend_id = resolve_backend_id(companion_id)
        journal = await JournalService.mark_journal_as_read(str(user.id), backend_id, stage)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found",
            )
        return JournalEntryResponse(
            id=str(journal.id),
            user_id=journal.user_id,
            companion_id=journal.companion_id,
            stage=journal.stage,
            entry_text=journal.entry_text,
            is_unlocked=journal.is_unlocked,
            unlocked_at=journal.unlocked_at,
            is_read=journal.is_read,
            generated_at=journal.generated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking journal as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark journal as read",
        )
