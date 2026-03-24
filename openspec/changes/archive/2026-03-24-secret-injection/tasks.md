## 1. SecretsStore

- [x] 1.1 Create `src/agent/secrets.py` with `SecretsStore` class holding a `dict[str, str]`
- [x] 1.2 Implement `get(name) -> str | None`, `values() -> list[str]`, `names() -> list[str]`
- [x] 1.3 Implement `interpolate(text: str) -> str` using regex to replace `${NAME}` placeholders
- [x] 1.4 Write unit tests for `SecretsStore` (known key, unknown key, multiple placeholders, repeated placeholder, no placeholders)

## 2. Scrubber: runtime secret registration

- [x] 2.1 Add `_RUNTIME: list[str]` module-level list to `scrub.py`
- [x] 2.2 Add `register_runtime_secrets(values: list[str]) -> None` — filters empty strings, sorts longest-first, extends `_RUNTIME`
- [x] 2.3 Apply `_RUNTIME` in `scrub()` after `_EXPLICIT`
- [x] 2.4 Write unit tests for runtime registration (masking after registration, longest-first, empty string ignored)

## 3. registry.execute() — secrets parameter and interpolation

- [x] 3.1 Add `secrets: SecretsStore | None = None` parameter to `ToolsRegistry.execute()`
- [x] 3.2 After `tool_call_start` log (which uses original args), create `validated_args = dict(args)` and interpolate all string values via `secrets.interpolate()` when secrets is not None
- [x] 3.3 Ensure interpolation happens before the validator loop
- [x] 3.4 Write unit tests: placeholder in url resolved before validator, placeholder in body resolved, no secrets = no change, non-string args unchanged, log gets pre-interpolation args

## 4. run() — secrets parameter and scrubber wiring

- [x] 4.1 Add `secrets: SecretsStore | None = None` parameter to `run()`
- [x] 4.2 Call `scrub.register_runtime_secrets(secrets.values())` at the start of `run()` when secrets is not None
- [x] 4.3 Pass `secrets` to every `registry.execute()` call inside the loop
- [x] 4.4 Write integration test: `run()` with secrets resolves placeholder in tool call arg

## 5. http_post — headers parameter

- [x] 5.1 Add `headers: str = "{}"` parameter to `http_post`
- [x] 5.2 Parse `headers` with `json.loads()`, raise `ValueError` on invalid JSON
- [x] 5.3 Merge parsed headers into the httpx request
- [x] 5.4 Write tests: custom header sent, empty headers default, invalid JSON raises ValueError

## 6. http_get — headers parameter

- [x] 6.1 Add `headers: str = "{}"` parameter to `http_get`
- [x] 6.2 Parse `headers` with `json.loads()`, raise `ValueError` on invalid JSON
- [x] 6.3 Merge parsed headers into the httpx request
- [x] 6.4 Write tests: custom header sent, empty headers default, invalid JSON raises ValueError

## 7. System prompt convention

- [x] 7.1 Add `SecretsStore.format_system_prompt_section()` method explaining `${NAME}` syntax and normalization from other formats
