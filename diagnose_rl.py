#!/usr/bin/env python
"""
RL Training Diagnostic Script

This script checks:
1. If RL agents are initialized for Julian and Victoria
2. If there are training transitions in the database
3. Current model state and epsilon values
4. Runs a quick training cycle and shows results
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.config import get_settings
from app.rl_agent import get_rl_agent, get_all_agents
from app.rl_training import RLTrainingPipeline
from app.database import get_database, is_database_available

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def diagnose_rl_system():
    """Diagnose the RL training system."""
    
    logger.info("="*70)
    logger.info("RL TRAINING DIAGNOSTIC REPORT")
    logger.info("="*70)
    
    settings = get_settings()
    
    # 1. Check database
    logger.info("\n1. DATABASE STATUS")
    db_available = await is_database_available()
    logger.info(f"   Database available: {'✓ YES' if db_available else '✗ NO'}")
    
    if not db_available:
        logger.error("Cannot proceed without database connection")
        return
    
    db = await get_database()
    
    # 2. Check trainable companions
    logger.info("\n2. TRAINABLE COMPANIONS")
    logger.info(f"   Configured companions: {settings.trainable_companions}")
    logger.info(f"   Demo companions: {settings.demo_companions}")
    
    # 3. Check RL agents
    logger.info("\n3. RL AGENT STATUS")
    for companion_id in settings.trainable_companions:
        try:
            agent = get_rl_agent(companion_id)
            logger.info(f"\n   {companion_id.upper()}:")
            logger.info(f"   ✓ Agent initialized")
            logger.info(f"     - State dimension: {agent.state_dim}")
            logger.info(f"     - Action dimension: {agent.action_dim}")
            logger.info(f"     - Actions: {agent.actions}")
            logger.info(f"     - Epsilon (exploration rate): {agent.epsilon:.4f}")
            logger.info(f"     - Epsilon min: {agent.epsilon_min:.4f}")
            logger.info(f"     - Learning rate: {agent.learning_rate}")
            logger.info(f"     - Gamma (discount factor): {agent.gamma}")
            logger.info(f"     - Network: {agent.policy_network}")
            
            # Count parameters
            total_params = sum(p.numel() for p in agent.policy_network.parameters())
            logger.info(f"     - Total parameters: {total_params:,}")
            
        except Exception as e:
            logger.error(f"   ✗ {companion_id}: {e}")
    
    # 4. Check training data in database
    logger.info("\n4. TRAINING DATA (RL TRANSITIONS)")
    
    pipeline = RLTrainingPipeline()
    
    for companion_id in settings.trainable_companions:
        try:
            transitions = await pipeline.collect_transitions(companion_id, limit=10000)
            
            logger.info(f"\n   {companion_id.upper()}:")
            logger.info(f"   Total transitions: {len(transitions)}")
            
            if transitions:
                # Analyze transitions
                rewards = [t.get("reward", 0) for t in transitions]
                actions = [t.get("action", {}).get("action_type", "unknown") for t in transitions]
                
                logger.info(f"   Average reward: {np.mean(rewards):.2f}")
                logger.info(f"   Reward std: {np.std(rewards):.2f}")
                logger.info(f"   Min reward: {min(rewards):.2f}")
                logger.info(f"   Max reward: {max(rewards):.2f}")
                
                # Action distribution
                action_counts = {}
                for action in actions:
                    action_counts[action] = action_counts.get(action, 0) + 1
                
                logger.info(f"   Action distribution:")
                for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / len(actions)) * 100
                    logger.info(f"     - {action}: {count} ({percentage:.1f}%)")
                
                # Recent transitions
                logger.info(f"   Most recent transition:")
                latest = transitions[0]
                logger.info(f"     - State: {latest.get('state', {}).get('user_message', '')[:80]}...")
                logger.info(f"     - Action: {latest.get('action', {}).get('action_type')}")
                logger.info(f"     - Reward: {latest.get('reward')}")
            else:
                logger.warning(f"   ⚠ No training data found!")
                logger.warning(f"   Users need to chat with {companion_id} to generate training data")
                
        except Exception as e:
            logger.error(f"   ✗ Error analyzing {companion_id}: {e}")
    
    # 5. Run a quick training cycle
    logger.info("\n5. QUICK TRAINING TEST")
    logger.info("   Running 2 epochs with batch size 32...")
    
    for companion_id in settings.trainable_companions:
        try:
            transitions = await pipeline.collect_transitions(companion_id, limit=1000)
            
            if len(transitions) < 10:
                logger.warning(f"\n   {companion_id.upper()}:")
                logger.warning(f"   ⚠ Skipping training - only {len(transitions)} transitions (need at least 10)")
                continue
            
            agent = get_rl_agent(companion_id)
            old_epsilon = agent.epsilon
            
            # Quick training
            result = await pipeline.train_companion(
                companion_id,
                num_epochs=2,
                batch_size=32
            )
            
            new_epsilon = agent.epsilon
            
            logger.info(f"\n   {companion_id.upper()}:")
            logger.info(f"   Transitions used: {result.get('total_transitions', 0)}")
            
            if 'epoch_losses' in result and result['epoch_losses']:
                logger.info(f"   Epoch 1 loss: {result['epoch_losses'][0]:.4f}")
                if len(result['epoch_losses']) > 1:
                    logger.info(f"   Epoch 2 loss: {result['epoch_losses'][1]:.4f}")
                    loss_change = ((result['epoch_losses'][1] - result['epoch_losses'][0]) / result['epoch_losses'][0]) * 100
                    logger.info(f"   Loss change: {loss_change:+.1f}%")
            
            if 'average_rewards' in result and result['average_rewards']:
                logger.info(f"   Avg reward: {result['average_rewards'][-1]:.2f}")
            
            logger.info(f"   Epsilon: {old_epsilon:.4f} → {new_epsilon:.4f}")
            logger.info(f"   ✓ Training successful")
            
        except Exception as e:
            logger.error(f"   ✗ Training failed for {companion_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # 6. Check if model checkpoints exist
    logger.info("\n6. MODEL CHECKPOINTS")
    models_dir = Path(__file__).parent / "backend" / "models"
    
    if not models_dir.exists():
        logger.warning("   ⚠ Models directory doesn't exist yet")
        logger.warning("   Models will be saved after first training cycle")
    else:
        for companion_id in settings.trainable_companions:
            checkpoint_path = models_dir / f"rl_{companion_id}_checkpoint.pth"
            if checkpoint_path.exists():
                size_kb = checkpoint_path.stat().st_size / 1024
                logger.info(f"   ✓ {companion_id}: {checkpoint_path.name} ({size_kb:.1f} KB)")
            else:
                logger.warning(f"   ⚠ {companion_id}: No checkpoint file yet")
    
    # 7. Summary and recommendations
    logger.info("\n" + "="*70)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("="*70)
    
    total_transitions = 0
    for companion_id in settings.trainable_companions:
        try:
            transitions = await pipeline.collect_transitions(companion_id, limit=10000)
            total_transitions += len(transitions)
        except:
            pass
    
    if total_transitions == 0:
        logger.info("\n⚠ STATUS: NO TRAINING DATA")
        logger.info("\nRecommendations:")
        logger.info("  1. Users need to chat with Julian and Victoria to generate transitions")
        logger.info("  2. Each chat message creates a transition stored in rl_transitions collection")
        logger.info("  3. Minimum 50 transitions needed for meaningful training")
        logger.info("  4. After collecting data, training runs automatically every 60 minutes")
        logger.info("\nTo manually trigger training:")
        logger.info("  - Backend automatically trains based on rl_training_interval_minutes setting")
        logger.info("  - Or call the training endpoint if available")
    elif total_transitions < 50:
        logger.info(f"\n⚠ STATUS: LOW TRAINING DATA ({total_transitions} transitions)")
        logger.info("\nRecommendations:")
        logger.info("  1. Need at least 50 transitions for initial training")
        logger.info("  2. Continue chatting with Julian and Victoria")
        logger.info("  3. Training will improve with more diverse interactions")
    else:
        logger.info(f"\n✓ STATUS: TRAINING DATA AVAILABLE ({total_transitions} transitions)")
        logger.info("\nNext steps:")
        logger.info("  1. RL agents should be training automatically")
        logger.info("  2. Check backend logs for training completion messages")
        logger.info("  3. Response quality should improve over time as epsilon decreases")
        logger.info("  4. Monitor action distribution to see RL learning patterns")
    
    logger.info("\n" + "="*70)


async def main():
    """Main entry point."""
    try:
        await diagnose_rl_system()
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
