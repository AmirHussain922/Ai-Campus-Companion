"""
Server-side XP evaluator for trainable companions.

Evaluates user messages and awards XP / penalties based on quality,
engagement, toxicity, and immersion-breaking detection.
"""

from __future__ import annotations
from app.core.database import get_database
from bson import ObjectId


def evaluate_xp(
    *,
    text: str,
    recent_user_messages: list[str] | None = None,
    has_active_scenario: bool = False,
) -> tuple[int, list[str]]:
    """Evaluate a user message and return (xp_delta, reasons).
    No automatic XP from casual chatting - only from quests/tasks!
    """
    normalized = text.strip().lower()
    reasons: list[str] = []

    # --- Penalties ---
    low_effort_set = {
        "ok", "k", "kk", "hmm", "hm", "ya", "yes", "no", "lol", "idk", "sure",
    }
    is_low_effort = (
        len(normalized) <= 2
        or (normalized in low_effort_set and len(normalized.split()) <= 2)
    )
    if is_low_effort:
        reasons.append("low effort")

    toxic_words = [
        "stupid", "idiot", "dumb", "shut up", "hate you",
        "kill yourself", "moron", "trash", "worthless",
        "bitch", "asshole", "fuck you",
    ]
    is_toxic = any(w in normalized for w in toxic_words)
    if is_toxic:
        reasons.append("toxic")

    breaks_immersion_phrases = [
        "you're just an ai", "you are just an ai",
        "you're an ai", "you are an ai",
        "this is fake", "this story is fake",
        "not real", "roleplay is fake",
    ]
    breaks_immersion = any(p in normalized for p in breaks_immersion_phrases)
    if breaks_immersion:
        reasons.append("breaks immersion")

    recent = [m.strip().lower() for m in (recent_user_messages or []) if m.strip()]
    is_spam_repeat = (
        len(recent) >= 3 and all(m == normalized for m in recent[:3])
    )
    if is_spam_repeat:
        reasons.append("spam repeat")

    delta = 0
    if is_toxic:
        delta -= 5
    if breaks_immersion:
        delta -= 2
    if is_spam_repeat:
        delta -= 1
    if is_low_effort and not is_toxic:
        delta -= 1

    # No automatic rewards from casual chatting anymore! Only from quests!

    delta = max(-5, min(delta, 15))
    return delta, reasons


async def add_quest_completion_xp(
    *,
    user_id: str,
    companion_id: str,
    quest_type: str,
    xp_reward: int,
) -> dict:
    """Add XP to a companion from quest completion, and handle level ups!"""
    db = await get_database()
    
    # Find user doc
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        return {"success": False, "error": "User not found"}
    
    progression_list = list(user_doc.get("companion_progression", []))
    found = False
    
    for i, p in enumerate(progression_list):
        if p.get("companion_id") == companion_id:
            current_xp = p.get("xp", 0)
            current_level = p.get("level", 1)
            
            new_xp = current_xp + xp_reward
            new_level = current_level
            pending_level_up = False
            
            # Check level up
            xp_needed = _xp_for_next_level(current_level)
            while new_xp >= xp_needed:
                pending_level_up = True
                new_level += 1
                new_xp -= xp_needed
                xp_needed = _xp_for_next_level(new_level)
            
            # Update progression
            p["xp"] = new_xp
            p["level"] = new_level
            p["pending_level_up"] = pending_level_up
            
            progression_list[i] = p
            found = True
            break
    
    if not found:
        # Add new companion progression
        progression_list.append({
            "companion_id": companion_id,
            "xp": xp_reward,
            "level": 1,
            "relationship_points": 0,
            "relationship_stage": "Stranger",
            "current_episode_id": None,
            "episodes_unlocked": [],
            "total_messages": 0,
            "last_interaction": None,
            "pending_level_up": xp_reward >= _xp_for_next_level(1),
        })
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"companion_progression": progression_list}}
    )
    
    return {
        "success": True,
        "xp_added": xp_reward,
        "new_progression": progression_list,
    }


def _xp_for_next_level(level: int) -> int:
    """Calculate XP needed for next level with increasing curve: 100 * 1.5^(level-1)"""
    return int(100 * (1.5 ** (level - 1)))


# ---------------------------------------------------------------------------
# Relationship stage mapping
# ---------------------------------------------------------------------------

_RELATIONSHIP_STAGES = [
    (0, "Stranger"),
    (50, "Curious"),
    (150, "Friend"),
    (300, "Close Friend"),
    (500, "Confidant"),
]


def get_relationship_stage(points: int) -> str:
    """Map relationship points to a stage name."""
    stage = "Stranger"
    for threshold, name in _RELATIONSHIP_STAGES:
        if points >= threshold:
            stage = name
    return stage
