from agent.registry import ToolsRegistry
from agent.conversation import Conversation
from agent.run import run, run_sync
from agent.logging import configure_logging
from agent.tool import tool
from agent.hitl import HITLHandler, HITLRequest, TerminalHITLHandler, get_hitl_handler

tools = ToolsRegistry()  # default global instance
tools.include("agent.builtin_tools")  # explicit registration of all builtin tools

configure_logging()

__all__ = [
    "ToolsRegistry", "tool", "tools", "Conversation", "run", "run_sync",
    "HITLHandler", "HITLRequest", "TerminalHITLHandler", "get_hitl_handler",
]
