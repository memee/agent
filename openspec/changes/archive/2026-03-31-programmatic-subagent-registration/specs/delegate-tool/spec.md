## MODIFIED Requirements

### Requirement: delegate tool schema reflects loaded profiles dynamically

The `delegate` tool schema SHALL reflect the current contents of `AgentProfileRegistry`, including profiles that are programmatically registered after module import.

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

#### Scenario: profile enum updates after programmatic registration

- **WHEN** a new profile `planner` is programmatically registered in `AgentProfileRegistry` after `delegate` has already been imported
- **THEN** the next inspection of the `delegate` tool schema includes `planner` in the `profile` enum
