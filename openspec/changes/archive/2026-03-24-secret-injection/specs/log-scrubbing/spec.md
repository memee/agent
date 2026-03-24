## ADDED Requirements

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
