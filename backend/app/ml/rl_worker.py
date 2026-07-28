"""
Background RL training worker for trainable companions.

Runs periodically in the background to train RL agents using
accumulated transitions from the `rl_transitions` collection.
"""

from __future__ import annotations

import asyncio
import logging

from app.config import get_settings
from app.ml.rl_training import run_training_for_all_companions

logger = logging.getLogger(__name__)

_training_task: asyncio.Task | None = None


async def _training_loop() -> None:
    """Periodic training loop that runs in the background."""
    settings = get_settings()
    interval_seconds = settings.rl_training_interval_minutes * 60

    logger.info(
        f"RL training worker started (interval={settings.rl_training_interval_minutes}min)"
    )

    while True:
        try:
            await asyncio.sleep(interval_seconds)
            logger.info("Starting background RL training cycle...")
            results = await run_training_for_all_companions()
            for r in results:
                cid = r.get("companion_id", "?")
                total = r.get("total_transitions", 0)
                logger.info(f"Training complete for {cid}: {total} transitions processed")
        except asyncio.CancelledError:
            logger.info("RL training worker cancelled")
            break
        except Exception as e:
            logger.error(f"RL training cycle failed: {e}", exc_info=True)
            # Wait before retrying
            await asyncio.sleep(60)


def start_training_worker() -> None:
    """Start the background training worker as an asyncio task."""
    global _training_task
    if _training_task is None or _training_task.done():
        _training_task = asyncio.create_task(_training_loop())
        logger.info("RL background training worker launched")


def stop_training_worker() -> None:
    """Cancel the background training worker."""
    global _training_task
    if _training_task is not None and not _training_task.done():
        _training_task.cancel()
        logger.info("RL background training worker stop requested")
