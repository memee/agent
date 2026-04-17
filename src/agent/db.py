"""SQLite connection management for agent persistence.

Provides open_db() — an async context manager that opens an aiosqlite
connection, enables WAL mode, and ensures all required tables exist.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiosqlite

_AGENTS_DDL = """
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    parent_id TEXT,
    source_call_id TEXT,
    waiting_for TEXT NOT NULL DEFAULT '[]',
    config TEXT NOT NULL,
    turn_count INTEGER NOT NULL DEFAULT 0,
    result TEXT,
    error TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""

_ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
"""

_DEFAULT_DB_PATH = "agent.db"


@asynccontextmanager
async def open_db(path: str | None = None) -> AsyncIterator[aiosqlite.Connection]:
    """Open an aiosqlite connection, enable WAL mode, and ensure tables exist.

    Yields the connection. Closes it when the context exits.
    Path defaults to AGENT_DB_PATH env var or 'agent.db' in the current directory.
    """
    resolved = path or os.environ.get("AGENT_DB_PATH", _DEFAULT_DB_PATH)
    async with aiosqlite.connect(resolved) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute(_AGENTS_DDL)
        await conn.execute(_ITEMS_DDL)
        await conn.commit()
        yield conn
