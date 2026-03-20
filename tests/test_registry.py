import pytest
from agent.registry import ToolsRegistry


@pytest.fixture
def registry() -> ToolsRegistry:
    return ToolsRegistry()


def test_register_and_execute(registry: ToolsRegistry):
    @registry.register("greet")
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello {name}!"

    assert registry.execute("greet", {"name": "World"}) == "Hello World!"


def test_register_returns_original_function(registry: ToolsRegistry):
    @registry.register("fn")
    def fn(x: int) -> int:
        """Fn."""
        return x * 2

    assert fn(5) == 10  # decorator is transparent


def test_names_all(registry: ToolsRegistry):
    @registry.register("a")
    def a() -> None: ...

    @registry.register("b")
    def b() -> None: ...

    assert sorted(registry.names()) == ["a", "b"]


def test_names_filtered_by_group(registry: ToolsRegistry):
    @registry.register("x", "g1")
    def x() -> None: ...

    @registry.register("y", "g2")
    def y() -> None: ...

    @registry.register("z")
    def z() -> None: ...

    assert registry.names("g1") == ["x"]
    assert registry.names("g2") == ["y"]


def test_groups(registry: ToolsRegistry):
    @registry.register("a", "g1")
    def a() -> None: ...

    @registry.register("b", "g2")
    def b() -> None: ...

    @registry.register("c")
    def c() -> None: ...

    assert sorted(registry.groups()) == ["g1", "g2"]


def test_to_openai_schema_all(registry: ToolsRegistry):
    @registry.register("fn")
    def fn(x: str) -> str:
        """Do something."""
        ...

    schemas = registry.to_openai_schema()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "fn"
    assert schemas[0]["function"]["description"] == "Do something."


def test_to_openai_schema_filtered_by_group(registry: ToolsRegistry):
    @registry.register("a", "g1")
    def a() -> None: ...

    @registry.register("b", "g2")
    def b() -> None: ...

    schemas = registry.to_openai_schema("g1")
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "a"


def test_execute_unknown_tool_raises(registry: ToolsRegistry):
    with pytest.raises(KeyError, match="unknown"):
        registry.execute("unknown", {})


def test_execute_passes_kwargs(registry: ToolsRegistry):
    @registry.register("add")
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    assert registry.execute("add", {"a": 3, "b": 4}) == 7


def test_schema_required_reflects_defaults(registry: ToolsRegistry):
    @registry.register("fn")
    def fn(required: str, optional: bool = False) -> None:
        """Fn."""
        ...

    schema = registry.to_openai_schema()[0]
    params = schema["function"]["parameters"]
    assert "required" in params["required"]
    assert "optional" not in params["required"]
