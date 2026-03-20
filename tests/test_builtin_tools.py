from unittest.mock import MagicMock, patch

from agent import tools


def test_delegate_registered_in_builtin():
    assert "delegate" in tools.names("builtin")


def test_delegate_in_openai_schema():
    schemas = tools.to_openai_schema("builtin")
    assert any(s["function"]["name"] == "delegate" for s in schemas)


def test_delegate_uses_scoped_tools(monkeypatch):
    """delegate should call run() with only the tools from the given group."""
    from agent.builtin_tools import delegate as delegate_module

    captured = {}

    def fake_run(conv, client, model, registry, tools=None, max_iterations=10):
        captured["tools"] = tools
        return "done"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "openai", MagicMock())

    tools.execute("delegate", {
        "system_prompt": "You are a helper.",
        "task": "Do something.",
        "group": "builtin",
        "model": "gpt-4o-mini",
    })

    # Only builtin-group tools should be passed
    assert captured["tools"] is not None
    names_passed = [t["function"]["name"] for t in captured["tools"]]
    assert "delegate" in names_passed


def test_hello_world_registered():
    assert "hello_world" in tools.names()


def test_hello_world_default():
    assert tools.execute("hello_world", {}) == "Hello, World!"


def test_hello_world_with_name():
    assert tools.execute("hello_world", {"name": "Agent"}) == "Hello, Agent!"


def test_hello_world_in_builtin_group():
    assert "hello_world" in tools.names("builtin")


def test_hello_world_schema():
    schemas = tools.to_openai_schema("builtin")
    assert any(s["function"]["name"] == "hello_world" for s in schemas)
