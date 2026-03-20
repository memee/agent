## ADDED Requirements

### Requirement: Provider selection via environment variable

The system SHALL read `AI_PROVIDER` from the environment to determine which LLM provider to use. When `AI_PROVIDER` is not set, it SHALL default to `openai`.

#### Scenario: Default provider is openai

- **WHEN** `AI_PROVIDER` is not set
- **THEN** `create_client()` returns a client configured for `https://api.openai.com/v1`

#### Scenario: OpenRouter provider selected

- **WHEN** `AI_PROVIDER=openrouter`
- **THEN** `create_client()` returns a client configured for `https://openrouter.ai/api/v1`

#### Scenario: Unknown provider raises error

- **WHEN** `AI_PROVIDER` is set to an unrecognised value (e.g. `anthropic`)
- **THEN** `create_client()` raises `ValueError` with a message listing supported providers

### Requirement: API key resolution

The system SHALL read the API key from `AI_PROVIDER_API_KEY`. When `AI_PROVIDER_API_KEY` is not set, it SHALL fall back to `OPENAI_API_KEY`.

#### Scenario: AI_PROVIDER_API_KEY takes precedence

- **WHEN** both `AI_PROVIDER_API_KEY` and `OPENAI_API_KEY` are set
- **THEN** `create_client()` uses the value of `AI_PROVIDER_API_KEY`

#### Scenario: Fallback to OPENAI_API_KEY

- **WHEN** `AI_PROVIDER_API_KEY` is not set and `OPENAI_API_KEY` is set
- **THEN** `create_client()` uses the value of `OPENAI_API_KEY`

### Requirement: Client is OpenAI SDK compatible

`create_client()` SHALL return an `openai.OpenAI` instance so it can be passed directly to `run()` without any changes to the agent loop.

#### Scenario: Returned client is usable by run()

- **WHEN** `create_client()` is called with valid env vars
- **THEN** the returned object is an `openai.OpenAI` instance accepted by `run()`
