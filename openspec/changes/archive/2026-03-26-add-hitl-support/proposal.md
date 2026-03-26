## Why

Agents sometimes need a human decision — approval, clarification, or a choice — before continuing. Without HITL support the agent either guesses or halts; with it, the loop can pause, surface the question in the terminal, and resume with the human's answer.

## What Changes

- Add a `ask_human` builtin tool the LLM can call when it needs human input (confirmation, free-text, or a choice from a list).
- Add a pluggable `HITLHandler` protocol so the caller can swap in any interaction backend (terminal, web, test stub).
- Provide a default terminal handler using `questionary` for rich prompts (yes/no, text, select).
- Register the active handler via a context variable so nested/sub-agent calls inherit it automatically.

## Capabilities

### New Capabilities

- `hitl-handler`: Registry and protocol for pluggable human-in-the-loop backends — registration, lookup, context propagation.
- `ask-human-tool`: Builtin `ask_human` tool — schema, dispatch to active handler, result injection back into the conversation.
- `terminal-hitl-handler`: Default terminal handler using `questionary` — yes/no confirmation, free-text, and select-from-list prompt types.

### Modified Capabilities

<!-- No existing spec-level behavior changes -->

## Impact

- **New files**: `src/agent/hitl.py` (protocol + context var + default handler), `src/agent/builtin_tools/ask_human.py`
- **`run.py`**: Accept optional `hitl_handler` kwarg; store it in context before the loop.
- **`__init__.py`**: Export `HITLHandler`, `register_hitl_handler`, `TerminalHITLHandler`.
- **New dependency**: `questionary` (terminal prompts).
- No breaking changes to existing `run()` callers — handler defaults to `TerminalHITLHandler`.
