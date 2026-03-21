## ADDED Requirements

### Requirement: delegate_async spawns a non-blocking sub-agent

The library SHALL provide `delegate_async(profile, task, image_url)` that inserts a child agent record in `AgentRepository` with `status="pending"`, registers an `asyncio.Event` keyed by the new agent's ID, and returns the `agent_id` string immediately without waiting for the child to complete.

The spawned child agent SHALL inherit `parent_id` pointing to the current agent and SHALL set `source_call_id` to the tool call ID that triggered the delegation.

#### Scenario: delegate_async returns immediately

- **WHEN** `agent_id = await delegate_async("researcher", "find X")` is called
- **THEN** it returns a string agent_id without waiting for the researcher to finish

#### Scenario: Spawned agent appears in DB as pending

- **WHEN** `delegate_async` returns
- **THEN** an agent record with `status="pending"` and the correct `parent_id` exists in the DB

### Requirement: delegate supports fan-out via delegate_all

The library SHALL provide `delegate_all(tasks)` where `tasks` is a list of `(profile, task)` tuples. It SHALL spawn all agents via `delegate_async` and then `await asyncio.gather()` on all their completion events, returning a list of result strings in the same order as the input.

#### Scenario: Fan-out executes agents concurrently

- **WHEN** `results = await delegate_all([("researcher", "find A"), ("researcher", "find B")])` is called
- **THEN** both sub-agents run concurrently and both results are returned as a list once all complete

#### Scenario: Fan-out preserves order

- **WHEN** `delegate_all` is called with tasks `[("a", "task1"), ("b", "task2")]`
- **THEN** the returned list index 0 contains the result from "a/task1" and index 1 contains "b/task2" regardless of completion order

### Requirement: delegate (blocking) delegates to delegate_async internally

The existing `delegate` tool SHALL be reimplemented as a wrapper: it calls `delegate_async`, then immediately `await`s the completion event for that single agent, and returns the result string.

This preserves the existing behaviour for orchestrators that delegate one task at a time, while reusing the async machinery.

#### Scenario: Single delegate still returns result string

- **WHEN** an orchestrator's tool loop executes `delegate(profile="researcher", task="find X")`
- **THEN** the tool result returned to the LLM is the researcher's final text response, same as before
