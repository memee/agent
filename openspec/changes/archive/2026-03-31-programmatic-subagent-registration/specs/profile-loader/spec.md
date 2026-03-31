## ADDED Requirements

### Requirement: Profile registry supports programmatic registration

The library SHALL allow `AgentProfileRegistry` to register an `AgentProfile` programmatically in addition to loading bundled profiles from `src/agent/subagents/`.

Programmatically registered profiles SHALL be exposed through the same read APIs as autodiscovered profiles:

- `all()` SHALL return both autodiscovered and programmatically registered profiles
- `names()` SHALL include names from both sources
- `get(name)` SHALL return a programmatically registered profile by name

The merged results SHALL remain sorted alphabetically by profile name.

#### Scenario: Register profile before first read

- **WHEN** a fresh `AgentProfileRegistry` registers an `AgentProfile(name="planner", ...)` before `load_all()` or any read method is called
- **THEN** `registry.get("planner")` returns that profile and `planner` appears in `registry.names()`

#### Scenario: Register profile after built-in profiles are loaded

- **WHEN** `AgentProfileRegistry.load_all()` has already loaded built-in profiles and then `register()` is called with `AgentProfile(name="planner", ...)`
- **THEN** `registry.all()` contains both the built-in profiles and `planner`

#### Scenario: Merged profile names remain alphabetical

- **WHEN** the registry contains autodiscovered profile `researcher` and programmatically registered profiles `zap` and `alpha`
- **THEN** `registry.names()` returns `["alpha", "researcher", "zap"]`

### Requirement: Profile registry rejects duplicate profile names

`AgentProfileRegistry` SHALL reject duplicate profile names across all profile sources.

If a programmatically registered profile name matches any existing autodiscovered or already registered profile, registration SHALL raise `ValueError` and SHALL NOT replace the existing profile.

If autodiscovery encounters multiple profiles with the same `name`, loading SHALL raise `ValueError` instead of silently overwriting an earlier profile.

#### Scenario: Registering duplicate of built-in profile raises error

- **WHEN** the registry already contains the built-in `researcher` profile and `register()` is called with `AgentProfile(name="researcher", ...)`
- **THEN** `register()` raises `ValueError` identifying the duplicate profile name

#### Scenario: Registering duplicate of programmatically added profile raises error

- **WHEN** the registry has already registered `AgentProfile(name="planner", ...)` and `register()` is called again with another `AgentProfile(name="planner", ...)`
- **THEN** `register()` raises `ValueError` and the first `planner` profile remains registered
