"""
Companion memory store for trainable companions.

Separate from the legacy memory_store.py — this operates on the
`companion_memories` collection and uses FAISS for semantic search.
Used exclusively by trainable companions (Julian, Victoria).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from app.core.database import get_database
from app.memory.embedding_client import embed_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompanionMemoryRecord:
    """Immutable representation of a companion memory."""
    id: str
    memory_type: str
    content: str
    metadata: dict
    importance: float
    created_at: datetime


def _normalize(v: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(v)
    if denom == 0:
        return v
    return v / denom


async def add_companion_memory(
    *,
    user_id: str,
    companion_id: str,
    memory_type: str,
    content: str,
    metadata: dict | None = None,
    importance: float = 1.0,
) -> str:
    """Store a memory with its embedding vector for a trainable companion."""
    db = await get_database()
    col = db.companion_memories

    # Generate embedding
    embedding: list[float] | None = None
    try:
        vec = await embed_text(text=content)
        v = _normalize(np.asarray(vec, dtype=np.float32))
        embedding = v.astype(np.float32).tolist()
    except Exception as e:
        logger.warning(f"Failed to generate embedding for companion memory: {e}")

    doc = {
        "user_id": user_id,
        "companion_id": companion_id,
        "memory_type": memory_type,
        "content": content,
        "metadata": metadata or {},
        "importance": float(importance),
        "embedding": embedding,
        "created_at": datetime.now(timezone.utc),
    }
    result = await col.insert_one(doc)
    return str(result.inserted_id)


async def search_companion_memories(
    *,
    user_id: str,
    companion_id: str,
    query_embedding: list[float],
    k: int = 5,
) -> list[CompanionMemoryRecord]:
    """Semantic search over companion memories using FAISS or brute-force cosine."""
    db = await get_database()
    col = db.companion_memories

    q = _normalize(np.asarray(query_embedding, dtype=np.float32))
    dim = int(q.shape[0])

    # Fetch all memories with embeddings for this user+companion
    cursor = col.find({"user_id": user_id, "companion_id": companion_id})
    docs: list[dict] = []
    async for d in cursor:
        docs.append(d)

    if not docs:
        return []

    vecs: list[np.ndarray] = []
    kept_docs: list[dict] = []
    for d in docs:
        emb = d.get("embedding")
        if not isinstance(emb, list):
            continue
        v = np.asarray(emb, dtype=np.float32)
        if v.shape[0] != dim:
            continue
        vecs.append(_normalize(v).astype(np.float32))
        kept_docs.append(d)

    if not vecs:
        return []

    # Try FAISS
    faiss = _try_init_faiss()
    if faiss is not None:
        index = faiss.IndexFlatIP(dim)
        mat = np.vstack(vecs).astype(np.float32)
        index.add(mat)
        _, idxs = index.search(q.reshape(1, -1).astype(np.float32), k)
        results: list[CompanionMemoryRecord] = []
        for i in [int(x) for x in idxs[0] if int(x) != -1]:
            d = kept_docs[i]
            results.append(_doc_to_record(d))
        return results

    # Fallback: brute-force cosine similarity
    scored: list[tuple[float, int]] = []
    for i, v in enumerate(vecs):
        scored.append((float(np.dot(v, q)), i))
    scored.sort(key=lambda t: t[0], reverse=True)
    results = []
    for _, i in scored[:k]:
        d = kept_docs[i]
        results.append(_doc_to_record(d))
    return results


async def get_recent_memories(
    *,
    user_id: str,
    companion_id: str,
    memory_type: str | None = None,
    limit: int = 5,
) -> list[CompanionMemoryRecord]:
    """Get the most recent memories, optionally filtered by type."""
    db = await get_database()
    col = db.companion_memories
    query: dict = {"user_id": user_id, "companion_id": companion_id}
    if memory_type:
        query["memory_type"] = memory_type
    cursor = col.find(query).sort("created_at", -1).limit(limit)
    results: list[CompanionMemoryRecord] = []
    async for d in cursor:
        results.append(_doc_to_record(d))
    return results


async def store_rl_transition(
    *,
    user_id: str,
    companion_id: str,
    state: dict,
    action: dict,
    reward: float,
    next_state: dict,
    done: bool = False,
) -> str:
    """Store an RL transition in the rl_transitions collection."""
    db = await get_database()
    doc = {
        "user_id": user_id,
        "companion_id": companion_id,
        "state": state,
        "action": action,
        "reward": float(reward),
        "next_state": next_state,
        "done": done,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.rl_transitions.insert_one(doc)
    return str(result.inserted_id)


def _doc_to_record(d: dict) -> CompanionMemoryRecord:
    return CompanionMemoryRecord(
        id=str(d.get("_id", "")),
        memory_type=str(d.get("memory_type", "memory")),
        content=str(d.get("content", "")),
        metadata=dict(d.get("metadata") or {}),
        importance=float(d.get("importance") or 1.0),
        created_at=d.get("created_at", datetime.now(timezone.utc)),
    )


def _try_init_faiss():
    try:
        import faiss  # type: ignore
        return faiss
    except Exception:
        return None
