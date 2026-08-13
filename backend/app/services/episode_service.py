"""
Episode service for managing story episodes and progress.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId

from app.core.database import (
    get_episodes_collection,
    get_episode_progress_collection,
    get_users_collection,
    get_rl_transitions_collection,
)
from app.models import (
    EpisodeInDB,
    EpisodeProgressInDB,
    EpisodeScriptNode,
    EpisodeNodeChoice,
)
from app.companions.companions import companions

logger = logging.getLogger(__name__)

# Relationship stage mapping (from xp_evaluator.py)
_RELATIONSHIP_STAGE_TO_INT = {
    "Stranger": 0,
    "Curious": 1,
    "Friend": 2,
    "Close Friend": 3,
    "Confidant": 4,
}


class EpisodeService:
    """Service class for managing story episodes."""

    @staticmethod
    async def seed_episodes() -> None:
        """Seed default episodes for all companions."""
        episodes_collection = await get_episodes_collection()

        # Check if episodes already exist
        existing_count = await episodes_collection.count_documents({})
        if existing_count > 0:
            logger.info("Episodes already seeded, skipping...")
            return

        # Define episodes for each companion
        episodes_data = [
            # Life-of-the-Party (party_friend)
            {
                "companion_id": "party_friend",
                "title": "Event Planning 101",
                "description": "Help Party Friend plan the biggest event of the semester!",
                "required_relationship_stage": 0,
                "script_nodes": [
                    {
                        "node_id": "start",
                        "companion_dialogue": "Okay, okay—big news! I'm organizing the spring fling this year! But I have NO idea where to start.",
                        "is_start_node": True,
                        "choices": [
                            {"choice_id": "c1", "choice_text": "Let's make a list of everything we need.", "next_node_id": "list", "xp_reward": 10},
                            {"choice_id": "c2", "choice_text": "First, let's pick a theme!", "next_node_id": "theme", "xp_reward": 12},
                        ],
                    },
                    {
                        "node_id": "list",
                        "companion_dialogue": "Smart! Okay, let's see—venue, music, food... What's the most important?",
                        "choices": [
                            {"choice_id": "c3", "choice_text": "Venue first—we need to lock that in.", "next_node_id": "venue", "xp_reward": 10},
                            {"choice_id": "c4", "choice_text": "Music is the key to a great party!", "next_node_id": "music", "xp_reward": 12},
                        ],
                    },
                    {
                        "node_id": "theme",
                        "companion_dialogue": "Yes! Theme ideas: tropical, 80s, neon? What do you think?",
                        "choices": [
                            {"choice_id": "c5", "choice_text": "Tropical is perfect for spring!", "next_node_id": "list", "xp_reward": 10},
                            {"choice_id": "c6", "choice_text": "80s would be so fun!", "next_node_id": "list", "xp_reward": 10},
                        ],
                    },
                    {
                        "node_id": "venue",
                        "companion_dialogue": "Okay, venue booked! Now let's think about music.",
                        "choices": [
                            {"choice_id": "c7", "choice_text": "Let's make a playlist together!", "next_node_id": "music", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "music",
                        "companion_dialogue": "This playlist is AMAZING! Okay, I think we've got this. The party is going to be legendary!",
                        "is_end_node": True,
                        "choices": [],
                    },
                ],
            },
            # Night-Owl Philosopher (philosopher)
            {
                "companion_id": "philosopher",
                "title": "Writer's Block",
                "description": "Help Philosopher break through a severe case of writer's block.",
                "required_relationship_stage": 0,
                "script_nodes": [
                    {
                        "node_id": "start",
                        "companion_dialogue": "... I can't write a single word. The page is just... blank. Empty.",
                        "is_start_node": True,
                        "choices": [
                            {"choice_id": "c1", "choice_text": "What are you trying to write about?", "next_node_id": "topic", "xp_reward": 10},
                            {"choice_id": "c2", "choice_text": "Maybe we should take a walk and clear your head.", "next_node_id": "walk", "xp_reward": 8},
                        ],
                    },
                    {
                        "node_id": "topic",
                        "companion_dialogue": "About... meaning. Purpose. But every time I try to put it into words, they dissolve.",
                        "choices": [
                            {"choice_id": "c3", "choice_text": "Start with something small—maybe a memory?", "next_node_id": "memory", "xp_reward": 15},
                            {"choice_id": "c4", "choice_text": "What if we don't try to find 'meaning'? Just write what you feel.", "next_node_id": "feel", "xp_reward": 12},
                        ],
                    },
                    {
                        "node_id": "walk",
                        "companion_dialogue": "Okay... the night air is cool. Let's go.",
                        "choices": [
                            {"choice_id": "c5", "choice_text": "Look at the stars. What do they make you think of?", "next_node_id": "stars", "xp_reward": 12},
                        ],
                    },
                    {
                        "node_id": "memory",
                        "companion_dialogue": "A memory... When I was a kid, I used to climb the old oak tree in the backyard and pretend I was somewhere else.",
                        "choices": [
                            {"choice_id": "c6", "choice_text": "Write that down. That's beautiful.", "next_node_id": "success", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "feel",
                        "companion_dialogue": "Just write what I feel... That's... not something I've ever tried before.",
                        "choices": [
                            {"choice_id": "c7", "choice_text": "Try it. Just one sentence.", "next_node_id": "success", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "stars",
                        "companion_dialogue": "The stars... they make me feel both infinitely small and infinitely important at the same time.",
                        "choices": [
                            {"choice_id": "c8", "choice_text": "There's your first sentence.", "next_node_id": "success", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "success",
                        "companion_dialogue": "... You're right. The words are starting to come. Thank you. For seeing what I couldn't.",
                        "is_end_node": True,
                        "choices": [],
                    },
                ],
            },
            # Competitive Rival (rival)
            {
                "companion_id": "rival",
                "title": "The Debate",
                "description": "Go head-to-head with Rival in the most important debate of the year.",
                "required_relationship_stage": 0,
                "script_nodes": [
                    {
                        "node_id": "start",
                        "companion_dialogue": "So, we're opponents in the final debate. Don't think I'll go easy on you.",
                        "is_start_node": True,
                        "choices": [
                            {"choice_id": "c1", "choice_text": "I wouldn't want you to. May the best one win.", "next_node_id": "respect", "xp_reward": 12},
                            {"choice_id": "c2", "choice_text": "Good—because I'm going to beat you fair and square.", "next_node_id": "challenge", "xp_reward": 10},
                        ],
                    },
                    {
                        "node_id": "respect",
                        "companion_dialogue": "... Hmm. Well, at least you have some dignity. Let's make this a debate worth remembering.",
                        "choices": [
                            {"choice_id": "c3", "choice_text": "What's your position going to be?", "next_node_id": "prep", "xp_reward": 12},
                            {"choice_id": "c4", "choice_text": "Want to run some practice arguments?", "next_node_id": "practice", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "challenge",
                        "companion_dialogue": "That's the spirit! I love the fire. Now let's make sure we're both prepared.",
                        "choices": [
                            {"choice_id": "c5", "choice_text": "Let's go over our research together.", "next_node_id": "prep", "xp_reward": 12},
                        ],
                    },
                    {
                        "node_id": "prep",
                        "companion_dialogue": "Okay, here are my sources. I expect you to have done your homework too.",
                        "choices": [
                            {"choice_id": "c6", "choice_text": "Of course. Let's see who has the stronger case.", "next_node_id": "practice", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "practice",
                        "companion_dialogue": "Wow... your counterargument was actually brilliant. I didn't expect that.",
                        "choices": [
                            {"choice_id": "c7", "choice_text": "Told you I wouldn't make it easy.", "next_node_id": "success", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "success",
                        "companion_dialogue": "This debate is going to be incredible. Win or lose, I'm glad you're my opponent. You make me better.",
                        "is_end_node": True,
                        "choices": [],
                    },
                ],
            },
            # Clueless Freshman (freshman)
            {
                "companion_id": "freshman",
                "title": "First Week Jitters",
                "description": "Help Freshman navigate his first week of college!",
                "required_relationship_stage": 0,
                "script_nodes": [
                    {
                        "node_id": "start",
                        "companion_dialogue": "Oh no... I think I'm lost. I have a class in 10 minutes and I have no idea where the building is!",
                        "is_start_node": True,
                        "choices": [
                            {"choice_id": "c1", "choice_text": "Okay, calm down. Let's look at your schedule together.", "next_node_id": "schedule", "xp_reward": 10},
                            {"choice_id": "c2", "choice_text": "Which class is it? I might know where it is!", "next_node_id": "class", "xp_reward": 8},
                        ],
                    },
                    {
                        "node_id": "schedule",
                        "companion_dialogue": "It's Introduction to Computer Science in... um... Building A?",
                        "choices": [
                            {"choice_id": "c3", "choice_text": "Building A is right this way—let's go!", "next_node_id": "walk", "xp_reward": 10},
                            {"choice_id": "c4", "choice_text": "Wait, let's check the campus map app first.", "next_node_id": "map", "xp_reward": 12},
                        ],
                    },
                    {
                        "node_id": "class",
                        "companion_dialogue": "Introduction to Computer Science!",
                        "choices": [
                            {"choice_id": "c5", "choice_text": "I know where that is! Let's hurry.", "next_node_id": "walk", "xp_reward": 10},
                        ],
                    },
                    {
                        "node_id": "map",
                        "companion_dialogue": "Oh, right! The app! I forgot I even installed it.",
                        "choices": [
                            {"choice_id": "c6", "choice_text": "Okay, it says Building A is two minutes that way!", "next_node_id": "walk", "xp_reward": 10},
                        ],
                    },
                    {
                        "node_id": "walk",
                        "companion_dialogue": "We made it! Thank you SO much. I was so scared I'd miss the first class.",
                        "choices": [
                            {"choice_id": "c7", "choice_text": "No problem! Want to grab lunch after class and I can show you around?", "next_node_id": "success", "xp_reward": 15},
                        ],
                    },
                    {
                        "node_id": "success",
                        "companion_dialogue": "Really? That would be AWESOME! You're the best upperclassman ever!",
                        "is_end_node": True,
                        "choices": [],
                    },
                ],
            },
        ]

        # Insert episodes
        for episode_data in episodes_data:
            episode_in_db = EpisodeInDB(**episode_data)
            await episodes_collection.insert_one(episode_in_db.model_dump(by_alias=True))

        logger.info(f"Seeded {len(episodes_data)} episodes successfully!")

    @staticmethod
    async def get_available_episodes(user_id: str, companion_id: str) -> list[EpisodeInDB]:
        """Get episodes available to a user for a specific companion."""
        episodes_collection = await get_episodes_collection()
        users_collection = await get_users_collection()

        # Get user's companion progression
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        companion_prog = next(
            (cp for cp in user.get("companion_progression", []) if cp.get("companion_id") == companion_id),
            None
        )
        user_stage = _RELATIONSHIP_STAGE_TO_INT.get(
            companion_prog.get("relationship_stage", "Stranger") if companion_prog else "Stranger",
            0,
        )

        # Get all episodes for companion with required stage <= user's stage
        cursor = episodes_collection.find({
            "companion_id": companion_id,
            "required_relationship_stage": {"$lte": user_stage},
        })
        episodes = []
        async for doc in cursor:
            episodes.append(EpisodeInDB(**doc))
        return episodes

    @staticmethod
    async def start_episode(user_id: str, episode_id: str) -> EpisodeProgressInDB:
        """Start an episode for a user."""
        episodes_collection = await get_episodes_collection()
        progress_collection = await get_episode_progress_collection()

        # Get episode
        episode = await episodes_collection.find_one({"_id": ObjectId(episode_id)})
        if not episode:
            raise ValueError("Episode not found")

        # Check if user already has progress for this episode
        existing_progress = await progress_collection.find_one({
            "user_id": user_id,
            "episode_id": str(episode_id),
        })
        if existing_progress:
            return EpisodeProgressInDB(**existing_progress)

        # Find start node
        start_node = next((n for n in episode["script_nodes"] if n["is_start_node"]), None)
        if not start_node:
            raise ValueError("Episode has no start node")

        # Create new progress
        new_progress = EpisodeProgressInDB(
            user_id=user_id,
            episode_id=str(episode_id),
            companion_id=episode["companion_id"],
            status="in_progress",
            current_node_id=start_node["node_id"],
        )
        await progress_collection.insert_one(new_progress.model_dump(by_alias=True))
        return new_progress

    @staticmethod
    async def make_choice(user_id: str, episode_id: str, choice_id: str) -> dict:
        """Make a choice in an episode."""
        episodes_collection = await get_episodes_collection()
        progress_collection = await get_episode_progress_collection()
        users_collection = await get_users_collection()
        rl_transitions_collection = await get_rl_transitions_collection()

        # Get episode and progress
        episode = await episodes_collection.find_one({"_id": ObjectId(episode_id)})
        if not episode:
            raise ValueError("Episode not found")

        progress = await progress_collection.find_one({
            "user_id": user_id,
            "episode_id": str(episode_id),
        })
        if not progress:
            raise ValueError("Episode progress not found")

        if progress["status"] == "completed":
            raise ValueError("Episode already completed")

        # Find current node
        current_node = next(
            (n for n in episode["script_nodes"] if n["node_id"] == progress["current_node_id"]),
            None,
        )
        if not current_node:
            raise ValueError("Current node not found")

        # Find the choice
        choice = next((c for c in current_node["choices"] if c["choice_id"] == choice_id), None)
        if not choice:
            raise ValueError("Choice not found")

        # Calculate XP earned
        xp_earned = choice["xp_reward"]
        total_xp_earned = progress["total_xp_earned"] + xp_earned

        # Update user's companion XP
        if xp_earned > 0:
            await users_collection.update_one(
                {"_id": ObjectId(user_id), "companion_progression.companion_id": episode["companion_id"]},
                {
                    "$inc": {
                        "companion_progression.$.xp": xp_earned,
                        "companion_progression.$.relationship_points": xp_earned,
                    },
                },
            )

        # Check if choice leads to end or another node
        next_node = None
        is_completed = False

        if choice["next_node_id"]:
            # Find next node
            next_node_data = next(
                (n for n in episode["script_nodes"] if n["node_id"] == choice["next_node_id"]),
                None,
            )
            if next_node_data:
                if next_node_data["is_end_node"]:
                    # End of episode
                    is_completed = True
                    # Update progress to completed
                    await progress_collection.update_one(
                        {"_id": ObjectId(progress["_id"])},
                        {
                            "$set": {
                                "status": "completed",
                                "current_node_id": None,
                                "total_xp_earned": total_xp_earned,
                                "completed_at": datetime.utcnow(),
                            },
                        },
                    )
                    next_node = next_node_data

                    # Add RL transition
                    await rl_transitions_collection.insert_one({
                        "user_id": user_id,
                        "companion_id": episode["companion_id"],
                        "state": {"episode_id": str(episode_id), "node": progress["current_node_id"]},
                        "action": {"choice_id": choice_id},
                        "reward": 10.0,
                        "next_state": {"episode_id": str(episode_id), "completed": True},
                        "done": True,
                        "created_at": datetime.utcnow(),
                    })
                else:
                    # Move to next node
                    await progress_collection.update_one(
                        {"_id": ObjectId(progress["_id"])},
                        {
                            "$set": {
                                "current_node_id": choice["next_node_id"],
                                "total_xp_earned": total_xp_earned,
                            },
                        },
                    )
                    next_node = next_node_data
        else:
            # No next node, complete episode
            is_completed = True
            await progress_collection.update_one(
                {"_id": ObjectId(progress["_id"])},
                {
                    "$set": {
                        "status": "completed",
                        "current_node_id": None,
                        "total_xp_earned": total_xp_earned,
                        "completed_at": datetime.utcnow(),
                    },
                },
            )
            # Add RL transition
            await rl_transitions_collection.insert_one({
                "user_id": user_id,
                "companion_id": episode["companion_id"],
                "state": {"episode_id": str(episode_id), "node": progress["current_node_id"]},
                "action": {"choice_id": choice_id},
                "reward": 10.0,
                "next_state": {"episode_id": str(episode_id), "completed": True},
                "done": True,
                "created_at": datetime.utcnow(),
            })

        return {
            "success": True,
            "next_node": next_node,
            "xp_earned": xp_earned,
            "total_xp_earned": total_xp_earned,
            "is_completed": is_completed,
        }

    @staticmethod
    async def get_episode_state(user_id: str, episode_id: str) -> Optional[EpisodeScriptNode]:
        """Get the current state of an episode for a user."""
        episodes_collection = await get_episodes_collection()
        progress_collection = await get_episode_progress_collection()

        episode = await episodes_collection.find_one({"_id": ObjectId(episode_id)})
        if not episode:
            raise ValueError("Episode not found")

        progress = await progress_collection.find_one({
            "user_id": user_id,
            "episode_id": str(episode_id),
        })
        if not progress:
            return None

        if progress["status"] == "completed":
            return None

        current_node = next(
            (n for n in episode["script_nodes"] if n["node_id"] == progress["current_node_id"]),
            None,
        )
        return EpisodeScriptNode(**current_node) if current_node else None

    @staticmethod
    async def get_completed_episodes(user_id: str, companion_id: str) -> list[EpisodeProgressInDB]:
        """Get all completed episodes for a user and companion."""
        progress_collection = await get_episode_progress_collection()
        cursor = progress_collection.find({
            "user_id": user_id,
            "companion_id": companion_id,
            "status": "completed",
        })
        results = []
        async for doc in cursor:
            results.append(EpisodeProgressInDB(**doc))
        return results
