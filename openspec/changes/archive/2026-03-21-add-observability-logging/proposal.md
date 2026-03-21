## Why

The agent has no visibility into its own execution — tool calls, LLM calls, token usage, and timings are invisible. This makes debugging multi-step agent runs and sub-agent hierarchies difficult and wastes money (no token tracking).

## What Changes

- Add structured logging using Python `logging` + `contextvars` as the foundation
- Instrument `run()` to log each LLM call with model, duration, and token usage
- Instrument `ToolsRegistry.execute()` to log each tool call with name, arguments, duration, and result preview
- Add execution context (run_id, parent_run_id, depth, agent_name, iteration) propagated automatically via `contextvars`
- Configure two log handlers out of the box: stdout (human-readable) and file (structured JSON)
- Sub-agents spawned via `delegate` inherit context and extend it (depth, parent_run_id)

## Capabilities

### New Capabilities

- `agent-context`: Execution context carried via `contextvars` — run_id, parent_run_id, depth, agent_name, iteration. Set at `run()` entry, inherited by sub-agents, available to all log records.
- `agent-logging`: Logging infrastructure — log record format, handler configuration (stdout + JSON file), and log levels for agent events.
- `run-instrumentation`: Instrumentation of `run()` and `ToolsRegistry.execute()` — captures LLM call metrics (tokens, duration) and tool call metrics (name, args, duration, result preview).

### Modified Capabilities

- `agent-loop`: The run loop gains instrumentation hooks (LLM call timing, token capture, tool call timing). No requirement changes — internal implementation only.
- `llm-client`: No requirement changes.

## Impact

- `src/agent/run.py` — instrumented with timing and token capture
- `src/agent/registry.py` — instrumented with timing around `execute()`
- `src/agent/builtin_tools/delegate.py` — sets child context (depth, parent_run_id)
- New module: `src/agent/context.py` — `contextvars` definitions
- New module: `src/agent/logging.py` — handler setup and log record format
- No new dependencies (stdlib only: `logging`, `contextvars`, `json`, `time`)
