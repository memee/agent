## Context

The agent is currently a synchronous Python library. The entry point `run()` drives a blocking tool-call loop. Sub-agents are spawned by `delegate()`, which calls `run()` recursively and waits for the result before returning. There is no persistence — all state lives in `Conversation` (a list of dicts in memory).

This design introduces async execution and SQLite persistence as the foundation for parallel sub-agent execution. The key insight from the reference implementation (01_05_agent TypeScript) is that parallel execution requires three things working together: (1) async loop so agents don't block each other, (2) persistent state so agents can be "paused" and "resumed", and (3) a scheduler that connects child completion to parent resumption.

## Goals / Non-Goals

**Goals:**

- Enable `asyncio.gather()` style fan-out: orchestrator spawns N sub-agents and waits for all results
- Persist agent state (status, conversation history) in SQLite so agents survive process restarts
- Keep the public API change minimal — callers change `run()` to `await run()` or `asyncio.run(run(...))`
- Preserve existing tool registration and sandbox system unchanged

**Non-Goals:**

- HTTP server or REST API (this stays a library)
- Cross-process or distributed scheduling (single process, single event loop)
- Cancellation / timeout of individual sub-agents (future change)
- Context pruning / summarization (separate change)

## Decisions

### Decision 1: asyncio over threading

**Choice**: `asyncio` with `async def run()`.

**Rationale**: The bottleneck is LLM API calls (I/O bound). `asyncio` gives cooperative concurrency with no GIL contention, clean structured concurrency via `asyncio.TaskGroup` (Python 3.11+), and the `openai` Python SDK already supports async via `AsyncOpenAI`.

**Alternatives considered**:

- `ThreadPoolExecutor`: Works but adds lock complexity for shared state; GIL still limits CPU-bound parts; harder to cancel.
- Subprocess per agent: True isolation but prohibitive overhead per agent and complex IPC.

### Decision 2: SQLite with aiosqlite

**Choice**: `aiosqlite` wrapping SQLite. Schema: two tables — `agents` and `items`.

**Rationale**: SQLite is zero-infrastructure, file-based, and sufficient for single-process use. `aiosqlite` provides async-compatible access without blocking the event loop. The `items` table replaces the in-memory `Conversation` list, making history persistent and queryable.

**Schema**:

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,          -- pending | running | waiting | completed | failed
    parent_id TEXT,
    source_call_id TEXT,           -- tool_call.id that spawned this agent
    waiting_for TEXT,              -- JSON array of call_ids
    config TEXT NOT NULL,          -- JSON: {profile, model, task}
    turn_count INTEGER DEFAULT 0,
    result TEXT,
    error TEXT,
    created_at REAL,
    updated_at REAL
);

CREATE TABLE items (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    type TEXT NOT NULL,            -- message | function_call | function_call_output
    content TEXT NOT NULL,         -- JSON
    sequence INTEGER NOT NULL,
    created_at REAL,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
```

**Alternatives considered**:

- Keep in-memory `Conversation`: doesn't support resumption; can't share state between coroutines safely.
- `sqlalchemy[asyncio]`: More overhead; SQLite direct is simpler for this use case.

### Decision 3: Non-blocking delegate with waiting loop

**Choice**: `delegate()` inserts a child agent record, creates an `asyncio.Event` keyed by `call_id`, then `await`s the event. The scheduler delivers results by setting the event.

**Rationale**: This keeps the agent loop code clean — the loop still runs linearly from the agent's perspective. The scheduler handles the fan-out/fan-in. An `asyncio.Event` per pending call is lightweight and avoids polling.

**Flow**:

```
orchestrator loop
  └─ tool_call: delegate(profile="researcher", task="...")
       └─ delegate():
            1. INSERT agent (status=pending, parent_id=current, source_call_id=call_id)
            2. Create Event: _pending_results[call_id] = asyncio.Event()
            3. Scheduler picks up pending agent → starts run() coroutine
            4. await _pending_results[call_id].wait()  ← orchestrator suspends here
            5. Child completes → deliver_result(call_id, result)
            6. Event is set → orchestrator resumes
            7. Return result string to tool loop
```

For **parallel delegation** (fan-out), orchestrator calls `delegate_all([...])` which fires all spawns then `await asyncio.gather(...)` on all events.

**Alternatives considered**:

- DB polling loop: `while agent.status != 'completed': await asyncio.sleep(0.1)` — works but wasteful and adds latency.
- Queue (asyncio.Queue): Adds indirection; Event is simpler for one-shot delivery.

### Decision 4: Scheduler as an asyncio background task

**Choice**: A `Scheduler` class runs as an `asyncio` background task. It watches for `pending` agents in DB and starts their `run()` coroutines via `asyncio.create_task()`.

**Rationale**: Decouples agent spawning from execution. `delegate()` just inserts to DB; the scheduler is responsible for lifecycle. This also makes it easy to add concurrency limits later (e.g., max 5 agents at once).

```python
class Scheduler:
    async def run(self):
        while True:
            pending = await self.repo.list_pending()
            for agent in pending:
                asyncio.create_task(self._run_agent(agent))
                await self.repo.set_status(agent.id, "running")
            await asyncio.sleep(0.05)  # 50ms poll
```

### Decision 5: Keep Conversation as a view over items

**Choice**: `Conversation` becomes a thin wrapper that reads/writes `items` rows instead of a list. The OpenAI message format is reconstructed from items on demand.

**Rationale**: Preserves the existing `run()` interface (`Conversation` passed in, appended to). Callers don't need to know about items.

## Risks / Trade-offs

- **asyncio.Event per call_id lives in process memory** → if process crashes between delegate() and deliver_result(), the event is lost. Mitigation: on startup, scheduler checks for `waiting` agents with all `waiting_for` calls already `completed` in DB and auto-delivers.
- **SQLite write contention** → many concurrent agents writing items. Mitigation: enable WAL mode (`PRAGMA journal_mode=WAL`); SQLite handles concurrent readers + single writer fine at this scale.
- **Breaking change to `run()`** → all existing callers need `await`. Mitigation: provide `run_sync()` shim using `asyncio.run()` for scripts.
- **50ms scheduler poll latency** → sub-agents start up to 50ms after `delegate()` call. Acceptable for LLM workflows where each turn is 500ms–5s.

## Migration Plan

1. Add `aiosqlite` to `pyproject.toml`
2. Create DB schema + migration on first `run()` call (auto-create tables if not exist)
3. Add `run_sync()` as backwards-compat shim
4. Update `delegate` tool — old behavior (blocking) preserved via `run_sync()` for non-async callers
5. Existing tests: wrap `run()` calls with `asyncio.run()` or use `pytest-asyncio`

## Open Questions

- Should `agent_id` be UUID or a shorter ID? (current code uses no agent IDs)
- Should the DB path be configurable via env var (`AGENT_DB_PATH`) or always `agent.db` in cwd?
- Should `waiting` state be exposed in the return value of `run()` or always resolved before returning to the top-level caller?
