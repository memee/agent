"""Repository for conversation items stored in SQLite."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any

import aiosqlite


@dataclass
class ItemRecord:
    id: str
    agent_id: str
    type: str  # message | function_call | function_call_output
    content: dict | list
    sequence: int
    created_at: float


def _row_to_record(row: aiosqlite.Row) -> ItemRecord:
    return ItemRecord(
        id=row["id"],
        agent_id=row["agent_id"],
        type=row["type"],
        content=json.loads(row["content"]),
        sequence=row["sequence"],
        created_at=row["created_at"],
    )


class ItemRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def append(self, agent_id: str, type: str, content: Any) -> ItemRecord:
        """Insert a new item with auto-incremented sequence per agent."""
        async with self._conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) FROM items WHERE agent_id = ?",
            (agent_id,),
        ) as cursor:
            row = await cursor.fetchone()
        next_seq = (row[0] if row else 0) + 1
        now = time.time()
        item = ItemRecord(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            type=type,
            content=content,
            sequence=next_seq,
            created_at=now,
        )
        await self._conn.execute(
            "INSERT INTO items (id, agent_id, type, content, sequence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (item.id, item.agent_id, item.type, json.dumps(item.content), item.sequence, item.created_at),
        )
        await self._conn.commit()
        return item

    async def list_for_agent(self, agent_id: str) -> list[ItemRecord]:
        """Return all items for the agent ordered by sequence ascending."""
        async with self._conn.execute(
            "SELECT * FROM items WHERE agent_id = ? ORDER BY sequence ASC",
            (agent_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_record(r) for r in rows]

    async def get_output_by_call_id(self, call_id: str) -> ItemRecord | None:
        """Find a function_call_output item whose content contains the given call_id."""
        async with self._conn.execute(
            "SELECT * FROM items WHERE type = 'function_call_output'"
        ) as cursor:
            rows = await cursor.fetchall()
        for row in rows:
            content = json.loads(row["content"])
            if isinstance(content, dict) and content.get("call_id") == call_id:
                return _row_to_record(row)
        return None
