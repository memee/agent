## ADDED Requirements

### Requirement: ItemRepository persists conversation items in SQLite

The library SHALL provide an `ItemRepository` class backed by SQLite that stores and retrieves conversation items for an agent.

Each item record SHALL contain: `id` (UUID string), `agent_id` (foreign key to agents), `type` (one of `message | function_call | function_call_output`), `content` (JSON), `sequence` (integer, auto-incremented per agent), `created_at` (float timestamp).

`ItemRepository` SHALL be initialized with an `aiosqlite` connection and SHALL create the `items` table on first use if it does not exist with a foreign key constraint to `agents`.

#### Scenario: Append item for agent

- **WHEN** `await repo.append(agent_id, type, content)` is called
- **THEN** a new item is inserted with an auto-incremented `sequence` number relative to that agent

#### Scenario: List items for agent in order

- **WHEN** `await repo.list_for_agent(agent_id)` is called
- **THEN** all items for that agent are returned ordered by `sequence` ascending

#### Scenario: Items from different agents are isolated

- **WHEN** `await repo.list_for_agent(agent_a_id)` is called when agent B also has items
- **THEN** only items belonging to agent A are returned

#### Scenario: Get item by call_id

- **WHEN** `await repo.get_output_by_call_id(call_id)` is called
- **THEN** the `function_call_output` item whose content contains that `call_id` is returned, or `None` if not found
