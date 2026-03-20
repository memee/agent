import pytest
from agent.schema import function_to_tool_schema


def test_basic_types():
    def fn(name: str, count: int, ratio: float, active: bool) -> str:
        """A test function."""
        ...

    schema = function_to_tool_schema("fn", fn)
    props = schema["function"]["parameters"]["properties"]
    assert props["name"]["type"] == "string"
    assert props["count"]["type"] == "integer"
    assert props["ratio"]["type"] == "number"
    assert props["active"]["type"] == "boolean"


def test_required_vs_optional():
    def fn(required_arg: str, optional_arg: str = "default") -> str:
        """Docstring."""
        ...

    schema = function_to_tool_schema("fn", fn)
    params = schema["function"]["parameters"]
    assert "required_arg" in params["required"]
    assert "optional_arg" not in params["required"]


def test_description_from_docstring():
    def fn(x: str) -> str:
        """Greet someone by name."""
        ...

    schema = function_to_tool_schema("fn", fn)
    assert schema["function"]["description"] == "Greet someone by name."


def test_empty_docstring():
    def fn(x: str) -> None:
        pass

    schema = function_to_tool_schema("fn", fn)
    assert schema["function"]["description"] == ""


def test_unknown_type_falls_back_to_string():
    def fn(data: list) -> None:
        """Fn."""
        ...

    schema = function_to_tool_schema("fn", fn)
    assert schema["function"]["parameters"]["properties"]["data"]["type"] == "string"


def test_no_type_hint_falls_back_to_string():
    def fn(x) -> None:
        """Fn."""
        ...

    schema = function_to_tool_schema("fn", fn)
    assert schema["function"]["parameters"]["properties"]["x"]["type"] == "string"


def test_schema_structure():
    def fn(x: str) -> None:
        """Fn."""
        ...

    schema = function_to_tool_schema("greet", fn)
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "greet"
    assert "parameters" in schema["function"]
    assert schema["function"]["parameters"]["type"] == "object"


def test_no_parameters():
    def fn() -> str:
        """No args."""
        ...

    schema = function_to_tool_schema("fn", fn)
    assert schema["function"]["parameters"]["properties"] == {}
    assert schema["function"]["parameters"]["required"] == []
