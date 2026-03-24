"""Secret scrubbing utilities for log sanitization.

Provides:
- scrub(text): replaces known secret patterns and explicit secret values with ***
- ScrubFilter: logging.Filter that applies scrub() to all log record fields
"""
from __future__ import annotations

import logging
import os
import re

# --- Regex patterns (applied in order) ---
# Each pattern is (compiled_regex, replacement_string)
# Groups in the pattern use backreferences in replacement where prefix is preserved.

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # OpenAI-style keys: sk- followed by >=20 word chars/dashes — preserve prefix
    (re.compile(r"sk-[A-Za-z0-9\-_]{20,}"), "sk-***"),
    # HTTP Bearer tokens
    (re.compile(r"(Bearer\s+)\S{8,}"), r"\1***"),
    # Generic key/token/password/secret fields in JSON or query strings
    # Matches: preceded by ", ?, &; field name; separator (=, :, whitespace); value >=4 chars
    (
        re.compile(
            r'(["\?&](?:api[_\-]?key|token|password|secret)[":\s=]+)[^\s"\'`,}\]&]{4,}',
            re.IGNORECASE,
        ),
        r"\1***",
    ),
]

# --- Explicit secrets from env var (read once at import time) ---
_raw = os.environ.get("AGENT_SCRUB_SECRETS", "")
# Sort longest-first to prevent shorter prefix from masking before longer match
_EXPLICIT: list[str] = sorted(
    (s for s in _raw.split(",") if s.strip()),
    key=len,
    reverse=True,
)

# --- Runtime secrets (registered dynamically via register_runtime_secrets) ---
_RUNTIME: list[str] = []


def register_runtime_secrets(values: list[str]) -> None:
    """Register secret values to be masked at runtime.

    Filters empty strings. Maintains longest-first ordering to prevent partial
    masking. Safe to call multiple times; duplicates are deduplicated.
    """
    global _RUNTIME
    combined = set(_RUNTIME) | {v for v in values if v}
    _RUNTIME = sorted(combined, key=len, reverse=True)


def scrub(text: str) -> str:
    """Return *text* with all known secrets replaced by ***.

    Applies regex patterns first, then explicit values from AGENT_SCRUB_SECRETS.
    """
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    for secret in _EXPLICIT:
        text = text.replace(secret, "***")
    for secret in _RUNTIME:
        text = text.replace(secret, "***")
    return text


# Standard LogRecord attributes — not touched by the filter
_RECORD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName", "asctime",
})


def _scrub_value(value: object) -> object:
    """Recursively scrub a value that may be str, dict, list, or other."""
    if isinstance(value, str):
        return scrub(value)
    if isinstance(value, dict):
        return {k: _scrub_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub_value(item) for item in value)
    return value


class ScrubFilter(logging.Filter):
    """Logging filter that masks secrets in every log record.

    Applies scrub() to:
    - record.msg
    - record.args (tuple or dict)
    - all extra fields not in the standard LogRecord attribute set, recursively
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _scrub_value(record.msg)
        if record.args:
            record.args = _scrub_value(record.args)  # type: ignore[assignment]
        for key, value in record.__dict__.items():
            if key not in _RECORD_ATTRS and not key.startswith("_"):
                setattr(record, key, _scrub_value(value))
        return True
