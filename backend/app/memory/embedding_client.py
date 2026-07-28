from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.services.openrouter_client import OpenRouterError


async def embed_text(*, text: str) -> list[float]:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise OpenRouterError("Missing OPENROUTER_API_KEY environment variable.")

    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer
    if settings.openrouter_x_title:
        headers["X-Title"] = settings.openrouter_x_title

    payload: dict[str, Any] = {
        "model": settings.openrouter_embedding_model,
        "input": text,
    }

    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(
                f"{settings.openrouter_base_url}/embeddings",
                headers=headers,
                json=payload,
            )
        except httpx.HTTPError as e:
            msg = str(e).strip()
            if not msg:
                msg = repr(e)
            raise OpenRouterError(f"Failed to reach OpenRouter embeddings: {type(e).__name__}: {msg}") from e

    if resp.status_code >= 400:
        detail: str
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            detail = resp.text
        raise OpenRouterError(f"OpenRouter embeddings error ({resp.status_code}): {detail}")

    try:
        data = resp.json()
    except Exception as e:
        raise OpenRouterError("OpenRouter embeddings returned invalid JSON.") from e

    embeddings = data.get("data")
    if not isinstance(embeddings, list) or not embeddings:
        raise OpenRouterError("OpenRouter embeddings response missing data.")
    vec = embeddings[0].get("embedding")
    if not isinstance(vec, list) or not vec or not all(isinstance(x, (int, float)) for x in vec):
        raise OpenRouterError("OpenRouter embeddings response missing embedding vector.")

    return [float(x) for x in vec]

