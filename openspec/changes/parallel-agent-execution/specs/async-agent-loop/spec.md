## ADDED Requirements

### Requirement: run() is an async coroutine

`run()` SHALL be redefined as `async def run(...)` accepting the same parameters as before (`Conversation`, `AsyncOpenAI`-compatible client, `model`, `ToolsRegistry`, optional `tools`, optional `sandbox`, optional `max_iterations`).

All LLM API calls inside `run()` SHALL use `await` so they do not block the event loop.

All tool executions that are themselves coroutines SHALL be `await`-ed; synchronous tools SHALL be called directly.

#### Scenario: run() can be awaited

- **WHEN** `await run(conv, client, model, registry)` is called inside an async context
- **THEN** it completes and returns the final assistant text as a `str`

#### Scenario: run() does not block the event loop during LLM calls

- **WHEN** two `run()` coroutines are scheduled concurrently via `asyncio.gather()`
- **THEN** both make progress interleaved (neither blocks while the other awaits its LLM response)

### Requirement: run_sync() provides a synchronous entry point

The library SHALL expose `run_sync()` as a backwards-compatible synchronous wrapper that calls `asyncio.run(run(...))`.

`run_sync()` SHALL accept identical parameters to `run()` and return the same `str` result.

#### Scenario: run_sync() works in a synchronous context

- **WHEN** `run_sync(conv, client, model, registry)` is called from non-async code
- **THEN** it returns the final assistant text as a `str` without requiring the caller to manage an event loop
