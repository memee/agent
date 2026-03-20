## MODIFIED Requirements

### Requirement: delegate tool runs a sub-agent

The library SHALL register a `delegate` tool in the `"builtin"` group.
It SHALL accept: `profile: str` (name of a loaded `AgentProfile`) and `task: str`.

It SHALL look up the named profile from `AgentProfileRegistry`, build a `SandboxConfig`
from the profile's sandbox config, create a fresh `Conversation` with the profile's
system prompt, add `task` as the first user message, and call `run()` with the
tool list filtered to the profile's `tools` list and the profile's `model`.

It SHALL return the sub-agent's final text response as a string, which becomes
the tool result visible to the orchestrator.

#### Scenario: Orchestrator delegates a task using a named profile

- **WHEN** an orchestrator's `run()` loop executes a `delegate` tool call with `profile="researcher"` and a task string
- **THEN** a nested `run()` is invoked using the researcher profile's system prompt, model, and tool list, and its final text is returned as the tool result to the orchestrator

#### Scenario: Sub-agent uses only tools listed in the profile

- **WHEN** `delegate` is called with `profile="researcher"` and the researcher profile lists `["http_get", "read_file"]`
- **THEN** the nested `run()` receives only those two tools, not the full registry

#### Scenario: Unknown profile name raises an error

- **WHEN** `delegate` is called with a `profile` name that does not exist in `AgentProfileRegistry`
- **THEN** a `KeyError` is raised with the unknown profile name

### Requirement: delegate tool schema reflects loaded profiles dynamically

The `delegate` tool schema SHALL be generated at import time from the loaded `AgentProfileRegistry`.

The `profile` parameter SHALL be typed as an enum of profile names, with a combined `description` listing each profile name and its one-line description so the orchestrator LLM can select the right one.

#### Scenario: profile enum contains all loaded profiles

- **WHEN** the tool schema for `delegate` is inspected
- **THEN** the `profile` parameter's `enum` array contains exactly the names of all profiles in `AgentProfileRegistry`

#### Scenario: delegate available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"delegate"` appears in `tools.names("builtin")`
