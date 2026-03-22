## 1. Core scrubbing module

- [x] 1.1 Create `src/agent/scrub.py` with `scrub(text: str) -> str` function
- [x] 1.2 Implement regex layer: OpenAI key pattern (`sk-***`), Bearer token, generic key/token/password/secret fields
- [x] 1.3 Implement explicit-value layer: read `AGENT_SCRUB_SECRETS` at import time, sort longest-first, replace literally

## 2. Logging integration

- [x] 2.1 Add `ScrubFilter(logging.Filter)` to `src/agent/logging.py`
- [x] 2.2 Implement recursive scrubbing of `record.msg`, `record.args`, and all extra fields in `ScrubFilter.filter()`
- [x] 2.3 Attach `ScrubFilter` to both stdout and file handlers in `configure_logging()`

## 3. Tests

- [x] 3.1 Test `scrub()` with each regex pattern (OpenAI key, Bearer, api_key/token/password fields)
- [x] 3.2 Test explicit-value scrubbing via `AGENT_SCRUB_SECRETS` (single, multiple, longest-first ordering)
- [x] 3.3 Test `ScrubFilter` with secret in `msg`, in `args`, and in nested `extra` dict
- [x] 3.4 Test that `ScrubFilter.filter()` always returns `True`

## 4. Documentation

- [x] 4.1 Document `AGENT_SCRUB_SECRETS` env var in `CLAUDE.md` environment variables section
