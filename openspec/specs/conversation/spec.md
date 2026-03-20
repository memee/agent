## ADDED Requirements

### Requirement: Conversation holds message history

`Conversation` SHALL store messages as `list[dict]` in OpenAI message format.
It SHALL expose typed methods for appending each role:
`add_system`, `add_user`, `add_assistant`, `add_tool_result`.
It SHALL expose a `messages` property returning the raw list for passing to
the OpenAI API.

#### Scenario: Add messages of each role

- **WHEN** `add_system`, `add_user`, `add_assistant`, and `add_tool_result`
  are called in sequence
- **THEN** `messages` returns a list with dicts containing the correct `role`
  and `content` (or `tool_call_id` for tool results) for each entry

#### Scenario: Empty conversation

- **WHEN** a new `Conversation` is created with no arguments
- **THEN** `messages` returns an empty list

### Requirement: Conversation initialised with system prompt

`Conversation` SHALL accept an optional `system_prompt: str` in `__init__`.
When provided, it SHALL prepend a system message automatically.

#### Scenario: System prompt in constructor

- **WHEN** `Conversation(system_prompt="You are helpful.")` is created
- **THEN** `messages[0]` equals `{"role": "system", "content": "You are helpful."}`
