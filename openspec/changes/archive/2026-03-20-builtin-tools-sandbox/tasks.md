## 1. SandboxConfig

- [x] 1.1 Create `agent/sandbox.py` with `SandboxConfig` dataclass (all fields with defaults)
- [x] 1.2 Implement `SandboxConfig.default()` class method
- [x] 1.3 Implement `SandboxConfig.strict(file_base_dir: Path)` class method
- [x] 1.4 Implement `SandboxConfig.off()` class method
- [x] 1.5 Write tests for all three presets and field defaults

## 2. Validators

- [x] 2.1 Create `agent/validators.py` with `Validator` type alias
- [x] 2.2 Implement `file_path_validator` (resolve, base_dir check, blocked_paths check)
- [x] 2.3 Implement `http_url_validator` (scheme check, allowed_hosts check, private IP check)
- [x] 2.4 Write tests for `file_path_validator` (allowed path, traversal, blocked pattern, no base_dir)
- [x] 2.5 Write tests for `http_url_validator` (public URL, private IP, non-allowed host, bad scheme)

## 3. Registry integration

- [x] 3.1 Add `validators: dict[str, Validator] | None = None` parameter to `ToolsRegistry.register()`
- [x] 3.2 Store validators in the tool entry dict
- [x] 3.3 Add `sandbox: SandboxConfig | None = None` parameter to `ToolsRegistry.execute()`
- [x] 3.4 Apply validators in `execute()` before calling the tool function (default to `SandboxConfig.default()` when `None`)
- [x] 3.5 Write tests: tool with validators applied, tool without validators, default sandbox used when none passed

## 4. run() integration

- [x] 4.1 Add `sandbox: SandboxConfig | None = None` parameter to `run()`
- [x] 4.2 Forward sandbox to each `registry.execute()` call
- [x] 4.3 Write tests: sandbox forwarded correctly, defaults to `SandboxConfig.default()`

## 5. Built-in tools

- [x] 5.1 Add `httpx` to project dependencies
- [x] 5.2 Create `agent/builtin_tools/read_file.py` registered with `validators={"path": file_path_validator}`
- [x] 5.3 Implement size limit check in `read_file` using `sandbox.max_file_bytes`
- [x] 5.4 Create `agent/builtin_tools/http_get.py` registered with `validators={"url": http_url_validator}`
- [x] 5.5 Implement timeout and size limit in `http_get` using `sandbox.http_timeout` and `sandbox.max_response_bytes`
- [x] 5.6 Register both tools via side-effect import in `agent/builtin_tools/__init__.py`
- [x] 5.7 Write tests for `read_file` (happy path, size limit, blocked path)
- [x] 5.8 Write tests for `http_get` (happy path mocked, private IP blocked, size limit, timeout)
