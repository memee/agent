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

    def fake_run(conv, client, model, registry, tools=None, sandbox=None, max_iterations=10, **kwargs):
        captured["tools"] = tools
        captured["model"] = model
        return "done"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "create_client", MagicMock())

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

    def fake_run(conv, client, model, registry, tools=None, sandbox=None, max_iterations=10, **kwargs):
        captured["model"] = model
        return "done"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "create_client", MagicMock())

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


# ---------------------------------------------------------------------------
# http_post
# ---------------------------------------------------------------------------

def test_http_post_registered():
    assert "http_post" in tools.names("builtin")


def test_http_post_happy_path():
    import httpx

    mock_response = MagicMock()
    mock_response.text = '{"status": "ok"}'
    mock_response.content = b'{"status": "ok"}'

    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=False))
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = tools.execute(
            "http_post",
            {"url": "https://example.com/api", "body": '{"key": "value"}'},
            sandbox=sandbox,
        )

    assert result == '{"status": "ok"}'
    mock_client.post.assert_called_once_with("https://example.com/api", json={"key": "value"}, headers={})


def test_http_post_invalid_json_raises_before_request():
    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=False))
    with patch("httpx.Client") as mock_client_cls:
        with pytest.raises(ValueError, match="not valid JSON"):
            tools.execute(
                "http_post",
                {"url": "https://example.com/api", "body": "not json"},
                sandbox=sandbox,
            )
        mock_client_cls.assert_not_called()


def test_http_post_private_ip_blocked():
    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=True))
    with pytest.raises(PermissionError):
        tools.execute(
            "http_post",
            {"url": "http://192.168.1.100/api", "body": "{}"},
            sandbox=sandbox,
        )


def test_http_post_size_limit_rejected():
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
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(ValueError, match="500"):
            tools.execute(
                "http_post",
                {"url": "https://example.com/api", "body": "{}"},
                sandbox=sandbox,
            )


def test_http_post_timeout():
    import httpx

    sandbox = SandboxConfig(http=HttpSandbox(block_private_ips=False))
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.TimeoutException("timeout")
        mock_client_cls.return_value = mock_client

        with pytest.raises(TimeoutError):
            tools.execute(
                "http_post",
                {"url": "https://slow.example.com/api", "body": "{}"},
                sandbox=sandbox,
            )


# ---------------------------------------------------------------------------
# http_download
# ---------------------------------------------------------------------------

def test_http_download_registered():
    assert "http_download" in tools.names("builtin")


def test_http_download_saves_file(tmp_path):
    dest = tmp_path / "image.png"
    file_content = b"\x89PNG\r\n\x1a\n"  # PNG magic bytes

    mock_response = MagicMock()
    mock_response.content = file_content

    sandbox = SandboxConfig(
        http=HttpSandbox(block_private_ips=False),
        filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]),
    )
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = tools.execute(
            "http_download",
            {"url": "https://example.com/image.png", "path": str(dest)},
            sandbox=sandbox,
        )

    assert dest.read_bytes() == file_content
    assert result == str(dest)


def test_http_download_creates_parent_dirs(tmp_path):
    dest = tmp_path / "subdir" / "nested" / "image.png"
    mock_response = MagicMock()
    mock_response.content = b"data"

    sandbox = SandboxConfig(
        http=HttpSandbox(block_private_ips=False),
        filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]),
    )
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        tools.execute(
            "http_download",
            {"url": "https://example.com/image.png", "path": str(dest)},
            sandbox=sandbox,
        )

    assert dest.exists()


def test_http_download_overwrites_existing_file(tmp_path):
    dest = tmp_path / "image.png"
    dest.write_bytes(b"old content")

    mock_response = MagicMock()
    mock_response.content = b"new content"

    sandbox = SandboxConfig(
        http=HttpSandbox(block_private_ips=False),
        filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]),
    )
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        tools.execute(
            "http_download",
            {"url": "https://example.com/image.png", "path": str(dest)},
            sandbox=sandbox,
        )

    assert dest.read_bytes() == b"new content"


def test_http_download_private_ip_blocked(tmp_path):
    sandbox = SandboxConfig(
        http=HttpSandbox(block_private_ips=True),
        filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]),
    )
    with pytest.raises(PermissionError):
        tools.execute(
            "http_download",
            {"url": "http://192.168.1.100/image.png", "path": str(tmp_path / "img.png")},
            sandbox=sandbox,
        )


def test_http_download_path_outside_base_dir_blocked(tmp_path):
    import tempfile
    other_dir = tmp_path / "other"
    other_dir.mkdir()

    sandbox = SandboxConfig(
        http=HttpSandbox(block_private_ips=False),
        filesystem=FileSandbox(base_dir=tmp_path / "allowed", blocked_paths=[]),
    )
    with pytest.raises(PermissionError):
        tools.execute(
            "http_download",
            {"url": "https://example.com/img.png", "path": str(other_dir / "img.png")},
            sandbox=sandbox,
        )


def test_http_download_timeout(tmp_path):
    import httpx

    sandbox = SandboxConfig(
        http=HttpSandbox(block_private_ips=False),
        filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]),
    )
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.TimeoutException("timeout")
        mock_client_cls.return_value = mock_client

        with pytest.raises(TimeoutError):
            tools.execute(
                "http_download",
                {"url": "https://slow.example.com/img.png", "path": str(tmp_path / "img.png")},
                sandbox=sandbox,
            )


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

def test_write_file_registered():
    assert "write_file" in tools.names("builtin")


def test_write_file_creates_file_with_correct_content(tmp_path):
    dest = tmp_path / "output.txt"
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]))

    result = tools.execute(
        "write_file",
        {"path": str(dest), "content": "hello world"},
        sandbox=sandbox,
    )

    assert dest.read_text(encoding="utf-8") == "hello world"
    assert result == str(dest)


def test_write_file_overwrites_existing_file(tmp_path):
    dest = tmp_path / "output.txt"
    dest.write_text("old content")
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]))

    tools.execute(
        "write_file",
        {"path": str(dest), "content": "new content"},
        sandbox=sandbox,
    )

    assert dest.read_text(encoding="utf-8") == "new content"


def test_write_file_creates_parent_dirs(tmp_path):
    dest = tmp_path / "subdir" / "nested" / "output.txt"
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[]))

    tools.execute(
        "write_file",
        {"path": str(dest), "content": "data"},
        sandbox=sandbox,
    )

    assert dest.exists()


def test_write_file_size_limit_rejected(tmp_path):
    dest = tmp_path / "big.txt"
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[], max_file_bytes=10))

    with pytest.raises(ValueError, match="10"):
        tools.execute(
            "write_file",
            {"path": str(dest), "content": "x" * 100},
            sandbox=sandbox,
        )

    assert not dest.exists()


def test_write_file_blocked_path_raises(tmp_path):
    env_file = tmp_path / ".env"
    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path, blocked_paths=[".env"]))

    with pytest.raises(PermissionError):
        tools.execute(
            "write_file",
            {"path": str(env_file), "content": "SECRET=abc"},
            sandbox=sandbox,
        )


def test_write_file_path_outside_base_dir_blocked(tmp_path):
    other_dir = tmp_path / "other"
    other_dir.mkdir()

    sandbox = SandboxConfig(filesystem=FileSandbox(base_dir=tmp_path / "allowed", blocked_paths=[]))

    with pytest.raises(PermissionError):
        tools.execute(
            "write_file",
            {"path": str(other_dir / "output.txt"), "content": "data"},
            sandbox=sandbox,
        )


# ---------------------------------------------------------------------------
# delegate image_url
# ---------------------------------------------------------------------------

def test_delegate_no_image_url_produces_plain_message(monkeypatch):
    from agent.builtin_tools import delegate as delegate_module

    captured = {}

    def fake_run(conv, client, model, registry, tools=None, sandbox=None, max_iterations=10, **kwargs):
        captured["messages"] = conv.messages
        return "done"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "create_client", MagicMock())

    tools.execute("delegate", {"profile": "researcher", "task": "Do research."})

    user_msg = next(m for m in captured["messages"] if m["role"] == "user")
    assert user_msg["content"] == "Do research."


def test_delegate_with_image_url_produces_multimodal_message(monkeypatch):
    from agent.builtin_tools import delegate as delegate_module

    captured = {}

    def fake_run(conv, client, model, registry, tools=None, sandbox=None, max_iterations=10, **kwargs):
        captured["messages"] = conv.messages
        return "done"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "create_client", MagicMock())
    monkeypatch.setattr(delegate_module, "http_url_validator", lambda url, sandbox: url)

    tools.execute("delegate", {
        "profile": "researcher",
        "task": "Analyze the image.",
        "image_url": "https://example.com/photo.png",
    })

    user_msg = next(m for m in captured["messages"] if m["role"] == "user")
    assert isinstance(user_msg["content"], list)
    assert user_msg["content"][0] == {"type": "text", "text": "Analyze the image."}
    assert user_msg["content"][1] == {"type": "image_url", "image_url": {"url": "https://example.com/photo.png"}}


def test_delegate_private_ip_in_image_url_raises_before_subagent(monkeypatch):
    from agent.builtin_tools import delegate as delegate_module

    fake_run = MagicMock()
    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "create_client", MagicMock())

    with pytest.raises(PermissionError):
        tools.execute("delegate", {
            "profile": "researcher",
            "task": "Analyze.",
            "image_url": "http://192.168.1.100/image.png",
        })

    fake_run.assert_not_called()


def test_delegate_schema_descriptions_do_not_list_subagent_details():
    """delegate tool and profile parameter descriptions must not enumerate sub-agent names/descriptions."""
    from agent.profile import profile_registry

    schemas = tools.to_openai_schema("builtin")
    delegate_schema = next(s for s in schemas if s["function"]["name"] == "delegate")
    fn = delegate_schema["function"]
    profile_desc = fn["parameters"]["properties"]["profile"].get("description", "")
    tool_desc = fn.get("description", "")

    # No profile name should appear as a bullet-style listing
    for profile in profile_registry.all():
        assert f"- {profile.name}:" not in tool_desc
        assert f"- {profile.name}:" not in profile_desc


def test_delegate_schema_refreshes_after_programmatic_registration(monkeypatch):
    """delegate schema enum refreshes when a profile is registered after import."""
    from agent.profile import profile_registry, AgentProfile
    from agent.builtin_tools import delegate as delegate_module

    original_discovered = dict(profile_registry._discovered_profiles)
    original_registered = dict(profile_registry._registered_profiles)
    original_loaded = profile_registry._loaded

    monkeypatch.setattr(profile_registry, "_discovered_profiles", dict(original_discovered))
    monkeypatch.setattr(profile_registry, "_registered_profiles", dict(original_registered))
    monkeypatch.setattr(profile_registry, "_loaded", original_loaded)

    profile_registry.register(
        AgentProfile(
            name="planner",
            description="Plans work.",
            model="gpt-4o-mini",
            tools=["read_file"],
            system_prompt="Plan the work carefully.",
            sandbox_config={},
        )
    )

    schemas = tools.to_openai_schema("builtin")
    delegate_schema = next(s for s in schemas if s["function"]["name"] == "delegate")
    profile_param = delegate_schema["function"]["parameters"]["properties"]["profile"]

    assert "planner" in profile_param["enum"]

    monkeypatch.setattr(profile_registry, "_discovered_profiles", original_discovered)
    monkeypatch.setattr(profile_registry, "_registered_profiles", original_registered)
    monkeypatch.setattr(profile_registry, "_loaded", original_loaded)
    delegate_module._refresh_delegate_schema()


def test_delegate_executes_programmatically_registered_profile(monkeypatch):
    """delegate can execute a profile registered after module import."""
    from agent.profile import profile_registry, AgentProfile
    from agent.builtin_tools import delegate as delegate_module

    original_discovered = dict(profile_registry._discovered_profiles)
    original_registered = dict(profile_registry._registered_profiles)
    original_loaded = profile_registry._loaded

    monkeypatch.setattr(profile_registry, "_discovered_profiles", dict(original_discovered))
    monkeypatch.setattr(profile_registry, "_registered_profiles", dict(original_registered))
    monkeypatch.setattr(profile_registry, "_loaded", original_loaded)

    profile_registry.register(
        AgentProfile(
            name="planner",
            description="Plans work.",
            model="gpt-4o-mini",
            tools=["read_file"],
            system_prompt="Plan the work carefully.",
            sandbox_config={},
        )
    )

    captured = {}

    def fake_run(conv, client, model, registry, tools=None, sandbox=None, max_iterations=10, **kwargs):
        captured["model"] = model
        captured["tools"] = tools
        captured["messages"] = conv.messages
        return "planned"

    monkeypatch.setattr(delegate_module, "run", fake_run)
    monkeypatch.setattr(delegate_module, "create_client", MagicMock())

    result = tools.execute("delegate", {"profile": "planner", "task": "Plan the release."})

    assert result == "planned"
    assert captured["model"] == "gpt-4o-mini"
    names_passed = [t["function"]["name"] for t in captured["tools"]]
    assert names_passed == ["read_file"]
    assert any(m["role"] == "user" and m["content"] == "Plan the release." for m in captured["messages"])

    monkeypatch.setattr(profile_registry, "_discovered_profiles", original_discovered)
    monkeypatch.setattr(profile_registry, "_registered_profiles", original_registered)
    monkeypatch.setattr(profile_registry, "_loaded", original_loaded)
    delegate_module._refresh_delegate_schema()


# ---------------------------------------------------------------------------
# http_post headers
# ---------------------------------------------------------------------------

def test_http_post_sends_custom_header():
    from unittest.mock import patch, MagicMock
    from agent.builtin_tools.http_post import http_post
    from agent.sandbox import HttpSandbox

    mock_response = MagicMock()
    mock_response.content = b'{"ok": true}'
    mock_response.text = '{"ok": true}'

    with patch("agent.builtin_tools.http_post.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        http_post(
            url="https://example.com/api",
            body="{}",
            headers='{"Authorization": "Bearer tok123"}',
            sandbox=HttpSandbox.off(),
        )

    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs["headers"] == {"Authorization": "Bearer tok123"}


def test_http_post_default_empty_headers():
    from unittest.mock import patch, MagicMock
    from agent.builtin_tools.http_post import http_post
    from agent.sandbox import HttpSandbox

    mock_response = MagicMock()
    mock_response.content = b"ok"
    mock_response.text = "ok"

    with patch("agent.builtin_tools.http_post.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        http_post(url="https://example.com/api", body="{}", sandbox=HttpSandbox.off())

    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs["headers"] == {}


def test_http_post_invalid_headers_raises():
    from agent.builtin_tools.http_post import http_post
    from agent.sandbox import HttpSandbox

    with pytest.raises(ValueError, match="headers"):
        http_post(
            url="https://example.com",
            body="{}",
            headers="not-json",
            sandbox=HttpSandbox.off(),
        )


# ---------------------------------------------------------------------------
# http_get headers
# ---------------------------------------------------------------------------

def test_http_get_sends_custom_header():
    from unittest.mock import patch, MagicMock
    from agent.builtin_tools.http_get import http_get
    from agent.sandbox import HttpSandbox

    mock_response = MagicMock()
    mock_response.content = b"data"
    mock_response.text = "data"

    with patch("agent.builtin_tools.http_get.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        http_get(
            url="https://example.com/data",
            headers='{"X-Api-Key": "secret123"}',
            sandbox=HttpSandbox.off(),
        )

    call_kwargs = mock_client.get.call_args
    assert call_kwargs.kwargs["headers"] == {"X-Api-Key": "secret123"}


def test_http_get_default_empty_headers():
    from unittest.mock import patch, MagicMock
    from agent.builtin_tools.http_get import http_get
    from agent.sandbox import HttpSandbox

    mock_response = MagicMock()
    mock_response.content = b"data"
    mock_response.text = "data"

    with patch("agent.builtin_tools.http_get.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        http_get(url="https://example.com/data", sandbox=HttpSandbox.off())

    call_kwargs = mock_client.get.call_args
    assert call_kwargs.kwargs["headers"] == {}


def test_http_get_invalid_headers_raises():
    from agent.builtin_tools.http_get import http_get
    from agent.sandbox import HttpSandbox

    with pytest.raises(ValueError, match="headers"):
        http_get(
            url="https://example.com",
            headers="not-json",
            sandbox=HttpSandbox.off(),
        )
