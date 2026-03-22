from typing import Any, Callable


def tool(
    name: str,
    group: str | None = None,
    validators: "dict[str, Any] | None" = None,
    domain: str | None = None,
) -> Callable:
    """Annotate a function as a tool without registering it anywhere.

    Attaches a _tool_meta attribute to the function with the provided metadata.
    Use ToolsRegistry.include() to collect and register annotated functions.
    """
    def decorator(fn: Callable) -> Callable:
        fn._tool_meta = {
            "name": name,
            "group": group,
            "validators": validators or {},
            "domain": domain,
        }
        return fn
    return decorator
