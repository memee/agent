## ADDED Requirements

### Requirement: registry.execute() accepts and applies SecretsStore

`ToolsRegistry.execute()` SHALL accept an optional `secrets: SecretsStore | None` parameter (default `None`).
When `secrets` is provided, it SHALL call `secrets.interpolate(value)` on every string value in the `args` dict **before** validators run and before the tool function is called.
Non-string arg values SHALL be passed through unchanged.
The original `args` dict SHALL NOT be mutated; a copy SHALL be used for interpolation.
The `tool_call_start` log entry SHALL record the **original** (pre-interpolation) args so that placeholders appear in logs, not resolved values.

#### Scenario: Placeholder in URL arg is resolved before validator

- **WHEN** `execute("http_get", {"url": "https://api.example.com?key=${API_KEY}"}, secrets=SecretsStore({"API_KEY": "real"}))`
- **THEN** the URL validator and tool receive `"https://api.example.com?key=real"`

#### Scenario: Placeholder in body arg is resolved

- **WHEN** `execute("http_post", {"url": "https://x.com", "body": '{"key":"${API_KEY}"}'}, secrets=SecretsStore({"API_KEY": "real"}))`
- **THEN** the tool receives `body='{"key":"real"}'`

#### Scenario: Placeholder in headers arg is resolved

- **WHEN** `execute("http_post", {"url": "https://x.com", "body": "{}", "headers": '{"Authorization":"Bearer ${TOKEN}"}'}, secrets=SecretsStore({"TOKEN": "tok123"}))`
- **THEN** the tool receives `headers='{"Authorization":"Bearer tok123"}'`

#### Scenario: Log records pre-interpolation args

- **WHEN** `execute()` is called with `{"url": "https://x.com?key=${API_KEY}"}` and a SecretsStore
- **THEN** the `tool_call_start` log entry contains `"url": "https://x.com?key=${API_KEY}"` (placeholder, not resolved value)

#### Scenario: No secrets — behaviour unchanged

- **WHEN** `execute()` is called with `secrets=None`
- **THEN** args are passed to validators and the tool function without any interpolation step

#### Scenario: Non-string args are not interpolated

- **WHEN** `execute()` is called with an integer or dict arg and a SecretsStore
- **THEN** the non-string arg is passed to the tool unchanged

### Requirement: run() accepts and forwards SecretsStore

`run()` SHALL accept an optional `secrets: SecretsStore | None` parameter (default `None`).
It SHALL pass `secrets` to every `registry.execute()` call within the loop.
When `secrets` is not `None`, it SHALL call `scrub.register_runtime_secrets(secrets.values())` once before the loop starts so resolved values are masked in all subsequent log output.

#### Scenario: Secrets registered with scrubber before loop

- **WHEN** `run()` is called with a `SecretsStore` containing `{"KEY": "supersecret"}`
- **THEN** `"supersecret"` is masked as `"***"` in any subsequent log entry

#### Scenario: run() without secrets — no change in behaviour

- **WHEN** `run()` is called with `secrets=None`
- **THEN** no interpolation occurs and no runtime secrets are registered with the scrubber
