## ADDED Requirements

### Requirement: Scrub known secret patterns from text

The system SHALL provide a `scrub(text: str) -> str` function that replaces
known secret patterns in a string with masked values. Patterns are applied in
order; all matches are replaced.

Patterns:

- OpenAI-style keys (`sk-` followed by ≥20 alphanumeric/dash/underscore chars)
  SHALL be replaced with `sk-***`
- HTTP Bearer tokens (`Bearer` followed by ≥8 non-whitespace chars) SHALL be
  replaced with `Bearer ***`
- JSON/query-string fields named `api_key`, `api-key`, `apikey`, `token`,
  `password`, or `secret` (preceded by `"`, `?`, `&`) followed by `:`, `=`,
  or whitespace and a value ≥4 chars SHALL have their value replaced with `***`

#### Scenario: OpenAI key in plain text

- **WHEN** `scrub("key=sk-proj-ABCDEFGHIJKLMNOPQRSTUVwxyz")` is called
- **THEN** it returns `"key=sk-***"`

#### Scenario: Bearer token in Authorization header

- **WHEN** `scrub("Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.payload")` is called
- **THEN** it returns `"Authorization: Bearer ***"`

#### Scenario: api_key in JSON body

- **WHEN** `scrub('{"api_key": "my-secret-value"}')` is called
- **THEN** it returns `'{"api_key": "***"}'`

#### Scenario: No secrets present

- **WHEN** `scrub("hello world")` is called
- **THEN** it returns `"hello world"` unchanged

### Requirement: Scrub explicit secret values from text

The system SHALL read a comma-separated list of literal secret values from the
`AGENT_SCRUB_SECRETS` environment variable and replace any occurrence of these
values in text with `***`. Matching is case-sensitive. When multiple secrets
share a prefix, longer secrets SHALL be matched first to prevent partial masking.

The environment variable SHALL be read once at module import time.

#### Scenario: Explicit secret masked

- **WHEN** `AGENT_SCRUB_SECRETS=mysecretkey123` is set and `scrub("token=mysecretkey123")` is called
- **THEN** it returns `"token=***"`

#### Scenario: Multiple explicit secrets

- **WHEN** `AGENT_SCRUB_SECRETS=abc,abcdef` is set and `scrub("x=abcdef y=abc")` is called
- **THEN** it returns `"x=*** y=***"` (longer match applied first, no partial collision)

#### Scenario: Empty env var

- **WHEN** `AGENT_SCRUB_SECRETS` is not set or empty
- **THEN** no explicit-value scrubbing is applied

### Requirement: Runtime secrets can be registered with the scrubber

The `scrub` module SHALL expose a `register_runtime_secrets(values: list[str]) -> None` function.
It SHALL add each non-empty value to an in-memory runtime list.
Values in this list SHALL be masked to `"***"` by `scrub()` using the same longest-first ordering as `AGENT_SCRUB_SECRETS`.
The runtime list SHALL be separate from the env-var-based `_EXPLICIT` list but applied in the same pass.
The function SHALL be safe to call multiple times; duplicate values SHALL not cause double-masking.

#### Scenario: Runtime secret is masked after registration

- **WHEN** `register_runtime_secrets(["mysecret123"])` is called and then `scrub("token=mysecret123")` is called
- **THEN** returns `"token=***"`

#### Scenario: Registration does not affect env-var secrets

- **WHEN** `register_runtime_secrets(["rt-secret"])` is called
- **THEN** `AGENT_SCRUB_SECRETS`-based masking continues to work unchanged

#### Scenario: Longest-first ordering applies to runtime secrets

- **WHEN** `register_runtime_secrets(["abc", "abcdef"])` is called and `scrub("x=abcdef y=abc")` is called
- **THEN** returns `"x=*** y=***"` (longer match applied first, no partial collision)

#### Scenario: Empty string values are ignored

- **WHEN** `register_runtime_secrets(["", "real-secret"])` is called
- **THEN** only `"real-secret"` is added; empty string does not cause incorrect masking of all text

### Requirement: Scrub filter applies scrubbing to all log record fields

The system SHALL provide a `ScrubFilter(logging.Filter)` that, for every log
record passing through it, applies `scrub()` to:

- `record.msg` (the message template)
- Each element of `record.args` if it is a tuple, or each value if it is a dict
- Every `extra` field on the record that is not a standard `LogRecord` attribute,
  recursively for nested dicts and lists

The filter SHALL return `True` (never suppress records).

#### Scenario: Secret in log message

- **WHEN** `logger.info("key=%s", "sk-proj-ABCDEFGHIJKLMNOPQRSTUVWXYZ123")` is called with `ScrubFilter` active
- **THEN** the emitted log line contains `sk-***` not the original key

#### Scenario: Secret in extra dict field

- **WHEN** `logger.info("tool_call", extra={"tool_args": {"body": '{"api_key":"s3cr3t"}'}})` is called with `ScrubFilter` active
- **THEN** the emitted log line contains `***` in place of `s3cr3t`

#### Scenario: Filter never suppresses records

- **WHEN** any log record passes through `ScrubFilter`
- **THEN** the filter returns `True` and the record is emitted
