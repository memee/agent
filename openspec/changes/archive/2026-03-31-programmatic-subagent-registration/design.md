## Context

Today, `AgentProfileRegistry` loads profiles only from `src/agent/subagents/*.md` on first access, and `delegate` stores its generated tool schema with the profile enum at module import time. That is sufficient for built-in profiles, but not for an application that wants to add a profile from code during process startup or runtime configuration.

This change cuts across two areas:

- `src/agent/profile.py`, where the registry needs safe mutation without breaking autodiscovery
- `src/agent/builtin_tools/delegate.py`, where the `profile` schema must reflect the current registry state rather than only the import-time snapshot

Key constraints:

- we do not want to remove or rewrite the existing autodiscovery of packaged Markdown files
- the public API `delegate(profile, task, image_url=None)` must remain unchanged
- the result of `all()` / `names()` must remain deterministic so prompts and tests stay stable

## Goals / Non-Goals

**Goals:**

- Add an explicit API for registering `AgentProfile` objects from code.
- Preserve coexistence of autodiscovered and programmatically registered profiles.
- Define unambiguous behavior for duplicate-name conflicts.
- Ensure `delegate` and its schema can see profiles added after module import.
- Cover the new behavior with unit tests.

**Non-Goals:**

- Hot reloading files from `src/agent/subagents/`.
- Registering profiles from external directories or new configuration sources.
- Changing the `AgentProfile` format or the frontmatter of existing Markdown files.
- Extending `delegate` with new arguments or new sub-agent execution semantics.

## Decisions

### D1: The registry will store autodiscovered and manually added profiles separately

**Decision**: `AgentProfileRegistry` will maintain two state collections: profiles discovered from files and profiles registered programmatically. The read methods (`all`, `names`, `get`) will return a merged view.

**Rationale**: This keeps autodiscovery as a simple one-time step, while manual registration does not require rewriting the loader or mutating packaged resources. The alternative of a single mutable dictionary would blur the source of entries and make consistent reloading harder.

### D2: A duplicate name will be an error regardless of source

**Decision**: Programmatic registration of a profile whose name already exists in the merged registry will raise `ValueError`. Similarly, if autodiscovery encounters two profiles with the same name, the loader will fail the same way instead of silently overwriting.

**Rationale**: Silent overwrites would be hard to diagnose and could change `delegate` behavior without any signal. An explicit error gives a deterministic contract and simpler tests. The considered alternative of "manual overrides built-in" was rejected because it increases the risk of hidden configuration changes.

### D3: Registration before and after first load should behave the same

**Decision**: `register(profile: AgentProfile)` will not require a prior `load_all()`. Read methods will always ensure file-based profiles are loaded before merging in manual entries.

**Rationale**: Application code should not need to know the internal registry lifecycle. This allows a profile to be registered immediately after module import while reads still behave correctly. The alternative of requiring explicit `load_all()` would be brittle and easy to misuse.

### D4: `delegate` will refresh its own schema from the current registry

**Decision**: `delegate` will not rely only on the schema built at import time. The module will get a lightweight way to refresh `tools._tools["delegate"]["schema"]` after registry changes, or it will generate the schema on each relevant registry read.

**Rationale**: A programmatically added profile must become selectable by the LLM, and the old enum does not provide that. The smallest change is an explicit refresh for `delegate` only; redesigning the whole `ToolsRegistry` around dynamic schemas would be broader than this change requires.

### D5: Result ordering remains alphabetical by name

**Decision**: The merged view returned by `all()` and `names()` will remain sorted alphabetically by `profile.name`, regardless of source.

**Rationale**: Stable ordering is already part of the existing contract and affects the system prompt and tests. Preserving registration order as a priority does not add user value and would reduce determinism.

## Risks / Trade-offs

- `[The delegate schema may remain stale]` -> schema refresh will be tied directly to the registration API and covered by a test that checks the enum after `register()`.
- `[The change may surface existing hidden duplicate names]` -> duplicate-name errors will include the conflicting profile name so the fix is quick.
- `[A mutable singleton may make tests harder to isolate]` -> tests will use fresh `AgentProfileRegistry` instances, and singleton-level tests will reset local state.
- `[Manual registration may happen after the system prompt was already built]` -> this is an acceptable trade-off; new profiles will become visible on the next prompt build or next schema read.

## Migration Plan

- No data migration and no file format changes.
- Code that relies only on autodiscovery requires no changes.
- Code that wants to add a profile programmatically will be able to call the new registry API during process bootstrap.
- In a rollback, removing the new `register(...)` calls is sufficient; file-based profiles will continue to work as before.

## Open Questions

- Do we also need a helper like `register_many(...)` in addition to `register(profile)`, or is a single-item operation sufficient for the current scope?
