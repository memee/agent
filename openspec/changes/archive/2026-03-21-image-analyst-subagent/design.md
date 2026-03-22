## Context

The agent framework uses an OpenAI-compatible client and a tool registry. Sub-agents are defined as Markdown+YAML profiles and invoked via the `delegate` tool. Vision models require the image to be delivered as an `image_url` content block in a chat message — there is no mechanism for a tool to inject content into a running agent's conversation mid-run. A sub-agent that receives a remote URL currently has no way to download and visually analyze it without orchestrator support.

## Goals / Non-Goals

**Goals:**

- Provide an `analyze_image` tool that accepts a local image path and a prompt, makes a self-contained vision LLM call, and returns textual analysis.
- Ship an `image_analyst` sub-agent profile that uses `http_download` + `analyze_image` to fully own the download-and-analyze pipeline without orchestrator involvement.

**Non-Goals:**

- Streaming vision responses.
- Multi-image analysis in a single tool call.
- Modifying the conversation layer or run loop.
- Supporting video or audio files.
- Extending `read_file` with base64 mode (separate concern).

## Decisions

### D1: `analyze_image` makes its own self-contained LLM API call

**Decision**: `analyze_image` constructs a one-shot vision request directly via the OpenAI-compatible client, independent of the running agent's conversation history.

**Rationale**: The only way for a vision model to "see" an image is via `image_url` content in a chat message. Injecting into the sub-agent's live conversation would require exposing the `Conversation` object to tools (e.g., via context vars) and changing `run.py` — a significant framework change. A self-contained call inside the tool is simpler, has no side effects on conversation history, and returns the analysis as a plain string tool result.

**Alternative considered**: `show_image` tool that injects `add_user_with_image` into the running conversation via context vars. Rejected — requires framework changes (context vars for Conversation, run.py modifications) with no meaningful benefit for the current use case.

### D2: Image passed as base64 data URL

**Decision**: `analyze_image` reads the file from disk, base64-encodes it, and passes it as `data:<mime>;base64,<data>` in the vision request.

**Rationale**: The tool operates on local files (downloaded by `http_download`). Base64 data URLs work with all OpenAI-compatible providers and do not require the file to be publicly accessible.

### D3: Vision model configured via `VISION_MODEL` env var

**Decision**: `analyze_image` reads the model from `VISION_MODEL` env var, defaulting to `"gpt-4o"`.

**Rationale**: Decouples the vision model from the orchestrating sub-agent's model. The `image_analyst` profile can run on any model while `VISION_MODEL` controls the actual vision call.

### D4: `analyze_image` registers in `filesystem` domain

**Decision**: Domain is `filesystem`; uses `file_path_validator` for path validation.

**Rationale**: The tool only reads a local file. HTTP policy was already enforced by `http_download`. Reusing the filesystem sandbox gives consistent path validation with no additional configuration.

## Risks / Trade-offs

- **Base64 token cost**: Large images inflate the vision API request. → Accepted; callers should pass reasonably-sized files. Future mitigation could add a file size warning.
- **MIME type detection**: Wrong MIME in the data URL can cause API errors. → Mitigation: use `mimetypes.guess_type` with fallback to `"image/jpeg"`.
- **Provider compatibility**: `data:` URLs are supported by OpenAI but may not work on all OpenRouter-routed models. → Documented in tool description.
