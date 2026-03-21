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


# ---------------------------------------------------------------------------
# add_user_with_image
# ---------------------------------------------------------------------------

def test_add_user_with_image_structure():
    conv = Conversation()
    conv.add_user_with_image("Describe this image", "https://example.com/img.png")
    msg = conv.messages[-1]
    assert msg["role"] == "user"
    assert msg["content"] == [
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", "image_url": {"url": "https://example.com/img.png"}},
    ]


def test_add_user_with_image_appended_after_existing():
    conv = Conversation(system_prompt="You are a vision model.")
    conv.add_user_with_image("What is in this image?", "https://example.com/photo.jpg")
    assert len(conv.messages) == 2
    assert conv.messages[0]["role"] == "system"
    assert conv.messages[1]["role"] == "user"


def test_add_user_still_produces_plain_string():
    conv = Conversation()
    conv.add_user("Hello")
    msg = conv.messages[-1]
    assert msg == {"role": "user", "content": "Hello"}
