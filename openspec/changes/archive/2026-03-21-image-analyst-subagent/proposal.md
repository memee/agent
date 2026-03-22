## Why

The framework has no way for a sub-agent to visually analyze an image autonomously — vision models require the image to be delivered as an `image_url` content block in the conversation, but there is no tool that converts a local file into that format. A sub-agent that receives a URL must rely on the orchestrator to download, encode, and re-inject the image, which breaks autonomy.

## What Changes

- New tool `analyze_image(image_path, prompt)` — reads a local image file, base64-encodes it, constructs a data URL, and makes a self-contained call to a vision-capable LLM; returns the textual analysis.
- New sub-agent profile `image_analyst` — uses `http_download` + `analyze_image` to fully own the pipeline: receive URL or local path → download if needed → analyze → return description and file path.

## Capabilities

### New Capabilities

- `analyze-image-tool`: New builtin tool that performs vision analysis on a local image file by calling a configurable vision LLM via the OpenAI-compatible client.
- `image-analyst-subagent`: Sub-agent profile that autonomously handles image analysis tasks end-to-end.

### Modified Capabilities

_(none)_

## Impact

- New file: `src/agent/builtin_tools/analyze_image.py`
- New file: `src/agent/subagents/image_analyst.md`
- New env var: `VISION_MODEL` (default: `gpt-4o`)
- The `analyze_image` tool registers in the `filesystem` domain so the existing filesystem sandbox validates the image path.
- No breaking changes to existing tools or APIs.
