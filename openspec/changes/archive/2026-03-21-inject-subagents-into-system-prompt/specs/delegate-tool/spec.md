## MODIFIED Requirements

### Requirement: delegate tool schema reflects loaded profiles dynamically

The `delegate` tool schema SHALL be generated at import time from the loaded `AgentProfileRegistry`.

The `profile` parameter SHALL be typed as an enum of profile names. The tool description and `profile` parameter description SHALL NOT enumerate sub-agent names or one-line descriptions — that information is surfaced in the main agent's system prompt instead.

#### Scenario: profile enum contains all loaded profiles

- **WHEN** the tool schema for `delegate` is inspected
- **THEN** the `profile` parameter's `enum` array contains exactly the names of all profiles in `AgentProfileRegistry`

#### Scenario: delegate available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"delegate"` appears in `tools.names("builtin")`

#### Scenario: tool and parameter descriptions do not list sub-agent details

- **WHEN** the tool schema for `delegate` is inspected
- **THEN** neither the top-level `description` nor the `profile` parameter `description` contains a formatted list of sub-agent names and descriptions
