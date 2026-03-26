## ADDED Requirements

### Requirement: ask_human builtin tool

The system SHALL provide a builtin tool named `ask_human` that the LLM can call to pause execution and request human input. The tool SHALL accept three parameters: `question` (str, required), `type` (str, one of "confirm"/"text"/"select", default "text"), `choices` (list of strings, required when type="select", omitted otherwise).

#### Scenario: Tool is callable by the LLM with confirm type

- **WHEN** the LLM issues a tool call `ask_human(question="Delete the file?", type="confirm")`
- **THEN** the tool dispatches to the active handler and returns "yes" or "no" as a string

#### Scenario: Tool is callable with text type

- **WHEN** the LLM issues `ask_human(question="Enter the API key", type="text")`
- **THEN** the tool returns the human-entered string

#### Scenario: Tool is callable with select type

- **WHEN** the LLM issues `ask_human(question="Which environment?", type="select", choices=["dev","staging","prod"])`
- **THEN** the tool returns the selected choice string

#### Scenario: Missing choices for select raises ValueError

- **WHEN** the LLM calls `ask_human(type="select")` without `choices`
- **THEN** the tool raises `ValueError` with a descriptive message before calling the handler

### Requirement: ask_human dispatches to active HITLHandler

The tool implementation SHALL call `get_hitl_handler().ask(request)` where `request` is constructed from the tool arguments. The tool result returned to the LLM SHALL be the string returned by the handler.

#### Scenario: Handler response becomes tool result

- **WHEN** the registered handler returns "staging" for a select prompt
- **THEN** the tool result appended to the conversation is the string "staging"

#### Scenario: Handler exception propagates as tool error

- **WHEN** the handler raises an exception (e.g. user pressed Ctrl+C)
- **THEN** the exception propagates out of `registry.execute()` and is not silently swallowed
