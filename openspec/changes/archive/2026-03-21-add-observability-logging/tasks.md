## 1. Execution Context

- [x] 1.1 Create `src/agent/context.py` with `ContextVar` definitions: `run_id`, `parent_run_id`, `depth`, `agent_name`, `iteration`
- [x] 1.2 Add `set_run_context()` helper that sets all context vars for a new `run()` entry, deriving values from current context (for sub-agent nesting)
- [x] 1.3 Update `run()` to call `set_run_context()` at entry and update `iteration` var on each loop

## 2. Logging Infrastructure

- [x] 2.1 Create `src/agent/logging.py` with `JsonFormatter` that serializes log records to single-line JSON including all `extra` fields
- [x] 2.2 Add `ContextFilter` that injects current `contextvars` values into every log record (with safe defaults when outside `run()`)
- [x] 2.3 Add `configure_logging()` function that sets up the `agent` logger with stdout (human-readable) and file (JSON) handlers; reads `AGENT_LOG_FILE` env var

## 3. Run Instrumentation

- [x] 3.1 Instrument `run()` — wrap `client.chat.completions.create()` with `time.monotonic()` and emit `"llm_call"` log with model, duration_ms, and token counts from `response.usage`
- [x] 3.2 Handle missing `response.usage` gracefully (log token fields as `None`)

## 4. Registry Instrumentation

- [x] 4.1 Instrument `ToolsRegistry.execute()` — emit `"tool_call_start"` before `fn()` with tool name and args
- [x] 4.2 Emit `"tool_call_end"` after successful return with tool name, duration_ms, and `result_preview` (first 200 chars)
- [x] 4.3 Catch exceptions in `execute()`, emit `"tool_call_error"` at ERROR level with tool name, duration_ms, and error message, then re-raise

## 5. Sub-agent Context Propagation

- [x] 5.1 Update `delegate()` in `builtin_tools/delegate.py` to pass `agent_name` (from profile name) to `run()` so sub-agent context is set correctly

## 6. Wiring

- [x] 6.1 Call `configure_logging()` in the agent entry point / `__init__.py` so handlers are registered before any `run()` call

## 7. Tests

- [x] 7.1 Test `set_run_context()` — verify top-level sets depth=0, parent_run_id=None
- [x] 7.2 Test sub-agent context — verify child gets depth=1, parent_run_id=parent's run_id, and parent is unchanged
- [x] 7.3 Test `ContextFilter` — verify log records contain context fields; verify safe defaults outside `run()`
- [x] 7.4 Test `JsonFormatter` — verify output is valid JSON with expected fields
- [x] 7.5 Test `run()` instrumentation — verify `"llm_call"` log emitted with correct fields (mock client)
- [x] 7.6 Test `registry.execute()` instrumentation — verify start/end/error events emitted with correct fields
