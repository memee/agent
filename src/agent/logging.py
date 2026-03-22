"""Logging infrastructure for the agent.

Provides:
- JsonFormatter: serializes log records to single-line JSON
- ContextFilter: injects execution context fields into every log record
- configure_logging(): sets up the 'agent' logger with stdout and file handlers
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import agent.context as _ctx
from agent.scrub import ScrubFilter

# Standard LogRecord attributes to exclude from the key=value section of human output
_RECORD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName", "asctime",
})
# Context fields shown in the prefix — not repeated as key=value
_CONTEXT_ATTRS = frozenset(
    {"run_id", "parent_run_id", "depth", "agent_name", "iteration"})


class JsonFormatter(logging.Formatter):
    """Serializes each log record to a single JSON line.

    Includes timestamp, level, event (the log message), context fields, and
    any extra fields added via extra={} at the call site.
    """

    def format(self, record: logging.LogRecord) -> str:
        data: dict = {
            "timestamp": datetime.fromtimestamp(record.created,
                                                tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        # Context fields (injected by ContextFilter)
        for field in _CONTEXT_ATTRS:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        # Event-specific extra fields
        for key, value in record.__dict__.items():
            if key not in _RECORD_ATTRS and key not in _CONTEXT_ATTRS and not key.startswith(
                    "_"):
                data[key] = value
        return json.dumps(data, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for stdout.

    Format: [HH:MM:SS] LEVEL agent_name(depth) | message key=value ...
    """

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%H:%M:%S")
        name = getattr(record, "agent_name", "unknown")
        dep = getattr(record, "depth", 0)
        msg = record.getMessage()

        # Collect event-specific extra fields only
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if
            k not in _RECORD_ATTRS and k not in _CONTEXT_ATTRS and not k.startswith(
                "_")
        }
        prefix = f"[{ts}] {record.levelname} {name}({dep}) | {msg}"
        if extras:
            kv = " ".join(f"{k}={v}" for k, v in extras.items())
            return f"{prefix} {kv}"
        return prefix


class ContextFilter(logging.Filter):
    """Injects current contextvars values into every log record.

    Provides safe defaults when called outside of a run() context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = _ctx.run_id.get()
        record.parent_run_id = _ctx.parent_run_id.get()
        record.depth = _ctx.depth.get()
        record.agent_name = _ctx.agent_name.get()
        record.iteration = _ctx.iteration.get()
        return True


def configure_logging() -> None:
    """Configure the 'agent' logger with stdout (human-readable) and file (JSON) handlers.

    Reads AGENT_LOG_FILE env var for the file path; defaults to 'agent.log' in cwd.
    Idempotent — does nothing if the logger already has handlers.
    """
    agent_logger = logging.getLogger("agent")
    if agent_logger.handlers:
        return

    agent_logger.setLevel(logging.DEBUG)
    agent_logger.propagate = False

    context_filter = ContextFilter()
    scrub_filter = ScrubFilter()

    # Stdout handler — human-readable
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(HumanFormatter())
    stdout_handler.addFilter(context_filter)
    stdout_handler.addFilter(scrub_filter)
    agent_logger.addHandler(stdout_handler)

    # File handler — structured JSON
    log_file = os.environ.get("AGENT_LOG_FILE", "agent.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())
    file_handler.addFilter(context_filter)
    file_handler.addFilter(scrub_filter)
    agent_logger.addHandler(file_handler)
