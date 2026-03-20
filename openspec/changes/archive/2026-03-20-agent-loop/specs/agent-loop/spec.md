## ADDED Requirements

### Requirement: run() drives the tool-call cycle

`run()` SHALL accept a `Conversation`, an `openai.OpenAI`-compatible client,
a `model` string, an optional `tools` list (OpenAI schema format), and an
optional `max_iterations` integer (default 10).

It SHALL send the conversation to the LLM, and if the response contains
`tool_calls`, execute each tool via `ToolsRegistry.execute()`, append the
results to the conversation, and repeat.

It SHALL return the final assistant text response as a `str` when the LLM
returns a message with no `tool_calls`.

#### Scenario: No tools needed

- **WHEN** `run()` is called and the LLM responds with plain text on the first call
- **THEN** `run()` returns that text without making additional LLM calls

#### Scenario: Single tool call resolved

- **WHEN** the LLM responds with a `tool_call`, the tool is executed, and the
  next LLM response is plain text
- **THEN** `run()` returns the final plain text after one tool-call cycle

#### Scenario: Iteration limit reached

- **WHEN** the LLM keeps calling tools and `max_iterations` cycles complete
  without a final text response
- **THEN** `run()` raises `RuntimeError` with a message indicating the limit
  was reached

### Requirement: run() appends all turns to Conversation

`run()` SHALL mutate the passed `Conversation` by appending every assistant
message and every tool result so the caller retains the full history after
the call.

#### Scenario: History preserved after run

- **WHEN** `run()` completes after one tool-call cycle
- **THEN** the `Conversation.messages` list contains the original messages plus
  the assistant tool-call message and the tool result message
