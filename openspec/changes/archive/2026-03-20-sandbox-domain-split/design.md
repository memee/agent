## Context

`SandboxConfig` is a flat dataclass with 7 fields spanning two unrelated domains: file-access and HTTP-access. Both `read_file` and `http_get` receive the full object but use only their half. Validators (`file_path_validator`, `http_url_validator`) access fields from `SandboxConfig` directly. `registry.execute()` passes a single `SandboxConfig` to all tools regardless of domain.

The registry has a `group` field per tool (currently `"builtin"` for all built-ins) used for schema filtering. A separate `domain` concept is needed for sandbox routing.

## Goals / Non-Goals

**Goals:**

- `FileSandbox` and `HttpSandbox` as independent, independently-configurable dataclasses
- `SandboxConfig` as a thin composite holding one of each
- Registry routes the right sub-config to each tool based on a new `domain` field
- Presets at both sub-config and composite level
- No change to how `run()` is called (still accepts `SandboxConfig | None`)

**Non-Goals:**

- Adding new sandbox domains (e.g. `execute_code`) — not needed yet
- Per-operation limits (separate read vs write byte limits) — one `max_file_bytes` covers both
- Changing tool registration API beyond adding `domain` param

## Decisions

### 1. `domain` as a separate field from `group`

`group` means "where the tool comes from" (builtin, mcp, custom) and is used for schema filtering. `domain` means "which resource class the tool touches" and is used for sandbox routing. Conflating them would force a choice between filtering and routing semantics.

**Alternative considered**: rename `group` → `domain` and handle filtering differently. Rejected — `group` is already used in `to_openai_schema()` and changing it would be a separate breaking change with no gain.

### 2. Sub-configs as nested dataclasses, not a dict

```python
@dataclass
class SandboxConfig:
    filesystem: FileSandbox = field(default_factory=FileSandbox)
    http: HttpSandbox = field(default_factory=HttpSandbox)
```

Attribute access (`sandbox.filesystem.base_dir`) is type-safe and IDE-friendly. A `dict[str, Any]` would lose type information and require casting in validators.

### 3. Validators accept domain sub-config, not full `SandboxConfig`

`file_path_validator(value, sandbox: FileSandbox)` — validator only knows about its domain. This enforces the boundary: a file validator cannot accidentally read an HTTP field.

`registry.execute()` is responsible for the routing:

```python
domain = entry["domain"]  # "filesystem" | "http" | None
if domain is not None:
    domain_sandbox = getattr(effective_sandbox, domain)
else:
    domain_sandbox = effective_sandbox  # tools with no domain get full config (edge case)
validated_args[arg_name] = validator(value, domain_sandbox)
```

### 4. Presets at both levels

Sub-configs have their own presets (`FileSandbox.strict(path)`, `HttpSandbox.off()`).
`SandboxConfig` presets delegate to sub-config presets:

```python
@classmethod
def strict(cls, file_base_dir: Path) -> "SandboxConfig":
    return cls(
        filesystem=FileSandbox.strict(file_base_dir),
        http=HttpSandbox.strict(),
    )
```

This lets operators compose independently (`SandboxConfig(filesystem=FileSandbox.strict(path), http=HttpSandbox.off())`) or use a convenience preset.

### 5. `Validator` type alias updated

```python
# was: Callable[[Any, SandboxConfig], Any]
# file validators:
FileValidator = Callable[[Any, FileSandbox], Any]
# http validators:
HttpValidator = Callable[[Any, HttpSandbox], Any]
```

Or keep a single union type — to be decided during implementation. Simplest option: keep `Validator = Callable[[Any, Any], Any]` and rely on runtime routing.

## Risks / Trade-offs

- **Breaking change to validator signatures** → All existing validators and their test fixtures need updating. Low risk (internal API, small surface area).
- **`domain=None` tools** → If a tool is registered without a domain, the routing falls back to passing the full `SandboxConfig`. This is a footgun but acceptable for edge cases; can be tightened later.
- **Field rename** (`file_base_dir` → `base_dir`, `http_timeout` → `timeout`) inside sub-configs — cleaner names but requires updating all references → mitigated by small codebase.

## Migration Plan

1. Add `FileSandbox` and `HttpSandbox` in `sandbox.py`, keep old `SandboxConfig` temporarily
2. Update `registry.register()` to accept `domain` param
3. Update `registry.execute()` to route sub-config
4. Update validators to accept sub-configs
5. Update `read_file` and `http_get` to accept sub-configs
6. Rewrite `SandboxConfig` as composite, remove old flat fields
7. Update tests

No migration needed for external callers — `run()` signature unchanged, `SandboxConfig.default()` and `SandboxConfig.strict()` presets preserved.
