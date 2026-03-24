## Context

The agent framework passes tool arguments directly from LLM-generated tool calls. If an agent task requires an API key or auth token (e.g., to POST to a verification endpoint), the only current mechanism is to put the literal value in the conversation — either in the system prompt or as explicit instructions. That value then propagates into LLM context, tool call args, and log output, all of which are unsafe surfaces.

The framework already has `SandboxConfig` as a typed, injected non-schema parameter. Secrets follow the same pattern.

## Goals / Non-Goals

**Goals:**

- Allow callers to supply named secrets at `run()` call time without embedding values in prompts
- Resolve `${NAME}` placeholders in tool call args before validators and execution
- Ensure resolved values never appear in log output (scrubber integration)
- Allow LLMs to specify request headers (including auth) via `${NAME}` references
- Teach agents via system prompt to normalize any placeholder style to `${NAME}`

**Non-Goals:**

- Profile-level secret declarations (secrets are always runtime / caller-supplied)
- Encrypted secret storage or secret rotation
- Secrets for non-HTTP tools (filesystem, delegate) — can be added later if needed
- Partial-match obfuscation of secret names in LLM context (names are visible, values are not)

## Decisions

### D1: Interpolation happens in `registry.execute()`, before validators

**Chosen**: interpolate all string args in `execute()` before the validator loop runs.

**Why**: URL validators do DNS resolution to check private IPs. If the URL contains `${API_KEY}` as a query param, the validator sees a syntactically valid URL and operates correctly only after interpolation. Doing it after validators would silently bypass security checks.

**Alternative considered**: interpolate inside each tool function. Rejected — requires every tool to know about secrets, is repetitive, and is easy to forget.

### D2: Unknown placeholders are left unchanged (not errors)

**Chosen**: `${UNKNOWN}` in args → left as-is, no exception.

**Why**: a tool's body might contain legitimate `${...}` text that is not a secret reference (e.g., template strings in content). Raising on unknown names would make the system brittle. The `scrub.py` backstop handles accidental leakage of values that slip through.

**Alternative considered**: raise `KeyError` on unknown names. Rejected — too fragile for general use; would require escaping in non-secret content.

### D3: Resolved values are registered with scrubber at `run()` setup

**Chosen**: `SecretsStore` exposes `values() -> list[str]`; caller (or `run()`) passes these to `scrub.register_runtime_secrets()` before the loop starts.

**Why**: even with correct interpolation, secrets could appear in HTTP response bodies echoed by the LLM, or in error messages. The scrubber is the last line of defense.

**Alternative considered**: scrub only at log emit time using patterns. Rejected — patterns are heuristic and miss arbitrary-format secrets.

### D4: `headers` parameter on HTTP tools accepts a JSON string

**Chosen**: `headers: str = "{}"` — same pattern as `body`.

**Why**: consistent with how `http_post` already handles `body`; the LLM can construct headers as a JSON object string with `${NAME}` references. The tool parses the JSON internally.

**Alternative considered**: `headers: dict` typed param. Rejected — OpenAI function calling schema maps `dict` to `"object"` type which requires a fixed schema; a JSON string is simpler and more flexible for dynamic header construction.

### D5: Agent normalization via system prompt, not framework-level multi-format parsing

**Chosen**: add a convention block to the base system prompt instructing agents to convert any placeholder format to `${NAME}` in tool calls.

**Why**: the set of placeholder formats used in real-world task instructions is unbounded (`<NAME>`, `{NAME}`, `[[NAME]]`, `__NAME__`, etc.). Teaching the LLM the canonical form is more robust than writing regex for every format. The framework only needs to handle one syntax.

**Alternative considered**: regex normalization in `execute()` for common formats. Rejected — fragile, would incorrectly transform legitimate content.

## Risks / Trade-offs

- **LLM normalization failure**: LLM may copy a literal `<API_KEY>` string into a tool arg instead of converting to `${API_KEY}`. The scrubber will mask it in logs if the value is registered, but the HTTP call will fail (unknown placeholder or wrong value). Mitigation: clear system prompt instruction; the error surfaces fast during testing.

- **Legitimate `${...}` content**: a body containing template text like `"template": "${user_name}"` will be left unchanged if `user_name` is not in `SecretsStore`, which is correct. But if someone happens to name a secret the same as a template variable, silent substitution occurs. Mitigation: use descriptive, unique secret names (e.g., `AIDEVS_API_KEY` not `key`).

- **Secrets visible to subagents**: `run()` passes `SecretsStore` to subagents via `delegate`. Subagents can use the same secrets, but also have them in their interpolation scope. This is acceptable — subagents operate within the same trust boundary.

## Migration Plan

All changes are additive. `secrets` parameter on `run()` defaults to `None`; when `None`, no interpolation occurs and behavior is identical to current. `headers` on HTTP tools defaults to `"{}"` (empty). Existing callers require no changes.

## Open Questions

- Should `delegate` forward the parent's `SecretsStore` to the subagent automatically, or require explicit passing? Current decision: forward automatically (same trust boundary). Revisit if subagent isolation becomes a requirement.
