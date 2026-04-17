"""Async tests for ItemRepository."""
import pytest

from agent.db import open_db
from agent.repositories.agent_repo import AgentRepository
from agent.repositories.item_repo import ItemRepository


@pytest.fixture
async def repos(tmp_path):
    db_path = str(tmp_path / "test.db")
    async with open_db(db_path) as conn:
        agent_repo = AgentRepository(conn)
        item_repo = ItemRepository(conn)
        # Create a couple of agents for use in tests
        agent_a = await agent_repo.create({"profile": "p", "model": "m", "task": "a"})
        agent_b = await agent_repo.create({"profile": "p", "model": "m", "task": "b"})
        yield item_repo, agent_a.id, agent_b.id


async def test_append_returns_item_with_sequence(repos):
    item_repo, agent_a, _ = repos
    item = await item_repo.append(agent_a, "message", {"role": "user", "content": "hello"})

    assert item.id
    assert item.agent_id == agent_a
    assert item.type == "message"
    assert item.sequence == 1


async def test_append_increments_sequence_per_agent(repos):
    item_repo, agent_a, _ = repos
    i1 = await item_repo.append(agent_a, "message", {"content": "a"})
    i2 = await item_repo.append(agent_a, "message", {"content": "b"})

    assert i1.sequence == 1
    assert i2.sequence == 2


async def test_list_for_agent_returns_ordered(repos):
    item_repo, agent_a, _ = repos
    await item_repo.append(agent_a, "message", {"content": "first"})
    await item_repo.append(agent_a, "message", {"content": "second"})

    items = await item_repo.list_for_agent(agent_a)
    assert len(items) == 2
    assert items[0].content["content"] == "first"
    assert items[1].content["content"] == "second"


async def test_items_from_different_agents_are_isolated(repos):
    item_repo, agent_a, agent_b = repos
    await item_repo.append(agent_a, "message", {"content": "for_a"})
    await item_repo.append(agent_b, "message", {"content": "for_b"})

    items_a = await item_repo.list_for_agent(agent_a)
    items_b = await item_repo.list_for_agent(agent_b)

    assert len(items_a) == 1
    assert items_a[0].content["content"] == "for_a"
    assert len(items_b) == 1
    assert items_b[0].content["content"] == "for_b"


async def test_get_output_by_call_id_found(repos):
    item_repo, agent_a, _ = repos
    await item_repo.append(agent_a, "function_call_output", {"call_id": "call_123", "result": "ok"})

    item = await item_repo.get_output_by_call_id("call_123")
    assert item is not None
    assert item.content["call_id"] == "call_123"
    assert item.content["result"] == "ok"


async def test_get_output_by_call_id_not_found(repos):
    item_repo, agent_a, _ = repos
    result = await item_repo.get_output_by_call_id("no_such_call")
    assert result is None
