"""Scheduler — manages the async agent pool.

Polls AgentRepository for pending agents, starts each as an asyncio Task,
and delivers results to waiting parents.
"""
from __future__ import annotations

import asyncio
import logging
from contextvars import ContextVar
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    pass

from agent.repositories.agent_repo import AgentRecord, AgentRepository
from agent.repositories.item_repo import ItemRepository

logger = logging.getLogger("agent")

# ContextVar used by delegate tools to access the active Scheduler instance.
scheduler_var: ContextVar[Scheduler | None] = ContextVar("scheduler_var", default=None)

_POLL_INTERVAL = 0.05  # 50 ms


class Scheduler:
    """Runs pending agents and routes results back to waiting parents."""

    def __init__(
        self,
        agent_repo: AgentRepository,
        item_repo: ItemRepository,
        runner: Callable[[AgentRecord], Awaitable[None]] | None = None,
    ) -> None:
        self._agent_repo = agent_repo
        self._item_repo = item_repo
        # runner: called with the AgentRecord to start a sub-agent run
        self._runner = runner
        # Events keyed by call_id (source_call_id of the child agent)
        self._events: dict[str, asyncio.Event] = {}
        # Results keyed by call_id — populated by deliver_result
        self._results: dict[str, str] = {}
        self._task: asyncio.Task | None = None
        # Track which agent IDs we've already started to avoid double-starting
        self._started: set[str] = set()

    def start(self) -> None:
        """Launch the background poll loop and run startup recovery."""
        self._task = asyncio.ensure_future(self._poll_loop())
        asyncio.ensure_future(self._recover_waiting_agents())

    async def stop(self) -> None:
        """Cancel the background poll task."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _poll_loop(self) -> None:
        """Continuously poll for pending agents and start them."""
        while True:
            try:
                pending = await self._agent_repo.list_by_status("pending")
                for agent in pending:
                    if agent.id not in self._started:
                        self._started.add(agent.id)
                        agent.status = "running"
                        await self._agent_repo.update(agent)
                        asyncio.ensure_future(self._run_agent(agent))
            except Exception:
                logger.exception("scheduler_poll_error")
            await asyncio.sleep(_POLL_INTERVAL)

    async def _run_agent(self, agent: AgentRecord) -> None:
        """Execute one agent using the registered runner and deliver its result."""
        try:
            if self._runner is not None:
                await self._runner(agent)
        except Exception as exc:
            logger.exception("scheduler_agent_error", extra={"agent_id": agent.id})
            agent_rec = await self._agent_repo.get(agent.id)
            if agent_rec is not None:
                agent_rec.status = "failed"
                agent_rec.error = str(exc)
                await self._agent_repo.update(agent_rec)
            if agent.source_call_id:
                await self.deliver_result(agent.source_call_id, f"ERROR: {exc}")

    async def deliver_result(self, call_id: str, result: str) -> None:
        """Store child result and resume any parent waiting for this call_id."""
        # Store result for the awaiting coroutine
        self._results[call_id] = result

        # Find parent agent waiting for this call_id
        parent = await self._agent_repo.find_waiting_for(call_id)
        if parent is not None:
            # Store result as a function_call_output item on the parent
            await self._item_repo.append(
                parent.id,
                "function_call_output",
                {"call_id": call_id, "result": result},
            )
            # Remove this call_id from waiting_for
            parent.waiting_for = [c for c in parent.waiting_for if c != call_id]
            if not parent.waiting_for:
                parent.status = "running"
            await self._agent_repo.update(parent)

        # Wake up any coroutine that is await-ing this event
        event = self._events.get(call_id)
        if event is not None:
            event.set()

    def register_event(self, call_id: str) -> asyncio.Event:
        """Create and register an Event for the given call_id."""
        event = asyncio.Event()
        self._events[call_id] = event
        return event

    def get_result(self, call_id: str) -> str | None:
        """Return the stored result for a call_id, or None if not yet delivered."""
        return self._results.get(call_id)

    async def _recover_waiting_agents(self) -> None:
        """On startup, auto-deliver results for waiting agents whose results are in DB."""
        waiting = await self._agent_repo.list_by_status("waiting")
        for agent in waiting:
            all_resolved = True
            for call_id in agent.waiting_for:
                item = await self._item_repo.get_output_by_call_id(call_id)
                if item is None:
                    all_resolved = False
                    break
                # Re-populate in-memory results
                self._results[call_id] = item.content.get("result", "")  # type: ignore[union-attr]
            if all_resolved:
                for call_id in list(agent.waiting_for):
                    await self.deliver_result(call_id, self._results[call_id])
