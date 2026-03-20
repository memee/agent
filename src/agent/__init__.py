from agent.registry import ToolsRegistry

tools = ToolsRegistry()  # default global instance

import agent.builtin_tools  # noqa: F401 — side-effect import: each module in builtin_tools self-registers via @tools.register

__all__ = ["ToolsRegistry", "tools"]
