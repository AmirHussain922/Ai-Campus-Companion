"""
Reinforcement Learning agent for trainable companions.

Provides per-companion RL agents (Julian, Victoria) with enriched
conversation state tracking and DQN-style policy optimization.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from pydantic import BaseModel


class ConversationState(BaseModel):
    """Represents the current conversation state for RL decision making."""

    user_message: str
    conversation_history: List[Dict[str, str]]
    companion_traits: List[str]
    user_engagement_score: float  # 0.0 to 1.0
    conversation_length: int
    previous_feedback: List[int]  # -1, 0, 1 ratings
    context_embedding: Optional[List[float]] = None

    # --- Enriched fields for trainable companions ---
    companion_id: str = "philosopher"
    relationship_level: int = 0  # raw relationship points
    relationship_stage: str = "Stranger"
    xp: int = 0
    level: int = 1
    episode_id: Optional[str] = None
    emotional_state: str = "neutral"  # neutral, happy, sad, frustrated, curious


@dataclass
class RLAction:
    """Possible actions the RL agent can take."""

    action_type: str  # 'ask_question', 'share_story', 'empathize', 'change_topic', 'deep_dive'
    intensity: float  # 0.0 to 1.0, how strongly to perform the action
    topic_focus: Optional[str] = None  # specific topic to focus on


class PolicyNetwork(nn.Module):
    """Neural network that learns optimal conversation strategies."""

    def __init__(
        self,
        state_dim: int = 128,
        action_dim: int = 5,
        hidden_dim: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim

        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.dropout1 = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.dropout2 = nn.Dropout(dropout)
        self.fc3 = nn.Linear(hidden_dim // 2, action_dim)

        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass to get action probabilities."""
        x = self.relu(self.fc1(x))
        x = self.dropout1(x)
        x = self.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)
        return self.softmax(x)


# ---------------------------------------------------------------------------
# Relationship stage helper
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


# ---------------------------------------------------------------------------
# ConversationRLAgent
# ---------------------------------------------------------------------------

class ConversationRLAgent:
    """Reinforcement Learning agent for optimizing companion conversations."""

    def __init__(
        self,
        companion_id: str = "philosopher",
        learning_rate: float = 0.001,
        gamma: float = 0.95,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        self.companion_id = companion_id
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        # Initialize policy network
        self.policy_network = PolicyNetwork()
        self.optimizer = optim.Adam(self.policy_network.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()

        # Action mapping
        self.actions = [
            "ask_question",
            "share_story",
            "empathize",
            "change_topic",
            "deep_dive",
        ]

        # Experience replay buffer
        self.experience_buffer: List[Tuple] = []
        self.buffer_size = 10000

    def state_to_tensor(self, state: ConversationState) -> torch.Tensor:
        """Convert conversation state to tensor for neural network."""
        features: list[float] = []

        # Message length feature
        features.append(len(state.user_message) / 1000.0)

        # Engagement score
        features.append(state.user_engagement_score)

        # Conversation length (normalized)
        features.append(min(state.conversation_length / 50.0, 1.0))

        # Previous feedback average
        if state.previous_feedback:
            avg_feedback = sum(state.previous_feedback) / len(state.previous_feedback)
            features.append((avg_feedback + 1) / 2.0)
        else:
            features.append(0.5)

        # Trait presence (simplified)
        trait_features = [0.0] * 10
        for i, trait in enumerate(state.companion_traits[:10]):
            trait_features[i] = 1.0
        features.extend(trait_features)

        # --- Enriched features ---
        # Relationship level (normalized 0-1)
        features.append(min(state.relationship_level / 500.0, 1.0))

        # XP (normalized 0-1 based on typical max ~1000)
        features.append(min(state.xp / 1000.0, 1.0))

        # Level (normalized)
        features.append(min(state.level / 20.0, 1.0))

        # Emotional state encoding
        emotion_map = {"neutral": 0.0, "happy": 0.25, "sad": 0.5, "frustrated": 0.75, "curious": 1.0}
        features.append(emotion_map.get(state.emotional_state, 0.0))

        # Companion ID encoding
        if state.companion_id == "philosopher":
            features.extend([1.0, 0.0])
        elif state.companion_id == "rival":
            features.extend([0.0, 1.0])
        else:
            features.extend([0.0, 0.0])

        # Pad or truncate to fixed size (128)
        while len(features) < 128:
            features.append(0.0)

        return torch.tensor(features[:128], dtype=torch.float32).unsqueeze(0)

    def select_action(self, state: ConversationState) -> RLAction:
        """Select action using epsilon-greedy policy."""
        state_tensor = self.state_to_tensor(state)

        if random.random() < self.epsilon:
            action_idx = random.randint(0, len(self.actions) - 1)
            intensity = random.random()
        else:
            with torch.no_grad():
                action_probs = self.policy_network(state_tensor)
                action_idx = torch.multinomial(action_probs, 1).item()
                intensity = action_probs[0, action_idx].item()

        return RLAction(
            action_type=self.actions[action_idx],
            intensity=intensity,
        )

    def update_policy(
        self,
        state: ConversationState,
        action: RLAction,
        reward: float,
        next_state: ConversationState,
    ):
        """Update policy network using experience."""
        state_tensor = self.state_to_tensor(state)
        next_state_tensor = self.state_to_tensor(next_state)

        current_q_values = self.policy_network(state_tensor)

        with torch.no_grad():
            next_q_values = self.policy_network(next_state_tensor)
            max_next_q = torch.max(next_q_values).item()

        action_idx = self.actions.index(action.action_type)
        target_q_value = reward + (self.gamma * max_next_q)

        target_q_values = current_q_values.clone()
        target_q_values[0, action_idx] = target_q_value

        loss = self.criterion(current_q_values, target_q_values)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        experience = (state, action, reward, next_state)
        self.experience_buffer.append(experience)
        if len(self.experience_buffer) > self.buffer_size:
            self.experience_buffer.pop(0)

    def calculate_reward(
        self,
        previous_state: ConversationState,
        action: RLAction,
        user_feedback: int,
        response_quality: float,
    ) -> float:
        """Calculate reward based on user feedback and response quality."""
        base_reward = user_feedback * 10.0
        quality_bonus = response_quality * 5.0
        engagement_bonus = previous_state.user_engagement_score * 3.0

        action_bonus = 0.0
        if action.action_type == "ask_question" and user_feedback > 0:
            action_bonus = 2.0
        elif action.action_type == "empathize" and user_feedback > 0:
            action_bonus = 2.5

        total_reward = base_reward + quality_bonus + engagement_bonus + action_bonus
        return max(-20.0, min(20.0, total_reward))

    def save_model(self, filepath: str):
        """Save the trained model."""
        torch.save({
            "companion_id": self.companion_id,
            "policy_network_state_dict": self.policy_network.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
        }, filepath)

    def load_model(self, filepath: str):
        """Load a trained model."""
        checkpoint = torch.load(filepath, map_location="cpu")
        self.policy_network.load_state_dict(checkpoint["policy_network_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = checkpoint.get("epsilon", self.epsilon)


# ---------------------------------------------------------------------------
# Per-companion agent registry
# ---------------------------------------------------------------------------

_agents: dict[str, ConversationRLAgent] = {}


def get_rl_agent(companion_id: str = "philosopher") -> ConversationRLAgent:
    """Get or create an RL agent for a specific companion."""
    if companion_id not in _agents:
        _agents[companion_id] = ConversationRLAgent(companion_id=companion_id)
    return _agents[companion_id]


def get_all_agents() -> dict[str, ConversationRLAgent]:
    """Return all registered agents."""
    return _agents


# ---------------------------------------------------------------------------
# High-level RL application function
# ---------------------------------------------------------------------------

def apply_rl_to_conversation(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    companion_traits: List[str],
    user_engagement_score: float,
    previous_feedback: List[int],
    companion_id: str = "philosopher",
    relationship_level: int = 0,
    relationship_stage: str = "Stranger",
    xp: int = 0,
    level: int = 1,
    episode_id: str | None = None,
    emotional_state: str = "neutral",
) -> tuple[RLAction, ConversationState]:
    """Apply RL to optimize conversation strategy.

    Returns a tuple of (action, state) so the caller can store the
    transition for offline training.
    """
    agent = get_rl_agent(companion_id)

    state = ConversationState(
        user_message=user_message,
        conversation_history=conversation_history,
        companion_traits=companion_traits,
        user_engagement_score=user_engagement_score,
        conversation_length=len(conversation_history),
        previous_feedback=previous_feedback,
        companion_id=companion_id,
        relationship_level=relationship_level,
        relationship_stage=relationship_stage,
        xp=xp,
        level=level,
        episode_id=episode_id,
        emotional_state=emotional_state,
    )

    action = agent.select_action(state)
    return action, state
