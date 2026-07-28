"""
Chat routes with dual-pipeline architecture.

- Trainable companions (Julian, Victoria): Full RL + memory + embeddings +
  session tracking + XP progression + per-companion model routing.
- Demo companions (Oliver, Chloe, Toby): Lightweight personality-prompt chat.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, get_current_active_user
from app.companions.companions import companions, get_companion_tier, resolve_backend_id
from app.config import get_settings
from app.core.database import get_database
from app.models import ChatRequestV2, ChatResponseV2, CompanionProgression, UserInDB
from app.services.openrouter_client import OpenRouterError, generate_reply
from app.companions.prompt_builder import build_messages
from app.core.security import sanitize_input
from app.utils.rate_limiter import check_rate_limit, RateLimitAction

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Companion listing (no auth required)
# ---------------------------------------------------------------------------

class CompanionListItem(BaseModel):
    id: str
    name: str
    tier: str


@router.get("/companions", response_model=list[CompanionListItem])
async def list_companions() -> list[CompanionListItem]:
    return [
        CompanionListItem(
            id=cid,
            name=data["name"],
            tier=get_companion_tier(cid),
        )
        for cid, data in companions.items()
    ]


# ---------------------------------------------------------------------------
# Main chat endpoint — dual pipeline
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponseV2)
async def chat(
    req: ChatRequestV2,
    request: Request,
    user: UserInDB = Depends(get_current_active_user),
) -> ChatResponseV2:
    settings = get_settings()
    user_id = str(user.id)
    
    # Track quest progress for sending messages
    from app.services.quest_service import QuestService
    await QuestService.track_quest_progress(user_id, "send_message")

    # Rate limiting for chat endpoint (30 messages per hour per user to control API costs)
    allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.CHAT,
        identifier=f"chat:{user_id}"
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Too many messages. Please wait before sending another.",
                "retry_after": rate_info.get("reset_timestamp", 0)
            }
        )

    # Sanitize user message to prevent XSS and injection attacks
    try:
        sanitized_message = sanitize_input(
            req.message,
            max_length=settings.max_message_length,
            allow_html=False,
            check_sql=True,
            check_javascript=True
        )
        # Create a modified request with sanitized message
        req.message = sanitized_message
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 1. Resolve companion ID
    personality_id = req.personality_id or resolve_backend_id(req.companion_key)
    template = companions.get(personality_id)
    if not template:
        template = companions.get("study_buddy")
        personality_id = "study_buddy"

    tier = get_companion_tier(personality_id)

    # Dispatch to appropriate pipeline
    if tier == "trainable":
        return await _trainable_pipeline(
            req=req,
            user=user,
            user_id=user_id,
            personality_id=personality_id,
            template=template,
            settings=settings,
        )
    else:
        return await _demo_pipeline(
            req=req,
            user_id=user_id,
            personality_id=personality_id,
            template=template,
            settings=settings,
        )


# ---------------------------------------------------------------------------
# DEMO pipeline
# ---------------------------------------------------------------------------

async def _demo_pipeline(
    *,
    req: ChatRequestV2,
    user_id: str,
    personality_id: str,
    template: dict,
    settings,
) -> ChatResponseV2:
    """Lightweight chat — personality prompt with conversation history for context."""
    profile = req.companion_profile or {}
    companion_name = profile.get("name", template["name"])
    companion_age = profile.get("age", template.get("age"))
    companion_relationship = profile.get("relationship", template.get("relationship"))
    companion_story = profile.get("story", template.get("story"))
    companion_traits = profile.get("traits", template.get("traits"))
    relationship_stage = profile.get("relationshipStage")

    # Fetch conversation history from session for context-aware replies
    conversation_history: list[dict] = []
    try:
        from app.utils.session_manager import get_or_create_session, get_session_messages
        await get_or_create_session(
            user_id=user_id,
            companion_id=personality_id,
            episode_id=req.episode_id,
        )
        session_messages = await get_session_messages(
            user_id=user_id, companion_id=personality_id, limit=10,
        )
        conversation_history = [
            {"role": m["role"], "content": m["content"]}
            for m in session_messages
            if m.get("role") in ("user", "assistant")
        ]
    except Exception as e:
        logger.warning(f"Demo session history fetch failed: {e}")

    messages, _ = build_messages(
        companion_id=personality_id,
        companion_name=companion_name,
        companion_age=companion_age,
        companion_relationship=companion_relationship,
        companion_story=companion_story,
        companion_traits=companion_traits,
        companion_system_prompt=template["system_prompt"],
        scenario_memory=req.scenario_text,
        retrieved_memories=[],
        user_message=req.message,
        conversation_history=conversation_history,
        use_rl_optimization=False,
        relationship_stage=relationship_stage,
        story_context=req.scenario_text,
    )

    model = settings.get_model_for_companion(personality_id)
    try:
        reply = await generate_reply(messages=messages, model=model)
    except OpenRouterError as e:
        logger.error(f"OpenRouter error for {personality_id} (model={model}): {e}")
        reply = (
            f"Hey — I'm here but having trouble connecting to my AI service right now. "
            f"Tell me what you'd like to talk about and I'll do my best!"
        )
    except Exception as e:
        logger.error(f"Unexpected error generating reply for {personality_id}: {type(e).__name__}: {e}")
        reply = (
            f"Hey — I'm here but having trouble connecting to my AI service right now. "
            f"Tell me what you'd like to talk about and I'll do my best!"
        )

    # Store conversation in session for future context
    try:
        from app.utils.session_manager import get_or_create_session, append_message_to_session
        session = await get_or_create_session(
            user_id=user_id,
            companion_id=personality_id,
            episode_id=req.episode_id,
        )
        session_id = str(session.get("_id", ""))
        logger.info(f"Step 3: Session created/obtained: {session_id}")

        # --- Get user's progression for this companion ---
        logger.info("Step 4: Getting user progression")
        await append_message_to_session(
            session_id=session_id, role="user", content=req.message,
        )
        await append_message_to_session(
            session_id=session_id, role="assistant", content=reply,
        )
    except Exception as e:
        logger.warning(f"Demo session update failed: {e}")

    return ChatResponseV2(
        companion=companion_name,
        reply=reply,
        companion_id=personality_id,
        tier="demo",
    )


# ---------------------------------------------------------------------------
# TRAINABLE pipeline
# ---------------------------------------------------------------------------

async def _trainable_pipeline(
    *,
    req: ChatRequestV2,
    user: UserInDB,
    user_id: str,
    personality_id: str,
    template: dict,
    settings,
) -> ChatResponseV2:
    """Full RL pipeline with memory, embeddings, sessions, XP, and model routing."""
    logger.info(f"=== TRAINABLE PIPELINE START for {personality_id} ===")

    from app.utils.session_manager import (
        get_or_create_session,
        append_message_to_session,
        append_rl_action,
        update_session_xp,
        get_session_messages,
    )
    from app.memory.companion_memory import (
        get_relevant_memories,
        get_latest_scenario,
        remember_conversation_exchange,
        remember_fact,
    )
    from app.memory.companion_memory_store import store_rl_transition
    from app.ml.xp_evaluator import evaluate_xp, get_relationship_stage

    logger.info("Step 1: Imports successful")

    # --- Get/create session ---
    logger.info("Step 2: Getting/creating session")
    session = await get_or_create_session(
        user_id=user_id,
        companion_id=personality_id,
        episode_id=req.episode_id,
    )
    session_id = str(session.get("_id", ""))

    # --- Get user's progression for this companion ---
    progression = _get_companion_progression(user, personality_id)
    relationship_points = progression.relationship_points
    xp = progression.xp
    level = progression.level
    relationship_stage = get_relationship_stage(relationship_points)
    has_active_scenario = progression.current_episode_id is not None
    logger.info(f"Step 5: Progression loaded - XP: {xp}, Level: {level}, Stage: {relationship_stage}")

    # --- Server-side XP evaluation ---
    logger.info("Step 6: Evaluating XP")
    session_messages = await get_session_messages(
        user_id=user_id, companion_id=personality_id, limit=5,
    )
    recent_user_msgs = [
        m.get("content", "") for m in session_messages if m.get("role") == "user"
    ]
    xp_delta, xp_reasons = evaluate_xp(
        text=req.message,
        recent_user_messages=recent_user_msgs,
        has_active_scenario=has_active_scenario,
    )
    logger.info(f"Step 7: XP delta calculated: {xp_delta}")

    # --- Retrieve companion memories (semantic search) ---
    logger.info("Step 8: Retrieving memories")
    companion_memory_context = ""
    try:
        relevant = await get_relevant_memories(
            user_id=user_id,
            companion_id=personality_id,
            query=req.message,
            k=5,
        )
        if relevant:
            lines = [f"- ({m.memory_type}) {m.content[:200]}" for m in relevant]
            companion_memory_context = "\n".join(lines)
    except Exception as e:
        logger.error(f"Memory retrieval failed: {e}", exc_info=True)

    # --- Get latest scenario ---
    logger.info("Step 9: Getting scenario")
    scenario_text = req.scenario_text
    if not scenario_text:
        try:
            scenario_mem = await get_latest_scenario(
                user_id=user_id, companion_id=personality_id,
            )
            if scenario_mem:
                scenario_text = scenario_mem.content
        except Exception:
            pass
    logger.info(f"Step 10: Scenario text length: {len(scenario_text) if scenario_text else 0}")

    # --- RL action ---
    logger.info("Step 11: Starting RL action selection")
    rl_action = None
    conversation_state = None
    try:
        conv_history = [
            {"role": m["role"], "content": m["content"]}
            for m in session_messages
            if m.get("role") in ("user", "assistant")
        ]

        profile = req.companion_profile or {}
        companion_traits = profile.get("traits", template.get("traits"))

        logger.info(f"Building messages with RL for {personality_id}")
        messages, rl_action = build_messages(
            companion_id=personality_id,
            companion_name=profile.get("name", template["name"]),
            companion_age=profile.get("age", template.get("age")),
            companion_relationship=profile.get("relationship", template.get("relationship")),
            companion_story=profile.get("story", template.get("story")),
            companion_traits=companion_traits,
            companion_system_prompt=template["system_prompt"],
            scenario_memory=scenario_text,
            retrieved_memories=[],
            user_message=req.message,
            conversation_history=conv_history,
            user_engagement_score=0.5,
            previous_feedback=[],
            use_rl_optimization=True,
            relationship_stage=relationship_stage,
            story_context=scenario_text,
            companion_memory_context=companion_memory_context,
            rl_companion_id=personality_id,
            rl_relationship_level=relationship_points,
            rl_xp=xp,
            rl_level=level,
            rl_episode_id=req.episode_id,
        )
        logger.info(f"RL action selected: {rl_action.action_type if rl_action else 'None'}")

        # Keep conversation_state for later transition storage
        if rl_action is not None:
            from ..rl_agent import ConversationState, get_rl_agent
            agent = get_rl_agent(personality_id)
            conversation_state = ConversationState(
                user_message=req.message,
                conversation_history=conv_history,
                companion_traits=companion_traits or [],
                user_engagement_score=0.5,
                conversation_length=len(conv_history),
                previous_feedback=[],
                companion_id=personality_id,
                relationship_level=relationship_points,
                relationship_stage=relationship_stage,
                xp=xp,
                level=level,
                episode_id=req.episode_id,
            )
    except Exception as e:
        logger.error(f"RL action selection failed: {e}", exc_info=True)
        # Fallback: build messages without RL
        logger.info(f"Falling back to non-RL mode for {personality_id}")
        profile = req.companion_profile or {}
        messages, _ = build_messages(
            companion_id=personality_id,
            companion_name=profile.get("name", template["name"]),
            companion_age=profile.get("age", template.get("age")),
            companion_relationship=profile.get("relationship", template.get("relationship")),
            companion_story=profile.get("story", template.get("story")),
            companion_traits=profile.get("traits", template.get("traits")),
            companion_system_prompt=template["system_prompt"],
            scenario_memory=scenario_text,
            retrieved_memories=[],
            user_message=req.message,
            use_rl_optimization=False,
            relationship_stage=relationship_stage,
            companion_memory_context=companion_memory_context,
        )
        logger.info("Step 12: Fallback messages built successfully")

    # --- Call OpenRouter with companion-specific model ---
    logger.info("Step 13: Preparing to call OpenRouter")

    # --- Call OpenRouter with companion-specific model ---
    model = settings.get_model_for_companion(personality_id)
    logger.info(f"Calling OpenRouter for {personality_id} with model={model}")
    try:
        reply = await generate_reply(messages=messages, model=model)
        logger.info(f"OpenRouter reply received for {personality_id}: {reply[:50]}...")
    except OpenRouterError as e:
        logger.error(f"OpenRouterError for {personality_id} (model={model}): {e}")
        trait_hint = ", ".join(template.get("traits", [])[:3])
        reply = (
            f"Hey — I'm here but having trouble connecting right now. "
            f"Tell me what you'd like to talk about ({trait_hint}) and I'll respond."
        )
    except Exception as e:
        logger.error(f"Unexpected error generating reply for {personality_id}: {type(e).__name__}: {e}")
        trait_hint = ", ".join(template.get("traits", [])[:3])
        reply = (
            f"Hey — I'm here but having trouble connecting right now. "
            f"Tell me what you'd like to talk about ({trait_hint}) and I'll respond."
        )

    # --- Store session messages ---
    try:
        await append_message_to_session(
            session_id=session_id, role="user", content=req.message,
        )
        await append_message_to_session(
            session_id=session_id, role="assistant", content=reply,
        )
        if rl_action:
            await append_rl_action(
                session_id=session_id,
                action_dict={
                    "action_type": rl_action.action_type,
                    "intensity": rl_action.intensity,
                },
            )
        await update_session_xp(
            session_id=session_id,
            xp_delta=xp_delta,
            relationship_delta=xp_delta,  # same delta for relationship
        )
    except Exception as e:
        logger.warning(f"Session update failed: {e}")

    # --- Update user progression ---
    new_relationship_points = max(0, relationship_points + xp_delta)
    new_xp = max(0, xp + xp_delta)
    new_stage = get_relationship_stage(new_relationship_points)
    new_level = level
    pending_level_up = False
    
    # Check if we need to set pending level up instead of auto-leveling
    xp_needed = _xp_for_next_level(level)
    if new_xp >= xp_needed:
        pending_level_up = True
        new_xp = xp_needed  # Cap XP at max for current level

    await _update_companion_progression(
        user_id=user_id,
        companion_id=personality_id,
        xp=new_xp,
        level=new_level,
        relationship_points=new_relationship_points,
        relationship_stage=new_stage,
        episode_id=req.episode_id,
        pending_level_up=pending_level_up,
    )
    
    # --- Handle journal generation and unlocking ---
    try:
        from app.services.journal_service import JournalService
        from app.ml.xp_evaluator import _RELATIONSHIP_STAGES
        
        # Get new stage index
        new_stage_int = 0
        for i, (threshold, name) in enumerate(_RELATIONSHIP_STAGES):
            if new_stage == name:
                new_stage_int = i
        
        # Check if stage increased
        old_stage_int = 0
        for i, (threshold, name) in enumerate(_RELATIONSHIP_STAGES):
            if relationship_stage == name:
                old_stage_int = i
        
        if new_stage_int > old_stage_int:
            # Generate missing journals and unlock up to new stage
            await JournalService.check_and_generate_journals(user_id, personality_id)
            await JournalService.unlock_journals_up_to_stage(user_id, personality_id, new_stage_int)
    except Exception as e:
        logger.warning(f"Journal handling failed: {e}")

    # --- Store companion memory (important facts) ---
    try:
        msg_lower = req.message.lower()
        if len(req.message.strip()) >= 20 and (
            "my " in msg_lower or "i am " in msg_lower or "i'm " in msg_lower or "i have " in msg_lower
        ):
            await remember_fact(
                user_id=user_id,
                companion_id=personality_id,
                content=req.message,
            )
        await remember_conversation_exchange(
            user_id=user_id,
            companion_id=personality_id,
            user_message=req.message,
            companion_reply=reply,
        )
    except Exception as e:
        logger.warning(f"Memory storage failed: {e}")

    # --- Store RL transition for offline training ---
    if rl_action and conversation_state:
        try:
            from ..rl_agent import ConversationState as CS
            next_state = CS(
                user_message="",
                conversation_history=conversation_state.conversation_history + [
                    {"role": "user", "content": req.message},
                    {"role": "assistant", "content": reply},
                ],
                companion_traits=conversation_state.companion_traits,
                user_engagement_score=conversation_state.user_engagement_score,
                conversation_length=conversation_state.conversation_length + 2,
                previous_feedback=conversation_state.previous_feedback,
                companion_id=personality_id,
                relationship_level=new_relationship_points,
                relationship_stage=new_stage,
                xp=new_xp,
                level=new_level,
                episode_id=req.episode_id,
            )
            # Reward: xp_delta normalized
            reward = float(xp_delta)
            await store_rl_transition(
                user_id=user_id,
                companion_id=personality_id,
                state=conversation_state.model_dump(),
                action={
                    "action_type": rl_action.action_type,
                    "intensity": rl_action.intensity,
                    "topic_focus": rl_action.topic_focus,
                },
                reward=reward,
                next_state=next_state.model_dump(),
            )
        except Exception as e:
            logger.warning(f"RL transition storage failed: {e}")

    companion_name = (req.companion_profile or {}).get("name", template["name"])

    return ChatResponseV2(
        companion=companion_name,
        reply=reply,
        companion_id=personality_id,
        tier="trainable",
        xp_delta=xp_delta,
        total_xp=new_xp,
        level=new_level,
        relationship_stage=new_stage,
        rl_action=rl_action.action_type if rl_action else None,
        pending_level_up=pending_level_up,
    )


# ---------------------------------------------------------------------------
# Progression helpers
# ---------------------------------------------------------------------------

def _xp_for_next_level(level: int) -> int:
    """Calculate XP needed for the next level (100 * 1.5^(level-1))."""
    return int(100 * (1.5 ** (level - 1)))


def _get_companion_progression(user: UserInDB, companion_id: str) -> CompanionProgression:
    """Find companion progression from user document."""
    for p in (user.companion_progression or []):
        if p.get("companion_id") == companion_id:
            return CompanionProgression(**p)
    return CompanionProgression(companion_id=companion_id)


async def _update_companion_progression(
    *,
    user_id: str,
    companion_id: str,
    xp: int,
    level: int,
    relationship_points: int,
    relationship_stage: str,
    episode_id: str | None = None,
    pending_level_up: bool = False,
) -> None:
    """Update companion progression on user document."""
    db = await get_database()
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        return

    progression_list = list(user_doc.get("companion_progression", []))

    # Find and update existing or append new
    found = False
    for i, p in enumerate(progression_list):
        if p.get("companion_id") == companion_id:
            p["xp"] = xp
            p["level"] = level
            p["relationship_points"] = relationship_points
            p["relationship_stage"] = relationship_stage
            p["total_messages"] = p.get("total_messages", 0) + 1
            p["last_interaction"] = datetime.now(timezone.utc).isoformat()
            p["pending_level_up"] = pending_level_up
            if episode_id:
                p["current_episode_id"] = episode_id
            progression_list[i] = p
            found = True
            break

    if not found:
        progression_list.append({
            "companion_id": companion_id,
            "xp": xp,
            "level": level,
            "relationship_points": relationship_points,
            "relationship_stage": relationship_stage,
            "current_episode_id": episode_id,
            "episodes_unlocked": [],
            "total_messages": 1,
            "last_interaction": datetime.now(timezone.utc).isoformat(),
            "pending_level_up": pending_level_up,
        })

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"companion_progression": progression_list}},
    )


# ---------------------------------------------------------------------------
# Progression retrieval endpoint
# ---------------------------------------------------------------------------

class ProgressionResponse(BaseModel):
    companion_id: str
    xp: int
    level: int
    relationship_points: int
    relationship_stage: str
    total_messages: int
    episodes_unlocked: list[str] = Field(default_factory=list)
    pending_level_up: bool = False


@router.post("/companion/{companion_id}/unlock-level")
async def unlock_level(
    companion_id: str,
    user: UserInDB = Depends(get_current_active_user),
    db = Depends(get_database),
):
    """Unlock the next level for a companion when pending_level_up is True."""
    backend_id = resolve_backend_id(companion_id)
    user_doc = await db.users.find_one({"_id": user.id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    progression_list = list(user_doc.get("companion_progression", []))
    found = False
    
    for i, p in enumerate(progression_list):
        if p.get("companion_id") == backend_id:
            if not p.get("pending_level_up", False):
                raise HTTPException(status_code=400, detail="No pending level up")
            
            # Level up
            current_level = p.get("level", 1)
            new_level = current_level + 1
            xp_needed = _xp_for_next_level(current_level)
            
            # Reset XP and pending_level_up
            p["level"] = new_level
            p["xp"] = 0  # Reset XP for new level
            p["pending_level_up"] = False
            
            progression_list[i] = p
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    await db.users.update_one(
        {"_id": user.id},
        {"$set": {"companion_progression": progression_list}}
    )
    
    return {
        "success": True,
        "message": "Level unlocked successfully",
        "level": new_level
    }


@router.get("/progression/{companion_id}", response_model=ProgressionResponse)
async def get_progression(
    companion_id: str,
    user: UserInDB = Depends(get_current_user),
) -> ProgressionResponse:
    """Get user's progression for a specific companion."""
    backend_id = resolve_backend_id(companion_id)
    progression = _get_companion_progression(user, backend_id)
    return ProgressionResponse(
        companion_id=backend_id,
        xp=progression.xp,
        level=progression.level,
        relationship_points=progression.relationship_points,
        relationship_stage=progression.relationship_stage,
        total_messages=progression.total_messages,
        episodes_unlocked=progression.episodes_unlocked,
        pending_level_up=progression.pending_level_up,
    )


@router.delete("/companion/{companion_id}")
async def delete_companion(
    companion_id: str,
    user: UserInDB = Depends(get_current_active_user),
    db = Depends(get_database),
):
    """Delete a companion and all associated data for the user."""
    backend_id = resolve_backend_id(companion_id)
    
    # Remove from user's companion progression
    await db.users.update_one(
        {"_id": user.id},
        {"$pull": {"companion_progression": {"companion_id": backend_id}}}
    )
    
    # Delete companion memories
    await db.companion_memories.delete_many({
        "user_id": str(user.id),
        "companion_id": backend_id
    })
    
    # Delete conversation sessions
    await db.conversation_sessions.delete_many({
        "user_id": str(user.id),
        "companion_id": backend_id
    })
    
    # Delete RL transitions
    await db.rl_transitions.delete_many({
        "user_id": str(user.id),
        "companion_id": backend_id
    })
    
    return {"success": True, "message": f"Companion {backend_id} deleted successfully"}


@router.get("/progression", response_model=list[ProgressionResponse])
async def get_all_progression(
    user: UserInDB = Depends(get_current_user),
) -> list[ProgressionResponse]:
    """Get user's progression for all companions."""
    results = []
    for p in (user.companion_progression or []):
        prog = CompanionProgression(**p)
        results.append(ProgressionResponse(
            companion_id=prog.companion_id,
            xp=prog.xp,
            level=prog.level,
            relationship_points=prog.relationship_points,
            relationship_stage=prog.relationship_stage,
            total_messages=prog.total_messages,
            episodes_unlocked=prog.episodes_unlocked,
            pending_level_up=prog.pending_level_up,
        ))
    return results
