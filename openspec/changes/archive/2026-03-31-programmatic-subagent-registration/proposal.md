## Why

Sub-agents are currently discovered only through autodiscovery of files in `src/agent/subagents/`, which works for built-in profiles but blocks cases where an application wants to register a profile from code at runtime. We need an explicit registration API so the library can expose or compose sub-agents programmatically without bypassing the existing registry.

## What Changes

- `AgentProfileRegistry` will gain an explicit API for registering profiles from code alongside the current autodiscovery-based loading.
- Programmatic registration will accept full `AgentProfile` objects and expose them through the same read APIs as file-discovered profiles.
- The registry will define deterministic merge rules for discovered and manually registered profiles, including duplicate-name handling.
- Existing consumers of the registry, especially `delegate` and the sub-agent section rendered into the system prompt, will see programmatically registered profiles without separate integration paths.
- Autodiscovery will remain supported and will continue to work for built-in profiles.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `profile-loader`: the profile registry must support programmatic `AgentProfile` registration in addition to autodiscovery, deterministic result ordering, and unambiguous duplicate-name handling.
- `delegate-tool`: the dynamic schema and execution path for `delegate` must include programmatically registered profiles, including registrations performed after module import.

## Impact

- `src/agent/profile.py` - extend `AgentProfileRegistry` with write APIs and profile merge logic.
- `src/agent/builtin_tools/delegate.py` - refresh the dynamic schema and execution path so they use the extended registry without changing the call API.
- Profile and delegate tests - add new cases for manual registration, duplicate-name conflicts, and visibility of registered profiles.
