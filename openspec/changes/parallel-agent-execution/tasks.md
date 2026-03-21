## 1. Dependencies & DB Setup

- [ ] 1.1 Add `aiosqlite` to `pyproject.toml` dependencies
- [ ] 1.2 Create `src/agent/db.py` with `open_db(path)` async context manager that opens an `aiosqlite` connection and enables WAL mode (`PRAGMA journal_mode=WAL`)
- [ ] 1.3 Create `agents` table DDL and auto-create-on-connect logic in `db.py`
- [ ] 1.4 Create `items` table DDL with foreign key constraint on `agent_id`

## 2. Agent Repository

- [ ] 2.1 Create `src/agent/repositories/agent_repo.py` with `AgentRecord` dataclass (id, status, parent_id, source_call_id, waiting_for, config, turn_count, result, error, created_at, updated_at)
- [ ] 2.2 Implement `AgentRepository.create(config)` — inserts record with `status="pending"`, UUID id
- [ ] 2.3 Implement `AgentRepository.get(agent_id)` — returns `AgentRecord | None`
- [ ] 2.4 Implement `AgentRepository.update(agent)` — persists all mutable fields, refreshes `updated_at`
- [ ] 2.5 Implement `AgentRepository.list_by_status(status)` — returns ordered list
- [ ] 2.6 Implement `AgentRepository.find_waiting_for(call_id)` — scans `waiting_for` JSON arrays

## 3. Item Repository

- [ ] 3.1 Create `src/agent/repositories/item_repo.py` with `ItemRecord` dataclass (id, agent_id, type, content, sequence, created_at)
- [ ] 3.2 Implement `ItemRepository.append(agent_id, type, content)` — inserts with auto-incremented sequence per agent
- [ ] 3.3 Implement `ItemRepository.list_for_agent(agent_id)` — returns items ordered by sequence
- [ ] 3.4 Implement `ItemRepository.get_output_by_call_id(call_id)` — finds `function_call_output` item by call_id in content JSON

## 4. Async Agent Loop

- [ ] 4.1 Rewrite `run()` in `src/agent/run.py` as `async def run(...)` using `AsyncOpenAI` client
- [ ] 4.2 Replace `client.chat.completions.create(...)` with `await client.chat.completions.create(...)`
- [ ] 4.3 For tool execution: `await tool_fn(...)` if coroutine, else call directly (use `asyncio.iscoroutinefunction`)
- [ ] 4.4 Keep `copy_context()` isolation for sub-agent ContextVars
- [ ] 4.5 Add `run_sync()` shim: `def run_sync(...): return asyncio.run(run(...))`
- [ ] 4.6 Update `client.py` to expose both `create_client()` (sync, for backwards compat) and `create_async_client()` returning `AsyncOpenAI`

## 5. Scheduler

- [ ] 5.1 Create `src/agent/scheduler.py` with `Scheduler` class holding `AgentRepository`, `ItemRepository`, and a `dict[str, asyncio.Event]` for pending results
- [ ] 5.2 Implement `Scheduler.start()` — launches background `asyncio.Task` running the poll loop
- [ ] 5.3 Implement poll loop: query `list_by_status("pending")`, call `create_task(_run_agent(agent))` for each, mark them `running`
- [ ] 5.4 Implement `Scheduler.deliver_result(call_id, result)` — finds waiting parent, stores output item, removes call_id from `waiting_for`, sets event if `waiting_for` is now empty
- [ ] 5.5 Implement startup recovery: on `Scheduler.start()`, scan for `waiting` agents whose entire `waiting_for` list has items in DB and auto-deliver them

## 6. Parallel Delegate

- [ ] 6.1 Create `src/agent/builtin_tools/parallel_delegate.py` with `delegate_async(profile, task, image_url, call_id, scheduler)` — inserts child agent record, registers `asyncio.Event`, returns `agent_id`
- [ ] 6.2 Implement `delegate_all(tasks, scheduler)` — calls `delegate_async` for each, then `await asyncio.gather(...)` on all events, returns ordered results
- [ ] 6.3 Rewrite `delegate()` in `src/agent/builtin_tools/delegate.py` to call `delegate_async()` then `await` its event and return the result string
- [ ] 6.4 Wire `scheduler` into `delegate` tool execution — pass scheduler via a `ContextVar` or inject into the tool's closure at registration time

## 7. Integration & Wiring

- [ ] 7.1 Update `src/agent/__init__.py` to initialize DB, repositories, and scheduler on library import (or lazily on first `run()` call)
- [ ] 7.2 Pass `AsyncOpenAI` client into `run()` by default; keep `create_client()` for `run_sync()` path
- [ ] 7.3 Update `ContextVar` setup in `context.py` to include `agent_id` (current agent's DB id)
- [ ] 7.4 Ensure `copy_context()` in `run()` still isolates ContextVars between parent and child agents

## 8. Tests

- [ ] 8.1 Add `pytest-asyncio` to dev dependencies and configure `asyncio_mode = "auto"` in `pyproject.toml`
- [ ] 8.2 Write async tests for `AgentRepository` (create, get, update, list_by_status, find_waiting_for)
- [ ] 8.3 Write async tests for `ItemRepository` (append, list_for_agent, isolation, get_output_by_call_id)
- [ ] 8.4 Write async test: two `run()` coroutines via `asyncio.gather()` complete independently
- [ ] 8.5 Write async test: `delegate_all` with two profiles returns ordered results
- [ ] 8.6 Write test: `run_sync()` works from synchronous context and returns expected string
