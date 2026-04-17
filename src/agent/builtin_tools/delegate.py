from __future__ import annotations

import agent.context as _ctx
from agent.builtin_tools.parallel_delegate import delegate_async
from agent.client import create_async_client
from agent.conversation import Conversation
from agent.profile import profile_registry, sandbox_from_profile
from agent.run import run
from agent.scheduler import scheduler_var
from agent.validators import http_url_validator


def _build_delegate_schema() -> dict:
    """Build the delegate tool schema dynamically from loaded profiles."""
    profiles = profile_registry.all()
    profile_names = [p.name for p in profiles]

    return {
        "type": "function",
        "function": {
            "name": "delegate",
            "description": "Run a sub-agent using a named profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "string",
                        "enum": profile_names,
                        "description": "Name of the sub-agent profile to use.",
                    },
                    "task": {
                        "type": "string",
                        "description": "The task for the sub-agent to complete.",
                    },
                    "image_url": {
                        "type": "string",
                        "description": (
                            "Optional URL of an image to pass to the sub-agent. "
                            "When provided, the sub-agent's first message will be multimodal "
                            "(text + image), enabling vision models to see the image directly."
                        ),
                    },
                },
                "required": ["profile", "task"],
            },
        },
    }


def _refresh_delegate_schema() -> None:
    """Refresh the registered delegate schema from the current profile registry."""
    from agent import tools

    if "delegate" in tools._tools:
        tools._tools["delegate"]["schema"] = _build_delegate_schema()


async def delegate(profile: str, task: str, image_url: str | None = None) -> str:
    """Run a sub-agent using a named profile.

    Spawns the sub-agent via delegate_async(), awaits its completion event,
    and returns the sub-agent's final text response.

    If image_url is provided, it is validated before the sub-agent starts.
    """
    agent_profile = profile_registry.get(profile)
    sandbox = sandbox_from_profile(agent_profile.sandbox_config)

    if image_url:
        http_url_validator(image_url, sandbox.http)

    scheduler = scheduler_var.get()
    call_id: str | None = _ctx.current_call_id.get()

    if scheduler is None:
        # Fallback: run inline without scheduler (backwards compat / tests without scheduler)
        from agent import tools as registry

        client = create_async_client()
        conv = Conversation(system_prompt=agent_profile.system_prompt)
        if image_url:
            conv.add_user_with_image(task, image_url)
        else:
            conv.add_user(task)
        scoped_tools = registry.to_openai_schema_by_names(agent_profile.tools) or None
        return await run(conv, client, agent_profile.model, registry, tools=scoped_tools, sandbox=sandbox, agent_name=profile)

    # Spawn child agent asynchronously
    await delegate_async(profile, task, image_url)

    # Wait for the result via the event registered by delegate_async
    if call_id and call_id in scheduler._events:
        await scheduler._events[call_id].wait()
        return scheduler.get_result(call_id) or ""

    return ""


# Register the delegate tool manually with a dynamic schema.
# Cannot use @tool() because the schema is built dynamically from loaded profiles.
def _register_delegate() -> None:
    from agent import tools
    tools._tools["delegate"] = {
        "fn": delegate,
        "group": "builtin",
        "domain": None,
        "schema": _build_delegate_schema(),
        "validators": {},
    }


profile_registry.add_change_listener(_refresh_delegate_schema)
_register_delegate()
