from __future__ import annotations

import os

import openai

_PROVIDER_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def _provider_kwargs() -> dict:
    """Return common kwargs (api_key, base_url, timeout) from env vars."""
    provider = os.environ.get("AI_PROVIDER", "openai").lower()
    if provider not in _PROVIDER_BASE_URLS:
        raise ValueError(
            f"Unknown AI_PROVIDER '{provider}'. "
            f"Supported providers: {sorted(_PROVIDER_BASE_URLS)}"
        )
    api_key = os.environ.get("AI_PROVIDER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    return {"api_key": api_key, "base_url": _PROVIDER_BASE_URLS[provider], "timeout": 120.0}


def create_client() -> openai.OpenAI:
    """Create a synchronous OpenAI-compatible client from environment variables."""
    return openai.OpenAI(**_provider_kwargs())


def create_async_client() -> openai.AsyncOpenAI:
    """Create an async OpenAI-compatible client from environment variables."""
    return openai.AsyncOpenAI(**_provider_kwargs())
