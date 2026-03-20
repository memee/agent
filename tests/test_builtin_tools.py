from unittest.mock import MagicMock, patch

import pytest

from agent import tools
from agent.sandbox import FileSandbox, HttpSandbox, SandboxConfig


def test_delegate_registered_in_builtin():
    assert "delegate" in tools.names("builtin")


def test_delegate_in_openai_schema():
    schemas = tools.to_openai_schema("builtin")
    assert any(s["function"]["name"] == "delegate" for s in schemas)


def test_delegate_uses_profile_tools(monkeypatch):
    """delegate should call run() with only the tools listed in the profile."""
    from agent.builtin_tools import delegate as delegate_module

    captured = {}

    def fake_run(conv, client, model, registry, tools=None, sandbox=None, max_iterations=10):
        captured["tools"] = tools
        captured["model"] = model
        return "done"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "openai", MagicMock())

    tools.execute("delegate", {
        "profile": "researcher",
        "task": "Find information about Python.",
    })

    # Only researcher profile tools should be passed
    assert captured["tools"] is not None
    names_passed = [t["function"]["name"] for t in captured["tools"]]
    assert "http_get" in names_passed
    assert "read_file" in names_passed
    assert "delegate" not in names_passed  # delegate is not in researcher profile


def test_delegate_uses_profile_model(monkeypatch):
    """delegate should use the model from the profile."""
    from agent.builtin_tools import delegate as delegate_module

    captured = {}

    def fake_run(conv, client, model, registry, tools=None, sandbox=None, max_iterations=10):
        captured["model"] = model
        return "done"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "openai", MagicMock())

    tools.execute("delegate", {"profile": "researcher", "task": "some task"})
    assert captured["model"] == "gpt-4o-mini"


# Task 5.5: delegate schema reflects loaded profiles
def test_delegate_schema_profile_enum_matches_registry():
    """delegate tool schema 'profile' enum contains exactly the loaded profile names."""
    from agent.profile import profile_registry

    schemas = tools.to_openai_schema("builtin")
    delegate_schema = next(s for s in schemas if s["function"]["name"] == "delegate")
    profile_param = delegate_schema["function"]["parameters"]["properties"]["profile"]

    assert "enum" in profile_param
    assert set(profile_param["enum"]) == set(profile_registry.names())


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


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------

def test_read_file_registered():
    assert "read_file" in tools.names("builtin")


def test_read_file_happy_path(tmp_path):
    target = tmp_path / "hello.txt"
    target.write_text("hello world")
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]))
    result = tools.execute("read_file", {"path": str(target)}, sandbox=sandbox)
    assert result == "hello world"


def test_read_file_size_limit_rejected(tmp_path):
    target = tmp_path / "big.txt"
    target.write_bytes(b"x" * 100)
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[], max_file_bytes=50))
    with pytest.raises(ValueError, match="50"):
        tools.execute("read_file", {"path": str(target)}, sandbox=sandbox)


def test_read_file_blocked_path_raises(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=abc")
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[".env"]))
    with pytest.raises(PermissionError):
        tools.execute("read_file", {"path": str(env_file)}, sandbox=sandbox)


# ---------------------------------------------------------------------------
# http_get
# ---------------------------------------------------------------------------

def test_http_get_registered():
    assert "http_get" in tools.names("builtin")


def test_http_get_happy_path():
    import httpx

    mock_response = MagicMock()
    mock_response.text = "<html>ok</html>"
    mock_response.content = b"<html>ok</html>"

    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=False))
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = tools.execute("http_get", {"url": "https://example.com"}, sandbox=sandbox)

    assert result == "<html>ok</html>"


def test_http_get_private_ip_blocked():
    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=True))
    with pytest.raises(PermissionError):
        tools.execute("http_get", {"url": "http://192.168.1.100/page"}, sandbox=sandbox)


def test_http_get_size_limit_rejected():
    import httpx

    big_content = b"x" * 1000
    mock_response = MagicMock()
    mock_response.text = "x" * 1000
    mock_response.content = big_content

    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=False, max_response_bytes=500))
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(ValueError, match="500"):
            tools.execute("http_get", {"url": "https://example.com"}, sandbox=sandbox)


def test_http_get_timeout():
    import httpx

    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=False))
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.TimeoutException("timeout")
        mock_client_cls.return_value = mock_client

        with pytest.raises(TimeoutError):
            tools.execute("http_get", {"url": "https://slow.example.com"}, sandbox=sandbox)
