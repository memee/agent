"""Tests for secret scrubbing utilities."""
from __future__ import annotations

import logging


def test_scrub_openai_key():
    from agent.scrub import scrub
    result = scrub("Authorization: sk-proj-ABCDEFGHIJKLMNOPQRSTUVwxyz1234")
    assert "sk-***" in result
    assert "ABCDEFGHIJKLMNOPQRSTUVwxyz1234" not in result


def test_scrub_bearer_token():
    from agent.scrub import scrub
    result = scrub("Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.payload.sig")
    assert "Bearer ***" in result
    assert "eyJhbGciOiJSUzI1NiJ9" not in result


def test_scrub_api_key_in_json():
    from agent.scrub import scrub
    result = scrub('{"api_key": "my-secret-value"}')
    assert "***" in result
    assert "my-secret-value" not in result


def test_scrub_token_in_json():
    from agent.scrub import scrub
    result = scrub('{"token": "abcdefghij"}')
    assert "***" in result
    assert "abcdefghij" not in result


def test_scrub_password_in_json():
    from agent.scrub import scrub
    result = scrub('{"password": "hunter2hunter"}')
    assert "***" in result
    assert "hunter2hunter" not in result


def test_scrub_no_secrets():
    from agent.scrub import scrub
    result = scrub("hello world")
    assert result == "hello world"


def test_scrub_explicit_single(monkeypatch):
    monkeypatch.setenv("AGENT_SCRUB_SECRETS", "mysecretkey123")
    # Re-import to pick up env var (module-level read)
    import importlib
    import agent.scrub as scrub_mod
    importlib.reload(scrub_mod)
    result = scrub_mod.scrub("token=mysecretkey123")
    assert "***" in result
    assert "mysecretkey123" not in result


def test_scrub_explicit_multiple_longest_first(monkeypatch):
    monkeypatch.setenv("AGENT_SCRUB_SECRETS", "abc,abcdef")
    import importlib
    import agent.scrub as scrub_mod
    importlib.reload(scrub_mod)
    result = scrub_mod.scrub("x=abcdef y=abc")
    assert "abcdef" not in result
    assert "abc" not in result
    assert result == "x=*** y=***"


def test_scrub_explicit_empty(monkeypatch):
    monkeypatch.delenv("AGENT_SCRUB_SECRETS", raising=False)
    import importlib
    import agent.scrub as scrub_mod
    importlib.reload(scrub_mod)
    result = scrub_mod.scrub("hello world")
    assert result == "hello world"


def test_scrub_filter_secret_in_msg():
    import importlib
    import agent.scrub as scrub_mod
    importlib.reload(scrub_mod)

    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg="key=sk-proj-ABCDEFGHIJKLMNOPQRSTUVwxyz1234",
        args=(), exc_info=None,
    )
    f = scrub_mod.ScrubFilter()
    result = f.filter(record)
    assert result is True
    assert "sk-***" in record.msg
    assert "ABCDEFGHIJKLMNOPQRSTUVwxyz1234" not in record.msg


def test_scrub_filter_secret_in_args():
    import importlib
    import agent.scrub as scrub_mod
    importlib.reload(scrub_mod)

    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg="key=%s",
        args=("sk-proj-ABCDEFGHIJKLMNOPQRSTUVwxyz1234",),
        exc_info=None,
    )
    f = scrub_mod.ScrubFilter()
    f.filter(record)
    assert "sk-***" in record.args[0]
    assert "ABCDEFGHIJKLMNOPQRSTUVwxyz1234" not in record.args[0]


def test_scrub_filter_secret_in_nested_extra():
    import importlib
    import agent.scrub as scrub_mod
    importlib.reload(scrub_mod)

    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg="tool_call",
        args=(), exc_info=None,
    )
    record.tool_args = {"body": '{"api_key": "s3cr3tvalue"}'}

    f = scrub_mod.ScrubFilter()
    f.filter(record)
    assert "s3cr3tvalue" not in record.tool_args["body"]
    assert "***" in record.tool_args["body"]


def test_scrub_filter_always_returns_true():
    import importlib
    import agent.scrub as scrub_mod
    importlib.reload(scrub_mod)

    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg="harmless message",
        args=(), exc_info=None,
    )
    f = scrub_mod.ScrubFilter()
    assert f.filter(record) is True
