"""Repository for agent records stored in SQLite."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import aiosqlite


@dataclass
class AgentRecord:
    id: str
    status: str  # pending | running | waiting | completed | failed
    config: dict
    parent_id: str | None = None
    source_call_id: str | None = None
    waiting_for: list[str] = field(default_factory=list)
    turn_count: int = 0
    result: str | None = None
    error: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0


def _row_to_record(row: aiosqlite.Row) -> AgentRecord:
    return AgentRecord(
        id=row["id"],
        status=row["status"],
        config=json.loads(row["config"]),
        parent_id=row["parent_id"],
        source_call_id=row["source_call_id"],
        waiting_for=json.loads(row["waiting_for"]),
        turn_count=row["turn_count"],
        result=row["result"],
        error=row["error"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AgentRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        config: dict[str, Any],
        parent_id: str | None = None,
        source_call_id: str | None = None,
    ) -> AgentRecord:
        """Insert a new agent record with status='pending' and a generated UUID."""
        now = time.time()
        agent = AgentRecord(
            id=str(uuid.uuid4()),
            status="pending",
            config=config,
            parent_id=parent_id,
            source_call_id=source_call_id,
            created_at=now,
            updated_at=now,
        )
        await self._conn.execute(
            """
            INSERT INTO agents
                (id, status, parent_id, source_call_id, waiting_for, config,
                 turn_count, result, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent.id,
                agent.status,
                agent.parent_id,
                agent.source_call_id,
                json.dumps(agent.waiting_for),
                json.dumps(agent.config),
                agent.turn_count,
                agent.result,
                agent.error,
                agent.created_at,
                agent.updated_at,
            ),
        )
        await self._conn.commit()
        return agent

    async def get(self, agent_id: str) -> AgentRecord | None:
        """Return the agent record for the given ID, or None if not found."""
        async with self._conn.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_record(row) if row is not None else None

    async def update(self, agent: AgentRecord) -> None:
        """Persist all mutable fields of the agent record and refresh updated_at."""
        agent.updated_at = time.time()
        await self._conn.execute(
            """
            UPDATE agents SET
                status = ?,
                parent_id = ?,
                source_call_id = ?,
                waiting_for = ?,
                config = ?,
                turn_count = ?,
                result = ?,
                error = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                agent.status,
                agent.parent_id,
                agent.source_call_id,
                json.dumps(agent.waiting_for),
                json.dumps(agent.config),
                agent.turn_count,
                agent.result,
                agent.error,
                agent.updated_at,
                agent.id,
            ),
        )
        await self._conn.commit()

    async def list_by_status(self, status: str) -> list[AgentRecord]:
        """Return all agents with the given status, in insertion order."""
        async with self._conn.execute(
            "SELECT * FROM agents WHERE status = ? ORDER BY created_at ASC",
            (status,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_record(r) for r in rows]

    async def find_waiting_for(self, call_id: str) -> AgentRecord | None:
        """Return the first agent whose waiting_for JSON array contains call_id."""
        async with self._conn.execute(
            "SELECT * FROM agents WHERE status = 'waiting'"
        ) as cursor:
            rows = await cursor.fetchall()
        for row in rows:
            waiting = json.loads(row["waiting_for"])
            if call_id in waiting:
                return _row_to_record(row)
        return None
