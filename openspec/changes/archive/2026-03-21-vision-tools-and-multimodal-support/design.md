## Context

The agent framework has `http_get`, `read_file`, and `delegate` as its primary I/O tools. Vision tasks require three additional capabilities: sending HTTP POST requests (to submit answers), downloading binary files to disk (images bypass the context window), and writing text files. Additionally, the `Conversation` class and `delegate` tool only support text messages — vision models need `image_url` content blocks to receive images.

The existing pattern (see `http_get.py`, `read_file.py`) is well-established: a module-level `@tools.register(...)` decorator registers the tool with sandbox injection via a `validators` dict. New tools follow this exact pattern.

## Goals / Non-Goals

**Goals:**

- Add `http_post`, `http_download`, `write_file` builtin tools following the existing registration pattern
- Add `add_user_with_image(text, image_url)` method to `Conversation` for multimodal messages
- Extend `delegate` with an optional `image_url: str` parameter that builds a multimodal first message

**Non-Goals:**

- Streaming responses from HTTP tools
- Multi-image support in a single message (one image per delegate call is sufficient)
- Base64 file reading (binary data should never enter context — `http_download` handles it directly)
- Changing the core `run()` loop or context model

## Decisions

### D1: http_download writes directly to disk — binary data never enters context

`http_download(url, path)` downloads via httpx and calls `path.write_bytes()`. It returns only the resolved path string. The alternative — `http_get` with a `binary=True` flag returning base64 — was rejected because a base64-encoded PNG is ~4MB in the context window, consuming tokens and crowding out the actual reasoning.

### D2: write_file accepts plain UTF-8 string, no encoding parameter

`write_file(path, content)` writes `content.encode("utf-8")`. No base64 mode. Binary data is handled by `http_download`. Adding an encoding parameter now would be premature generalization with no current use case.

### D3: Conversation.add_user_with_image — new method, not overloaded add_user

A separate `add_user_with_image(text, image_url)` method keeps `add_user(text)` simple and makes call sites explicit. Overloading `add_user` with an optional `image_url` parameter was considered but rejected: it obscures intent and the method would need to branch internally.

### D4: delegate image_url passed as plain string, validated by http_url_validator

The `image_url` parameter in `delegate` is a URL string. It is validated by `http_url_validator` before the subagent is started. The vision model receives the URL in the `image_url` content block — the image is fetched by the LLM provider, not by the agent. This avoids downloading the image twice.

### D5: http_post body is a JSON string parsed internally

`http_post(url, body)` accepts `body: str` (JSON), parses it with `json.loads()`, and passes `json=parsed` to httpx. The LLM always produces JSON as a string; parsing internally avoids requiring the LLM to produce a nested JSON-in-JSON structure.

## Risks / Trade-offs

- **[Risk] http_download path traversal** → Mitigated by routing `path` through `file_path_validator` (FileSandbox), same as `read_file`.
- **[Risk] Vision model URL access** → The image URL is passed to the LLM provider who fetches it. Private/internal URLs could leak if the URL bypasses HttpSandbox. Mitigation: validate `image_url` in `delegate` with `http_url_validator` before passing to the subagent.
- **[Trade-off] http_download bypasses response size limit** — writing directly to disk means we can't check `max_response_bytes` before writing. We accept this: disk space is cheap, context window is not. The FileSandbox `max_file_bytes` check can be applied post-write if needed in future.

## Open Questions

- Should `http_download` overwrite existing files silently, or raise if the path already exists? Current decision: overwrite silently (consistent with `write_file`).
