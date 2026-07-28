"""
Test script to check Oliver (study_buddy) and Victoria (rival) chat responses!
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

# Initialize settings first so environment variables are loaded!
from app.config import get_settings
settings = get_settings()

from app.services.openrouter_client import generate_reply
from app.companions.prompt_builder import build_messages
from app.companions.companions import companions

async def test_companion(companion_id: str, test_message: str):
    """Test a specific companion's response to a message!"""
    template = companions[companion_id]
    print(f"\n{'=' * 60}")
    print(f"Testing {template['name']} ({companion_id})")
    print(f"{'=' * 60}")
    print(f"User message: {test_message}")
    print()

    # Build messages just like the chat endpoint!
    messages, _ = build_messages(
        companion_id=companion_id,
        companion_name=template["name"],
        companion_age=template["age"],
        companion_relationship=template["relationship"],
        companion_story=template["story"],
        companion_traits=template["traits"],
        companion_system_prompt=template["system_prompt"],
        scenario_memory="",
        retrieved_memories=[],
        user_message=test_message,
        conversation_history=[],
        use_rl_optimization=False,
    )

    # Get the model for this companion!
    model = settings.get_model_for_companion(companion_id)
    print(f"Using model: {model}")
    print()

    # Call generate_reply directly!
    try:
        reply = await generate_reply(messages=messages, model=model)
        print(f"{template['name']}'s reply: {reply}")
        return reply
    except Exception as e:
        print(f"Error getting reply: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run all test cases!"""
    test_cases = [
        ("study_buddy", "Can you explain quantum mechanics in simple terms?"),
        ("study_buddy", "I have an exam tomorrow, what should I study first?"),
        ("rival", "I think I aced that math test. What did you get?"),
        ("rival", "Can you solve this problem: 2x + 5 = 15?"),
    ]

    print("=" * 60)
    print("Testing Oliver (study_buddy) and Victoria (rival) responses")
    print("=" * 60)

    for companion_id, test_msg in test_cases:
        await test_companion(companion_id, test_msg)

if __name__ == "__main__":
    asyncio.run(main())
