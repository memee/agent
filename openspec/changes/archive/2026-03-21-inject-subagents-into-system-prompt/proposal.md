## Why

The main agent's system prompt currently contains no information about available sub-agents — this information only appears in the `delegate` tool's schema, which the LLM sees as structured metadata rather than planning context. By surfacing sub-agent names and descriptions directly in the system prompt, the orchestrator LLM can reason about delegation opportunities earlier and more effectively when planning multi-step tasks.

## What Changes

- Add a `format_subagents_section(registry)` utility function to `agent.profile` that renders sub-agent info as a Markdown section
- Expose a convenience helper (e.g. `build_system_prompt(base_prompt, registry)`) that appends the sub-agent section to any given system prompt string
- The injection is opt-in: callers pass their base system prompt through the helper before constructing `Conversation`; no existing behavior changes by default
- Remove sub-agent descriptions from the `delegate` tool schema — the `profile` parameter keeps its enum (for validation) but drops the prose descriptions that now live in the system prompt

## Capabilities

### New Capabilities

- `system-prompt-subagent-injection`: Utility that appends a formatted list of available sub-agents (name + description) to a main agent system prompt string, sourced from the `AgentProfileRegistry`

### Modified Capabilities

- `delegate-tool`: The `profile` parameter description and tool-level description no longer enumerate sub-agent names/descriptions (removed to avoid duplication with the system prompt)

## Impact

- `agent/profile.py` — new public functions added, no existing API changes
- `agent/builtin_tools/delegate.py` — `_build_delegate_schema()` simplified: profile enum kept, descriptions removed
- Callers that build the main agent's `Conversation` can opt in to enriched system prompts
