from __future__ import annotations


class Conversation:
    """Manages message history in OpenAI list-of-dicts format."""

    def __init__(self, system_prompt: str | None = None) -> None:
        self._messages: list[dict] = []
        if system_prompt is not None:
            self.add_system(system_prompt)

    @property
    def messages(self) -> list[dict]:
        """Return the raw message list for passing to the OpenAI API."""
        return self._messages

    def add_system(self, content: str) -> None:
        self._messages.append({"role": "system", "content": content})

    def add_user(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def add_user_with_image(self, text: str, image_url: str) -> None:
        """Append a multimodal user message with text and an image URL.

        Produces an OpenAI vision-compatible content list:
        [{"type": "text", "text": text}, {"type": "image_url", "image_url": {"url": image_url}}]
        """
        self._messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        })

    def add_assistant(self, message: dict) -> None:
        """Append a raw assistant message dict (may include tool_calls)."""
        self._messages.append(message)

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self._messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        })
