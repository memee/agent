## ADDED Requirements

### Requirement: Profile loader discovers built-in profiles at import time

The library SHALL include an `AgentProfileRegistry` that loads all `*.md` files from `src/agent/subagents/` using `importlib.resources.files()` when first accessed.

The registry SHALL expose:

- `all() -> list[AgentProfile]`: all loaded profiles in stable order (alphabetical by name)
- `get(name: str) -> AgentProfile`: returns profile by name, raises `KeyError` if not found
- `names() -> list[str]`: sorted list of profile names

#### Scenario: Built-in profiles are available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `AgentProfileRegistry` contains at least the `researcher` profile

#### Scenario: get() raises KeyError for unknown profile

- **WHEN** `registry.get("nonexistent")` is called
- **THEN** a `KeyError` is raised with the unknown name

### Requirement: Library ships a researcher built-in profile

The library SHALL include `src/agent/subagents/researcher.md` with:

- `name: researcher`
- `description`: clearly explains the profile is for web research and document reading
- `model`: a capable but cost-efficient model (e.g. `gpt-4o-mini`)
- `tools`: `["http_get", "read_file"]`
- `sandbox.http.preset: strict` with an appropriate `allowed_hosts` or no host restriction
- `sandbox.filesystem.preset: strict` with `base_dir` set to `"./workspace"` or equivalent

#### Scenario: researcher profile loads with correct tools

- **WHEN** the profile registry is accessed
- **THEN** `registry.get("researcher").tools == ["http_get", "read_file"]`

#### Scenario: researcher sandbox restricts filesystem

- **WHEN** the researcher profile's sandbox is built
- **THEN** `sandbox.filesystem` is not `FileSandbox.off()` — filesystem access is sandboxed
