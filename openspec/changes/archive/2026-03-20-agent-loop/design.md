## Context

The library has `ToolsRegistry` (decorator-based tool registration) and
`function_to_tool_schema` (auto-generates OpenAI schemas). The missing piece
is the runtime: something that feeds these schemas to an LLM and acts on the
responses.

The AI Devs 4 course materials identify two core inter-agent primitives:
`delegate` (run a sub-agent, get its result as a tool return value) and
`message` (bidirectional pause-and-resume). This change delivers the loop
and `delegate`; `message` is deferred.

## Goals / Non-Goals

**Goals:**

- `Conversation` — typed wrapper around the list-of-dicts message format
- `run()` — synchronous tool-call loop with configurable iteration cap
- `delegate` built-in tool — Orchestrator pattern via sub-agent as tool call
- Clean separation: loop knows nothing about which LLM client is used (receives
  an `openai.OpenAI`-compatible client as a parameter)

**Non-Goals:**

- Async execution
- `message` tool (bidirectional pause) — future change
- Streaming
- Persistent memory / long-term context — separate concern
- Retry / error recovery beyond the iteration limit

## Decisions

### Conversation as a plain list wrapper

`Conversation` holds `list[dict]` internally and exposes typed `add_*` methods.
It does not own any LLM logic.

**Rationale**: The OpenAI API expects a plain list; keeping `Conversation`
as a thin wrapper makes it trivially serialisable and easy to inspect.

### `run()` as a free function, not a class

```python
def run(
    messages: Conversation,
    client: openai.OpenAI,
    model: str,
    tools: list[dict] | None = None,
    max_iterations: int = 10,
) -> str:
    ...
```

**Rationale**: Stateless function is easier to test and compose. State lives
in `Conversation`, which the caller owns.

**Alternative considered**: `Agent` class with `__call__` — rejected for now;
can be added as a thin wrapper later without changing the loop internals.

### `delegate` as a registered built-in tool

`delegate` is registered in the `"builtin"` group via `@tools.register`.
Internally it calls `run()` with a fresh `Conversation`, a given system prompt,
a (optionally different) model, and a scoped tool group.

```
Orchestrator run()
  └─ tool_call: delegate(system_prompt, task, group, model)
       └─ run(Conversation([system, user=task]), client, model,
              tools=registry.to_openai_schema(group))
            └─ returns final text → tool result back to orchestrator
```

**Rationale**: Sub-agent as tool call is the pattern described in AI Devs 4
course ("Uruchomienie delegate otwiera nowy wątek... Agent po zakończeniu
odpowiada, co staje się wynikiem narzędzia"). Fits naturally into
`ToolsRegistry` without any special loop logic.

### Iteration limit as a safety valve

`run()` raises `RuntimeError` (or returns partial result) after `max_iterations`
tool-call cycles.

**Rationale**: Prevents infinite loops in case the model repeatedly calls tools
without converging. Course materials warn about this failure mode.

## Risks / Trade-offs

- **Nested `run()` depth** → deep delegation chains consume tokens quickly.
  Mitigation: `max_iterations` per level; document recommended depth limit.
- **Shared `ToolsRegistry`** → sub-agent called via `delegate` sees all
  registered tools unless scoped by group. Mitigation: always pass `group`
  to `delegate` to restrict sub-agent's tool set.
- **Synchronous only** → blocking; not suitable for concurrent sub-agents.
  Mitigation: acceptable for course tasks; async is a future change.

## Open Questions

- Should `run()` return the full `Conversation` or just the final string?
  → Final string for simplicity; caller already holds the `Conversation` object.
- Should `delegate` be importable as a standalone tool or only auto-registered?
  → Auto-registered on `from agent import tools` import, consistent with
  `hello_world` pattern.
