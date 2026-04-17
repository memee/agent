"""Execution context carried via contextvars.

Provides run_id, parent_run_id, depth, agent_name, and iteration as ContextVar
instances. Values are set at run() entry and propagated automatically to all
code in the call stack, including sub-agents, without explicit parameter passing.
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar

run_id: ContextVar[str | None] = ContextVar("run_id", default=None)
parent_run_id: ContextVar[str | None] = ContextVar("parent_run_id", default=None)
depth: ContextVar[int] = ContextVar("depth", default=0)
agent_name: ContextVar[str] = ContextVar("agent_name", default="main")
iteration: ContextVar[int] = ContextVar("iteration", default=0)
agent_id: ContextVar[str | None] = ContextVar("agent_id", default=None)
current_call_id: ContextVar[str | None] = ContextVar("current_call_id", default=None)


def set_run_context(name: str = "main") -> None:
    """Set context vars for a new run() entry.

    Reads the current context to derive parent_run_id and depth for sub-agents.
    Must be called from within a copy_context().run() call so that modifications
    are scoped to the child context and do not affect the parent.
    """
    current_run_id = run_id.get()
    if current_run_id is not None:
        # Sub-agent: inherit from parent context
        parent_run_id.set(current_run_id)
        depth.set(depth.get() + 1)
    else:
        # Top-level: fresh context
        parent_run_id.set(None)
        depth.set(0)
    run_id.set(str(uuid.uuid4()))
    agent_name.set(name)
    iteration.set(0)
