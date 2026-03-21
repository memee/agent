## 1. http_post tool

- [x] 1.1 Create `src/agent/builtin_tools/http_post.py` with `http_post(url, body, sandbox)` — parse body with `json.loads()`, send via `httpx.Client.post(url, json=parsed)`, respect timeout and `max_response_bytes`, raise `TimeoutError` / `ValueError` as in `http_get`
- [x] 1.2 Add `from agent.builtin_tools import http_post  # noqa: F401` to `src/agent/builtin_tools/__init__.py`
- [x] 1.3 Write tests in `tests/test_builtin_tools.py`: valid POST returns response, invalid JSON raises `ValueError`, private IP raises `PermissionError`, response over size limit raises `ValueError`, timeout raises `TimeoutError`

## 2. http_download tool

- [x] 2.1 Create `src/agent/builtin_tools/http_download.py` with `http_download(url, path, sandbox)` — validate URL via `http_url_validator`, validate path via `file_path_validator`, download binary with httpx, create parent dirs, write bytes to disk, return resolved path string
- [x] 2.2 Add `from agent.builtin_tools import http_download  # noqa: F401` to `src/agent/builtin_tools/__init__.py`
- [x] 2.3 Write tests: file saved to disk and path returned, parent dirs created, existing file overwritten, private IP raises `PermissionError`, path outside `base_dir` raises `PermissionError`, timeout raises `TimeoutError`

## 3. write_file tool

- [x] 3.1 Create `src/agent/builtin_tools/write_file.py` with `write_file(path, content, sandbox)` — validate path via `file_path_validator`, check `len(content.encode("utf-8")) <= sandbox.max_file_bytes`, create parent dirs, write UTF-8 text, return resolved path string
- [x] 3.2 Add `from agent.builtin_tools import write_file  # noqa: F401` to `src/agent/builtin_tools/__init__.py`
- [x] 3.3 Write tests: file created with correct content, existing file overwritten, parent dirs created, content over size limit raises `ValueError`, path outside `base_dir` raises `PermissionError`, blocked path raises `PermissionError`

## 4. Multimodal Conversation support

- [x] 4.1 Add `add_user_with_image(self, text: str, image_url: str) -> None` method to `Conversation` in `src/agent/conversation.py` — appends `{"role": "user", "content": [{"type": "text", "text": text}, {"type": "image_url", "image_url": {"url": image_url}}]}`
- [x] 4.2 Write tests in `tests/test_conversation.py`: `add_user_with_image` produces correct multimodal structure, message is appended after existing messages, `add_user` still produces plain string content

## 5. delegate tool image_url parameter

- [x] 5.1 Add optional `image_url: str | None = None` parameter to the `delegate` function in `src/agent/builtin_tools/delegate.py`
- [x] 5.2 Validate `image_url` with `http_url_validator` against the HTTP sandbox when provided, before starting the subagent
- [x] 5.3 Branch on `image_url`: call `conversation.add_user_with_image(task, image_url)` if provided, else `conversation.add_user(task)` as before
- [x] 5.4 Update the tool's JSON schema to include `image_url` as an optional string parameter
- [x] 5.5 Write tests: `image_url=None` produces plain text message, `image_url` provided produces multimodal message, private IP in `image_url` raises `PermissionError` before subagent starts
