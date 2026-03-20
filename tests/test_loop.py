from unittest.mock import MagicMock, patch
import pytest

from agent.conversation import Conversation
from agent.run import run
from agent.registry import ToolsRegistry


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


def test_no_tools_needed():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_text_response("Hello!")
    registry = ToolsRegistry()
    conv = Conversation()
    conv.add_user("Hi")

    result = run(conv, client, "gpt-4o", registry)

    assert result == "Hello!"
    assert client.chat.completions.create.call_count == 1


def test_single_tool_call_resolved():
    registry = ToolsRegistry()

    @registry.register("add")
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _make_tool_call_response("add", {"a": 1, "b": 2}),
        _make_text_response("The answer is 3."),
    ]

    conv = Conversation()
    conv.add_user("What is 1+2?")

    result = run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema())

    assert result == "The answer is 3."
    assert client.chat.completions.create.call_count == 2


def test_iteration_limit_raises():
    registry = ToolsRegistry()

    @registry.register("ping")
    def ping() -> str:
        """Ping."""
        return "pong"

    client = MagicMock()
    client.chat.completions.create.return_value = _make_tool_call_response("ping", {})

    conv = Conversation()
    conv.add_user("Keep going")

    with pytest.raises(RuntimeError, match="3 iterations"):
        run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema(), max_iterations=3)


def test_conversation_mutated_after_run():
    registry = ToolsRegistry()

    @registry.register("echo")
    def echo(msg: str) -> str:
        """Echo."""
        return msg

    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _make_tool_call_response("echo", {"msg": "hi"}, call_id="call_x"),
        _make_text_response("Done."),
    ]

    conv = Conversation()
    conv.add_user("Say hi")
    initial_len = len(conv.messages)

    run(conv, client, "gpt-4o", registry, tools=registry.to_openai_schema())

    # original user msg + assistant tool-call msg + tool result + final assistant
    assert len(conv.messages) == initial_len + 3
    roles = [m["role"] for m in conv.messages]
    assert roles == ["user", "assistant", "tool", "assistant"]
