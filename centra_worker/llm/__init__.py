from __future__ import annotations
import os
from typing import Optional
from centra_worker.llm.base import BaseLLMProvider, AgentDecision
from centra_worker.llm.mock_provider import SmartMockProvider
from centra_worker.llm.openai_provider import OpenAIProvider
from centra_worker.llm.gemini_provider import GeminiProvider


def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory to return the appropriate LLM provider.
    Defaults to auto-detecting configured environment variables,
    or falls back to the deterministic SmartMockProvider if no API keys are present.
    """
    requested = (provider_type or os.getenv("LLM_PROVIDER", "auto")).lower()

    if requested == "openai":
        return OpenAIProvider()
    elif requested == "gemini":
        return GeminiProvider()
    elif requested == "mock":
        return SmartMockProvider()

    # Auto mode
    if os.getenv("OPENAI_API_KEY"):
        try:
            return OpenAIProvider()
        except Exception:
            pass

    if os.getenv("GEMINI_API_KEY"):
        try:
            return GeminiProvider()
        except Exception:
            pass

    # Default robust offline provider
    return SmartMockProvider()


__all__ = [
    "BaseLLMProvider",
    "AgentDecision",
    "SmartMockProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "get_llm_provider",
]
