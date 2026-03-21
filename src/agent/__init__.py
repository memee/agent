from agent.registry import ToolsRegistry
from agent.conversation import Conversation
from agent.run import run
from agent.logging import configure_logging

tools = ToolsRegistry()  # default global instance

import agent.builtin_tools  # noqa: F401 — side-effect import: each module in builtin_tools self-registers via @tools.register

configure_logging()

__all__ = ["ToolsRegistry", "tools", "Conversation", "run"]
