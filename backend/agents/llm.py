"""Shared LLM client with OpenAI / Anthropic / mock fallback."""
from __future__ import annotations

import json
import re
from typing import Any

from backend.config import (
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    use_mock_llm,
)


def _extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def call_llm_json(system: str, user: str, mock_payload: dict[str, Any]) -> dict[str, Any]:
    """Call configured LLM and parse JSON. Falls back to mock_payload."""
    if use_mock_llm():
        return mock_payload

    try:
        if LLM_PROVIDER == "anthropic":
            return await _call_anthropic(system, user)
        return await _call_openai(system, user)
    except Exception as exc:  # noqa: BLE001 — MVP resilience
        print(f"[LLM] Error, using mock: {exc}")
        return mock_payload


async def _call_openai(system: str, user: str) -> dict[str, Any]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return _extract_json(content)


async def _call_anthropic(system: str, user: str) -> dict[str, Any]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    model = LLM_MODEL if LLM_MODEL.startswith("claude") else "claude-3-5-sonnet-20241022"
    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=system + "\n\nRespond with valid JSON only. No markdown fences.",
        messages=[{"role": "user", "content": user}],
    )
    content = response.content[0].text if response.content else "{}"
    return _extract_json(content)
