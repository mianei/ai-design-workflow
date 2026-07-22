"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

_db_file = (ROOT_DIR / "database" / "workflow.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_db_file}")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "") or os.getenv("KIMI_API_KEY", "")
MOONSHOT_BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # openai | anthropic | kimi | moonshot | mock
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
PIPELINE_AGENT_TIMEOUT_SECONDS = float(os.getenv("PIPELINE_AGENT_TIMEOUT_SECONDS", "300"))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]


def use_mock_llm() -> bool:
    """Fallback to deterministic mock outputs when no API key is configured."""
    if LLM_PROVIDER == "mock":
        return True
    if LLM_PROVIDER in {"kimi", "moonshot"} and not MOONSHOT_API_KEY:
        return True
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        return True
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        return True
    return False
