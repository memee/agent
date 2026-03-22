## Why

Agent logs may contain secrets (API keys, tokens, passwords) in tool arguments,
tool results, and final responses — because the LLM can pass secrets dynamically
to any tool (e.g. `http_post` body). There is no safe point to intercept them
before logging without a dedicated scrubbing layer.

## What Changes

- New `scrub.py` module with a `scrub(text: str) -> str` utility function that
  applies regex patterns and explicit secret values to mask sensitive data
- New `ScrubFilter` logging filter that applies `scrub()` to all log record
  fields (message + all `extra` fields, recursively)
- `configure_logging()` updated to attach `ScrubFilter` to both handlers
- New `AGENT_SCRUB_SECRETS` environment variable for explicit secret values

## Capabilities

### New Capabilities

- `log-scrubbing`: Masking of secrets in log output via regex patterns and
  explicit values, applied transparently through the logging pipeline

### Modified Capabilities

- `agent-logging`: `configure_logging()` gains `ScrubFilter` on both handlers;
  no behavior changes to existing format or handlers

## Impact

- `src/agent/scrub.py` — new file
- `src/agent/logging.py` — `configure_logging()` updated
- `AGENT_SCRUB_SECRETS` env var documented in README / CLAUDE.md
- No changes to public API; `scrub()` is usable as a utility outside logging
