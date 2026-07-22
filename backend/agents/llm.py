"""Shared LLM client with OpenAI / Kimi(Moonshot) / Anthropic / mock fallback."""
from __future__ import annotations

import json
import re
from typing import Any

from backend.config import (
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    MOONSHOT_API_KEY,
    MOONSHOT_BASE_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
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
        if LLM_PROVIDER in {"kimi", "moonshot"}:
            return await _call_openai_compatible(
                api_key=MOONSHOT_API_KEY,
                base_url=MOONSHOT_BASE_URL,
                system=system,
                user=user,
                prefer_json_mode=False,  # Moonshot 部分模型对 json_object 支持不稳定
            )
        return await _call_openai_compatible(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL or None,
            system=system,
            user=user,
            prefer_json_mode=True,
        )
    except Exception as exc:  # noqa: BLE001 — MVP resilience
        print(f"[LLM] Error, using mock: {exc}")
        return mock_payload


async def _call_openai_compatible(
    *,
    api_key: str,
    base_url: str | None,
    system: str,
    user: str,
    prefer_json_mode: bool,
) -> dict[str, Any]:
    from openai import AsyncOpenAI

    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = AsyncOpenAI(**kwargs)

    messages = [
        {
            "role": "system",
            "content": system + "\n\n请只输出合法 JSON 对象，不要 Markdown 代码块或额外说明。",
        },
        {"role": "user", "content": user},
    ]

    create_kwargs: dict[str, Any] = {
        "model": LLM_MODEL,
        "temperature": 0.7,
        "messages": messages,
    }
    if prefer_json_mode:
        create_kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await client.chat.completions.create(**create_kwargs)
    except Exception:
        # 部分兼容端点不支持 response_format，降级重试
        create_kwargs.pop("response_format", None)
        response = await client.chat.completions.create(**create_kwargs)

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
