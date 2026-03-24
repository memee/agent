"""Tests for SecretsStore."""
from __future__ import annotations

import pytest

from agent.secrets import SecretsStore


def test_get_known_key():
    store = SecretsStore({"API_KEY": "abc123"})
    assert store.get("API_KEY") == "abc123"


def test_get_unknown_key_returns_none():
    store = SecretsStore({"API_KEY": "abc123"})
    assert store.get("MISSING") is None


def test_values_returns_all():
    store = SecretsStore({"A": "val1", "B": "val2"})
    assert set(store.values()) == {"val1", "val2"}


def test_names_returns_all():
    store = SecretsStore({"API_KEY": "x", "TOKEN": "y"})
    assert set(store.names()) == {"API_KEY", "TOKEN"}


def test_interpolate_single_placeholder():
    store = SecretsStore({"KEY": "secret"})
    assert store.interpolate("value=${KEY}") == "value=secret"


def test_interpolate_unknown_placeholder_unchanged():
    store = SecretsStore({"KEY": "secret"})
    assert store.interpolate("x=${MISSING}") == "x=${MISSING}"


def test_interpolate_multiple_different_placeholders():
    store = SecretsStore({"A": "1", "B": "2"})
    assert store.interpolate("${A}-${B}") == "1-2"


def test_interpolate_repeated_placeholder():
    store = SecretsStore({"K": "v"})
    assert store.interpolate("${K}:${K}") == "v:v"


def test_interpolate_no_placeholders_unchanged():
    store = SecretsStore({"K": "v"})
    assert store.interpolate("hello world") == "hello world"


def test_interpolate_placeholder_in_json_body():
    store = SecretsStore({"API_KEY": "real-key"})
    body = '{"apikey": "${API_KEY}", "task": "drone"}'
    result = store.interpolate(body)
    assert result == '{"apikey": "real-key", "task": "drone"}'


def test_interpolate_placeholder_in_url():
    store = SecretsStore({"TOKEN": "tok123"})
    url = "https://api.example.com/data?key=${TOKEN}"
    assert store.interpolate(url) == "https://api.example.com/data?key=tok123"