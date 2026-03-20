## Context

The agent library has a working `delegate` tool that spawns sub-agents inline — the orchestrator LLM must pass `system_prompt`, `group`, `model`, and `task` on every call. This works for ad-hoc delegation but prevents reuse, makes orchestrator prompts verbose, and lets LLMs hallucinate configuration. The goal is to replace inline config with named, declarative profiles bundled inside the library.

Current call shape:

```python
delegate(system_prompt="...", task="...", group="research", model="gpt-4o-mini")
```

Target call shape:

```python
delegate(profile="researcher", task="...")
```

## Goals / Non-Goals

**Goals:**

- Define sub-agent profiles as `src/agent/subagents/*.md` files (YAML frontmatter + Markdown body)
- Load profiles at import time into `AgentProfile` dataclass objects
- Expose sandbox config via `preset + field overrides` pattern in frontmatter
- Regenerate `delegate` tool schema dynamically so `profile` enum reflects loaded profiles
- Ship one built-in profile: `researcher`
- Keep `SandboxConfig` construction logic self-contained in `sandbox.py`

**Non-Goals:**

- Runtime profile hot-reload (profiles load once at import)
- User-supplied profile directories (only library-bundled profiles for now)
- Profile inheritance or composition
- Changing `run()` or `ToolsRegistry` interfaces

## Decisions

### Profile file format: Markdown with YAML frontmatter

**Decision**: Use `*.md` files with `---` YAML frontmatter, body = system prompt.

**Rationale**: Mirrors Claude Code's `CLAUDE.md` pattern — familiar, readable, editable without code changes. YAML frontmatter is well-supported by `python-frontmatter` / `PyYAML`. Alternatives: pure YAML (loses multiline prompt ergonomics), Python dataclasses in code (no separation of config from prose).

```markdown
---
name: researcher
description: Searches the web and reads documents to answer factual questions
model: gpt-4o-mini
tools:
  - http_get
  - read_file
sandbox:
  http:
    preset: strict
    allowed_hosts:
      - "api.wikipedia.org"
  filesystem:
    preset: off
---

You are a research specialist...
```

### Sandbox config: preset + field overrides

**Decision**: Frontmatter sandbox section supports `preset` key (`default` / `strict` / `off`) per domain plus optional field overrides applied on top.

**Rationale**: Presets encode safe defaults. Overrides allow per-agent precision (e.g. `strict` HTTP but with a specific allowed host list). Pure preset-only would be too coarse; fully explicit config would be verbose and error-prone.

Implementation:

1. Call `FileSandbox.<preset>()` or `HttpSandbox.<preset>()` to get base instance
2. Apply any extra keys from frontmatter as `dataclasses.replace()` overrides
3. `SandboxConfig` is assembled from the two domain configs

If `preset` key is absent, fall back to `default`.

### Dynamic delegate schema generation

**Decision**: `delegate` is registered with a factory pattern — at import time, profiles are loaded and the tool schema is built with a `profile` enum derived from profile names and descriptions.

**Rationale**: Enum in schema prevents LLM from inventing profile names. Descriptions in enum metadata help LLM pick the right profile. Alternatives: static schema with free-text `profile` field (no validation), separate `list_agents` tool (extra round-trip).

Concrete approach:

- `AgentProfileRegistry` loads all `*.md` from `src/agent/subagents/` using `importlib.resources`
- `delegate` registration reads the registry and calls `function_to_tool_schema` with a custom override for the `profile` parameter

### New module: `src/agent/profile.py`

**Decision**: All profile logic (dataclass, loader, registry, sandbox builder) lives in `profile.py`.

**Rationale**: Keeps `delegate.py` thin (execution only), `sandbox.py` unchanged (no profile-specific logic leaks in), and makes the loader independently testable.

## Risks / Trade-offs

- **`importlib.resources` path handling** — locating bundled `*.md` files works differently in editable install vs. wheel. Must use `importlib.resources.files()` (Python 3.9+) pattern, not `__file__` relative paths. → Test both modes.
- **Schema regeneration on every import** — profile files are read and schema rebuilt at import time. Cold import is slightly slower. Acceptable for now; cache with module-level singleton if profiling shows it matters.
- **Breaking change to `delegate` signature** — any existing orchestrator prompts or tests that call `delegate` with the old 4-param shape will break. → Documented in proposal; tests must be updated.
- **Tools filtered by name list** — `profile.tools` contains tool names (strings). `ToolsRegistry.to_openai_schema` currently filters by `group`, not by name. Need either a new filter method or name-based lookup. → Add `ToolsRegistry.to_openai_schema_by_names(names)` method.

## Open Questions

- Should `ToolsRegistry` get a `to_openai_schema_by_names(names: list[str])` overload, or should profiles also specify a group and filter by group? Name-list feels more explicit and avoids coupling profile files to internal group names.
