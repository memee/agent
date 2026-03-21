"""Tests for agent.context — contextvars definitions and set_run_context()."""
import contextvars

import agent.context as ctx
from agent.context import set_run_context


def _run_isolated(fn, *args, **kwargs):
    """Run fn in a copy of the current context (mirrors what run() does)."""
    c = contextvars.copy_context()
    return c.run(fn, *args, **kwargs)


# ---------------------------------------------------------------------------
# 7.1 — top-level sets depth=0, parent_run_id=None
# ---------------------------------------------------------------------------

def test_top_level_context():
    def _check():
        set_run_context("main")
        assert ctx.depth.get() == 0
        assert ctx.parent_run_id.get() is None
        assert ctx.run_id.get() is not None
        assert ctx.agent_name.get() == "main"

    _run_isolated(_check)


# ---------------------------------------------------------------------------
# 7.2 — sub-agent context: child gets depth=1, parent_run_id=parent's run_id,
#         and parent context is unchanged after child returns
# ---------------------------------------------------------------------------

def test_sub_agent_context():
    parent_run_id_captured = []
    child_run_id_captured = []
    child_depth_captured = []
    child_parent_run_id_captured = []

    def _parent():
        set_run_context("main")
        parent_run_id_captured.append(ctx.run_id.get())

        # Simulate delegate spawning a child run in an isolated copy
        _run_isolated(_child)

        # Parent context must be unchanged after child returns
        assert ctx.run_id.get() == parent_run_id_captured[0]
        assert ctx.depth.get() == 0
        assert ctx.parent_run_id.get() is None

    def _child():
        set_run_context("sub")
        child_run_id_captured.append(ctx.run_id.get())
        child_depth_captured.append(ctx.depth.get())
        child_parent_run_id_captured.append(ctx.parent_run_id.get())

    _run_isolated(_parent)

    assert child_depth_captured[0] == 1
    assert child_parent_run_id_captured[0] == parent_run_id_captured[0]
    assert child_run_id_captured[0] != parent_run_id_captured[0]
