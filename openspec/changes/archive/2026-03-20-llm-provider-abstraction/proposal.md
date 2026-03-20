## Why

The agent framework hard-codes OpenAI as the only LLM provider, making it impossible to switch to alternatives like OpenRouter without modifying library code. Adding a thin factory abstraction lets users configure the provider via environment variables with zero code changes.

## What Changes

- New `src/agent/client.py` module with a `create_client()` factory function
- `delegate.py` updated to call `create_client()` instead of inlining `openai.OpenAI(api_key=...)`
- `.env.example` updated to document `AI_PROVIDER` and `AI_PROVIDER_API_KEY`
- `import os` and `import openai` removed from `delegate.py` (no longer needed there)

## Capabilities

### New Capabilities

- `llm-client`: Factory that creates an OpenAI-compatible client from `AI_PROVIDER` and `AI_PROVIDER_API_KEY` env vars, with support for `openai` (default) and `openrouter` providers

### Modified Capabilities

<!-- No existing spec-level requirement changes -->

## Impact

- **`src/agent/builtin_tools/delegate.py`**: drops inline client creation, calls `create_client()` instead
- **`src/agent/client.py`**: new file
- **`.env.example`**: new env vars documented
- No changes to public `run()` API — callers who pass their own client are unaffected
- No new dependencies (uses existing `openai` SDK)
