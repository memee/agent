from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import openai

from agent.conversation import Conversation
from agent.registry import ToolsRegistry
from agent.sandbox import SandboxConfig


def run(
    messages: Conversation,
    client: "openai.OpenAI",
    model: str,
    registry: ToolsRegistry,
    tools: list[dict] | None = None,
    sandbox: SandboxConfig | None = None,
    max_iterations: int = 10,
) -> str:
    """Drive the tool-call cycle until a final text response or iteration limit.

    Mutates `messages` by appending every assistant turn and tool result.
    Returns the final assistant text response.
    """
    effective_sandbox = sandbox if sandbox is not None else SandboxConfig.default()
    for _ in range(max_iterations):
        kwargs: dict = {"model": model, "messages": messages.messages}
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        assistant_message = response.choices[0].message

        # Append raw assistant message dict to conversation
        messages.add_assistant(assistant_message.model_dump(exclude_unset=False))

        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # Execute each tool call and append results
        for tool_call in assistant_message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            result = str(registry.execute(name, args, sandbox=effective_sandbox))
            messages.add_tool_result(tool_call.id, result)

    raise RuntimeError(
        f"Agent did not produce a final response within {max_iterations} iterations."
    )
