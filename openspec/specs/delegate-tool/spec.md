## ADDED Requirements

### Requirement: delegate tool runs a sub-agent

The library SHALL register a `delegate` tool in the `"builtin"` group.
It SHALL accept: `system_prompt: str`, `task: str`, `group: str` (tool group
for the sub-agent), and `model: str`.

It SHALL create a fresh `Conversation` with the given `system_prompt`, add
`task` as the first user message, and call `run()` with the scoped tool list
(`registry.to_openai_schema(group)`).

It SHALL return the sub-agent's final text response as a string, which becomes
the tool result visible to the orchestrator.

#### Scenario: Orchestrator delegates a task

- **WHEN** an orchestrator's `run()` loop executes a `delegate` tool call with
  a system prompt, task, and group
- **THEN** a nested `run()` is invoked, the sub-agent completes the task, and
  its final text is returned as the tool result to the orchestrator

#### Scenario: Sub-agent uses only its scoped tools

- **WHEN** `delegate` is called with `group="research"`
- **THEN** the nested `run()` receives only tools registered under the
  `"research"` group, not the full registry

### Requirement: delegate is auto-registered on import

`delegate` SHALL be registered automatically when `from agent import tools`
is executed, consistent with other built-in tools.

#### Scenario: delegate available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"delegate"` appears in `tools.names("builtin")`
