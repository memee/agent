## 1. Implement analyze_image tool

- [x] 1.1 Create `src/agent/builtin_tools/analyze_image.py`
- [x] 1.2 Register tool with `@tools.register("analyze_image", "builtin", validators={"image_path": file_path_validator}, domain="filesystem")`
- [x] 1.3 Implement: read file bytes, base64-encode, detect MIME type via `mimetypes.guess_type` (fallback `"image/jpeg"`)
- [x] 1.4 Construct one-shot vision chat request with `image_url` content block + `text` prompt block
- [x] 1.5 Read model from `os.environ.get("VISION_MODEL", "gpt-4o")` and call `get_client()`
- [x] 1.6 Return `response.choices[0].message.content`
- [x] 1.7 Add import in `src/agent/__init__.py` so the tool is auto-registered

## 2. Create image_analyst sub-agent profile

- [x] 2.1 Overwrite `src/agent/subagents/image_analyst.md` with final content
- [x] 2.2 Set frontmatter: `name: image_analyst`, `model: openai/gpt-5.4`, `tools: [http_download, analyze_image]`, sandbox (`http: strict`, `filesystem: default, base_dir: ./workspace`)
- [x] 2.3 Write system prompt: URL → `http_download` → `analyze_image` → return analysis + path; local path → `analyze_image` directly

## 3. Verification

- [x] 3.1 Smoke-test `analyze_image` with a local image file and a simple prompt
- [x] 3.2 Verify `image_analyst` profile loads via `profile_registry.get("image_analyst")`
- [x] 3.3 Run existing tests to confirm no regressions
