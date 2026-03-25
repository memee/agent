## MODIFIED Requirements

### Requirement: analyze_image tool analyzes a local image file using a vision LLM

The library SHALL register a `analyze_image` tool in the `"builtin"` group with `domain="filesystem"`.

It SHALL accept:

- `image_path: str` — path to the local image file to analyze
- `prompt: str` — the question or instruction for the vision model
- `as_ascii: bool = False` — when `True`, convert the image to ASCII art and send
  as plain text instead of a multimodal attachment

It SHALL be registered with `validators={"image_path": file_path_validator}` so the path is validated and resolved before the file is read.

**When `as_ascii=False` (default):** the tool SHALL read the resolved file as raw bytes,
base64-encode them, detect the MIME type via `mimetypes.guess_type` (falling back to
`"image/jpeg"`), and construct a one-shot multimodal vision API request:

```
[{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": "data:<mime>;base64,<data>"}},
    {"type": "text", "text": <prompt>}
]}]
```

**When `as_ascii=True`:** the tool SHALL call `_image_to_ascii(image_path)` and send
a plain-text message combining the prompt and the ASCII representation:

```
[{"role": "user", "content": "<prompt>\n\nASCII representation of the image:\n```\n<ascii_art>\n```"}]
```

In both modes it SHALL obtain the model name from `VISION_MODEL` env var (default `"gpt-4o"`)
and use `create_client()`. It SHALL return the text content of the first choice.

#### Scenario: as_ascii=False sends multimodal attachment (default behaviour unchanged)

- **WHEN** `analyze_image` is called with a valid local image path and `as_ascii=False`
- **THEN** the image bytes are base64-encoded and sent as a multimodal message

#### Scenario: as_ascii=True sends plain-text with ASCII art

- **WHEN** `analyze_image` is called with `as_ascii=True`
- **THEN** the image is converted to ASCII art and sent as a plain-text message with no image attachment

#### Scenario: MIME type detected from extension (as_ascii=False)

- **WHEN** `analyze_image` is called with `as_ascii=False` and a file named `photo.png`
- **THEN** the data URL uses `image/png` as the MIME type

#### Scenario: Unknown extension falls back to image/jpeg (as_ascii=False)

- **WHEN** `analyze_image` is called with `as_ascii=False` and a file with an unrecognized extension
- **THEN** the data URL uses `image/jpeg` as the MIME type

#### Scenario: VISION_MODEL env var selects the model

- **WHEN** `VISION_MODEL=openai/gpt-5.4` is set
- **THEN** the API request uses `model="openai/gpt-5.4"` in both modes

#### Scenario: Path outside sandbox is rejected

- **WHEN** `analyze_image` is called with a path outside `FileSandbox.base_dir`
- **THEN** raises `PermissionError` from `file_path_validator` before any file I/O
