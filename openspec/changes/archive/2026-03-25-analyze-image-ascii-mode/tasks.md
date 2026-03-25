## 1. Dependencies

- [x] 1.1 Add `Pillow>=11.0` to `pyproject.toml` and run `uv sync`

## 2. ASCII Conversion Helper

- [x] 2.1 Define `_ASCII_CHARS = "@%#*+=-:. "` constant in `analyze_image.py`
- [x] 2.2 Implement `_image_to_ascii(image_path, width=100)` with lazy `PIL.Image` import, grayscale conversion, aspect-ratio correction (0.5 height factor), and brightness-to-char mapping

## 3. analyze_image Tool Extension

- [x] 3.1 Add `as_ascii: bool = False` parameter to `analyze_image` signature and docstring
- [x] 3.2 Implement `as_ascii=True` branch: call `_image_to_ascii`, build plain-text message with prompt + ASCII block
- [x] 3.3 Refactor `as_ascii=False` branch to reuse shared `create_client()` and model selection
- [x] 3.4 Fix cosmetic: `if image_url is not None:` → `if image_url:` in `delegate.py`

## 4. Tests

- [ ] 4.1 Add unit tests for `_image_to_ascii`: dark/light pixel mapping, aspect ratio, min height clamp
- [ ] 4.2 Add integration tests for `analyze_image` with `as_ascii=True`: verify plain-text message format, no image attachment
- [ ] 4.3 Verify existing `as_ascii=False` tests still pass unchanged
