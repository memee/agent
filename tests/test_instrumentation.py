"""Tests for run() and registry.execute() instrumentation."""
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.conversation import Conversation
from agent.registry import ToolsRegistry
from agent.run import run


class _LogCapture(logging.Handler):
    """Simple log handler that collects records."""

    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

    def messages(self) -> list[str]:
        return [r.getMessage() for r in self.records]


def _make_text_response(content: str, usage=None) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = None
    msg.model_dump.return_value = {"role": "assistant", "content": content}
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


def _make_tool_call_response(tool_name: str, args: dict, call_id: str = "call_1") -> MagicMock:
    import json as _json

    tool_call = MagicMock()
    tool_call.id = call_id
    tool_call.function.name = tool_name
    tool_call.function.arguments = _json.dumps(args)

    msg = MagicMock()
    msg.content = None
    msg.tool_calls = [tool_call]
    msg.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": call_id, "function": {"name": tool_name, "arguments": _json.dumps(args)}}],
    }
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    response.usage = None
    return response


# ---------------------------------------------------------------------------
# 7.5 — run() emits "llm_call" log with correct fields
# ---------------------------------------------------------------------------

async def test_run_emits_llm_call_log():
    capture = _LogCapture()
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(capture)
    agent_logger.setLevel(logging.DEBUG)

    try:
        usage = MagicMock()
        usage.prompt_tokens = 10
        usage.completion_tokens = 5
        usage.total_tokens = 15

        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=_make_text_response("Hello!", usage=usage))

        registry = ToolsRegistry()
        conv = Conversation()
        conv.add_user("Hi")

        await run(conv, client, "gpt-4o", registry)

        llm_records = [r for r in capture.records if r.getMessage() == "llm_call"]
        assert len(llm_records) == 1, f"Expected 1 llm_call, got {len(llm_records)}"

        rec = llm_records[0]
        assert rec.__dict__["model"] == "gpt-4o"
        assert "duration_ms" in rec.__dict__
        assert rec.__dict__["prompt_tokens"] == 10
        assert rec.__dict__["completion_tokens"] == 5
        assert rec.__dict__["total_tokens"] == 15
    finally:
        agent_logger.removeHandler(capture)


async def test_run_llm_call_log_missing_usage():
    """When response.usage is None, token fields are logged as None."""
    capture = _LogCapture()
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(capture)
    agent_logger.setLevel(logging.DEBUG)

    try:
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=_make_text_response("Hi", usage=None))

        registry = ToolsRegistry()
        conv = Conversation()
        conv.add_user("Hi")

        await run(conv, client, "gpt-4o", registry)

        llm_records = [r for r in capture.records if r.getMessage() == "llm_call"]
        assert len(llm_records) == 1

        rec = llm_records[0]
        assert rec.__dict__["prompt_tokens"] is None
        assert rec.__dict__["completion_tokens"] is None
        assert rec.__dict__["total_tokens"] is None
    finally:
        agent_logger.removeHandler(capture)


# ---------------------------------------------------------------------------
# 7.6 — registry.execute() emits start/end/error events
# ---------------------------------------------------------------------------

def test_registry_execute_emits_start_and_end():
    capture = _LogCapture()
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(capture)
    agent_logger.setLevel(logging.DEBUG)

    try:
        registry = ToolsRegistry()

        @registry.register("greet")
        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        registry.execute("greet", {"name": "World"})

        msgs = capture.messages()
        assert "tool_call_start" in msgs
        assert "tool_call_end" in msgs

        start_rec = next(r for r in capture.records if r.getMessage() == "tool_call_start")
        end_rec = next(r for r in capture.records if r.getMessage() == "tool_call_end")

        assert start_rec.__dict__["tool"] == "greet"
        assert start_rec.__dict__["tool_args"] == {"name": "World"}

        assert end_rec.__dict__["tool"] == "greet"
        assert "duration_ms" in end_rec.__dict__
        assert end_rec.__dict__["result_preview"] == "Hello, World!"
    finally:
        agent_logger.removeHandler(capture)


def test_registry_execute_emits_error_and_reraises():
    capture = _LogCapture()
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(capture)
    agent_logger.setLevel(logging.DEBUG)

    try:
        registry = ToolsRegistry()

        @registry.register("boom")
        def boom() -> str:
            """Always fails."""
            raise ValueError("kaboom")

        with pytest.raises(ValueError, match="kaboom"):
            registry.execute("boom", {})

        error_records = [r for r in capture.records if r.getMessage() == "tool_call_error"]
        assert len(error_records) == 1
        rec = error_records[0]
        assert rec.__dict__["tool"] == "boom"
        assert "duration_ms" in rec.__dict__
        assert "kaboom" in rec.__dict__["error"]
    finally:
        agent_logger.removeHandler(capture)


def test_registry_execute_result_preview_truncated():
    capture = _LogCapture()
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(capture)
    agent_logger.setLevel(logging.DEBUG)

    try:
        registry = ToolsRegistry()

        @registry.register("long_result")
        def long_result() -> str:
            """Returns a long string."""
            return "x" * 500

        registry.execute("long_result", {})

        end_rec = next(r for r in capture.records if r.getMessage() == "tool_call_end")
        assert len(end_rec.__dict__["result_preview"]) == 200
    finally:
        agent_logger.removeHandler(capture)
