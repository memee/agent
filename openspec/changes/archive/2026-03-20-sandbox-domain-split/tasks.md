## 1. Domain Sub-configs

- [x] 1.1 Add `FileSandbox` dataclass to `sandbox.py` with `base_dir`, `blocked_paths`, `max_file_bytes` fields and `default()`, `strict()`, `off()` presets
- [x] 1.2 Add `HttpSandbox` dataclass to `sandbox.py` with `block_private_ips`, `allowed_hosts`, `timeout`, `max_response_bytes` fields and `default()`, `strict()`, `off()` presets
- [x] 1.3 Rewrite `SandboxConfig` as a composite with `filesystem: FileSandbox` and `http: HttpSandbox` fields; update `default()`, `strict()`, `off()` to delegate to sub-configs; remove all flat fields

## 2. Registry Domain Routing

- [x] 2.1 Add `domain: str | None` parameter to `ToolsRegistry.register()`; store in tool entry
- [x] 2.2 Update `ToolsRegistry.execute()` to route the correct sub-config (`getattr(sandbox, domain)`) to validators when `domain` is set

## 3. Validators

- [x] 3.1 Update `file_path_validator` signature to accept `FileSandbox` instead of `SandboxConfig`; change `sandbox.file_base_dir` → `sandbox.base_dir`
- [x] 3.2 Update `http_url_validator` signature to accept `HttpSandbox` instead of `SandboxConfig`; change `sandbox.http_timeout` → `sandbox.timeout`
- [x] 3.3 Update `Validator` type alias to `Callable[[Any, Any], Any]`

## 4. Built-in Tools

- [x] 4.1 Update `read_file` registration to add `domain="filesystem"`; change `sandbox.max_file_bytes` reference to use `FileSandbox` (parameter type update)
- [x] 4.2 Update `http_get` registration to add `domain="http"`; change `sandbox.http_timeout` → `sandbox.timeout` and `sandbox.max_response_bytes` reference to use `HttpSandbox`

## 5. Tests

- [x] 5.1 Update `test_sandbox.py` — replace flat `SandboxConfig` field tests with `FileSandbox` and `HttpSandbox` tests; add composite `SandboxConfig` tests
- [x] 5.2 Update `test_validators.py` — pass `FileSandbox`/`HttpSandbox` instances instead of `SandboxConfig`
- [x] 5.3 Update `test_registry.py` — add `domain` to tool registrations; verify sub-config routing in `execute()`
- [x] 5.4 Update `test_builtin_tools.py` — update any `SandboxConfig` construction to use new composite API
