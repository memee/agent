## Context

The agent framework currently couples client creation directly to OpenAI: `delegate.py` hard-codes `openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))`. The `openai` Python SDK supports any OpenAI-compatible API via `base_url`, so switching providers requires only pointing to a different endpoint — no protocol changes needed.

## Goals / Non-Goals

**Goals:**

- Single `create_client()` factory that reads `AI_PROVIDER` and `AI_PROVIDER_API_KEY`
- Support `openai` (default) and `openrouter` out of the box
- Backwards-compatible: existing `OPENAI_API_KEY` still works when `AI_PROVIDER_API_KEY` is absent
- No new dependencies

**Non-Goals:**

- Supporting providers that are *not* OpenAI-compatible (would need a different interface)
- Per-profile provider configuration (can be added later if needed)
- Credential validation at startup

## Decisions

### D1: New `client.py` module, not inline in `delegate.py`

`create_client()` lives in `src/agent/client.py`. This makes it importable by any caller (including user-written main scripts), not just `delegate`.

*Alternative*: embed logic in `delegate.py`. Rejected — callers who build their own orchestrators would need to duplicate it.

### D2: Env-var driven, not constructor args

Provider and key come from environment, not function parameters. Consistent with how the rest of the framework reads config (sandbox presets, API keys).

*Alternative*: `create_client(provider=..., api_key=...)`. Rejected — adds unnecessary call-site verbosity for a global config concern.

### D3: Fallback to `OPENAI_API_KEY`

When `AI_PROVIDER_API_KEY` is unset, fall back to `OPENAI_API_KEY`. Existing projects keep working without any env changes.

### D4: Fail fast on unknown provider

Raise `ValueError` immediately if `AI_PROVIDER` is set to an unrecognised value. Silent misconfigurations (e.g. typos) are harder to debug than an explicit error at startup.

## Risks / Trade-offs

- [Provider list is static] → Adding a new provider requires a code change. Mitigation: the dict is trivially extensible; document it clearly.
- [Fallback chain hides misconfiguration] → If a user sets `AI_PROVIDER=openrouter` but forgets `AI_PROVIDER_API_KEY`, it silently falls back to `OPENAI_API_KEY`. Mitigation: acceptable trade-off; OpenRouter will return an auth error quickly.
