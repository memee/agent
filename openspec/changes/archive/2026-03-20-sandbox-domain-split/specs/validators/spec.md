## MODIFIED Requirements

### Requirement: Validator is a callable type alias

`agent/validators.py` SHALL define a `Validator` type alias:

```
Validator = Callable[[Any, Any], Any]
```

A `Validator` receives the argument value and the domain-specific sandbox sub-config (`FileSandbox` or `HttpSandbox`). It SHALL either return a (possibly transformed) value, or raise an exception to block the call.

#### Scenario: Validator transforms a value

- **WHEN** a validator is called with a relative path and a `FileSandbox` with `base_dir` set
- **THEN** it returns an absolute resolved path anchored within `base_dir`

#### Scenario: Validator blocks a forbidden value

- **WHEN** a validator is called with a path that resolves outside `base_dir`
- **THEN** it raises `PermissionError`

### Requirement: file_path_validator enforces file sandbox constraints

`file_path_validator` SHALL be a built-in `Validator` in `agent/validators.py` that accepts a `FileSandbox` as its second argument and:

1. Resolves the path (following symlinks) to an absolute path
2. If `sandbox.base_dir` is set, rejects paths that do not resolve within it (raises `PermissionError`)
3. Rejects paths matching any pattern in `sandbox.blocked_paths` against the resolved path (raises `PermissionError`)
4. Returns the resolved absolute `Path`

#### Scenario: Path within base_dir is allowed

- **WHEN** `file_path_validator("src/main.py", sandbox)` is called with `base_dir=Path("/workspace")`
- **THEN** returns `Path("/workspace/src/main.py")`

#### Scenario: Path traversal outside base_dir is blocked

- **WHEN** `file_path_validator("../../etc/passwd", sandbox)` is called with `base_dir=Path("/workspace")`
- **THEN** raises `PermissionError`

#### Scenario: Blocked path pattern is rejected

- **WHEN** `file_path_validator(".env", sandbox)` is called and `".env"` matches a pattern in `sandbox.blocked_paths`
- **THEN** raises `PermissionError`

#### Scenario: No base_dir set allows any path

- **WHEN** `file_path_validator("/etc/hosts", sandbox)` is called with `sandbox.base_dir = None`
- **THEN** returns `Path("/etc/hosts")` (still checks blocked_paths)

### Requirement: http_url_validator enforces HTTP sandbox constraints

`http_url_validator` SHALL be a built-in `Validator` in `agent/validators.py` that accepts an `HttpSandbox` as its second argument and:

1. Parses the URL; rejects non-HTTP/HTTPS schemes (raises `ValueError`)
2. If `sandbox.allowed_hosts` is set, rejects hostnames not in the list (raises `PermissionError`)
3. If `sandbox.block_private_ips` is `True`, resolves the hostname to an IP and rejects private/loopback ranges (raises `PermissionError`)
4. Returns the original URL string unchanged

#### Scenario: Public URL is allowed

- **WHEN** `http_url_validator("https://api.example.com/data", sandbox)` is called with `block_private_ips=True`
- **THEN** returns `"https://api.example.com/data"`

#### Scenario: Private IP is blocked

- **WHEN** `http_url_validator("http://169.254.169.254/latest/meta-data/", sandbox)` is called with `block_private_ips=True`
- **THEN** raises `PermissionError`

#### Scenario: Non-allowed host is blocked

- **WHEN** `http_url_validator("https://other.com", sandbox)` is called with `allowed_hosts=["api.example.com"]`
- **THEN** raises `PermissionError`

#### Scenario: Non-HTTP scheme is rejected

- **WHEN** `http_url_validator("file:///etc/passwd", sandbox)` is called
- **THEN** raises `ValueError`

### Requirement: ToolsRegistry.register() accepts domain parameter

`ToolsRegistry.register()` SHALL accept an optional `domain: str | None` parameter identifying the sandbox domain for the tool (`"filesystem"`, `"http"`, or `None`). The domain is stored with the tool entry and used by `execute()` to route the correct sub-config to validators.

#### Scenario: Tool registered with domain

- **WHEN** a tool is registered with `domain="filesystem"`
- **THEN** `execute()` passes `sandbox.filesystem` (a `FileSandbox`) to its validators

#### Scenario: Tool registered without domain

- **WHEN** a tool is registered with no `domain` argument
- **THEN** `execute()` passes the full `SandboxConfig` to its validators (fallback)

### Requirement: ToolsRegistry.execute() routes domain sub-config to validators

`ToolsRegistry.execute()` SHALL accept an optional `sandbox: SandboxConfig | None` parameter. When `sandbox` is `None`, it SHALL use `SandboxConfig.default()`. Before calling the tool function, it SHALL:

1. Look up the tool's `domain`
2. If `domain` is set, extract `getattr(sandbox, domain)` as the effective sub-config
3. Pass the sub-config to each registered validator

#### Scenario: execute() routes filesystem domain

- **WHEN** `registry.execute("read_file", {"path": ".env"})` is called
- **THEN** `file_path_validator` receives `sandbox.filesystem` (a `FileSandbox`), not the full `SandboxConfig`

#### Scenario: execute() uses default sandbox when none provided

- **WHEN** `registry.execute("read_file", {"path": ".env"})` is called with no sandbox
- **THEN** `SandboxConfig.default()` is used and `file_path_validator` blocks `.env`
