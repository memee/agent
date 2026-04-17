"""Async tests for delegate_all and the Scheduler."""
import asyncio
import pytest

from agent.db import open_db
from agent.repositories.agent_repo import AgentRepository
from agent.repositories.item_repo import ItemRepository
from agent.scheduler import Scheduler, scheduler_var


# ---------------------------------------------------------------------------
# Helper: in-memory scheduler with a fake runner
# ---------------------------------------------------------------------------

async def _make_scheduler(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = await __import__("aiosqlite").connect(db_path)
    conn.row_factory = __import__("aiosqlite").Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    # Initialise tables via open_db DDL
    async with open_db(db_path):
        pass  # just create tables
    import aiosqlite
    conn2 = await aiosqlite.connect(db_path)
    conn2.row_factory = aiosqlite.Row
    agent_repo = AgentRepository(conn2)
    item_repo = ItemRepository(conn2)
    return conn2, agent_repo, item_repo


# ---------------------------------------------------------------------------
# 8.5 — delegate_all with two profiles returns ordered results
# ---------------------------------------------------------------------------

async def test_delegate_all_returns_ordered_results(tmp_path, monkeypatch):
    """delegate_all spawns two agents and returns results in order."""
    from agent.builtin_tools.parallel_delegate import delegate_all
    from agent.profile import profile_registry, AgentProfile
    import agent.context as _ctx

    # Register two minimal test profiles
    for name in ("alpha", "beta"):
        if name not in profile_registry.names():
            profile_registry.register(AgentProfile(
                name=name,
                description=f"{name} agent",
                model="gpt-4o-mini",
                tools=[],
                system_prompt=f"You are {name}.",
                sandbox_config={},
            ))

    # Build an in-memory scheduler with a runner that immediately delivers results
    async with open_db(str(tmp_path / "test.db")) as conn:
        agent_repo = AgentRepository(conn)
        item_repo = ItemRepository(conn)

        results_delivered = {}

        async def fake_runner(agent):
            profile_name = agent.config.get("profile", "?")
            result = f"result_from_{profile_name}"
            results_delivered[agent.source_call_id] = result
            await scheduler.deliver_result(agent.source_call_id, result)

        scheduler = Scheduler(agent_repo, item_repo, runner=fake_runner)
        scheduler.start()
        token = scheduler_var.set(scheduler)

        try:
            results = await delegate_all([("alpha", "task A"), ("beta", "task B")])
        finally:
            scheduler_var.reset(token)
            await scheduler.stop()

    assert len(results) == 2
    assert results[0] == "result_from_alpha"
    assert results[1] == "result_from_beta"


# ---------------------------------------------------------------------------
# Scheduler: pending agent is started
# ---------------------------------------------------------------------------

async def test_scheduler_starts_pending_agent(tmp_path):
    """Scheduler picks up a pending agent and calls the runner."""
    async with open_db(str(tmp_path / "sched.db")) as conn:
        agent_repo = AgentRepository(conn)
        item_repo = ItemRepository(conn)

        started_ids = []

        async def fake_runner(agent):
            started_ids.append(agent.id)

        scheduler = Scheduler(agent_repo, item_repo, runner=fake_runner)

        # Create a pending agent
        agent = await agent_repo.create({"profile": "p", "model": "m", "task": "t"})
        scheduler.start()

        # Give the scheduler loop a moment to pick up the agent
        await asyncio.sleep(0.2)
        await scheduler.stop()

    assert agent.id in started_ids


# ---------------------------------------------------------------------------
# Scheduler: deliver_result wakes waiting parent
# ---------------------------------------------------------------------------

async def test_deliver_result_wakes_parent(tmp_path):
    """deliver_result() sets the event so a waiting coroutine can resume."""
    async with open_db(str(tmp_path / "dr.db")) as conn:
        agent_repo = AgentRepository(conn)
        item_repo = ItemRepository(conn)
        scheduler = Scheduler(agent_repo, item_repo)

        # Create a parent agent in waiting state
        parent = await agent_repo.create({"profile": "p", "model": "m", "task": "t"})
        parent.status = "waiting"
        parent.waiting_for = ["call_xyz"]
        await agent_repo.update(parent)

        event = scheduler.register_event("call_xyz")

        # deliver_result in a background task
        async def deliver():
            await asyncio.sleep(0.05)
            await scheduler.deliver_result("call_xyz", "the answer")

        asyncio.ensure_future(deliver())
        await asyncio.wait_for(event.wait(), timeout=2.0)

        assert scheduler.get_result("call_xyz") == "the answer"

        # Verify item stored and parent updated
        item = await item_repo.get_output_by_call_id("call_xyz")
        assert item is not None
        assert item.content["result"] == "the answer"

        updated_parent = await agent_repo.get(parent.id)
        assert updated_parent.waiting_for == []
