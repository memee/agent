## ADDED Requirements

### Requirement: Conversation supports multimodal user messages with an image URL

`Conversation` SHALL expose a method `add_user_with_image(text: str, image_url: str)`.

When called, it SHALL append a user message whose `content` is a list of two content blocks
in OpenAI vision format:

1. `{"type": "text", "text": text}`
2. `{"type": "image_url", "image_url": {"url": image_url}}`

This method SHALL be the only supported way to add image content — `add_user` SHALL continue
to accept only plain text and append `{"role": "user", "content": text}` unchanged.

#### Scenario: Multimodal message has correct structure

- **WHEN** `add_user_with_image("Describe this image", "https://example.com/img.png")` is called
- **THEN** the last entry in `messages` is `{"role": "user", "content": [{"type": "text", "text": "Describe this image"}, {"type": "image_url", "image_url": {"url": "https://example.com/img.png"}}]}`

#### Scenario: Multimodal message is appended after existing messages

- **WHEN** a `Conversation` with a system prompt calls `add_user_with_image(...)`
- **THEN** `messages` has two entries: the system message first, then the multimodal user message

#### Scenario: add_user still produces plain text messages

- **WHEN** `add_user("Hello")` is called on the same Conversation class
- **THEN** the appended message is `{"role": "user", "content": "Hello"}` (a plain string, not a list)
