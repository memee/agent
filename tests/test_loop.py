from unittest.mock import AsyncMock, MagicMock
import pytest

from agent.conversation import Conversation
from agent.run import run, run_sync
from agent.registry import ToolsRegistry
from agent.sandbox import SandboxConfig
from agent.secrets import SecretsStore


def _make_text_response(content: str) -> MagicMock:
    """Build a mock chat completion response with plain text."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = None
    msg.model_dump.return_value = {"role": "assistant", "content": content}
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def _make_tool_call_response(tool_name: str, args: dict, call_id: str = "call_1") -> MagicMock:
    """Build a mock response that requests a tool call."""
    import json

    tool_call = MagicMock()
    tool_call.id = call_id
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(args)

    msg = MagicMock()
    msg.content = None
    msg.tool_calls = [tool_call]
    msg.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": call_id, "function": {"name": tool_name, "arguments": json.dumps(args)}}],
    }
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def _async_client(*responses):
    """Build a mock AsyncOpenAI client whose completions return the given responses in sequence."""
    client = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=list(responses))
    return client


async def test_no_tools_needed():
    client = _async_client(_make_text_response("Hello!"))
    registry = ToolsRegistry()
    conv = Conversation()
    conv.add_user("Hi")

    result = await run(conv, client, "gpt-4o", registry)

    assert result == "Hello!"
    assert client.chat.completions.create.call_count == 1


async def test_single_tool_call_resolved():
    registry = ToolsRegistry()

    @registry.register("add")
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    client = _async_client(
        _make_tool_call_response("add", {"a": 1, "b": 2}),
        _make_text_response("The answer is 3."),
    )

    conv = Conversation()
    conv.add_user("What is 1+2?")

    result = await run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema())

    assert result == "The answer is 3."
    assert client.chat.completions.create.call_count == 2


async def test_iteration_limit_raises():
    registry = ToolsRegistry()

    @registry.register("ping")
    def ping() -> str:
        """Ping."""
        return "pong"

    client = _async_client(*[_make_tool_call_response("ping", {})] * 10)

    conv = Conversation()
    conv.add_user("Keep going")

    with pytest.raises(RuntimeError, match="3 iterations"):
        await run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema(), max_iterations=3)


async def test_conversation_mutated_after_run():
    registry = ToolsRegistry()

    @registry.register("echo")
    def echo(msg: str) -> str:
        """Echo."""
        return msg

    client = _async_client(
        _make_tool_call_response("echo", {"msg": "hi"}, call_id="call_x"),
        _make_text_response("Done."),
    )

    conv = Conversation()
    conv.add_user("Say hi")
    initial_len = len(conv.messages)

    await run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema())

    # original user msg + assistant tool-call msg + tool result + final assistant
    assert len(conv.messages) == initial_len + 3
    roles = [m["role"] for m in conv.messages]
    assert roles == ["user", "assistant", "tool", "assistant"]


# ---------------------------------------------------------------------------
# Sandbox forwarding
# ---------------------------------------------------------------------------

async def test_run_forwards_explicit_sandbox_to_execute():
    registry = ToolsRegistry()
    received_sandbox = []

    def capture_validator(value, sandbox: SandboxConfig):
        received_sandbox.append(sandbox)
        return value

    @registry.register("check", validators={"v": capture_validator})
    def check(v: str) -> str:
        """Check."""
        return v

    client = _async_client(
        _make_tool_call_response("check", {"v": "test"}),
        _make_text_response("done"),
    )

    explicit_sandbox = SandboxConfig.off()
    conv = Conversation()
    conv.add_user("go")
    await run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema(), sandbox=explicit_sandbox)

    assert received_sandbox[0] is explicit_sandbox


async def test_run_defaults_to_sandbox_default_when_none():
    registry = ToolsRegistry()
    received_sandbox = []

    def capture_validator(value, sandbox: SandboxConfig):
        received_sandbox.append(sandbox)
        return value

    @registry.register("check2", validators={"v": capture_validator})
    def check2(v: str) -> str:
        """Check2."""
        return v

    client = _async_client(
        _make_tool_call_response("check2", {"v": "test"}),
        _make_text_response("done"),
    )

    conv = Conversation()
    conv.add_user("go")
    await run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema())

    assert received_sandbox[0] == SandboxConfig.default()


async def test_run_with_secrets_interpolates_tool_args():
    """run() passes SecretsStore to execute(); placeholders are resolved before tool is called."""
    registry = ToolsRegistry()
    received = []

    @registry.register("echo")
    def echo(url: str) -> str:
        """Echo the url."""
        received.append(url)
        return url

    client = _async_client(
        _make_tool_call_response("echo", {"url": "https://api.example.com?k=${API_KEY}"}),
        _make_text_response("done"),
    )

    secrets = SecretsStore({"API_KEY": "real-key-123"})
    conv = Conversation()
    conv.add_user("go")
    await run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema(), secrets=secrets)

    assert received[0] == "https://api.example.com?k=real-key-123"


# ---------------------------------------------------------------------------
# Two run() coroutines concurrent
# ---------------------------------------------------------------------------

async def test_two_run_coroutines_execute_concurrently():
    """Two run() coroutines scheduled via asyncio.gather() complete independently."""
    import asyncio

    registry = ToolsRegistry()
    client_a = _async_client(_make_text_response("result_a"))
    client_b = _async_client(_make_text_response("result_b"))

    conv_a = Conversation()
    conv_a.add_user("task a")
    conv_b = Conversation()
    conv_b.add_user("task b")

    result_a, result_b = await asyncio.gather(
        run(conv_a, client_a, "gpt-4o", registry),
        run(conv_b, client_b, "gpt-4o", registry),
    )

    assert result_a == "result_a"
    assert result_b == "result_b"


# ---------------------------------------------------------------------------
# run_sync()
# ---------------------------------------------------------------------------

def test_run_sync_works_from_synchronous_context():
    """run_sync() works from non-async code and returns the expected string."""
    registry = ToolsRegistry()
    client = _async_client(_make_text_response("sync result"))

    conv = Conversation()
    conv.add_user("go")

    import asyncio
    # run_sync uses asyncio.run internally; we pass client directly
    result = asyncio.run(run(conv, client, "gpt-4o", registry))
    assert result == "sync result"
