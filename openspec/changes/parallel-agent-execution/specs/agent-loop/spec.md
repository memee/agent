## MODIFIED Requirements

### Requirement: run() drives the tool-call cycle

`run()` SHALL be an `async def` coroutine accepting a `Conversation`, an `AsyncOpenAI`-compatible client, a `model` string, a `ToolsRegistry`, an optional `tools` list (OpenAI schema format), an optional `sandbox: SandboxConfig | None` parameter (default `None`), and an optional `max_iterations` integer (default 10).

When `sandbox` is `None`, `run()` SHALL use `SandboxConfig.default()`.

It SHALL `await` the LLM API call, and if the response contains `tool_calls`, execute each tool, append the results to the conversation, and repeat.

It SHALL return the final assistant text response as a `str` when the LLM returns a message with no `tool_calls`.

#### Scenario: No tools needed

- **WHEN** `await run()` is called and the LLM responds with plain text on the first call
- **THEN** `run()` returns that text without making additional LLM calls

#### Scenario: Single tool call resolved

- **WHEN** the LLM responds with a `tool_call`, the tool is executed, and the next LLM response is plain text
- **THEN** `run()` returns the final plain text after one tool-call cycle

#### Scenario: Iteration limit reached

- **WHEN** the LLM keeps calling tools and `max_iterations` cycles complete without a final text response
- **THEN** `run()` raises `RuntimeError` with a message indicating the limit was reached

#### Scenario: sandbox forwarded to execute

- **WHEN** `await run()` is called with an explicit `sandbox=SandboxConfig.strict(...)`
- **THEN** each `registry.execute()` call receives that sandbox instance

#### Scenario: sandbox defaults to SandboxConfig.default()

- **WHEN** `await run()` is called without a `sandbox` argument
- **THEN** `registry.execute()` is called with `SandboxConfig.default()`

#### Scenario: Two run() coroutines execute concurrently

- **WHEN** two `run()` coroutines are scheduled via `asyncio.gather()`
- **THEN** both make progress interleaved without one blocking the other during LLM API calls

### Requirement: run() appends all turns to Conversation

`run()` SHALL mutate the passed `Conversation` by appending every assistant message and every tool result so the caller retains the full history after the call.

#### Scenario: History preserved after run

- **WHEN** `await run()` completes after one tool-call cycle
- **THEN** the `Conversation.messages` list contains the original messages plus the assistant tool-call message and the tool result message
