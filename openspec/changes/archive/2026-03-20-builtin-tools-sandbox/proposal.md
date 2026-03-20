## Why

The agent framework has a registry and loop, but no practical built-in tools — just a `hello_world` placeholder. Any real task requires fetching HTTP resources or reading files. These tools must be safe to hand to an LLM, which means sandboxing is not optional: without it, a model can read `/etc/passwd` or hit internal cloud metadata endpoints.

## What Changes

- Add `agent/sandbox.py` — `SandboxConfig` dataclass with presets (`default`, `strict`, `off`)
- Add `agent/validators.py` — `Validator` type alias and built-in validators (`file_path_validator`, `http_url_validator`)
- Extend `ToolsRegistry.register()` to accept a `validators` parameter mapping argument names to `Validator` callables
- Extend `ToolsRegistry.execute()` to apply validators before calling the tool; `sandbox=None` falls back to `SandboxConfig.default()`
- Extend `run()` to accept and forward a `sandbox` parameter
- Add `builtin_tools/read_file.py` — reads a file, validated with `file_path_validator`
- Add `builtin_tools/http_get.py` — HTTP GET, validated with `http_url_validator`

## Capabilities

### New Capabilities

- `sandbox-config`: `SandboxConfig` dataclass with `default`, `strict`, and `off` presets controlling file and HTTP constraints
- `validators`: `Validator` type alias and built-in `file_path_validator` / `http_url_validator`; tools declare validators at registration; `execute()` applies them with sandbox config as context
- `read-file-tool`: built-in tool that reads a file from disk, sandboxed via `file_path_validator`
- `http-get-tool`: built-in tool that performs an HTTP GET request, sandboxed via `http_url_validator`

### Modified Capabilities

- `agent-loop`: `run()` gains an optional `sandbox` parameter (defaulting to `SandboxConfig.default()`), forwarded to `execute()`

## Impact

- `agent/registry.py` — `register()` and `execute()` signatures change; backwards-compatible (new optional params)
- `agent/run.py` — `run()` signature gains optional `sandbox` parameter
- `agent/builtin_tools/__init__.py` — two new modules auto-registered on import
- New dependency: `httpx` (or stdlib `urllib`) for HTTP — to be decided in design
