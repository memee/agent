from __future__ import annotations

import os

import openai

_PROVIDER_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def create_client() -> openai.OpenAI:
    """Create an OpenAI-compatible client from environment variables.

    Reads:
      AI_PROVIDER        — provider name: 'openai' (default) or 'openrouter'
      AI_PROVIDER_API_KEY — API key for the selected provider

    Falls back to OPENAI_API_KEY when AI_PROVIDER_API_KEY is not set.
    """
    provider = os.environ.get("AI_PROVIDER", "openai").lower()

    if provider not in _PROVIDER_BASE_URLS:
        raise ValueError(
            f"Unknown AI_PROVIDER '{provider}'. "
            f"Supported providers: {sorted(_PROVIDER_BASE_URLS)}"
        )

    api_key = os.environ.get("AI_PROVIDER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = _PROVIDER_BASE_URLS[provider]

    return openai.OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
