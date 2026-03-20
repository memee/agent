## ADDED Requirements

### Requirement: SandboxConfig holds file and HTTP execution constraints

`SandboxConfig` SHALL be a dataclass in `agent/sandbox.py` with the following fields:

- `file_base_dir: Path | None` — if set, all file paths must resolve within this directory; `None` means no directory restriction
- `blocked_paths: list[str]` — glob patterns matched against the resolved path; matching paths are rejected
- `max_file_bytes: int` — maximum number of bytes a file read may return
- `block_private_ips: bool` — if `True`, requests to private/loopback IP ranges are rejected
- `allowed_hosts: list[str] | None` — if set, only these hostnames are permitted; `None` allows all
- `http_timeout: float` — timeout in seconds for HTTP requests
- `max_response_bytes: int` — maximum response body size in bytes

#### Scenario: Default construction

- **WHEN** `SandboxConfig()` is instantiated with no arguments
- **THEN** `block_private_ips` is `True`, `blocked_paths` includes `".env"` and `".git"`, `allowed_hosts` is `None`, `max_file_bytes` is `1_000_000`, `http_timeout` is `10.0`, `max_response_bytes` is `500_000`

### Requirement: SandboxConfig provides three class-method presets

`SandboxConfig` SHALL expose three class methods:

- `SandboxConfig.default()` — sensible defaults: `block_private_ips=True`, common blocked paths, no host allowlist
- `SandboxConfig.strict(file_base_dir: Path)` — all default restrictions plus mandatory `file_base_dir`, shorter timeout (`5.0`), smaller size limits
- `SandboxConfig.off()` — no restrictions: `block_private_ips=False`, empty `blocked_paths`, no `file_base_dir`, long timeout

#### Scenario: default preset blocks private IPs

- **WHEN** `SandboxConfig.default()` is used
- **THEN** `block_private_ips` is `True` and `blocked_paths` is non-empty

#### Scenario: strict preset requires file_base_dir

- **WHEN** `SandboxConfig.strict(Path("/workspace"))` is called
- **THEN** `file_base_dir` equals `Path("/workspace")` and `http_timeout` is `5.0`

#### Scenario: off preset disables all restrictions

- **WHEN** `SandboxConfig.off()` is used
- **THEN** `block_private_ips` is `False`, `blocked_paths` is empty, and `file_base_dir` is `None`
