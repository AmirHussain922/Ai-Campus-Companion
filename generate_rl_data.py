#!/usr/bin/env python
"""
Generate RL Training Data Script

Simulates chat sessions with Julian and Victoria to generate
the minimum 50+ transitions needed for RL training.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.config import get_settings
from app.database import get_database
from app.companion_memory_store import store_rl_transition
from app.rl_agent import ConversationState, RLAction, get_rl_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diverse conversation scenarios to generate varied training data
SCENARIOS = [
    {
        "user_message": "I've been thinking about the meaning of life lately. What do you think gives life purpose?",
        "action_type": "deep_dive",
        "reward": 15,
        "engagement": 0.9,
    },
    {
        "user_message": "Can you recommend a good book on philosophy?",
        "action_type": "ask_question",
        "reward": 12,
        "engagement": 0.8,
    },
    {
        "user_message": "I had a really bad day today. Everything went wrong.",
        "action_type": "empathize",
        "reward": 14,
        "engagement": 0.85,
    },
    {
        "user_message": "Do you believe in fate or free will?",
        "action_type": "deep_dive",
        "reward": 15,
        "engagement": 0.95,
    },
    {
        "user_message": "Tell me about your favorite philosophical concept",
        "action_type": "share_story",
        "reward": 13,
        "engagement": 0.8,
    },
    {
        "user_message": "I'm not sure what to do with my life. Any advice?",
        "action_type": "ask_question",
        "reward": 14,
        "engagement": 0.9,
    },
    {
        "user_message": "What's the most important lesson you've learned?",
        "action_type": "share_story",
        "reward": 15,
        "engagement": 0.9,
    },
    {
        "user_message": "I disagree with you on that point",
        "action_type": "change_topic",
        "reward": 8,
        "engagement": 0.6,
    },
    {
        "user_message": "That's really interesting! Can you elaborate?",
        "action_type": "deep_dive",
        "reward": 12,
        "engagement": 0.85,
    },
    {
        "user_message": "How do you deal with existential crisis?",
        "action_type": "empathize",
        "reward": 15,
        "engagement": 0.95,
    },
    {
        "user_message": "ok",
        "action_type": "ask_question",
        "reward": 2,
        "engagement": 0.2,
    },
    {
        "user_message": "yes",
        "action_type": "change_topic",
        "reward": 3,
        "engagement": 0.3,
    },
    {
        "user_message": "I just got accepted to my dream university!",
        "action_type": "empathize",
        "reward": 15,
        "engagement": 0.9,
    },
    {
        "user_message": "What do you think about artificial intelligence?",
        "action_type": "deep_dive",
        "reward": 14,
        "engagement": 0.85,
    },
    {
        "user_message": "I'm feeling really lonely",
        "action_type": "empathize",
        "reward": 15,
        "engagement": 0.95,
    },
]


async def generate_training_data():
    """Generate training transitions for Julian and Victoria."""
    
    settings = get_settings()
    db = await get_database()
    
    logger.info("="*70)
    logger.info("GENERATING RL TRAINING DATA")
    logger.info("="*70)
    
    target_transitions = 60  # Generate 60 per companion (above minimum 50)
    
    for companion_id in settings.trainable_companions:
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating data for: {companion_id.upper()}")
        logger.info(f"{'='*60}")
        
        agent = get_rl_agent(companion_id)
        
        # Get existing count
        existing_count = await db.rl_transitions.count_documents({
            "companion_id": companion_id
        })
        logger.info(f"Existing transitions: {existing_count}")
        
        needed = max(0, target_transitions - existing_count)
        
        if needed == 0:
            logger.info(f"✓ Already has {existing_count} transitions (target: {target_transitions})")
            continue
        
        logger.info(f"Generating {needed} new transitions...")
        
        for i in range(needed):
            scenario = SCENARIOS[i % len(SCENARIOS)]
            
            # Create conversation state
            state = ConversationState(
                user_message=scenario["user_message"],
                conversation_history=[
                    {"role": "user", "content": scenario["user_message"]},
                    {"role": "assistant", "content": f"Response {i}"}
                ],
                companion_traits=["Deep thinker", "empathetic"] if companion_id == "philosopher" else ["Sharp", "witty", "challenging"],
                user_engagement_score=scenario["engagement"],
                conversation_length=i * 2,
                previous_feedback=[],
                companion_id=companion_id,
                relationship_level=i * 5,
                relationship_stage="Stranger" if i < 10 else "Curious" if i < 20 else "Friend",
                xp=i * 10,
                level=max(1, i // 10 + 1),
                episode_id=None,
                emotional_state="curious" if scenario["engagement"] > 0.7 else "neutral",
            )
            
            # Create RL action
            action = RLAction(
                action_type=scenario["action_type"],
                intensity=0.5 + (scenario["engagement"] * 0.5),
                topic_focus="philosophy" if companion_id == "philosopher" else "competition",
            )
            
            # Create next state (slightly different)
            next_state = ConversationState(
                user_message="",
                conversation_history=state.conversation_history + [
                    {"role": "assistant", "content": "Follow-up response"}
                ],
                companion_traits=state.companion_traits,
                user_engagement_score=min(1.0, scenario["engagement"] + 0.1),
                conversation_length=state.conversation_length + 2,
                previous_feedback=[],
                companion_id=companion_id,
                relationship_level=state.relationship_level + scenario["reward"],
                relationship_stage=state.relationship_stage,
                xp=state.xp + scenario["reward"],
                level=state.level,
                episode_id=None,
                emotional_state="happy" if scenario["reward"] > 10 else "neutral",
            )
            
            # Store transition
            reward = float(scenario["reward"])
            
            await store_rl_transition(
                user_id="test_user_rl_generation",
                companion_id=companion_id,
                state=state.model_dump(),
                action={
                    "action_type": action.action_type,
                    "intensity": action.intensity,
                    "topic_focus": action.topic_focus,
                },
                reward=reward,
                next_state=next_state.model_dump(),
            )
            
            if (i + 1) % 20 == 0:
                logger.info(f"  Generated {i + 1}/{needed} transitions...")
        
        # Verify count
        new_count = await db.rl_transitions.count_documents({
            "companion_id": companion_id
        })
        logger.info(f"\n✓ Generated {needed} transitions")
        logger.info(f"  Total transitions for {companion_id}: {new_count}")
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("GENERATION COMPLETE")
    logger.info(f"{'='*70}")
    
    for companion_id in settings.trainable_companions:
        count = await db.rl_transitions.count_documents({
            "companion_id": companion_id
        })
        status = "✓ READY FOR TRAINING" if count >= 50 else "⚠ Need more data"
        logger.info(f"{companion_id}: {count} transitions - {status}")
    
    logger.info(f"\nNext step: Run 'python diagnose_rl.py' to verify training readiness")


async def main():
    """Main entry point."""
    try:
        await generate_training_data()
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
