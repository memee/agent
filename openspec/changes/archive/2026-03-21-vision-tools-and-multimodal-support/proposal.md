## Why

The agent lacks tools to send HTTP POST requests, download binary files, and write files to disk — all required for vision-based tasks that involve fetching images, analyzing them with a multimodal model, and submitting answers to an external API. Additionally, the `delegate` tool and `Conversation` class only support text messages, making it impossible to pass images to a vision subagent.

## What Changes

- Add `http_post` builtin tool — sends HTTP POST with a JSON body, analogous to `http_get`
- Add `http_download` builtin tool — downloads a binary file from a URL and writes it directly to disk (binary data never enters the LLM context window)
- Add `write_file` builtin tool — writes text content to a file on disk, analogous to `read_file`
- Add multimodal message support to `Conversation` — allow user messages with both text and `image_url` content blocks (OpenAI vision format)
- Extend `delegate` tool with an optional `image_url` parameter — when provided, the subagent's first user message is multimodal, enabling vision models to see the image directly

## Capabilities

### New Capabilities

- `http-post-tool`: HTTP POST with JSON body, sandbox-validated, analogous to `http-get-tool`
- `http-download-tool`: Download binary file from URL and save to local path; respects both HTTP and filesystem sandboxes
- `write-file-tool`: Write UTF-8 text content to a file; respects filesystem sandbox
- `multimodal-conversation`: `Conversation` supports user messages with `image_url` content blocks for vision models

### Modified Capabilities

- `delegate-tool`: Adds optional `image_url` parameter to create a multimodal first user message for the subagent

## Impact

- `src/agent/builtin_tools/http_post.py` — new file
- `src/agent/builtin_tools/http_download.py` — new file
- `src/agent/builtin_tools/write_file.py` — new file
- `src/agent/builtin_tools/__init__.py` — new imports
- `src/agent/conversation.py` — add multimodal user message support
- `src/agent/builtin_tools/delegate.py` — add `image_url` parameter
- `tests/` — new tests for all new tools and modified behaviors
