from agent import tools


def test_hello_world_registered():
    assert "hello_world" in tools.names()


def test_hello_world_default():
    assert tools.execute("hello_world", {}) == "Hello, World!"


def test_hello_world_with_name():
    assert tools.execute("hello_world", {"name": "Agent"}) == "Hello, Agent!"


def test_hello_world_in_builtin_group():
    assert "hello_world" in tools.names("builtin")


def test_hello_world_schema():
    schemas = tools.to_openai_schema("builtin")
    assert any(s["function"]["name"] == "hello_world" for s in schemas)
