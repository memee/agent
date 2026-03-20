import inspect
from typing import Callable, get_type_hints


_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def function_to_tool_schema(name: str, fn: Callable) -> dict:
    """Convert a function to an OpenAI tool schema using type hints and docstring."""
    sig = inspect.signature(fn)
    hints = get_type_hints(fn)

    properties: dict[str, dict] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name == "return":
            continue

        hint = hints.get(param_name)
        json_type = _TYPE_MAP.get(hint, "string") if hint is not None else "string"

        properties[param_name] = {"type": json_type}

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    description = (fn.__doc__ or "").strip()

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
