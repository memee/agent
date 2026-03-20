## 1. Profile Module

- [x] 1.1 Create `src/agent/profile.py` with `AgentProfile` dataclass (`name`, `description`, `model`, `tools`, `system_prompt`, `sandbox_config: dict`)
- [x] 1.2 Implement `sandbox_from_profile(config: dict) -> SandboxConfig` in `profile.py`
- [x] 1.3 Implement `AgentProfileRegistry` class with `load_all()`, `all()`, `get(name)`, `names()` using `importlib.resources.files()`
- [x] 1.4 Create `src/agent/subagents/` directory and add `__init__.py` or package marker so `importlib.resources` can locate the files

## 2. Built-in Profiles

- [x] 2.1 Create `src/agent/subagents/researcher.md` with correct frontmatter (`name`, `description`, `model`, `tools`, `sandbox`) and system prompt body

## 3. ToolsRegistry: name-based filtering

- [x] 3.1 Add `to_openai_schema_by_names(names: list[str]) -> list[dict]` method to `ToolsRegistry` in `registry.py`

## 4. Rewrite delegate tool

- [x] 4.1 Rewrite `src/agent/builtin_tools/delegate.py`: new signature `(profile: str, task: str)`, look up `AgentProfile` from registry, build `SandboxConfig` via `sandbox_from_profile`, filter tools by name list, call `run()`
- [x] 4.2 Generate `delegate` tool schema dynamically from loaded profiles: `profile` param as enum of profile names with aggregated descriptions

## 5. Tests

- [x] 5.1 Unit tests for `sandbox_from_profile`: empty config, preset-only, preset + override, unknown preset, unknown field
- [x] 5.2 Unit tests for `AgentProfileRegistry`: loads built-in profiles, `get()` raises `KeyError` for unknown name
- [x] 5.3 Unit test for `researcher.md`: correct tools list, sandbox is not fully off
- [x] 5.4 Update/replace existing `delegate` tool tests to use new `(profile, task)` signature
- [x] 5.5 Test `delegate` tool schema: `profile` enum matches loaded profile names
