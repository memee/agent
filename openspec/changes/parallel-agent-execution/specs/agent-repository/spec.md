## ADDED Requirements

### Requirement: AgentRepository persists agent state in SQLite

The library SHALL provide an `AgentRepository` class backed by SQLite that stores and retrieves agent records.

Each agent record SHALL contain: `id` (UUID string), `status` (one of `pending | running | waiting | completed | failed`), `parent_id` (optional agent ID), `source_call_id` (optional tool call ID that spawned this agent), `waiting_for` (JSON array of call IDs, default empty), `config` (JSON with `profile`, `model`, `task`), `turn_count` (integer, default 0), `result` (optional string), `error` (optional string), `created_at` (float timestamp), `updated_at` (float timestamp).

`AgentRepository` SHALL be initialized with an `aiosqlite` connection and SHALL create the `agents` table on first use if it does not exist.

#### Scenario: Create agent record

- **WHEN** `await repo.create(config)` is called with a config dict
- **THEN** a new agent record is inserted with `status="pending"`, a generated UUID `id`, and the config stored as JSON

#### Scenario: Get agent by ID

- **WHEN** `await repo.get(agent_id)` is called with a known ID
- **THEN** the agent record is returned as a dataclass instance with all fields populated

#### Scenario: Get unknown agent returns None

- **WHEN** `await repo.get("nonexistent-id")` is called
- **THEN** `None` is returned

#### Scenario: Update agent status

- **WHEN** `await repo.update(agent)` is called with a modified agent instance
- **THEN** all mutable fields are persisted and `updated_at` is refreshed

#### Scenario: List pending agents

- **WHEN** `await repo.list_by_status("pending")` is called
- **THEN** all agents with `status="pending"` are returned in insertion order

#### Scenario: Find waiting agent by call_id

- **WHEN** `await repo.find_waiting_for(call_id)` is called
- **THEN** the agent whose `waiting_for` JSON array contains `call_id` is returned, or `None` if none found
