## 1. Create llm-client module

- [x] 1.1 Create `src/agent/client.py` with `create_client()` factory reading `AI_PROVIDER` and `AI_PROVIDER_API_KEY`
- [x] 1.2 Add provider → base_url mapping for `openai` and `openrouter`
- [x] 1.3 Implement `OPENAI_API_KEY` fallback when `AI_PROVIDER_API_KEY` is not set
- [x] 1.4 Raise `ValueError` with helpful message for unknown providers

## 2. Update delegate tool

- [x] 2.1 Replace inline `openai.OpenAI(api_key=...)` in `delegate.py` with `create_client()`
- [x] 2.2 Remove unused `import os` and `import openai` from `delegate.py`

## 3. Update env documentation

- [x] 3.1 Add `AI_PROVIDER` and `AI_PROVIDER_API_KEY` entries to `.env.example`
