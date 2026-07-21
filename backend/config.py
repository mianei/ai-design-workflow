"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'database' / 'workflow.db'}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # openai | anthropic | mock
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]


def use_mock_llm() -> bool:
    """Fallback to deterministic mock outputs when no API key is configured."""
    if LLM_PROVIDER == "mock":
        return True
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        return True
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        return True
    return False
