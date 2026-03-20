from agent import tools


@tools.register("hello_world", "builtin")
def hello_world(name: str = "World") -> str:
    """Return a friendly greeting. Useful for verifying the agent is working."""
    return f"Hello, {name}!"
