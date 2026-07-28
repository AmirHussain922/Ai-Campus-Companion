from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class OpenRouterError(RuntimeError):
    pass


def _extract_text(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterError("OpenRouter response missing choices.")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise OpenRouterError("OpenRouter response missing message.")

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
        text = "".join(text_parts).strip()
        if text:
            return text

    raise OpenRouterError("OpenRouter response missing content.")


async def generate_reply(*, messages: list[dict], model: str | None = None) -> str:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise OpenRouterError("Missing OPENROUTER_API_KEY environment variable.")

    # Use caller-specified model, or fall back to the global default
    chosen_model = model or settings.openrouter_model

    logger.info(f"generate_reply called: model={chosen_model}, messages={len(messages)}")

    payload: dict[str, Any] = {
        "model": chosen_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
    }

    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer
    if settings.openrouter_x_title:
        headers["X-Title"] = settings.openrouter_x_title

    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    if resp.status_code >= 400:
        detail: str
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            detail = resp.text
        logger.error(f"OpenRouter error {resp.status_code}: {detail}")
        raise OpenRouterError(f"OpenRouter error {resp.status_code}: {detail}")

    try:
        data = resp.json()
        return _extract_text(data)
    except Exception as e:
        raise OpenRouterError("OpenRouter returned invalid JSON.") from e


