"""Non-blocking delegate machinery for parallel sub-agent fan-out.

Provides:
  delegate_async(profile, task, image_url) → agent_id (non-blocking)
  delegate_all(tasks) → list of results (fan-out + gather)
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import agent.context as _ctx
from agent.profile import profile_registry, sandbox_from_profile
from agent.repositories.agent_repo import AgentRepository
from agent.scheduler import Scheduler, scheduler_var

if TYPE_CHECKING:
    pass

logger = logging.getLogger("agent")


async def delegate_async(
    profile: str,
    task: str,
    image_url: str | None = None,
) -> str:
    """Spawn a child agent non-blocking.

    Inserts a child agent record with status='pending', registers an asyncio.Event
    keyed by source_call_id, and returns the new agent_id immediately.
    The caller must await the event and retrieve the result from the scheduler.
    """
    scheduler: Scheduler | None = scheduler_var.get()
    if scheduler is None:
        raise RuntimeError("No scheduler available. Initialize and set scheduler_var before using delegate.")

    call_id: str | None = _ctx.current_call_id.get()
    parent_agent_id: str | None = _ctx.agent_id.get()

    # Verify profile exists
    agent_profile = profile_registry.get(profile)

    config = {
        "profile": profile,
        "model": agent_profile.model,
        "task": task,
        "image_url": image_url,
    }

    # Create child agent record in DB (all fields set atomically to avoid race with scheduler)
    child = await scheduler._agent_repo.create(
        config,
        parent_id=parent_agent_id,
        source_call_id=call_id,
    )

    # Register event keyed by source_call_id (the tool call ID from the parent run loop)
    if call_id:
        scheduler.register_event(call_id)

    logger.info("delegate_async_spawn", extra={"child_agent_id": child.id, "call_id": call_id, "profile": profile})
    return child.id


async def delegate_all(tasks: list[tuple[str, str]]) -> list[str]:
    """Fan-out: spawn all sub-agents and wait for all results.

    tasks: list of (profile, task) tuples.
    Returns a list of result strings in the same order as the input.
    """
    scheduler: Scheduler | None = scheduler_var.get()
    if scheduler is None:
        raise RuntimeError("No scheduler available.")

    # Save call_id for each task — we need unique call_ids per sub-task.
    # We generate synthetic call_ids for fan-out sub-tasks.
    import uuid
    call_ids: list[str] = []
    agent_ids: list[str] = []

    for profile, task in tasks:
        # Generate a unique call_id for each parallel sub-task
        synthetic_call_id = f"parallel_{uuid.uuid4().hex}"
        _ctx.current_call_id.set(synthetic_call_id)
        agent_id = await delegate_async(profile, task)
        agent_ids.append(agent_id)
        call_ids.append(synthetic_call_id)

    # Wait for all events
    events = [scheduler._events[cid] for cid in call_ids if cid in scheduler._events]
    await asyncio.gather(*(e.wait() for e in events))

    # Retrieve results in order
    return [scheduler.get_result(cid) or "" for cid in call_ids]
