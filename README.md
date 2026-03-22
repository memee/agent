# agent

Minimal Python agent framework with a tool-call loop, sandbox, and subagent
support. Built for AI Devs 4 tasks.

## Architecture

```
run(messages, client, model, registry, sandbox)
  └── tool-call loop
        ├── registry.execute(tool, args, sandbox)   # validates + runs tool
        └── Conversation                             # OpenAI message history
```

**Key modules:**

- `run.py` — main agent loop
- `registry.py` — tool registration and execution; `include()` scans a module/package for `@tool`-annotated functions
- `tool.py` — standalone `@tool` decorator (annotates only, does not register)
- `sandbox.py` — `HttpSandbox` / `FileSandbox` / `SandboxConfig`
- `conversation.py` — message history (text + multimodal)
- `profile.py` — subagent profiles loaded from `subagents/*.md`
- `client.py` — OpenAI-compatible client factory (`AI_PROVIDER`,
  `AI_PROVIDER_API_KEY`)

## Usage

### Basic agent

```python
from agent import Conversation, run, tools
from agent.client import create_client

conv = Conversation("You are a helpful assistant.")
conv.add_user("What is the capital of France?")

result = run(conv, create_client(), "gpt-4o", tools)
print(result)
```

### Custom registry with selective tools

```python
from agent import Conversation, run, ToolsRegistry
from agent.client import create_client

my_tools = ToolsRegistry()
my_tools.include("agent.builtin_tools")   # all builtin tools
# or include a single module:
# my_tools.include("agent.builtin_tools.http_get")

conv = Conversation("You are a helpful assistant.")
conv.add_user("Fetch https://example.com")
result = run(conv, create_client(), "gpt-4o", my_tools)
```

### Custom tool with @tool decorator

```python
from agent import tool, ToolsRegistry

@tool("my_tool", group="custom")
def my_tool(message: str) -> str:
    """Returns the message in uppercase."""
    return message.upper()

my_tools = ToolsRegistry()
my_tools.include(__name__)   # scans this module for @tool-annotated functions
```

### Agent with subagent awareness in system prompt

```python
from agent import Conversation, run, tools
from agent.client import create_client
from agent.profile import build_system_prompt, profile_registry

system_prompt = build_system_prompt("You are an orchestrator.",
                                    profile_registry)
conv = Conversation(system_prompt)
conv.add_user("Research the latest news about AI and summarize.")

result = run(conv, create_client(), "gpt-4o", tools)
```

`build_system_prompt` appends an `## Available Sub-agents` section so the LLM
knows which profiles it can delegate to via the `delegate` tool.

### Custom sandbox

```python
from agent.sandbox import SandboxConfig, HttpSandbox, FileSandbox

sandbox = SandboxConfig(
    http=HttpSandbox(block_private_ips=True, allowed_hosts=["api.example.com"]),
    filesystem=FileSandbox.strict("./workspace"),
)
result = run(conv, create_client(), "gpt-4o", tools, sandbox=sandbox)
```

## Builtin Tools

| Tool             | Domain     | Description                                         |
|------------------|------------|-----------------------------------------------------|
| `http_get`       | http       | GET request → response text                         |
| `http_post`      | http       | POST with JSON body → response text                 |
| `http_download`  | —          | Download binary file to disk → path                 |
| `read_file`      | filesystem | Read text file → content                            |
| `write_file`     | filesystem | Write text file → path                              |
| `analyze_image`  | filesystem | Analyze a local image with a vision LLM → text      |
| `delegate`       | —          | Run subagent by profile name                        |
| `hello_world`    | —          | Smoke-test tool                                     |

## Subagent Profiles

Profiles live in `src/agent/subagents/*.md` — YAML frontmatter + system prompt:

```yaml
---
name: researcher
description: Searches the web and reads documents
model: gpt-4o-mini
tools: [ http_get, read_file ]
sandbox:
  http:
    preset: strict
  filesystem:
    preset: strict
    base_dir: "./workspace"
---
You are a research specialist...
```

The `delegate` tool picks up all profiles automatically on import.

## Environment

```
AI_PROVIDER=openai          # or: openrouter
AI_PROVIDER_API_KEY=sk-...  # falls back to OPENAI_API_KEY
VISION_MODEL=gpt-4o         # model used by analyze_image (default: gpt-4o)
```

## Running Tests

```bash
uv run pytest
```

## TODOs

- [ ] **Per-validator sandbox routing** — `registry.execute()` routes a single
  sandbox object
  (selected by `domain`) to all validators of a tool. Tools that need both
  `HttpSandbox`
  and `FileSandbox` validation (e.g. `http_download`) must bypass the validator
  mechanism
  and call validators manually inside the function body.
  Fix: extend `register()` to accept per-argument domain mappings, e.g.
  `validators={"url": (http_url_validator, "http"), "path": (file_path_validator, "filesystem")}`.
