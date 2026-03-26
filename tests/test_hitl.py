import contextvars
from unittest.mock import MagicMock, patch

import pytest

from agent.hitl import (
    HITLRequest,
    TerminalHITLHandler,
    _hitl_handler_var,
    get_hitl_handler,
)


# ─── 6.1 HITLRequest construction ─────────────────────────────────────────────


def test_hitlrequest_fields():
    req = HITLRequest(type="select", question="Pick one", choices=["a", "b"])
    assert req.type == "select"
    assert req.question == "Pick one"
    assert req.choices == ["a", "b"]


def test_hitlrequest_no_choices_default():
    req = HITLRequest(type="text", question="Enter value:")
    assert req.choices is None


# ─── 6.2 get_hitl_handler default ─────────────────────────────────────────────


def test_get_hitl_handler_returns_terminal_by_default():
    # Ensure no handler is set in this context
    token = _hitl_handler_var.set(None)
    try:
        handler = get_hitl_handler()
        assert isinstance(handler, TerminalHITLHandler)
    finally:
        _hitl_handler_var.reset(token)


# ─── 6.3 get_hitl_handler with registered handler ─────────────────────────────


def test_get_hitl_handler_returns_registered_handler():
    stub = MagicMock()
    token = _hitl_handler_var.set(stub)
    try:
        assert get_hitl_handler() is stub
    finally:
        _hitl_handler_var.reset(token)


# ─── 6.4 ask_human raises ValueError without choices for select ────────────────


def test_ask_human_select_without_choices_raises():
    from agent.builtin_tools.ask_human import ask_human

    with pytest.raises(ValueError, match="choices"):
        ask_human(question="Pick?", type="select", choices="")


# ─── 6.5 ask_human dispatches to handler and returns result ───────────────────


def test_ask_human_calls_handler_and_returns_result():
    from agent.builtin_tools.ask_human import ask_human

    stub = MagicMock()
    stub.ask.return_value = "staging"

    token = _hitl_handler_var.set(stub)
    try:
        result = ask_human(question="Which env?", type="select", choices="dev,staging,prod")
    finally:
        _hitl_handler_var.reset(token)

    assert result == "staging"
    stub.ask.assert_called_once()
    req = stub.ask.call_args[0][0]
    assert req.type == "select"
    assert req.question == "Which env?"
    assert req.choices == ["dev", "staging", "prod"]


# ─── 6.6 sub-agent inherits parent HITL handler via copy_context ──────────────


def test_run_hitl_handler_inherited_by_subagent():
    """Verify that copy_context() in run() propagates the handler to nested calls."""
    import json
    from unittest.mock import MagicMock

    from agent.conversation import Conversation
    from agent.registry import ToolsRegistry
    from agent.run import run

    stub_handler = MagicMock()
    stub_handler.ask.return_value = "yes"

    captured: list = []
    registry = ToolsRegistry()

    @registry.register("spy")
    def spy_tool(sandbox=None):
        # Called inside the run() loop — check that the context var is set
        captured.append(_hitl_handler_var.get())
        return "done"

    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "spy"
    tool_call.function.arguments = "{}"

    msg_with_tool = MagicMock()
    msg_with_tool.content = None
    msg_with_tool.tool_calls = [tool_call]
    msg_with_tool.model_dump.return_value = {"role": "assistant", "content": None, "tool_calls": []}

    final_msg = MagicMock()
    final_msg.content = "all done"
    final_msg.tool_calls = None
    final_msg.model_dump.return_value = {"role": "assistant", "content": "all done"}

    def make_response(msg):
        r = MagicMock()
        r.choices = [MagicMock(message=msg)]
        r.usage = MagicMock(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        return r

    client = MagicMock()
    client.chat.completions.create.side_effect = [
        make_response(msg_with_tool),
        make_response(final_msg),
    ]

    messages = Conversation([{"role": "user", "content": "go"}])
    run(messages, client, "gpt-4o-mini", registry, hitl_handler=stub_handler)

    assert len(captured) == 1
    assert captured[0] is stub_handler
