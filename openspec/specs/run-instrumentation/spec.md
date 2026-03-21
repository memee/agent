## ADDED Requirements

### Requirement: LLM call metrics logged

The system SHALL log an event after each successful LLM API call within `run()`
containing: model name, duration in milliseconds, prompt_tokens,
completion_tokens, and total_tokens.

#### Scenario: LLM call produces a log record

- **WHEN** `client.chat.completions.create()` returns a response
- **THEN** a log record with event `"llm_call"` is emitted containing: `model`,
  `duration_ms`, `prompt_tokens`, `completion_tokens`, `total_tokens`

#### Scenario: Token counts match API response

- **WHEN** the API response contains a `usage` object
- **THEN** logged token counts exactly match `response.usage.prompt_tokens`,
  `response.usage.completion_tokens`, `response.usage.total_tokens`

#### Scenario: Missing usage does not crash

- **WHEN** the API response has no `usage` field (e.g., streaming or provider
  limitation)
- **THEN** token fields are logged as `None` and no exception is raised

### Requirement: Tool call metrics logged

The system SHALL log two events per tool call in `ToolsRegistry.execute()`: one
before execution (`tool_call_start`) and one after (`tool_call_end`). The end
event SHALL include duration in milliseconds and a truncated result preview.

#### Scenario: Tool call start is logged

- **WHEN** `registry.execute(name, args)` is called
- **THEN** a log record with event `"tool_call_start"` is emitted containing:
  `tool` (name) and `args`

#### Scenario: Tool call end is logged with timing and result

- **WHEN** the tool function returns successfully
- **THEN** a log record with event `"tool_call_end"` is emitted containing:
  `tool`, `duration_ms`, `result_preview` (first 200 chars of `str(result)`)

#### Scenario: Tool call error is logged

- **WHEN** the tool function raises an exception
- **THEN** a log record with event `"tool_call_error"` is emitted at ERROR level
  containing: `tool`, `duration_ms`, `error` (exception message)

### Requirement: Result preview truncated to 200 characters

The system SHALL truncate tool result previews to the first 200 characters of
`str(result)`.

#### Scenario: Long result is truncated

- **WHEN** a tool returns a result whose string representation exceeds 200
  characters
- **THEN** `result_preview` in the log contains exactly the first 200 characters

#### Scenario: Short result is not padded

- **WHEN** a tool returns a result whose string representation is under 200
  characters
- **THEN** `result_preview` contains the full string
