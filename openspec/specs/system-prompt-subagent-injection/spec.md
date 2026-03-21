### Requirement: format_subagents_section renders available sub-agents as Markdown

The `agent.profile` module SHALL expose a `format_subagents_section(registry: AgentProfileRegistry) -> str` function that returns a Markdown string listing all profiles from the registry.

The returned string SHALL:

- Begin with a heading `## Available Sub-agents`
- List each profile as `- **<name>**: <description>` in alphabetical order by name
- Return only the heading and an empty list note when the registry contains no profiles

#### Scenario: Non-empty registry produces formatted section

- **WHEN** `format_subagents_section` is called with a registry containing at least one profile
- **THEN** the returned string contains `## Available Sub-agents` and each profile's name and description in `- **name**: description` format

#### Scenario: Empty registry produces section with empty note

- **WHEN** `format_subagents_section` is called with a registry containing no profiles
- **THEN** the returned string contains `## Available Sub-agents` and a note indicating no sub-agents are available

#### Scenario: Profiles are listed in alphabetical order

- **WHEN** the registry contains profiles `"zap"` and `"alpha"`
- **THEN** the returned string lists `alpha` before `zap`

### Requirement: build_system_prompt appends the sub-agents section to a base prompt

The `agent.profile` module SHALL expose a `build_system_prompt(base_prompt: str, registry: AgentProfileRegistry) -> str` function that returns the base prompt with the sub-agents section appended.

The returned string SHALL be `<base_prompt>\n\n<format_subagents_section(registry)>` where leading/trailing whitespace on each part is preserved.

#### Scenario: Base prompt is extended with sub-agents section

- **WHEN** `build_system_prompt("You are a helpful assistant.", registry)` is called with a registry containing one profile named `researcher`
- **THEN** the returned string starts with `"You are a helpful assistant."` and ends with the `## Available Sub-agents` section including `researcher`

#### Scenario: Empty base prompt produces only the sub-agents section

- **WHEN** `build_system_prompt("", registry)` is called
- **THEN** the returned string contains the `## Available Sub-agents` section
