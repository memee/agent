## ADDED Requirements

### Requirement: Execution context carried via contextvars

The system SHALL maintain an execution context using `contextvars.ContextVar` instances that are automatically propagated to all code running within a `run()` call, including sub-agents.

The context SHALL contain:

- `run_id` (str): UUID generated at `run()` entry for this agent instance
- `parent_run_id` (str | None): `run_id` of the parent agent, or None for top-level runs
- `depth` (int): nesting level — 0 for top-level, incremented by 1 for each sub-agent
- `agent_name` (str): name of the agent — derived from profile name, defaults to `"main"`
- `iteration` (int): current loop iteration within `run()`, starting at 1

#### Scenario: Top-level run sets context

- **WHEN** `run()` is called at the top level (no parent context)
- **THEN** `run_id` is set to a new UUID, `parent_run_id` is None, `depth` is 0, `agent_name` is `"main"`, `iteration` starts at 1

#### Scenario: Sub-agent inherits and extends context

- **WHEN** `delegate()` spawns a sub-agent via `run()`
- **THEN** sub-agent sets its own `run_id`, sets `parent_run_id` to the parent's `run_id`, increments `depth` by 1, sets `agent_name` from the profile name

#### Scenario: Child context does not affect parent

- **WHEN** a sub-agent modifies its context variables
- **THEN** the parent's context variables remain unchanged after the sub-agent returns

#### Scenario: Iteration counter updates each loop

- **WHEN** `run()` enters each iteration of the tool-call loop
- **THEN** `iteration` is updated to reflect the current iteration number
