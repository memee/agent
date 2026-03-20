## MODIFIED Requirements

### Requirement: SandboxConfig holds file and HTTP execution constraints

`SandboxConfig` SHALL be a dataclass in `agent/sandbox.py` with the following fields:

- `filesystem: FileSandbox` — file-access constraints; defaults to `FileSandbox()`
- `http: HttpSandbox` — HTTP-access constraints; defaults to `HttpSandbox()`

The flat file and HTTP fields (`file_base_dir`, `blocked_paths`, `max_file_bytes`, `block_private_ips`, `allowed_hosts`, `http_timeout`, `max_response_bytes`) are removed.

#### Scenario: Default construction

- **WHEN** `SandboxConfig()` is instantiated with no arguments
- **THEN** `filesystem` is a `FileSandbox` with default values and `http` is an `HttpSandbox` with default values

### Requirement: SandboxConfig provides three class-method presets

`SandboxConfig` SHALL expose three class methods:

- `SandboxConfig.default()` — `filesystem=FileSandbox.default()`, `http=HttpSandbox.default()`
- `SandboxConfig.strict(file_base_dir: Path)` — `filesystem=FileSandbox.strict(file_base_dir)`, `http=HttpSandbox.strict()`
- `SandboxConfig.off()` — `filesystem=FileSandbox.off()`, `http=HttpSandbox.off()`

#### Scenario: default preset delegates to sub-config defaults

- **WHEN** `SandboxConfig.default()` is used
- **THEN** `filesystem.block_private_ips` does not exist; `http.block_private_ips` is `True`

#### Scenario: strict preset requires file_base_dir

- **WHEN** `SandboxConfig.strict(Path("/workspace"))` is called
- **THEN** `filesystem.base_dir` equals `Path("/workspace")` and `http.timeout` is `5.0`

#### Scenario: off preset disables all restrictions

- **WHEN** `SandboxConfig.off()` is used
- **THEN** `filesystem.blocked_paths` is empty and `http.block_private_ips` is `False`

#### Scenario: independent domain configuration

- **WHEN** `SandboxConfig(filesystem=FileSandbox.strict(Path("/workspace")), http=HttpSandbox.off())` is created
- **THEN** `filesystem.base_dir` is set and `http.block_private_ips` is `False`
