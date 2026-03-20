from agent.conversation import Conversation


def test_empty_conversation():
    conv = Conversation()
    assert conv.messages == []


def test_system_prompt_in_constructor():
    conv = Conversation(system_prompt="You are helpful.")
    assert conv.messages[0] == {"role": "system", "content": "You are helpful."}


def test_add_system():
    conv = Conversation()
    conv.add_system("Be concise.")
    assert conv.messages[-1] == {"role": "system", "content": "Be concise."}


def test_add_user():
    conv = Conversation()
    conv.add_user("Hello!")
    assert conv.messages[-1] == {"role": "user", "content": "Hello!"}


def test_add_assistant():
    conv = Conversation()
    msg = {"role": "assistant", "content": "Hi there."}
    conv.add_assistant(msg)
    assert conv.messages[-1] == msg


def test_add_tool_result():
    conv = Conversation()
    conv.add_tool_result("call_123", "42")
    assert conv.messages[-1] == {
        "role": "tool",
        "tool_call_id": "call_123",
        "content": "42",
    }


def test_all_roles_in_sequence():
    conv = Conversation(system_prompt="sys")
    conv.add_user("user msg")
    conv.add_assistant({"role": "assistant", "content": "reply"})
    conv.add_tool_result("call_1", "result")
    roles = [m["role"] for m in conv.messages]
    assert roles == ["system", "user", "assistant", "tool"]
