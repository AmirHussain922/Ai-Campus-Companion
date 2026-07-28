from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.memory.embedding_client import embed_text
from app.memory.memory import get_memory_store
from app.services.openrouter_client import OpenRouterError

router = APIRouter(prefix="/memory", tags=["memory"])


class AddMemoryRequest(BaseModel):
    user_id: str = Field(default="local", min_length=1)
    companion_id: str = Field(min_length=1, description="Unique companion key (e.g. frontend companion id).")
    memory_type: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=50_000)
    metadata: dict = Field(default_factory=dict)
    importance: float = Field(default=1.0, ge=0.0, le=10.0)


class AddMemoryResponse(BaseModel):
    id: str


class SearchMemoryResponseItem(BaseModel):
    id: str
    memory_type: str
    content: str
    metadata: dict
    importance: float
    created_at: int


@router.post("", response_model=AddMemoryResponse)
async def add_memory(req: AddMemoryRequest) -> AddMemoryResponse:
    store = get_memory_store()
    try:
        memory_id = await store.add_memory(
            user_id=req.user_id,
            companion_id=req.companion_id,
            memory_type=req.memory_type,
            content=req.content,
            metadata=req.metadata,
            importance=req.importance,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return AddMemoryResponse(id=memory_id)


@router.get("/search", response_model=list[SearchMemoryResponseItem])
async def search_memory(
    user_id: str = "local",
    companion_id: str = "",
    query: str = "",
    k: int = 5,
) -> list[SearchMemoryResponseItem]:
    if not companion_id:
        raise HTTPException(status_code=400, detail="companion_id is required.")
    if not query:
        return []

    store = get_memory_store()
    try:
        vec = await embed_text(text=query)
    except OpenRouterError:
        return []
    memories = await store.search_memories(user_id=user_id, companion_id=companion_id, query_embedding=vec, k=k)
    return [
        SearchMemoryResponseItem(
            id=m.id,
            memory_type=m.memory_type,
            content=m.content,
            metadata=m.metadata,
            importance=m.importance,
            created_at=m.created_at,
        )
        for m in memories
    ]


class ScenarioUnlockRequest(BaseModel):
    user_id: str = Field(default="local", min_length=1)
    companion_id: str = Field(min_length=1, description="Unique companion key (e.g. frontend companion id).")
    title: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    backstory: str = Field(min_length=1)
    narration: str = Field(min_length=1)


@router.post("/scenario/unlock", response_model=AddMemoryResponse)
async def scenario_unlock(req: ScenarioUnlockRequest) -> AddMemoryResponse:
    content = (
        f"{req.title}\n\n"
        f"Scenario:\n{req.scenario}\n\n"
        f"Backstory:\n{req.backstory}\n\n"
        f"Narration:\n{req.narration}"
    )
    store = get_memory_store()
    memory_id = await store.add_memory(
        user_id=req.user_id,
        companion_id=req.companion_id,
        memory_type="story_memory",
        content=content,
        metadata={"title": req.title, "kind": "scenario"},
        importance=3.0,
    )
    return AddMemoryResponse(id=memory_id)


class FeedbackRequest(BaseModel):
    user_id: str = Field(default="local", min_length=1)
    companion_id: str = Field(min_length=1, description="Unique companion key (e.g. frontend companion id).")
    rating: int = Field(ge=-1, le=1)
    user_message: str | None = None
    assistant_message: str | None = None


class FeedbackResponse(BaseModel):
    id: str


@router.post("/feedback", response_model=FeedbackResponse)
async def add_feedback(req: FeedbackRequest) -> FeedbackResponse:
    if req.rating not in (-1, 1):
        raise HTTPException(status_code=400, detail="rating must be -1 or 1.")
    store = get_memory_store()
    try:
        fid = await store.add_feedback(
            user_id=req.user_id,
            companion_id=req.companion_id,
            rating=req.rating,
            user_message=req.user_message,
            assistant_message=req.assistant_message,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        label = "GOOD" if req.rating == 1 else "BAD"
        parts: list[str] = [f"User feedback: {label}"]
        if req.user_message:
            parts.append(f"User message: {req.user_message}")
        if req.assistant_message:
            parts.append(f"Assistant reply: {req.assistant_message}")
        await store.add_memory(
            user_id=req.user_id,
            companion_id=req.companion_id,
            memory_type="relationship_memory",
            content="\n".join(parts),
            metadata={"kind": "feedback", "rating": req.rating},
            importance=3.0 if req.rating == -1 else 2.0,
        )
    except Exception:
        pass

    return FeedbackResponse(id=fid)


@router.get("/feedback/export")
async def export_feedback(user_id: str = "local", companion_id: str | None = None) -> list[dict]:
    store = get_memory_store()
    return await store.export_feedback(user_id=user_id, companion_id=companion_id)

