from agent.tool import tool


@tool("hello_world", group="builtin")
def hello_world(name: str = "World") -> str:
    """Return a friendly greeting. Useful for verifying the agent is working."""
    return f"Hello, {name}!"
