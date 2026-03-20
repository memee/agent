## Context

The agent framework has a working registry, loop, and `delegate` tool but no practical built-in tools. Adding `read_file` and `http_get` means handing filesystem and network access to an LLM — sandboxing is a first-order concern, not an afterthought.

The current `ToolsRegistry.execute()` calls tools as pure functions with no validation layer. `run()` has no notion of execution context. Both need to grow without breaking existing usage.

## Goals / Non-Goals

**Goals:**

- Add `SandboxConfig` with three presets (`default`, `strict`, `off`) covering file and HTTP constraints
- Add a `Validator` type and two built-in validators (`file_path_validator`, `http_url_validator`)
- Let any tool declare which of its arguments need validation, using built-in or custom validators
- Apply validation in `execute()` before calling the tool; `sandbox=None` silently uses `SandboxConfig.default()`
- Add `read_file` and `http_get` as auto-registered builtin tools
- Extend `run()` with an optional `sandbox` parameter forwarded to `execute()`

**Non-Goals:**

- LLM provider abstraction (separate concern)
- Per-tool sandbox overrides (one sandbox per `execute()` call is enough)
- Network-level proxying or OS-level sandboxing
- Response caching or retry logic

## Decisions

### D1: Validators live at the tool, sandbox config lives at call site

**Decision**: `validators` are declared on the tool at `register()` time as a `dict[str, Validator]` mapping argument names to callables. `SandboxConfig` is passed at `execute()` time (not stored in the registry).

**Rationale**: The registry is a catalog — it should not own runtime execution policy. Different callers (`run()`, tests, scripts) may want different sandbox configs on the same registry. Putting config at call site keeps the registry reusable.

**Alternative considered**: Store `SandboxConfig` in `ToolsRegistry.__init__()` — rejected because it forces multiple registry instances to get different sandboxes, complicating `delegate` and the global `tools` singleton.

### D2: Validator signature is `(value: Any, sandbox: SandboxConfig) -> Any`

**Decision**: Validators are plain callables that receive the argument value and the current `SandboxConfig`. They may transform (e.g., resolve a path) or raise (e.g., block a private IP). The return value replaces the original argument.

**Rationale**: Allows validators to both validate and normalise. `file_path_validator` returns an absolute resolved path so the tool never has to do its own resolution.

**Alternative considered**: Validators only raise, never transform — simpler, but forces tools to do their own path resolution after validation passes.

### D3: `sandbox=None` defaults to `SandboxConfig.default()` silently

**Decision**: Both `execute()` and `run()` treat `None` as `SandboxConfig.default()`. No `sandbox=None` means "off" escape hatch at these call sites — callers must explicitly pass `SandboxConfig.off()` to disable checks.

**Rationale**: Safe by default. Most callers won't think about sandbox; they shouldn't accidentally skip validation.

### D4: HTTP client — `httpx` over stdlib `urllib`

**Decision**: Use `httpx` for `http_get`.

**Rationale**: Cleaner API, built-in timeout support, follows redirects safely, returns response as text. `urllib` requires more boilerplate and redirect handling.

**Alternative considered**: `requests` — similar ergonomics but heavier; `httpx` is already async-ready if needed later.

### D5: Built-in tools registered as closures, not side-effect module imports

**Decision**: `read_file` and `http_get` modules register on the global `tools` instance via side-effect import (consistent with existing `hello_world` / `delegate` pattern). The validators they reference are imported from `agent.validators`.

**Rationale**: Keeps registration pattern consistent across all builtins. No new mechanism needed.

## Risks / Trade-offs

- **SSRF via DNS rebinding** → `block_private_ips=True` checks the resolved IP at request time (not DNS lookup time); still vulnerable to rebinding in theory. Acceptable for course tasks. → Mitigation: document the limitation.
- **`file_path_validator` resolves symlinks** → `Path.resolve()` follows symlinks, so a symlink inside `base_dir` pointing outside will be blocked. May surprise users with symlinked project trees. → Mitigation: document behaviour.
- **`httpx` as new dependency** → Adds one dependency. → Mitigation: lightweight, widely used.
- **Validator errors are untyped** — validators raise `ValueError` or `PermissionError`; `run()` does not catch them. A bad tool call will propagate up as an exception rather than returning a tool error to the LLM. → Mitigation: future work to wrap validator errors into tool result messages.

## Open Questions

- Should `strict` preset require callers to pass `file_base_dir` explicitly, or default to `Path.cwd()`? (Current leaning: require it — fail loudly.)
- Should `http_get` follow redirects by default? (Current leaning: yes, but cap at 5 hops.)
