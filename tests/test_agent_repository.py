"""Async tests for AgentRepository."""
import pytest

from agent.db import open_db
from agent.repositories.agent_repo import AgentRepository


@pytest.fixture
async def repo(tmp_path):
    db_path = str(tmp_path / "test.db")
    async with open_db(db_path) as conn:
        yield AgentRepository(conn)


async def test_create_returns_pending_agent(repo):
    config = {"profile": "researcher", "model": "gpt-4o", "task": "find X"}
    agent = await repo.create(config)

    assert agent.id
    assert agent.status == "pending"
    assert agent.config == config
    assert agent.waiting_for == []
    assert agent.turn_count == 0
    assert agent.result is None


async def test_get_returns_record(repo):
    agent = await repo.create({"profile": "p", "model": "m", "task": "t"})
    fetched = await repo.get(agent.id)

    assert fetched is not None
    assert fetched.id == agent.id
    assert fetched.status == "pending"


async def test_get_unknown_returns_none(repo):
    result = await repo.get("nonexistent-id")
    assert result is None


async def test_update_persists_fields(repo):
    agent = await repo.create({"profile": "p", "model": "m", "task": "t"})
    agent.status = "running"
    agent.turn_count = 3
    agent.result = "done"
    await repo.update(agent)

    fetched = await repo.get(agent.id)
    assert fetched.status == "running"
    assert fetched.turn_count == 3
    assert fetched.result == "done"


async def test_list_by_status_returns_pending(repo):
    a1 = await repo.create({"profile": "p", "model": "m", "task": "1"})
    a2 = await repo.create({"profile": "p", "model": "m", "task": "2"})
    a2.status = "running"
    await repo.update(a2)

    pending = await repo.list_by_status("pending")
    assert len(pending) == 1
    assert pending[0].id == a1.id


async def test_list_by_status_empty(repo):
    result = await repo.list_by_status("pending")
    assert result == []


async def test_find_waiting_for_returns_agent(repo):
    agent = await repo.create({"profile": "p", "model": "m", "task": "t"})
    agent.status = "waiting"
    agent.waiting_for = ["call_abc"]
    await repo.update(agent)

    found = await repo.find_waiting_for("call_abc")
    assert found is not None
    assert found.id == agent.id


async def test_find_waiting_for_returns_none_if_not_found(repo):
    result = await repo.find_waiting_for("no_such_call")
    assert result is None


async def test_find_waiting_for_not_found_if_not_waiting(repo):
    agent = await repo.create({"profile": "p", "model": "m", "task": "t"})
    agent.status = "running"
    agent.waiting_for = ["call_abc"]
    await repo.update(agent)

    result = await repo.find_waiting_for("call_abc")
    assert result is None
