## Why

The library has a tool registry and schema generation, but nothing that actually
drives a conversation with an LLM. Without a loop, there is no agent — just
isolated utilities. The loop is the core of everything, including future
sub-agent delegation via the `delegate` tool.

## What Changes

- Add `Conversation` class for managing message history (system, user, assistant,
  tool turns)
- Add `run()` function implementing the tool-call cycle: send → inspect →
  execute tools → repeat until final answer or iteration limit
- Add `delegate` built-in tool that runs a nested `Agent` as a sub-agent and
  returns its response as a tool result
- Export `run`, `Conversation` from `src/agent/__init__.py`

## Capabilities

### New Capabilities

- `conversation`: Message history management — adding system/user/assistant/tool
  turns, serialising to the list-of-dicts format expected by the OpenAI API
- `agent-loop`: The `run()` function — sends requests to an LLM, handles
  tool_calls, appends results, iterates until a final text response or a
  configurable max-iterations limit
- `delegate-tool`: Built-in `delegate` tool registered in the `builtin` group —
  accepts a system prompt, tool group, model, and task; spins up a nested `run()`
  call and returns its result; enables the Orchestrator pattern described in the
  AI Devs 4 course materials

### Modified Capabilities

<!-- None -->

## Impact

- New files: `src/agent/conversation.py`, `src/agent/loop.py`,
  `src/agent/builtin_tools/delegate.py`
- `src/agent/__init__.py`: export `Conversation`, `run`
- Depends on: `ToolsRegistry` (already exists), `openai` package (to be added
  as a dependency separately or alongside this change)
- No breaking changes to existing modules
