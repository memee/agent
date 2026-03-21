## 1. Implementation

- [x] 1.1 Add `format_subagents_section(registry: AgentProfileRegistry) -> str` to `agent/profile.py`
- [x] 1.2 Add `build_system_prompt(base_prompt: str, registry: AgentProfileRegistry) -> str` to `agent/profile.py`
- [x] 1.3 Simplify `_build_delegate_schema()` in `agent/builtin_tools/delegate.py`: remove sub-agent prose descriptions from the tool description and `profile` parameter description; keep the `profile` enum

## 2. Tests

- [x] 2.1 Test `format_subagents_section` with a registry containing one or more profiles (checks heading, name/description format, alphabetical order)
- [x] 2.2 Test `format_subagents_section` with an empty registry (checks heading + empty note)
- [x] 2.3 Test `build_system_prompt` appends section to a non-empty base prompt
- [x] 2.4 Test `build_system_prompt` with an empty base prompt
- [x] 2.5 Test `delegate` tool schema: `profile` enum contains all profile names, descriptions do not list sub-agent details
