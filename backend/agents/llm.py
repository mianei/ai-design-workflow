"""Shared LLM client with OpenAI / Kimi(Moonshot) / Anthropic / mock fallback."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from backend.config import (
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT_SECONDS,
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
    # Recover leading/trailing prose around a JSON object
    if not text.startswith("{") and "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]
    return json.loads(text)


async def call_llm_json(system: str, user: str, mock_payload: dict[str, Any]) -> dict[str, Any]:
    """Call configured LLM and parse JSON. Uses mock only when mock mode is enabled."""
    if use_mock_llm():
        print("[LLM] mock_mode enabled — using built-in demo payload")
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
                prefer_json_mode=False,
            )
        return await _call_openai_compatible(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL or None,
            system=system,
            user=user,
            prefer_json_mode=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"LLM call failed ({LLM_PROVIDER}/{LLM_MODEL}): {exc}") from exc


async def _call_openai_compatible(
    *,
    api_key: str,
    base_url: str | None,
    system: str,
    user: str,
    prefer_json_mode: bool,
) -> dict[str, Any]:
    from openai import AsyncOpenAI

    timeout = httpx.Timeout(LLM_TIMEOUT_SECONDS, connect=20.0)
    kwargs: dict[str, Any] = {"api_key": api_key, "timeout": timeout}
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
        "messages": messages,
    }
    # kimi-k3 only allows temperature=1; omit for kimi family to use server default when needed
    if LLM_PROVIDER in {"kimi", "moonshot"} or LLM_MODEL.startswith("kimi"):
        create_kwargs["temperature"] = 1
    else:
        create_kwargs["temperature"] = 0.7

    if prefer_json_mode:
        create_kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await client.chat.completions.create(**create_kwargs)
    except Exception as first_exc:
        msg = str(first_exc).lower()
        if prefer_json_mode and ("response_format" in msg or "json_object" in msg or "invalid" in msg):
            create_kwargs.pop("response_format", None)
            response = await client.chat.completions.create(**create_kwargs)
        else:
            raise

    content = response.choices[0].message.content or "{}"
    return _extract_json(content)


async def _call_anthropic(system: str, user: str) -> dict[str, Any]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, timeout=LLM_TIMEOUT_SECONDS)
    model = LLM_MODEL if LLM_MODEL.startswith("claude") else "claude-3-5-sonnet-20241022"
    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=system + "\n\nRespond with valid JSON only. No markdown fences.",
        messages=[{"role": "user", "content": user}],
    )
    content = response.content[0].text if response.content else "{}"
    return _extract_json(content)
