import importlib
import inspect
import logging
import pkgutil
import time
import types
from typing import Any, Callable

from agent.sandbox import SandboxConfig
from agent.schema import function_to_tool_schema

logger = logging.getLogger("agent")


class ToolsRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}  # name → {fn, group, domain, schema, validators}

    def register(
        self,
        name: str,
        group: str | None = None,
        validators: "dict[str, Any] | None" = None,
        domain: str | None = None,
    ) -> Callable:
        """Decorator that registers a function as a tool."""
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = {
                "fn": fn,
                "group": group,
                "domain": domain,
                "schema": function_to_tool_schema(name, fn),
                "validators": validators or {},
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

    def to_openai_schema_by_names(self, names: list[str]) -> list[dict]:
        """Return OpenAI tool dicts for the given list of tool names."""
        return [
            self._tools[name]["schema"]
            for name in names
            if name in self._tools
        ]

    def execute(self, name: str, args: dict, sandbox: SandboxConfig | None = None) -> Any:
        """Call registered tool by name with given arguments, applying validators first."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        effective_sandbox = sandbox if sandbox is not None else SandboxConfig.default()
        entry = self._tools[name]
        domain = entry["domain"]
        domain_sandbox = getattr(effective_sandbox, domain) if domain is not None else effective_sandbox
        validated_args = dict(args)
        for arg_name, validator in entry["validators"].items():
            if arg_name in validated_args:
                validated_args[arg_name] = validator(validated_args[arg_name], domain_sandbox)
        # Inject sandbox if the tool function accepts it
        fn = entry["fn"]
        if "sandbox" in inspect.signature(fn).parameters:
            validated_args["sandbox"] = domain_sandbox

        logger.info("tool_call_start", extra={"tool": name, "tool_args": args})
        t0 = time.monotonic()
        try:
            result = fn(**validated_args)
        except Exception as exc:
            duration_ms = round((time.monotonic() - t0) * 1000, 1)
            logger.error(
                "tool_call_error",
                extra={"tool": name, "duration_ms": duration_ms, "error": str(exc)},
            )
            raise
        duration_ms = round((time.monotonic() - t0) * 1000, 1)
        logger.info(
            "tool_call_end",
            extra={
                "tool": name,
                "duration_ms": duration_ms,
                "result_preview": str(result)[:200],
            },
        )
        return result

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

    def include(self, module_or_package: "types.ModuleType | str") -> None:
        """Register all @tool-annotated functions from a module or package.

        Accepts a module object or a dotted string name. If the target is a
        package (has __path__), all submodules are imported and scanned
        recursively. Functions without a _tool_meta attribute are silently
        skipped.
        """
        if isinstance(module_or_package, str):
            module_or_package = importlib.import_module(module_or_package)

        self._collect_from_module(module_or_package)

        if hasattr(module_or_package, "__path__"):
            for finder, name, _is_pkg in pkgutil.walk_packages(
                module_or_package.__path__,
                prefix=module_or_package.__name__ + ".",
            ):
                submodule = importlib.import_module(name)
                self._collect_from_module(submodule)

    def _collect_from_module(self, module: "types.ModuleType") -> None:
        """Register all @tool-annotated callables found in module's namespace."""
        for obj in vars(module).values():
            if callable(obj) and hasattr(obj, "_tool_meta"):
                meta = obj._tool_meta
                self._tools[meta["name"]] = {
                    "fn": obj,
                    "group": meta["group"],
                    "domain": meta["domain"],
                    "schema": function_to_tool_schema(meta["name"], obj),
                    "validators": meta["validators"],
                }
