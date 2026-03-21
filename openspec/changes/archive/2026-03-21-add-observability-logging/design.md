## Context

The agent currently has no observability — `run()` calls the LLM and executes tools with no timing, no token tracking, and no structured output. When debugging a multi-step run or a sub-agent hierarchy, there is no way to know what happened, in what order, or at what cost.

The codebase is synchronous and single-threaded. Sub-agents are invoked via `delegate()`, which calls `run()` directly on the same thread. There are no external dependencies beyond the OpenAI-compatible client.

## Goals / Non-Goals

**Goals:**

- Capture LLM call metrics: model, duration_ms, prompt_tokens, completion_tokens, total_tokens
- Capture tool call metrics: tool name, arguments, duration_ms, result preview (first 200 chars)
- Carry execution context (run_id, parent_run_id, depth, agent_name, iteration) through the call stack without passing it explicitly
- Emit human-readable logs to stdout and structured JSON logs to a file
- Sub-agent context inherits from parent automatically

**Non-Goals:**

- OpenTelemetry or distributed tracing
- TUI integration (future — will add a third handler without touching this code)
- Async support
- Log rotation or log management

## Decisions

### 1. `contextvars` for execution context, not explicit parameters

**Decision:** Use `contextvars.ContextVar` for run_id, parent_run_id, depth, agent_name, and iteration. Set at `run()` entry. Read by log calls anywhere in the call stack.

**Why:** Python's `contextvars` is copied automatically into sub-calls on the same thread. Setting a var in the child does not affect the parent. This gives us propagation without threading risk and without polluting every function signature with an `ctx` parameter.

**Alternatives considered:**

- Thread-local storage (`threading.local`) — works but semantically wrong for coroutines, and less idiomatic for this pattern
- Explicit `context` parameter on `run()` — cleaner API but intrusive; every caller must construct and pass context

### 2. Python `logging` as the event backbone, not a custom observer

**Decision:** Instrument `run()` and `registry.execute()` with `logger.info(...)` calls using `extra={}` for structured fields. Configure handlers externally (stdout + file).

**Why:** `logging` already supports multiple handlers, log levels, and filters. Adding a TUI handler later requires zero changes to instrumented code. An observer/callback pattern would require changing `run()`'s signature and all call sites.

**Alternatives considered:**

- Custom observer passed to `run()` — more explicit, but breaks the call site API and duplicates what `logging` handlers already do
- structlog — more ergonomic but adds a dependency; stdlib `logging` with `extra={}` is sufficient

### 3. JSON log format via a custom `Formatter`, not a third-party library

**Decision:** Implement a `JsonFormatter(logging.Formatter)` that serializes `LogRecord` fields + `extra` dict into a single JSON line.

**Why:** No dependency on `python-json-logger` or `structlog`. The format is simple enough to own.

### 4. Instrumentation at the call sites in `run()` and `registry.execute()`, not via monkey-patching or decorators

**Decision:** Add `time.monotonic()` calls and `logger.info()` directly in `run()` (around `client.chat.completions.create`) and in `registry.execute()` (around `fn(**validated_args)`).

**Why:** Explicit and readable. Decorators would hide the instrumentation. The two call sites are well-defined and unlikely to multiply.

### 5. Result preview truncated to 200 characters

**Decision:** Log `str(result)[:200]` as `result_preview`.

**Why:** Tool results can be large (HTTP responses, file contents). Logging the full result would bloat log files and leak sensitive data. 200 chars gives enough context for debugging.

## Risks / Trade-offs

- **Log file path is hardcoded or env-configured** → For now, default to `agent.log` in CWD. Can be overridden via `AGENT_LOG_FILE` env var.
- **`extra={}` fields are not type-checked** → Typos in field names silently produce logs with missing fields. Mitigated by centralizing log calls in a thin `emit_*` helper module rather than scattering raw `logger.info` calls.
- **No log rotation** → Long-running sessions will grow `agent.log` unboundedly. Out of scope for now; user can configure `RotatingFileHandler` externally.
- **contextvars depth tracking requires discipline** → If `run()` is called without going through `delegate()`, depth will be 0 regardless. Acceptable — only `delegate` creates sub-agents.

## Open Questions

- Should `agent_name` be set explicitly by the caller or derived from the profile name? → Derive from profile; default to `"main"` for top-level runs.
- Should arguments be logged in full or also truncated? → Full for now (they tend to be small), truncated later if needed.
