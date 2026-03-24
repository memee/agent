## ADDED Requirements

### Requirement: SecretsStore holds named secret values

The library SHALL provide a `SecretsStore` class in `src/agent/secrets.py`.
It SHALL be constructed with a `dict[str, str]` mapping secret names to their values.
It SHALL expose a `get(name: str) -> str | None` method returning the value or `None` if the name is unknown.
It SHALL expose a `values() -> list[str]` method returning all secret values (for scrubber registration).
It SHALL expose a `names() -> list[str]` method returning all secret names (for system prompt injection).

#### Scenario: Known secret is retrieved

- **WHEN** `SecretsStore({"API_KEY": "abc123"}).get("API_KEY")` is called
- **THEN** returns `"abc123"`

#### Scenario: Unknown secret returns None

- **WHEN** `SecretsStore({"API_KEY": "abc123"}).get("MISSING")` is called
- **THEN** returns `None`

#### Scenario: values() returns all secret values

- **WHEN** `SecretsStore({"A": "val1", "B": "val2"}).values()` is called
- **THEN** returns a list containing `"val1"` and `"val2"` (order unspecified)

#### Scenario: names() returns all secret names

- **WHEN** `SecretsStore({"API_KEY": "x", "TOKEN": "y"}).names()` is called
- **THEN** returns a list containing `"API_KEY"` and `"TOKEN"` (order unspecified)

### Requirement: SecretsStore interpolates ${NAME} placeholders in strings

`SecretsStore` SHALL expose an `interpolate(text: str) -> str` method.
It SHALL replace all occurrences of `${NAME}` in `text` with the corresponding secret value.
It SHALL leave `${UNKNOWN}` placeholders unchanged if the name is not in the store.
It SHALL support multiple placeholders in a single string.
It SHALL support the same placeholder appearing more than once.

#### Scenario: Single placeholder is resolved

- **WHEN** `SecretsStore({"KEY": "secret"}).interpolate("value=${KEY}")` is called
- **THEN** returns `"value=secret"`

#### Scenario: Unknown placeholder is preserved

- **WHEN** `SecretsStore({"KEY": "secret"}).interpolate("x=${MISSING}")` is called
- **THEN** returns `"x=${MISSING}"` unchanged

#### Scenario: Multiple different placeholders in one string

- **WHEN** `SecretsStore({"A": "1", "B": "2"}).interpolate("${A}-${B}")` is called
- **THEN** returns `"1-2"`

#### Scenario: Repeated placeholder in one string

- **WHEN** `SecretsStore({"K": "v"}).interpolate("${K}:${K}")` is called
- **THEN** returns `"v:v"`

#### Scenario: String with no placeholders is unchanged

- **WHEN** `SecretsStore({"K": "v"}).interpolate("hello world")` is called
- **THEN** returns `"hello world"` unchanged
