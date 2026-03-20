## Why

`SandboxConfig` is a flat dataclass that mixes file-access and HTTP-access fields in a single object, forcing operators to configure both domains together. Operators need independent control — e.g. strict filesystem restrictions with unrestricted HTTP, or vice versa — which the current design prevents.

## What Changes

- `SandboxConfig` becomes a composite with two domain sub-configs: `filesystem: FileSandbox` and `http: HttpSandbox`
- **BREAKING**: `FileSandbox` replaces the flat file fields (`file_base_dir`, `blocked_paths`, `max_file_bytes`)
- **BREAKING**: `HttpSandbox` replaces the flat HTTP fields (`block_private_ips`, `allowed_hosts`, `http_timeout`, `max_response_bytes`)
- Presets (`default`, `strict`, `off`) exist on both sub-config level and composite level
- Tool registration gains a `domain` field (`"filesystem"` | `"http"` | `None`) separate from `group`
- `registry.execute()` routes the correct sub-config to validators and tool functions based on domain
- `read_file` and `write_file` share `FileSandbox`; `http_get` and `http_post` share `HttpSandbox`

## Capabilities

### New Capabilities

- `filesystem-sandbox`: `FileSandbox` dataclass with file-access constraints and presets
- `http-sandbox`: `HttpSandbox` dataclass with HTTP-access constraints and presets

### Modified Capabilities

- `sandbox-config`: `SandboxConfig` becomes a composite of `FileSandbox` + `HttpSandbox` instead of a flat dataclass
- `read-file-tool`: updated to use `FileSandbox` instead of flat `SandboxConfig`
- `http-get-tool`: updated to use `HttpSandbox` instead of flat `SandboxConfig`
- `validators`: file and HTTP validators updated to accept domain sub-configs

## Impact

- `src/agent/sandbox.py` — full rewrite
- `src/agent/registry.py` — `register()` gains `domain` param; `execute()` routes sub-config by domain
- `src/agent/builtin_tools/read_file.py` — accepts `FileSandbox` instead of `SandboxConfig`
- `src/agent/builtin_tools/http_get.py` — accepts `HttpSandbox` instead of `SandboxConfig`
- `src/agent/validators.py` — validator signatures updated
- `tests/test_sandbox.py`, `tests/test_registry.py`, `tests/test_builtin_tools.py` — updated
