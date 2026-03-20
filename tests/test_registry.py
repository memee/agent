import pytest
from agent.registry import ToolsRegistry
from agent.sandbox import FileSandbox, HttpSandbox, SandboxConfig
from agent.validators import Validator


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


# ---------------------------------------------------------------------------
# Validator and sandbox integration
# ---------------------------------------------------------------------------

def test_execute_applies_validator(registry: ToolsRegistry):
    calls = []

    def double_validator(value, sandbox: SandboxConfig):
        calls.append(value)
        return value * 2

    @registry.register("use_x", validators={"x": double_validator})
    def use_x(x: int) -> int:
        """Use x."""
        return x

    result = registry.execute("use_x", {"x": 3})
    assert result == 6  # validator doubled it
    assert calls == [3]


def test_execute_without_validators_calls_tool_directly(registry: ToolsRegistry):
    @registry.register("identity")
    def identity(x: str) -> str:
        """Identity."""
        return x

    assert registry.execute("identity", {"x": "hello"}) == "hello"


def test_execute_defaults_to_sandbox_default_when_none(registry: ToolsRegistry):
    received_sandbox = []

    def capture_sandbox(value, sandbox: SandboxConfig):
        received_sandbox.append(sandbox)
        return value

    @registry.register("check", validators={"v": capture_sandbox})
    def check(v: str) -> str:
        """Check."""
        return v

    registry.execute("check", {"v": "x"})
    assert received_sandbox[0] == SandboxConfig.default()


def test_execute_uses_provided_sandbox(registry: ToolsRegistry):
    received_sandbox = []

    def capture_sandbox(value, sandbox: SandboxConfig):
        received_sandbox.append(sandbox)
        return value

    @registry.register("check2", validators={"v": capture_sandbox})
    def check2(v: str) -> str:
        """Check2."""
        return v

    off = SandboxConfig.off()
    registry.execute("check2", {"v": "x"}, sandbox=off)
    assert received_sandbox[0] is off


def test_execute_injects_sandbox_to_tool(registry: ToolsRegistry):
    received = []

    @registry.register("needs_sandbox")
    def needs_sandbox(x: str, sandbox: SandboxConfig = SandboxConfig.default()) -> str:
        """Needs sandbox."""
        received.append(sandbox)
        return x

    explicit = SandboxConfig.strict(file_base_dir=__import__("pathlib").Path("/tmp"))
    registry.execute("needs_sandbox", {"x": "hi"}, sandbox=explicit)
    assert received[0] is explicit


def test_sandbox_param_hidden_from_schema(registry: ToolsRegistry):
    @registry.register("with_sandbox")
    def with_sandbox(x: str, sandbox: SandboxConfig = SandboxConfig.default()) -> str:
        """With sandbox."""
        return x

    schema = registry.to_openai_schema()[0]
    props = schema["function"]["parameters"]["properties"]
    assert "sandbox" not in props
    assert "x" in props


# ---------------------------------------------------------------------------
# Domain routing
# ---------------------------------------------------------------------------

def test_execute_domain_routes_filesystem_sub_config(registry: ToolsRegistry):
    received = []

    def capture(value, sandbox):
        received.append(sandbox)
        return value

    @registry.register("fs_tool", domain="filesystem", validators={"v": capture})
    def fs_tool(v: str) -> str:
        """Filesystem tool."""
        return v

    cfg = SandboxConfig.strict(file_base_dir=__import__("pathlib").Path("/tmp"))
    registry.execute("fs_tool", {"v": "x"}, sandbox=cfg)
    assert isinstance(received[0], FileSandbox)
    assert received[0] is cfg.filesystem


def test_execute_domain_routes_http_sub_config(registry: ToolsRegistry):
    received = []

    def capture(value, sandbox):
        received.append(sandbox)
        return value

    @registry.register("http_tool", domain="http", validators={"v": capture})
    def http_tool(v: str) -> str:
        """HTTP tool."""
        return v

    cfg = SandboxConfig.strict(file_base_dir=__import__("pathlib").Path("/tmp"))
    registry.execute("http_tool", {"v": "x"}, sandbox=cfg)
    assert isinstance(received[0], HttpSandbox)
    assert received[0] is cfg.http


def test_execute_domain_injects_sub_config_to_tool(registry: ToolsRegistry):
    received = []

    @registry.register("fs_inject", domain="filesystem")
    def fs_inject(x: str, sandbox: FileSandbox = FileSandbox.default()) -> str:
        """Needs FileSandbox."""
        received.append(sandbox)
        return x

    cfg = SandboxConfig(filesystem=FileSandbox.strict(__import__("pathlib").Path("/tmp")))
    registry.execute("fs_inject", {"x": "hi"}, sandbox=cfg)
    assert isinstance(received[0], FileSandbox)
    assert received[0] is cfg.filesystem


def test_execute_no_domain_passes_full_sandbox(registry: ToolsRegistry):
    received = []

    @registry.register("no_domain")
    def no_domain(x: str, sandbox: SandboxConfig = SandboxConfig.default()) -> str:
        """No domain tool."""
        received.append(sandbox)
        return x

    cfg = SandboxConfig.off()
    registry.execute("no_domain", {"x": "hi"}, sandbox=cfg)
    assert received[0] is cfg
