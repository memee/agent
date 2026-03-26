## Context

The agent loop in `run.py` is fully autonomous: once started it runs until the LLM produces a final text response or `max_iterations` is exceeded. Some tasks need a human decision mid-run — e.g. "Should I delete this file?", "Which option do you prefer?", "What is the password?". Without a structured pause mechanism the LLM must guess or refuse, which degrades reliability.

Current state: no HITL primitives exist. The loop and tool registry have no concept of pausing for input.

## Goals / Non-Goals

**Goals:**

- Let the LLM request human input via a normal tool call (`ask_human`).
- Keep the `run()` loop synchronous and unchanged in structure.
- Allow callers to swap the interaction backend (terminal, test stub, web queue).
- Default to a polished terminal experience with questionary.
- Context-propagate the handler so sub-agents inherit it automatically.

**Non-Goals:**

- Async/event-loop HITL (e.g. streaming to a browser with SSE).
- Generators or coroutines-based `run()` redesign.
- Forcing the LLM to always confirm — HITL is opt-in via the tool.
- Textualize/Textual TUI (heavy dependency, no benefit over questionary for now).

## Decisions

### D1 — Tool call, not generator

**Decision**: `ask_human` is a regular builtin tool, not a generator `yield` point in `run()`.

**Rationale**: Converting `run()` to a generator is a breaking API change (all callers must iterate). A tool call keeps the loop untouched. The LLM decides when to ask — it has full context to know when a decision is needed. Callers that never register the tool never see HITL behaviour.

**Alternatives considered**:

- Generator `run()`: clean semantics, but breaks all callers and complicates `copy_context()` isolation.
- Exception-based pause: fragile and abuses Python's exception mechanism.

### D2 — Context-variable handler, not a global

**Decision**: The active `HITLHandler` is stored in a `contextvars.ContextVar`. `run()` accepts an optional `hitl_handler` kwarg and sets it before the loop. Sub-agents created via `delegate` inherit the parent context via `copy_context()`.

**Rationale**: A module-level global would be clobbered by concurrent runs or tests. A context variable gives per-run isolation for free, consistent with how `run_id` and `agent_name` already work.

### D3 — `questionary` for the default terminal handler

**Decision**: Default `TerminalHITLHandler` uses `questionary` for prompts.

**Rationale**: `questionary` provides confirmation, text, and select prompts with keyboard navigation in ~3 lines each. Rich/Textual are heavier and not needed for simple terminal interaction. `input()` alone can't do choice lists without extra code.

**Alternatives considered**:

- `prompt_toolkit` directly: lower-level, more boilerplate.
- Textual TUI: full-screen app — overkill for a mid-run pause.
- Plain `input()`: sufficient for text but no choice-list support.

### D4 — Prompt types: confirm, text, select

**Decision**: `ask_human` accepts a `type` field (`"confirm"`, `"text"`, `"select"`) and an optional `choices` list (required for `"select"`).

**Rationale**: Three types cover the vast majority of HITL scenarios. The LLM learns the schema from the tool definition and can choose the right type. Keeping the surface small reduces prompt complexity.

## Risks / Trade-offs

- **LLM over-asking** → The system prompt for tools that include `ask_human` should instruct the model to use it sparingly. Risk is low in practice because every `ask_human` call costs a round-trip.
- **Blocking in async contexts** → `questionary` uses `input()` under the hood which blocks the thread. Callers running inside `asyncio` must wrap with `loop.run_in_executor`. Documented but not solved here (Non-Goal).
- **Test isolation** → Tests must register a stub `HITLHandler` or the default handler will block waiting for stdin. The `HITLHandler` protocol makes stubs trivial to write.

## Migration Plan

No migration needed. All changes are additive:

1. New files: `hitl.py`, `builtin_tools/ask_human.py`.
2. `run()` gains one optional kwarg; existing call sites are unaffected.
3. `__init__.py` gains new exports.
4. `questionary` is added to `pyproject.toml` dependencies.
