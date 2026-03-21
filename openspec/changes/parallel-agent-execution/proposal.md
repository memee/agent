## Why

The current agent executes sub-agents sequentially — `delegate` blocks until the sub-agent completes, making it impossible to run independent agents in parallel. This forces a serial execution model even when tasks are independent, and prevents coordination patterns like fan-out (spawn N researchers, collect all results) that are natural for multi-agent workflows.

## What Changes

- **NEW** SQLite persistence layer: agent state and conversation history stored in DB, enabling resumable and cross-process agents
- **NEW** Async `run()` loop: rewrites the agent loop as `async def`, allowing concurrent execution via `asyncio`
- **NEW** Non-blocking `delegate`: returns an `agent_id` immediately instead of blocking; orchestrator continues or waits for multiple agents at once
- **NEW** `waiting` agent state: when orchestrator delegates, it records `waiting_for` call IDs and suspends the loop
- **NEW** `deliver_result()`: when a child agent completes, delivers its result to the parent and resumes the parent's loop
- **NEW** Scheduler: manages the pool of running agents, starts tasks, and wakes waiting agents when their dependencies resolve
- **BREAKING** `run()` signature changes to `async def` — callers must `await` it or use `asyncio.run()`
- **BREAKING** `delegate` tool result changes from `str` (final answer) to `str` (agent_id) until result is delivered

## Capabilities

### New Capabilities

- `agent-repository`: SQLite-backed storage for agent state (`id`, `status`, `waiting_for`, `config`, `turn_count`)
- `item-repository`: SQLite-backed storage for conversation items per agent (messages, tool calls, tool outputs)
- `async-agent-loop`: async version of `run()` that drives the tool-call cycle without blocking the event loop
- `agent-scheduler`: orchestrates a pool of agents, starts coroutines, delivers results, resumes waiting agents
- `parallel-delegate`: non-blocking variant of delegate that spawns a child agent and returns its ID

### Modified Capabilities

- `agent-loop`: `run()` becomes `async def`; adds `waiting` exit condition alongside `no tool_calls` and `max_iterations`
- `delegate-tool`: returns `agent_id` immediately; result delivered asynchronously via `deliver_result()`

## Impact

- `src/agent/run.py` — full rewrite to async
- `src/agent/builtin_tools/delegate.py` — non-blocking spawn, returns agent_id
- `src/agent/conversation.py` — may be replaced by item-repository for persistence
- New: `src/agent/db.py`, `src/agent/repositories/`, `src/agent/scheduler.py`
- Dependency: `aiosqlite` or `sqlalchemy[asyncio]`
- Python minimum: 3.11+ (asyncio task groups)
