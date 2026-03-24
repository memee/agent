## Why

Agent tools like `http_post` sometimes need secret values (API keys, tokens, passwords) that must not appear in the LLM conversation context or logs. Currently there is no mechanism to pass secrets to tools without embedding them literally in messages, making leakage unavoidable.

## What Changes

- **NEW** `SecretsStore`: a runtime container mapping secret names to values, loaded from caller-supplied dict (typically sourced from env vars at the call site)
- **NEW** `${NAME}` interpolation in `registry.execute()`: before validators run, all string args are scanned for `${NAME}` placeholders and replaced with values from `SecretsStore`; unknown placeholders are left unchanged
- **NEW** `headers` parameter on `http_post` and `http_get`: accepts a JSON string so the LLM can specify request headers (including auth headers) using `${NAME}` references
- **NEW** `secrets` parameter on `run()`: `SecretsStore` is passed through to `registry.execute()` alongside `sandbox`
- **NEW** scrubber integration: resolved secret values are registered with `scrub.py` at runtime so they are masked in any log output
- **NEW** base system prompt instruction: teaches agents to normalize any placeholder format (`<NAME>`, `{NAME}`) to `${NAME}` when constructing tool call arguments

## Capabilities

### New Capabilities

- `secrets-store`: Runtime container for named secret values; supports `${NAME}` interpolation of strings
- `secret-interpolation`: Mechanism in `registry.execute()` that resolves `${NAME}` placeholders in tool args before validators and execution

### Modified Capabilities

- `http-post-tool`: Gains optional `headers` parameter (JSON string)
- `http-get-tool`: Gains optional `headers` parameter (JSON string)
- `log-scrubbing`: Extended to accept runtime-registered secrets in addition to env-var-declared ones

## Impact

- `src/agent/run.py` — `run()` gains `secrets: SecretsStore | None` parameter
- `src/agent/registry.py` — `execute()` gains `secrets` parameter; interpolation step added before validators
- `src/agent/scrub.py` — `register_runtime_secrets(values)` function added
- `src/agent/builtin_tools/http_post.py` — `headers` parameter added
- `src/agent/builtin_tools/http_get.py` — `headers` parameter added
- New: `src/agent/secrets.py` — `SecretsStore` class
- Base system prompt template updated with secret reference convention
