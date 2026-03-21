"""Tests for agent.logging — ContextFilter and JsonFormatter."""
import contextvars
import json
import logging

import agent.context as ctx
from agent.context import set_run_context
from agent.logging import ContextFilter, JsonFormatter


def _run_isolated(fn, *args, **kwargs):
    c = contextvars.copy_context()
    return c.run(fn, *args, **kwargs)


# ---------------------------------------------------------------------------
# 7.3 — ContextFilter injects context fields; safe defaults outside run()
# ---------------------------------------------------------------------------

def test_context_filter_injects_fields_in_run():
    def _check():
        set_run_context("myagent")
        record = logging.LogRecord(
            name="agent", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None,
        )
        f = ContextFilter()
        f.filter(record)
        assert record.agent_name == "myagent"
        assert record.depth == 0
        assert record.run_id is not None
        assert record.iteration == 0

    _run_isolated(_check)


def test_context_filter_safe_defaults_outside_run():
    """Outside run(), context vars have defaults — filter must not crash."""
    def _check():
        # Fresh copy: no set_run_context called — all vars at defaults
        record = logging.LogRecord(
            name="agent", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None,
        )
        f = ContextFilter()
        f.filter(record)
        assert record.run_id is None
        assert record.depth == 0
        assert record.agent_name == "main"
        assert record.iteration == 0

    c = contextvars.copy_context()
    c.run(_check)


# ---------------------------------------------------------------------------
# 7.4 — JsonFormatter produces valid JSON with expected fields
# ---------------------------------------------------------------------------

def test_json_formatter_valid_json():
    record = logging.LogRecord(
        name="agent", level=logging.INFO, pathname="", lineno=0,
        msg="llm_call", args=(), exc_info=None,
    )
    # Simulate context filter having run
    record.run_id = "test-uuid"
    record.parent_run_id = None
    record.depth = 0
    record.agent_name = "main"
    record.iteration = 1
    # Event-specific extras
    record.__dict__["model"] = "gpt-4o"
    record.__dict__["duration_ms"] = 123.4

    formatter = JsonFormatter()
    output = formatter.format(record)

    data = json.loads(output)  # Must not raise
    assert data["event"] == "llm_call"
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["run_id"] == "test-uuid"
    assert data["agent_name"] == "main"
    assert data["depth"] == 0
    assert data["model"] == "gpt-4o"
    assert data["duration_ms"] == 123.4


def test_json_formatter_single_line():
    record = logging.LogRecord(
        name="agent", level=logging.INFO, pathname="", lineno=0,
        msg="test", args=(), exc_info=None,
    )
    record.run_id = None
    record.parent_run_id = None
    record.depth = 0
    record.agent_name = "main"
    record.iteration = 0

    output = JsonFormatter().format(record)
    assert "\n" not in output
