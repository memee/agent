from __future__ import annotations

from agent import tools
from agent.client import create_client
from agent.conversation import Conversation
from agent.profile import profile_registry, sandbox_from_profile
from agent.run import run


def _build_delegate_schema() -> dict:
    """Build the delegate tool schema dynamically from loaded profiles."""
    profiles = profile_registry.all()
    profile_names = [p.name for p in profiles]
    descriptions = "\n".join(f"- {p.name}: {p.description}" for p in profiles)

    return {
        "type": "function",
        "function": {
            "name": "delegate",
            "description": (
                "Run a sub-agent using a named profile.\n\n"
                "Available profiles:\n" + descriptions
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "string",
                        "enum": profile_names,
                        "description": (
                            "Name of the sub-agent profile to use. "
                            "Available profiles:\n" + descriptions
                        ),
                    },
                    "task": {
                        "type": "string",
                        "description": "The task for the sub-agent to complete.",
                    },
                },
                "required": ["profile", "task"],
            },
        },
    }


def delegate(profile: str, task: str) -> str:
    """Run a sub-agent using a named profile.

    Looks up the named profile from the registry, builds a SandboxConfig
    from the profile's sandbox config, creates a fresh Conversation with
    the profile's system prompt, and calls run() with the profile's tool
    list and model. Returns the sub-agent's final text response.
    """
    agent_profile = profile_registry.get(profile)
    sandbox = sandbox_from_profile(agent_profile.sandbox_config)

    from agent import tools as registry  # re-import to ensure all tools are registered

    client = create_client()
    conv = Conversation(system_prompt=agent_profile.system_prompt)
    conv.add_user(task)
    scoped_tools = registry.to_openai_schema_by_names(agent_profile.tools) or None
    return run(conv, client, agent_profile.model, registry, tools=scoped_tools, sandbox=sandbox)


# Register the delegate tool manually with a dynamic schema
tools._tools["delegate"] = {
    "fn": delegate,
    "group": "builtin",
    "domain": None,
    "schema": _build_delegate_schema(),
    "validators": {},
}
