## Why

The `delegate` tool requires the orchestrator LLM to construct sub-agent configuration inline (system prompt, tool group, model) on every call, making sub-agents ad-hoc, non-reusable, and hard to control. A profile system lets developers define named sub-agents declaratively, and lets the orchestrator LLM select them by name from a well-typed enum rather than hallucinating configuration.

## What Changes

- New `subagents/` directory inside the library (`src/agent/subagents/*.md`) holds built-in sub-agent profile files
- Each profile is a Markdown file: YAML frontmatter (name, description, model, tools, sandbox) + body = system prompt
- Sandbox config in frontmatter supports `preset` (`default` / `strict` / `off`) plus field-level overrides applied on top
- A new `AgentProfile` loader reads and parses all profile files at import time
- The `delegate` tool signature changes: `profile` (enum of loaded profile names) + `task` replace the current `system_prompt`, `group`, `model` params — **BREAKING**
- `delegate` tool schema is generated dynamically so the `profile` enum and per-profile descriptions are always in sync with the files on disk
- At least one built-in profile (`researcher`) ships with the library

## Capabilities

### New Capabilities

- `subagent-profile`: Declarative sub-agent profile files with YAML frontmatter (name, description, model, tools, sandbox preset + overrides) and Markdown system prompt body
- `profile-loader`: Library component that discovers, parses, and exposes `AgentProfile` objects from `subagents/*.md` at import time
- `sandbox-from-profile`: Mapping from profile frontmatter sandbox config (preset + overrides) to a `SandboxConfig` instance

### Modified Capabilities

- `delegate-tool`: Signature changes from `(system_prompt, task, group, model)` to `(profile, task)` where `profile` is a dynamic enum; tool schema is generated from loaded profiles

## Impact

- `src/agent/builtin_tools/delegate.py` — rewritten
- `src/agent/subagents/` — new directory with profile files
- New module `src/agent/profile.py` (or similar) for `AgentProfile` and loader
- `src/agent/sandbox.py` — may need a factory function to build `SandboxConfig` from frontmatter dict
- Existing code that calls `delegate` with old signature will break (breaking change)
- Tests for `delegate` need updating
