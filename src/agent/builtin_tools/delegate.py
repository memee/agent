from __future__ import annotations

import os

import openai

from agent import tools
from agent.conversation import Conversation
from agent.run import run


@tools.register("delegate", "builtin")
def delegate(system_prompt: str, task: str, group: str, model: str) -> str:
    """Run a sub-agent with a dedicated system prompt and scoped tool group.

    Creates a fresh conversation, adds the task as the first user message,
    and drives the tool-call loop until a final response. Returns the
    sub-agent's final text response.
    """
    from agent import tools as registry  # re-import to ensure all tools are registered

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    conv = Conversation(system_prompt=system_prompt)
    conv.add_user(task)
    scoped_tools = registry.to_openai_schema(group) or None
    return run(conv, client, model, registry, tools=scoped_tools)
