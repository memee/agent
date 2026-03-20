from typing import Any, Callable

from agent.schema import function_to_tool_schema


class ToolsRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}  # name → {fn, group, schema}

    def register(self, name: str, group: str | None = None) -> Callable:
        """Decorator that registers a function as a tool."""
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = {
                "fn": fn,
                "group": group,
                "schema": function_to_tool_schema(name, fn),
            }
            return fn
        return decorator

    def to_openai_schema(self, group: str | None = None) -> list[dict]:
        """Return OpenAI tool dicts — all tools or filtered by group."""
        return [
            entry["schema"]
            for entry in self._tools.values()
            if group is None or entry["group"] == group
        ]

    def execute(self, name: str, args: dict) -> Any:
        """Call registered tool by name with given arguments."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        return self._tools[name]["fn"](**args)

    def names(self, group: str | None = None) -> list[str]:
        """Return list of tool names — all or filtered by group."""
        return [
            name
            for name, entry in self._tools.items()
            if group is None or entry["group"] == group
        ]

    def groups(self) -> list[str]:
        """Return list of all registered group names."""
        return list({entry["group"] for entry in self._tools.values() if entry["group"] is not None})
