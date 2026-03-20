## 1. Dependency

- [x] 1.1 Add `openai` to `pyproject.toml` and run `uv sync --all-packages`

## 2. Conversation

- [x] 2.1 Create `src/agent/conversation.py` with `Conversation` class
- [x] 2.2 Implement `__init__(system_prompt=None)`, `add_system`, `add_user`,
          `add_assistant`, `add_tool_result`, and `messages` property
- [x] 2.3 Export `Conversation` from `src/agent/__init__.py`
- [x] 2.4 Write tests in `tests/test_conversation.py` covering all roles,
          empty state, and system-prompt constructor

## 3. Agent Loop

- [x] 3.1 Create `src/agent/loop.py` with `run()` function
- [x] 3.2 Implement tool-call cycle: send → inspect `tool_calls` → execute →
          append results → repeat
- [x] 3.3 Implement `max_iterations` guard raising `RuntimeError` on limit
- [x] 3.4 Export `run` from `src/agent/__init__.py`
- [x] 3.5 Write tests in `tests/test_loop.py` using a mock OpenAI client:
          no-tool path, single tool-call path, iteration limit path,
          conversation mutation after run

## 4. Delegate Built-in Tool

- [x] 4.1 Create `src/agent/builtin_tools/delegate.py`
- [x] 4.2 Implement `delegate(system_prompt, task, group, model)` registered
          via `@tools.register("delegate", "builtin")`
- [x] 4.3 Import in `src/agent/builtin_tools/__init__.py` so it auto-registers
- [x] 4.4 Write tests in `tests/test_builtin_tools.py`: delegate appears in
          `tools.names("builtin")`, scoped tool list is passed to nested run
