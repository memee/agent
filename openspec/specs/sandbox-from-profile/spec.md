## ADDED Requirements

### Requirement: SandboxConfig can be built from a profile frontmatter dict

The library SHALL provide a function `sandbox_from_profile(config: dict) -> SandboxConfig` (in `agent/profile.py` or `agent/sandbox.py`) that constructs a `SandboxConfig` from a frontmatter sandbox mapping.

The function SHALL:

1. For each domain key (`http`, `filesystem`) present in `config`:
   a. Read the `preset` value (default: `"default"`) and instantiate the domain sandbox via its class method (e.g. `HttpSandbox.default()`)
   b. Collect remaining keys as field overrides
   c. Apply overrides using `dataclasses.replace()`
2. For domains absent from `config`, use the domain's `default()` preset
3. Return a `SandboxConfig` assembled from both domain instances

#### Scenario: Empty config produces default SandboxConfig

- **WHEN** `sandbox_from_profile({})` is called
- **THEN** the result equals `SandboxConfig.default()`

#### Scenario: HTTP strict preset with allowed_hosts override

- **WHEN** `sandbox_from_profile({"http": {"preset": "strict", "allowed_hosts": ["example.com"]}})` is called
- **THEN** result's `http` starts from `HttpSandbox.strict()` and `http.allowed_hosts == ["example.com"]`

#### Scenario: Filesystem off preset

- **WHEN** `sandbox_from_profile({"filesystem": {"preset": "off"}})` is called
- **THEN** result's `filesystem` equals `FileSandbox.off()` and `http` equals `HttpSandbox.default()`

#### Scenario: Unknown preset raises ValueError

- **WHEN** `sandbox_from_profile({"http": {"preset": "banana"}})` is called
- **THEN** a `ValueError` is raised identifying the invalid preset name

#### Scenario: Unknown override field raises ValueError

- **WHEN** `sandbox_from_profile({"http": {"nonexistent_field": True}})` is called
- **THEN** a `ValueError` is raised identifying the invalid field name
