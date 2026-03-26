## ADDED Requirements

### Requirement: HITLHandler protocol

The system SHALL define a `HITLHandler` protocol (structural subtype) with a single method `ask(request: HITLRequest) -> str`. Any object implementing this method is a valid handler. `HITLRequest` is a dataclass carrying: `type` (Literal["confirm", "text", "select"]), `question` (str), `choices` (list[str] | None).

#### Scenario: Protocol is satisfied by any callable object

- **WHEN** an object has a method `ask(request: HITLRequest) -> str`
- **THEN** it is accepted wherever `HITLHandler` is expected without inheritance

#### Scenario: HITLRequest carries type, question, and optional choices

- **WHEN** the system constructs a `HITLRequest` with type="select", question="Pick one", choices=["a","b"]
- **THEN** all three fields are accessible on the resulting object

### Requirement: Context-variable handler storage

The system SHALL store the active `HITLHandler` in a `contextvars.ContextVar` named `_hitl_handler_var`. `run()` SHALL accept an optional `hitl_handler: HITLHandler | None` kwarg and, when provided, set the context variable before entering the loop.

#### Scenario: Handler set via run() is visible inside the loop

- **WHEN** `run()` is called with `hitl_handler=my_handler`
- **THEN** `get_hitl_handler()` returns `my_handler` during that run

#### Scenario: Sub-agent inherits parent handler via copy_context

- **WHEN** a sub-agent is spawned inside a run where `hitl_handler` was set
- **THEN** `get_hitl_handler()` inside the sub-agent returns the same handler

#### Scenario: No handler set returns default TerminalHITLHandler

- **WHEN** `run()` is called without `hitl_handler`
- **THEN** `get_hitl_handler()` returns a `TerminalHITLHandler` instance

### Requirement: Handler lookup function

The system SHALL expose `get_hitl_handler() -> HITLHandler` that reads the context variable and returns `TerminalHITLHandler()` as the default when none is set.

#### Scenario: Returns context-local handler

- **WHEN** the context variable holds a custom handler
- **THEN** `get_hitl_handler()` returns that handler without constructing a new one
