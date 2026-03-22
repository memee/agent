## ADDED Requirements

### Requirement: analyze_image tool analyzes a local image file using a vision LLM

The library SHALL register a `analyze_image` tool in the `"builtin"` group with `domain="filesystem"`.

It SHALL accept:

- `image_path: str` — path to the local image file to analyze
- `prompt: str` — the question or instruction for the vision model (e.g., `"Describe this image"`)

It SHALL be registered with `validators={"image_path": file_path_validator}` so the path is validated and resolved before the file is read.

It SHALL read the resolved file as raw bytes, base64-encode them, and detect the MIME type via `mimetypes.guess_type`, falling back to `"image/jpeg"` if detection fails.

It SHALL construct a one-shot vision API request in OpenAI chat format:

```
[{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": "data:<mime>;base64,<data>"}},
    {"type": "text", "text": <prompt>}
]}]
```

It SHALL obtain the vision model name from the `VISION_MODEL` environment variable, defaulting to `"gpt-4o"` if the variable is absent or empty.

It SHALL use the same OpenAI-compatible client returned by `get_client()`.

It SHALL return the text content of the first choice from the API response as a string.

#### Scenario: Image is analyzed and description returned

- **WHEN** `analyze_image` is called with a valid local image path and a prompt
- **THEN** the image bytes are base64-encoded and sent to the vision LLM, and the LLM's text response is returned

#### Scenario: MIME type detected from extension

- **WHEN** `analyze_image` is called with a file named `photo.png`
- **THEN** the data URL uses `image/png` as the MIME type

#### Scenario: Unknown extension falls back to image/jpeg

- **WHEN** `analyze_image` is called with a file that has an unrecognized extension
- **THEN** the data URL uses `image/jpeg` as the MIME type

#### Scenario: VISION_MODEL env var selects the model

- **WHEN** `VISION_MODEL=openai/gpt-5.4` is set in the environment
- **THEN** the API request is sent with `model="openai/gpt-5.4"`

#### Scenario: VISION_MODEL absent defaults to gpt-4o

- **WHEN** `VISION_MODEL` is not set in the environment
- **THEN** the API request is sent with `model="gpt-4o"`

#### Scenario: Path outside sandbox is rejected

- **WHEN** `analyze_image` is called with a path outside the `FileSandbox.base_dir`
- **THEN** raises `PermissionError` from `file_path_validator` before any file I/O

### Requirement: analyze_image is auto-registered on import

`analyze_image` SHALL be registered automatically when `from agent import tools` is executed.

#### Scenario: analyze_image available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"analyze_image"` appears in `tools.names("builtin")`
