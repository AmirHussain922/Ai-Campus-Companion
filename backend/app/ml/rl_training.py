"""
RL Training pipeline for trainable companions.

Reads transitions from the `rl_transitions` collection, reconstructs
ConversationState / RLAction objects, trains per-companion agents,
and saves checkpoints.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import torch

from app.config import get_settings
from app.core.database import get_database
from app.ml.rl_agent import (
    ConversationRLAgent,
    ConversationState,
    RLAction,
    get_all_agents,
    get_rl_agent,
)

logger = logging.getLogger(__name__)


class RLTrainingPipeline:
    """Training pipeline that reads from rl_transitions and trains per-companion agents."""

    def __init__(self):
        self.settings = get_settings()

    async def collect_transitions(self, companion_id: str, limit: int = 5000) -> list[dict]:
        """Fetch recent RL transitions for a companion from MongoDB."""
        db = await get_database()
        cursor = (
            db.rl_transitions
            .find({"companion_id": companion_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        transitions: list[dict] = []
        async for doc in cursor:
            transitions.append(doc)
        return transitions

    def _reconstruct_state(self, state_dict: dict) -> ConversationState:
        """Reconstruct a ConversationState from a serialized dict."""
        return ConversationState(
            user_message=state_dict.get("user_message", ""),
            conversation_history=state_dict.get("conversation_history", []),
            companion_traits=state_dict.get("companion_traits", []),
            user_engagement_score=float(state_dict.get("user_engagement_score", 0.5)),
            conversation_length=int(state_dict.get("conversation_length", 0)),
            previous_feedback=state_dict.get("previous_feedback", []),
            companion_id=state_dict.get("companion_id", "philosopher"),
            relationship_level=int(state_dict.get("relationship_level", 0)),
            relationship_stage=state_dict.get("relationship_stage", "Stranger"),
            xp=int(state_dict.get("xp", 0)),
            level=int(state_dict.get("level", 1)),
            episode_id=state_dict.get("episode_id"),
            emotional_state=state_dict.get("emotional_state", "neutral"),
        )

    def _reconstruct_action(self, action_dict: dict) -> RLAction:
        """Reconstruct an RLAction from a serialized dict."""
        return RLAction(
            action_type=action_dict.get("action_type", "deep_dive"),
            intensity=float(action_dict.get("intensity", 0.5)),
            topic_focus=action_dict.get("topic_focus"),
        )

    async def train_companion(
        self,
        companion_id: str,
        num_epochs: int = 5,
        batch_size: int = 32,
    ) -> dict[str, Any]:
        """Train a single companion's RL agent."""
        agent = get_rl_agent(companion_id)
        transitions = await self.collect_transitions(companion_id)

        if not transitions:
            return {
                "companion_id": companion_id,
                "message": "No transitions found",
                "transitions": 0,
            }

        stats: dict[str, Any] = {
            "companion_id": companion_id,
            "total_transitions": len(transitions),
            "epoch_losses": [],
            "average_rewards": [],
        }

        for epoch in range(num_epochs):
            epoch_losses: list[float] = []
            epoch_rewards: list[float] = []

            np.random.shuffle(transitions)

            for i in range(0, len(transitions), batch_size):
                batch = transitions[i : i + batch_size]

                for doc in batch:
                    state = self._reconstruct_state(doc.get("state", {}))
                    action = self._reconstruct_action(doc.get("action", {}))
                    reward = float(doc.get("reward", 0.0))
                    next_state = self._reconstruct_state(doc.get("next_state", {}))

                    state_tensor = agent.state_to_tensor(state)
                    current_q = agent.policy_network(state_tensor)

                    action_idx = agent.actions.index(action.action_type)
                    next_state_tensor = agent.state_to_tensor(next_state)

                    with torch.no_grad():
                        next_q = agent.policy_network(next_state_tensor)
                        max_next_q = torch.max(next_q).item()

                    target_q_value = reward + (agent.gamma * max_next_q)
                    target_q = current_q.clone()
                    target_q[0, action_idx] = target_q_value

                    loss = agent.criterion(current_q, target_q)

                    agent.optimizer.zero_grad()
                    loss.backward()
                    agent.optimizer.step()

                    agent.epsilon = max(
                        agent.epsilon_min, agent.epsilon * agent.epsilon_decay
                    )

                    epoch_losses.append(float(loss.item()))
                    epoch_rewards.append(reward)

            avg_loss = float(np.mean(epoch_losses)) if epoch_losses else 0.0
            avg_reward = float(np.mean(epoch_rewards)) if epoch_rewards else 0.0
            stats["epoch_losses"].append(avg_loss)
            stats["average_rewards"].append(avg_reward)
            logger.info(
                f"[{companion_id}] Epoch {epoch+1}/{num_epochs}: "
                f"loss={avg_loss:.4f} reward={avg_reward:.2f}"
            )

        return stats


async def run_training_for_all_companions() -> list[dict]:
    """Run training for all trainable companions."""
    settings = get_settings()
    pipeline = RLTrainingPipeline()
    results = []

    for companion_id in settings.trainable_companions:
        result = await pipeline.train_companion(companion_id)
        results.append(result)

    # Save checkpoints
    for companion_id in settings.trainable_companions:
        agent = get_rl_agent(companion_id)
        path = f"models/rl_{companion_id}_checkpoint.pth"
        try:
            agent.save_model(path)
            logger.info(f"Saved model checkpoint for {companion_id} to {path}")
        except Exception as e:
            logger.error(f"Failed to save model for {companion_id}: {e}")

    return results
