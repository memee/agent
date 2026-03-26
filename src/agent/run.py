from __future__ import annotations

import contextvars as _cv
import json
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import openai

import agent.context as _ctx
import agent.scrub as _scrub
from agent.context import set_run_context
from agent.conversation import Conversation
from agent.registry import ToolsRegistry
from agent.sandbox import SandboxConfig
from agent.secrets import SecretsStore

logger = logging.getLogger("agent")


def run(
    messages: Conversation,
    client: "openai.OpenAI",
    model: str,
    registry: ToolsRegistry,
    tools: list[dict] | None = None,
    sandbox: SandboxConfig | None = None,
    max_iterations: int = 10,
    agent_name: str = "main",
    secrets: SecretsStore | None = None,
    max_completion_tokens: int | None = None,
) -> str:
    """Drive the tool-call cycle until a final text response or iteration limit.

    Mutates `messages` by appending every assistant turn and tool result.
    Returns the final assistant text response.

    Execution context is isolated via copy_context() so sub-agent calls do not
    overwrite the parent's context variables.
    """
    ctx = _cv.copy_context()
    return ctx.run(
        _run_in_context,
        messages, client, model, registry, tools, sandbox, max_iterations, agent_name, secrets,
        max_completion_tokens,
    )


def _run_in_context(
    messages: Conversation,
    client: "openai.OpenAI",
    model: str,
    registry: ToolsRegistry,
    tools: list[dict] | None = None,
    sandbox: SandboxConfig | None = None,
    max_iterations: int = 10,
    agent_name: str = "main",
    secrets: SecretsStore | None = None,
    max_completion_tokens: int | None = None,
) -> str:
    set_run_context(agent_name)
    effective_sandbox = sandbox if sandbox is not None else SandboxConfig.default()

    if secrets is not None:
        _scrub.register_runtime_secrets(secrets.values())

    for i in range(max_iterations):
        _ctx.iteration.set(i + 1)

        kwargs: dict = {"model": model, "messages": messages.messages}
        if tools:
            kwargs["tools"] = tools
        if max_completion_tokens is not None:
            kwargs["max_completion_tokens"] = max_completion_tokens

        t0 = time.monotonic()
        response = client.chat.completions.create(**kwargs)
        duration_ms = round((time.monotonic() - t0) * 1000, 1)

        usage = response.usage
        logger.info(
            "llm_call",
            extra={
                "model": model,
                "duration_ms": duration_ms,
                "prompt_tokens": usage.prompt_tokens if usage is not None else None,
                "completion_tokens": usage.completion_tokens if usage is not None else None,
                "total_tokens": usage.total_tokens if usage is not None else None,
            },
        )

        assistant_message = response.choices[0].message

        # Append raw assistant message dict to conversation
        messages.add_assistant(assistant_message.model_dump(exclude_unset=False))

        # Log reasoning text that precedes tool calls (final response is logged separately)
        if assistant_message.tool_calls and assistant_message.content:
            logger.info("agent_reasoning", extra={"content": assistant_message.content})

        if not assistant_message.tool_calls:
            final = assistant_message.content or ""
            logger.info("agent_final_response", extra={"content": final})
            return final

        # Execute each tool call and append results
        for tool_call in assistant_message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            result = str(registry.execute(name, args, sandbox=effective_sandbox, secrets=secrets))
            messages.add_tool_result(tool_call.id, result)

    raise RuntimeError(
        f"Agent did not produce a final response within {max_iterations} iterations."
    )
