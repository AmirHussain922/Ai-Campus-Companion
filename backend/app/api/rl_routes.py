"""
RL routes for trainable companions.

Provides endpoints for RL action recommendations, feedback,
training triggers, and agent status per companion.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.models import UserInDB
from app.ml.rl_agent import (
    ConversationRLAgent,
    ConversationState,
    RLAction,
    get_all_agents,
    get_rl_agent,
)
from app.ml.rl_training import run_training_for_all_companions

router = APIRouter(prefix="/rl", tags=["reinforcement-learning"])


class RLActionResponse(BaseModel):
    action_type: str
    intensity: float
    topic_focus: Optional[str] = None
    confidence: float
    explanation: str


class RLFeedbackRequest(BaseModel):
    companion_id: str
    user_message: str
    companion_response: str
    user_feedback: int  # -1, 0, 1
    response_quality: float = 0.5
    conversation_history: List[Dict[str, str]] = []
    user_engagement_score: float = 0.5
    previous_feedback: List[int] = []


class RLTrainingResponse(BaseModel):
    success: bool
    message: str
    results: list[dict]


class RLAgentStatus(BaseModel):
    companion_id: str
    is_initialized: bool
    epsilon: float
    experience_buffer_size: int
    average_reward: Optional[float] = None


@router.get("/status", response_model=list[RLAgentStatus])
async def get_all_agent_status() -> list[RLAgentStatus]:
    """Get status of all RL agents."""
    agents = get_all_agents()
    results = []
    for cid, agent in agents.items():
        recent_rewards = []
        if agent.experience_buffer:
            recent = agent.experience_buffer[-100:]
            recent_rewards = [exp[2] for exp in recent if len(exp) > 2]
        avg = float(np.mean(recent_rewards)) if recent_rewards else None
        results.append(RLAgentStatus(
            companion_id=cid,
            is_initialized=True,
            epsilon=agent.epsilon,
            experience_buffer_size=len(agent.experience_buffer),
            average_reward=avg,
        ))
    return results


@router.get("/status/{companion_id}", response_model=RLAgentStatus)
async def get_agent_status(companion_id: str) -> RLAgentStatus:
    """Get status of a specific RL agent."""
    agent = get_rl_agent(companion_id)
    recent_rewards = []
    if agent.experience_buffer:
        recent = agent.experience_buffer[-100:]
        recent_rewards = [exp[2] for exp in recent if len(exp) > 2]
    avg = float(np.mean(recent_rewards)) if recent_rewards else None
    return RLAgentStatus(
        companion_id=companion_id,
        is_initialized=True,
        epsilon=agent.epsilon,
        experience_buffer_size=len(agent.experience_buffer),
        average_reward=avg,
    )


@router.post("/feedback", response_model=Dict[str, Any])
async def update_with_feedback(
    request: RLFeedbackRequest,
    user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update RL agent with user feedback for a specific companion."""
    agent = get_rl_agent(request.companion_id)

    state = ConversationState(
        user_message=request.user_message,
        conversation_history=request.conversation_history,
        companion_traits=[],
        user_engagement_score=request.user_engagement_score,
        conversation_length=len(request.conversation_history),
        previous_feedback=request.previous_feedback,
        companion_id=request.companion_id,
    )

    action = RLAction(action_type="deep_dive", intensity=0.5)

    reward = agent.calculate_reward(
        previous_state=state,
        action=action,
        user_feedback=request.user_feedback,
        response_quality=request.response_quality,
    )

    next_state = ConversationState(
        user_message="",
        conversation_history=request.conversation_history + [
            {"role": "user", "content": request.user_message},
            {"role": "assistant", "content": request.companion_response},
        ],
        companion_traits=[],
        user_engagement_score=max(
            0.0, min(1.0, request.user_engagement_score + (request.user_feedback * 0.1))
        ),
        conversation_length=len(request.conversation_history) + 2,
        previous_feedback=request.previous_feedback + [request.user_feedback],
        companion_id=request.companion_id,
    )

    agent.update_policy(state=state, action=action, reward=reward, next_state=next_state)

    return {
        "success": True,
        "reward": reward,
        "epsilon": agent.epsilon,
        "companion_id": request.companion_id,
    }


@router.post("/train", response_model=RLTrainingResponse)
async def train_agents() -> RLTrainingResponse:
    """Trigger training for all trainable companions."""
    try:
        results = await run_training_for_all_companions()
        return RLTrainingResponse(
            success=True,
            message="Training completed",
            results=results,
        )
    except Exception as e:
        return RLTrainingResponse(
            success=False,
            message=f"Training failed: {str(e)}",
            results=[],
        )


@router.post("/save-model/{companion_id}")
async def save_model(companion_id: str) -> Dict[str, Any]:
    """Save a companion's RL model to disk."""
    agent = get_rl_agent(companion_id)
    filepath = f"models/rl_{companion_id}_checkpoint.pth"
    agent.save_model(filepath)
    return {"success": True, "filepath": filepath}
