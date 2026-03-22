from __future__ import annotations

from agent.client import create_client
from agent.conversation import Conversation
from agent.profile import profile_registry, sandbox_from_profile
from agent.run import run
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


def delegate(profile: str, task: str, image_url: str | None = None) -> str:
    """Run a sub-agent using a named profile.

    Looks up the named profile from the registry, builds a SandboxConfig
    from the profile's sandbox config, creates a fresh Conversation with
    the profile's system prompt, and calls run() with the profile's tool
    list and model. Returns the sub-agent's final text response.

    If image_url is provided, the sub-agent's first user message is multimodal
    (text + image_url content blocks), enabling vision models to see the image.
    The image_url is validated against the HTTP sandbox before the sub-agent starts.
    """
    agent_profile = profile_registry.get(profile)
    sandbox = sandbox_from_profile(agent_profile.sandbox_config)

    if image_url is not None:
        http_url_validator(image_url, sandbox.http)

    from agent import tools as registry

    client = create_client()
    conv = Conversation(system_prompt=agent_profile.system_prompt)
    if image_url is not None:
        conv.add_user_with_image(task, image_url)
    else:
        conv.add_user(task)
    scoped_tools = registry.to_openai_schema_by_names(agent_profile.tools) or None
    return run(conv, client, agent_profile.model, registry, tools=scoped_tools, sandbox=sandbox, agent_name=profile)


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

_register_delegate()
