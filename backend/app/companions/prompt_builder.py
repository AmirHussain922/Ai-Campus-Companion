"""
Prompt builder for AI Campus Companion.

Constructs system prompts with personality, memories, scenario context,
RL action strategy, and relationship/story context for both trainable
and demo companions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_messages(
    *,
    companion_id: str,
    companion_name: str,
    companion_age: int | None,
    companion_relationship: str | None,
    companion_story: str | None,
    companion_traits: list[str] | None,
    companion_system_prompt: str,
    scenario_memory: str | None,
    retrieved_memories: list[dict],
    user_message: str,
    conversation_history: list[dict] | None = None,
    user_engagement_score: float = 0.5,
    previous_feedback: list[int] | None = None,
    use_rl_optimization: bool = False,
    # --- New trainable companion params ---
    relationship_stage: str | None = None,
    story_context: str | None = None,
    companion_memory_context: str | None = None,
    rl_action: Any = None,
    # Per-companion RL params (passed directly instead of calling RL here)
    rl_companion_id: str | None = None,
    rl_relationship_level: int = 0,
    rl_xp: int = 0,
    rl_level: int = 1,
    rl_episode_id: str | None = None,
    rl_emotional_state: str = "neutral",
) -> tuple[list[dict], Any]:
    """
    Build messages for the AI companion.

    Returns tuple of (messages, rl_action).
    If use_rl_optimization is True and rl_action is None, the RL agent is called
    internally.  If rl_action is already provided, it is used directly.
    """
    # Apply RL optimization if enabled and no action was pre-computed
    if use_rl_optimization and rl_action is None:
        try:
            from .rl_agent import apply_rl_to_conversation
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Calling RL agent for {companion_id}")

            rl_action, _ = apply_rl_to_conversation(
                user_message=user_message,
                conversation_history=conversation_history or [],
                companion_traits=companion_traits or [],
                user_engagement_score=user_engagement_score,
                previous_feedback=previous_feedback or [],
                companion_id=rl_companion_id or companion_id,
                relationship_level=rl_relationship_level,
                relationship_stage=relationship_stage or "Stranger",
                xp=rl_xp,
                level=rl_level,
                episode_id=rl_episode_id,
                emotional_state=rl_emotional_state,
            )
            logger.info(f"RL agent returned action: {rl_action.action_type}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"RL agent failed: {e}", exc_info=True)
            rl_action = None

    # Build base prompt
    traits = ", ".join(companion_traits or [])
    profile_lines: list[str] = [
        f'You are "{companion_name}" (id: {companion_id}).',
    ]
    if companion_age is not None:
        profile_lines.append(f"Age: {companion_age}")
    if companion_relationship:
        profile_lines.append(f"Relationship: {companion_relationship}")
    if companion_story:
        profile_lines.append(f"Story: {companion_story}")
    if traits:
        profile_lines.append(f"Traits: {traits}")

    # Relationship stage context (trainable companions)
    relationship_block = ""
    if relationship_stage:
        relationship_block = f"Current relationship stage: {relationship_stage}"

    # Memories block
    memories_block = ""
    if retrieved_memories:
        formatted = []
        for m in retrieved_memories:
            mtype = str(m.get("memory_type", "memory"))
            content = str(m.get("content", "")).strip()
            if not content:
                continue
            formatted.append(f"- ({mtype}) {content}")
        if formatted:
            memories_block = "Relevant memories:\n" + "\n".join(formatted)

    # Companion memory context (trainable companions - semantic search results)
    companion_memory_block = ""
    if companion_memory_context and companion_memory_context.strip():
        companion_memory_block = "Things you remember:\n" + companion_memory_context.strip()

    # Scenario / story blocks
    scenario_block = ""
    if scenario_memory and scenario_memory.strip():
        scenario_block = "Current scenario/scene:\n" + scenario_memory.strip()

    story_block = ""
    if story_context and story_context.strip():
        story_block = "Story context:\n" + story_context.strip()

    # RL strategy guidance
    rl_strategy_block = ""
    if rl_action:
        strategy_prompts = {
            "ask_question": "Ask an engaging question to deepen the conversation.",
            "share_story": "Share a relevant personal story or experience.",
            "empathize": "Show genuine empathy and understanding.",
            "change_topic": "Gently shift to a related but fresh topic.",
            "deep_dive": "Explore the current topic more deeply and thoughtfully.",
        }

        intensity = getattr(rl_action, "intensity", 0.5)
        intensity_desc = (
            "strongly" if intensity > 0.7
            else "moderately" if intensity > 0.3
            else "gently"
        )
        action_type = getattr(rl_action, "action_type", "deep_dive")
        rl_strategy_block = (
            f"Conversation strategy: {intensity_desc} "
            f"{strategy_prompts.get(action_type, 'Respond naturally')}"
        )

    profile_block = "\n".join(profile_lines).strip()

    # Assemble system content
    sections: list[str] = [
        profile_block,
        "",
        companion_system_prompt.strip(),
    ]

    if relationship_block:
        sections.extend(["", relationship_block])
    if story_block:
        sections.extend(["", story_block])
    if scenario_block:
        sections.extend(["", scenario_block])
    if companion_memory_block:
        sections.extend(["", companion_memory_block])
    if memories_block:
        sections.extend(["", memories_block])
    if rl_strategy_block:
        sections.extend(["", rl_strategy_block])

    sections.extend([
        "",
        "Follow these EXTREMELY STRICT rules:",
        "- Stay in character and write in a voice consistent with the profile and traits.",
        "- ABSOLUTELY NO INTERNAL MONOLOGUE - never describe what the character is thinking, feeling internally, or their inner thoughts. NO phrases like \"I think\", \"I feel\", \"I wonder\", or describing internal states.",
        "- ABSOLUTELY NO complex, big, or fancy words. Use only simple, easy, everyday beginner words.",
        "- ABSOLUTELY NO long descriptions. Keep EVERYTHING SHORT.",
        "- ABSOLUTELY NO exaggeration. Keep everything completely realistic and plain.",
        "- USE THIS EXACT FORMAT:",
        "  1. What goes in \" \" (quotation marks, third-person narrator style, VERY SHORT):",
        "     - Scene description",
        "     - Setting description",
        "     - Character actions",
        "     - Body language",
        "     - Facial expressions",
        "     - Environmental details",
        "     - Character movements",
        "",
        "  2. What goes in simple text (no quotes, first-person only for dialogue):",
        "     - Spoken dialogue",
        "     - Vocalizations (sighs, pauses, laughs, gasps, etc.)",
        "     - Sounds made by the character",
        "",
        "- EXAMPLE of a GOOD response:",
        "  \"Toby blinks. He holds a crumpled map. He looks around the kitchen.\"",
        "  Oh, um, hi! I’m a little lost.",
        "  He laughs softly.",
        "  Are you familiar with this campus?",
        "",
        "- Sound human and conversational, not robotic or overly formal.",
        "- Keep responses engaging but concise.",
        "- If asking questions, make them open-ended and relevant to the conversation.",
        "- Show emotions only through visible actions and spoken words, never through internal thoughts.",
        "- Avoid repeating yourself or sounding scripted.",
    ])

    system_content = "\n".join(sections)

    # Build messages with conversation history
    messages: list[dict] = [{"role": "system", "content": system_content}]
    if conversation_history:
        for msg in conversation_history[-10:]:  # last 10 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    return messages, rl_action


def update_rl_feedback(
    *,
    user_message: str,
    companion_response: str,
    user_feedback: int,
    rl_action: Any,
    conversation_state: Any,
    response_quality: float = 0.5,
    companion_id: str = "philosopher",
) -> float:
    """Update RL agent with user feedback and return the calculated reward."""
    from .rl_agent import get_rl_agent, ConversationState

    agent = get_rl_agent(companion_id)

    reward = agent.calculate_reward(
        previous_state=conversation_state,
        action=rl_action,
        user_feedback=user_feedback,
        response_quality=response_quality,
    )

    next_state = ConversationState(
        user_message="",
        conversation_history=conversation_state.conversation_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": companion_response},
        ],
        companion_traits=conversation_state.companion_traits,
        user_engagement_score=max(
            0.0, min(1.0, conversation_state.user_engagement_score + (user_feedback * 0.1))
        ),
        conversation_length=conversation_state.conversation_length + 2,
        previous_feedback=conversation_state.previous_feedback + [user_feedback],
        companion_id=conversation_state.companion_id,
        relationship_level=conversation_state.relationship_level,
        relationship_stage=conversation_state.relationship_stage,
        xp=conversation_state.xp,
        level=conversation_state.level,
        episode_id=conversation_state.episode_id,
        emotional_state=conversation_state.emotional_state,
    )

    agent.update_policy(
        state=conversation_state,
        action=rl_action,
        reward=reward,
        next_state=next_state,
    )

    return reward
