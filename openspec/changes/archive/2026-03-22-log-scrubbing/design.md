## Context

The agent logs tool arguments, tool results, and final responses. The LLM can
pass secrets (API keys, tokens, passwords) dynamically in any field — most
notably in `http_post` body or URL parameters. There is no static annotation
possible; scrubbing must be applied at the logging layer, universally.

Current logging pipeline: `logger.info(msg, extra={...})` → `ContextFilter` →
`HumanFormatter` / `JsonFormatter` → stdout / file handler.

## Goals / Non-Goals

**Goals:**

- Mask known secret patterns (OpenAI keys, Bearer tokens, generic key/token/password fields)
- Mask explicit secrets listed in `AGENT_SCRUB_SECRETS` env var
- Work transparently — no changes to call sites
- Provide `scrub()` as a reusable utility (future: sanitize error messages)

**Non-Goals:**

- Scrubbing exception tracebacks (deferred)
- Auto-discovery of secrets from `.env` (user must opt-in via `AGENT_SCRUB_SECRETS`)
- Detecting arbitrary high-entropy strings as secrets

## Decisions

### D1: Scrubbing as a `logging.Filter`, not in formatters

A `logging.Filter` sits between the logger and the handler — it can mutate
`LogRecord` fields before any formatter serializes them. This means both
`HumanFormatter` and `JsonFormatter` receive already-scrubbed data, with zero
changes to the formatters themselves.

Alternative: mutate in formatters. Rejected — duplicates logic, misses `extra`
fields that formatters iterate dynamically.

### D2: Scrub `msg`, `args`, and all `extra` fields recursively

`record.getMessage()` interpolates `args` into `msg`. To scrub the final
message, we must scrub both `record.msg` (the template) and `record.args`
(the values). Extra fields can be nested dicts/lists, so recursion is needed.

### D3: Two-layer scrubbing: regex patterns + explicit values

**Layer 1 — regex (catch-all):** Recognises known secret shapes:

- `sk-[a-zA-Z0-9\-_]{20,}` → `sk-***` (preserve prefix for debuggability)
- `Bearer\s+\S{8,}` → `Bearer ***`
- JSON/query fields: `(["&?](?:api[_-]?key|token|password|secret)[":\s=]+)\S{4,}` → `\1***`

**Layer 2 — explicit values (env var):** `AGENT_SCRUB_SECRETS=val1,val2` are
matched literally (case-sensitive, longest-first to avoid prefix collisions).
Applied after regex so env-var secrets always win.

Alternative: only regex. Rejected — cannot cover custom/opaque key formats.
Alternative: only explicit values. Rejected — tedious for known patterns like OpenAI keys.

### D4: `scrub.py` as a standalone module

`scrub(text: str) -> str` lives in its own module, initialized once at import
time (patterns compiled, env var read). The `ScrubFilter` in `logging.py`
imports and calls it. This keeps `logging.py` focused on configuration and
makes `scrub()` testable in isolation and reusable elsewhere.

## Risks / Trade-offs

**[Risk] Regex false positives** — a random long alphanumeric string matching
`sk-` prefix would be masked.
→ Mitigation: prefix-anchored patterns are specific enough in practice; the
`sk-` pattern requires ≥20 chars after the prefix.

**[Risk] Performance** — every log record is regex-scanned.
→ Mitigation: patterns are pre-compiled; log volume is low (tool calls, not
hot paths); acceptable overhead.

**[Risk] Env var read at import time** — if `AGENT_SCRUB_SECRETS` is set after
`scrub.py` is imported, changes won't take effect.
→ Mitigation: documented limitation; standard for this type of configuration.

**[Risk] Scrubbing mutates the LogRecord** — downstream handlers (if any added
later) will receive the scrubbed version, not the original.
→ This is intentional and desirable.

## Open Questions

None — scope is well-defined and implementation is straightforward.
