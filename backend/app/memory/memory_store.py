from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.memory.embedding_client import embed_text


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    memory_type: str
    content: str
    metadata: dict
    importance: float
    created_at: int


def _now_ms() -> int:
    return int(time.time() * 1000)


def _normalize(v: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(v)
    if denom == 0:
        return v
    return v / denom


class MemoryStore:
    def __init__(self, *, mongo_uri: str, mongo_db: str) -> None:
        self._client = AsyncIOMotorClient(mongo_uri)
        self._db: AsyncIOMotorDatabase = self._client[mongo_db]
        self._faiss = self._try_init_faiss()

    async def ensure_indexes(self) -> None:
        await self._db["memories"].create_index([("user_id", 1), ("companion_id", 1), ("created_at", -1)])
        await self._db["memories"].create_index([("user_id", 1), ("companion_id", 1), ("memory_type", 1)])
        await self._db["feedback"].create_index([("user_id", 1), ("companion_id", 1), ("created_at", -1)])

    async def clear_user_data(self, *, user_id: str) -> None:
        await self._db["memories"].delete_many({"user_id": user_id})
        await self._db["feedback"].delete_many({"user_id": user_id})

    def _try_init_faiss(self):
        try:
            import faiss  # type: ignore

            return faiss
        except Exception:
            return None

    @property
    def _memories(self):
        return self._db["memories"]

    @property
    def _feedback(self):
        return self._db["feedback"]

    async def add_memory(
        self,
        *,
        user_id: str,
        companion_id: str,
        memory_type: str,
        content: str,
        metadata: dict | None = None,
        importance: float = 1.0,
    ) -> str:
        vlist: list[float] | None = None
        try:
            vec = await embed_text(text=content)
            v = _normalize(np.asarray(vec, dtype=np.float32))
            vlist = v.astype(np.float32).tolist()
        except Exception:
            vlist = None
        created_at = _now_ms()
        doc = {
            "user_id": user_id,
            "companion_id": companion_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "importance": float(importance),
            "created_at": created_at,
        }
        if vlist is not None:
            doc["embedding"] = vlist
        res = await self._memories.insert_one(doc)
        return str(res.inserted_id)

    async def get_latest_story_memory(
        self, *, user_id: str, companion_id: str, kind: str | None = None
    ) -> MemoryRecord | None:
        query: dict = {"user_id": user_id, "companion_id": companion_id, "memory_type": "story_memory"}
        if kind:
            query["metadata.kind"] = kind
        doc = await self._memories.find_one(query, sort=[("created_at", -1)])
        if not doc:
            return None
        return MemoryRecord(
            id=str(doc.get("_id")),
            memory_type=str(doc.get("memory_type")),
            content=str(doc.get("content")),
            metadata=dict(doc.get("metadata") or {}),
            importance=float(doc.get("importance") or 1.0),
            created_at=int(doc.get("created_at") or 0),
        )

    async def export_feedback(self, *, user_id: str, companion_id: str | None = None) -> list[dict]:
        query: dict = {"user_id": user_id}
        if companion_id:
            query["companion_id"] = companion_id
        cursor = self._feedback.find(query, sort=[("created_at", 1)])
        out: list[dict] = []
        async for doc in cursor:
            out.append(
                {
                    "id": str(doc.get("_id")),
                    "user_id": str(doc.get("user_id")),
                    "companion_id": str(doc.get("companion_id")),
                    "rating": int(doc.get("rating") or 0),
                    "user_message": doc.get("user_message"),
                    "assistant_message": doc.get("assistant_message"),
                    "created_at": int(doc.get("created_at") or 0),
                }
            )
        return out

    async def get_recent_feedback(
        self, *, user_id: str, companion_id: str, limit: int = 5
    ) -> list[dict]:
        limit = max(1, min(int(limit), 20))
        cursor = self._feedback.find(
            {"user_id": user_id, "companion_id": companion_id}, sort=[("created_at", -1)], limit=limit
        )
        out: list[dict] = []
        async for doc in cursor:
            out.append(
                {
                    "rating": int(doc.get("rating") or 0),
                    "user_message": doc.get("user_message"),
                    "assistant_message": doc.get("assistant_message"),
                    "created_at": int(doc.get("created_at") or 0),
                }
            )
        return out

    async def search_memories(
        self,
        *,
        user_id: str,
        companion_id: str,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[MemoryRecord]:
        k = max(1, min(int(k), 20))
        q = _normalize(np.asarray(query_embedding, dtype=np.float32))
        docs: list[dict] = []
        cursor = self._memories.find({"user_id": user_id, "companion_id": companion_id})
        async for d in cursor:
            docs.append(d)
        if not docs:
            return []

        dim = int(q.shape[0])
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

        if self._faiss is not None:
            index = self._faiss.IndexFlatIP(dim)
            mat = np.vstack(vecs).astype(np.float32)
            index.add(mat)
            _, idxs = index.search(q.reshape(1, -1).astype(np.float32), k)
            out: list[MemoryRecord] = []
            for i in [int(x) for x in idxs[0] if int(x) != -1]:
                d = kept_docs[i]
                out.append(
                    MemoryRecord(
                        id=str(d.get("_id")),
                        memory_type=str(d.get("memory_type")),
                        content=str(d.get("content")),
                        metadata=dict(d.get("metadata") or {}),
                        importance=float(d.get("importance") or 1.0),
                        created_at=int(d.get("created_at") or 0),
                    )
                )
            return out

        scored: list[tuple[float, int]] = []
        for i, v in enumerate(vecs):
            scored.append((float(np.dot(v, q)), i))
        scored.sort(key=lambda t: t[0], reverse=True)
        out: list[MemoryRecord] = []
        for _, i in scored[:k]:
            d = kept_docs[i]
            out.append(
                MemoryRecord(
                    id=str(d.get("_id")),
                    memory_type=str(d.get("memory_type")),
                    content=str(d.get("content")),
                    metadata=dict(d.get("metadata") or {}),
                    importance=float(d.get("importance") or 1.0),
                    created_at=int(d.get("created_at") or 0),
                )
            )
        return out

    async def add_feedback(
        self,
        *,
        user_id: str,
        companion_id: str,
        rating: int,
        user_message: str | None = None,
        assistant_message: str | None = None,
    ) -> str:
        rating = int(rating)
        if rating not in (-1, 1):
            raise ValueError("rating must be -1 or 1")

        created_at = _now_ms()
        doc = {
            "user_id": user_id,
            "companion_id": companion_id,
            "rating": rating,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "created_at": created_at,
        }
        res = await self._feedback.insert_one(doc)
        return str(res.inserted_id)

