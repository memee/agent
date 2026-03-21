## ADDED Requirements

### Requirement: Scheduler starts pending agents from the DB

The library SHALL provide a `Scheduler` class that runs as an `asyncio` background task. It SHALL poll `AgentRepository` for agents with `status="pending"` and start each one as an `asyncio.Task` via `create_task()`, updating their status to `"running"` before starting.

The scheduler SHALL prevent double-starting: once an agent's task is created, it SHALL NOT be picked up again on the next poll cycle.

#### Scenario: Scheduler starts a pending agent

- **WHEN** an agent with `status="pending"` exists in the DB and the scheduler polls
- **THEN** the scheduler creates an asyncio task running that agent's `run()` coroutine and updates its status to `"running"`

#### Scenario: Scheduler does not re-start a running agent

- **WHEN** an agent with `status="running"` exists in the DB
- **THEN** the scheduler does not create a second task for it

### Requirement: Scheduler delivers results to waiting parents

The library SHALL provide `deliver_result(call_id, result, agent_repo, events)` that:

1. Finds the agent waiting for `call_id` via `AgentRepository.find_waiting_for(call_id)`
2. Removes `call_id` from that agent's `waiting_for` list
3. Stores the result as a `function_call_output` item
4. If `waiting_for` is now empty, sets an `asyncio.Event` to resume the parent's loop

#### Scenario: deliver_result resumes a waiting parent

- **WHEN** `deliver_result(call_id, "result text")` is called and a parent agent is waiting for that call_id
- **THEN** the call_id is removed from `waiting_for`, the result is stored, and the parent's loop resumes

#### Scenario: deliver_result with multiple pending calls

- **WHEN** a parent is waiting for two call_ids and only one is delivered
- **THEN** the parent remains in `waiting` status until the second result is also delivered

### Requirement: Scheduler recovers orphaned waiting agents on startup

On initialization, the `Scheduler` SHALL scan for agents with `status="waiting"` whose entire `waiting_for` list has corresponding `function_call_output` items already in the DB, and SHALL auto-deliver those results to resume them.

#### Scenario: Recovery after process restart

- **WHEN** the process restarts and an agent in `waiting` status has all its pending results already stored in the items table
- **THEN** the scheduler resumes that agent without requiring external re-delivery
