## ADDED Requirements

### Requirement: TerminalHITLHandler default implementation

The system SHALL provide `TerminalHITLHandler`, a concrete `HITLHandler` implementation that renders prompts in the terminal using `questionary`. It SHALL be the default handler returned by `get_hitl_handler()` when no handler is registered.

#### Scenario: confirm prompt renders yes/no question

- **WHEN** the handler receives `HITLRequest(type="confirm", question="Proceed?", choices=None)`
- **THEN** it calls `questionary.confirm("Proceed?")` and returns "yes" or "no"

#### Scenario: text prompt renders free-text input

- **WHEN** the handler receives `HITLRequest(type="text", question="Enter value:", choices=None)`
- **THEN** it calls `questionary.text("Enter value:")` and returns the entered string

#### Scenario: select prompt renders a choice list

- **WHEN** the handler receives `HITLRequest(type="select", question="Pick:", choices=["a","b","c"])`
- **THEN** it calls `questionary.select("Pick:", choices=["a","b","c"])` and returns the selected item

#### Scenario: Unknown type raises ValueError

- **WHEN** the handler receives a request with an unrecognised type
- **THEN** it raises `ValueError` naming the invalid type

### Requirement: TerminalHITLHandler logs interaction

The handler SHALL emit a structured log entry (`hitl_request`) before prompting and another (`hitl_response`) after the human answers, both at INFO level and including `type` and `question` fields.

#### Scenario: Pre-prompt log is emitted

- **WHEN** `ask()` is called
- **THEN** a log record with event="hitl_request" and the question is emitted before the prompt appears

#### Scenario: Post-response log is emitted

- **WHEN** the human provides an answer
- **THEN** a log record with event="hitl_response" is emitted (response value SHALL NOT be logged to avoid leaking secrets)
