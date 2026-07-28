"""
Episode API routes.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models import (
    UserInDB,
    EpisodeResponse,
    EpisodeProgressResponse,
    EpisodeChoiceRequest,
    EpisodeChoiceResponse,
    EpisodeScriptNode,
)
from app.services.episode_service import EpisodeService
from app.companions.companions import resolve_backend_id

router = APIRouter(prefix="/episodes", tags=["episodes"])

logger = logging.getLogger(__name__)


@router.get("/{companion_id}", response_model=list[EpisodeResponse])
async def get_available_episodes(
    companion_id: str,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """Get all available episodes for a specific companion."""
    try:
        resolved_companion_id = resolve_backend_id(companion_id)
        episodes = await EpisodeService.get_available_episodes(
            str(current_user.id),
            resolved_companion_id,
        )
        # Convert to response model
        return [
            EpisodeResponse(
                _id=str(ep.id),
                companion_id=ep.companion_id,
                title=ep.title,
                description=ep.description,
                required_relationship_stage=ep.required_relationship_stage,
                script_nodes=ep.script_nodes,
                created_at=ep.created_at,
            )
            for ep in episodes
        ]
    except Exception as e:
        logger.error(f"Error getting available episodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available episodes",
        )


@router.post("/start", response_model=EpisodeProgressResponse)
async def start_episode(
    episode_id: str,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """Start an episode."""
    try:
        progress = await EpisodeService.start_episode(
            str(current_user.id),
            episode_id,
        )
        return EpisodeProgressResponse(
            _id=str(progress.id),
            user_id=progress.user_id,
            episode_id=progress.episode_id,
            companion_id=progress.companion_id,
            status=progress.status,
            current_node_id=progress.current_node_id,
            total_xp_earned=progress.total_xp_earned,
            completed_at=progress.completed_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error starting episode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start episode",
        )


@router.get("/state/{episode_id}", response_model=EpisodeScriptNode)
async def get_episode_state(
    episode_id: str,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """Get the current state of an episode."""
    try:
        state = await EpisodeService.get_episode_state(
            str(current_user.id),
            episode_id,
        )
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Episode state not found or episode is completed",
            )
        return state
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting episode state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get episode state",
        )


@router.post("/choice", response_model=EpisodeChoiceResponse)
async def make_choice(
    request: EpisodeChoiceRequest,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """Make a choice in an episode."""
    try:
        result = await EpisodeService.make_choice(
            str(current_user.id),
            request.episode_id,
            request.choice_id,
        )
        return EpisodeChoiceResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error making choice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to make choice",
        )


@router.get("/completed/{companion_id}", response_model=list[EpisodeProgressResponse])
async def get_completed_episodes(
    companion_id: str,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """Get all completed episodes for a specific companion."""
    try:
        resolved_companion_id = resolve_backend_id(companion_id)
        completed = await EpisodeService.get_completed_episodes(
            str(current_user.id),
            resolved_companion_id,
        )
        return [
            EpisodeProgressResponse(
                _id=str(p.id),
                user_id=p.user_id,
                episode_id=p.episode_id,
                companion_id=p.companion_id,
                status=p.status,
                current_node_id=p.current_node_id,
                total_xp_earned=p.total_xp_earned,
                completed_at=p.completed_at,
            )
            for p in completed
        ]
    except Exception as e:
        logger.error(f"Error getting completed episodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get completed episodes",
        )
