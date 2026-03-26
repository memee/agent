## 1. Dependencies & Setup

- [x] 1.1 Add `questionary` to `pyproject.toml` dependencies and run `uv sync`

## 2. Core HITL Module

- [x] 2.1 Create `src/agent/hitl.py` with `HITLRequest` dataclass and `HITLHandler` Protocol
- [x] 2.2 Add `_hitl_handler_var: ContextVar` and `get_hitl_handler()` function in `hitl.py`
- [x] 2.3 Implement `TerminalHITLHandler` in `hitl.py` using `questionary` for confirm/text/select
- [x] 2.4 Add structured logging (`hitl_request` / `hitl_response`) in `TerminalHITLHandler.ask()`

## 3. ask_human Tool

- [x] 3.1 Create `src/agent/builtin_tools/ask_human.py` with the `@tool` decorated `ask_human` function
- [x] 3.2 Validate that `choices` is provided when `type="select"`, raise `ValueError` otherwise
- [x] 3.3 Dispatch to `get_hitl_handler().ask(request)` and return the result string

## 4. Integration with run()

- [x] 4.1 Add `hitl_handler: HITLHandler | None = None` kwarg to `run()` and `_run_in_context()`
- [x] 4.2 Set the context variable in `_run_in_context()` before the loop when handler is provided

## 5. Exports

- [x] 5.1 Export `HITLHandler`, `HITLRequest`, `TerminalHITLHandler`, `get_hitl_handler` from `src/agent/__init__.py`

## 6. Tests

- [x] 6.1 Test `HITLRequest` dataclass construction and field access
- [x] 6.2 Test `get_hitl_handler()` returns `TerminalHITLHandler` when no handler registered
- [x] 6.3 Test `get_hitl_handler()` returns the registered handler when one is set via context
- [x] 6.4 Test `ask_human` tool raises `ValueError` when `type="select"` and `choices` is missing
- [x] 6.5 Test `ask_human` tool calls handler and returns its response (stub handler)
- [x] 6.6 Test sub-agent inherits parent's HITL handler via `copy_context` in `run()`
