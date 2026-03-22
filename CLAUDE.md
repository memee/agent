# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

A minimal Python agent framework (`src/agent/`) built for AI Devs 4 course
tasks. It provides a tool-call loop, sandbox enforcement, subagent delegation,
and structured logging on top of the OpenAI-compatible API.

## Commands

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_registry.py

# Run a single test by name
uv run pytest tests/test_registry.py::test_execute_calls_tool

# Lint
uv run ruff check src/ tests/
```

Python version: 3.14 (see `.python-version`). Venv is at `.venv/`.

## Architecture

### Core loop

`run(messages, client, model, registry, sandbox)` in `run.py` drives the
tool-call cycle. It:

1. Calls the LLM via OpenAI client
2. Appends the assistant message to `Conversation`
3. Executes each `tool_call` through `registry.execute()`
4. Appends each tool result back to the conversation
5. Repeats until no tool calls or `max_iterations` exceeded

Each `run()` call isolates context variables via `copy_context()` so nested
subagent calls don't pollute the parent's context.

### Tool registration

`tool.py` — `@tool` decorator only annotates the function with `_tool_meta`; it
does **not** register it.

`registry.py` — `ToolsRegistry.include(module_or_package)` scans a
module/package for `_tool_meta`-annotated functions and registers them.
`registry.execute()` applies validators, injects `sandbox` if the function
signature accepts it, then calls the function.

`__init__.py` creates a global `tools` instance and calls
`tools.include("agent.builtin_tools")`.

### Sandbox

Two sandbox types: `HttpSandbox` (block private IPs, allowed_hosts, timeout, max
bytes) and `FileSandbox` (base_dir, blocked_paths, max bytes). Both support
`.default()`, `.strict()`, `.off()` presets. `SandboxConfig` groups them and is
passed through `run()` to `registry.execute()`.

Validators (`validators.py`) receive the domain-specific sandbox object.
`domain` on `@tool` controls which sandbox sub-object is routed: `"http"` →
`sandbox.http`, `"filesystem"` → `sandbox.filesystem`.

**Known limitation**: tools needing both domains (e.g. `http_download`) must
call validators manually inside the function body — see TODOs in README.

### Subagents / profiles

Profiles live in `src/agent/subagents/*.md` with YAML frontmatter:

```yaml
---
name: researcher
description: ...
model: gpt-4o-mini
tools: [ http_get, read_file ]
sandbox:
  http: { preset: strict }
  filesystem: { preset: strict, base_dir: "./workspace" }
---
System prompt body here
```

`profile.py` parses these into `AgentProfile` objects via
`AgentProfileRegistry` (module-level singleton `profile_registry`).
`build_system_prompt(base, registry)` appends an `## Available Sub-agents`
section for orchestrators. The `delegate` builtin tool runs a subagent by
profile name using the same `run()` loop.

### Schema generation

`schema.py` converts a function's type hints + docstring into an OpenAI tool
schema. The `sandbox` parameter is excluded from the schema (it's injected by
the registry, not supplied by the LLM). Only `str/int/float/bool` are mapped;
everything else defaults to `"string"`.

### Logging / context

`logging.py` configures JSON-structured logging to `agent.log`. `context.py`
tracks `agent_name`, `run_id`, and `iteration` as `contextvars`. All log entries
from `run.py` and `registry.py` include these via a custom `LoggingFilter`.

## Environment variables

```
AI_PROVIDER=openai          # or: openrouter
AI_PROVIDER_API_KEY=sk-...  # falls back to OPENAI_API_KEY
VISION_MODEL=gpt-4o         # model used by analyze_image (default: gpt-4o)
AGENT_SCRUB_SECRETS=val1,val2  # comma-separated literal secrets to mask in logs as ***
```

## openspec/

Design artifacts (specs, change proposals, archive) for the framework's own
evolution. Not production code. Use `opsx:*` skills to work with them.
